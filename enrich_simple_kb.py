"""
enrich_simple_kb.py — Add SIMPLE-mode fields to Grade 1-2 KB lessons.

Adds to every topic (ADDITIVE — never overwrites existing fields):
    emoji, text_simple, audio_text, simple_quiz

- Grades 1-2 ONLY.
- Resumable: a topic that already has all 4 fields is SKIPPED (no re-spend).
- Caches to disk: the KB JSON itself is the cache (written back in place).
- Budget guard: hard-stops if estimated spend exceeds BUDGET_RS.

Run:
    python enrich_simple_kb.py            # enrich missing topics
    python enrich_simple_kb.py --dry-run  # show what WOULD be done, no API
    python enrich_simple_kb.py --force    # re-generate even if fields exist
"""
import os, json, sys, time
import ai_config                      # endpoint config: ai_config.json

def get_client():
    return ai_config.get_client()

MODEL = ai_config.MODEL

GRADES = [1, 2]
SUBJECTS = ["ai", "english", "math", "robotics", "science"]
SIMPLE_FIELDS = ("emoji", "text_simple", "audio_text", "simple_quiz")

# gpt-4o-mini pricing (USD per 1M tokens): input 0.15, output 0.60
IN_RATE, OUT_RATE = 0.15 / 1_000_000, 0.60 / 1_000_000
USD_TO_RS = 285.0            # approx; only for the on-screen estimate
BUDGET_RS = 60.0            # hard cap — script aborts before exceeding

DRY_RUN = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv

PROMPT = """You write for AI4Kids.pk — Islamabad ka pehla Urdu AI school.
Audience: Grade {grade} bachay (5-7 saal). Bohat chhotay bachay jo abhi parhna seekh rahe hain.

RULES (bohat zaroori):
- ROMAN URDU ONLY. Na English paragraphs, na Urdu script (اردو). Sirf Roman Urdu.
- Bohat aasaan, chhote jumle. Pakistani misalein (biryani, cricket, rickshaw).

Topic: "{title}"
Is topic ka poora sabaq (reference): {lesson}

Neeche EXACTLY is JSON format mein jawab do (aur kuch nahi):
{{
  "emoji": "<ek emoji jo topic ko dikhaye>",
  "text_simple": "<60 se 80 alfaaz ka BOHAT aasaan Roman Urdu sabaq, chhote jumle>",
  "audio_text": "<wohi text_simple, awaaz mein sunane ke liye — saaf, dheeme>",
  "simple_quiz": [
    {{
      "emoji": "❓",
      "question_short": "<ek chhota sawaal Roman Urdu mein>",
      "options": [
        {{"emoji": "<emoji>", "text": "<sahi jawab, 1-3 alfaaz>"}},
        {{"emoji": "<emoji>", "text": "<galat jawab>"}},
        {{"emoji": "<emoji>", "text": "<galat jawab>"}}
      ],
      "answer": <0, 1 ya 2 — sahi option ka index>
    }}
  ]
}}
"""

def has_all_fields(topic):
    return all(topic.get(f) for f in SIMPLE_FIELDS)

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1])

def enrich_topic(topic, grade):
    prompt = PROMPT.format(grade=grade, title=topic.get("title", ""),
                           lesson=(topic.get("lesson", "") or "")[:1200])
    r = get_client().chat.completions.create(
        model=MODEL, temperature=0.5, max_tokens=700,
        messages=[{"role": "user", "content": prompt}])
    usage = r.usage
    data = parse_json(r.choices[0].message.content)
    # ADDITIVE: only set the 4 simple fields, never touch existing keys
    for f in SIMPLE_FIELDS:
        if f in data:
            topic[f] = data[f]
    return usage.prompt_tokens, usage.completion_tokens

def main():
    total_in = total_out = 0
    done = skipped = failed = 0
    for grade in GRADES:
        for sub in SUBJECTS:
            fp = os.path.join("kb", f"grade_{grade}", f"{sub}.json")
            if not os.path.exists(fp):
                print(f"  MISSING {fp}"); continue
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
            changed = False
            for topic in d.get("topics", []):
                title = topic.get("title", "?")
                if has_all_fields(topic) and not FORCE:
                    skipped += 1
                    print(f"  SKIP   g{grade}/{sub}: {title}")
                    continue
                # Budget guard BEFORE spending
                est_rs = (total_in * IN_RATE + total_out * OUT_RATE) * USD_TO_RS
                if est_rs >= BUDGET_RS:
                    print(f"\n!! BUDGET CAP hit (~Rs {est_rs:.1f} >= {BUDGET_RS}). Stopping.")
                    if changed and not DRY_RUN:
                        with open(fp, "w", encoding="utf-8") as f:
                            json.dump(d, f, ensure_ascii=False, indent=2)
                    print(f"\nDone={done} Skipped={skipped} Failed={failed} ~Rs {est_rs:.2f}")
                    return
                if DRY_RUN:
                    print(f"  WOULD g{grade}/{sub}: {title}")
                    done += 1
                    continue
                try:
                    ti, to = enrich_topic(topic, grade)
                    total_in += ti; total_out += to
                    changed = True; done += 1
                    rs = (total_in * IN_RATE + total_out * OUT_RATE) * USD_TO_RS
                    print(f"  OK     g{grade}/{sub}: {title}  (~Rs {rs:.2f} total)")
                    time.sleep(0.3)
                except Exception as e:
                    failed += 1
                    print(f"  FAIL   g{grade}/{sub}: {title} -> {e}")
            # Write back after each file (so a crash mid-run still saves progress)
            if changed and not DRY_RUN:
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
                print(f"  saved {fp}")
    rs = (total_in * IN_RATE + total_out * OUT_RATE) * USD_TO_RS
    print(f"\n=== DONE ===  enriched={done} skipped={skipped} failed={failed}")
    print(f"tokens in={total_in} out={total_out}  ~Rs {rs:.2f}  (~${rs/USD_TO_RS:.4f})")

if __name__ == "__main__":
    main()
