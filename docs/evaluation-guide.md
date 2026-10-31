# Evaluation Guide

## Overview

The evaluation harness runs 15 held-out questions through both pipelines and produces a side-by-side comparison report. These questions were **not used in fine-tune training** — they test genuine generalisation.

---

## Running the Evaluation

```bash
source .venv/bin/activate

# Run both modes (default)
python -m evaluation.compare

# Run RAG only
python -m evaluation.compare --rag

# Run fine-tune only (requires trained adapter)
python -m evaluation.compare --finetune
```

Output: `evaluation/comparison_report.md`

> Requires Ollama running for RAG mode: `ollama serve &`

---

## Question Categories

### In-Domain (8 questions)
Questions whose answers are directly covered by the knowledge base.

Examples:
- *"What does cloud-native mean?"*
- *"What is the strangler fig pattern?"*
- *"What is the difference between blue-green and canary deployments?"*
- *"How does a service mesh differ from a traditional API gateway?"*

**Expected behaviour:**
- RAG: Accurate, grounded, cites the relevant source file.
- Fine-tune: Good if the concept was in training data with similar phrasing.

### Paraphrased (4 questions)
Same concepts as in-domain, but rephrased to test generalisation.

Examples:
- *"How do containers differ from virtual machines in resource usage?"* (paraphrase of a training concept)
- *"Why is statelessness important for horizontal scaling?"*

**Expected behaviour:**
- RAG: Handles well — semantic search is robust to paraphrasing.
- Fine-tune: Variable — may miss if the training examples used very different phrasing.

### Out-of-Scope (3 questions)
Questions that have nothing to do with cloud-native topics.

Examples:
- *"What is the capital of France?"*
- *"How do you make sourdough bread?"*
- *"Who started World War I?"*

**Expected behaviour:**
- RAG: Should say it doesn't have the information (nothing retrieved matches).
- Fine-tune: Likely **hallucinates** a confident answer — this is the key demonstration of fine-tuning risk.

---

## Reading the Report

`evaluation/comparison_report.md` contains:

```markdown
## Question 1 (in_domain)
**Q:** What does cloud-native mean?

**RAG** (2.3s)
Cloud-native is an approach to building...
Sources: 01_cloud_native_fundamentals.md

**Fine-tuned** (1.8s)
Cloud-native refers to applications designed...
```

### What to look for

| Signal | What it tells you |
|---|---|
| RAG says "I don't have that information" | Retrieval correctly found nothing relevant |
| Fine-tune gives a wrong-but-confident answer | Classic hallucination |
| RAG cites multiple sources | Multi-document retrieval working |
| Latency difference | Fine-tune is typically 1–2s faster (no retrieval step) |
| Fine-tune answer is vaguer | Small training set — generalisation limit |
| RAG answer is longer | Retrieved context adds more detail than fine-tune memory |

---

## Latency Summary Table

The report ends with a summary table:

```
| Category    | RAG avg | Fine-tune avg |
|-------------|---------|---------------|
| in_domain   | 4.2s    | 2.1s          |
| paraphrased | 4.8s    | 2.3s          |
| out_of_scope| 3.9s    | 1.9s          |
```

Fine-tuned is consistently faster because:
1. No embedding step
2. No FAISS search
3. Smaller model (1.1B vs 3B)
4. No network call to Ollama

---

## Interpreting Results

### If RAG gives wrong answers
- Check if `rag.ingest` was run after the latest knowledge base changes.
- Increase `TOP_K` (more chunks retrieved): `TOP_K=6 python -m evaluation.compare`
- The question may be too ambiguous for semantic search.

### If Fine-tune gives repetitive answers
- `repetition_penalty=1.3` in `finetune_pipeline.py` mitigates this.
- Increase penalty or reduce `max_new_tokens` for shorter, crisper answers.

### If Fine-tune always says "I don't know"
- Training likely didn't converge. Check training loss output.
- Try more epochs: `FINETUNE_EPOCHS=5 python -m finetune.train_lora`

### If out-of-scope questions get answered confidently by RAG
- Check if the prompt template in `rag_pipeline.py` includes the grounding instruction.
- The line *"If the context does not contain the answer, say you don't have that information"* is critical.
