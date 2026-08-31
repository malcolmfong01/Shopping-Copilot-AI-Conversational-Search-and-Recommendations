# Demo video script (90–120s)

Record the **live webapp**, not slides. The pipeline inspector at the bottom of the results panel is the visual. Use **Try Example** so the three turns are deterministic.

Setup: desktop ~1440×900, captions on, voiceover. Start on an empty session (header scores visible, chat empty).

| Time | On screen | Say |
|------|-----------|-----|
| 0–12s | Header: `Hit Rate 98.5% · 0.858 · 8× baseline`. Empty chat. | Shopping search usually takes many turns of “what color, what size.” Ours finds the target in about 2.4 turns. |
| 12–25s | Same header; cursor over the score badge. | This is retrieval and constraint ranking — not a chatbot wrapper. Composite 0.858, eight times the baseline. |
| 25–50s | Click **Try Example**. Turn 1: inspector lights Extract → BM25 → Soft rank → LLM rank → Ask. | Watch the pipeline. We extract category and the key feature, BM25 cuts 50,000 products to a few hundred, then soft ranking keeps full and partial matches. |
| 50–75s | Turn 2: constraint pills grow (`color`, `budget`); candidate counts drop. Click **Soft rank** then **LLM rank**. | Turn two adds black and under $80. The funnel tightens. If LLM re-rank is live you’ll see products move; if not, we keep retrieval order — the spine still scores 8× baseline. |
| 75–95s | Turn 3: size and brand pills. Inspector Ask stage. | We only ask the next discriminating attribute. Ten turns is the cap; we are done in three. |
| 95–115s | Zoom / cursor on the #1 product card ticks (matched vs missed constraints). | This is number one because it matched breathable mesh, black, and the budget — you can see every constraint on the card. |
| 115–120s | Freeze on inspector + products. | Constraint extraction, BM25, soft rank, optional LLM re-rank, then the next question. That’s the copilot. |

## Filming notes

- 1440px desktop; also glance at ~768px so the inspector scrolls horizontally instead of overflowing.
- Captions on. Do not autoplay anything.
- If Groq/Gemini is slow or unset, film with **LLM rank · fallback** visible and say so in the 50–75s beat. Submitted score is 0.858 without LLM; Groq mini-eval was 0.865 (n=20) but that path is off for the full run (cost / rate limits).
- Do not enable `ENABLE_DENSE=1` for the recording; dense retrieval is off by default and the inspector must not imply a vector stage ran.
- After the take, leave the final product list on screen (no fade to black over an empty UI).
