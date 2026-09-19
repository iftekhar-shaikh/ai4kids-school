# -*- coding: utf-8 -*-
"""Build AI4Kids offline zip packs per class (Grade 1-5)."""
from __future__ import annotations
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK_DIR = ROOT / "packs"

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


def _quiz_list(t: dict):
    quiz = t.get("quiz")
    if isinstance(quiz, dict) and isinstance(quiz.get("questions"), list):
        return quiz["questions"]
    if isinstance(t.get("questions"), list):
        return t["questions"]
    return []


def load_topics(grade: int):
    rows = []
    gdir = ROOT / "kb" / f"grade_{grade}"
    if not gdir.exists():
        return rows
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
                "lesson": t.get("lesson") or "",
                "questions": _quiz_list(t),
                "file": rel,
            })
    return rows


def build_index(grade: int, topics) -> str:
    # Embed topic data (lessons included) — file:// safe, no fetch needed
    payload = []
    for i, t in enumerate(topics):
        qs = []
        for q in (t.get("questions") or [])[:5]:
            if not isinstance(q, dict):
                continue
            qs.append({
                "q": q.get("q") or q.get("question") or "",
                "a": q.get("a") or "",
                "b": q.get("b") or "",
                "c": q.get("c") or "",
                "d": q.get("d") or "",
                "correct": str(q.get("correct") or "a")[:1].lower(),
            })
        payload.append({
            "i": i,
            "sk": t["sk"],
            "subj": t["subj"],
            "emoji": t["emoji"],
            "title": t["title"],
            "desc": t["desc"],
            "lesson": t["lesson"],
            "file": t["file"],
            "questions": qs,
        })
    data_json = json.dumps(payload, ensure_ascii=False)
    # escape for script tag
    data_json = data_json.replace("<", "\\u003c")

    return f"""<!doctype html>
<html lang="ur"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI4Kids — Class {grade} Offline Pack</title>
<style>
:root{{--ink:#17252f;--muted:#526672;--paper:#fffdf7;--green:#27ae60;--green-deep:#1e8449;--teal:#1abc9c;--purple:#8e44ad;--yellow:#fff0b8;--red:#e74c3c;--font:'Segoe UI','Trebuchet MS',Tahoma,sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:var(--font);background:var(--paper);color:var(--ink);line-height:1.55;padding-bottom:48px}}
.header{{background:linear-gradient(135deg,var(--green),var(--teal));color:#fff;padding:22px 16px;text-align:center}}
.header h1{{margin:0 0 6px;font-size:clamp(1.4rem,5vw,2rem)}}
.trust{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding:10px 12px;margin:12px 16px;background:#eafaf1;border:2px solid var(--green);border-radius:14px}}
.pill{{background:#fff;border:2px solid var(--ink);border-radius:999px;padding:6px 12px;font-weight:800;font-size:.95rem}}
.wrap{{max-width:1000px;margin:0 auto;padding:8px 16px 24px}}
.note{{margin:0 0 14px;padding:12px;background:var(--yellow);border:2px solid var(--ink);border-radius:12px;font-weight:700}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.fbtn{{border:2px solid #ddd;background:#fff;border-radius:999px;padding:8px 14px;font-weight:800;cursor:pointer;min-height:44px}}
.fbtn.active{{background:var(--green);color:#fff;border-color:var(--green)}}
.subj{{margin:18px 0}}
.subj h2{{font-size:clamp(1.2rem,4vw,1.5rem);margin:0 0 10px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.card{{display:flex;flex-direction:column;gap:4px;text-align:left;background:#fff;border:3px solid #d9d2c5;border-radius:14px;padding:14px;min-height:88px;font-weight:800;cursor:pointer;font:inherit;color:inherit}}
.card:hover{{border-color:var(--green);background:#eafaf1}}
.card .d{{font-size:.9rem;color:var(--muted);font-weight:600}}
#browse.hidden,#play.hidden{{display:none}}
.back{{display:block;width:100%;margin:0 0 12px;padding:12px;font-weight:900;font-size:1.1rem;border:3px solid var(--ink);border-radius:14px;background:#fff;cursor:pointer;min-height:52px}}
.play-title{{font-size:clamp(1.4rem,5vw,1.9rem);margin:0 0 4px}}
.play-meta{{color:var(--muted);margin:0 0 14px;font-weight:700}}
.read-btn,.khelo-btn{{display:block;width:100%;margin:8px 0;padding:14px;font-weight:900;font-size:1.15rem;border:none;border-radius:14px;cursor:pointer;min-height:54px;color:#fff}}
.read-btn{{background:var(--purple)}}
.khelo-btn{{background:var(--green);border:3px solid var(--green-deep)}}
.khelo-btn:disabled{{opacity:.5;cursor:not-allowed}}
.lesson{{background:#111;color:#f5f5f5;border-radius:14px;border:2px solid #333;padding:18px 16px;font-size:clamp(1.15rem,4vw,1.35rem);line-height:1.85;white-space:pre-wrap;min-height:140px;margin:8px 0 14px}}
.frame-wrap{{border:3px solid var(--ink);border-radius:14px;overflow:hidden;background:#fff;margin:10px 0}}
#appFrame{{width:100%;height:min(75vh,720px);min-height:420px;border:0;display:block}}
.quiz h3{{margin:18px 0 10px}}
.q{{margin:0 0 16px}}
.q p{{font-weight:900;font-size:1.15rem}}
.opt{{display:block;width:100%;text-align:left;margin:6px 0;padding:12px;border:2px solid #d9d2c5;border-radius:12px;background:#fff;font-weight:700;cursor:pointer;min-height:48px}}
.opt.right{{border-color:var(--green);background:#e6f4eb}}
.opt.wrong{{border-color:var(--red);background:#f9e6e1}}
.status{{font-size:.95rem;color:var(--muted);min-height:1.2em}}
</style></head><body>
<div class="header"><h1>📚 AI4Kids — Class {grade} Offline</h1>
<p>Sabaq + Sunlo → Khelo app → Quiz</p></div>
<div class="trust" role="note" style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding:10px 12px;margin:12px 16px;background:#eafaf1;border:2px solid var(--green);border-radius:14px">
<b style="color:#1e8449">Parents ke liye</b>
<span class="pill">🛡️ Safe for kids</span>
<span class="pill">📶 Offline</span>
<span class="pill">🔓 Bina login</span></div>
<div class="wrap">
<p class="note">Order online jaisa: pehle <b>Sabaq + Sunlo</b>, phir <b>Khelo</b> app, phir quiz.</p>

<div id="browse">
  <div class="filters" id="filters"></div>
  <div id="subjects"></div>
</div>

<div id="play" class="hidden">
  <button type="button" class="back" id="backBtn">⬅️ Wapas list</button>
  <h2 class="play-title" id="playTitle"></h2>
  <p class="play-meta" id="playMeta"></p>
  <h3>📖 Sabaq</h3>
  <button type="button" class="read-btn" id="sunloBtn">🔊 Sunlo — sabaq suno</button>
  <div class="status" id="sunloStatus"></div>
  <div class="lesson" id="lessonBox"></div>
  <h3>🎮 Khelo — app</h3>
  <button type="button" class="khelo-btn" id="kheloBtn">🎮 KHELO — app chalao</button>
  <div class="frame-wrap" id="frameWrap" style="display:none">
    <iframe id="appFrame" title="Khelo app"></iframe>
  </div>
  <div class="quiz" id="quizBox"></div>
</div>
</div>
<script>
const ALL = {data_json};
let skFilter = 'all';
let speaking = false;

function cleanSpeech(s){{
  if(!s) return '';
  return String(s).replace(/^#+\\s*/gm,'').replace(/^[-*]\\s+/gm,'')
    .replace(/\\*\\*?/g,'').replace(/`+/g,'')
    .replace(/\\bHOOK\\b/gi,'Shuru. ').replace(/\\bSAMJHAO\\b/gi,'Samjhao. ')
    .replace(/\\bMISAAL\\b/gi,'Misaal. ').replace(/\\bKARO\\b/gi,'Karo. ')
    .replace(/\\bSAWAAL\\b/gi,'Sawaal. ')
    .replace(/\\n+/g,'. ').replace(/\\s+/g,' ').trim();
}}
function pickVoice(){{
  const vs = speechSynthesis.getVoices()||[];
  let best=null, bestS=-1;
  for (const v of vs){{
    const n=((v.lang||'')+' '+(v.name||'')).toLowerCase();
    let s=0;
    if(n.includes('ur')) s+=100;
    if(n.includes('hindi')||n.includes('hi-in')) s+=70;
    if(s>bestS){{bestS=s;best=v;}}
  }}
  return best;
}}
function sunlo(text){{
  const st=document.getElementById('sunloStatus');
  if(!('speechSynthesis' in window)){{ if(st) st.textContent='Awaaz support nahi'; return; }}
  if(speaking){{ speechSynthesis.cancel(); speaking=false; if(st) st.textContent='Roka'; return; }}
  const u=new SpeechSynthesisUtterance(cleanSpeech(text));
  const v=pickVoice();
  if(v){{ u.voice=v; u.lang=((v.lang||'').toLowerCase().startsWith('ur'))?'ur-PK':'hi-IN'; }}
  else u.lang='hi-IN';
  u.rate=0.82; u.pitch=1;
  u.onend=function(){{ speaking=false; if(st) st.textContent='Mukammal'; }};
  speaking=true; if(st) st.textContent='Bol raha hai…';
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}}
if('speechSynthesis' in window){{ try{{ speechSynthesis.getVoices(); }}catch(e){{}} }}

function renderBrowse(){{
  const host=document.getElementById('subjects');
  const filters=document.getElementById('filters');
  const keys=['all',...new Set(ALL.map(t=>t.sk))];
  filters.innerHTML='';
  keys.forEach(k=>{{
    const b=document.createElement('button');
    b.type='button'; b.className='fbtn'+(skFilter===k?' active':'');
    b.textContent = k==='all'?'All': (ALL.find(t=>t.sk===k)||{{}}).subj || k;
    b.onclick=()=>{{ skFilter=k; renderBrowse(); }};
    filters.appendChild(b);
  }});
  const by={{}};
  ALL.forEach(t=>{{ if(skFilter!=='all' && t.sk!==skFilter) return; (by[t.sk]=by[t.sk]||[]).push(t); }});
  let html='';
  Object.keys(by).forEach(sk=>{{
    const list=by[sk]; const emoji=list[0].emoji; const subj=list[0].subj;
    html+=`<section class="subj"><h2>${{emoji}} ${{subj}}</h2><div class="grid">`;
    list.forEach(t=>{{
      html+=`<button type="button" class="card" data-i="${{t.i}}"><span class="t">${{emoji}} ${{t.title}}</span><span class="d">${{t.desc||''}}</span></button>`;
    }});
    html+=`</div></section>`;
  }});
  host.innerHTML=html||'<p>Is filter mein topic nahi.</p>';
  host.querySelectorAll('.card').forEach(btn=>{{
    btn.onclick=()=>openTopic(+btn.getAttribute('data-i'));
  }});
}}

function openTopic(i){{
  const t=ALL.find(x=>x.i===i); if(!t) return;
  try{{ speechSynthesis.cancel(); }}catch(e){{}}
  speaking=false;
  document.getElementById('browse').classList.add('hidden');
  document.getElementById('play').classList.remove('hidden');
  document.getElementById('playTitle').textContent=(t.emoji||'')+' '+t.title;
  document.getElementById('playMeta').textContent=(t.subj||'')+' · Class {grade} · '+(t.desc||'');
  document.getElementById('lessonBox').textContent=t.lesson||'Lesson text abhi nahi.';
  document.getElementById('sunloStatus').textContent='';
  document.getElementById('sunloBtn').onclick=()=>sunlo(t.lesson||t.title);
  const fw=document.getElementById('frameWrap');
  const frame=document.getElementById('appFrame');
  fw.style.display='none'; frame.src='about:blank';
  const kb=document.getElementById('kheloBtn');
  if(t.file){{
    kb.disabled=false; kb.textContent='🎮 KHELO — app chalao';
    kb.onclick=()=>{{
      fw.style.display='block';
      frame.src=t.file;
      fw.scrollIntoView({{behavior:'smooth'}});
    }};
  }} else {{
    kb.disabled=true; kb.textContent='App abhi nahi';
    kb.onclick=null;
  }}
  // Quiz after app section
  const qb=document.getElementById('quizBox');
  qb.innerHTML='';
  if(t.questions && t.questions.length){{
    let h=`<h3>📝 Quiz — ${{t.questions.length}} sawaal (app ke baad)</h3>`;
    t.questions.forEach((q,qi)=>{{
      h+=`<div class="q" id="qq${{qi}}"><p>Q${{qi+1}}. ${{(q.q||'').replace(/</g,'&lt;')}}</p>`;
      ['a','b','c','d'].forEach(L=>{{
        if(!q[L]) return;
        h+=`<button type="button" class="opt" data-q="${{qi}}" data-opt="${{L}}">${{L.toUpperCase()}}) ${{String(q[L]).replace(/</g,'&lt;')}}</button>`;
      }});
      h+=`</div>`;
    }});
    qb.innerHTML=h;
    qb.querySelectorAll('.opt').forEach(btn=>{{
      btn.onclick=()=>{{
        const qi=+btn.getAttribute('data-q');
        const opt=btn.getAttribute('data-opt');
        const q=t.questions[qi];
        const box=document.getElementById('qq'+qi);
        box.querySelectorAll('.opt').forEach(o=>{{ o.classList.remove('right','wrong'); o.disabled=true; }});
        if(opt===q.correct) btn.classList.add('right');
        else {{
          btn.classList.add('wrong');
          const right=box.querySelector('.opt[data-opt="'+q.correct+'"]');
          if(right) right.classList.add('right');
        }}
      }};
    }});
  }}
  window.scrollTo(0,0);
}}

document.getElementById('backBtn').onclick=()=>{{
  try{{ speechSynthesis.cancel(); }}catch(e){{}}
  document.getElementById('appFrame').src='about:blank';
  document.getElementById('frameWrap').style.display='none';
  document.getElementById('play').classList.add('hidden');
  document.getElementById('browse').classList.remove('hidden');
}};
renderBrowse();
</script>
</body></html>
"""


def zip_path(grade: int) -> Path:
    return PACK_DIR / f"ai4kids-grade{grade}-offline.zip"


def build_zip(grade: int = 1):
    grade = int(grade)
    if grade < 1 or grade > 5:
        raise ValueError("grade must be 1-5")
    PACK_DIR.mkdir(exist_ok=True)
    topics = load_topics(grade)
    missing = []
    files_added = 0
    out = zip_path(grade)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("index.html", build_index(grade, topics))
        z.writestr(
            "README-UR.txt",
            f"AI4Kids Class {grade} Offline Pack\n"
            "1) Zip extract karo\n"
            "2) index.html Chrome/Edge mein kholo\n"
            "3) Topic → Sabaq + Sunlo → KHELO → Quiz\n"
            "Login nahi chahiye. WhatsApp: 0337 1468899\n",
        )
        gdir = ROOT / "kb" / f"grade_{grade}"
        if gdir.exists():
            for p in gdir.glob("*.json"):
                z.write(p, arcname=f"kb/grade_{grade}/{p.name}")
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
        "grade": grade,
        "zip": str(out),
        "bytes": out.stat().st_size,
        "mb": round(out.stat().st_size / 1e6, 2),
        "topics": len(topics),
        "files": files_added,
        "missing": missing,
        "has_lessons": sum(1 for t in topics if t.get("lesson")),
    }


def build_all():
    return [build_zip(g) for g in range(1, 6)]


if __name__ == "__main__":
    for info in build_all():
        print(info)
