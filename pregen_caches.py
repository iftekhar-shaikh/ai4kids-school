"""
pregen_caches.py — Grade 3-5 ke liye sab kuch pehle se bana kar cache karo.

Banata hai:
  1. Checkpoint sawaal   -> checkpoint_cache.json   (har lesson section ke liye)
  2. Fill-in-the-blank   -> fitb_cache.json         (har topic ke 3 blanks)
  3. Roman Urdu summary  -> urdu_summary_cache.json (har topic ka khulasa)

Iske baad Grade 3-5 ka sabaq bhi API ke baghair chalta hai (sirf chat par kharcha).

AHEM: prompts aur cache keys SEEDHE ai4kids_school.py se nikale jate hain (ast se),
taake app aur yeh script kabhi alag na hon.

    python pregen_caches.py --dry-run     # kuch kharch kiye baghair plan dekho
    python pregen_caches.py               # asli generation (resumable)
"""
import os, sys, io, json, ast, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import ai_config

APP = "ai4kids_school.py"
GRADES = [3, 4, 5]
SUBJECTS = ["ai", "english", "math", "robotics", "science"]

IN_RATE, OUT_RATE = 0.15 / 1_000_000, 0.60 / 1_000_000   # gpt-4o-mini
USD_TO_RS = 285.0
BUDGET_RS = 250.0

DRY = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# 1. App source se constants + pure functions nikalo (koi Streamlit import nahi)
# ---------------------------------------------------------------------------
WANT_CONST = ["BRAND", "MCQ_EXAMINER_PROMPT", "SECTION_META", "CHECKPOINT_PROMPTS",
              "FITB_GENERATE_PROMPT", "URDU_SUMMARY_PROMPT", "URDU_SUMMARY_CACHE",
              "CHECKPOINT_CACHE_FILE", "FITB_CACHE_FILE", "KB_DIR"]
WANT_FUNC = ["cache_key", "parse_json", "parse_lesson_sections", "load_kb_topic"]

src = open(APP, encoding="utf-8").read()
tree = ast.parse(src)
ns = {"os": os, "json": json, "re": re}
picked_c, picked_f = [], []
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in WANT_CONST:
                exec(compile(ast.Module([node], []), "<c>", "exec"), ns)
                picked_c.append(t.id)
    elif isinstance(node, ast.FunctionDef) and node.name in WANT_FUNC:
        exec(compile(ast.Module([node], []), "<f>", "exec"), ns)
        picked_f.append(node.name)

missing = [x for x in WANT_CONST + WANT_FUNC if x not in picked_c + picked_f]
print(f"  extracted {len(picked_c)} constants, {len(picked_f)} functions")
if missing:
    print(f"  !! MISSING from {APP}: {missing}")
    sys.exit(1)

cache_key = ns["cache_key"]
parse_json = ns["parse_json"]
parse_lesson_sections = ns["parse_lesson_sections"]
load_kb_topic = ns["load_kb_topic"]
CK_FILE = ns["CHECKPOINT_CACHE_FILE"]
FITB_FILE = ns["FITB_CACHE_FILE"]
SUM_FILE = ns["URDU_SUMMARY_CACHE"]

# ---------------------------------------------------------------------------
# 2. Apna run_agent (ai_config endpoint use karta hai)
# ---------------------------------------------------------------------------
spent = 0.0
client = None if DRY else ai_config.get_client()

def run_agent(system_prompt, task, max_tokens=2000):
    global spent
    r = client.chat.completions.create(
        model=ai_config.MODEL, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": task}])
    u = r.usage
    spent += u.prompt_tokens * IN_RATE + u.completion_tokens * OUT_RATE
    return r.choices[0].message.content.strip()

def money():
    return spent * USD_TO_RS

def load(fp):
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save(fp, data):
    json.dump(data, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

ck_cache, fitb_cache, sum_cache = load(CK_FILE), load(FITB_FILE), load(SUM_FILE)
made = {"ck": 0, "fitb": 0, "sum": 0}
skip = {"ck": 0, "fitb": 0, "sum": 0}
fail = 0

def over_budget():
    if money() >= BUDGET_RS:
        print(f"\n!! BUDGET CAP (~Rs {money():.1f}) — ruk gaya.")
        return True
    return False

# ---------------------------------------------------------------------------
# 3. Loop
# ---------------------------------------------------------------------------
for grade in GRADES:
    for sub in SUBJECTS:
        fp = os.path.join(ns["KB_DIR"], f"grade_{grade}", f"{sub}.json")
        if not os.path.exists(fp):
            continue
        for topic in json.load(open(fp, encoding="utf-8")).get("topics", []):
            title = topic.get("title", "")
            lesson = topic.get("lesson", "") or ""
            if not title or not lesson:
                continue

            # ---- 3a. checkpoints (one per section, last section skipped in app) ----
            secs = parse_lesson_sections(lesson)
            for sec in secs[:-1] if len(secs) > 1 else secs:
                k = f"{title}_{sec['key']}_{grade}"
                if k in ck_cache:
                    skip["ck"] += 1; continue
                if DRY:
                    made["ck"] += 1; continue
                if over_budget(): break
                try:
                    prompt = (f"Tum Grade {grade} ke liye ek Roman Urdu checkpoint sawaal banao.\n"
                              f"Topic: {title}\nSection: {sec['key']}\n\nSection content:\n"
                              f"{sec['body'][:600]}\n\n"
                              f"{ns['CHECKPOINT_PROMPTS'].get(sec['key'], ns['CHECKPOINT_PROMPTS']['SAMJHAO'])}")
                    q = parse_json(run_agent(ns["MCQ_EXAMINER_PROMPT"], prompt, 500))
                    # MCQ_EXAMINER_PROMPT poora quiz object deta hai
                    # {title, difficulty, questions:[...]} — magar app SIRF flat
                    # {q, a, b, c, d, correct} accept karta hai. Isliye flatten karo.
                    if isinstance(q, dict) and "q" not in q:
                        qs = q.get("questions")
                        q = qs[0] if isinstance(qs, list) and qs else None
                    if isinstance(q, dict) and "q" in q and "correct" in q:
                        ck_cache[k] = q; save(CK_FILE, ck_cache); made["ck"] += 1
                    else:
                        fail += 1
                except Exception as e:
                    fail += 1

            # ---- 3b. FITB ----
            k = f"{title}_{grade}"
            if k in fitb_cache:
                skip["fitb"] += 1
            elif DRY:
                made["fitb"] += 1
            elif not over_budget():
                try:
                    p = ns["FITB_GENERATE_PROMPT"].format(grade=grade, topic=title,
                                                          content=lesson[:1500])
                    d = parse_json(run_agent(ns["BRAND"], p, 800))
                    blanks = d.get("blanks") if isinstance(d, dict) else None
                    if blanks:
                        fitb_cache[k] = blanks; save(FITB_FILE, fitb_cache); made["fitb"] += 1
                except Exception:
                    fail += 1

            # ---- 3c. Urdu summary ----
            k = cache_key(sub, title, grade)
            if k in sum_cache:
                skip["sum"] += 1
            elif DRY:
                made["sum"] += 1
            elif not over_budget():
                try:
                    s = run_agent(ns["URDU_SUMMARY_PROMPT"], f"Sabaq: {title}\n\n{lesson}", 800)
                    if s:
                        sum_cache[k] = s; save(SUM_FILE, sum_cache); made["sum"] += 1
                except Exception:
                    fail += 1

            if not DRY:
                print(f"  g{grade}/{sub:9} {title[:30]:30} "
                      f"ck={made['ck']:3} fitb={made['fitb']:3} sum={made['sum']:3} "
                      f"~Rs {money():6.1f}")

print(f"\n=== DONE ===")
print(f"  checkpoints : made {made['ck']:4}  skipped {skip['ck']:4}")
print(f"  FITB        : made {made['fitb']:4}  skipped {skip['fitb']:4}")
print(f"  summaries   : made {made['sum']:4}  skipped {skip['sum']:4}")
print(f"  failed      : {fail}")
print(f"  kharcha     : ${spent:.4f}  ~Rs {money():.1f}")
