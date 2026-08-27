from src.retrieval.bm25 import BM25Index
from src.retrieval.dense import DenseIndex

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


class HybridRetriever:
    def __init__(self, bm25: BM25Index, dense: DenseIndex, catalog: dict[str, dict]):
        self._bm25 = bm25
        self._dense = dense
        self._catalog = catalog

    def search(
        self,
        query: str,
        constraints: dict[str, str] | None = None,
        top_k: int = 20,
    ) -> list[dict]:
        retrieval_k = top_k * 5

        bm25_results = self._bm25.search(query, top_k=retrieval_k)
        dense_results = self._dense.search(query, top_k=retrieval_k)

        merged_asins = reciprocal_rank_fusion(bm25_results, dense_results, top_k=retrieval_k)

        if constraints:
            merged_asins = self._apply_constraints(merged_asins, constraints)

        results = []
        for asin in merged_asins[:top_k]:
            if asin in self._catalog:
                results.append(self._catalog[asin])
        return results

    def _apply_constraints(self, asins: list[str], constraints: dict[str, str]) -> list[str]:
        filtered = []
        for asin in asins:
            product = self._catalog.get(asin)
            if not product:
                continue
            if self._matches_constraints(product, constraints):
                filtered.append(asin)
        return filtered if filtered else asins[:20]

    def _matches_constraints(self, product: dict, constraints: dict[str, str]) -> bool:
        searchable = (
            f"{product.get('title', '')} "
            f"{' '.join(product.get('categories', []))} "
            f"{' '.join(product.get('features', []) if isinstance(product.get('features'), list) else [])} "
            f"{product.get('store', '')}"
        ).lower()

        for attr, value in constraints.items():
            if value and value.lower() not in searchable:
                return False
        return True
