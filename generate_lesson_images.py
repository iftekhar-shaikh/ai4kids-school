"""
generate_lesson_images.py — Grade 1-2 SIMPLE mode ke liye lesson tasveerein.

Har topic ke liye ek picture-book illustration banata hai (gpt-image-1-mini, low
quality) aur lesson_images/ mein cache karta hai.

- RESUMABLE: jo tasveer pehle se maujood hai woh SKIP hoti hai (dobara paisa nahi).
- BUDGET CAP: kharcha limit se upar jaye to khud ruk jata hai.
- Do step: (1) gpt-4o-mini se English image-prompt banao  (2) tasveer banao.

Run:
    python generate_lesson_images.py --dry-run   # kuch kharch kiye baghair dekho
    python generate_lesson_images.py             # asli generation
    python generate_lesson_images.py --force     # sab dobara banao (mehnga!)
"""
import os, sys, io, json, time, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import ai_config
from topic_visuals import LESSON_IMAGE_DIR, lesson_image_slug, lesson_image_path

GRADES = [1, 2]
SUBJECTS = ["ai", "english", "math", "robotics", "science"]

IMAGE_MODEL = "gpt-image-1-mini"
IMAGE_QUALITY = "low"          # 272 output tokens — measured
IMAGE_SIZE = "1024x1024"

# measured rates
IMG_OUT_RATE = 8.00 / 1_000_000      # image output tokens
TXT_IN_RATE = 2.00 / 1_000_000
TXT_MODEL_IN = 0.15 / 1_000_000      # gpt-4o-mini
TXT_MODEL_OUT = 0.60 / 1_000_000
USD_TO_RS = 285.0
BUDGET_RS = 150.0                    # hard cap (estimate is ~Rs 45)

DRY = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv

STYLE = ("Children's educational picture-book illustration for a 5-7 year old child. "
         "Bright friendly colours, thick clean outlines, simple flat shapes, plain "
         "uncluttered background, cheerful and warm. Pakistani children, clothing and "
         "setting where people appear. "
         "CRITICAL: absolutely NO text, NO letters, NO numbers, NO writing anywhere.")

PROMPT_BUILDER = """You write prompts for a children's illustration AI.

Lesson topic (Roman Urdu): "{title}"
Lesson text (Roman Urdu): {text}

Write ONE English sentence (max 40 words) describing a single clear, concrete
scene that would help a 5-7 year old Pakistani child understand this topic.
Rules:
- Describe only what is VISIBLE. No abstract words.
- If the topic involves a specific count, state the exact number of objects.
- Do NOT ask for any text/letters/numbers in the image.
- Reply with the sentence only, nothing else."""

os.makedirs(LESSON_IMAGE_DIR, exist_ok=True)
client = None if DRY else ai_config.get_client()   # dry-run ko key ki zaroorat nahi

spent = 0.0
made = skipped = failed = 0

def money():
    return spent * USD_TO_RS

for grade in GRADES:
    for sub in SUBJECTS:
        fp = os.path.join("kb", f"grade_{grade}", f"{sub}.json")
        if not os.path.exists(fp):
            continue
        data = json.load(open(fp, encoding="utf-8"))
        for topic in data.get("topics", []):
            title = topic.get("title", "")
            if not title:
                continue
            if lesson_image_path(grade, sub, title) and not FORCE:
                skipped += 1
                continue
            if money() >= BUDGET_RS:
                print(f"\n!! BUDGET CAP (~Rs {money():.1f}) — ruk gaya.")
                print(f"   made={made} skipped={skipped} failed={failed}")
                sys.exit(0)
            slug = lesson_image_slug(grade, sub, title)
            if DRY:
                print(f"  WOULD  g{grade}/{sub:9} {title}")
                made += 1
                continue
            try:
                # 1) topic -> English scene prompt
                pr = client.chat.completions.create(
                    model=ai_config.MODEL, max_tokens=90, temperature=0.6,
                    messages=[{"role": "user", "content": PROMPT_BUILDER.format(
                        title=title, text=(topic.get("text_simple") or
                                           topic.get("description") or "")[:400])}])
                scene = pr.choices[0].message.content.strip().strip('"')
                u = pr.usage
                spent += u.prompt_tokens * TXT_MODEL_IN + u.completion_tokens * TXT_MODEL_OUT

                # 2) scene -> image
                r = client.images.generate(model=IMAGE_MODEL, n=1, size=IMAGE_SIZE,
                                           quality=IMAGE_QUALITY,
                                           prompt=f"{scene}\n\nSTYLE: {STYLE}")
                d = r.data[0]
                img = base64.b64decode(d.b64_json) if getattr(d, "b64_json", None) else None
                if img is None:
                    import urllib.request
                    with urllib.request.urlopen(d.url) as fh:
                        img = fh.read()
                iu = getattr(r, "usage", None)
                if iu:
                    spent += (getattr(iu, "output_tokens", 272) * IMG_OUT_RATE
                              + getattr(iu, "input_tokens", 150) * TXT_IN_RATE)
                else:
                    spent += 272 * IMG_OUT_RATE + 150 * TXT_IN_RATE

                open(os.path.join(LESSON_IMAGE_DIR, slug + ".png"), "wb").write(img)
                made += 1
                print(f"  OK   g{grade}/{sub:9} {title[:34]:34} ~Rs {money():5.1f}")
                time.sleep(0.3)
            except Exception as e:
                failed += 1
                print(f"  FAIL g{grade}/{sub:9} {title[:34]:34} {type(e).__name__}: {str(e)[:90]}")

print(f"\n=== DONE ===  made={made} skipped={skipped} failed={failed}")
print(f"    kharcha: ${spent:.4f}  ~Rs {money():.1f}")
