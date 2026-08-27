# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

---

## Current Status

| Metric | Baseline (starter) | Current (no LLM) | Target (with LLM) |
|--------|-------------------|-------------------|-------------------|
| Hit Rate@10 | 12.5% | **84%** | 90%+ |
| MRR | 0.068 | **0.545** | 0.70+ |
| MTTC | 9.81 turns | **4.48 turns** | 3.5 |
| **Composite Score** | **0.107** | **0.714** | **0.80+** |

Scoring: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`

The retrieval pipeline alone (BM25, no LLM, heuristic attribute selection) scores **6.7x the baseline**. The remaining headroom is in **MRR** — that's where LLM re-ranking will have the biggest impact.

---

## What's Been Done (Malcolm)

1. **BM25 retrieval** (SQLite FTS5) with tuned column weights
2. **Constraint extraction** — parses all evaluator response formats ("For that, what matters is: X; Y.", "A key requirement is: X.", etc.)
3. **Query construction** — strips noise prefixes, uses specific category terms, skips budget from BM25 queries
4. **Attribute priority** — asking "feature" early (turn 2) is the single biggest efficiency win. Features like "waterproof", "RFID blocking" are extremely discriminating for BM25.
5. **Intent override handling** — flushes preferences but preserves category on mind-change
6. **Optional dense retrieval** — system runs without faiss/PyTorch (graceful fallback)
7. **Full evaluator integration** — runs end-to-end, outputs to `results/`

---

## What Yanyox Needs To Do

**Full spec: [`tasks/yanyox.md`](tasks/yanyox.md)**

### Summary

You own 3 functions that use the LLM to improve the score:

| Function | File | Impact |
|----------|------|--------|
| `rank_candidates()` | `src/ranking/llm_ranker.py` | MRR (30% of score) |
| `select_attribute()` | `src/dialog/attribute_selector.py` | Efficiency (20% of score) |
| `generate_message()` | `src/ranking/llm_ranker.py` | Demo only (not scored) |

### The Big Win: Re-Ranking

Right now the agent returns products in BM25 retrieval order. MRR = 0.545 means the target lands around position 2-3 on average. If your re-ranker can push it to #1 consistently, MRR jumps to 0.7+, which alone adds ~0.05 to the composite score.

You get 20 candidates with full metadata (title, categories, features, details, price) + the user's accumulated preferences. Just rank them.

### Setup

```bash
# 1. Install deps
uv sync --extra groq

# 2. Get a free Groq API key (instant signup)
#    https://console.groq.com
export GROQ_API_KEY="gsk_..."

# 3. Run mini eval (20 sessions, ~40 LLM calls, fast)
.venv/bin/python -c "
import json
from evaluator.local_evaluator import evaluate, catalog_index, load_jsonl
from src.agent import Agent

samples = load_jsonl('data/public_set.jsonl')[:20]
catalog_ids, categories, products = catalog_index('data/catalog.jsonl')
agent = Agent('data/catalog.jsonl')
result = evaluate(agent, samples, catalog_ids, categories, products)
print(json.dumps({k: v for k, v in result.items() if k != 'sessions'}, indent=2))
"

# 4. Run full eval (200 sessions)
.venv/bin/python -m evaluator.local_evaluator
```

### Rate Limits

- **Groq** (recommended): 30 RPM, 14400 requests/day. Mini eval = instant. Full eval = ~2 hours.
- **Gemini 3.6 Flash**: Only 20 requests/day on free tier. Not enough for eval runs.

### Iteration Loop

1. Edit prompts in `src/ranking/llm_ranker.py` or `src/dialog/attribute_selector.py`
2. Run mini eval (20 sessions)
3. Check score — compare to baseline 0.714 (no LLM)
4. If score improves, run full eval to confirm
5. Repeat

### Tips

- Study failures: check `results/latest.json` for sessions where `"hit": false`
- Re-ranking has 2x the weight of attribute selection (30% vs 20% of score)
- Keep prompts short — less tokens = faster iterations + less rate limiting
- The simulator is deterministic — same session always responds the same way
- `generate_message()` is cosmetic only (for the demo video). Don't spend time here until ranking works.

---

## Architecture

```
User message
    ↓
[Constraint Extraction] — parses "what matters is:", "key requirement:", etc.
    ↓
[Build Query] — clean terms from constraints (no noise)
    ↓
[BM25 Retrieval] — top 150, then constraint filter → 50 candidates
    ↓
[YOUR CODE: rank_candidates()] — LLM picks best 10 from top 20
    ↓
[YOUR CODE: select_attribute()] — LLM picks most discriminating attribute
    ↓
[YOUR CODE: generate_message()] — conversational reply
    ↓
Return: {recommendations, ask_attribute, message}
```

Every turn ALWAYS returns both recommendations AND asks one attribute. The evaluator ends the session the moment the target appears in top-10.

---

## Project Structure

```
.
├── data/                    # Competition data (downloaded, gitignored)
│   ├── download.sh
│   └── embeddings/          # Precomputed vectors (Day 2)
├── docs/                    # Challenge documentation
├── evaluator/               # Official local evaluator
├── results/                 # Eval output (gitignored)
├── scripts/                 # Diagnostic + eval runners
├── src/
│   ├── agent.py             # Main Agent class
│   ├── llm_client.py        # Groq (primary) / Gemini (fallback)
│   ├── dialog/
│   │   ├── state.py         # Session state + query builder
│   │   ├── attribute_selector.py  # [YANYOX] select_attribute()
│   │   └── intent_detector.py     # Rule-based override detection
│   ├── ranking/
│   │   └── llm_ranker.py    # [YANYOX] rank_candidates() + generate_message()
│   ├── retrieval/
│   │   ├── bm25.py          # SQLite FTS5
│   │   ├── dense.py         # FAISS (optional, Day 2)
│   │   └── hybrid.py        # RRF merge + constraint filtering
│   └── embeddings/
│       └── precompute.py    # BGE embedding generation (Day 2)
├── tasks/
│   └── yanyox.md            # Full task spec for Yanyox
└── pyproject.toml
```

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/problem-statement.md](docs/problem-statement.md) | Full challenge description |
| [docs/evaluation.md](docs/evaluation.md) | Scoring formula, metrics, scenarios |
| [docs/agent-api-contract.md](docs/agent-api-contract.md) | Agent interface and schemas |
| [docs/data-guide.md](docs/data-guide.md) | Catalog/session schemas, simulator behavior |
| [docs/deliverables.md](docs/deliverables.md) | Submission requirements |
| [docs/resources.md](docs/resources.md) | Links and references |
