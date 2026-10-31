# Architecture

## 1. High-Level Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (UI)                          │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ Mic/Text │  │  Mode Picker  │  │   Answer Cards + TTS │  │
│  │  input   │  │RAG|FT|Compare │  │   (sequential audio) │  │
│  └────┬─────┘  └───────┬───────┘  └──────────┬───────────┘  │
└───────┼────────────────┼───────────────────────┼────────────┘
        │ webm/text      │                       │ WAV
        ▼                ▼                       ▲
┌───────────────────────────────────────────────────────────┐
│                    FastAPI Server (port 4005)              │
│  POST /transcribe   POST /chat   POST /speak   GET /audio  │
│        │                 │            │                    │
│    faster-whisper    _answer()    tts.synthesize()         │
│    (speech→text)        │         (text→WAV)               │
│                    ┌────┴────┐                             │
│                 rag│         │finetune                     │
│                    ▼         ▼                             │
│            rag_pipeline  finetune_pipeline                 │
└────────────────────────────────────────────────────────────┘
          │                         │
          ▼                         ▼
  ┌───────────────┐        ┌────────────────────┐
  │  FAISS Index  │        │  TinyLlama 1.1B    │
  │  (kb.faiss)   │        │  + LoRA Adapter    │
  │  + Embedder   │        │  (local weights)   │
  │  MiniLM-L6-v2 │        └────────────────────┘
  └───────┬───────┘
          │ top-4 chunks
          ▼
  ┌───────────────┐
  │  Ollama LLM   │
  │  llama3.2:3b  │
  │  (port 11434) │
  └───────────────┘
```

---

## 2. Request Flow — Single Mode

```
User speaks
    │
    ▼  (webm audio blob)
POST /transcribe
    │
    ▼  faster-whisper
"What is a circuit breaker?"
    │
    ▼  POST /chat  {question, mode:"rag"}
    │
    ├─── [RAG PATH] ──────────────────────────────────────────────┐
    │   1. Embed question  (all-MiniLM-L6-v2, 384-dim)            │
    │   2. FAISS inner-product search → top-4 chunks              │
    │   3. Build prompt:                                           │
    │      "Context: <chunk1>...<chunk4>                          │
    │       Answer ONLY from context. Question: ..."              │
    │   4. POST Ollama /api/generate (llama3.2:3b)                 │
    │   5. Return {answer, sources:[...], retrieved:[...]}         │
    └─────────────────────────────────────────────────────────────┘
    │
    ├─── [FINE-TUNE PATH] ────────────────────────────────────────┐
    │   1. Apply ChatML template                                   │
    │      <|system|>...<|user|>...<|assistant|>                  │
    │   2. Tokenize (TinyLlama tokenizer)                          │
    │   3. model.generate (TinyLlama + LoRA adapter)               │
    │      do_sample=True, temp=0.2, rep_penalty=1.3               │
    │   4. Decode output tokens → strip prompt                     │
    │   5. Return {answer, sources:[], retrieved:[]}               │
    └─────────────────────────────────────────────────────────────┘
    │
    ▼  POST /speak  {text: answer}
    tts.synthesize() → WAV file
    │
    ▼  FileResponse (audio/wav)
Browser plays audio
```

---

## 3. Request Flow — Compare Mode

```
POST /chat (mode=rag)  ──┐
                          ├── Promise.all() → both fetched in parallel
POST /chat (mode=ft)   ──┘
                          │
                          ▼  both cards filled simultaneously
                    ┌─────┴──────┐
                    │            │
                 RAG card     FT card
                 (shown)      (shown)
                    │
                    ▼  sequential audio playback
               Play RAG audio
                    │ (waits for onended)
                    ▼
               Play FT audio
                    │
                    ▼
              "Done — ask another question."
```

---

## 4. RAG Pipeline Detail

```
knowledge_base/*.md
        │
        ▼  rag/ingest.py
┌────────────────────────────────────┐
│  1. Parse Markdown                 │
│     • split on ## headings         │
│     • pack paragraphs ≤ 1100 chars │
│     • prefix: "DocTitle — Section" │
│  → ~N chunks                       │
│                                    │
│  2. Embed                          │
│     sentence-transformers          │
│     all-MiniLM-L6-v2               │
│     → 384-dimensional vectors      │
│     L2-normalised (cosine sim)     │
│                                    │
│  3. Index                          │
│     FAISS IndexFlatIP              │
│     (inner product = cosine on     │
│      normalised vectors)           │
└─────────────┬──────────────────────┘
              │ write
              ▼
   rag/index/kb.faiss        (binary index)
   rag/index/chunks.json     (text + metadata)

─────────────────────────────────── query time ──

query string
   │
   ▼  embed (same model, lru_cache)
384-dim vector
   │
   ▼  FAISS search top-k=4
chunk scores + indices
   │
   ▼  lookup chunks.json
[{text, source, score}, ...]
   │
   ▼  format prompt
"Context:\n[chunk1]\n[chunk2]...\nQuestion: ..."
   │
   ▼  Ollama llama3.2:3b
answer string
```

---

## 5. Fine-tuning Pipeline Detail

```
knowledge_base/*.md
        │
        ▼  finetune/prepare_dataset.py
45 hand-authored Q&A pairs
(covering all 6 topic areas)
        │
        ▼  write ChatML format
finetune/data/train.jsonl
  {"messages": [
    {"role": "system", "content": "..."},
    {"role": "user",   "content": "question"},
    {"role": "assistant", "content": "answer"}
  ]}

─────────────────────────────────── training ──

        ▼  finetune/train_lora.py
┌────────────────────────────────────────┐
│  Base: TinyLlama/TinyLlama-1.1B-Chat   │
│                                        │
│  LoRA config:                          │
│    r=16, alpha=32, dropout=0.05        │
│    target: q_proj k_proj v_proj o_proj │
│                                        │
│  Training:                             │
│    epochs=3, lr=2e-4, batch=1          │
│    max_len=512 tokens                  │
│    HuggingFace Trainer                 │
│    device: CUDA → MPS → CPU            │
└────────────────┬───────────────────────┘
                 │ save
                 ▼
  finetune/adapter/
    adapter_config.json
    adapter_model.safetensors   (~10 MB)
    tokenizer*.json

─────────────────────────────────── inference ──

query string
   │
   ▼  apply_chat_template
formatted prompt string
   │
   ▼  tokenizer → input_ids
   │
   ▼  PeftModel(TinyLlama + adapter).generate()
output tokens
   │
   ▼  decode + strip prompt
answer string
```

---

## 6. Voice I/O Layers

```
┌──────────────────────────────────────────┐
│  Speech-to-Text (common/stt.py)          │
│                                          │
│  Engine: faster-whisper                  │
│  Model:  base (configurable)             │
│  Device: cpu (configurable)              │
│  Compute: int8 quantised                 │
│                                          │
│  Input:  any audio (wav/webm/mp3/ogg)    │
│  Output: transcribed text string         │
│  Feature: VAD filter (silence skipped)   │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Text-to-Speech (common/tts.py)          │
│                                          │
│  Priority order:                         │
│  1. piper   (neural, needs .onnx model)  │
│  2. say     (macOS built-in, no install) │
│  3. pyttsx3 (cross-platform fallback)    │
│                                          │
│  Input:  text string                     │
│  Output: WAV file path (22050 Hz LEI16)  │
└──────────────────────────────────────────┘
```

---

## 7. Memory & Process Model

```
Process: python -m server.app (single uvicorn worker)
│
├── STT model (faster-whisper base)
│     loaded on first /transcribe — ~80 MB
│     lru_cache(1) — stays in memory
│
├── RAG embedder (all-MiniLM-L6-v2)
│     loaded on first /chat?mode=rag — ~90 MB
│     lru_cache(1)
│
├── FAISS index (kb.faiss)
│     loaded alongside embedder — tiny (~1 MB)
│     lru_cache(1)
│
├── Ollama (separate process, port 11434)
│     llama3.2:3b — ~2 GB VRAM/RAM
│     managed by Ollama runtime
│
└── Fine-tune model (TinyLlama + LoRA)
      preloaded at startup in daemon thread — ~2.5 GB RAM
      lru_cache(1) — stays in memory after first load
```
