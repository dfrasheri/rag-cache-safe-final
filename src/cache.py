from typing import Optional, Dict, Any

from src.models import RetrievalCacheEntry, ResponseCacheEntry
from src.utils import normalize_query, canonicalize_filters, compute_hash

PROMPT_V: int = 1



class RetrievalCache:

    def __init__(self) -> None:
        self._store: Dict[str, RetrievalCacheEntry] = {}

    
    def make_key(self, query: str, filters: Optional[Dict[str, Any]]) -> str:
        raw = normalize_query(query) + "|" + canonicalize_filters(filters)
        return compute_hash(raw)

    
    def get(
        self,
        key: str,
        current_corpus_version: int,
    ) -> Optional[RetrievalCacheEntry]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.corpus_version_at_write != current_corpus_version:
            del self._store[key]
            return None
        return entry

    
    def put(self, key: str, entry: RetrievalCacheEntry) -> None:
        self._store[key] = entry



class ResponseCache:

    def __init__(self) -> None:
        self._store: Dict[str, ResponseCacheEntry] = {}

    
    def make_key(self, query: str, context_hash: str) -> str:
        raw = normalize_query(query) + "|" + context_hash + "|" + str(PROMPT_V)
        return compute_hash(raw)

    
    def get(self, key: str) -> Optional[ResponseCacheEntry]:
        return self._store.get(key)

    def put(self, key: str, entry: ResponseCacheEntry) -> None:
        self._store[key] = entry
