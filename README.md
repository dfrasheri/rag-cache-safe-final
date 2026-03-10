# RAG Prototype — Caching + Safe Invalidation

Two-layer cached retrieval-augmented generation with corpus versioning. Standard library only.

## Cache Keys

### Retrieval cache

```
key = SHA256( normalize(query) + "|" + canonicalize(filters) )[:12]
```

- `normalize(query)` — lowercase, strip, collapse whitespace
- `canonicalize(filters)` — `json.dumps(filters, sort_keys=True, separators=(",",":"))`
- Stored value: list of `(doc_id, version, score, snippet)` + `corpus_version_at_write`
- On read: if `corpus_version_at_write != current_corpus_version` → miss, delete

### Response cache

```
key = SHA256( normalize(query) + "|" + context_hash + "|" + str(PROMPT_V) )[:12]
```

- `PROMPT_V = 1`
- `context_hash = SHA256( json.dumps( sorted([ (doc_id, version, snippet), ... ]) ) )[:12]`
- Stored value: answer string + citations
- No explicit invalidation needed — changed docs shift `context_hash` → different key → natural miss

## Invalidation behavior

Two mechanisms:

1. **Corpus version gate** — any doc update bumps `corpus_version`. Retrieval cache entries written under old version are treated as misses on read.
2. **Context hash drift** — response key includes hash of `(doc_id, version, snippet)` tuples. Changed doc content → different hash → different key. This catches cases even if the version bump were somehow skipped.

## How to run

```
cd SHFA
python -m src.main
```

Requires Python 3.7+. No external dependencies.

## Demo output

Five steps, expected cache behavior:

| Step | Action | Retrieval | Response |
|------|--------|-----------|----------|
| 1 | Load 10 base docs | — | — |
| 2 | Query Q1 (first time) | MISS | MISS |
| 3 | Query Q1 (repeat, same corpus) | HIT | HIT |
| 4 | Update doc03, doc07 | — | — |
| 5 | Query Q1 (post-update) | MISS | MISS |

Step 2→3: same query, unchanged corpus. Keys match, `corpus_version` unchanged → both hit.

Step 3→5: `corpus_version` went 1→2. Retrieval cache entry was written at version 1, so it's invalidated. Re-retrieval gets updated docs → new `context_hash` → response cache also misses.

Each step prints `corpus_version`, `retrieval_key`, `context_hash`, `response_key`, and `HIT`/`MISS` labels.

## Cost / latency

- Retrieval hit skips the scoring pass (~10–100ms saved, depends on corpus size).
- Response hit skips the LLM call (~200–2000ms, $0.01–$0.10 per call saved).
- Memory: bounded by unique (query, filters) pairs. 10K unique queries × top-3 results ≈ 5–20MB.
- The two layers are independent: a retrieval hit can still produce a response miss (e.g. after bumping `PROMPT_V`), so prompt iteration doesn't force re-retrieval.

## Risk + mitigation

**Cache poisoning via unbounded growth.** An attacker floods unique query+filter combinations. Each one creates a new cache entry. Eventually the process runs out of memory.

Mitigation: cap cache size (e.g. 50K entries) with LRU eviction. Normalize and length-limit queries before hashing to collapse near-duplicates. Add per-entry TTL as a secondary bound.

## File structure

```
SHFA/
├── README.md
├── docs/
│   ├── base/
│   │   ├── doc01.json .. doc10.json
│   └── updated/
│       ├── doc03.json
│       └── doc07.json
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
