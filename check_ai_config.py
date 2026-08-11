"""
check_ai_config.py — endpoint badalne ke baad YEH chalayein.

Batata hai: konsa endpoint/model active hai, chat kaam kar raha hai ya nahi,
aur TTS available hai ya nahi. Koi lesson kharab kiye baghair.

    python check_ai_config.py
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import ai_config

print("=" * 62)
print(" AI4Kids — Inference endpoint check")
print("=" * 62)
s = ai_config.config_summary()
print("  -- INFERENCE (text) --")
for k in ("label", "source", "base_url", "api_key", "model"):
    print(f"    {k:12}: {s[k]}")
print("  -- TTS (audio) --")
print(f"    {'separate':12}: {'YES — alag provider' if s['tts_separate'] else 'no — same as inference'}")
for k in ("tts_base_url", "tts_api_key", "tts_model", "tts_voice", "tts_enabled"):
    print(f"    {k:12}: {s[k]}")
print()

# ---------- 1. client ----------
try:
    client = ai_config.get_client(force_reload=True)
    print("  [1/3] Client bana                 ✅")
except Exception as e:
    print(f"  [1/3] Client FAIL                 ❌  {e}")
    sys.exit(1)

# ---------- 2. chat ----------
try:
    t0 = time.time()
    r = client.chat.completions.create(
        model=ai_config.MODEL, max_tokens=20,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}])
    dt = time.time() - t0
    txt = (r.choices[0].message.content or "").strip()
    u = getattr(r, "usage", None)
    print(f"  [2/3] Chat/inference              ✅  '{txt[:30]}'  ({dt:.1f}s)")
    if u:
        print(f"        tokens in={u.prompt_tokens} out={u.completion_tokens}")
except Exception as e:
    print(f"  [2/3] Chat/inference FAIL         ❌")
    print(f"        {type(e).__name__}: {str(e)[:300]}")
    print("        -> model name aur base_url dobara check karein.")
    sys.exit(2)

# ---------- 3. tts ----------
if not ai_config.TTS_ENABLED:
    print("  [3/3] TTS band hai (config)       ⏭   browser awaaz use hogi")
else:
    try:
        tts_client = ai_config.get_tts_client(force_reload=True)
        if ai_config.tts_is_separate():
            print("        (alag TTS provider use ho raha hai)")
        resp = tts_client.audio.speech.create(
            model=ai_config.TTS_MODEL, voice=ai_config.TTS_VOICE,
            input="Assalam o alaikum bachon")
        audio = resp.read() if hasattr(resp, "read") else resp.content
        print(f"  [3/3] TTS                         ✅  {len(audio):,} bytes mp3")
    except Exception as e:
        print(f"  [3/3] TTS available NAHI          ⚠️   {type(e).__name__}")
        print(f"        {str(e)[:200]}")
        print("        -> Koi masla nahi: app khud browser ki awaaz par chala jayega.")
        print("        -> Chaahein to ai_config.json mein tts_enabled=false kar dein.")

print("\n  Sab theek — app chala sakte hain.\n")
