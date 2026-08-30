# LLM Prompt Strategy — Task Spec

## Start Here (Read In Order)

| # | Doc | What you'll learn |
|---|-----|-------------------|
| 1 | [README.md](../README.md) | Repo overview, architecture, project structure, team split |
| 2 | [docs/problem-statement.md](../docs/problem-statement.md) | The full competition challenge and what we're building |
| 3 | [docs/evaluation.md](../docs/evaluation.md) | How scoring works (hit_rate, MRR, efficiency, composite) |
| 4 | [docs/experiments.md](../docs/experiments.md) | What Malcolm tried on retrieval, scores, what worked/failed |
| 5 | [docs/agent-api-contract.md](../docs/agent-api-contract.md) | Agent interface — what `respond()` returns and how it's scored |
| 6 | [docs/data-guide.md](../docs/data-guide.md) | Catalog schema, session format, simulator behavior |
| 7 | This file | Your specific tasks, API contract, setup instructions |

---

## TL;DR

The retrieval pipeline scores **0.853** without any LLM. Your job: use a free-tier LLM (Groq Llama 3.3 70B) to push it above **0.90** through re-ranking and smarter attribute selection.

**What you own:**
1. **Re-rank** 20 candidates → best 10 (biggest impact: MRR)
2. **Pick next attribute** to ask the user (impacts efficiency/MTTC)
3. **Generate reply** message (cosmetic, for demo video only)

**Scoring:** `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`

---

## Architecture

```
User message → [Constraint Extraction] → [Build Query] → [BM25 Search] → [Soft Constraint Rank] → 50 candidates
                                                                                                        ↓
                                                                                          [YOUR CODE: rank_candidates()]
                                                                                          Re-rank top 20 → best 10
                                                                                                        ↓
                                                                                          [YOUR CODE: select_attribute()]
                                                                                          Pick most discriminating attribute
                                                                                                        ↓
                                                                                          [YOUR CODE: generate_message()]
                                                                                          Natural reply (2-3 sentences)
                                                                                                        ↓
                                                                                          Return: {recommendations, ask_attribute, message}
```

Every turn ALWAYS returns both recommendations AND asks one attribute.

**Note on dense retrieval:** The 0.853 baseline is BM25-only. Dense retrieval (MiniLM + FAISS) was evaluated and does not improve BM25 for this evaluator. It's opt-in via `ENABLE_DENSE=1` env var. Don't enable it — your LLM should build on the BM25-only baseline.

---

## Your 3 Functions

### 1. `rank_candidates(candidates, state)` → `list[str]`

**File:** `src/ranking/llm_ranker.py`

**Input:**
- `candidates`: list of 20 product dicts with keys: `parent_asin`, `title`, `categories`, `features`, `details`, `store`, `description`, `price`
- `state`: `SessionState` object (see below)

**Output:** Ordered list of `parent_asin` strings, best match first (up to 10).

**Why it matters:** MRR = 1/rank. Target at #1 → MRR=1.0. At #5 → MRR=0.2. At #10 → MRR=0.1. This function has 2x the score weight of attribute selection.

**Current behavior:** Passes through retrieval order (no intelligence). This is your biggest opportunity.

---

### 2. `select_attribute(state, candidate_stats)` → `str`

**File:** `src/dialog/attribute_selector.py` (specifically `_llm_select()`)

**Input:**
- `state`: SessionState
- `candidate_stats`: dict of attribute → value distribution in current pool

```python
# Example candidate_stats:
{
    "category": {"dress": 12, "shoes": 5},
    "color": {"black": 8, "red": 3},
    "budget": {"$25-50": 7, "under $25": 4}
}
```

**Output:** One of: `category`, `material`, `color`, `size`, `style`, `brand`, `budget`, `feature`, `use_case`, `other`

**Current behavior:** Heuristic priority order (feature → other → material → ...). Your LLM can do better by analyzing which attribute would maximally narrow the candidate pool.

---

### 3. `generate_message(state, recommendations, ask_attribute)` → `str`

**File:** `src/ranking/llm_ranker.py`

**Output:** Natural language reply. Keep it short (2-3 sentences). Not scored — only for demo video.

---

## SessionState (what you get)

```python
state.constraints        # {"category": "dress", "color": "black", "feature": "waterproof|breathable"}
state.conversation_history  # [{"role": "user/assistant", "content": "..."}]
state.user_profile       # {"summary": "...", "purchase_frequency": "...", "preference_tags": [...]}
state.turn               # Current turn number
state.attributes_asked   # ["category", "feature", ...]
state.last_candidates    # Full 50 candidates from retrieval
state.get_context_summary()  # Pre-formatted string of recent context
```

**Note on constraints:** Pipe-separated values (e.g. `"waterproof|breathable"`) mean multiple values for the same attribute. Each part is an independent requirement.

---

## Evaluator Behavior

The simulator has a hidden target product. When you set `ask_attribute`:

| What you ask | What happens |
|---|---|
| Valid attribute matching undisclosed constraint | Reveals it: "For that, what matters is: leather; waterproof" |
| Valid attribute, nothing left | "I don't have an additional preference for [attribute]" |
| `null` | "Ask me about one specific attribute" (wasted turn) |

**Scenario types:**
- **buying** (40%): Clear intent, reveals constraints readily
- **browsing** (40%): Vague preferences, broader exploration
- **intent_override** (15%): User changes mind at turn 3-4 (constraints auto-flushed)
- **boundary** (5%): Refuses first question regardless of attribute

---

## Setup

```bash
# 1. Install deps
uv sync --extra groq

# 2. Get a free Groq API key (instant signup): https://console.groq.com
export GROQ_API_KEY="gsk_..."

# 3. Download data (if not already done)
bash data/download.sh
```

That's it. You're ready to edit code and test.

---

## Testing Your Changes

The evaluator simulates shopping conversations and scores the agent. Run it to see whether a prompt change improved things.

**Iteration loop:**
1. Edit prompts in `src/ranking/llm_ranker.py` or `src/dialog/attribute_selector.py`
2. Run mini eval to check the score
3. Compare to 0.853 baseline (the retrieval-only score without LLM improvements)

The mini eval (20 sessions) is your main feedback tool for iterating quickly. The full eval runs all 200 sessions from the public set — use it to validate your best version before committing to it as the final pipeline.

### Mini Eval

20 sessions, ~40 LLM calls, ~1 minute:

```bash
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
```

### Full Eval

All 200 sessions from the public set. Takes ~2 hours due to Groq's 30 RPM rate limit. Run this to validate your best prompt version — if the score holds across all scenarios, that's your final pipeline.

```bash
.venv/bin/python -m evaluator.local_evaluator
```

---

## LLM Provider

Use `src/llm_client.py`:

```python
from src.llm_client import llm_call
response = llm_call("your prompt here", max_tokens=200)
```

**Recommended:** Groq Llama 3.3 70B (`GROQ_API_KEY`)
- Free tier: 30 RPM, 14400 RPD
- Mini eval (20 sessions): instant
- Full eval (200 sessions): ~2 hours

**Gotchas:**
- Llama 3.3 70B is weaker at structured JSON than GPT-4/Claude — be very explicit about output format
- If response is invalid JSON, `llm_call()` returns `None` and system silently falls back to heuristic
- You won't see errors when this happens, just no improvement in score
- Keep prompts concise (shorter = faster + less rate limiting)

---

## Files You Own

| File | What to edit |
|------|-------------|
| `src/ranking/llm_ranker.py` | `rank_candidates()` and `generate_message()` |
| `src/dialog/attribute_selector.py` | `_llm_select()` inside `select_attribute()` |

## Files to Read (don't modify)

| File | Why |
|------|-----|
| `src/dialog/state.py` | Understand SessionState |
| `src/llm_client.py` | How `llm_call()` works |
| `evaluator/local_evaluator.py` | How scoring works |
| `docs/evaluation.md` | Scoring formula details |
| `docs/experiments.md` | What retrieval optimizations were tried |

---

## Tips

1. **Study failures first:** After mini eval, look at `results/latest.json` → sessions where `"hit": false`. Understand WHY the target wasn't in top 10.
2. **Re-ranking has the biggest bang:** If the target is already in the 20 candidates (it usually is), ranking it #1 vs #5 is a huge MRR difference.
3. **The simulator is deterministic:** Same session always reveals same constraints in same order.
4. **Don't over-engineer messages:** Only `ask_attribute` and `recommendations` are scored.
5. **Prompt engineering > architecture:** Your main lever is crafting prompts that make Llama 3.3 70B reliably output correct JSON rankings.
