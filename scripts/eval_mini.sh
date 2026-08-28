#!/usr/bin/env bash
set -euo pipefail

# Run evaluation on first 20 sessions (5 per scenario type) for fast iteration
# Expected runtime: ~2-5 min with Groq LLM, ~30s without LLM

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m evaluator.local_evaluator \
    --catalog data/catalog.jsonl \
    --dataset data/public_set.jsonl \
    --output results_mini.json \
    --limit 20

echo ""
echo "=== Mini eval results ==="
python -c "import json; r=json.load(open('results_mini.json')); print(f\"Hit Rate: {r['hit_rate_at_10']:.3f} | MRR: {r['mrr']:.3f} | MTTC: {r['mttc']:.2f} | Score: {r['technical_score']:.3f}\")"
echo "Baseline: Hit Rate: 0.125 | MRR: 0.068 | MTTC: 9.81 | Score: 0.107"
