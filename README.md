# Shopping Copilot: AI Conversational Search and Recommendations

TikTok TechJam 2026 — Track 4

An intelligent conversational shopping agent that navigates real-world customer dynamics over a 50K-product clothing catalog, using intent routing, multi-turn dialog strategy, and LLM-powered ranking.

## Quick Start

```bash
# 1. Download required data
./data/download.sh

# 2. (coming soon) Install dependencies and run evaluator
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
├── data/               # Competition data (downloaded, gitignored)
│   ├── download.sh     # Script to fetch catalog + sessions
│   └── README.md       # Data file documentation
├── docs/               # All challenge documentation
└── README.md
```

## Key Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Hit Rate@10 | 12.5% | Higher |
| MRR | 0.068 | Higher |
| MTTC | 9.81 turns | Lower |
| **Composite** | **0.107** | **Higher** |

Scoring: `0.50 * hit_rate + 0.30 * mrr + 0.20 * efficiency`
