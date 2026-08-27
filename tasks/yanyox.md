# LLM Prompt Strategy — Task Spec

## TL;DR

We're building a conversational shopping agent that searches a 50K-product catalog through multi-turn dialog. The retrieval pipeline surfaces ~50 candidate products per turn. **Your job**: write the LLM prompts that (1) re-rank these candidates so the right product lands at #1, (2) decide which attribute to ask next to narrow the search fastest, and (3) generate natural conversational replies.

The system uses **free-tier LLMs** (Google Gemini Flash or Groq/Llama 3.3 70B). No paid APIs needed.

**What success looks like**: the target product appears in top-10 as early as possible. Score = `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`. Baseline (no LLM, no questions asked) scores 0.107. We need to beat that significantly.

---

## Architecture Overview

```
User message → [State Update] → [Hybrid Retrieval: BM25 + Dense] → Top 50 candidates
                                                                          ↓
                                                              [YOUR CODE: Re-rank top 20 → best 10]
                                                              [YOUR CODE: Pick next attribute to ask]
                                                              [YOUR CODE: Generate reply message]
                                                                          ↓
                                                              Return: recommendations + ask_attribute + message
```

Every turn, the agent ALWAYS returns both recommendations AND asks one attribute. This means:
- Turn 1: even before knowing much, we recommend our best guess AND ask a question
- Each subsequent turn: refined recommendations + another question
- The session ends the moment the target product appears in our top-10

---

## Your 3 Modules

### 1. Re-Ranking (`src/ranking/llm_ranker.py` → `rank_candidates()`)

**Input**: 20 candidate products + full session context
**Output**: Ordered list of up to 10 `parent_asin` strings (best match first)

```python
def rank_candidates(candidates: list[dict], state: SessionState) -> list[str]:
```

Each candidate dict has: `parent_asin`, `title`, `categories`, `features`, `details`, `store`, `description`, `price`

The `state` object gives you:
- `state.constraints` — accumulated preferences: `{"category": "dress", "color": "black"}`
- `state.conversation_history` — full dialog so far
- `state.user_profile` — purchase frequency, preference tags, summary
- `state.get_context_summary()` — pre-formatted string of recent context

**Why this matters**: MRR = 1/rank. Target at position 1 → MRR=1.0. Position 5 → MRR=0.2. Position 10 → MRR=0.1.

**Current placeholder**: passes through retrieval order (no intelligence).

---

### 2. Attribute Selection (`src/dialog/attribute_selector.py` → `select_attribute()`)

**Input**: Session state + distribution of attribute values in current candidate pool
**Output**: One attribute string

```python
def select_attribute(state: SessionState, candidate_stats: dict) -> str:
```

`candidate_stats` looks like:
```python
{
    "category": {"dress": 12, "shoes": 5, "jacket": 3},
    "color": {"black": 8, "red": 3, "blue": 2},
    "budget": {"$25-50": 7, "under $25": 4, "over $100": 2}
}
```

**Allowed return values**: `category`, `material`, `color`, `size`, `style`, `brand`, `budget`, `feature`, `use_case`, `other`

**Rules**:
- Turn 1: hardcoded to "category" (don't change this — it's correct)
- Turn 2+: your LLM decides based on what maximally narrows the pool

**Why this matters**: each turn costs efficiency. Pick the attribute that eliminates the most candidates per turn → faster convergence → better MTTC.

---

### 3. Message Generation (`src/ranking/llm_ranker.py` → `generate_message()`)

**Input**: Session state + current recommendations + chosen attribute
**Output**: Natural language reply (2-3 sentences max)

```python
def generate_message(state: SessionState, recommendations: list[dict], ask_attribute: str | None) -> str:
```

**Requirements**: Acknowledge the user's input, briefly reference your top recommendation, naturally ask about the chosen attribute. Keep it SHORT — the simulator doesn't evaluate message quality, only `ask_attribute` and `recommendations` are scored.

---

## How the Simulator Works (Important)

The evaluator simulates a user with a hidden target product. When you set `ask_attribute`:

| What you ask | What happens |
|---|---|
| Valid attribute matching an undisclosed constraint | Simulator reveals it: "For that, what matters is: leather; waterproof" |
| Valid attribute, nothing left to reveal | "I don't have an additional preference for [attribute]" |
| `null` | "Ask me about one specific attribute" (wasted turn) |

**Scenario types** (your prompts should handle all):
- **buying** (40%): clear intent, reveals constraints readily
- **browsing** (40%): vague preferences, broader exploration
- **intent_override** (15%): user changes mind at turn 3-4. Constraints get flushed automatically — you just need to handle the fresh context gracefully
- **boundary** (5%): refuses first question with "I don't have a preference" regardless of attribute

---

## Setup & Testing

```bash
# Install deps
uv sync --extra gemini

# Set API key (Gemini Flash — free)
export GOOGLE_API_KEY="<ask Malcolm for this>"

# Run mini eval (20 sessions)
./scripts/eval_mini.sh

# Run diagnostic to understand retrieval quality
python scripts/diagnostic.py
```

**Your iteration loop**: edit prompts → run mini eval → check score → repeat.

**Current score: 0.714** (no LLM, just BM25 + heuristic attribute selection).
Target: push above 0.80 with LLM re-ranking and smarter attribute selection.

---

## LLM Provider

The system uses `src/llm_client.py` which auto-detects your provider:
- **Recommended**: Groq Llama 3.3 70B (`GROQ_API_KEY`) — free tier: 30 RPM, 14400 RPD.
- **Fallback**: Google Gemini 3.6 Flash (`GOOGLE_API_KEY`) — free tier only allows ~20 requests/day, which likely won't be enough since a single mini eval needs ~40 LLM calls.

**Drawbacks to be aware of:**
- Groq's 30 RPM cap means a full 200-session eval takes ~2 hours (can't parallelise)
- Llama 3.3 70B is weaker at structured JSON output than GPT-4 or Claude — your prompts need to be very explicit about the output format or it may return malformed JSON (the system falls back to heuristics silently when this happens)
- If rate limited or the response is invalid, `llm_call()` returns `None` and the agent uses the fallback heuristic — you won't see an error, just no improvement in score

**Get a Groq key**: Sign up at https://console.groq.com (free, instant). Set it as:
```bash
export GROQ_API_KEY="gsk_..."
```

You call the LLM via:
```python
from src.llm_client import llm_call
response = llm_call("your prompt", max_tokens=200)
```

Keep prompts concise — shorter = faster eval iterations + lower risk of rate limiting.

**Rate limit math**: 200 sessions × 10 turns × 2 calls/turn = 4000 calls max for full eval. At 30 RPM, full eval takes ~2.2 hours. Use mini eval (20 sessions) for iteration — ~40 calls per run, instant.

---

## Files You Own

| File | What to edit |
|------|-------------|
| `src/ranking/llm_ranker.py` | `rank_candidates()` and `generate_message()` |
| `src/dialog/attribute_selector.py` | `select_attribute()` (specifically `_llm_select()`) |

## Files You Read But Don't Modify

| File | Why |
|------|-----|
| `src/dialog/state.py` | Understand the `SessionState` dataclass |
| `src/llm_client.py` | Understand how `llm_call()` works |
| `evaluator/local_evaluator.py` | Understand how scoring works |
| `docs/evaluation.md` | Scoring formula and scenario details |
| `docs/agent-api-contract.md` | API contract and attribute enum |

---

## Tips

- **Study failures**: after a mini eval, look at `results_mini.json` → find sessions where `hit: false` and understand why
- **The simulator is deterministic**: same session always reveals same constraints in same order
- **Re-ranking has the biggest impact on MRR** (30% of score): if the target is in the 20 candidates, ranking it #1 vs #10 is the difference between MRR=1.0 and MRR=0.1
- **Attribute selection has the biggest impact on efficiency** (20% of score): asking the right questions early means hitting the target sooner
- **Don't over-engineer messages**: the simulator only cares about `ask_attribute` and `recommendations`. Messages are cosmetic for the demo video only.
