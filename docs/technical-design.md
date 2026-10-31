# Technical Design

## Design Goals

1. **Fully offline** — no cloud API calls, no data egress, no API keys.
2. **Fair comparison** — both iterations consume the exact same knowledge source (6 Markdown files), making RAG vs fine-tune differences attributable to the technique, not the data.
3. **Laptop-friendly** — runs on Apple Silicon (M1/M2/M3) without a GPU; LoRA keeps training under 30 min.
4. **Modular** — each layer (STT, TTS, RAG, fine-tune, server) is independently replaceable via config.

---

## Module Reference

### `config.py` — Central Configuration

All settings live here and every one can be overridden with an environment variable of the same name.

| Variable | Default | Description |
|---|---|---|
| `STT_MODEL` | `base` | Whisper model size: `tiny` / `base` / `small` / `medium` / `large-v3` |
| `STT_DEVICE` | `cpu` | `cpu` or `cuda` |
| `STT_COMPUTE_TYPE` | `int8` | Quantisation for faster-whisper |
| `TTS_ENGINE` | `auto` | `auto` \| `piper` \| `say` \| `pyttsx3` |
| `PIPER_MODEL_PATH` | `server/voices/en_US-lessac-medium.onnx` | Path to Piper ONNX model |
| `OLLAMA_HOST` | `http://localhost:11434` | Local Ollama endpoint |
| `RAG_LLM_MODEL` | `llama3.2:3b` | Ollama model tag |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `CHUNK_SIZE` | `1100` | Max characters per knowledge chunk |
| `TOP_K` | `4` | Chunks retrieved per query |
| `FINETUNE_BASE_MODEL` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | HuggingFace base model ID |
| `FINETUNE_EPOCHS` | `3` | Training epochs |
| `FINETUNE_LR` | `2e-4` | Learning rate |
| `FINETUNE_BATCH_SIZE` | `1` | Per-device batch size |
| `FINETUNE_MAX_LEN` | `512` | Max token length per training example |
| `HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `4005` | Server port |

---

### `common/stt.py` — Speech-to-Text

**Engine:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — a CTranslate2 re-implementation of OpenAI Whisper. Runs fully on CPU with int8 quantisation; no GPU required.

**Key choices:**
- `lru_cache(1)` on model load — loads once, stays in RAM for the server's lifetime.
- VAD (Voice Activity Detection) filter enabled — silences and dead air are skipped before transcription, improving accuracy on short mic recordings.
- Language hardcoded to `"en"` — avoids auto-detect latency.
- Accepts any audio format that ffmpeg understands (webm from browser, wav, mp3, ogg).

**Public API:**
```python
transcribe(audio_path: str, language: str = "en") -> str
```

---

### `common/tts.py` — Text-to-Speech

Three backends tried in priority order:

| Priority | Engine | Quality | Notes |
|---|---|---|---|
| 1 | **piper** | Neural (best) | Needs `en_US-lessac-medium.onnx` in `server/voices/` |
| 2 | **say** | Good (macOS only) | Uses macOS built-in `say` command, no install |
| 3 | **pyttsx3** | Acceptable | Cross-platform fallback, BSD licence |

`auto` mode (default) probes for piper first, then falls back in order. The active engine is reported in the `/health` endpoint.

**Output:** Always a 22050 Hz 16-bit PCM WAV file. The path is returned to the caller.

**Guard:** raises `RuntimeError` if the output file is missing or zero-byte — catches silent TTS failures.

---

### `common/llm.py` — Ollama Client

A thin `requests`-based HTTP client for the local Ollama server.

```python
is_up() -> bool           # GET /api/tags, 2s timeout
generate(prompt, system, model, temperature) -> str
                          # POST /api/generate, 120s timeout, streaming=False
```

The server checks `is_up()` before every RAG request and returns HTTP 503 with a helpful message if Ollama is down.

---

### `rag/ingest.py` — Index Builder

**Chunking strategy** (heading-aware):

1. `_split_into_sections` — splits each Markdown file on `##` headings. Each section becomes a unit of meaning.
2. `_pack_paragraphs` — merges consecutive short paragraphs within a section until `CHUNK_SIZE` (1100 chars) is reached, then starts a new chunk. This keeps related sentences together without crossing topic boundaries.
3. **Context prefix** — every chunk is prepended with `"{document title} — {section heading}"` before embedding. This ensures the embedding vector captures the topic ("Kubernetes — Health Probes") rather than just the text content. Significantly improves retrieval precision.

**Index type:** `IndexFlatIP` (inner product). Embeddings are L2-normalised before indexing, so inner product equals cosine similarity. Exact search (no approximation) — fast enough for a small KB.

**Artefacts written:**
- `rag/index/kb.faiss` — binary FAISS index
- `rag/index/chunks.json` — list of `{text, source, heading}` dicts, same order as index rows

---

### `rag/retriever.py` — Query Engine

```python
retrieve(query: str, top_k: int) -> list[dict]
```

1. Encodes the query with the same `all-MiniLM-L6-v2` model (cached).
2. L2-normalises the query vector.
3. `index.search(vector, top_k)` → distances + row indices.
4. Looks up `chunks.json` by index → returns `[{text, source, score}, ...]`.

The model and index are `lru_cache(1)` — loaded once when the first RAG query arrives.

---

### `rag/rag_pipeline.py` — RAG Answering

```python
answer(question: str, top_k: int = None) -> dict
```

Prompt template (strict grounding):
```
You are a concise teaching assistant for an M.Tech course...
Use ONLY the context below to answer the question.
If the context does not contain the answer, say you don't have that information.

Context:
[chunk 1 text]
---
[chunk 2 text]
...

Question: {question}
```

Returns:
```json
{
  "mode": "rag",
  "answer": "...",
  "sources": ["02_api_design.md", "03_microservices.md"],
  "retrieved": [{"source": "...", "score": 0.44}, ...]
}
```

---

### `finetune/prepare_dataset.py` — Training Data

45 hand-authored Q&A pairs covering all 6 knowledge-base topics:

| Topic | # Pairs |
|---|---|
| Cloud-native fundamentals | 8 |
| API design (REST/GraphQL/gRPC) | 9 |
| Microservices patterns | 8 |
| Containers & Kubernetes | 8 |
| DevOps & CI/CD | 6 |
| Security, resilience & observability | 6 |

Written in ChatML format (system + user + assistant messages) matching TinyLlama's native template.

---

### `finetune/train_lora.py` — LoRA Training

**Why LoRA?** Full fine-tuning of a 1.1B model requires ~10 GB VRAM and hours of training. LoRA adds small trainable rank-decomposition matrices (`r=16`) to the attention projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`), updating only ~0.5% of parameters. The result: ~10 MB adapter, ~30 min training on CPU.

**LoRA hyperparameters:**
| Param | Value | Rationale |
|---|---|---|
| `r` | 16 | Rank — controls capacity. 16 is sufficient for a small domain. |
| `lora_alpha` | 32 | Scale = alpha/r = 2. Standard starting point. |
| `dropout` | 0.05 | Light regularisation for small dataset. |
| `target_modules` | q, k, v, o projections | All attention heads — best for knowledge injection. |

**Training loop:** HuggingFace `Trainer` with `DataCollatorForLanguageModeling` (causal LM, no masked padding). Gradient checkpointing off (small model, fits in RAM).

**Device selection:** CUDA → MPS (Apple Silicon GPU) → CPU. MPS gives ~3× speedup over CPU on M-series chips.

---

### `finetune/finetune_pipeline.py` — Fine-tune Inference

```python
is_trained() -> bool      # checks adapter_config.json exists
answer(question, max_new_tokens=160) -> dict
```

**Generation settings:**
| Param | Value | Rationale |
|---|---|---|
| `do_sample` | `True` | Enables temperature sampling |
| `temperature` | `0.2` | Low → near-deterministic, factual answers |
| `repetition_penalty` | `1.3` | Prevents the model looping the same sentence |
| `max_new_tokens` | `160` | Keeps answers short enough for TTS |

**Startup preloading:** `server/app.py` spawns a daemon thread at startup that calls `_load()`. The `lru_cache(1)` on `_load` means the model is in memory before the first user request, avoiding the 30–60s cold-start timeout.

---

### `server/app.py` — FastAPI Server

Synchronous endpoints (FastAPI runs them in a threadpool automatically):

| Endpoint | Input | Output | Notes |
|---|---|---|---|
| `POST /transcribe` | multipart audio | `{text}` | Rejects < 2000 bytes |
| `POST /chat` | `{question, mode}` | `{mode, answer, sources, retrieved}` | Routes to RAG or FT |
| `POST /speak` | `{text}` | WAV file | Temp file served then retained briefly |
| `POST /ask` | audio + mode form | full round-trip JSON | Not used by current UI |
| `GET /health` | — | status JSON | Polled every 15s by UI |
| `GET /audio/{name}` | — | WAV file | Serves temp audio files |

Audio temp files are stored in `{tmpdir}/voice_assistant_audio/`. They are not cleaned up automatically — a background cleanup task could be added for long-running deployments.

---

### `server/static/app.js` — UI Logic

Key design decisions:

**Hold-to-talk:** `mousedown`/`touchstart` starts `MediaRecorder`; `mouseup`/`touchend`/`mouseleave` stops it and submits the blob. Blob size guard (< 2000 bytes) filters accidental taps.

**Parallel fetch, sequential audio:** In compare mode, both `/chat` + `/speak` calls are wrapped in `Promise.all` so both answers are generated simultaneously (fast). Audio playback then runs sequentially using `Promise` + `onended` event — RAG speaks first, fine-tuned after.

**Audio toggle:** `currentAudio` global tracks the playing `Audio` object. Toggling off calls `.pause()` + `.currentTime = 0` immediately, and clears all `.speaking` CSS classes. Future requests respect the `audioEnabled` flag before calling `playAudio()`.

**Lazy card creation:** Cards are created before the fetch starts (`makeCard`) so the loading shimmer appears immediately, improving perceived responsiveness.

---

## Key Design Decisions

### Why the same knowledge base for both?

The entire point of the project is to compare techniques, not data. Using the same 6 Markdown files for both RAG indexing and fine-tune Q&A generation means any quality difference between the two modes is due to the retrieval/memorisation mechanism, not information asymmetry.

### Why TinyLlama for fine-tuning?

- Apache 2.0 licence — fully permissive
- 1.1B parameters — trains in ~30 min on CPU, runs inference in ~5 seconds
- ChatML template support — easy to apply structured prompts
- Achieves good enough quality on a small, focused domain

### Why Llama 3.2 3B for RAG?

- Larger model → better instruction following and grounding
- Ollama handles model management (download, serving, GPU offloading)
- The RAG prompt constrains the model to retrieved context, so the quality difference vs fine-tuning is primarily about retrieval accuracy

### Why FAISS IndexFlatIP?

The knowledge base is small (~50–100 chunks). Exact search has zero approximation error and finishes in microseconds at this scale. Approximate methods (HNSW, IVF) would add complexity with no practical benefit here.

### Why heading-aware chunking?

Embedding a raw paragraph like *"It uses a uniform set of HTTP verbs"* gives a generic vector. Prefixing it with *"API Design — REST Constraints"* bakes the topic into the embedding, making retrieval far more accurate for domain questions.
