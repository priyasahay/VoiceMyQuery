"""Text-to-speech (voice OUT).

Fully-offline, permissively-licensed backends, tried in this order for "auto":
  * piper   - Piper neural TTS (MIT). High quality. Needs a downloaded .onnx voice.
  * say     - macOS built-in `say` command. Native, free, reliable WAV output.
  * pyttsx3 - wraps the OS speech engine (BSD). Cross-platform fallback.

TTS_ENGINE="auto" picks the best available. Output is always a WAV file the
browser can play.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def _piper_available() -> bool:
    return shutil.which("piper") is not None and Path(config.PIPER_MODEL_PATH).exists()


def _say_available() -> bool:
    return platform.system() == "Darwin" and shutil.which("say") is not None


def _synthesize_piper(text: str, out_path: str) -> None:
    # piper reads text on stdin and writes a wav to --output_file
    subprocess.run(
        ["piper", "--model", config.PIPER_MODEL_PATH, "--output_file", out_path],
        input=text.encode("utf-8"),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _synthesize_say(text: str, out_path: str) -> None:
    # macOS `say` writes a proper WAV with explicit file/data format flags.
    subprocess.run(
        ["say", "--file-format=WAVE", "--data-format=LEI16@22050", "-o", out_path, text],
        check=True,
    )


def _synthesize_pyttsx3(text: str, out_path: str) -> None:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.save_to_file(text, out_path)
    engine.runAndWait()


def synthesize(text: str, out_path: str | None = None) -> str:
    """Render `text` to a WAV file and return its path."""
    if out_path is None:
        out_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    engine = active_engine()

    if engine == "piper":
        _synthesize_piper(text, out_path)
    elif engine == "say":
        _synthesize_say(text, out_path)
    else:
        _synthesize_pyttsx3(text, out_path)

    # Guard against an empty/failed render so the API never returns a broken file.
    if not Path(out_path).exists() or Path(out_path).stat().st_size == 0:
        raise RuntimeError(f"TTS engine '{engine}' produced no audio")
    return out_path


def active_engine() -> str:
    if config.TTS_ENGINE != "auto":
        return config.TTS_ENGINE
    if _piper_available():
        return "piper"
    if _say_available():
        return "say"
    return "pyttsx3"


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Hello from the local voice assistant."
    path = synthesize(text)
    print(f"engine={active_engine()} wrote {path}")
