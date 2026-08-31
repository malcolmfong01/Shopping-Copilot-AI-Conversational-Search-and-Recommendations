# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

---

## Current Score

| Metric | Baseline | Current (BM25 + soft-rank, no LLM key) |
|--------|----------|----------------------------------------|
| Hit Rate@10 | 12.5% | **98.5%** |
| MRR | 0.068 | **0.645** |
| MTTC | 9.81 turns | **2.40 turns** |
| **Composite** | **0.107** | **0.858** |

Scoring: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`

The published composite is the **full 200-session** BM25 + soft-rank run with LLM re-ranking **off** (`results/latest.json`). On a 20-session mini-eval, enabling Groq re-ranking lifted the composite to **0.865**; that path is not used for the submitted score (see Limitations).

---

## Architecture

```
User message
    ↓
Constraint Extraction — pattern-match "looking for…", "key requirement:", "what matters is:"
    ↓                    Pipe-separated accumulation (e.g. waterproof|breathable)
Build Query — short keyword string for BM25 (skip budget, trim category)
    ↓
BM25 Search — SQLite FTS5, weighted columns, k=200 → ~200 candidates
    ↓
Soft Constraint Rank — score against full constraint dict (incl. budget vs price)
    ↓                    Full matches first, near-misses interleaved → ~50 candidates
LLM Re-rank — reorder top 20 → best 10 (bypass if no key or invalid JSON)
    ↓
Attribute Select — pick the most discriminating unasked attribute
    ↓
Return: {recommendations, ask_attribute, message}
```

Dense vector retrieval (MiniLM-L6-v2 + FAISS) is implemented but opt-in (`ENABLE_DENSE=1`). It was evaluated and does not improve BM25 — see [experiments.md](docs/experiments.md) for the analysis.

---

## Quick Start

### Prerequisites

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management

### Evaluation

```bash
# Download competition data (~500 MB)
bash data/download.sh

# Install dependencies
uv sync

# Run full eval (200 sessions, LLM off, ~2 min) — submitted score 0.858
bash scripts/eval_full.sh
```

### Unit Tests

```bash
uv sync --extra dev
uv run pytest tests/ -q
```

### LLM Features

Optional for the **demo** and for a 20-session mini-eval (measured Groq composite **0.865**). Not used in `scripts/eval_full.sh` — that is the submitted **0.858** run. See Limitations.

```bash
uv sync --extra groq
export GROQ_API_KEY="gsk_..."
# optional fallback if Groq unset:
# uv sync --extra gemini && export GOOGLE_API_KEY="..."
bash scripts/eval_mini.sh
```

### Demo Webapp

```bash
# 1. Install webapp dependency
uv sync --extra demo

# 2. Start Flask API server (loads catalog ~9 s, serves on port 8080)
.venv/bin/python webapp/app.py

# 3. In a second terminal, start the React dev server
cd webapp/frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Click **Try Example** to auto-type a 3-turn conversation showing constraint extraction, product narrowing, and pipeline tracing.

The **Architecture** tab walks judges through each pipeline stage with before/after examples and live data from the Product session.

---

## Project Structure

```
├── src/
│   ├── agent.py                  # Main Agent + constraint extraction
│   ├── llm_client.py             # Groq / Gemini client
│   ├── dialog/
│   │   ├── state.py              # Session state + query builder
│   │   ├── attribute_selector.py # select_attribute()
│   │   └── intent_detector.py    # Override detection
│   ├── ranking/
│   │   └── llm_ranker.py         # rank_candidates() + generate_message()
│   └── retrieval/
│       ├── bm25.py               # SQLite FTS5
│       ├── dense.py              # FAISS + MiniLM (opt-in)
│       └── hybrid.py             # Soft constraint scoring
├── webapp/
│   ├── app.py                    # Flask API server
│   └── frontend/                 # React + Vite
├── evaluator/                    # Official local evaluator
├── data/                         # Competition data (gitignored)
├── docs/                         # Problem statement, scoring, experiments
└── pyproject.toml
```

---

## Team

| Member | Scope |
|--------|-------|
| Malcolm | Retrieval pipeline, constraint extraction, eval harness, demo webapp |
| Yanyox | LLM re-ranking, attribute selection, message generation |

---

## Limitations

- **LLM re-ranking is not enabled in the submitted run** — on 20 public sessions, Groq re-ranking improved the composite from the BM25 spine to **0.865**. We still report **0.858** from the full 200-session eval **without** an LLM: Groq's free-tier rate limit (~30 RPM) makes a 200-session LLM eval ~2 hours and token-costly, so the ranked submission is BM25 + soft-rank only. The ranker still runs in the demo when `GROQ_API_KEY` or `GOOGLE_API_KEY` is set.
- **Remaining misses are semantically ambiguous** — ~6 sessions have ultra-generic constraints ("polyester + Imported + Button closure") matching 40+ products. LLM re-ranking is the intended way to break those near-duplicates; we could not afford to turn it on for the full scored run.
- **Dense retrieval does not help** — the evaluator generates literal substring constraints, making BM25 near-optimal by construction. See [experiments.md](docs/experiments.md) for the analysis.

---

## Docs

| Doc | Description |
|-----|-------------|
| [deliverables.md](docs/deliverables.md) | Rules, scoring, deliverables, judging, checklist |
| [experiments.md](docs/experiments.md) | Optimization log, dense opt-in rationale, LLM status |
| [evaluation.md](docs/evaluation.md) | Eval config and how to run |
| [data-guide.md](docs/data-guide.md) | Catalog/session schemas, simulator behavior |
| [problem-statement.md](docs/problem-statement.md) | Original challenge description |
| [agent-api-contract.md](docs/agent-api-contract.md) | Agent ↔ evaluator message contract |
| [demo-script.md](docs/demo-script.md) | 90–120s demo video outline |
| [resources.md](docs/resources.md) | Official competition links |
