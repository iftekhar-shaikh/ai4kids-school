"""
Build lesson_bank.html from KB JSON files
Run: python build_lesson_bank.py
"""
import json
import base64, os, base64
from pathlib import Path
import re as _re
try:
    from PIL import Image
    from io import BytesIO
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

def _slug(s):
    s = (s or "").lower().strip()
    s = _re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def find_thumb(grade, sk, title):
    """Return (mime, base64) tiny card thumb or (None, None)."""
    folder = Path("lesson_images")
    if not folder.exists():
        return None, None
    slug = _slug(title)
    candidates = [
        folder / f"g{grade}_{sk}_{slug}.jpg",
        folder / f"g{grade}_{sk}_{slug}.png",
        folder / f"g{grade}_{sk}_{slug}.webp",
    ]
    if not any(c.exists() for c in candidates):
        token = slug.split("-")[0] if slug else ""
        hits = sorted(folder.glob(f"g{grade}_{sk}_*"))
        for f in hits:
            if token and token in f.stem:
                candidates.insert(0, f)
                break
        candidates.extend(hits)
    path = next((c for c in candidates if c.exists()), None)
    if not path:
        return None, None
    try:
        if _HAS_PIL:
            im = Image.open(path).convert("RGB")
            im.thumbnail((360, 200), Image.Resampling.LANCZOS)
            buf = BytesIO()
            im.save(buf, format="JPEG", quality=62, optimize=True)
            return "image/jpeg", base64.b64encode(buf.getvalue()).decode("ascii")
        raw = path.read_bytes()
        mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        return mime, base64.b64encode(raw).decode("ascii")
    except Exception:
        return None, None


KB_DIR = "kb"
OUT = "lesson_bank.html"

SUBJ_META = {
    "ai":       {"name": "AI & Technology", "emoji": "🤖", "color": "#1abc9c"},
    "math":     {"name": "Hisaab (Math)",   "emoji": "🔢", "color": "#27ae60"},
    "english":  {"name": "English",          "emoji": "📚", "color": "#9b59b6"},
    "science":  {"name": "General Science",  "emoji": "🔬", "color": "#e74c3c"},
    "robotics": {"name": "Automation & Robotics","emoji":"⚙️","color":"#f39c12"},
    "social":   {"name": "Social Studies", "emoji": "🌍", "color": "#2980b9"},
    "islamiat": {"name": "Islamiat", "emoji": "🕌", "color": "#0e6655"},
    "urdu": {"name": "Urdu", "emoji": "📗", "color": "#8e44ad"},
}

def esc(t):
    if not t: return ""
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')

# Collect all topics
all_topics = []
for grade in range(1, 6):
    for sk, sm in SUBJ_META.items():
        fp = os.path.join(KB_DIR, f"grade_{grade}", f"{sk}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        for topic in data.get("topics", []):
            qs = topic.get("quiz", {}).get("questions", [])
            mime, tb64 = find_thumb(grade, sk, topic.get("title", ""))
            all_topics.append({
                "grade": grade,
                "subj_key": sk,
                "subj_name": sm["name"],
                "subj_emoji": sm["emoji"],
                "subj_color": sm["color"],
                "title": topic.get("title", ""),
                "desc": topic.get("description", ""),
                "lesson": topic.get("lesson", ""),
                "quiz_count": len(qs),
                "questions": qs,
                "interactive_file": topic.get("interactive_file", ""),
                "interactive_label": topic.get("interactive_label", ""),
                "thumb_mime": mime or "",
                "thumb_b64": tb64 or "",
            })

print(f"Found {len(all_topics)} topics — building HTML...")

# Build HTML
lines = []
lines.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI4Kids.pk — Lesson Bank</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:#f5f5f0;color:#2c3e50}
.header{background:linear-gradient(135deg,#27ae60,#1abc9c);color:#fff;padding:24px;text-align:center}
.header h1{font-size:clamp(1.4rem,5vw,2rem);margin-bottom:4px}
.header p{font-size:0.95rem;opacity:0.9}
.controls{background:#fff;padding:18px 56px 14px 20px;border-bottom:2px solid #eee;
  display:flex;flex-wrap:wrap;gap:10px;align-items:center;position:sticky;top:0;z-index:100}
.search{flex:1;min-width:200px;padding:8px 14px;border:2px solid #ddd;
  border-radius:20px;font-size:0.95rem;outline:none}
.search:focus{border-color:#27ae60}
.filters{display:flex;flex-wrap:wrap;gap:8px;padding-right:8px;align-items:center}
.filter-btn{padding:5px 12px;border:2px solid #ddd;border-radius:16px;
  background:#fff;cursor:pointer;font-size:0.85rem;transition:all .2s}
.filter-btn.active{background:#27ae60;color:#fff;border-color:#27ae60}
.stats{padding:10px 20px;font-size:0.85rem;color:#666;background:#fffbea;
  border-bottom:1px solid #eee}
.grid{padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.card{background:#fff;border-radius:14px;border:2px solid #eee;overflow:hidden;
  transition:box-shadow .2s;cursor:pointer}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}
.card-header{padding:12px 16px;display:flex;align-items:center;gap:10px}
.card-emoji{font-size:1.5rem}
.card-info h3{font-size:clamp(1.05rem,3.5vw,1.25rem);margin:0}
.card-info .meta{font-size:0.78rem;color:#888;margin-top:2px}
.grade-badge{padding:2px 8px;border-radius:10px;font-size:0.75rem;
  font-weight:700;color:#fff;margin-left:auto;flex-shrink:0}
.card-desc{padding:0 16px 10px;font-size:clamp(0.95rem,3vw,1.1rem);color:#666}
.card-footer{padding:8px 16px;background:#f9f9f9;border-top:1px solid #eee;
  display:flex;gap:8px;align-items:center}
.tag{padding:2px 8px;border-radius:10px;font-size:0.75rem;background:#eee;color:#555}
.tag.has-lesson{background:#e8f8f5;color:#16a085}
.tag.has-quiz{background:#fef9e7;color:#d68910}
.tag.has-interactive{background:#f5eef8;color:#8e44ad}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,.5);z-index:200;overflow-y:auto}
.modal.open{display:flex;align-items:flex-start;justify-content:center;padding:20px}
.modal-box{background:#fff;border-radius:16px;width:100%;max-width:760px;
  max-height:90vh;overflow-y:auto;padding:24px;position:relative;margin:auto}
.modal-close{position:absolute;top:14px;right:16px;font-size:1.5rem;
  cursor:pointer;color:#999;background:none;border:none;line-height:1}
.modal-close:hover{color:#333}
.modal h2{font-size:clamp(1.55rem,5vw,2rem);margin-bottom:4px}
.modal .meta{font-size:clamp(1rem,3.2vw,1.15rem);color:#555;margin-bottom:16px}
.lesson-text{font-size:clamp(1.25rem,4.2vw,1.55rem);line-height:1.85;padding:22px 18px;background:#111;color:#f5f5f5;border-radius:14px;border:2px solid #333;min-height:160px;white-space:pre-wrap;margin:10px 0}
.read-bar{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.read-btn{display:inline-block;padding:16px 24px;border:none;border-radius:22px;background:#8e44ad;
  color:#fff;font-size:clamp(1.2rem,4.2vw,1.45rem);font-weight:800;cursor:pointer;min-height:56px;
  line-height:1.35;white-space:normal}
.read-btn:hover{background:#7d3c98}
.read-status{color:#8e44ad;font-weight:600;font-size:0.9rem}
.rw.reading{background:#ffe08a;border-radius:4px;box-shadow:0 0 0 2px #ffe08a}
.quiz-section{margin-top:20px}
.quiz-section h3{margin-bottom:12px;color:#d68910}
.question{background:#fffbea;border-radius:10px;padding:14px;margin-bottom:10px;
  border-left:4px solid #f39c12}
.question p{font-weight:600;margin-bottom:8px;font-size:clamp(1.05rem,3.5vw,1.2rem)}
.option{padding:4px 0;font-size:0.9rem}
.option.correct{color:#27ae60;font-weight:700}
/* --- interactive quiz --- */
.opt-btn{display:block;width:100%;text-align:left;padding:14px 16px;margin:8px 0;
  border:2px solid #ddd;border-radius:12px;background:#fff;cursor:pointer;
  font-size:clamp(1.05rem,3.5vw,1.2rem);font-family:inherit;color:#2c3e50;transition:all .15s;min-height:48px}
.opt-btn:hover:not(:disabled){border-color:#f39c12;background:#fffdf5}
.opt-btn:disabled{cursor:default;opacity:.95}
.opt-btn.right{background:#eafaf1;border-color:#27ae60;color:#1e8449;font-weight:700}
.opt-btn.wrong{background:#fdedec;border-color:#e74c3c;color:#c0392b}
.q-feedback{margin-top:8px;font-weight:700;font-size:0.95rem}
.q-feedback.ok{color:#27ae60}
.q-feedback.no{color:#e74c3c}
.quiz-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.quiz-score{background:#eafaf1;border:2px solid #27ae60;color:#1e8449;
  padding:5px 14px;border-radius:16px;font-weight:700;font-size:0.9rem}
.key-btn{padding:5px 14px;border:2px solid #9b59b6;border-radius:16px;
  background:#fff;color:#8e44ad;font-weight:700;font-size:0.85rem;cursor:pointer}
.key-btn:hover{background:#f5eef8}
.showkey .opt-btn[data-correct="1"]{background:#eafaf1;border-color:#27ae60;
  color:#1e8449;font-weight:700}
.explanation{margin-top:8px;font-size:0.82rem;color:#666;font-style:italic}
.empty{text-align:center;padding:60px 20px;color:#999}
.empty .icon{font-size:3rem;margin-bottom:12px}

.continue-bar{background:#e8f8f5;border-bottom:2px solid #1abc9c;padding:10px 16px;
  display:none;align-items:center;gap:10px;flex-wrap:wrap;position:sticky;top:62px;z-index:99}
.continue-bar.show{display:flex}
.continue-bar button{padding:8px 14px;border:none;border-radius:18px;background:#16a085;
  color:#fff;font-weight:700;cursor:pointer;font-size:0.9rem}
.continue-bar .meta{font-size:0.85rem;color:#0e6655;flex:1}
.card-thumb{width:100%;height:120px;object-fit:cover;background:linear-gradient(135deg,#e8f8f5,#f5eef8);display:block}
.card-thumb-fallback{height:120px;display:flex;align-items:center;justify-content:center;
  font-size:2.6rem;background:linear-gradient(135deg,#e8f8f5,#f5eef8)}
.khelo-top{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0 16px;align-items:center}
.khelo-top .khelo-go{
  display:block;width:100%;box-sizing:border-box;
  padding:18px 20px;margin:8px 0;border:none;border-radius:16px;
  background:#8e44ad;color:#fff;font-weight:800;
  font-size:clamp(1.25rem,4.5vw,1.55rem);line-height:1.4;
  cursor:pointer;min-height:64px;text-align:center;
  white-space:normal;word-break:break-word;
}
.khelo-go.secondary{background:#7f8c8d}
.khelo-top{display:flex;flex-direction:column;gap:12px;margin:12px 0;width:100%}
.khelo-top .hint{font-size:clamp(1rem,3.5vw,1.15rem);line-height:1.45;color:#555}
.khelo-top .hint{font-size:clamp(0.95rem,3vw,1.05rem);color:#6c3483}
.khelo-frame-wrap{margin:12px 0 18px;scroll-margin-top:12px}
.khelo-badge{padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:800;
  background:#8e44ad;color:#fff;letter-spacing:.02em}
.tag.has-interactive{background:#8e44ad;color:#fff;font-weight:700}

html{ -webkit-text-size-adjust:100%; }
body{ overflow-x:hidden; }
.header{ padding: clamp(14px, 4vw, 24px); }
.header h1{ font-size: clamp(1.25rem, 5vw, 1.8rem); }
.controls{ padding: 12px 12px 10px; gap:8px; }
.search{ width:100%; min-width:0; font-size:16px; /* prevent iOS zoom */ }
.grid{ padding:10px; grid-template-columns:repeat(auto-fill,minmax(min(100%,280px),1fr)); gap:10px; }
.card-thumb,.card-thumb-fallback{ height: clamp(90px, 28vw, 120px); }
.modal.open{ padding:8px; align-items:stretch; }
.modal-box{ max-width:100%; max-height:100vh; border-radius:12px; padding: clamp(14px, 4vw, 24px); margin:0; }
.modal-box iframe{ width:100% !important; height: min(70vh, 560px) !important; border:0; }
.opt-btn,.read-btn,.continue-bar button,.khelo-badge{ min-height:44px; }
.continue-bar{ top:0; }
@media(max-width:480px){
  .filters{ width:100%; }
  .filter-btn{ flex:1 1 auto; text-align:center; }
  .card-footer{ flex-wrap:wrap; }
}
@media(max-width:500px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header">
  <h1>📚 AI4Kids.pk — Lesson Bank</h1>
  <p>SNC Curriculum • Class 1-5 • 8 Subjects • __TOPIC_COUNT__ Topics • Roman Urdu</p>
</div>
<div class="controls">
  <input class="search" id="search" placeholder="Search... تلاش کریں (e.g. fractions, robot, grammar)" oninput="filterCards()">
  <div class="filters" id="gradeFilters">
    <button type="button" class="filter-btn active" data-grade="all" onclick="setFilter('grade','all',event)">All</button>
""")

for g in range(1, 6):
    lines.append(f'    <button type="button" class="filter-btn" data-grade="{g}" onclick="setFilter(\'grade\',\'{g}\',event)">Grade {g}</button>')

lines.append('  </div>\n  <div class="filters" id="subjFilters">')
lines.append('    <button type="button" class="filter-btn active" data-subj="all" onclick="setFilter(\'subj\',\'all\',event)">All subjects</button>')
for sk, sm in SUBJ_META.items():
    lines.append(f'    <button type="button" class="filter-btn" data-subj="{sk}" onclick="setFilter(\'subj\',\'{sk}\',event)">{sm["emoji"]} {sm["name"]}</button>')

lines.append(f"""  </div>
</div>
<div class="continue-bar" id="continueBar">
  <span class="meta" id="continueMeta">Continue where you left</span>
  <button type="button" id="continueBtn" onclick="continueLast()">▶️ Continue</button>
  <button type="button" onclick="clearContinue()" style="background:#95a5a6">Clear</button>
</div>
<div class="stats" id="stats">{len(all_topics)} topics found</div>
<div class="grid" id="grid">
""")

for i, t in enumerate(all_topics):
    lesson_short = t["lesson"][:200].replace('"', '&quot;').replace('\n', ' ') if t["lesson"] else ""
    lines.append(f"""<div class="card" 
  data-grade="{t['grade']}" data-subj="{t['subj_key']}"
  data-title="{esc(t['title'])}" data-desc="{esc(t['desc'])}"
  data-search="{esc(t['title'])} {esc(t['desc'])} {esc(t['subj_name'])} grade{t['grade']}"
  onclick="openModal({i})">
  <div class="card-thumb-wrap">
    {('<img class="card-thumb" alt="" src="data:'+t['thumb_mime']+';base64,'+t['thumb_b64']+'">') if t.get('thumb_b64') else ('<div class="card-thumb-fallback" style="background:linear-gradient(135deg,'+t['subj_color']+'33,'+t['subj_color']+'11)">'+t['subj_emoji']+'</div>')}
  </div>
  <div class="card-header" style="border-left:4px solid {t['subj_color']}">
    <span class="card-emoji">{t['subj_emoji']}</span>
    <div class="card-info">
      <h3>{esc(t['title'])}</h3>
      <div class="meta">{esc(t['subj_name'])}</div>
    </div>
    <span class="grade-badge" style="background:{t['subj_color']}">Grade {t['grade']}</span>
  </div>
  <div class="card-desc">{esc(t['desc'][:100])}</div>
  <div class="card-footer">
    {'<span class="tag has-lesson">📖 Lesson</span>' if t['lesson'] else '<span class="tag">No lesson</span>'}
    {'<span class="tag has-quiz">📝 ' + str(t['quiz_count']) + ' MCQs</span>' if t['quiz_count'] else ''}
    {'<span class="khelo-badge">🎮 Khelo</span>' if t.get('interactive_file') else ''}
  </div>
</div>""")

lines.append('</div>')
lines.append('<div class="empty" id="empty" style="display:none"><div class="icon">🔍</div><p>Koi topic nahi mila — search clear karein</p></div>')

# Modal
lines.append('<div class="modal" id="modal"><div class="modal-box">')
lines.append('<button class="modal-close" onclick="closeModal()">✕</button>')
lines.append('<div id="modal-content"></div>')
lines.append('</div></div>')
lines.append('''<div id="playStage" style="display:none;padding:8px 4px 24px">
  <button type="button" class="khelo-go secondary" id="playBackBtn" style="margin-bottom:12px">← Grid wapas</button>
  <h2 id="playTitle" style="margin:8px 0;font-size:clamp(1.4rem,5vw,1.9rem)"></h2>
  <p id="playMeta" class="meta"></p>
  <div class="read-bar" id="playReadBar" style="display:none">
    <button class="read-btn" id="playReadBtn" type="button">🔊 Sunlo</button>
    <span class="read-status" id="playReadStatus"></span>
  </div>
  <div class="lesson-text" id="playLesson" style="display:none"></div>
  <h3 style="margin:16px 0 8px;font-size:clamp(1.25rem,4vw,1.5rem)">🎮 App (grid ke bahar)</h3>
  <iframe id="playFrame" title="Khelo app" sandbox="allow-scripts allow-same-origin allow-forms"
    style="width:100%;height:min(75vh,720px);min-height:420px;border:2px solid #ddd;border-radius:14px;background:#fff"></iframe>
  <div id="playQuiz"></div>
</div>''')

# JS data + logic
# Embed interactives so KHELO can play in-place inside Lesson Bank (Streamlit parent nav is blocked)
for t in all_topics:
    t["interactive_b64"] = ""
    rel = t.get("interactive_file") or ""
    if rel:
        ip = Path(os.path.dirname(os.path.abspath(__file__))) / rel
        if ip.exists():
            t["interactive_b64"] = base64.b64encode(ip.read_bytes()).decode("ascii")

topics_json = json.dumps([{
    "grade": t["grade"],
    "sk": t["subj_key"],
    "subj": t["subj_name"],
    "emoji": t["subj_emoji"],
    "color": t["subj_color"],
    "title": t["title"],
    "desc": t["desc"],
    "lesson": t["lesson"],
    "questions": t["questions"],
    "interactive_file": t.get("interactive_file") or "",
    "interactive_label": t.get("interactive_label") or "",
    "interactive_b64": t.get("interactive_b64") or "",
} for t in all_topics], ensure_ascii=False)

lines.append(f"""<script>
const ALL = {topics_json};
let gf = 'all', sf = 'all';
if ('speechSynthesis' in window) {{ window.speechSynthesis.getVoices(); window.speechSynthesis.onvoiceschanged = function(){{ window.speechSynthesis.getVoices(); }}; }}

const LB_KEY = 'ai4kids_lb_last';

function decodeKheloB64(b64) {{
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder('utf-8').decode(bytes);
}}
function mountKhelo(b64) {{
  const fr = document.getElementById('kheloFrame');
  const st = document.getElementById('kheloStatus');
  if (!fr || !b64) return;
  try {{
    if (window.__kheloBlobUrl) {{
      try {{ URL.revokeObjectURL(window.__kheloBlobUrl); }} catch (e) {{}}
    }}
    const html = decodeKheloB64(b64);
    window.__kheloHtml = html;
    const blob = new Blob([html], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    window.__kheloBlobUrl = url;
    fr.onload = function() {{
      if (st) st.textContent = 'App ready — andar scroll karke khelo. Blank ho to \"nayi window\" dabayein.';
    }};
    fr.onerror = function() {{
      if (st) st.textContent = 'Embed block ho gaya. Purple button: nayi window mein kholo.';
    }};
    fr.removeAttribute('srcdoc');
    fr.src = url;
    // Also try srcdoc as secondary after a tick (some WebViews need it)
    setTimeout(function() {{
      try {{
        if (fr.contentDocument && fr.contentDocument.body && fr.contentDocument.body.childElementCount === 0) {{
          fr.srcdoc = html;
          if (st) st.textContent = 'srcdoc fallback use hua.';
        }}
      }} catch (e) {{
        /* cross-origin / sandbox — rely on blob or new window */
        if (st) st.textContent = 'Is browser mein embed limited hai — \"nayi window\" use karein.';
      }}
    }}, 600);
  }} catch (err) {{
    if (st) st.textContent = 'Load error: ' + err;
  }}
}}
function openKheloWindow() {{
  let html = window.__kheloHtml;
  if (!html && window.__kheloB64) {{
    try {{ html = decodeKheloB64(window.__kheloB64); window.__kheloHtml = html; }}
    catch (e) {{ alert('Interactive decode nahi hui'); return; }}
  }}
  if (!html) {{ alert('Interactive maujood nahi'); return; }}
  const w = window.open('', '_blank');
  if (!w) {{
    alert('Popup block hai — browser site ke liye popups allow karein, ya Yahan dikhao try karein.');
    return;
  }}
  w.document.open();
  w.document.write(html);
  w.document.close();
}}

function refreshContinue() {{
  const bar = document.getElementById('continueBar');
  const meta = document.getElementById('continueMeta');
  if (!bar || !meta) return;
  try {{
    const raw = localStorage.getItem(LB_KEY);
    if (!raw) {{ bar.classList.remove('show'); return; }}
    const d = JSON.parse(raw);
    if (d.i == null || !ALL[d.i]) {{ bar.classList.remove('show'); return; }}
    meta.textContent = 'Continue: ' + (d.emoji||'') + ' ' + d.title + ' (Grade ' + d.grade + ')';
    bar.classList.add('show');
  }} catch (e) {{ bar.classList.remove('show'); }}
}}
function continueLast() {{
  try {{
    const d = JSON.parse(localStorage.getItem(LB_KEY) || '{{}}');
    if (d.i != null) openModal(d.i);
  }} catch (e) {{}}
}}
function clearContinue() {{
  try {{ localStorage.removeItem(LB_KEY); }} catch (e) {{}}
  refreshContinue();
}}


function setFilter(type, val, event) {{
  if (event && typeof event.preventDefault === 'function') {{
    event.preventDefault();
    if (typeof event.stopPropagation === 'function') event.stopPropagation();
  }}
  val = String(val);
  if (type==='grade') {{
    gf = val;
    document.querySelectorAll('#gradeFilters .filter-btn').forEach(b => {{
      b.classList.toggle('active', String(b.dataset.grade)===gf);
    }});
  }} else {{
    sf = val;
    document.querySelectorAll('#subjFilters .filter-btn').forEach(b => {{
      b.classList.toggle('active', String(b.dataset.subj)===sf);
    }});
  }}
  filterCards();
}}

function filterCards() {{
  const q = (document.getElementById('search').value || '').toLowerCase();
  const cards = document.querySelectorAll('.card');
  let vis = 0;
  const gradeFilter = String(gf);
  const subjFilter = String(sf);
  cards.forEach(c => {{
    const gm = gradeFilter==='all' || String(c.dataset.grade)===gradeFilter;
    const sm = subjFilter==='all' || String(c.dataset.subj)===subjFilter;
    const qm = !q || (c.dataset.search || '').toLowerCase().includes(q);
    const show = gm && sm && qm;
    c.style.display = show ? '' : 'none';
    if (show) vis++;
  }});
  document.getElementById('stats').textContent = vis + ' topics found';
  document.getElementById('empty').style.display = vis ? 'none' : 'block';
}}

function wireFilters() {{
  document.querySelectorAll('#gradeFilters .filter-btn').forEach(b => {{
    b.setAttribute('type', 'button');
    b.addEventListener('click', function(e) {{
      setFilter('grade', b.getAttribute('data-grade') || 'all', e);
    }});
  }});
  document.querySelectorAll('#subjFilters .filter-btn').forEach(b => {{
    b.setAttribute('type', 'button');
    b.addEventListener('click', function(e) {{
      setFilter('subj', b.getAttribute('data-subj') || 'all', e);
    }});
  }});
}}
if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', wireFilters);
}} else {{
  wireFilters();
  refreshContinue();
}}

function openModal(i) {{
  const t = ALL[i];
  try {{
    localStorage.setItem('ai4kids_lb_last', JSON.stringify({{
      i: i, title: t.title, grade: t.grade, subj: t.subj, emoji: t.emoji, ts: Date.now()
    }}));
    refreshContinue();
  }} catch (e) {{}}

  let html = `<h2>${{t.emoji}} ${{t.title}}</h2>
  <p class="meta">${{t.subj}} • Grade ${{t.grade}} • ${{t.desc}}</p>`;

  // ONLY lesson + Sunlo inside grid/modal
  if (t.lesson) {{
    window.__lessonRaw = t.lesson;
    html += `<div class="read-bar">
      <button class="read-btn" id="readBtn" onclick="toggleRead()">🔊 Sunlo</button>
      <span class="read-status" id="readStatus"></span>
    </div>`;
    html += `<div class="lesson-text" id="lessonText">${{t.lesson.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`;
  }} else {{
    html += '<p style="color:#999;padding:10px;font-size:1.1rem">Lesson abhi available nahi hai.</p>';
  }}

  // After lesson text → close grid; App + Quiz stay OUTSIDE (playStage)
  html += `<div class="khelo-top">`;
  html += `<button type="button" class="khelo-go secondary" id="modalCloseBtn">✖️ Band karo — sirf modal</button>`;
  if (t.interactive_file) {{
    html += `<button type="button" class="khelo-go" id="kheloBelowBtn">🎮 KHELO — grid band, phir App + Quiz bahar</button>`;
    html += `<span class="hint">Pehle sabaq/Sunlo yahan. Phir KHELO: grid band hoga, App aur Quiz grid ke bahar milenge (connected).</span>`;
  }}
  html += `</div>`;

  document.getElementById('modal-content').innerHTML = html;
  const bClose = document.getElementById('modalCloseBtn');
  if (bClose) bClose.onclick = function() {{ closeModal(); }};
  if (t.interactive_file) {{
    const bK = document.getElementById('kheloBelowBtn');
    if (bK) bK.onclick = function() {{
      closeModal();
      openKheloBelow(t);
    }};
  }}
  document.getElementById('modal').classList.add('open');
}}

function b64ToUtf8(b64) {{
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder('utf-8').decode(bytes);
}}

function setBrowseVisible(show) {{
  ['search','gradeFilters','subjFilters','continueBar','stats','grid','empty'].forEach(function(id) {{
    const el = document.getElementById(id);
    if (!el) return;
    if (id === 'empty') {{
      if (show) return; // leave empty logic alone when showing browse
      el.style.display = 'none';
      return;
    }}
    el.style.display = show ? '' : 'none';
  }});
  // hide filter row parents if any
  const play = document.getElementById('playStage');
  if (play) play.style.display = show ? 'none' : 'block';
}}

function openKheloBelow(t) {{
  try {{ closeModal(); }} catch (e) {{}}
  if (!t || !t.interactive_b64) {{
    alert('Is topic ki app file nahi mili.');
    return;
  }}
  setBrowseVisible(false);
  const title = document.getElementById('playTitle');
  const meta = document.getElementById('playMeta');
  const lessonEl = document.getElementById('playLesson');
  const readBar = document.getElementById('playReadBar');
  const frame = document.getElementById('playFrame');
  const quizHost = document.getElementById('playQuiz');
  if (title) title.textContent = (t.emoji || '') + ' ' + t.title;
  if (meta) meta.textContent = (t.subj || '') + ' • Grade ' + t.grade + ' • ' + (t.desc || '');

  // 1) Lesson + Sunlo
  if (t.lesson) {{
    window.__lessonRaw = t.lesson;
    if (readBar) readBar.style.display = 'flex';
    if (lessonEl) {{
      lessonEl.style.display = 'block';
      lessonEl.textContent = t.lesson;
    }}
    const pr = document.getElementById('playReadBtn');
    if (pr) pr.onclick = function() {{ toggleRead(); }};
  }} else {{
    if (readBar) readBar.style.display = 'none';
    if (lessonEl) lessonEl.style.display = 'none';
  }}

  // 2) App in-place (blob iframe inside Lesson Bank — no Streamlit parent needed)
  try {{
    if (frame._blobUrl) {{ URL.revokeObjectURL(frame._blobUrl); frame._blobUrl = null; }}
    const html = b64ToUtf8(t.interactive_b64);
    const blob = new Blob([html], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    frame._blobUrl = url;
    frame.src = url;
  }} catch (e) {{
    frame.replaceWith(frame.cloneNode(false));
    const f2 = document.getElementById('playFrame');
    try {{
      const html = b64ToUtf8(t.interactive_b64);
      f2.srcdoc = html;
    }} catch (e2) {{
      alert('App load nahi hui: ' + e2);
    }}
  }}

  // 3) Quiz under app
  if (quizHost) {{
    quizHost.innerHTML = '';
    if (t.questions && t.questions.length) {{
      window.__curQuestions = t.questions;
      __score = 0; __answered = 0; __keyShown = false;
      let qhtml = `<div class="quiz-section"><h3>📝 Quiz — ${{t.questions.length}} sawaal (app ke baad)</h3>
        <div class="quiz-head">
          <span class="quiz-score" id="quizScore">0 / ${{t.questions.length}} sahi</span>
          <button class="key-btn" onclick="toggleKey()" id="keyBtn">🔑 Ustaad: jawab dikhao</button>
        </div>`;
      t.questions.forEach((q,qi) => {{
        qhtml += `<div class="question" id="qbox${{qi}}" data-done="0">
          <p>Q${{qi+1}}: ${{(q.q||'').replace(/</g,'&lt;')}}</p>`;
        ['a','b','c','d'].forEach(opt => {{
          if (!q[opt]) return;
          const isRight = q.correct===opt;
          qhtml += `<button class="opt-btn" data-opt="${{opt}}" data-correct="${{isRight?1:0}}"
                     onclick="answerQ(${{qi}},'${{opt}}')">
            ${{opt.toUpperCase()}}) ${{(q[opt]||'').replace(/</g,'&lt;')}}
          </button>`;
        }});
        qhtml += `<div class="q-feedback" id="fb${{qi}}"></div>`;
        if (q.explanation) qhtml += `<div class="explanation" id="ex${{qi}}" style="display:none">💡 ${{q.explanation.replace(/</g,'&lt;')}}</div>`;
        qhtml += '</div>';
      }});
      qhtml += '</div>';
      quizHost.innerHTML = qhtml;
    }}
  }}

  window.scrollTo(0, 0);
  const back = document.getElementById('playBackBtn');
  if (back) back.onclick = function() {{
    try {{
      const f = document.getElementById('playFrame');
      if (f && f._blobUrl) {{ URL.revokeObjectURL(f._blobUrl); f._blobUrl = null; }}
      if (f) f.src = 'about:blank';
    }} catch (e) {{}}
    setBrowseVisible(true);
    // restore empty/grid display via existing filter render if any
    try {{ if (typeof filterCards === 'function') filterCards(); }} catch (e) {{}}
    const g = document.getElementById('grid');
    if (g) g.style.display = '';
    const st = document.getElementById('stats');
    if (st) st.style.display = '';
  }};
}}

function closeModal() {{
  stopRead();
  document.getElementById('modal').classList.remove('open');
}}

// ---- Interactive quiz: kid taps an option, gets instant feedback ----
let __score = 0, __answered = 0, __keyShown = false;

function answerQ(qi, opt) {{
  const q = window.__curQuestions[qi];
  const box = document.getElementById('qbox' + qi);
  if (!box || box.dataset.done === '1') return;   // one attempt per question
  box.dataset.done = '1';
  const correct = q.correct;
  box.querySelectorAll('.opt-btn').forEach(b => {{
    b.disabled = true;
    if (b.dataset.opt === correct) b.classList.add('right');
    else if (b.dataset.opt === opt) b.classList.add('wrong');
  }});
  const fb = document.getElementById('fb' + qi);
  if (opt === correct) {{
    fb.className = 'q-feedback ok';
    fb.textContent = '✅ Sahi jawab! Shabash!';
    __score++;
  }} else {{
    fb.className = 'q-feedback no';
    fb.textContent = '❌ Koshish acchi thi — sahi jawab: ' + correct.toUpperCase();
  }}
  const ex = document.getElementById('ex' + qi);
  if (ex) ex.style.display = 'block';             // explain only AFTER answering
  __answered++;
  updateScore();
}}

function updateScore() {{
  const el = document.getElementById('quizScore');
  if (!el || !window.__curQuestions) return;
  const total = window.__curQuestions.length;
  el.textContent = __score + ' / ' + total + ' sahi';
  if (__answered === total) {{
    el.textContent += (__score === total) ? '  🎉 Sab sahi!' : '  — shabash!';
  }}
}}

function toggleKey() {{
  const sec = document.getElementById('quizSection');
  const btn = document.getElementById('keyBtn');
  if (!sec) return;
  __keyShown = !__keyShown;
  sec.classList.toggle('showkey', __keyShown);
  btn.textContent = __keyShown ? '🔑 Teacher: jawab chupao' : '🔑 Ustaad: jawab dikhao';
}}

// ---- Read-aloud (Sunlo) with live word highlight ----
let __reading = false, __wordSpans = [];
function cleanForSpeech(s) {{
  if (!s) return '';
  let out = String(s);
  out = out.replace(/^#+\\s*/gm, '');
  out = out.replace(/^[-*]\\s+/gm, '');
  out = out.replace(/\\*\\*?/g, '');
  out = out.replace(/`+/g, '');
  out = out.replace(/\\bAI\\b/g, 'A I');
  out = out.replace(/\\b3D\\b/g, 'three D');
  out = out.replace(/\\bHOOK\\b/gi, 'Shuru. ');
  out = out.replace(/\\bSHURU\\b/gi, 'Shuru. ');
  out = out.replace(/\\bSAMJHAO\\b/gi, 'Samjhao. ');
  out = out.replace(/\\bMISAAL\\b/gi, 'Misaal. ');
  out = out.replace(/\\bKARO\\b/gi, 'Karo. ');
  out = out.replace(/\\bSAWAAL\\b/gi, 'Sawaal. ');
  out = out.replace(/\\n+/g, '. ');
  out = out.replace(/\\s+/g, ' ').trim();
  return out;
}}
function escHtml(s) {{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
function tokenizeRead(text) {{
  let html='', spans=[]; const re=/(\\s+)|(\\S+)/g; let m;
  while ((m=re.exec(text))!==null) {{
    if (m[1]) {{ html += m[1]; }}
    else {{ const s=m.index, e=s+m[2].length;
      html += '<span class="rw">'+escHtml(m[2])+'</span>';
      spans.push({{start:s, end:e, el:null}}); }}
  }}
  return {{html:html, spans:spans}};
}}
function pickVoice() {{
  const voices = window.speechSynthesis.getVoices() || [];
  const score = (v) => {{
    const n = ((v.lang||'') + ' ' + (v.name||'')).toLowerCase();
    let s = 0;
    if (n.includes('ur-pk') || n.includes('ur_pk')) s += 100;
    if (n.includes('urdu')) s += 90;
    if (n.includes('hi-in') || n.includes('hindi')) s += 70;
    if (n.includes('google') && (n.includes('हिन्दी') || n.includes('hindi') || n.includes('urdu'))) s += 20;
    if (n.includes('female') || n.includes('zira') || n.includes('neural')) s += 5;
    return s;
  }};
  let best = null, bestS = -1;
  for (const v of voices) {{
    const s = score(v);
    if (s > bestS) {{ bestS = s; best = v; }}
  }}
  return best;
}}
function toggleRead() {{ if (__reading) stopRead(); else startRead(); }}
function startRead() {{
  const st = document.getElementById('readStatus');
  if (!('speechSynthesis' in window)) {{ if(st) st.textContent='Awaaz support nahi'; return; }}
  const clean = cleanForSpeech(window.__lessonRaw);
  const el = document.getElementById('lessonText');
  const tk = tokenizeRead(clean);
  el.innerHTML = tk.html; __wordSpans = tk.spans;
  const nodes = el.querySelectorAll('.rw');
  for (let j=0;j<__wordSpans.length;j++) __wordSpans[j].el = nodes[j];
  const u = new SpeechSynthesisUtterance(clean);
  u.lang=(pickVoice()&&(pickVoice().lang||'').toLowerCase().startsWith('ur'))?'ur-PK':'hi-IN'; u.rate=0.82; u.pitch=1.0; const v=pickVoice(); if(v) u.voice=v;
  u.onboundary = function(e) {{ if (e.name && e.name!=='word') return; highlightAt(e.charIndex); }};
  u.onend = function() {{ stopRead(); }};
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
  __reading = true;
  const b=document.getElementById('readBtn'); if(b) b.textContent='⏸ Ruko';
  if(st) st.textContent='▶ parh raha hoon...';
}}
function stopRead() {{
  try {{ window.speechSynthesis.cancel(); }} catch(e) {{}}
  __reading = false;
  const b=document.getElementById('readBtn'); if(b) b.textContent='🔊 Sunlo';
  const st=document.getElementById('readStatus'); if(st) st.textContent='';
  document.querySelectorAll('.rw.reading').forEach(x=>x.classList.remove('reading'));
}}
function highlightAt(idx) {{
  let cur=null;
  for (const w of __wordSpans) {{ if (idx>=w.start && idx<w.end) {{ cur=w; break; }} }}
  if (!cur) for (const w of __wordSpans) {{ if (w.start>=idx) {{ cur=w; break; }} }}
  document.querySelectorAll('.rw.reading').forEach(x=>x.classList.remove('reading'));
  if (cur && cur.el) {{ cur.el.classList.add('reading');
    cur.el.scrollIntoView({{block:'center', behavior:'smooth'}}); }}
}}

document.getElementById('modal').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});

document.addEventListener('keydown', e => {{ if (e.key==='Escape') closeModal(); }});
</script>
</body></html>""")

html_out = "\n".join(lines).replace("__TOPIC_COUNT__", str(len(all_topics)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html_out)

size = os.path.getsize(OUT)
print(f"Done! {OUT} — {size:,} bytes ({len(all_topics)} topics)")
