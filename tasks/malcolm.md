# Retrieval Pipeline — Remaining Tasks

## Current Score: 0.853 (BM25-only, no LLM)

---

## 1. Validate Dense Retrieval — DONE (decision pending)

Ran on Apple Silicon (arm64). Dense active: **True**. Mini eval (20 sessions):

| Metric | Dense hybrid | BM25 baseline |
|---|---|---|
| `recommended_technical_score` | **0.839** | **0.853** |
| Hit@10 | 0.95 | — |
| MRR | 0.656 | — |
| MTTC | 2.65 | — |
| Efficiency | 0.835 | — |

Dense is wired and runnable, but the first hybrid pass is ~0.014 below BM25-only. Embeddings are at `data/embeddings/minilm.npy`.

**Open decision — improve or skip?**
- **Try improving:** tune hybrid fusion weights / top-k, query text construction, or when dense is used (e.g. browsing-only), then re-run the mini eval and see if it clears 0.853.
- **Skip:** leave dense off for the competition pipeline and put effort into the LLM re-ranker on top of BM25.

---

## 2. Full Eval With Best Pipeline

Once the dense improve-vs-skip call is made, run the full 200-session eval with the chosen pipeline to confirm the final retrieval-only score:

```bash
.venv/bin/python -m evaluator.local_evaluator
```

This is the baseline Yanyox builds on top of.

---

## 3. Support Yanyox

- Help test LLM re-ranker against the best retrieval pipeline
- Demo video: record a conversational walkthrough showing the agent in action
