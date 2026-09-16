"""
AI4Kids - Device Locked Access Codes
=====================================
Ek code = ek device. Pehli baar jis device pe use hua, wahin lock ho jata hai.

Install:
    pip install streamlit-js-eval supabase
"""

import hashlib
import secrets
import streamlit as st
from datetime import datetime, timezone
from streamlit_js_eval import streamlit_js_eval

# ---------------------------------------------------------------- CONFIG
LS_KEY = "ai4kids_device_id_v1"   # localStorage key
STRICT_MODE = True                # True = admin hi reset kar sakta hai
MAX_RESETS = 3

MASTER_HASH = None                # runtime pe st.secrets se aata hai


def _master_hash():
    global MASTER_HASH
    if MASTER_HASH is None:
        try:
            MASTER_HASH = str(st.secrets.get("MASTER_KEY_HASH", "")).strip()
        except Exception:
            MASTER_HASH = ""
    return MASTER_HASH


def is_master(code: str) -> bool:
    """Master key device lock ko bypass karti hai - sirf teacher/owner ke liye."""
    h = _master_hash()
    if not h:
        return False
    return secrets.compare_digest(
        hashlib.sha256((code or "").strip().encode()).hexdigest(), h
    )


# ---------------------------------------------------------------- SUPABASE
from supabase import create_client


def is_configured() -> bool:
    """Secrets set hain ya nahi - na hon to purana password gate chalega."""
    try:
        return bool(st.secrets.get("SUPABASE_URL")) and \
               bool(st.secrets.get("SUPABASE_SERVICE_KEY"))
    except Exception:
        return False


@st.cache_resource
def get_sb():
    return create_client(
        str(st.secrets["SUPABASE_URL"]).strip(),
        str(st.secrets["SUPABASE_SERVICE_KEY"]).strip(),
    )


# ---------------------------------------------------------------- DEVICE IDENTITY
_FP_JS = """(function(){
  var n = navigator, s = screen;
  var c = '';
  try {
    var cv = document.createElement('canvas');
    var ctx = cv.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = "14px 'Arial'";
    ctx.fillStyle = '#f60';
    ctx.fillRect(0,0,62,20);
    ctx.fillStyle = '#069';
    ctx.fillText('ai4kids', 2, 2);
    c = cv.toDataURL().slice(-64);
  } catch(e) { c = 'nocanvas'; }
  return [
    n.userAgent, n.language, n.platform || '',
    n.hardwareConcurrency || 0, n.maxTouchPoints || 0,
    s.width + 'x' + s.height, s.colorDepth,
    Intl.DateTimeFormat().resolvedOptions().timeZone, c
  ].join('|');
})()"""


def _read_or_create_uuid():
    """localStorage se device UUID parhta hai; na ho to naya bana ke save karta hai."""
    existing = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{LS_KEY}')",
        key="ai4k_read_uuid",
    )
    if existing:
        return existing

    if "ai4k_pending_uuid" not in st.session_state:
        new_id = secrets.token_hex(16)
        st.session_state["ai4k_pending_uuid"] = new_id
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('{LS_KEY}', '{new_id}') || '{new_id}'",
            key="ai4k_write_uuid",
        )
    return st.session_state.get("ai4k_pending_uuid")


def get_device_identity():
    """(device_uuid, fingerprint_hash). None ho to page abhi load ho raha hai."""
    raw_fp = streamlit_js_eval(js_expressions=_FP_JS, key="ai4k_fp")
    dev_uuid = _read_or_create_uuid()
    if not raw_fp or not dev_uuid:
        return None, None
    return dev_uuid, hashlib.sha256(raw_fp.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- VERIFY
OK           = "OK"
BAD_CODE     = "BAD_CODE"
BLOCKED      = "BLOCKED"
EXPIRED      = "EXPIRED"
WRONG_DEVICE = "WRONG_DEVICE"


def _log(code, dev_uuid, fp_hash, result):
    """Har koshish ka record - sharing pakadne ke liye."""
    try:
        get_sb().table("access_log").insert({
            "code": code, "device_uuid": dev_uuid,
            "fingerprint": fp_hash, "result": result,
        }).execute()
    except Exception:
        pass


def verify_code(code: str, dev_uuid: str, fp_hash: str):
    """
    Return: (status, row_or_None)
      1. device_uuid khali  -> pehli baar, bind kar do
      2. UUID match         -> allow
      3. UUID naya lekin fingerprint match -> wohi device, re-bind
      4. warna              -> reject
    """
    sb = get_sb()
    code = (code or "").strip().upper()
    if not code:
        return BAD_CODE, None

    res = sb.table("access_codes").select("*").eq("code", code).limit(1).execute()
    if not res.data:
        _log(code, dev_uuid, fp_hash, BAD_CODE)
        return BAD_CODE, None

    row = res.data[0]
    now = datetime.now(timezone.utc).isoformat()

    if row.get("status") != "active":
        _log(code, dev_uuid, fp_hash, BLOCKED)
        return BLOCKED, row

    if row.get("expires_on") and str(row["expires_on"]) < datetime.now().strftime("%Y-%m-%d"):
        _log(code, dev_uuid, fp_hash, EXPIRED)
        return EXPIRED, row

    if not row.get("device_uuid"):
        sb.table("access_codes").update({
            "device_uuid": dev_uuid, "fingerprint": fp_hash,
            "claimed_at": now, "last_seen": now,
        }).eq("code", code).execute()
        _log(code, dev_uuid, fp_hash, "FIRST_CLAIM")
        return OK, row

    if row["device_uuid"] == dev_uuid:
        sb.table("access_codes").update({"last_seen": now}).eq("code", code).execute()
        return OK, row

    if row.get("fingerprint") and row["fingerprint"] == fp_hash:
        sb.table("access_codes").update({
            "device_uuid": dev_uuid, "last_seen": now,
        }).eq("code", code).execute()
        _log(code, dev_uuid, fp_hash, "REBIND")
        return OK, row

    _log(code, dev_uuid, fp_hash, WRONG_DEVICE)
    return WRONG_DEVICE, row


# ---------------------------------------------------------------- ADMIN
def generate_codes(n, grade, prefix="A4K", expires_on=None):
    sb = get_sb()
    rows = [{
        "code": f"{prefix}-{secrets.token_hex(3).upper()}-{secrets.token_hex(2).upper()}",
        "grade": grade, "expires_on": expires_on, "status": "active",
    } for _ in range(n)]
    sb.table("access_codes").insert(rows).execute()
    return [r["code"] for r in rows]


def reset_device(code):
    """Phone tut gaya / naya laptop - device unbind kar do."""
    sb = get_sb()
    row = sb.table("access_codes").select("reset_count").eq("code", code).execute().data
    count = (row[0]["reset_count"] if row else 0) or 0
    sb.table("access_codes").update({
        "device_uuid": None, "fingerprint": None,
        "claimed_at": None, "reset_count": count + 1,
    }).eq("code", code).execute()


def block_code(code):
    get_sb().table("access_codes").update({"status": "blocked"}).eq("code", code).execute()


# ---------------------------------------------------------------- UI GATE
def login_gate():
    """True = student/teacher andar aa chuka. False = abhi login screen dikh rahi hai."""
    if st.session_state.get("ai4k_authed"):
        return True

    st.markdown(
        '<div style="text-align:center;padding:24px 16px;'
        'background:linear-gradient(135deg,#fef9e7,#eafaf1);border-radius:18px;'
        'border:3px solid #f39c12;margin-bottom:18px">'
        '<h1>🐱 AI4Kids.pk</h1>'
        '<p style="font-size:1.15em;margin:0">اسلام آباد کا پہلا اردو AI سکول</p>'
        '<p style="margin-top:10px">🔒 Apna Access Code daal kar andar aayein</p>'
        '</div>', unsafe_allow_html=True)

    dev_uuid, fp_hash = get_device_identity()
    if not dev_uuid or not fp_hash:
        st.info("Device check ho raha hai… ek lamha intezar karein.")
        st.stop()

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        code = st.text_input("Access Code", key="ai4k_code_in",
                             label_visibility="collapsed",
                             placeholder="A4K-XXXXXX-XXXX")

        if st.button("🚪 Andar aao", type="primary", width='stretch'):
            if is_master(code):
                _log("MASTER", dev_uuid, fp_hash, "MASTER_LOGIN")
                st.session_state["ai4k_authed"] = True
                st.session_state["ai4k_admin"] = True
                st.rerun()

            status, row = verify_code(code, dev_uuid, fp_hash)
            if status == OK:
                st.session_state["ai4k_authed"] = True
                st.session_state["ai4k_code"] = (code or "").strip().upper()
                st.session_state["ai4k_grade"] = row.get("grade")
                st.rerun()
            elif status == WRONG_DEVICE:
                st.error("❌ Ye code kisi aur device pe register ho chuka hai. "
                         "Naya phone/laptop hai to WhatsApp karein: 0337 1468899")
            elif status == BLOCKED:
                st.error("❌ Ye code band kar diya gaya hai. School se rabta karein.")
            elif status == EXPIRED:
                st.error("⏳ Is code ki muddat khatam ho chuki hai.")
            else:
                st.error("❌ Ghalat code. Dobara koshish karein.")

        st.caption("Har code sirf ek hi device pe chalta hai.")

    return False
