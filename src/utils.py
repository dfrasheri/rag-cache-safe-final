import hashlib
import json
import re
from typing import Dict, Any, List, Optional, Tuple



def normalize_query(query: str) -> str:
    if not query:
        return ""
    return re.sub(r"\s+", " ", query.strip().lower())



def canonicalize_filters(filters: Optional[Dict[str, Any]]) -> str:
    return json.dumps(filters or {}, sort_keys=True, separators=(",", ":"))



def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:12]



def compute_context_hash(items: List[Tuple[str, int, str]]) -> str:
    payload = json.dumps(sorted(items), sort_keys=True, separators=(",", ":"))
    return compute_hash(payload)



def tokenize(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))
