# Yanyox's Task Spec: LLM Prompt Strategy

## Your Role

You own the **LLM intelligence layer** — the prompts that make the agent smart. The retrieval pipeline (BM25 + vector search) feeds you candidate products; your prompts decide what to recommend and what to ask.

## What You're Building

You have **3 modules** to implement. Each has a clear interface — you fill in the prompt logic.

---

### 1. Re-Ranking (`src/ranking/llm_ranker.py`)

**What it does**: Takes 20 candidate products + conversation context → returns the 10 best-matching products in order.

**Interface**:
```python
def rank_candidates(candidates: list[dict], state: SessionState) -> list[str]:
    """
    Args:
        candidates: Top-20 products. Each has: parent_asin, title, categories, features, details, store, description, price
        state: Session context with .constraints (dict), .conversation_history (list), .user_profile (dict)

    Returns:
        Ordered list of parent_asin strings (best first, max 10)
    """
```

**Why it matters**: This directly controls MRR (30% of score). Putting the right product at position 1 gives MRR=1.0 vs position 10 giving MRR=0.1.

**Current placeholder**: Just passes through retrieval order (no re-ranking).

**Your job**: Write a prompt that:
- Takes the user's accumulated preferences/constraints
- Compares them against each candidate's attributes
- Returns the best matches ordered by relevance

---

### 2. Attribute Selection (`src/dialog/attribute_selector.py`)

**What it does**: Decides which attribute to ask about on each turn.

**Interface**:
```python
def select_attribute(state: SessionState, candidate_stats: dict) -> str:
    """
    Args:
        state: Has .attributes_asked, .constraints, .turn, .conversation_history
        candidate_stats: Distribution of values in current pool, e.g.:
            {"category": {"dress": 12, "shoes": 5}, "color": {"black": 8, "red": 3}}

    Returns:
        One of: "category"|"material"|"color"|"size"|"style"|"brand"|"budget"|"feature"|"use_case"|"other"
    """
```

**Why it matters**: Each turn you can only ask ONE question. Picking the most discriminating attribute narrows the pool fastest → better MTTC (efficiency).

**Current placeholder**: Fixed priority order (category → budget → style → ...).

**Your job**: Write a prompt that looks at what's known, what's not, and the candidate distribution to pick the attribute that will most reduce ambiguity.

**Rules**:
- Turn 1: always ask "category" (this is hardcoded and correct — don't change it)
- Turn 2+: LLM decides based on what's left

---

### 3. Message Generation (`src/ranking/llm_ranker.py` → `generate_message()`)

**What it does**: Generates the conversational text reply to the user.

**Interface**:
```python
def generate_message(state: SessionState, recommendations: list[dict], ask_attribute: str | None) -> str:
    """
    Returns a natural-language reply that:
    - Acknowledges what the user said
    - Briefly mentions top recommendation(s)
    - Asks about the chosen attribute naturally
    """
```

**Current placeholder**: Template-based ("Based on your preferences, I'd recommend X. What color do you prefer?")

**Your job**: Make it conversational and natural. Keep it SHORT (2-3 sentences max) — the simulator doesn't care about length, only about `ask_attribute` and `recommendations`.

---

## How to Test

```bash
# Run mini eval (20 sessions, ~2-5 min)
./scripts/eval_mini.sh

# Check results — you're beating baseline if score > 0.107
```

## LLM Setup

We use **Groq** (free tier, Llama 3.3 70B):
1. Get free API key at https://console.groq.com
2. Set it: `export GROQ_API_KEY=gsk_...`
3. The modules already call Groq — just improve the prompts

## Key Facts

- **Scoring**: `0.50 * hit_rate@10 + 0.30 * MRR + 0.20 * efficiency`
- **Max 10 turns** per session
- **Always recommend + ask** every turn (both fields filled)
- **Allowed attributes**: category, material, color, size, style, brand, budget, feature, use_case, other
- **Catalog**: 50K clothing products (title, categories, features, details, store, description, price)
- **Scenarios**: buying (40%), browsing (40%), intent_override (15%), boundary (5%)

## What NOT to Touch

- `src/retrieval/` — that's the retrieval pipeline (my domain)
- `src/dialog/state.py` — shared state structure (coordinate with me if you need changes)
- `evaluator/` — official eval code, don't modify

## Tips

- The simulator reveals constraints progressively when you ask valid attributes
- For intent_override: user changes mind at turn 3-4. The detector in `intent_detector.py` catches this and flushes constraints — you just need to handle the fresh start gracefully in your prompts
- Keep prompts concise — Groq has rate limits on free tier. Shorter prompts = more evals per minute
- The `state.get_context_summary()` method gives you a pre-formatted context string
