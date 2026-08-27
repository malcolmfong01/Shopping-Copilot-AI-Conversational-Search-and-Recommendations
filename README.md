# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

An intelligent conversational shopping agent that navigates real-world customer dynamics over a 50K-product clothing catalog, using intent routing, multi-turn dialog strategy, and LLM-powered ranking.

## Quick Start

```bash
# 1. Install dependencies (pick one LLM provider)
uv sync --extra gemini    # Google Gemini (free)
# OR: uv sync --extra groq  # Groq/Llama (free)

# 2. Download required data
./data/download.sh

# 3. Precompute embeddings (one-time, ~2-5 min)
python -m src.embeddings.precompute

# 4. Set your LLM API key
export GOOGLE_API_KEY="your-key-here"
# OR: export GROQ_API_KEY="gsk_..."

# 5. Run mini evaluation (20 sessions, fast)
./scripts/eval_mini.sh

# 6. Run full evaluation (200 sessions)
./scripts/eval_full.sh
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/problem-statement.md](docs/problem-statement.md) | Full challenge description and 4 pillars |
| [docs/evaluation.md](docs/evaluation.md) | Scoring formula, metrics, baseline results |
| [docs/agent-api-contract.md](docs/agent-api-contract.md) | Agent interface and message schemas |
| [docs/data-guide.md](docs/data-guide.md) | Catalog/session schemas, simulator behavior |
| [docs/deliverables.md](docs/deliverables.md) | Submission requirements and judging criteria |
| [docs/resources.md](docs/resources.md) | Links and strategic insights |

## Project Structure

```
.
├── data/                    # Competition data (downloaded, gitignored)
│   ├── download.sh          # Fetches catalog + sessions via gh CLI
│   └── embeddings/          # Precomputed vectors (generated locally)
├── docs/                    # Challenge documentation
├── src/
│   ├── agent.py             # Main Agent class (API contract implementation)
│   ├── llm_client.py        # Provider-agnostic LLM interface (Groq/Gemini)
│   ├── retrieval/           # BM25 + dense + hybrid RRF merge
│   ├── ranking/             # LLM re-ranking (Yanyox)
│   ├── dialog/              # State management, attribute selection, intent detection
│   └── embeddings/          # Precomputation script
├── evaluator/               # Official local evaluator
├── scripts/                 # Eval runner scripts
├── tasks/                   # Team task specs
└── pyproject.toml
```

## Key Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Hit Rate@10 | 12.5% | Higher |
| MRR | 0.068 | Higher |
| MTTC | 9.81 turns | Lower |
| **Composite** | **0.107** | **Higher** |

Scoring: `0.50 * hit_rate + 0.30 * mrr + 0.20 * efficiency`
