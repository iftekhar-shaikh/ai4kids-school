"""
prewarm_tts.py — Pre-generate & cache TTS audio for all Grade 1-2 SIMPLE lessons.

Cache-first + resumable: skips any audio_text whose MP3 is already on disk.
Uses the SAME md5 key convention as autoplay_tts.get_tts_mp3 in the app,
so the app finds these files at runtime (zero API cost after prewarm).
"""
import os, json, hashlib, sys, time
import ai_config                      # endpoint config: ai_config.json
client = ai_config.get_tts_client()   # alag TTS provider ho to wohi use hoga

TTS_CACHE_DIR = "tts_cache"
TTS_MODEL = ai_config.TTS_MODEL
TTS_VOICE = ai_config.TTS_VOICE
GRADES = [1, 2]
SUBJECTS = ["ai", "english", "math", "robotics", "science"]

# gpt-4o-mini-tts: ~$0.015 / 1K chars (audio). Rough guard.
USD_PER_1K_CHARS = 0.015
USD_TO_RS = 285.0
BUDGET_RS = 150.0   # covers all 60 clips (~Rs 82 est) with headroom

os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def key_path(text):
    key = hashlib.md5(text.strip().encode("utf-8")).hexdigest()
    return os.path.join(TTS_CACHE_DIR, f"{key}.mp3")

def main():
    total_chars = 0
    done = skipped = failed = 0
    for g in GRADES:
        for sub in SUBJECTS:
            fp = os.path.join("kb", f"grade_{g}", f"{sub}.json")
            d = json.load(open(fp, encoding="utf-8"))
            for t in d.get("topics", []):
                text = (t.get("audio_text") or t.get("text_simple") or "").strip()
                if not text:
                    continue
                path = key_path(text)
                if os.path.exists(path):
                    skipped += 1
                    continue
                est_rs = (total_chars / 1000.0) * USD_PER_1K_CHARS * USD_TO_RS
                if est_rs >= BUDGET_RS:
                    print(f"!! BUDGET cap (~Rs {est_rs:.1f}). Stopping.")
                    print(f"done={done} skipped={skipped} failed={failed}")
                    return
                try:
                    resp = client.audio.speech.create(
                        model=TTS_MODEL, voice=TTS_VOICE, input=text)
                    audio = resp.read() if hasattr(resp, "read") else resp.content
                    with open(path, "wb") as f:
                        f.write(audio)
                    total_chars += len(text)
                    done += 1
                    print(f"OK g{g}/{sub}: {t.get('title','?')} ({len(audio)} bytes)")
                    time.sleep(0.2)
                except Exception as e:
                    failed += 1
                    print(f"FAIL g{g}/{sub}: {t.get('title','?')} -> {e}")
    rs = (total_chars / 1000.0) * USD_PER_1K_CHARS * USD_TO_RS
    print(f"\n=== TTS PREWARM DONE === done={done} skipped={skipped} failed={failed}")
    print(f"chars={total_chars}  ~Rs {rs:.2f}")

if __name__ == "__main__":
    main()
