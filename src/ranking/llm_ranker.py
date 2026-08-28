"""LLM-based re-ranking module. OWNED BY YANYOX.

Interface contract:
- rank_candidates() receives top-20 products + full session context
- Returns an ordered list of parent_asins (best first, max 10)
- generate_message() produces a conversational reply

rank_candidates() calls the LLM with candidate descriptions + user context,
falls back to retrieval order if LLM is unavailable or returns invalid JSON.
generate_message() uses template strings (cosmetic only, not scored).
"""

import json

from src.dialog.state import SessionState
from src.llm_client import llm_call


def rank_candidates(
    candidates: list[dict],
    state: SessionState,
) -> list[str]:
    """Re-rank candidates using LLM. Returns ordered parent_asins (best first, max 10).

    Args:
        candidates: Top-20 products with full metadata from hybrid retrieval.
        state: Full session context (constraints, history, profile).

    Returns:
        List of up to 10 parent_asin strings, best match first.
    """
    if not candidates:
        return []

    candidate_descriptions = []
    for i, c in enumerate(candidates[:20]):
        desc = f"[{i}] {c.get('title', 'Unknown')} | {' '.join(c.get('categories', [])[:2])}"
        if c.get("price"):
            desc += f" | ${c['price']}"
        candidate_descriptions.append(desc)

    context = state.get_context_summary()

    prompt = f"""You are a shopping assistant. Given the user's preferences and conversation context, rank these products by relevance. Return ONLY a JSON array of indices (0-based) in order of best match, max 10 items.

Context:
{context}

Known preferences: {json.dumps(state.constraints)}

Candidates:
{chr(10).join(candidate_descriptions)}

Return JSON array of indices only, e.g. [3, 0, 7, ...]"""

    content = llm_call(prompt, max_tokens=200)
    if content:
        try:
            indices = json.loads(content)
            return [candidates[i]["parent_asin"] for i in indices if isinstance(i, int) and i < len(candidates)][:10]
        except (json.JSONDecodeError, IndexError):
            pass

    return [c["parent_asin"] for c in candidates[:10]]


def generate_message(
    state: SessionState,
    recommendations: list[dict],
    ask_attribute: str | None,
) -> str:
    """Generate a conversational reply to the user.

    Placeholder implementation. Yanyox replaces with LLM-generated responses.
    """
    if not recommendations:
        msg = "Let me help you find the perfect item."
    else:
        top = recommendations[0]
        msg = f"Based on your preferences, I'd recommend: {top.get('title', 'this item')}."

    if ask_attribute:
        attribute_questions = {
            "category": "What type of product are you looking for?",
            "material": "Do you have a material preference?",
            "color": "Any color preference?",
            "size": "What size do you need?",
            "style": "What style are you going for?",
            "brand": "Any brand preference?",
            "budget": "What's your budget range?",
            "feature": "Any specific features you need?",
            "use_case": "What will you be using this for?",
            "other": "Any other preferences I should know about?",
        }
        msg += f" {attribute_questions.get(ask_attribute, 'Tell me more about what you want.')}"

    return msg
