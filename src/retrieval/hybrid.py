from __future__ import annotations

import re

from src.retrieval.bm25 import BM25Index

try:
    from src.retrieval.dense import DenseIndex
except ImportError:
    DenseIndex = None

RRF_K = 60


def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[str, float]],
    top_k: int = 20,
) -> list[str]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, (asin, _) in enumerate(ranked_list):
            scores[asin] = scores.get(asin, 0.0) + 1.0 / (RRF_K + rank + 1)

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

        if self._dense:
            dense_results = self._dense.search(query, top_k=retrieval_k)
            merged_asins = reciprocal_rank_fusion(bm25_results, dense_results, top_k=retrieval_k)
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

        filtered = []
        scored_fallback = []
        for asin in asins:
            product = self._catalog.get(asin)
            if not product:
                continue
            if self._matches_all(product, constraints):
                filtered.append(asin)
            else:
                score = self._partial_score(product, constraints)
                scored_fallback.append((asin, score))

        if not filtered:
            scored_fallback.sort(key=lambda x: x[1], reverse=True)
            return [asin for asin, _ in scored_fallback[:50]]

        scored_fallback.sort(key=lambda x: x[1], reverse=True)
        top_partial = [asin for asin, s in scored_fallback[:20] if s > 0]
        filtered_set = set(filtered)
        extras = [a for a in top_partial if a not in filtered_set]
        return filtered + extras

    def _matches_all(self, product: dict, constraints: dict[str, str]) -> bool:
        searchable = self._searchable_text(product)
        for attr, value in constraints.items():
            if not value:
                continue
            if attr == "budget":
                budget_range = _parse_budget(value)
                if budget_range:
                    price = product.get("price")
                    if not price or not (budget_range[0] <= price <= budget_range[1]):
                        return False
                continue
            if value.lower() not in searchable:
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
            total += 1
            if attr == "budget":
                budget_range = _parse_budget(value)
                if budget_range:
                    price = product.get("price")
                    if price and budget_range[0] <= price <= budget_range[1]:
                        matched += 1
                continue
            if value.lower() in searchable:
                matched += 1
            else:
                value_tokens = _tokenize(value)
                if value_tokens and len(value_tokens & searchable_tokens) / len(value_tokens) >= 0.8:
                    matched += 1
        return matched / total if total else 1.0

    def _searchable_text(self, product: dict) -> str:
        return (
            f"{product.get('title', '')} "
            f"{' '.join(product.get('categories', []))} "
            f"{' '.join(product.get('features', []) if isinstance(product.get('features'), list) else [])} "
            f"{product.get('store', '')}"
        ).lower()

    def _full_searchable_text(self, product: dict) -> str:
        parts = [
            product.get("title", ""),
            " ".join(product.get("categories", [])),
            " ".join(product.get("features", []) if isinstance(product.get("features"), list) else []),
            product.get("store", "") or "",
        ]
        if isinstance(product.get("details"), dict):
            parts.append(" ".join(f"{k} {v}" for k, v in product["details"].items()))
        return " ".join(parts).lower()
