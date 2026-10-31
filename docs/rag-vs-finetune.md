# RAG vs Fine-tuning — Deep Dive

## The Core Question

Both approaches try to solve the same problem: *how do you make a general-purpose language model give accurate, domain-specific answers?*

They solve it in completely opposite ways.

---

## Retrieval-Augmented Generation (RAG)

### The idea

Don't change the model. Instead, before every question, *find the relevant notes* and hand them to the model as part of the prompt.

```
Question: "What is a circuit breaker?"

Step 1: Search knowledge base
        → "Resilience — Circuit Breaker: A circuit breaker wraps..."
        → "Microservices — Fault Tolerance: When a downstream..."

Step 2: Build prompt
        "Here is relevant context:
         [retrieved text]
         Using only the context above, answer: What is a circuit breaker?"

Step 3: LLM reads context → generates answer
```

The model never "learned" about circuit breakers. It just reads what you showed it, like an open-book exam.

### How retrieval works

1. Every chunk of text in the knowledge base is converted to a **384-dimensional vector** (a list of 384 numbers that captures the *meaning* of the text).
2. When a question arrives, it's converted to a vector too.
3. The system finds the 4 chunks whose vectors are closest to the question vector — these are the most semantically relevant passages.
4. Those 4 chunks go into the prompt.

This "meaning comparison" is called **semantic search** — it works even when the question uses different words than the text (e.g. asking "how does a breaker pattern work?" still finds text about "circuit breaker").

### Strengths

| Strength | Why |
|---|---|
| **Honest about gaps** | If nothing is retrieved, the prompt has no context, so the model says "I don't have that information" |
| **Cites sources** | The response includes which documents were retrieved |
| **Easy to update** | Add a new Markdown file → re-run `rag.ingest` (30 seconds). No retraining |
| **Uses a large, capable model** | Llama 3.2 3B is much stronger than TinyLlama 1.1B |
| **Grounded** | The model is prompted to answer *only* from retrieved context |

### Weaknesses

| Weakness | Why |
|---|---|
| **Retrieval can fail** | If the question is phrased unusually, the relevant chunk might not rank in top-4 |
| **Requires Ollama** | An external LLM runtime must be running |
| **Slower inference** | Embedding + FAISS search + Ollama generation (~3–8s) |
| **No style learning** | The model's tone/format is controlled only via the system prompt |

---

## Fine-tuning (LoRA)

### The idea

Change the model. Show it the questions and answers during training so it *memorises* them. At query time, it answers from memory — no retrieval, no external context.

```
Training (once):
  Question: "What is a circuit breaker?"
  Answer:   "A circuit breaker is a resilience pattern..."
  → model adjusts its weights to associate this Q→A

Inference:
  Question: "What is a circuit breaker?"
  → model generates answer directly from memory
```

### What LoRA actually does

Full fine-tuning rewrites all 1.1 billion weights — expensive and slow. LoRA (Low-Rank Adaptation) instead adds small trainable matrices *on top* of the frozen original weights:

```
Original weight matrix W (frozen, 1.1B params)
    +
LoRA: W_update = A × B  (A and B are tiny — ~0.5% of params)

Effective weight = W + A × B
```

Only `A` and `B` are trained. The result is a ~10 MB "adapter" file that sits alongside the original 1.1B model.

### Strengths

| Strength | Why |
|---|---|
| **No external runtime** | Runs entirely locally, no Ollama needed |
| **Fast inference** | No retrieval step; smaller model → ~2–3s |
| **Style/tone control** | The model learns the answer *format* from training examples |
| **Compact** | Adapter is ~10 MB; the base model is cached |

### Weaknesses

| Weakness | Why |
|---|---|
| **Hallucinates on out-of-scope questions** | The model has no way to say "I don't know" — it generates confidently regardless |
| **No citations** | Cannot point to source documents |
| **Expensive to update** | Adding new facts requires retraining the adapter (10–30 min) |
| **Generalises poorly to paraphrasing** | A small dataset (45 examples) means the model may fail on rephrased versions of trained questions |
| **Smaller model** | TinyLlama 1.1B is weaker than Llama 3.2 3B at complex reasoning |

---

## Side-by-Side Comparison

| Dimension | RAG | Fine-tuning |
|---|---|---|
| **Where knowledge lives** | External index | Model weights |
| **Query time** | Embed → search → generate | Tokenise → generate |
| **In-domain accuracy** | High (grounded) | Good on trained phrasings |
| **Out-of-scope behaviour** | "I don't have that information" | Confident hallucination |
| **Citation/provenance** | Yes | No |
| **Knowledge update cost** | Seconds (re-index) | Minutes–hours (retrain) |
| **Setup cost** | Index once + Ollama running | Training time + dataset |
| **Inference latency** | ~3–8s | ~2–3s |
| **Offline? (no internet)** | Yes (after model download) | Yes |
| **Style control** | Prompt only | Strong (learned from examples) |
| **Best when** | Facts change; provenance matters | Fixed domain; specific persona/format |

---

## What to Observe in the UI

### Ask an in-domain question
> *"What is the difference between PUT and PATCH?"*

- **RAG:** Grounded, accurate, cites `02_api_design.md`. May include extra context from retrieved chunks.
- **Fine-tune:** Concise, matches the training-data style. May miss nuance if the question phrasing diverges from training.

### Ask a paraphrased question
> *"How do PUT and PATCH differ when updating a resource?"* (same meaning, different words)

- **RAG:** Handles well — semantic search finds the right chunk regardless of phrasing.
- **Fine-tune:** May struggle — small training set means generalisation is limited.

### Ask an out-of-scope question
> *"What is the capital of France?"*

- **RAG:** "I don't have that information in my knowledge base" (nothing retrieved).
- **Fine-tune:** Confidently answers "Paris" (or hallucinates something related to cloud computing). **This is the hallucination risk of fine-tuning clearly visible.**

### Ask about something subtle
> *"Why should microservices use asynchronous communication?"*

- **RAG:** Retrieves the relevant microservices passage and grounds the answer precisely.
- **Fine-tune:** Answers from weight memory — may be vaguer if the exact concept wasn't strongly represented in training.

---

## One-Line Takeaway

**RAG retrieves** knowledge (accurate, updatable, honest about gaps, cites sources).
**Fine-tuning memorises** knowledge (fast, stylistically consistent, but hallucination-prone and expensive to update).

In production systems they are often combined: fine-tune for tone and format, RAG for current factual grounding.
