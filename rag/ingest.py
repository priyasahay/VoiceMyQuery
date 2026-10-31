"""RAG ingestion: chunk the knowledge base, embed it, and build a FAISS index.

Run once (and again whenever the knowledge base changes):
    python -m rag.ingest

Everything is local: sentence-transformers (Apache 2.0) for embeddings,
FAISS (MIT) for the vector index.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def _doc_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split a markdown doc into (heading, body) pairs on level-2 (##) headings."""
    sections: list[tuple[str, str]] = []
    current_head = ""
    current_body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_body:
                sections.append((current_head, "\n".join(current_body).strip()))
            current_head = line[3:].strip()
            current_body = []
        elif line.startswith("# "):
            continue  # doc title handled separately
        else:
            current_body.append(line)
    if current_body:
        sections.append((current_head, "\n".join(current_body).strip()))
    return [(h, b) for h, b in sections if b]


def _pack_paragraphs(body: str, size: int) -> list[str]:
    """Group paragraphs so each piece stays under `size` without splitting words."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces: list[str] = []
    buf = ""
    for para in paragraphs:
        if buf and len(buf) + len(para) + 2 > size:
            pieces.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        pieces.append(buf)
    return pieces


def _chunk_document(text: str, size: int) -> list[str]:
    """Heading-aware chunking: one coherent, topic-tagged chunk per section.

    Each chunk is prefixed with the document title and section heading so the
    embedding captures the topic and the LLM sees where the text came from.
    """
    title = _doc_title(text)
    chunks: list[str] = []
    for heading, body in _split_into_sections(text):
        header = f"{title} — {heading}".strip(" —")
        for piece in _pack_paragraphs(body, size):
            chunks.append(f"{header}\n{piece}" if header else piece)
    return chunks


def build_index() -> None:
    from sentence_transformers import SentenceTransformer
    import faiss

    docs = sorted(config.KNOWLEDGE_BASE_DIR.glob("*.md"))
    if not docs:
        raise SystemExit(f"No .md files found in {config.KNOWLEDGE_BASE_DIR}")

    records: list[dict] = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for i, chunk in enumerate(_chunk_document(text, config.CHUNK_SIZE)):
            records.append({"source": doc.name, "chunk_id": i, "text": chunk})

    print(f"[ingest] {len(docs)} documents -> {len(records)} chunks")

    model = SentenceTransformer(config.EMBEDDING_MODEL)
    embeddings = model.encode(
        [r["text"] for r in records],
        normalize_embeddings=True,      # cosine similarity via inner product
        show_progress_bar=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    config.RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(config.RAG_INDEX_DIR / "kb.faiss"))
    (config.RAG_INDEX_DIR / "chunks.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[ingest] wrote index to {config.RAG_INDEX_DIR}")


if __name__ == "__main__":
    build_index()
