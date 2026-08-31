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
import re

from src.dialog.state import SessionState
from src.llm_client import llm_call

last_rank_meta: dict = {"used": False}


def _extract_json_array(text: str | None) -> list[int] | None:
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.I)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if isinstance(data, list):
        indices = [item for item in data if isinstance(item, int)]
        if indices:
            return indices
    return None


def rank_candidates(
    candidates: list[dict],
    state: SessionState,
) -> list[str]:
    """Re-rank candidates using LLM. Returns ordered parent_asins (best first, max 10)."""
    if not candidates:
        return []

    candidate_descriptions = []
    for i, candidate in enumerate(candidates[:20]):
        description = f"[{i}] {candidate.get('title', 'Unknown')} | {' '.join(candidate.get('categories', [])[:2])}"
        if candidate.get("features"):
            features = candidate["features"]
            if isinstance(features, list):
                features = ", ".join(features[:5])
            description += f" | features: {features}"
        if candidate.get("details"):
            description += f" | details: {candidate['details']}"
        if candidate.get("price"):
            description += f" | ${candidate['price']}"
        candidate_descriptions.append(description)

    context = state.get_context_summary()
    prompt = f"""You are reranking the top candidates for a shopping assistant.

Task: sort the candidate indices by how well they match the user's stated preferences and conversation context.

Rules:
- Return ONLY valid JSON: a single array of integer indices, 0-based.
- No markdown fences, no prose, no explanations, no trailing commas.
- Use at most 10 indices.
- Prefer exact attribute matches (category, material, color, size, budget, use case, style, brand) over generic "looks good" items.
- If the user preferences are broad or vague, keep the strongest candidates near the top but still rank by textual relevance.
- Do not invent indices outside the provided candidate list.

Context:
{context}

Known preferences: {json.dumps(state.constraints, ensure_ascii=False)}

Candidates:
{chr(10).join(candidate_descriptions)}

Output format example:
[3, 0, 7, 12]

Final answer must be only the JSON array."""

    global last_rank_meta
    content = llm_call(prompt, max_tokens=1500)
    if content:
        indices = _extract_json_array(content)
        if indices is not None:
            result = [
                candidates[index]["parent_asin"]
                for index in indices
                if 0 <= index < len(candidates)
            ][:10]
            if result:
                last_rank_meta = {"used": True}
                return result

    last_rank_meta = {"used": False}
    return [candidate["parent_asin"] for candidate in candidates[:10]]


def generate_message(
    state: SessionState,
    recommendations: list[dict],
    ask_attribute: str | None,
) -> str:
    """Generate a conversational reply to the user."""
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
