# AI4Kids Class 5 interactives pack

Drop the `interactives/` folder into the root of [ai4kids-school](https://github.com/iftekhar-shaikh/ai4kids-school):

```
ai4kids-school/
  interactives/   ← this folder
  kb/
  ai4kids_school.py
  ...
```

## Files → Lesson Bank topics

| File | Grade 5 KB topic |
|------|------------------|
| `g5-place-value.html` | Numbers 10 lakh tak (`kb/grade_5/math.json`) |
| `g5-hcf-lcm.html` | HCF aur LCM (`kb/grade_5/math.json`) |
| `g5-perimeter-area.html` | Perimeter aur area (`kb/grade_5/math.json`) |
| `g5-cells.html` | Cells (`kb/grade_5/science.json`) |
| `g5-khoon-nizam.html` | Khoon ka nizam (`kb/grade_5/science.json`) |
| `g5-energy.html` | *No exact card yet* — add topic **Energy — forms** or attach to closest science card |
| `g5-ai-literacy.html` | AI ethics (`kb/grade_5/ai.json`) — TTS-fixed pilot |

## JSON fields to add on each topic

```json
"interactive_file": "interactives/g5-hcf-lcm.html",
"interactive_label": "Khelo — interactive"
```

See `kb-patches.json` for all seven patches.

## Streamlit embed (in lesson modal)

```python
from pathlib import Path
import streamlit.components.v1 as components

rel = topic.get("interactive_file")
if rel:
    path = Path(__file__).resolve().parent / rel
    if path.is_file():
        st.caption(topic.get("interactive_label") or "🎮 Khelo — interactive")
        components.html(path.read_text(encoding="utf-8"), height=720, scrolling=True)
```

**Product rule:** HTML = instruction; keep Streamlit’s 5 MCQs as the exit ticket.
