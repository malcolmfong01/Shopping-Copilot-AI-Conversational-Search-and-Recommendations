"""LLM-based candidate re-ranking and reply templates.

rank_candidates() sends the top candidates plus session context to the LLM
and returns ordered parent_asins (best first, max 10). Falls back to
constraint-match order when the LLM is unavailable or returns invalid JSON.

generate_message() builds a short template reply (cosmetic; not scored).
"""

import json
import os
import re

from src.dialog.state import SessionState
from src.llm_client import llm_call, _debug

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


def _constraint_match_score(candidate: dict, state: SessionState) -> float:
    """Score how many active constraint values appear in a candidate."""
    if not state.constraints:
        return 0.0

    searchable_parts = [
        candidate.get("title", ""),
        candidate.get("store", ""),
        candidate.get("categories", []),
        candidate.get("features", []),
        candidate.get("details", {}),
        candidate.get("description", []),
    ]

    def values_from(part: object) -> list[object]:
        if isinstance(part, dict):
            return list(part.values())
        if isinstance(part, (list, tuple, set)):
            return list(part)
        return [part]

    searchable = " ".join(
        str(value)
        for part in searchable_parts
        for value in values_from(part)
        if value
    ).lower()

    matched = 0
    total = 0
    for value in state.constraints.values():
        for part in str(value).split("|"):
            tokens = re.findall(r"[a-z0-9]+", part.lower())
            if not tokens:
                continue
            total += 1
            if part.lower() in searchable:
                matched += 1
            elif sum(token in searchable for token in tokens) / len(tokens) >= 0.8:
                matched += 1
    return matched / total if total else 0.0


def _constraint_ranked_candidates(candidates: list[dict], state: SessionState) -> list[str]:
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            _constraint_match_score(candidate, state),
            float(candidate.get("price", 0) or 0),
        ),
        reverse=True,
    )
    return [candidate["parent_asin"] for candidate in ranked[:10]]


def rank_candidates(
    candidates: list[dict],
    state: SessionState,
) -> list[str]:
    """Re-rank candidates using LLM. Returns ordered parent_asins (best first, max 10)."""
    if not candidates:
        return []

    _debug(f"rank_candidates CALLED: candidates={len(candidates)}")

    candidate_descriptions = []
    for i, candidate in enumerate(candidates[:20]):
        title = str(candidate.get("title", "Unknown"))[:180]
        categories = " ".join(str(value) for value in candidate.get("categories", [])[:2])
        description = f"[{i}] {title} | {categories}"
        if candidate.get("features"):
            features = candidate["features"]
            if isinstance(features, list):
                features = ", ".join(str(value) for value in features[:4])
            description += f" | features: {str(features)[:300]}"
        if candidate.get("details"):
            description += f" | details: {str(candidate['details'])[:300]}"
        if candidate.get("price"):
            description += f" | ${candidate['price']}"
        candidate_descriptions.append(description)

    context = state.get_context_summary()

    # Build constraint matching hints for the LLM
    constraint_keys = list(state.constraints.keys())
    if constraint_keys:
        constraint_guidance = f"Match products against these user attributes first: {', '.join(constraint_keys)}. Products matching ALL constraints are best."
    else:
        constraint_guidance = "User has not stated specific constraints yet. Rank by general product quality and relevance."

    prompt = f"""You are reranking shopping candidates. GOAL: Put products that match the user's stated preferences as high as possible.

TASK: Return a JSON array of candidate indices, ranked by how well each matches the user's preferences.

CRITICAL RULES:
- Return ONLY valid JSON array format: [0, 3, 7, 2]
- No markdown fences, no prose, no explanations.
- Use at most 10 indices from the candidates below (0-based).
- Do NOT invent or repeat indices; each index appears at most once.

RANKING STRATEGY (strict order):
1. Tier 1 (best): Products matching ALL or most of the user's stated constraints.
2. Tier 2: Products matching 3+ user constraints.
3. Tier 3: Products matching 2 user constraints.
4. Tier 4 (fallback): Products matching 1 or 0 constraints.

Within each tier, prefer products with higher relevance (better title/category match).

Constraint matching hint:
{constraint_guidance}

User conversation context:
{context}

User's stated preferences:
{json.dumps(state.constraints, ensure_ascii=False)}

Candidates to rank (format: [index] title | categories | features):
{chr(10).join(candidate_descriptions)}

Output: Return ONLY the JSON array. No other text."""

    global last_rank_meta
    content = llm_call(prompt, max_tokens=600)
    _debug(f"llm_call returned: {repr(content)[:500]}")
    if content:
        indices = _extract_json_array(content)
        if indices is not None:
            result = [
                candidates[index]["parent_asin"]
                for index in indices
                if 0 <= index < len(candidates)
            ][:10]
            if result:
                model_result = list(result)
                # Preserve the model's semantic ordering within each exact-match tier.
                model_position = {asin: position for position, asin in enumerate(result)}
                remaining = [
                    candidate["parent_asin"]
                    for candidate in candidates
                    if candidate["parent_asin"] not in model_position
                ]
                result.extend(remaining)
                result.sort(
                    key=lambda asin: (
                        _constraint_match_score(
                            next(candidate for candidate in candidates if candidate["parent_asin"] == asin),
                            state,
                        ),
                        -model_position.get(asin, len(model_position)),
                    ),
                    reverse=True,
                )
                result = result[:10]
                last_rank_meta = {"used": True}
                if os.environ.get("DEBUG_LLM") == "1":
                    score_by_asin = {
                        candidate["parent_asin"]: round(_constraint_match_score(candidate, state), 3)
                        for candidate in candidates
                    }
                    _debug(f"MODEL ORDER: {model_result}")
                    _debug(
                        f"FINAL ORDER: {result} | CONSTRAINT SCORES: "
                        f"{[score_by_asin[asin] for asin in result]}"
                    )
                    _debug(f"rank_candidates LLM SUCCESS: returned={len(result)}")
                return result

    last_rank_meta = {"used": False}
    fallback = _constraint_ranked_candidates(candidates, state)
    _debug(f"rank_candidates FALLBACK: constraint_match_order={fallback}")
    return fallback


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
