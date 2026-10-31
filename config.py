"""Central configuration for the voice assistant.

Everything is local and free/open-source. No API keys, no data leaves the machine.
Override any value with an environment variable of the same name.
"""
import os
from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
RAG_INDEX_DIR = ROOT / "rag" / "index"
FINETUNE_DATA_DIR = ROOT / "finetune" / "data"
FINETUNE_ADAPTER_DIR = ROOT / "finetune" / "adapter"

# --- Speech-to-text (voice IN): faster-whisper, MIT license ------------------
# Models are downloaded once from Hugging Face then run fully offline.
# tiny/base/small/medium/large-v3 -> trade speed for accuracy.
STT_MODEL = os.getenv("STT_MODEL", "base")
STT_DEVICE = os.getenv("STT_DEVICE", "cpu")        # "cpu" or "cuda"
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")

# --- Text-to-speech (voice OUT) ---------------------------------------------
# Preferred: Piper (MIT). Fallback: pyttsx3 (BSD, uses OS voices, no download).
TTS_ENGINE = os.getenv("TTS_ENGINE", "auto")       # "auto" | "piper" | "pyttsx3"
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", str(ROOT / "server" / "voices" / "en_US-lessac-medium.onnx"))

# --- LLM for the RAG iteration: Ollama, MIT-licensed local runtime -----------
# Llama 3.2 is free under the Llama Community License. Swap for mistral / phi3 if preferred.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama3.2:3b")

# --- Embeddings for RAG: sentence-transformers, Apache 2.0 -------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --- RAG retrieval knobs -----------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1100"))      # max chars per section chunk
TOP_K = int(os.getenv("TOP_K", "4"))                   # chunks retrieved per query

# --- Fine-tuning iteration: base model must be permissively licensed ---------
# TinyLlama-1.1B is Apache 2.0 and small enough to LoRA-fine-tune on a laptop.
FINETUNE_BASE_MODEL = os.getenv("FINETUNE_BASE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
FINETUNE_EPOCHS = int(os.getenv("FINETUNE_EPOCHS", "3"))
FINETUNE_LR = float(os.getenv("FINETUNE_LR", "2e-4"))
FINETUNE_BATCH_SIZE = int(os.getenv("FINETUNE_BATCH_SIZE", "1"))
FINETUNE_MAX_LEN = int(os.getenv("FINETUNE_MAX_LEN", "512"))

# --- Server ------------------------------------------------------------------
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "4005"))

SYSTEM_PROMPT = (
    "You are a concise teaching assistant for an M.Tech course on "
    "'API-based Cloud Native Solutions'. Answer clearly and accurately for a "
    "graduate student. Keep answers to a few sentences suitable for being read aloud."
)
