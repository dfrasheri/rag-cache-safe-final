import os

from src.corpus import CorpusManager
from src.cache import RetrievalCache, ResponseCache, PROMPT_V
from src.retrieval import Retriever
from src.generator import Generator


# some logs here so i can see whats goin on
SEPARATOR = "=" * 60



def log_step(step: int, title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  STEP {step}: {title}")
    print(SEPARATOR)



def run_query(
    label: str,
    query: str,
    filters: dict,
    corpus: CorpusManager,
    retriever: Retriever,
    generator: Generator,
) -> None:
    print(f"\n--- {label} ---")
    print(f"  query          : '{query}'")
    print(f"  filters        : {filters}")
    print(f"  corpus_version : {corpus.corpus_version}")

    items, ret_key, ret_hit = retriever.retrieve(
        query=query,
        documents=corpus.documents,
        filters=filters,
        corpus_version=corpus.corpus_version,
    )

    ctx_hash = Retriever.context_hash_from_items(items)

    print(f"  retrieval_key  : {ret_key}")
    print(f"  RETRIEVAL      : {'HIT' if ret_hit else 'MISS'}")
    print(f"  context_hash   : {ctx_hash}")
    print(f"  retrieved docs : {len(items)}")

    for it in items:
        print(f"    -> {it.doc_id} v{it.version}  score={it.score}  snippet='{it.snippet[:60]}...'")

    answer, citations, resp_key, resp_hit = generator.generate(
        query=query, items=items, context_hash=ctx_hash
    )

    print(f"  response_key   : {resp_key}")
    print(f"  RESPONSE       : {'HIT' if resp_hit else 'MISS'}")
    print(f"  PROMPT_V       : {PROMPT_V}")
    print(f"\n  answer:\n{answer}")



def main() -> None:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "base")
    updated_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "updated")

    corpus = CorpusManager()
    ret_cache = RetrievalCache()
    resp_cache = ResponseCache()
    retriever = Retriever(cache=ret_cache, top_k=3)
    generator = Generator(cache=resp_cache)

    query = "python testing API security"
    filters = {"domain": "engineering", "level": "intermediate"}

    
    log_step(1, "Load base documents")
    corpus.load_base(base_dir)
    print(f"  Loaded {len(corpus.documents)} documents")
    print(f"  corpus_version : {corpus.corpus_version}")
    for doc_id, doc in sorted(corpus.documents.items()):
        print(f"    {doc.doc_id} v{doc.version}")

    
    log_step(2, "Query Q1 (first time) -> expect MISS / MISS")
    run_query("Q1 first", query, filters, corpus, retriever, generator)

    
    log_step(3, "Query Q1 (repeat) -> expect HIT / HIT")
    run_query("Q1 repeat", query, filters, corpus, retriever, generator)

    
    log_step(4, "Apply document updates")
    changes = corpus.apply_updates(updated_dir)
    print(f"  corpus_version : {corpus.corpus_version}")
    for doc_id, old_v, new_v in changes:
        print(f"    {doc_id}: v{old_v} -> v{new_v}")

    
    log_step(5, "Query Q1 (after update) -> expect MISS / MISS")
    run_query("Q1 after update", query, filters, corpus, retriever, generator)



if __name__ == "__main__":
    main()
