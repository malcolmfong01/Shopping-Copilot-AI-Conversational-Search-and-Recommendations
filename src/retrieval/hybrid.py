from __future__ import annotations

import re

from src.retrieval.bm25 import BM25Index

try:
    from src.retrieval.dense import DenseIndex
except ImportError:
    DenseIndex = None

RRF_K = 10
BM25_ALPHA = 0.75
DENSE_ALPHA = 0.25

# Attribute labels for natural-language dense queries (matches MiniLM sentence style).
_DENSE_ATTR_PHRASES = {
    "category": "looking for",
    "material": "made of",
    "color": "in",
    "size": "size",
    "style": "style",
    "brand": "brand",
    "budget": "budget",
    "feature": "with",
    "use_case": "for",
    "other": "",
}


def build_dense_query(query: str, constraints: dict[str, str] | None = None) -> str:
    """Build a natural-language query for dense retrieval.

    Uses full category text and all constraint values (including pipe-separated
    multi-values), unlike BM25's keyword-fragment query.
    """
    if not constraints:
        return query

    parts: list[str] = []
    for attr, val in constraints.items():
        if not val:
            continue
        cleaned = re.sub(
            r"^(color|material|budget|size|style|brand|feature):\s*",
            "",
            val,
            flags=re.I,
        )
        # Expand pipe-separated multi-values into natural phrasing
        values = [p.strip() for p in cleaned.split("|") if p.strip()]
        value_text = " and ".join(values)
        phrase = _DENSE_ATTR_PHRASES.get(attr, "")
        if attr == "category":
            parts.append(f"{phrase} {value_text}".strip())
        elif phrase:
            parts.append(f"{phrase} {value_text}".strip())
        else:
            parts.append(value_text)

    if not parts:
        return query
    return " ".join(parts)


def reciprocal_rank_fusion(
    bm25_list: list[tuple[str, float]],
    dense_list: list[tuple[str, float]],
    top_k: int = 20,
) -> list[str]:
    scores: dict[str, float] = {}
    for rank, (asin, _) in enumerate(bm25_list):
        scores[asin] = scores.get(asin, 0.0) + BM25_ALPHA / (RRF_K + rank + 1)
    for rank, (asin, _) in enumerate(dense_list):
        scores[asin] = scores.get(asin, 0.0) + DENSE_ALPHA / (RRF_K + rank + 1)

    sorted_asins = sorted(scores, key=scores.get, reverse=True)
    return sorted_asins[:top_k]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _parse_budget(value: str) -> tuple[float, float] | None:
    m = re.search(r"under\s*\$?(\d+)", value, re.I)
    if m:
        return (0, float(m.group(1)))
    m = re.search(r"around\s*\$?(\d+)", value, re.I)
    if m:
        target = float(m.group(1))
        return (target * 0.7, target * 1.3)
    m = re.search(r"\$(\d+)\s*[-–]\s*\$?(\d+)", value)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.search(r"\$(\d+)", value)
    if m:
        target = float(m.group(1))
        return (target * 0.7, target * 1.3)
    return None


class HybridRetriever:
    def __init__(self, bm25: BM25Index, dense: DenseIndex | None, catalog: dict[str, dict]):
        self._bm25 = bm25
        self._dense = dense
        self._catalog = catalog

    def search(
        self,
        query: str,
        constraints: dict[str, str] | None = None,
        top_k: int = 50,
    ) -> list[dict]:
        retrieval_k = top_k * 4

        bm25_results = self._bm25.search(query, top_k=retrieval_k)

        use_dense = self._dense is not None
        if use_dense and constraints:
            n_specific = sum(
                1 for k, v in constraints.items()
                if v and k != "budget" and "|" not in v
            )
            if n_specific >= 2:
                use_dense = False

        if use_dense:
            try:
                dense_query = build_dense_query(query, constraints)
                dense_results = self._dense.search(dense_query, top_k=50)
                merged_asins = reciprocal_rank_fusion(bm25_results, dense_results, top_k=retrieval_k)
            except Exception:
                merged_asins = [asin for asin, _ in bm25_results]
        else:
            merged_asins = [asin for asin, _ in bm25_results]

        if constraints:
            merged_asins = self._soft_rank(merged_asins, constraints)

        results = []
        for asin in merged_asins[:top_k]:
            if asin in self._catalog:
                results.append(self._catalog[asin])
        return results

    def _soft_rank(self, asins: list[str], constraints: dict[str, str]) -> list[str]:
        if not constraints:
            return asins

        n_constraints = sum(1 for k, v in constraints.items() if v and k != "budget")
        near_threshold = (n_constraints - 1) / n_constraints if n_constraints > 1 else 0.5

        filtered = []
        scored_fallback = []
        high_bm25_partial = []
        for rank, asin in enumerate(asins):
            product = self._catalog.get(asin)
            if not product:
                continue
            if self._matches_all(product, constraints):
                filtered.append(asin)
            else:
                score = self._partial_score(product, constraints)
                scored_fallback.append((asin, score))
                if rank < 10 and score >= near_threshold:
                    high_bm25_partial.append(asin)

        if not filtered:
            scored_fallback.sort(key=lambda x: x[1], reverse=True)
            return [asin for asin, _ in scored_fallback[:50]]

        scored_fallback.sort(key=lambda x: x[1], reverse=True)
        top_partial = [asin for asin, s in scored_fallback[:20] if s > 0]
        filtered_set = set(filtered)
        extras = [a for a in top_partial if a not in filtered_set]

        result = filtered[:8]
        for a in high_bm25_partial:
            if a not in set(result):
                result.append(a)
        for a in filtered[8:]:
            if a not in set(result):
                result.append(a)
        for a in extras:
            if a not in set(result):
                result.append(a)
        return result

    def _matches_all(self, product: dict, constraints: dict[str, str]) -> bool:
        searchable = self._full_searchable_text(product)
        for attr, value in constraints.items():
            if not value:
                continue
            if attr == "budget":
                budget_range = _parse_budget(value)
                if budget_range:
                    price = product.get("price")
                    if not isinstance(price, (int, float)) or not (budget_range[0] <= price <= budget_range[1]):
                        return False
                continue
            parts = value.split("|") if "|" in value else [value]
            if not all(p.lower() in searchable for p in parts):
                return False
        return True

    def _partial_score(self, product: dict, constraints: dict[str, str]) -> float:
        if not constraints:
            return 1.0
        searchable = self._full_searchable_text(product)
        searchable_tokens = _tokenize(searchable)
        matched = 0
        total = 0
        for attr, value in constraints.items():
            if not value:
                continue
            if attr == "budget":
                total += 1
                budget_range = _parse_budget(value)
                if budget_range:
                    price = product.get("price")
                    if isinstance(price, (int, float)) and budget_range[0] <= price <= budget_range[1]:
                        matched += 1
                continue
            parts = value.split("|") if "|" in value else [value]
            for part in parts:
                total += 1
                if part.lower() in searchable:
                    matched += 1
                else:
                    part_tokens = _tokenize(part)
                    if part_tokens and len(part_tokens & searchable_tokens) / len(part_tokens) >= 0.8:
                        matched += 1
        return matched / total if total else 1.0

    def _full_searchable_text(self, product: dict) -> str:
        parts = [
            product.get("title", ""),
            " ".join(product.get("categories", [])),
            " ".join(product.get("features", []) if isinstance(product.get("features"), list) else []),
            product.get("store", "") or "",
        ]
        if isinstance(product.get("details"), dict):
            parts.append(" ".join(f"{k} {v}" for k, v in product["details"].items()))
        desc = product.get("description")
        if isinstance(desc, list):
            parts.append(" ".join(str(d) for d in desc))
        elif isinstance(desc, str):
            parts.append(desc)
        return " ".join(parts).lower()
