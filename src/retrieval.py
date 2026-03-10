from typing import List, Optional, Dict, Any

from src.models import Document, RetrievedItem, RetrievalCacheEntry
from src.cache import RetrievalCache
from src.utils import tokenize, compute_context_hash


# ------------------------------
class Retriever:

    def __init__(self, cache: RetrievalCache, top_k: int = 3) -> None:
        self._cache = cache
        self._top_k = top_k

    # ------------------------------
    def retrieve(
        self,
        query: str,
        documents: Dict[str, Document],
        filters: Optional[Dict[str, Any]],
        corpus_version: int,
    ) -> tuple:
        key = self._cache.make_key(query, filters)
        cached = self._cache.get(key, corpus_version)
        if cached is not None:
            return cached.items, key, True

        query_tokens = tokenize(query)
        if not query_tokens:
            return [], key, False

        scored: List[RetrievedItem] = []
        for doc in documents.values():
            doc_tokens = tokenize(doc.text)
            if not doc_tokens:
                continue
            overlap = len(query_tokens & doc_tokens)
            score = round(overlap / len(query_tokens), 4)
            if score > 0:
                snippet = doc.text[:120]
                scored.append(
                    RetrievedItem(
                        doc_id=doc.doc_id,
                        version=doc.version,
                        score=score,
                        snippet=snippet,
                    )
                )

        scored.sort(key=lambda x: (-x.score, x.doc_id))
        top = scored[: self._top_k]

        entry = RetrievalCacheEntry(
            items=top, corpus_version_at_write=corpus_version
        )
        self._cache.put(key, entry)
        return top, key, False

    # ------------------------------
    @staticmethod
    def context_hash_from_items(items: List[RetrievedItem]) -> str:
        tuples = [(it.doc_id, it.version, it.snippet) for it in items]
        return compute_context_hash(tuples)
