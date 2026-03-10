# RAG Prototype (Caching + Safe Invalidation)

This repo is a tiny RAG demo built to answer one practical question: **how do you cache RAG safely when the underlying documents change?**

It loads a small document set, retrieves the top-k matches for a query, generates a short answer with citations, and then shows how caching behaves **before and after** a doc update.

## Quick definitions (plain English)

**Caching**  
Saving results from work you already did (retrieval or generation) so the next identical request is faster and cheaper.

**Safe invalidation**  
Making sure cached results don’t get reused when they’re no longer valid — e.g., when the documents were updated. In other words: *fast, but not wrong.*

## Run

```bash
python -m src.main
```

## How it works

The system uses two layers of caching:

### 1. Retrieval Cache
Saves the list of documents found for a query.
- **Key**: `hash(query + filters)`
- **Safety**: Each entry stores the `corpus_version`. If you update a doc, the `corpus_version` bumps, and the cache knows to ignore old results.

### 2. Response Cache
Saves the final answer generated from those documents.
- **Key**: `hash(query + context_hash + prompt_version)`
- **Safety**: The `context_hash` is built from the exact text and version of the retrieved docs. If the docs change, the hash changes, which naturally creates a "cache miss" for the response.

## Why this matters

In a real system, LLM calls are slow and expensive (~$0.01 - $0.10 and 1-2 seconds per call). Caching saves that cost. However, serving a "stale" answer from a doc that was deleted or edited 5 minutes ago is a common production bug. This prototype demonstrates a simple way to bake that safety into the cache keys themselves.

## Risks

**Cache Poisoning / Memory Pressure**  
Since this is an in-memory cache, an attacker (or a very curious user) could flood the system with millions of unique queries, causing the process to run out of RAM.

**Mitigation**: In a real app, you'd use a TTL (time-to-live), a max cache size with LRU (Least Recently Used) eviction, or a dedicated store like Redis.

## File structure

- `src/main.py`: The demo script.
- `src/cache.py`: The logic for both cache layers.
- `src/corpus.py`: Manages documents and their versions.
- `docs/base/`: Your starting document set.
- `docs/updated/`: The files used to simulate a document update.
