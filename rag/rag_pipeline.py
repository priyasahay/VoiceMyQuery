"""RAG pipeline (Iteration 1).

Retrieve relevant knowledge-base chunks, stuff them into the prompt as grounded
context, and let the local Ollama LLM answer *only* from that context. This is
the key property of RAG: the answer is grounded in retrieved source text and can
cite where it came from, and updating knowledge means re-running ingest — no
model retraining.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from common import llm
from rag.retriever import retrieve

_PROMPT_TEMPLATE = """Use ONLY the context below to answer the question. \
If the context does not contain the answer, say you don't have that information.

Context:
{context}

Question: {question}

Answer:"""


def answer(question: str, top_k: int | None = None) -> dict:
    hits = retrieve(question, top_k=top_k)
    context = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits)
    prompt = _PROMPT_TEMPLATE.format(context=context, question=question)
    text = llm.generate(prompt)
    sources = sorted({h["source"] for h in hits})
    return {
        "mode": "rag",
        "answer": text,
        "sources": sources,
        "retrieved": [{"source": h["source"], "score": round(h["score"], 3)} for h in hits],
    }


if __name__ == "__main__":
    if not llm.is_up():
        raise SystemExit(f"Ollama is not running at {config.OLLAMA_HOST}. Start it with: ollama serve")
    q = " ".join(sys.argv[1:]) or "What is the difference between PUT and PATCH?"
    result = answer(q)
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:", ", ".join(result["sources"]))
