#!/usr/bin/env bash
# One-shot setup for the local voice assistant (macOS / Apple Silicon).
# Everything installed here is free and permissively licensed. No API keys.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 1/6  System deps (Python 3.11 + Ollama via Homebrew)"
command -v python3.11 >/dev/null || brew install python@3.11
command -v ollama    >/dev/null || brew install ollama

echo "==> 2/6  Python virtualenv + dependencies"
python3.11 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> 3/6  Start Ollama and pull the RAG model"
(ollama serve >/tmp/ollama.log 2>&1 &) || true
sleep 3
ollama pull llama3.2:3b

echo "==> 4/6  Build the RAG vector index"
python -m rag.ingest

echo "==> 5/6  Prepare the fine-tuning dataset"
python -m finetune.prepare_dataset

echo "==> 6/6  Done."
cat <<'EOF'

Next steps:
  source .venv/bin/activate

  # Iteration 1 (RAG) is ready now — start the voice UI:
  python -m server.app        # then open http://127.0.0.1:4005

  # Iteration 2 (fine-tuning) — train the adapter (5-20 min), then restart:
  python -m finetune.train_lora

  # Compare both:
  python -m evaluation.compare
EOF
