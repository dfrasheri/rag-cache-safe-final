# RAG Prototype — Caching + Safe Invalidation

so this is a small rag demo the whole point is one thing: **cache the work, but dont serve old answers when the docs change**  
standard library only, no dependencies

## why two ideas matter

caching = i already did the retrieval or generation once so i save the result and reuse it next time instead of redoing everything

safe invalidation = when the docs change, cached stuff from before isnt trustworthy anymore instead of silently returning stale results the system forces a miss and recomputes

## whats inside

- retrieval step that picks top k docs for a query
- simple generator that formats an answer with citations
- two in memory caches — one for retrieval, one for responses
- corpus doc versioning so updates dont bleed into old cached answers

## running it

```
python -m src.main
```

## retrieval cache

stores retrieval results for the same query n filters combo

```
key = SHA256( normalize(query) + "|" + canonicalize(filters) )[:12]
```

- normalize(query) = lowercase, trim, collapse whitespace
- canonicalize(filters) = json.dumps(filters, sort_keys=True, separators=(",",":"))

stored value is a list of (doc_id, version, score, snippet) plus corpus_version_at_write

on read: if corpus_version_at_write != current_corpus_version → treat as miss and delete the entry

fast when nothing changed. safe when the corpus updates

## response cache

stores the final answer but its keyed by the query and the retrieved context — so it cant reuse an answer that came from old docs

```
key = SHA256( normalize(query) + "|" + context_hash + "|" + str(PROMPT_V) )[:12]
```

- prompt_v = 1
- context_hash is built from the retrieved context: sorted tuples of (doc_id, version, snippet)

stored value is the answer string n citations

no explicit invalidation needed here — if docs change, retrieval gives different versions or snippets → context_hash changes → new key → natural miss

## why stale answers dont get served

two layers:

1. corpus version gate (retrieval cache) — any doc update bumps corpus_version retrieval entries written under the old version get rejected on read

2. context bound response key (response cache) — the response key includes (doc_id, version, snippet) via context_hash if retrieved context shifts at all the old response key wont match

if one layer somehow got bypassed the other still catches it

## demo output

5 steps:

| Step | Action | Retrieval | Response |
|------|--------|-----------|----------|
| 1 | Load 10 base docs | — | — |
| 2 | Query Q1 (first time) | MISS | MISS |
| 3 | Query Q1 (repeat) | HIT | HIT |
| 4 | Update doc03 + doc07 | — | — |
| 5 | Query Q1 (after update) | MISS | MISS |

steps 2→3: same query, same corpus, same keys → both caches hit  
steps 3→5: corpus_version goes 1→2, so the retrieval entry is invalid; fresh retrieval gives a new context_hash, so response cache misses too

each step prints: corpus_version, retrieval_key, context_hash, response_key, and hit/miss

## why this matters

in real rag, generation is the expensive part — llm calls arent free this demo keeps generation deterministic but the same logic applies: a retrieval hit skips search/scoring work, a response hit skips regeneration entirely (big savings in production)

the caches grow with unique (query, filters) pairs so youd want to cap them in a real service the two caches are intentionally separate — if you bump prompt_v, you force regeneration without throwing away retrieval reuse

## risk + mitigation

flood it with unique query+filter combos and memory becomes a problem mitigations:

- cap cache size, evict with lru or by age
- normalize + length limit queries before hashing
- optional ttl per entry