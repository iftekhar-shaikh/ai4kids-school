# -*- coding: utf-8 -*-
"""Build AI4Kids Class 1 offline zip pack."""
from __future__ import annotations
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK_DIR = ROOT / "packs"
OUT_ZIP = PACK_DIR / "ai4kids-grade1-offline.zip"

META = {
    "ai": ("AI & Technology", "🤖"),
    "math": ("Hisaab (Math)", "🔢"),
    "english": ("English", "📚"),
    "science": ("Science", "🔬"),
    "robotics": ("Robotics", "🦾"),
    "social": ("Social Studies", "🌍"),
    "islamiat": ("Islamiat", "🕌"),
    "urdu": ("Urdu", "📖"),
}


def load_grade1_topics():
    rows = []
    gdir = ROOT / "kb" / "grade_1"
    for sk, (name, emoji) in META.items():
        p = gdir / f"{sk}.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        topics = data if isinstance(data, list) else data.get("topics") or []
        for t in topics:
            if not isinstance(t, dict):
                continue
            rel = (t.get("interactive_file") or "").replace("\\", "/")
            rows.append({
                "sk": sk,
                "subj": name,
                "emoji": emoji,
                "title": t.get("title") or "Topic",
                "desc": t.get("description") or t.get("desc") or "",
                "file": rel,
            })
    return rows


def build_index(topics) -> str:
    by = {}
    for t in topics:
        by.setdefault(t["sk"], []).append(t)
    sections = []
    for sk, (name, emoji) in META.items():
        items = by.get(sk) or []
        if not items:
            continue
        lis = []
        for t in items:
            href = t["file"] if t["file"] else "#"
            title = (t["title"] or "").replace("<", "&lt;")
            desc = (t["desc"] or "").replace("<", "&lt;")
            miss = "" if t["file"] else " (app jald)"
            lis.append(
                f'<a class="card" href="{href}">'
                f'<span class="t">{emoji} {title}{miss}</span>'
                f'<span class="d">{desc}</span></a>'
            )
        sections.append(
            f'<section class="subj"><h2>{emoji} {name}</h2>'
            f'<div class="grid">{"".join(lis)}</div></section>'
        )
    body = "\n".join(sections)
    return f"""<!doctype html>
<html lang="ur"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI4Kids — Class 1 Offline Pack</title>
<style>
:root{{--ink:#17252f;--muted:#526672;--paper:#fffdf7;--green:#27ae60;--green-deep:#1e8449;--teal:#1abc9c;--font:'Segoe UI','Trebuchet MS',Tahoma,sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:var(--font);background:var(--paper);color:var(--ink);line-height:1.5;padding-bottom:40px}}
.header{{background:linear-gradient(135deg,var(--green),var(--teal));color:#fff;padding:22px 16px;text-align:center}}
.header h1{{margin:0 0 6px;font-size:clamp(1.4rem,5vw,2rem)}}
.trust{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding:10px 12px;margin:12px 16px;background:#eafaf1;border:2px solid var(--green);border-radius:14px}}
.pill{{background:#fff;border:2px solid var(--ink);border-radius:999px;padding:6px 12px;font-weight:800;font-size:.95rem}}
.wrap{{max-width:1000px;margin:0 auto;padding:8px 16px 24px}}
.subj{{margin:18px 0}}
.subj h2{{font-size:clamp(1.2rem,4vw,1.5rem);margin:0 0 10px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.card{{display:flex;flex-direction:column;gap:4px;text-decoration:none;color:inherit;background:#fff;border:3px solid #d9d2c5;border-radius:14px;padding:14px;min-height:88px;font-weight:800}}
.card:hover{{border-color:var(--green);background:#eafaf1}}
.card .d{{font-size:.9rem;color:var(--muted);font-weight:600}}
.note{{margin:12px 16px;padding:12px;background:#fff0b8;border:2px solid var(--ink);border-radius:12px;font-weight:700}}
</style></head><body>
<div class="header"><h1>📚 AI4Kids — Class 1 Offline</h1>
<p>Unzip → index.html → topic → Khelo app</p></div>
<div class="trust" role="note"><b style="color:#1e8449">Parents ke liye</b>
<span class="pill">🛡️ Safe for kids</span>
<span class="pill">📶 Offline</span>
<span class="pill">🔓 Bina login</span></div>
<p class="note">Folder unzip karo, phir <code>index.html</code> browser mein kholo. Internet zaroori nahi.</p>
<div class="wrap">{body}</div>
</body></html>
"""


def build_zip():
    PACK_DIR.mkdir(exist_ok=True)
    topics = load_grade1_topics()
    missing = []
    files_added = 0
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("index.html", build_index(topics))
        z.writestr(
            "README-UR.txt",
            "AI4Kids Class 1 Offline Pack\\n"
            "1) Zip extract karo\\n"
            "2) index.html Chrome/Edge mein kholo\\n"
            "3) Subject → topic dabao → app\\n"
            "Login nahi chahiye. WhatsApp: 0337 1468899\\n",
        )
        for p in (ROOT / "kb" / "grade_1").glob("*.json"):
            z.write(p, arcname=f"kb/grade_1/{p.name}")
            files_added += 1
        for t in topics:
            rel = t["file"]
            if not rel:
                missing.append(t["title"])
                continue
            src = ROOT / rel
            if not src.exists():
                missing.append(rel)
                continue
            z.write(src, arcname=rel)
            files_added += 1
    return {
        "zip": str(OUT_ZIP),
        "bytes": OUT_ZIP.stat().st_size,
        "mb": round(OUT_ZIP.stat().st_size / 1e6, 2),
        "topics": len(topics),
        "files": files_added,
        "missing": missing,
    }


if __name__ == "__main__":
    info = build_zip()
    print(info)
