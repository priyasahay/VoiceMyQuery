// Study assistant UI: ask by voice OR text -> RAG / fine-tune / both -> spoken reply.

const recordBtn = document.getElementById("recordBtn");
const micWrap = document.getElementById("micWrap");
const statusEl = document.getElementById("status");
const transcriptEl = document.getElementById("transcript");
const transcriptBox = document.getElementById("transcriptBox");
const answersEl = document.getElementById("answers");
const healthEl = document.getElementById("health");
const cardTpl = document.getElementById("answerCard");
const textForm = document.getElementById("textForm");
const textBox = document.getElementById("textBox");
const audioToggle = document.getElementById("audioToggle");

let audioEnabled = true;
let currentAudio = null;  // track whatever is playing right now

audioToggle.addEventListener("click", () => {
  audioEnabled = !audioEnabled;
  audioToggle.textContent = audioEnabled ? "🔊 Audio on" : "🔇 Audio off";
  audioToggle.classList.toggle("muted", !audioEnabled);
  if (!audioEnabled && currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
    document.querySelectorAll(".replay.speaking").forEach(b => b.classList.remove("speaking"));
    statusEl.textContent = "Audio stopped — ask another question.";
  }
});

let mediaRecorder = null;
let chunks = [];

function selectedMode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

async function refreshHealth() {
  try {
    const h = await fetch("/health").then((r) => r.json());
    healthEl.innerHTML = [
      ["STT", h.stt_model, true],
      ["TTS", h.tts_engine, true],
      ["RAG", h.ollama_up ? "ready" : "Ollama down", h.ollama_up],
      ["Fine-tune", h.finetune_trained ? "ready" : "not trained", h.finetune_trained],
    ]
      .map(([k, v, ok]) => `<span>${k}: <b style="color:${ok ? "var(--success)" : "var(--danger)"}">${v}</b></span>`)
      .join("");
  } catch {
    healthEl.textContent = "backend unreachable";
  }
}

/* ---------- Recording ---------- */
async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  mediaRecorder.onstop = () => {
    stream.getTracks().forEach((t) => t.stop());
    handleAudio(new Blob(chunks, { type: "audio/webm" }));
  };
  mediaRecorder.start(200);
  recordBtn.classList.add("recording");
  micWrap.classList.add("recording");
  recordBtn.textContent = "● Recording… release";
  statusEl.textContent = "Listening…";
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  recordBtn.classList.remove("recording");
  micWrap.classList.remove("recording");
  recordBtn.textContent = "🎤 Hold to speak";
}

/* ---------- Cards ---------- */
function makeCard(mode) {
  const node = cardTpl.content.cloneNode(true);
  const card = node.querySelector(".card");
  const badge = node.querySelector(".badge");
  card.classList.add("loading", mode);
  badge.classList.add(mode);
  badge.textContent = mode === "rag" ? "RAG" : "Fine-tuned";
  card.querySelector(".answer").textContent = "thinking…";
  answersEl.appendChild(node);
  return card;
}

function fillCard(card, data, ms) {
  card.classList.remove("loading");
  card.querySelector(".answer").textContent = data.answer;
  card.querySelector(".latency").textContent = `${(ms / 1000).toFixed(1)}s`;
  const src = card.querySelector(".sources");
  if (data.sources && data.sources.length) {
    src.innerHTML = "<b>Sources:</b> " + data.sources.join(", ");
  } else if (data.mode === "finetune") {
    src.innerHTML = "<b>No retrieval</b> — answered from fine-tuned weights.";
  }
  const replay = card.querySelector(".replay");
  if (data.audio_url) {
    const audio = new Audio(data.audio_url);
    audio.onended = () => replay.classList.remove("speaking");
    replay.onclick = () => {
      replay.classList.add("speaking");
      audio.currentTime = 0;
      audio.play().catch(() => {});
    };
    return audio;
  }
  replay.style.display = "none";
  return null;
}

function playAudio(audio, replay) {
  return new Promise((resolve) => {
    if (!audio) { resolve(); return; }
    currentAudio = audio;
    if (replay) replay.classList.add("speaking");
    audio.currentTime = 0;
    audio.onended = () => {
      if (replay) replay.classList.remove("speaking");
      currentAudio = null;
      resolve();
    };
    audio.onerror = () => { currentAudio = null; resolve(); };
    audio.play().catch(() => { currentAudio = null; resolve(); });
  });
}

/* ---------- Ask (shared by voice + text) ---------- */
async function askText(question, mode, card) {
  const t0 = performance.now();
  try {
    const chat = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode }),
    });
    if (!chat.ok) throw new Error((await chat.json().catch(() => ({}))).detail || chat.statusText);
    const data = await chat.json();
    const speak = await fetch("/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: data.answer }),
    });
    if (speak.ok) data.audio_url = URL.createObjectURL(await speak.blob());
    const audio = fillCard(card, data, performance.now() - t0);
    return { audio, replay: card.querySelector(".replay") };
  } catch (err) {
    card.classList.remove("loading");
    card.querySelector(".answer").textContent = "⚠️ " + err.message;
    return { audio: null, replay: null };
  }
}

async function runQuestion(question) {
  transcriptBox.hidden = false;
  transcriptEl.textContent = question;
  answersEl.innerHTML = "";

  const mode = selectedMode();
  statusEl.textContent = "Generating answer…";
  const modes = mode === "both" ? ["rag", "finetune"] : [mode];
  answersEl.classList.toggle("compare", modes.length > 1);

  const cards = modes.map((m) => makeCard(m));

  // Fetch all responses in parallel (fast), but play audio sequentially
  const results = await Promise.all(modes.map((m, i) => askText(question, m, cards[i])));

  if (!audioEnabled) {
    statusEl.textContent = "Done — ask another question.";
    return;
  }

  if (modes.length === 1) {
    // Single mode — play immediately
    const { audio, replay } = results[0];
    statusEl.textContent = "Done — ask another question.";
    await playAudio(audio, replay);
  } else {
    // Compare mode — play RAG first, then Fine-tuned
    const labels = ["RAG", "Fine-tuned"];
    for (let i = 0; i < results.length; i++) {
      const { audio, replay } = results[i];
      if (audio) {
        statusEl.textContent = `🔊 Playing ${labels[i]} answer…`;
        await playAudio(audio, replay);
      }
    }
    statusEl.textContent = "Done — ask another question.";
  }
}

/* ---------- Voice path ---------- */
async function handleAudio(blob) {
  answersEl.innerHTML = "";
  if (blob.size < 2000) {
    statusEl.textContent = "Recording too short — hold the mic while you speak.";
    return;
  }
  statusEl.textContent = "Transcribing…";
  const fd = new FormData();
  fd.append("audio", blob, "speech.webm");

  let transcript;
  try {
    const res = await fetch("/transcribe", { method: "POST", body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { statusEl.textContent = data.error || "Transcription failed."; return; }
    transcript = data.text;
  } catch {
    statusEl.textContent = "Transcription failed — is the server running?";
    return;
  }

  if (!transcript) { statusEl.textContent = "Didn't catch that — try again."; return; }
  runQuestion(transcript);
}

/* ---------- Text path ---------- */
textForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = textBox.value.trim();
  if (!q) return;
  textBox.value = "";
  runQuestion(q);
});

/* ---------- Hold-to-talk ---------- */
recordBtn.addEventListener("mousedown", startRecording);
recordBtn.addEventListener("mouseup", stopRecording);
recordBtn.addEventListener("mouseleave", () => mediaRecorder?.state === "recording" && stopRecording());
recordBtn.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); });
recordBtn.addEventListener("touchend", (e) => { e.preventDefault(); stopRecording(); });

refreshHealth();
setInterval(refreshHealth, 15000);
