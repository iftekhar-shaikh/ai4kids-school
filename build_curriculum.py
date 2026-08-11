# -*- coding: utf-8 -*-
"""Rebuild curriculum.html from snc_curriculum.py — full Class 1-5 FBISE/SNC."""
import snc_curriculum as snc

AI_TOPICS = {
    1: ["AI kya hai? — machine jo sochti hai", "Robot dost — hamare madadgaar robots",
        "Smart vs Silly machine", "Computer pehchano — screen, keyboard, mouse",
        "Bolta computer — Alexa, Siri", "AI games mein"],
    2: ["AI ki aankh — face detection", "AI ke kaan — voice recognition",
        "Sorting seekho", "Yes/No decisions", "AI drawings", "AI hamare ghar mein"],
    3: ["Patterns dhundho", "Data kya hai?", "Algorithm — biryani ki recipe jaisa",
        "AI aur cricket — DRS, Hawk-Eye", "Coding intro", "Internet safety"],
    4: ["Machine learning — examples se training", "Chatbot kya hai — ChatGPT, Claude",
        "Data types — text, numbers, images", "AI decision tree",
        "Fake vs real — deepfakes pehchano", "AI jobs — future careers"],
    5: ["Neural network — dimaag jaisa computer", "Prompt engineering",
        "Computer vision — object detection", "NLP basics", "AI ethics", "AI project design"],
}
ROBO_TOPICS = {
    1: ["Machine kya hai? — lever, wheel", "Robot kya karta?", "Sensor dost",
        "Motor chalo!", "Traffic light system", "Toy robot design"],
    2: ["Ghar ki machines", "Remote control kaise kaam karta hai", "Battery aur switch",
        "Gears aur pulleys", "Robot ke hisse", "Paper robot banao"],
    3: ["Simple circuits", "Automatic machines — washing machine", "Robot ki aankhein (sensors)",
        "Wheels vs legs — robot movement", "Factory mein machines", "LEGO/block robots"],
    4: ["Arduino intro — chhota computer", "Drone kaise udta hai", "Factory robot",
        "Line follower robot", "Automatic gate", "Robotic arm"],
    5: ["IoT basics — smart devices", "3D printing", "AI + Robotics — smart robots",
        "Self-driving car system", "Space robots — Mars rovers", "Pakistan mein automation"],
}

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

parts = []
parts.append("""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI4Kids.pk — Curriculum (Class 1-5) — FBISE/SNC</title>
<style>
 body{font-family:'Segoe UI',Tahoma,sans-serif;background:#fdf8ef;color:#2c3e50;margin:0;padding:24px;max-width:960px;margin:auto}
 h1{text-align:center;color:#c0392b;margin-bottom:4px}
 .sub{text-align:center;color:#7f8c8d;margin-bottom:6px}
 .grade{background:#fff;border:2px solid #f39c12;border-radius:14px;padding:16px 22px;margin:18px 0;box-shadow:0 2px 6px rgba(0,0,0,.06)}
 .grade h2{color:#2980b9;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:0}
 h3{color:#27ae60;margin:14px 0 6px}
 h4{color:#8e44ad;margin:10px 0 4px}
 ul{margin:4px 0 10px;padding-left:24px}
 li{margin:3px 0;line-height:1.6}
 .weight{font-size:.85em;color:#7f8c8d;font-style:italic}
 .printbtn{display:block;margin:14px auto;padding:10px 26px;font-size:1rem;font-weight:700;color:#fff;background:#27ae60;border:none;border-radius:10px;cursor:pointer}
 .toc{background:#fff;border:2px dashed #2980b9;border-radius:12px;padding:12px 20px;margin:14px 0}
 .toc a{color:#2980b9;text-decoration:none;margin-right:14px;font-weight:600}
 @media print{.printbtn{display:none}body{background:#fff}}
</style></head><body>
<h1>🏫 AI4Kids.pk — Curriculum</h1>
<p class="sub">Classes 1–5 • Single National Curriculum (SNC) — Federal Board (FBISE), Islamabad</p>
<p class="sub">Subjects: Hisaab (Math) • English • General Science/GK • AI &amp; Technology (Lazmi) • Automation &amp; Robotics</p>
<button class="printbtn" onclick="window.print()">🖨️ Print / Save as PDF</button>
<div class="toc"><b>Jump to:</b> <a href="#g1">Grade 1</a><a href="#g2">Grade 2</a><a href="#g3">Grade 3</a><a href="#g4">Grade 4</a><a href="#g5">Grade 5</a></div>
""")

for g in range(1, 6):
    parts.append(f'<div class="grade" id="g{g}"><h2>🎒 Grade {g} — Class {g}</h2>')

    # MATH — full units + topics + weightage
    m = snc.MATH_CURRICULUM[g]
    parts.append("<h3>🔢 Hisaab (Math) — SNC</h3>")
    for unit in m["units"]:
        parts.append(f"<h4>{esc(unit['unit'])}</h4><ul>")
        for t in unit["topics"]:
            parts.append(f"<li>{esc(t)}</li>")
        parts.append("</ul>")
    w = ", ".join(f"{k} {v}%" for k, v in m["weightage"].items())
    parts.append(f'<p class="weight">Exam weightage: {esc(w)}</p>')

    # ENGLISH
    e = snc.ENGLISH_CURRICULUM[g]
    parts.append("<h3>📚 English — SNC</h3><ul>")
    for a in e["areas"]:
        parts.append(f"<li>{esc(a)}</li>")
    parts.append("</ul>")

    # SCIENCE / GK
    s = snc.SCIENCE_CURRICULUM[g]
    parts.append(f"<h3>🔬 {esc(s['title'].rsplit(' Grade',1)[0])} — SNC</h3><ul>")
    for a in s["areas"]:
        parts.append(f"<li>{esc(a)}</li>")
    parts.append("</ul>")

    # AI (Lazmi)
    parts.append("<h3>🤖 AI &amp; Technology (Lazmi — AI4Kids.pk special)</h3><ul>")
    for t in AI_TOPICS[g]:
        parts.append(f"<li>{esc(t)}</li>")
    parts.append("</ul>")

    # ROBOTICS
    parts.append("<h3>⚙️ Automation &amp; Robotics (AI4Kids.pk special)</h3><ul>")
    for t in ROBO_TOPICS[g]:
        parts.append(f"<li>{esc(t)}</li>")
    parts.append("</ul>")

    parts.append("</div>")

parts.append("""<p class="sub">AI4Kids.pk — اسلام آباد کا پہلا اردو AI سکول • Generated from snc_curriculum.py</p>
</body></html>""")

with open("curriculum.html", "w", encoding="utf-8") as f:
    f.write("\n".join(parts))

print("curriculum.html rebuilt successfully!")
print("Size:", __import__("os").path.getsize("curriculum.html"), "bytes")
