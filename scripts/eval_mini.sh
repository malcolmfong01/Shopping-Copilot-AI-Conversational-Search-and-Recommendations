#!/usr/bin/env bash
set -euo pipefail

# Mini eval: first 20 sessions for fast iteration.
# Without an API key: BM25 + soft-rank only (~30s).
# With GROQ_API_KEY set: LLM re-ranking (~1 min). Measured Groq mini-eval composite: 0.865.
# That LLM lift is not used for the submitted 200-session score 0.858 (see README Limitations).

cd "$(dirname "${BASH_SOURCE[0]}")/.."

.venv/bin/python -c "
import json
from evaluator.local_evaluator import evaluate, catalog_index, load_jsonl
from src.agent import Agent

samples = load_jsonl('data/public_set.jsonl')[:20]
catalog_ids, categories, products = catalog_index('data/catalog.jsonl')
agent = Agent('data/catalog.jsonl')
result = evaluate(agent, samples, catalog_ids, categories, products)

print(f\"Hit Rate: {result['hit_rate_at_10']:.3f} | MRR: {result['mrr']:.3f} | MTTC: {result['mttc']:.2f} | Score: {result['recommended_technical_score']:.4f}\")
print(f\"Baseline: Hit Rate: 0.125 | MRR: 0.068 | MTTC: 9.81 | Score: 0.107\")
"
