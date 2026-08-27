#!/usr/bin/env bash
set -euo pipefail

# Run full evaluation on all 200 public sessions
# Expected runtime: ~20-40 min with Groq LLM, ~5 min without LLM

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m evaluator.local_evaluator \
    --catalog data/catalog.jsonl \
    --dataset data/public_set.jsonl \
    --output results.json

echo ""
echo "=== Full eval results (200 sessions) ==="
python -c "import json; r=json.load(open('results.json')); print(f\"Hit Rate: {r['hit_rate_at_10']:.3f} | MRR: {r['mrr']:.3f} | MTTC: {r['mttc']:.2f} | Score: {r['technical_score']:.3f}\")"
echo "Baseline: Hit Rate: 0.125 | MRR: 0.068 | MTTC: 9.81 | Score: 0.107"
