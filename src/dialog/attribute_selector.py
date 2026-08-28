"""Attribute selection module. OWNED BY YANYOX.

Interface contract:
- select_attribute() receives session state + candidate pool stats
- Returns one of the allowed attribute strings

The current implementation uses a priority-based heuristic:
- Turn 1: always ask "category" (most discriminating for clothing)
- Later turns: pick the attribute with highest candidate variance

Yanyox can replace this with LLM-based selection for better results.
"""

import json
from collections import Counter

from src.dialog.state import ALLOWED_ATTRIBUTES, SessionState
from src.llm_client import llm_call

ATTRIBUTE_PRIORITY = [
    "feature",
    "other",
    "material",
    "color",
    "style",
    "use_case",
    "size",
    "category",
    "budget",
    "brand",
]


def select_attribute(
    state: SessionState,
    candidate_stats: dict[str, dict[str, int]] | None = None,
) -> str:
    """Select the best attribute to ask about next.

    Args:
        state: Current session state with constraints and history.
        candidate_stats: Distribution of attribute values in current candidate pool.
            e.g. {"category": {"dress": 12, "shoes": 5}, "color": {"black": 8, "red": 3}}

    Returns:
        One of the allowed attribute strings.
    """
    unasked = state.get_unasked_attributes()
    if not unasked:
        return "other"

    if candidate_stats:
        result = _llm_select(state, candidate_stats, unasked)
        if result:
            return result

    for attr in ATTRIBUTE_PRIORITY:
        if attr in unasked:
            return attr

    return unasked[0]


def _llm_select(
    state: SessionState,
    candidate_stats: dict[str, dict[str, int]],
    unasked: list[str],
) -> str | None:
    """LLM-based attribute selection. Picks the most discriminating attribute."""
    stats_summary = {k: dict(Counter(v).most_common(5)) for k, v in candidate_stats.items() if k in unasked}

    prompt = f"""You are optimizing a shopping search. Pick the ONE attribute to ask about next that will best narrow down the product pool.

User context: {state.get_context_summary()}
Already asked: {state.attributes_asked}
Available attributes to ask: {unasked}
Current candidate pool distribution:
{json.dumps(stats_summary, indent=2)}

Return ONLY the attribute name (one word), nothing else."""

    chosen = llm_call(prompt, max_tokens=20)
    if chosen:
        chosen = chosen.strip().lower().strip('"\'')
        if chosen in ALLOWED_ATTRIBUTES and chosen in unasked:
            return chosen
    return None


def compute_candidate_stats(candidates: list[dict]) -> dict[str, dict[str, int]]:
    """Compute attribute value distributions from a candidate list."""
    stats: dict[str, Counter] = {attr: Counter() for attr in ALLOWED_ATTRIBUTES}

    for product in candidates:
        categories = product.get("categories", [])
        if categories:
            stats["category"][categories[0] if isinstance(categories, list) else str(categories)] += 1

        if product.get("store"):
            stats["brand"][product["store"]] += 1

        title_lower = product.get("title", "").lower()
        for color in ["black", "white", "red", "blue", "green", "pink", "brown", "grey", "navy", "beige"]:
            if color in title_lower:
                stats["color"][color] += 1

        if product.get("price"):
            try:
                price = float(product["price"])
            except (ValueError, TypeError):
                continue
            if price < 25:
                stats["budget"]["under $25"] += 1
            elif price < 50:
                stats["budget"]["$25-50"] += 1
            elif price < 100:
                stats["budget"]["$50-100"] += 1
            else:
                stats["budget"]["over $100"] += 1

    return {k: dict(v) for k, v in stats.items() if v}
