"""
ai_config.py — AI4Kids.pk  |  SINGLE PLACE for inference endpoint settings.

Yahan se poora project apna API endpoint uthata hai. Endpoint badalna ho to
sirf `ai_config.json` edit karein — kisi bhi .py file ko haath lagane ki
zaroorat NAHI.

PRECEDENCE (upar wala jeet-ta hai):
  1. Environment variables   -> AI4KIDS_BASE_URL / AI4KIDS_API_KEY /
                                AI4KIDS_MODEL / AI4KIDS_TTS_MODEL
  2. ai_config.json          -> is folder mein
  3. Purana fallback         -> OPENAI_API_KEY env var + OpenAI ka default URL
                                (taake kuch set na ho to app pehle jaisa chale)

Check karne ke liye:  python check_ai_config.py
"""
import os, json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_config.json")

# Fallback defaults (agar config file na ho)
_DEFAULTS = {
    "base_url": "",                     # khali = OpenAI default (api.openai.com/v1)
    "api_key": "",                      # khali = OPENAI_API_KEY env var use hoga
    "model": "gpt-4o-mini",             # text / inference model

    # --- TTS: alag provider par bhi chal sakta hai ---
    # tts_base_url / tts_api_key khali chhoren  -> upar wala hi endpoint use hoga
    # bhar dein                                  -> TTS bilkul alag provider par
    "tts_base_url": "",
    "tts_api_key": "",
    "tts_model": "gpt-4o-mini-tts",
    "tts_voice": "alloy",
    "tts_enabled": True,
    "label": "OpenAI (default)",        # sirf dikhane ke liye
}


def _load_file():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except Exception as e:
            print(f"[ai_config] WARNING: {CONFIG_FILE} parhne mein masla: {e}")
    return {}


def get_config():
    """Return the effective config dict (env > json > defaults)."""
    cfg = dict(_DEFAULTS)
    cfg.update(_load_file())

    # env overrides
    env_map = {
        "base_url":     "AI4KIDS_BASE_URL",
        "api_key":      "AI4KIDS_API_KEY",
        "model":        "AI4KIDS_MODEL",
        "tts_base_url": "AI4KIDS_TTS_BASE_URL",
        "tts_api_key":  "AI4KIDS_TTS_API_KEY",
        "tts_model":    "AI4KIDS_TTS_MODEL",
        "tts_voice":    "AI4KIDS_TTS_VOICE",
    }
    for key, env_name in env_map.items():
        val = os.environ.get(env_name)
        if val:
            cfg[key] = val
            cfg["label"] = cfg.get("label", "") + " [env override]" \
                if "[env override]" not in cfg.get("label", "") else cfg["label"]

    # legacy fallback: koi key na mile to purana OPENAI_API_KEY
    if not cfg.get("api_key"):
        cfg["api_key"] = os.environ.get("OPENAI_API_KEY", "")

    if isinstance(cfg.get("tts_enabled"), str):
        cfg["tts_enabled"] = cfg["tts_enabled"].strip().lower() not in ("0", "false", "no")
    return cfg


# ---- effective values, importable directly ----
_CFG = get_config()
MODEL = _CFG["model"]
TTS_MODEL = _CFG["tts_model"]
TTS_VOICE = _CFG["tts_voice"]
TTS_ENABLED = bool(_CFG.get("tts_enabled", True))
BASE_URL = _CFG["base_url"]


_client = None
def get_client(force_reload=False):
    """Shared OpenAI-compatible client banaya jata hai config ke mutabiq."""
    global _client, MODEL, TTS_MODEL, TTS_VOICE, TTS_ENABLED, BASE_URL, _CFG
    if _client is not None and not force_reload:
        return _client
    from openai import OpenAI
    cfg = get_config()
    _CFG = cfg
    MODEL, TTS_MODEL = cfg["model"], cfg["tts_model"]
    TTS_VOICE, BASE_URL = cfg["tts_voice"], cfg["base_url"]
    TTS_ENABLED = bool(cfg.get("tts_enabled", True))

    if not cfg.get("api_key"):
        raise RuntimeError(
            "API key nahi mili. Ya to ai_config.json mein 'api_key' bharein, "
            "ya AI4KIDS_API_KEY / OPENAI_API_KEY environment variable set karein."
        )
    kwargs = {"api_key": cfg["api_key"]}
    if cfg.get("base_url"):
        kwargs["base_url"] = cfg["base_url"]
    _client = OpenAI(**kwargs)
    return _client


_tts_client = None
def get_tts_client(force_reload=False):
    """TTS ke liye client.
    Agar tts_base_url / tts_api_key config mein bhare hain to ALAG provider
    use hota hai; warna wohi main client (upar wala endpoint)."""
    global _tts_client
    if _tts_client is not None and not force_reload:
        return _tts_client
    cfg = get_config()
    t_url = (cfg.get("tts_base_url") or "").strip()
    t_key = (cfg.get("tts_api_key") or "").strip()
    if not t_url and not t_key:
        _tts_client = get_client(force_reload)      # same provider
        return _tts_client
    from openai import OpenAI
    kwargs = {"api_key": t_key or cfg.get("api_key")}
    if t_url:
        kwargs["base_url"] = t_url
    _tts_client = OpenAI(**kwargs)
    return _tts_client


def tts_is_separate():
    c = get_config()
    return bool((c.get("tts_base_url") or "").strip() or (c.get("tts_api_key") or "").strip())


def mask(secret):
    if not secret:
        return "(khali)"
    return f"{secret[:6]}...{secret[-4:]}  (length {len(secret)})"


def config_summary():
    """Human-readable summary — key hamesha masked."""
    c = get_config()
    return {
        "label":     c.get("label", ""),
        "base_url":  c.get("base_url") or "https://api.openai.com/v1  (default)",
        "api_key":   mask(c.get("api_key")),
        "model":     c.get("model"),
        "tts_model": c.get("tts_model"),
        "tts_voice": c.get("tts_voice"),
        "tts_enabled": c.get("tts_enabled", True),
        "tts_separate": tts_is_separate(),
        "tts_base_url": (c.get("tts_base_url") or "").strip()
                        or ("(same as inference)" if not tts_is_separate() else ""),
        "tts_api_key": mask(c.get("tts_api_key")) if (c.get("tts_api_key") or "").strip()
                       else "(same as inference)",
        "source":    "ai_config.json" if os.path.exists(CONFIG_FILE) else "env / defaults",
    }
