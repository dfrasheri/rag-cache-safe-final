from dataclasses import dataclass
from typing import List, Dict


# ------------------------------
@dataclass
class Document:
    doc_id: str
    text: str
    version: int = 1


# ------------------------------
@dataclass
class RetrievedItem:
    doc_id: str
    version: int
    score: float
    snippet: str


# ------------------------------
@dataclass
class RetrievalCacheEntry:
    items: List[RetrievedItem]
    corpus_version_at_write: int


# ------------------------------
@dataclass
class ResponseCacheEntry:
    answer: str
    citations: List[Dict[str, str]]
