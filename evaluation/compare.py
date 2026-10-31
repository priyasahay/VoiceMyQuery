"""Compare RAG vs fine-tuning on the same held-out questions.

Runs every evaluation question through both pipelines (whichever are available),
measures latency, and writes a side-by-side markdown report so you can see the
qualitative difference for your write-up.

    python -m evaluation.compare              # both pipelines
    python -m evaluation.compare --rag        # RAG only
    python -m evaluation.compare --finetune   # fine-tune only
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from evaluation.questions import ALL


def _run(pipeline_answer, question: str) -> tuple[str, float]:
    t0 = time.perf_counter()
    try:
        result = pipeline_answer(question)
        answer = result["answer"]
        if result.get("sources"):
            answer += f"\n\n_sources: {', '.join(result['sources'])}_"
    except Exception as exc:  # keep the whole run going even if one call fails
        answer = f"ERROR: {exc}"
    return answer, time.perf_counter() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rag", action="store_true", help="RAG only")
    ap.add_argument("--finetune", action="store_true", help="fine-tune only")
    args = ap.parse_args()

    run_rag = args.rag or not args.finetune
    run_ft = args.finetune or not args.rag

    rag_answer = ft_answer = None
    if run_rag:
        from common import llm
        if not llm.is_up():
            print(f"[warn] Ollama not up at {config.OLLAMA_HOST}; skipping RAG.")
            run_rag = False
        else:
            from rag.rag_pipeline import answer as rag_answer
    if run_ft:
        from finetune.finetune_pipeline import answer as ft_answer, is_trained
        if not is_trained():
            print("[warn] no fine-tuned adapter; skipping fine-tune.")
            run_ft = False

    lines = ["# RAG vs Fine-tuning — comparison\n",
             f"Base RAG model: `{config.RAG_LLM_MODEL}` · Fine-tune base: `{config.FINETUNE_BASE_MODEL}`\n"]
    rag_times, ft_times = [], []

    for category, question in ALL:
        print(f"→ [{category}] {question}")
        lines.append(f"\n## [{category}] {question}\n")
        if run_rag:
            ans, dt = _run(rag_answer, question)
            rag_times.append(dt)
            lines.append(f"**RAG** ({dt:.1f}s):\n\n{ans}\n")
        if run_ft:
            ans, dt = _run(ft_answer, question)
            ft_times.append(dt)
            lines.append(f"**Fine-tuned** ({dt:.1f}s):\n\n{ans}\n")

    lines.append("\n## Summary\n")
    if rag_times:
        lines.append(f"- RAG avg latency: {sum(rag_times)/len(rag_times):.1f}s")
    if ft_times:
        lines.append(f"- Fine-tune avg latency: {sum(ft_times)/len(ft_times):.1f}s")
    lines.append(
        "\n**What to look for:** on in-domain questions both should be accurate. "
        "On out-of-scope questions RAG should refuse (no context retrieved) while a "
        "small fine-tuned model may confidently hallucinate. RAG cites sources and "
        "updates by re-running ingest; the fine-tune bakes knowledge into weights and "
        "needs retraining to change."
    )

    out = Path(__file__).resolve().parent / "comparison_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
