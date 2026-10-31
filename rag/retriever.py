"""Retriever: load the FAISS index and fetch the top-k relevant chunks."""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


@lru_cache(maxsize=1)
def _load():
    import faiss
    from sentence_transformers import SentenceTransformer

    index_path = config.RAG_INDEX_DIR / "kb.faiss"
    chunks_path = config.RAG_INDEX_DIR / "chunks.json"
    if not index_path.exists() or not chunks_path.exists():
        raise SystemExit(
            "RAG index not found. Build it first with:  python -m rag.ingest"
        )
    index = faiss.read_index(str(index_path))
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    return index, chunks, model


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or config.TOP_K
    index, chunks, model = _load()
    q = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(q, top_k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        rec = dict(chunks[idx])
        rec["score"] = float(score)
        results.append(rec)
    return results


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is a circuit breaker?"
    for r in retrieve(q):
        print(f"[{r['score']:.3f}] {r['source']}#{r['chunk_id']}: {r['text'][:120]}...")
