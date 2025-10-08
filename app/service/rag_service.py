from typing import List
from app.configs.vector_db import vector_store


def index_document(doc_id: str, text: str, meta: dict = None):
    if meta is None:
        meta = {}
    vector_store.add_documents([{"id": doc_id, "text": text, "meta": meta}])


def retrieve(query: str, top_k: int = 5):
    """Return a list of retrieved docs with small context for RAG."""
    return vector_store.search(query, top_k=top_k)

def build_context_snippet(retrieved, max_chars: int = 1500):
    parts = []
    cur_len = 0
    for r in retrieved:
        t = r.get("text", "")
        allowed = max_chars - cur_len
        if allowed <= 0:
           break
        if len(t) > allowed:
            parts.append(t[:allowed] + "...")
            cur_len = max_chars
            break
        parts.append(t)
        cur_len += len(t)
    return "\n\n---\n\n".join(parts)