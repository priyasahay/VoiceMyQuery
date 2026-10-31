# Voice Assistant — RAG vs Fine-tuning

A **fully offline** voice-driven study assistant for the M.Tech course **"API-based Cloud Native Solutions"**. You speak a question, it answers out loud. The project exists to let you *see and hear* the difference between two AI grounding strategies on the same questions:

| | Iteration 1 — RAG | Iteration 2 — Fine-tuning |
|---|---|---|
| **Idea** | Look up the answer at query time | Memorise the answer during training |
| **Model** | Llama 3.2 3B (via Ollama) | TinyLlama 1.1B + LoRA adapter |
| **Knowledge lives in** | FAISS vector index | Model weights |
| **Cites sources?** | Yes | No |
| **Update knowledge** | Re-run `rag.ingest` (seconds) | Retrain adapter (minutes) |

Everything runs **on your machine**. No API keys. No data leaves the box.

---

## Quick Start (macOS)

```bash
# 1. Bootstrap everything in one shot
cd voice-rag-vs-finetune
./scripts/setup.sh

# 2. Activate the environment and start the server
source .venv/bin/activate
python -m server.app
```

Open **http://127.0.0.1:4005** — hold the mic button, ask a question, pick **RAG**, **Fine-tuned**, or **Compare both**.

> Fine-tuned mode requires training first — see [Setup Guide](docs/setup-guide.md).

---

## Manual Setup

```bash
# Dependencies
brew install python@3.11 ollama
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# RAG backend
ollama serve &
ollama pull llama3.2:3b
python -m rag.ingest          # builds FAISS index from knowledge_base/

# Fine-tune backend (optional, ~10–30 min on CPU)
python -m finetune.train_lora

# Start server
python -m server.app          # → http://127.0.0.1:4005
```

---

## Documentation

| Document | What it covers |
|---|---|
| [Architecture](docs/architecture.md) | System diagrams, component map, data-flow |
| [Technical Design](docs/technical-design.md) | Design decisions, module internals, config reference |
| [API Reference](docs/api-reference.md) | All REST endpoints with request/response schemas |
| [Setup Guide](docs/setup-guide.md) | Step-by-step setup, env vars, troubleshooting |
| [RAG vs Fine-tuning](docs/rag-vs-finetune.md) | Conceptual deep-dive into the two approaches |
| [Evaluation Guide](docs/evaluation-guide.md) | Running the comparison harness and reading results |

---

## Project Layout

```
voice-rag-vs-finetune/
│
├── knowledge_base/           6 Markdown files — the shared corpus
│   ├── 01_cloud_native_fundamentals.md
│   ├── 02_api_design.md
│   ├── 03_microservices.md
│   ├── 04_containers_kubernetes.md
│   ├── 05_devops_cicd.md
│   └── 06_security_resilience_observability.md
│
├── common/                   Shared voice + LLM utilities
│   ├── stt.py                Speech-to-text (faster-whisper)
│   ├── tts.py                Text-to-speech (piper / say / pyttsx3)
│   └── llm.py                Ollama HTTP client
│
├── rag/                      Iteration 1 — Retrieval-Augmented Generation
│   ├── ingest.py             Build FAISS index from knowledge_base/
│   ├── retriever.py          Query the index
│   ├── rag_pipeline.py       Retrieve → prompt → generate
│   └── index/                kb.faiss + chunks.json (auto-generated)
│
├── finetune/                 Iteration 2 — LoRA fine-tuning
│   ├── prepare_dataset.py    Generate train.jsonl from knowledge base
│   ├── train_lora.py         LoRA fine-tune TinyLlama
│   ├── finetune_pipeline.py  Inference with trained adapter
│   ├── data/train.jsonl      45 Q&A pairs (auto-generated)
│   └── adapter/              Saved LoRA weights (after training)
│
├── server/                   FastAPI web server + UI
│   ├── app.py                REST endpoints
│   └── static/               index.html + app.js + style.css
│
├── evaluation/               Comparison harness
│   ├── questions.py          15 held-out test questions
│   └── compare.py            Run both, produce comparison_report.md
│
├── docs/                     Full documentation
├── config.py                 All settings (override via env vars)
├── requirements.txt
└── scripts/setup.sh          One-shot bootstrap
```

---

## Licences

| Component | Library / Model | Licence |
|---|---|---|
| Speech-to-text | faster-whisper | MIT |
| Text-to-speech | Piper / pyttsx3 | MIT / BSD |
| RAG embeddings | sentence-transformers all-MiniLM-L6-v2 | Apache 2.0 |
| Vector index | FAISS | MIT |
| RAG LLM | Llama 3.2 3B via Ollama | Llama Community Licence (free) |
| Fine-tune base | TinyLlama-1.1B-Chat | Apache 2.0 |
| Fine-tune method | PEFT / LoRA | Apache 2.0 |
| Web server | FastAPI + Uvicorn | MIT / BSD |

All components are free for research and educational use.
