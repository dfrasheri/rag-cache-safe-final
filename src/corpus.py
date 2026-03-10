import json
import os
from typing import Dict, List, Optional, Tuple

from src.models import Document


# ------------------------------
class CorpusManager:

    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}
        self._corpus_version: int = 0

    @property
    def corpus_version(self) -> int:
        return self._corpus_version

    @property
    def documents(self) -> Dict[str, Document]:
        return self._docs

    # ------------------------------
    def load_base(self, directory: str) -> None:
        self._docs = {}
        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc = Document(doc_id=data["doc_id"], text=data["text"], version=1)
            self._docs[doc.doc_id] = doc
        self._corpus_version = 1

    # ------------------------------
    def apply_updates(self, directory: str) -> List[Tuple[str, int, int]]:
        changes: List[Tuple[str, int, int]] = []
        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc_id = data["doc_id"]
            if doc_id not in self._docs:
                continue
            old_version = self._docs[doc_id].version
            new_version = old_version + 1
            self._docs[doc_id] = Document(
                doc_id=doc_id, text=data["text"], version=new_version
            )
            changes.append((doc_id, old_version, new_version))
        if changes:
            self._corpus_version += 1
        return changes

    # ------------------------------
    def get_doc(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)
