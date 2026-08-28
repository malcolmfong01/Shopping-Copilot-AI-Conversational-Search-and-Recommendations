# Retrieval Pipeline — Remaining Tasks

## Current Score: 0.853 (BM25-only, no LLM)

---

## 1. Validate Dense Retrieval

Dense retrieval is wired up but untested. Run this on Apple Silicon MacBook (32GB) to see if it helps.

```bash
git clone https://github.com/malcolmfong01/Shopping-Copilot-AI-Conversational-Search-and-Recommendations.git
cd Shopping-Copilot-AI-Conversational-Search-and-Recommendations
git checkout malcolm/retrieval-pipeline

python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install sentence-transformers faiss-cpu

bash data/download.sh

# Precompute embeddings (~5 min on Apple Silicon)
.venv/bin/python -m src.embeddings.precompute

# Run mini eval — confirm "Dense retrieval active: True"
.venv/bin/python -c "
import json
from evaluator.local_evaluator import evaluate, catalog_index, load_jsonl
from src.agent import Agent

samples = load_jsonl('data/public_set.jsonl')[:20]
catalog_ids, categories, products = catalog_index('data/catalog.jsonl')
agent = Agent('data/catalog.jsonl')
print(f'Dense retrieval active: {agent._dense is not None}')
result = evaluate(agent, samples, catalog_ids, categories, products)
print(json.dumps({k: v for k, v in result.items() if k != 'sessions'}, indent=2))
"
```

Compare `recommended_technical_score` to **0.853**. If higher → dense retrieval helps, keep it. If same/lower → skip it, focus on LLM re-ranker.

**Why run it there:** The slow part is per-query model encoding at runtime (~200ms on Intel CPU, ~10ms on Apple Silicon). The precomputed catalog embeddings already exist — it's the live query encoding that makes eval impractical on Intel. You just need the score from one mini eval to decide if dense retrieval is worth keeping. The competition's eval server handles compute regardless.

---

## 2. Full Eval With Best Pipeline

Once dense retrieval is validated (or skipped), run the full 200-session eval on the Apple Silicon machine to confirm the final retrieval-only score:

```bash
.venv/bin/python -m evaluator.local_evaluator
```

This is the baseline Yanyox builds on top of.

---

## 3. Support Yanyox

- Help test LLM re-ranker against the best retrieval pipeline
- Demo video: record a conversational walkthrough showing the agent in action
