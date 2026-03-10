# RAG Prototype (Caching + Safe Invalidation)

Ok so this repo is a small RAG demo and the whole point is simple: **cache the work, but don’t serve old answers when the docs change.**  
It’s standard library only.

## What is caching?
Caching = I already did the work once (retrieval or generating the answer), so I save the result and reuse it next time instead of recomputing.

## What is “safe invalidation”?
Safe invalidation = when the document bundle changes, the old cached stuff is no longer trustworthy, so the system forces a miss and recomputes instead of accidentally returning stale results.

## What’s inside
- retrieval step that picks top-k docs for a query
- a simple generator that formats an answer with citations
- **two** in-memory caches (retrieval + response)
- corpus/doc versioning so updates don’t leak stale answers

## Run it
```bash
python -m src.main
```

## Retrieval cache
This cache stores the retrieval results for the same query + filters.

```
key = SHA256( normalize(query) + "|" + canonicalize(filters) )[:12]
```

- `normalize(query)` = lowercase + trim + collapse whitespace
- `canonicalize(filters)` = `json.dumps(filters, sort_keys=True, separators=(",",":"))`

**Stored value:**
- list of `(doc_id, version, score, snippet)`
- plus `corpus_version_at_write`

**On read:**
- if `corpus_version_at_write != current_corpus_version` → treat as MISS and delete the entry

So: fast when nothing changed, safe when the corpus updates.

## Response cache
This cache stores the final answer, but it’s keyed by the query and the retrieved context, so it can’t reuse an answer from old docs.

```
key = SHA256( normalize(query) + "|" + context_hash + "|" + str(PROMPT_V) )[:12]
```

- `PROMPT_V = 1`
- `context_hash` is computed from the retrieved context (sorted tuples of `(doc_id, version, snippet)`)

**Stored value:**
- answer string + citations

**No explicit invalidation step here:**
- if docs change, retrieval yields different versions/snippets → `context_hash` changes → new key → natural MISS

## Why it doesn’t serve stale answers
There are two layers of protection:

1. **Corpus version gate (retrieval cache)**  
   Any doc update bumps `corpus_version`. Retrieval cache entries written under the old version are rejected.

2. **Context-bound response key (response cache)**  
   The response key includes `(doc_id, version, snippet)` via `context_hash`. If the retrieved context changes, the old response key can’t match.

Even if one layer was somehow bypassed, the other still prevents stale reuse.

## Demo output (what it proves)
The demo runs 5 steps:

| Step | Action | Retrieval | Response |
|------|--------|-----------|----------|
| 1 | Load 10 base docs | — | — |
| 2 | Query Q1 (first time) | MISS | MISS |
| 3 | Query Q1 (repeat) | HIT | HIT |
| 4 | Update doc03 + doc07 | — | — |
| 5 | Query Q1 (after update) | MISS | MISS |

- **Step 2 → 3**: same query, same corpus, same keys → both caches hit.
- **Step 3 → 5**: `corpus_version` goes 1 → 2, so retrieval cache entry is invalid; fresh retrieval gives a new `context_hash`, so response cache misses too.

Each step prints: `corpus_version`, `retrieval_key`, `context_hash`, `response_key`, and `HIT`/`MISS` labels.

## Cost / latency (why this matters)
In real RAG, generation is the expensive part (LLM calls). This demo keeps generation deterministic, but the same idea applies:
- **retrieval hit** = skip the search/scoring work
- **response hit** = skip regeneration (big latency + cost savings in production)

Caches grow with unique (query, filters) pairs, so you’d cap them in a real service.  
Also: the two caches are separate on purpose. If you bump `PROMPT_V`, you can force regeneration without throwing away retrieval reuse.

## Risk + mitigation
**Risk**: cache poisoning / unbounded growth.  
If someone floods unique query+filter combos, the caches can grow until memory becomes a problem.

**Mitigation**:
- cap cache size and evict (LRU/oldest)
- normalize and length-limit queries before hashing
- optional TTL per entry

## File structure
```
SHFA/
├── README.md
├── docs/
│   ├── base/        (doc01..doc10)
│   └── updated/     (doc03, doc07)
└── src/
    ├── __init__.py
    ├── main.py
    ├── models.py
    ├── corpus.py
    ├── cache.py
    ├── retrieval.py
    ├── generator.py
    └── utils.py
```
