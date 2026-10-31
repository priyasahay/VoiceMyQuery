# Setup Guide

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11 | `brew install python@3.11` |
| Ollama | latest | `brew install ollama` |
| Git | any | pre-installed on macOS |

macOS (Apple Silicon or Intel) is the primary supported platform. Linux works with minor adjustments (replace `say` TTS with `piper` or `pyttsx3`).

---

## Step-by-Step Setup

### 1. Clone and enter the project

```bash
git clone <repo-url> voice-rag-vs-finetune
cd voice-rag-vs-finetune
```

### 2. Create Python virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, faster-whisper, pyttsx3, sentence-transformers, faiss-cpu, PyTorch, transformers, peft, datasets, accelerate.

> First install takes 5–10 minutes — PyTorch alone is ~800 MB.

### 3. Start Ollama and download the RAG model

```bash
ollama serve &           # starts Ollama in background
ollama pull llama3.2:3b  # downloads ~2 GB, once only
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### 4. Build the RAG index

```bash
python -m rag.ingest
```

Reads all `knowledge_base/*.md` files, chunks them, embeds with `all-MiniLM-L6-v2`, and writes `rag/index/kb.faiss` + `rag/index/chunks.json`. Takes ~30 seconds on first run (model download included).

### 5. Start the server (RAG mode ready)

```bash
python -m server.app
```

Open **http://127.0.0.1:4005**. RAG and voice are fully functional at this point.

---

## Iteration 2 — Fine-tuning (Optional)

### 6. Prepare training data

```bash
python -m finetune.prepare_dataset
```

Writes 45 Q&A pairs to `finetune/data/train.jsonl`. This is fast (seconds) — the data is already authored in the script.

### 7. Train the LoRA adapter

```bash
python -m finetune.train_lora
```

| Device | Estimated time |
|---|---|
| Apple M1/M2/M3 (MPS) | 5–10 min |
| CPU only (Intel/AMD) | 15–30 min |
| NVIDIA GPU (CUDA) | 1–3 min |

The adapter is saved to `finetune/adapter/` (~10 MB).

### 8. Restart the server

```bash
# Stop the running server (Ctrl+C), then:
python -m server.app
```

**Fine-tuned** and **Compare both** modes are now enabled.

---

## One-Shot Bootstrap

```bash
./scripts/setup.sh
```

Runs all steps above automatically. Does not run training (step 7) — that's intentionally separate.

---

## Environment Variables

Override any setting without editing code:

```bash
# Use a better Whisper model (slower but more accurate)
STT_MODEL=small python -m server.app

# Use a different Ollama model
RAG_LLM_MODEL=mistral python -m server.app

# Change server port
PORT=8080 python -m server.app

# Retrieve more chunks per query
TOP_K=6 python -m server.app

# Faster fine-tune training (less accurate)
FINETUNE_EPOCHS=1 python -m finetune.train_lora
```

Full list of variables: see [Technical Design — config.py](technical-design.md#configpy--central-configuration).

---

## Optional: Better TTS with Piper

The default TTS uses macOS `say` (decent quality). For neural voice:

```bash
pip install piper-tts
mkdir -p server/voices
cd server/voices

# Download a voice model from https://github.com/rhasspy/piper/releases
# Example: en_US-lessac-medium
curl -LO https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
curl -LO https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json
```

The TTS layer auto-detects Piper on restart — no config change needed.

---

## Troubleshooting

### "Ollama not running" error in UI

```bash
ollama serve &
# Then refresh the page
```

### Mic blocked / no audio recording

Browsers only allow `getUserMedia` on `localhost` or HTTPS. Always use `http://127.0.0.1:4005`, not `http://localhost:4005`.

### Fine-tune OOM on CPU

Reduce memory usage:
```bash
FINETUNE_MAX_LEN=256 FINETUNE_BATCH_SIZE=1 python -m finetune.train_lora
```

### RAG index missing

```bash
python -m rag.ingest
```

### Fine-tune "adapter not found" after training

Check that training completed:
```bash
ls finetune/adapter/
# Should show: adapter_config.json  adapter_model.safetensors  tokenizer*.json
```

If empty, training may have been interrupted. Re-run `python -m finetune.train_lora`.

### Server port already in use

```bash
lsof -ti:4005 | xargs kill -9
python -m server.app
```

### Slow first response in fine-tune mode

The fine-tune model (~2.5 GB) is preloaded at startup in a background thread. Wait ~30–60 seconds after starting the server before making a fine-tune request. The `/health` endpoint will still return `finetune_trained: true` during preloading — this is expected.

---

## Rebuilding after knowledge base changes

If you edit or add files to `knowledge_base/`:

```bash
# Rebuild RAG index
python -m rag.ingest

# Regenerate Q&A pairs and retrain fine-tune
python -m finetune.prepare_dataset
python -m finetune.train_lora

# Restart server
python -m server.app
```
