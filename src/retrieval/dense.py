import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class DenseIndex:
    def __init__(self, embeddings_path: str, asin_index_path: str):
        self._embeddings = np.load(embeddings_path)
        with open(asin_index_path, encoding="utf-8") as f:
            self._asins = json.load(f)

        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(self._embeddings)
        self._index.add(self._embeddings)

        self._model = SentenceTransformer(MODEL_NAME)

    def search(self, query: str, top_k: int = 50) -> list[tuple[str, float]]:
        query_vec = self._model.encode([query], normalize_embeddings=True)
        scores, indices = self._index.search(query_vec.astype(np.float32), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._asins):
                results.append((self._asins[idx], float(score)))
        return results
