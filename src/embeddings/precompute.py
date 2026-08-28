"""One-time script to precompute product embeddings.

Usage:
    python -m src.embeddings.precompute --catalog data/catalog.jsonl --output data/embeddings/

This takes ~2-5 minutes on CPU for 50K products.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 512


def build_searchable_text(product: dict) -> str:
    parts = [product.get("title", "")]

    categories = product.get("categories", [])
    if isinstance(categories, list):
        parts.extend(categories)

    features = product.get("features", [])
    if isinstance(features, list):
        parts.extend(features[:5])

    store = product.get("store", "")
    if store:
        parts.append(store)

    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Precompute product embeddings")
    parser.add_argument("--catalog", default="data/catalog.jsonl", help="Path to catalog.jsonl")
    parser.add_argument("--output", default="data/embeddings", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading catalog from {args.catalog}...")
    products = []
    asins = []
    with open(args.catalog) as f:
        for line in f:
            p = json.loads(line)
            products.append(p)
            asins.append(p["parent_asin"])

    print(f"Loaded {len(products)} products")

    texts = [build_searchable_text(p) for p in products]

    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Encoding {len(texts)} products (batch_size={BATCH_SIZE})...")
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True, normalize_embeddings=True)

    embeddings_path = output_dir / "minilm.npy"
    np.save(str(embeddings_path), embeddings.astype(np.float32))
    print(f"Saved embeddings: {embeddings_path} ({embeddings.shape})")

    index_path = output_dir / "asin_index.json"
    with open(index_path, "w") as f:
        json.dump(asins, f)
    print(f"Saved ASIN index: {index_path} ({len(asins)} entries)")

    print("Done!")


if __name__ == "__main__":
    main()
