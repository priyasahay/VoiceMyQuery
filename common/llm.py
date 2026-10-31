"""Thin client for a local Ollama server (MIT-licensed runtime).

Used by the RAG iteration. No API key, no network egress beyond localhost.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def is_up() -> bool:
    try:
        requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=2)
        return True
    except requests.RequestException:
        return False


def generate(prompt: str, system: str | None = None, model: str | None = None,
             temperature: float = 0.2) -> str:
    """Single-shot completion from the local Ollama model."""
    payload = {
        "model": model or config.RAG_LLM_MODEL,
        "prompt": prompt,
        "system": system or config.SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(f"{config.OLLAMA_HOST}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()
