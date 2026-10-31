"""Speech-to-text (voice IN) using faster-whisper (MIT license).

Runs fully offline after the model is downloaded once. The model is loaded
lazily and cached, so the first transcription pays the load cost and later
calls are fast.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


@lru_cache(maxsize=1)
def _get_model():
    from faster_whisper import WhisperModel

    print(f"[stt] loading faster-whisper model '{config.STT_MODEL}' ...", flush=True)
    return WhisperModel(
        config.STT_MODEL,
        device=config.STT_DEVICE,
        compute_type=config.STT_COMPUTE_TYPE,
    )


def transcribe(audio_path: str, language: str | None = "en") -> str:
    """Transcribe an audio file (wav/mp3/webm/ogg) to text."""
    model = _get_model()
    segments, _info = model.transcribe(audio_path, language=language, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m common.stt <audio-file>")
        raise SystemExit(1)
    print(transcribe(sys.argv[1]))
