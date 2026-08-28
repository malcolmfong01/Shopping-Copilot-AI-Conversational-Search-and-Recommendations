# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

---

## Current Status

| Metric | Baseline | Current (no LLM) | Target (with LLM) |
|--------|----------|-------------------|-------------------|
| Hit Rate@10 | 12.5% | **90.5%** | 95%+ |
| MRR | 0.068 | **0.637** | 0.80+ |
| MTTC | 9.81 turns | **3.93 turns** | 3.0 |
| **Composite Score** | **0.107** | **0.853** | **0.90+** |

Scoring: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`

The retrieval pipeline alone (BM25 + soft scoring + constraint accumulation, no LLM) scores **8.0x the baseline**. The remaining headroom is in MRR — that's where LLM re-ranking will have the biggest impact.

---

## Architecture

```
User message
    ↓
[Constraint Extraction] — parses "what matters is:", "key requirement:", etc.
    ↓                      Supports pipe-separated accumulation (color|size)
[Build Query] — clean terms from constraints, skip budget/noise
    ↓
[Hybrid Retrieval: BM25 + Dense (optional)]
    ↓  BM25: SQLite FTS5, k=200
    ↓  Dense: MiniLM-L6-v2 + FAISS (when available)
    ↓  RRF fusion (K=60)
    ↓
[Soft Constraint Ranking] — score by fraction matched, interleave partials
    ↓  → 50 candidates
    ↓
[rank_candidates()] — LLM re-ranks top 20 → best 10
    ↓
[select_attribute()] — picks most discriminating attribute to ask
    ↓
[generate_message()] — conversational reply
    ↓
Return: {recommendations, ask_attribute, message}
```

---

## Team Split

| Owner | Scope | Files |
|-------|-------|-------|
| Malcolm | Retrieval pipeline, constraint extraction, eval harness | `src/agent.py`, `src/retrieval/`, `src/dialog/state.py`, `src/dialog/intent_detector.py` |
| Yanyox | LLM re-ranking, attribute selection, message gen | `src/ranking/llm_ranker.py`, `src/dialog/attribute_selector.py` |

---

## Prerequisites

- Python 3.11 or 3.12 (3.14 breaks PyTorch; 3.10 and below untested)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
- [GitHub CLI](https://cli.github.com/) (`gh`) for data download

## Quick Start

```bash
# Download competition data (~500MB)
bash data/download.sh

# Install deps and create venv
uv sync

# Run full eval (200 sessions, no LLM needed, ~2 min)
.venv/bin/python -m evaluator.local_evaluator

# For LLM features (Yanyox)
uv sync --extra groq
export GROQ_API_KEY="gsk_..."
```

---

## Project Structure

```
.
├── data/                    # Competition data (downloaded, gitignored)
│   ├── download.sh
│   └── embeddings/          # Precomputed vectors (gitignored)
├── docs/
│   ├── experiments.md       # What was tried, scores, kept/reverted
│   ├── evaluation.md        # Scoring formula and scenarios
│   ├── agent-api-contract.md
│   ├── data-guide.md
│   ├── problem-statement.md
│   ├── deliverables.md
│   └── resources.md
├── evaluator/               # Official local evaluator
├── results/                 # Eval output (gitignored)
├── scripts/                 # Diagnostic + eval helpers
├── src/
│   ├── agent.py             # Main Agent class + constraint extraction
│   ├── llm_client.py        # Groq / Gemini client
│   ├── dialog/
│   │   ├── state.py         # Session state + query builder
│   │   ├── attribute_selector.py  # [YANYOX] select_attribute()
│   │   └── intent_detector.py     # Rule-based override detection
│   ├── ranking/
│   │   └── llm_ranker.py    # [YANYOX] rank_candidates() + generate_message()
│   ├── retrieval/
│   │   ├── bm25.py          # SQLite FTS5
│   │   ├── dense.py         # FAISS + MiniLM (optional)
│   │   └── hybrid.py        # RRF merge + soft constraint scoring
│   └── embeddings/
│       └── precompute.py    # MiniLM-L6-v2 embedding generation
├── tasks/
│   └── yanyox.md            # Full task spec for Yanyox
└── pyproject.toml
```

---

## Limitations & Future Work

- **Remaining misses are semantically ambiguous:** ~6 sessions have ultra-generic constraints ("polyester + Imported + Button closure") matching 40+ products. Pure text retrieval can't distinguish between them — LLM semantic understanding is needed.
- **Dense retrieval untested:** Embeddings are precomputed and code is wired up, but eval hasn't been run yet due to PyTorch/macOS compatibility issues. Expected to help with the remaining BM25-unfindable products.
- **No user profile utilization:** The `user_profile` field (preference tags, purchase frequency) is available but currently unused. Could inform initial retrieval before any questions are asked.
- **Rate limit ceiling:** Groq's 30 RPM free tier means full eval takes ~2 hours. A paid tier or local model would enable faster iteration on LLM prompts.

## Team Contributions

| Member | Contribution |
|--------|-------------|
| Malcolm | Retrieval pipeline (BM25, dense, hybrid RRF), constraint extraction, soft scoring, evaluator integration, documentation |
| Yanyox | LLM re-ranking prompts, attribute selection strategy, message generation |

---

## Submission Checklist

- [ ] Final score above 0.90 on full eval
- [ ] Demo video uploaded to YouTube (walkthrough showing conversational flow)
- [ ] Devpost submission with project description
- [ ] Code pushed to public GitHub repo

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/experiments.md](docs/experiments.md) | Optimization log: what was tried, scores, outcomes |
| [docs/problem-statement.md](docs/problem-statement.md) | Full challenge description |
| [docs/evaluation.md](docs/evaluation.md) | Scoring formula, metrics, scenarios |
| [docs/agent-api-contract.md](docs/agent-api-contract.md) | Agent interface and schemas |
| [docs/data-guide.md](docs/data-guide.md) | Catalog/session schemas, simulator behavior |
| [docs/deliverables.md](docs/deliverables.md) | Submission requirements |
| [tasks/yanyox.md](tasks/yanyox.md) | Yanyox's LLM task spec |
