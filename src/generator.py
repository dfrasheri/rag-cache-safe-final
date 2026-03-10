from typing import List, Dict

from src.models import RetrievedItem, ResponseCacheEntry
from src.cache import ResponseCache, PROMPT_V


# ------------------------------
class Generator:

    def __init__(self, cache: ResponseCache) -> None:
        self._cache = cache

    # ------------------------------
    def generate(
        self,
        query: str,
        items: List[RetrievedItem],
        context_hash: str,
    ) -> tuple:
        key = self._cache.make_key(query, context_hash)
        cached = self._cache.get(key)
        if cached is not None:
            return cached.answer, cached.citations, key, True

        citations: List[Dict[str, str]] = []
        parts: List[str] = []
        for item in items:
            parts.append(f"[{item.doc_id} v{item.version}]: {item.snippet}")
            citations.append({"doc_id": item.doc_id, "snippet": item.snippet})

        answer = (
            f"Answer (PROMPT_V={PROMPT_V}): Based on {len(items)} retrieved "
            f"documents for query '{query}':\n" + "\n".join(parts)
        )

        entry = ResponseCacheEntry(answer=answer, citations=citations)
        self._cache.put(key, entry)
        return answer, citations, key, False
