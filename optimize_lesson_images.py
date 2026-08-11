"""
optimize_lesson_images.py — lesson tasveerein chhoti karo (tez load hon).

1024x1024 PNG (~1.3 MB) bohat bhaari hai. Yeh script unhe 640px JPEG
(~80 KB) bana deta hai — dekhne mein wohi, magar 15x tez.
Asli PNG lesson_images/_original/ mein mehfooz rehti hai.

    python optimize_lesson_images.py
"""
import os, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    from PIL import Image
except ImportError:
    print("PIL nahi mila. Chalayein:  pip install pillow --break-system-packages")
    sys.exit(1)

SRC = "lesson_images"
BACKUP = os.path.join(SRC, "_original")
MAX_PX = 640
QUALITY = 82

os.makedirs(BACKUP, exist_ok=True)
before = after = 0
done = 0

for fn in sorted(os.listdir(SRC)):
    if not fn.lower().endswith(".png"):
        continue
    src = os.path.join(SRC, fn)
    if os.path.isdir(src):
        continue
    b = os.path.getsize(src)
    # keep the original once
    bak = os.path.join(BACKUP, fn)
    if not os.path.exists(bak):
        shutil.copy2(src, bak)
    im = Image.open(src).convert("RGB")
    im.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
    out = os.path.join(SRC, os.path.splitext(fn)[0] + ".jpg")
    im.save(out, "JPEG", quality=QUALITY, optimize=True)
    a = os.path.getsize(out)
    os.remove(src)                      # app .jpg bhi dhoond leta hai
    before += b; after += a; done += 1
    print(f"  {fn[:46]:46} {b/1024:7.0f}KB -> {a/1024:6.0f}KB")

if done:
    print(f"\n  {done} tasveerein: {before/1024/1024:.1f} MB -> {after/1024/1024:.1f} MB "
          f"({100*(1-after/before):.0f}% chhoti)")
    print(f"  Asli PNG yahan mehfooz hain: {BACKUP}\\")
else:
    print("  Koi PNG nahi mili (shayad pehle hi optimize ho chuki hain).")
