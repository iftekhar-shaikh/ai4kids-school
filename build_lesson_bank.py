"""
Build lesson_bank.html from KB JSON files
Run: python build_lesson_bank.py
"""
import json, os

KB_DIR = "kb"
OUT = "lesson_bank.html"

SUBJ_META = {
    "ai":       {"name": "AI & Technology", "emoji": "🤖", "color": "#1abc9c"},
    "math":     {"name": "Hisaab (Math)",   "emoji": "🔢", "color": "#27ae60"},
    "english":  {"name": "English",          "emoji": "📚", "color": "#9b59b6"},
    "science":  {"name": "General Science",  "emoji": "🔬", "color": "#e74c3c"},
    "robotics": {"name": "Automation & Robotics","emoji":"⚙️","color":"#f39c12"},
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
.header h1{font-size:1.8rem;margin-bottom:4px}
.header p{font-size:0.95rem;opacity:0.9}
.controls{background:#fff;padding:14px 20px;border-bottom:2px solid #eee;
  display:flex;flex-wrap:wrap;gap:10px;align-items:center;position:sticky;top:0;z-index:100}
.search{flex:1;min-width:200px;padding:8px 14px;border:2px solid #ddd;
  border-radius:20px;font-size:0.95rem;outline:none}
.search:focus{border-color:#27ae60}
.filters{display:flex;flex-wrap:wrap;gap:6px}
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
.card-info h3{font-size:1rem;margin:0}
.card-info .meta{font-size:0.78rem;color:#888;margin-top:2px}
.grade-badge{padding:2px 8px;border-radius:10px;font-size:0.75rem;
  font-weight:700;color:#fff;margin-left:auto;flex-shrink:0}
.card-desc{padding:0 16px 10px;font-size:0.85rem;color:#666}
.card-footer{padding:8px 16px;background:#f9f9f9;border-top:1px solid #eee;
  display:flex;gap:8px;align-items:center}
.tag{padding:2px 8px;border-radius:10px;font-size:0.75rem;background:#eee;color:#555}
.tag.has-lesson{background:#e8f8f5;color:#16a085}
.tag.has-quiz{background:#fef9e7;color:#d68910}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,.5);z-index:200;overflow-y:auto}
.modal.open{display:flex;align-items:flex-start;justify-content:center;padding:20px}
.modal-box{background:#fff;border-radius:16px;width:100%;max-width:760px;
  max-height:90vh;overflow-y:auto;padding:24px;position:relative;margin:auto}
.modal-close{position:absolute;top:14px;right:16px;font-size:1.5rem;
  cursor:pointer;color:#999;background:none;border:none;line-height:1}
.modal-close:hover{color:#333}
.modal h2{font-size:1.3rem;margin-bottom:4px}
.modal .meta{font-size:0.85rem;color:#888;margin-bottom:16px}
.lesson-text{white-space:pre-wrap;font-size:0.92rem;line-height:1.7;
  background:#fafafa;border-radius:10px;padding:16px;border:1px solid #eee}
.read-bar{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.read-btn{padding:9px 20px;border:none;border-radius:22px;background:#8e44ad;
  color:#fff;font-size:1.05rem;font-weight:700;cursor:pointer}
.read-btn:hover{background:#7d3c98}
.read-status{color:#8e44ad;font-weight:600;font-size:0.9rem}
.rw.reading{background:#ffe08a;border-radius:4px;box-shadow:0 0 0 2px #ffe08a}
.quiz-section{margin-top:20px}
.quiz-section h3{margin-bottom:12px;color:#d68910}
.question{background:#fffbea;border-radius:10px;padding:14px;margin-bottom:10px;
  border-left:4px solid #f39c12}
.question p{font-weight:600;margin-bottom:8px}
.option{padding:4px 0;font-size:0.9rem}
.option.correct{color:#27ae60;font-weight:700}
/* --- interactive quiz --- */
.opt-btn{display:block;width:100%;text-align:left;padding:11px 14px;margin:7px 0;
  border:2px solid #ddd;border-radius:12px;background:#fff;cursor:pointer;
  font-size:1rem;font-family:inherit;color:#2c3e50;transition:all .15s}
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
@media(max-width:500px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header">
  <h1>📚 AI4Kids.pk — Lesson Bank</h1>
  <p>SNC Curriculum • Class 1-5 • 5 Subjects • 150 Topics • Roman Urdu</p>
</div>
<div class="controls">
  <input class="search" id="search" placeholder="Search... تلاش کریں (e.g. fractions, robot, grammar)" oninput="filterCards()">
  <div class="filters" id="gradeFilters">
    <button class="filter-btn active" data-grade="all" onclick="setFilter('grade','all')">All</button>
""")

for g in range(1, 6):
    lines.append(f'    <button class="filter-btn" data-grade="{g}" onclick="setFilter(\'grade\',\'{g}\')">Grade {g}</button>')

lines.append('  </div>\n  <div class="filters" id="subjFilters">')
lines.append('    <button class="filter-btn active" data-subj="all" onclick="setFilter(\'subj\',\'all\')">All subjects</button>')
for sk, sm in SUBJ_META.items():
    lines.append(f'    <button class="filter-btn" data-subj="{sk}" onclick="setFilter(\'subj\',\'{sk}\')">{sm["emoji"]} {sm["name"]}</button>')

lines.append(f"""  </div>
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
  </div>
</div>""")

lines.append('</div>')
lines.append('<div class="empty" id="empty" style="display:none"><div class="icon">🔍</div><p>Koi topic nahi mila — search clear karein</p></div>')

# Modal
lines.append('<div class="modal" id="modal"><div class="modal-box">')
lines.append('<button class="modal-close" onclick="closeModal()">✕</button>')
lines.append('<div id="modal-content"></div>')
lines.append('</div></div>')

# JS data + logic
topics_json = json.dumps([{
    "grade": t["grade"],
    "subj": t["subj_name"],
    "emoji": t["subj_emoji"],
    "color": t["subj_color"],
    "title": t["title"],
    "desc": t["desc"],
    "lesson": t["lesson"],
    "questions": t["questions"],
} for t in all_topics], ensure_ascii=False)

lines.append(f"""<script>
const ALL = {topics_json};
let gf = 'all', sf = 'all';

function setFilter(type, val) {{
  if (type==='grade') {{
    gf = val;
    document.querySelectorAll('#gradeFilters .filter-btn').forEach(b => b.classList.toggle('active', b.dataset.grade===val));
  }} else {{
    sf = val;
    document.querySelectorAll('#subjFilters .filter-btn').forEach(b => b.classList.toggle('active', b.dataset.subj===val));
  }}
  filterCards();
}}

function filterCards() {{
  const q = document.getElementById('search').value.toLowerCase();
  const cards = document.querySelectorAll('.card');
  let vis = 0;
  cards.forEach(c => {{
    const gm = gf==='all' || c.dataset.grade===gf;
    const sm = sf==='all' || c.dataset.subj===sf;
    const qm = !q || c.dataset.search.toLowerCase().includes(q);
    const show = gm && sm && qm;
    c.style.display = show ? '' : 'none';
    if (show) vis++;
  }});
  document.getElementById('stats').textContent = vis + ' topics found';
  document.getElementById('empty').style.display = vis ? 'none' : 'block';
}}

function openModal(i) {{
  const t = ALL[i];
  let html = `<h2>${{t.emoji}} ${{t.title}}</h2>
  <p class="meta">${{t.subj}} • Grade ${{t.grade}} • ${{t.desc}}</p>`;
  if (t.lesson) {{
    window.__lessonRaw = t.lesson;
    html += `<div class="read-bar">
      <button class="read-btn" id="readBtn" onclick="toggleRead()">🔊 Sunlo</button>
      <span class="read-status" id="readStatus"></span>
    </div>`;
    html += `<div class="lesson-text" id="lessonText">${{t.lesson.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`;
  }} else {{
    html += '<p style="color:#999;padding:10px">Lesson abhi available nahi hai.</p>';
  }}
  if (t.questions && t.questions.length) {{
    window.__curQuestions = t.questions;
    __score = 0; __answered = 0; __keyShown = false;
    html += `<div class="quiz-section" id="quizSection">
      <h3>📝 Quiz — ${{t.questions.length}} sawaal</h3>
      <div class="quiz-head">
        <span class="quiz-score" id="quizScore">0 / ${{t.questions.length}} sahi</span>
        <button class="key-btn" onclick="toggleKey()" id="keyBtn">🔑 Teacher: jawab dikhao</button>
      </div>`;
    t.questions.forEach((q,qi) => {{
      html += `<div class="question" id="qbox${{qi}}" data-done="0">
        <p>Q${{qi+1}}: ${{q.q.replace(/</g,'&lt;')}}</p>`;
      ['a','b','c','d'].forEach(opt => {{
        if (!q[opt]) return;
        const isRight = q.correct===opt;
        html += `<button class="opt-btn" data-opt="${{opt}}" data-correct="${{isRight?1:0}}"
                   onclick="answerQ(${{qi}},'${{opt}}')">
          ${{opt.toUpperCase()}}) ${{(q[opt]||'').replace(/</g,'&lt;')}}
        </button>`;
      }});
      html += `<div class="q-feedback" id="fb${{qi}}"></div>`;
      if (q.explanation) html += `<div class="explanation" id="ex${{qi}}" style="display:none">💡 ${{q.explanation.replace(/</g,'&lt;')}}</div>`;
      html += '</div>';
    }});
    html += '</div>';
  }}
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal').classList.add('open');
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
  btn.textContent = __keyShown ? '🔑 Teacher: jawab chupao' : '🔑 Teacher: jawab dikhao';
}}

// ---- Read-aloud (Sunlo) with live word highlight ----
let __reading = false, __wordSpans = [];
function cleanForSpeech(t) {{
  return (t||'').replace(/\\r/g,'').replace(/`/g,' ').replace(/[*_>#]/g,' ');
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
  const vs = window.speechSynthesis.getVoices()||[];
  return vs.find(v=>/(^|[^a-z])ur/i.test(v.lang)||/urdu/i.test(v.name))
      || vs.find(v=>/hi-?IN/i.test(v.lang)||/hindi/i.test(v.name)) || null;
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
  u.lang='hi-IN'; u.rate=0.9; const v=pickVoice(); if(v) u.voice=v;
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

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

size = os.path.getsize(OUT)
print(f"Done! {OUT} — {size:,} bytes ({len(all_topics)} topics)")
