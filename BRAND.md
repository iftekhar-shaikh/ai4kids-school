# AI4Kids Brand System

Product: bilingual (Roman Urdu default) primary learning for Pakistan / Islamabad kids.

## Colors (tokens)

| Token | Hex | Use |
|-------|-----|-----|
| `--ink` | `#17252f` | Body text, borders |
| `--muted` | `#526672` | Secondary text |
| `--paper` | `#fffdf7` | App background |
| `--card` | `#ffffff` | Cards / panels |
| `--line` | `#d9d2c5` | Soft borders |
| `--green` | `#27ae60` | Primary brand / success / filter active |
| `--green-deep` | `#1e8449` | Hover / emphasis |
| `--teal` | `#1abc9c` | Header gradient partner |
| `--purple` | `#8e44ad` | Sunlo / Khelo / AI accent |
| `--orange` | `#e67e22` | Secondary CTA / focus ring |
| `--yellow` | `#fff0b8` | Highlights / comic caption |
| `--red` | `#e74c3c` | Stop / error / Roko |
| `--whatsapp` | `#25D366` | Contact CTA only |

## Type

- **UI / Roman Urdu:** `'Segoe UI', 'Trebuchet MS', Tahoma, sans-serif` (offline-safe; no CDN required)
- **Sizes:** mobile-first `clamp()` — titles large, body ≥1.1rem on phones
- **Weight:** 700–900 for buttons and kid-facing titles
- Do **not** load Google Fonts for core play (offline school / weak data)

## Chrome (consistent UI)

- Header / brand bar: green→teal gradient (`#27ae60` → `#1abc9c`), white text
- Primary action (Khelo / Play): green, min-height ~52px, full-width on mobile
- Accent action (Sunlo): purple `#8e44ad`
- Danger / stop: red `#e74c3c`
- Cards: white on warm paper, 2–3px ink or soft line border, radius 14–18px
- Filter chips: inactive white+line; active green fill
- Keep Lesson Bank **HTML card grid** layout — brand changes colors/type only

## Mascot rules (Islamabad kid)

1. **Look:** soft round face, dark hair, **green school shirt** (`#1f7a4c` / `--green-deep`), white panel on chest OK
2. **Skin:** warm `#f2c9a0` — friendly, not photoreal
3. **Tone:** helpful classmate, not a celebrity / licensed character
4. **Scenes:** Islamabad cues OK (Faisal Mosque silhouette, Margalla, green flag accents) — keep simple SVG
5. **Never:** scary, violent, political party symbols, or text that needs Nastaliq to be readable in-comic (use Roman Urdu / emoji / simple English labels in panels)
6. Comics sit **above** the interactive stage; do not replace the play controls

## WhatsApp

Public contact shown as **0337 1468899** with `--whatsapp` green on CTAs only.

## Files

- This doc: `BRAND.md`
- Shared CSS tokens: `brand.css` (reference; inlined into LB builder + Streamlit)
