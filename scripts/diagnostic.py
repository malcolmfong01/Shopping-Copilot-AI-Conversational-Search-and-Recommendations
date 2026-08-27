"""Diagnostic pass: measure retrieval recall before optimizing anything else.

Run this FIRST to understand where the bottleneck is.
Answers: "If my retrieval returns top-K candidates, how often is the target in there?"

Usage:
    python scripts/diagnostic.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.bm25 import BM25Index


def coarse_category(values):
    excluded = {"clothing", "clothing shoes & jewelry", "clothing, shoes & jewelry"}
    cleaned = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part and part.lower() not in excluded:
                cleaned.append(part)
    return " ".join(cleaned[-2:]) if cleaned else "clothing item"


def main():
    catalog_path = "data/catalog.jsonl"
    dataset_path = "data/public_set.jsonl"

    print("Loading BM25 index...")
    bm25 = BM25Index(catalog_path)

    print("Loading catalog for target product lookup...")
    catalog = {}
    with open(catalog_path) as f:
        for line in f:
            p = json.loads(line)
            catalog[p["parent_asin"]] = p

    print("Loading evaluation sessions...")
    with open(dataset_path) as f:
        samples = [json.loads(line) for line in f]

    print(f"\n{'='*60}")
    print(f"RETRIEVAL RECALL DIAGNOSTIC ({len(samples)} sessions)")
    print(f"{'='*60}\n")

    results_by_k = {10: 0, 20: 0, 50: 0, 100: 0}
    results_by_scenario = {}

    for sample in samples:
        target = sample["ground_truth"]["parent_asin"]
        scenario = sample["scenario_type"]

        if scenario not in results_by_scenario:
            results_by_scenario[scenario] = {10: 0, 20: 0, 50: 0, 100: 0, "total": 0}
        results_by_scenario[scenario]["total"] += 1

        # Simulate the ACTUAL initial message the evaluator generates
        # The evaluator uses: "I'm looking for {coarse_category(product.categories)}..."
        product = catalog.get(target, {})
        category = coarse_category(product.get("categories", []))
        query = f"I'm looking for {category}"

        # For buying scenarios, first hard constraint is also disclosed
        if scenario == "buying":
            # Simulate intent_card hard_constraints[0]
            features = product.get("features", [])
            details = product.get("details", {})
            if isinstance(features, list) and features:
                query += f" {features[0]}"
            elif isinstance(details, dict) and details:
                first_detail = next(iter(details.values()), "")
                query += f" {first_detail}"

        results = bm25.search(query, top_k=100)
        result_asins = [asin for asin, _ in results]

        for k in [10, 20, 50, 100]:
            if target in result_asins[:k]:
                results_by_k[k] += 1
                results_by_scenario[scenario][k] += 1

    print("Overall BM25 Recall (using user_profile as query):")
    print(f"  Recall@10:  {results_by_k[10]/len(samples)*100:.1f}%")
    print(f"  Recall@20:  {results_by_k[20]/len(samples)*100:.1f}%")
    print(f"  Recall@50:  {results_by_k[50]/len(samples)*100:.1f}%")
    print(f"  Recall@100: {results_by_k[100]/len(samples)*100:.1f}%")

    print(f"\nBy scenario type:")
    for scenario, counts in sorted(results_by_scenario.items()):
        total = counts["total"]
        print(f"\n  {scenario} ({total} sessions):")
        for k in [10, 20, 50, 100]:
            print(f"    Recall@{k}: {counts[k]/total*100:.1f}%")

    print(f"\n{'='*60}")
    print("INTERPRETATION:")
    print(f"  - If Recall@50 < 50%, retrieval is the bottleneck → improve query construction")
    print(f"  - If Recall@50 > 70%, re-ranking is the bottleneck → improve LLM prompts")
    print(f"  - Gap between @10 and @50 = room for re-ranking to help")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
