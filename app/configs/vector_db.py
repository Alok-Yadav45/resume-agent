from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import threading
import json
from typing import List, Dict, Any


class SimpleVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384):
        self.model = SentenceTransformer(model_name)
        self.dim = dim
        self.index = faiss.IndexFlatL2(self.dim)
        self.metadatas: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def embed(self, texts: List[str]) -> np.ndarray:
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        if embs.ndim == 1:
            embs = np.expand_dims(embs, 0)
        return embs.astype('float32')

    def add_documents(self, docs: List[Dict[str, Any]]):
       """docs: list of {"id": str, "text": str, "meta": {...}}"""
       texts = [d["text"] for d in docs]
       ids = [d.get("id") for d in docs]
       metas = [d.get("meta", {}) for d in docs]
       vectors = self.embed(texts)
       with self.lock:
           self.index.add(vectors)
           self.metadatas.extend([{"id": ids[i], "meta": metas[i], "text": texts[i]} for i in range(len(ids))])

    def search(self, query: str, top_k: int = 5):
        qv = self.embed([query])
        with self.lock:
            if self.index.ntotal == 0:
              return []
        D, I = self.index.search(qv, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.metadatas):
               continue
            meta = self.metadatas[idx]
            results.append({"id": meta["id"], "text": meta["text"], "meta": meta["meta"], "score": float(score)})
        return results


vector_store = SimpleVectorStore()