"""FastAPI server: voice in -> RAG or fine-tuned answer -> voice out.

Endpoints:
  GET  /                 -> the voice web UI
  GET  /health           -> which backends are available
  POST /transcribe       -> audio file (multipart) -> {text}
  POST /chat             -> {question, mode} -> {answer, sources, ...}
  POST /speak            -> {text} -> audio/wav
  POST /ask              -> audio + mode -> full round trip {transcript, answer, audio_url}

Everything runs locally. RAG uses Ollama; fine-tune uses the local LoRA adapter.
"""
from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from common import stt, tts

app = FastAPI(title="Voice RAG vs Fine-tune Assistant")

_AUDIO_DIR = Path(tempfile.gettempdir()) / "voice_assistant_audio"
_AUDIO_DIR.mkdir(exist_ok=True)


def _preload_finetune():
    """Load the fine-tune model in the background at startup so first request is instant."""
    try:
        from finetune.finetune_pipeline import is_trained, _load
        if is_trained():
            _load()
    except Exception:
        pass  # silently ignore — will surface properly on first /chat request


@app.on_event("startup")
def startup():
    threading.Thread(target=_preload_finetune, daemon=True).start()


def _answer(question: str, mode: str) -> dict:
    if mode == "rag":
        from common import llm
        if not llm.is_up():
            raise HTTPException(503, f"Ollama not running at {config.OLLAMA_HOST}. Run: ollama serve")
        from rag.rag_pipeline import answer
        return answer(question)
    if mode == "finetune":
        from finetune.finetune_pipeline import answer, is_trained
        if not is_trained():
            raise HTTPException(503, "Fine-tuned adapter not found. Train it first (see README).")
        return answer(question)
    raise HTTPException(400, f"unknown mode '{mode}' (use 'rag' or 'finetune')")


class ChatRequest(BaseModel):
    question: str
    mode: str = "rag"


class SpeakRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    from common import llm
    from finetune.finetune_pipeline import is_trained

    return {
        "stt_model": config.STT_MODEL,
        "tts_engine": tts.active_engine(),
        "rag_llm": config.RAG_LLM_MODEL,
        "ollama_up": llm.is_up(),
        "finetune_trained": is_trained(),
        "rag_index_built": (config.RAG_INDEX_DIR / "kb.faiss").exists(),
    }


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    tmp = _AUDIO_DIR / f"in_{next(tempfile._get_candidate_names())}{suffix}"
    data = await audio.read()
    tmp.write_bytes(data)
    try:
        if len(data) < 2000:
            return JSONResponse(
                {"text": "", "error": "recording too short — hold the mic a bit longer"},
                status_code=422,
            )
        try:
            text = stt.transcribe(str(tmp))
        except Exception:
            return JSONResponse(
                {"text": "", "error": "could not decode audio — please try again"},
                status_code=422,
            )
    finally:
        tmp.unlink(missing_ok=True)
    return {"text": text}


@app.post("/chat")
def chat(req: ChatRequest):
    return _answer(req.question, req.mode)


@app.post("/speak")
def speak(req: SpeakRequest):
    out = _AUDIO_DIR / f"out_{next(tempfile._get_candidate_names())}.wav"
    tts.synthesize(req.text, str(out))
    return FileResponse(str(out), media_type="audio/wav", filename="reply.wav")


@app.post("/ask")
async def ask(audio: UploadFile = File(...), mode: str = Form("rag")):
    """Full voice round trip: speech in -> answer -> speech out."""
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    tmp = _AUDIO_DIR / f"in_{next(tempfile._get_candidate_names())}{suffix}"
    data = await audio.read()
    tmp.write_bytes(data)
    try:
        if len(data) < 2000:
            return JSONResponse({"error": "recording too short — hold the mic a bit longer"}, status_code=422)
        try:
            transcript = stt.transcribe(str(tmp))
        except Exception:
            return JSONResponse({"error": "could not decode audio — please try again"}, status_code=422)
    finally:
        tmp.unlink(missing_ok=True)

    if not transcript:
        return JSONResponse({"error": "Could not understand audio."}, status_code=422)

    result = _answer(transcript, mode)

    out = _AUDIO_DIR / f"out_{next(tempfile._get_candidate_names())}.wav"
    tts.synthesize(result["answer"], str(out))

    return {
        "transcript": transcript,
        "mode": result["mode"],
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "retrieved": result.get("retrieved", []),
        "audio_url": f"/audio/{out.name}",
    }


@app.get("/audio/{name}")
def get_audio(name: str):
    path = _AUDIO_DIR / name
    if not path.exists():
        raise HTTPException(404, "audio expired")
    return FileResponse(str(path), media_type="audio/wav")


# Static UI (mounted last so API routes take precedence).
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
