#!/usr/bin/env bash
set -euo pipefail

# Full eval: all 200 public sessions
# ~2 hours with Groq LLM, ~2 min without

cd "$(dirname "${BASH_SOURCE[0]}")/.."

.venv/bin/python -m evaluator.local_evaluator \
    --catalog data/catalog.jsonl \
    --dataset data/public_set.jsonl \
    --output results/latest.json

echo ""
echo "=== Full eval results (200 sessions) ==="
.venv/bin/python -c "import json; r=json.load(open('results/latest.json')); print(f\"Hit Rate: {r['hit_rate_at_10']:.3f} | MRR: {r['mrr']:.3f} | MTTC: {r['mttc']:.2f} | Score: {r['recommended_technical_score']:.4f}\")"
echo "Baseline: Hit Rate: 0.125 | MRR: 0.068 | MTTC: 9.81 | Score: 0.107"
