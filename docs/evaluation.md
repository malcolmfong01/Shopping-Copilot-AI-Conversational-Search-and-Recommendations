# Evaluation

## Scoring Formula

```
technical_score = 0.50 * hit_rate@10 + 0.30 * mrr + 0.20 * efficiency
```

Where:
```
efficiency = clip((11 - mttc) / 10, 0, 1)
```

- **hit_rate@10**: Whether the ground-truth product appears in the agent's top-10 recommendations by session end
- **mrr** (Mean Reciprocal Rank): 1/rank of the ground-truth product in the final recommendation list (0 if not present)
- **mttc** (Mean Turns to Conversion): Average number of turns before the ground-truth product first appears in top-10. Sessions that never hit = 11 (miss_turn_value)

## Metric Weights

| Metric | Weight | What it rewards |
|--------|--------|-----------------|
| Hit Rate@10 | 50% | Finding the right product at all |
| MRR | 30% | Ranking the right product higher |
| Efficiency | 20% | Finding it in fewer turns |

## Baseline Results (Weak BM25 Starter)

| Metric | Value |
|--------|-------|
| hit_rate@10 | 0.125 (12.5%) |
| mrr | 0.068 |
| mttc | 9.81 |
| efficiency | 0.119 |
| **technical_score** | **0.107** |

The starter agent is weak because it **never asks clarifying questions** (`ask_attribute` is always null), meaning the simulator never reveals additional constraints.

## Scenarios & Simulator

See [data-guide.md](data-guide.md) for scenario distribution, simulator behavior, and how constraints are revealed.

## Evaluation Configuration

```json
{
  "catalog_id_field": "parent_asin",
  "top_k": 10,
  "max_turns": 10,
  "miss_turn_value": 11,
  "exact_match": true,
  "metrics": ["hit_rate_at_10", "mrr", "mttc", "reported_token_usage"],
  "scenario_metrics": ["buying", "browsing", "intent_override", "boundary"]
}
```

## Running the Evaluator

```bash
# Full eval (200 sessions, outputs to results/latest.json)
.venv/bin/python -m evaluator.local_evaluator

# With explicit paths (defaults shown)
.venv/bin/python -m evaluator.local_evaluator \
  --catalog data/catalog.jsonl \
  --dataset data/public_set.jsonl \
  --output results/latest.json
```
