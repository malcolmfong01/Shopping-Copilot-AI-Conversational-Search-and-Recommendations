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

## Current Validated Results (Public 200)

| Metric | Value |
|--------|-------|
| hit_rate@10 | 0.985 (98.5%) |
| mrr | 0.645 |
| mttc | 2.40 |
| **technical_score** | **0.858** |

These numbers are the **submitted** result: BM25 + soft-rank on all 200 public sessions, **LLM off**. Artifact: [`results/latest.json`](../results/latest.json) (`recommended_technical_score` 0.858051).

### LLM mini-eval (not the submitted score)

On the first **20** public sessions, the same pipeline with Groq re-ranking scored **0.865** (vs the BM25-only spine on that subset). That lift is why the ranker exists; it is **not** enabled for the full 200-session run because of Groq free-tier rate limits (~30 RPM, ~2 hours) and token cost. Reproduce the submitted 0.858 with keys unset (see `scripts/eval_full.sh`). To exercise LLM re-ranking on a short slice, export `GROQ_API_KEY` (or `GOOGLE_API_KEY`) and run `scripts/eval_mini.sh`.

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
# Submitted score: 200 sessions, LLM keys unset (0.858)
bash scripts/eval_full.sh

# Equivalent, with explicit paths (does not unset keys — use eval_full.sh to match 0.858)
.venv/bin/python -m evaluator.local_evaluator \
  --catalog data/catalog.jsonl \
  --dataset data/public_set.jsonl \
  --output results/latest.json

# Optional: 20-session LLM mini-eval (measured Groq composite 0.865)
# export GROQ_API_KEY=... && bash scripts/eval_mini.sh
```
