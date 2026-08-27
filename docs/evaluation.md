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

## Scenario Types

The 200 public development sessions are distributed as:

| Scenario | Count | % | Behavior |
|----------|-------|---|----------|
| buying | 80 | 40% | Straightforward purchase intent with clear constraints |
| browsing | 80 | 40% | Open-ended exploration, vaguer preferences |
| intent_override | 30 | 15% | User changes their mind at turn 3 or 4 — agent must detect and adapt |
| boundary | 10 | 5% | User refuses to answer the first attribute question ("I don't have a preference") |

## How the Simulator Works

1. **Agent sends `ask_attribute`** (e.g., "color") → simulator reveals the corresponding hard constraint or soft preference if not yet disclosed
2. **Agent sends `ask_attribute: null`** → simulator responds with "Ask me about one specific attribute"
3. **Intent override turns**: at a predetermined turn (3 or 4), the user's intent completely changes — new target product, new constraints
4. **Boundary sessions**: first attribute question gets "I don't have a preference" regardless of what's asked

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
python -m evaluator.local_evaluator \
  --catalog data/catalog.jsonl \
  --dataset data/public_set.jsonl \
  --output results.json
```
