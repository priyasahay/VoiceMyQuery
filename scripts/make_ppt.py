"""Generate the project presentation as a .pptx file."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Brand colours ────────────────────────────────────────────────────────────
BG_DARK   = RGBColor(0x0F, 0x17, 0x2A)   # deep navy
BG_MID    = RGBColor(0x1A, 0x26, 0x3D)   # slide body
ACCENT    = RGBColor(0x4F, 0x46, 0xE5)   # indigo (primary)
RAG_C     = RGBColor(0x25, 0x63, 0xEB)   # blue
FT_C      = RGBColor(0x7C, 0x3A, 0xED)   # violet
SUCCESS   = RGBColor(0x10, 0xB9, 0x81)   # green
WARN      = RGBColor(0xF5, 0x9E, 0x0B)   # amber
DANGER    = RGBColor(0xEF, 0x44, 0x44)   # red
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
MUTED     = RGBColor(0x94, 0xA3, 0xB8)
CARD_BG   = RGBColor(0x1E, 0x2D, 0x45)

W = Inches(13.33)   # widescreen width
H = Inches(7.5)     # widescreen height

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

BLANK = prs.slide_layouts[6]   # truly blank layout


# ── Helpers ───────────────────────────────────────────────────────────────────

def add_slide():
    return prs.slides.add_slide(BLANK)


def bg(slide, color=BG_MID):
    """Fill slide background."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def box(slide, x, y, w, h, fill_color=None, line_color=None, line_width=Pt(0)):
    from pptx.util import Emu
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.line.width = line_width
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def txt(slide, text, x, y, w, h,
        size=24, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
        italic=False, wrap=True):
    txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return txb


def label_box(slide, label, x, y, w, h, fill, text_color=WHITE, size=16, bold=True):
    b = box(slide, x, y, w, h, fill_color=fill)
    b.line.fill.background()
    tf = b.text_frame
    tf.word_wrap = True
    p  = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    from pptx.util import Pt as Pt2
    from pptx.oxml.ns import qn
    # vertical centering
    from pptx.enum.text import MSO_ANCHOR
    tf.auto_size = None
    b.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    run = p.add_run()
    run.text = label
    run.font.size  = Pt2(size)
    run.font.bold  = bold
    run.font.color.rgb = text_color
    return b


def accent_bar(slide, color=ACCENT):
    box(slide, 0, 0, 13.33, 0.08, fill_color=color)


def slide_num(slide, n):
    txt(slide, str(n), 12.8, 7.15, 0.5, 0.3, size=12, color=MUTED, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s, BG_DARK)

# gradient band
box(s, 0, 2.5, 13.33, 2.8, fill_color=RGBColor(0x14, 0x1F, 0x35))
box(s, 0, 0,   13.33, 0.12, fill_color=ACCENT)
box(s, 0, 7.38, 13.33, 0.12, fill_color=ACCENT)

txt(s, "Voice Assistant", 1, 1.6, 11, 1.2, size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(s, "RAG  vs  Fine-tuning", 1, 2.85, 11, 0.8, size=36, bold=False, color=ACCENT, align=PP_ALIGN.CENTER)
txt(s, "M.Tech · API-based Cloud Native Solutions", 1, 3.75, 11, 0.5,
    size=18, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

# pills
for i, (label, col) in enumerate([("Fully Offline", SUCCESS), ("Voice-Driven", ACCENT), ("Open Source", RAG_C)]):
    px = 3.5 + i * 2.2
    label_box(s, label, px, 4.7, 2.0, 0.45, fill=col, size=14)

txt(s, "Ask a question by voice  ·  Compare two AI approaches  ·  Hear the difference",
    1, 5.5, 11, 0.5, size=15, color=MUTED, align=PP_ALIGN.CENTER, italic=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — What is this project?
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 2)

txt(s, "What is this project?", 0.5, 0.25, 10, 0.7, size=32, bold=True, color=WHITE)
txt(s, "A fully offline voice assistant that answers questions about cloud computing — and compares two AI techniques.",
    0.5, 1.0, 12.3, 0.7, size=18, color=MUTED)

# 3 feature cards
cards = [
    ("🎤", "Speak a Question", "Hold the mic button and ask anything about the course material. No typing needed."),
    ("🧠", "Two AI Approaches", "The same question is answered two different ways — RAG and Fine-tuning — so you can compare."),
    ("🔊", "Hear the Answer", "The assistant reads the answer aloud. In Compare mode, RAG speaks first, then Fine-tuned."),
]
for i, (icon, title, desc) in enumerate(cards):
    cx = 0.4 + i * 4.3
    box(s, cx, 1.9, 4.0, 3.2, fill_color=CARD_BG)
    txt(s, icon,  cx+0.2, 2.0,  3.6, 0.7, size=34, align=PP_ALIGN.CENTER)
    txt(s, title, cx+0.2, 2.75, 3.6, 0.5, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txt(s, desc,  cx+0.2, 3.3,  3.6, 1.5, size=14, color=MUTED, align=PP_ALIGN.CENTER)

txt(s, "Everything runs on your laptop. No internet. No API keys. No data leaves the machine.",
    0.5, 5.35, 12.3, 0.5, size=16, color=SUCCESS, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — The Problem
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 3)

txt(s, "The Problem We're Solving", 0.5, 0.25, 10, 0.7, size=32, bold=True, color=WHITE)
txt(s, "General AI models know nothing about your specific course material. How do you fix that?",
    0.5, 1.0, 12.3, 0.6, size=18, color=MUTED)

# big question box
box(s, 0.5, 1.8, 12.3, 1.1, fill_color=RGBColor(0x1E, 0x2D, 0x45))
txt(s, "❓  You ask: \"What is a circuit breaker in microservices?\"",
    0.7, 1.9, 12.0, 0.8, size=20, color=WHITE, bold=True)

# two answer cards
box(s, 0.4, 3.1, 5.7, 2.5, fill_color=RGBColor(0x2A, 0x1A, 0x1A))
txt(s, "❌  Generic AI", 0.6, 3.2, 5.3, 0.5, size=18, bold=True, color=DANGER)
txt(s, "Might hallucinate. Doesn't know your course notes. Can't cite where it got the answer from.",
    0.6, 3.75, 5.3, 1.5, size=14, color=MUTED)

box(s, 7.2, 3.1, 5.7, 2.5, fill_color=RGBColor(0x1A, 0x2A, 0x1A))
txt(s, "✅  This Project", 7.4, 3.2, 5.3, 0.5, size=18, bold=True, color=SUCCESS)
txt(s, "Grounded in your 6 Markdown course files. Cites the source. Honestly says when it doesn't know.",
    7.4, 3.75, 5.3, 1.5, size=14, color=MUTED)

txt(s, "Two solutions → same problem → different trade-offs. That's what this project demonstrates.",
    0.5, 5.85, 12.3, 0.5, size=15, color=ACCENT, italic=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — How it works (big picture)
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 4)

txt(s, "How It Works — Big Picture", 0.5, 0.25, 10, 0.7, size=32, bold=True, color=WHITE)

# flow steps
steps = [
    ("1", "You Speak", "Hold mic, ask a question", ACCENT),
    ("2", "Whisper STT", "Audio → Text\n(runs offline)", RAG_C),
    ("3", "AI Answers", "RAG or Fine-tune\npipeline runs", FT_C),
    ("4", "TTS Speaks", "Text → Speech\n(macOS voice)", SUCCESS),
]
arrow = "→"
for i, (num, title, desc, col) in enumerate(steps):
    cx = 0.3 + i * 3.1
    label_box(s, num, cx, 1.9, 0.5, 0.5, fill=col, size=18)
    box(s, cx, 2.5, 2.8, 2.2, fill_color=CARD_BG)
    txt(s, title, cx+0.1, 2.6, 2.6, 0.5, size=18, bold=True, color=col, align=PP_ALIGN.CENTER)
    txt(s, desc,  cx+0.1, 3.15, 2.6, 1.4, size=14, color=MUTED, align=PP_ALIGN.CENTER)
    if i < 3:
        txt(s, "→", cx+2.85, 3.4, 0.4, 0.4, size=24, color=MUTED, align=PP_ALIGN.CENTER)

# below: two paths
box(s, 0.4, 5.1, 5.8, 1.9, fill_color=RGBColor(0x0F, 0x20, 0x40))
txt(s, "🔵  RAG Path", 0.6, 5.15, 5.4, 0.45, size=17, bold=True, color=RAG_C)
txt(s, "Search notes → find relevant chunks → feed to Llama 3.2 3B → grounded answer + sources",
    0.6, 5.65, 5.4, 1.2, size=13, color=MUTED)

box(s, 7.1, 5.1, 5.8, 1.9, fill_color=RGBColor(0x1A, 0x0F, 0x35))
txt(s, "🟣  Fine-tune Path", 7.3, 5.15, 5.4, 0.45, size=17, bold=True, color=FT_C)
txt(s, "No search needed → TinyLlama 1.1B already memorised the material → direct answer from weights",
    7.3, 5.65, 5.4, 1.2, size=13, color=MUTED)

txt(s, "⬆", 6.4, 5.6, 0.5, 0.5, size=20, color=MUTED, align=PP_ALIGN.CENTER)
txt(s, "same\nquestion", 6.15, 6.1, 1.0, 0.7, size=11, color=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Iteration 1: RAG
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
box(s, 0, 0, 13.33, 0.08, fill_color=RAG_C)
slide_num(s, 5)

txt(s, "Iteration 1 — RAG", 0.5, 0.2, 8, 0.65, size=32, bold=True, color=WHITE)
label_box(s, "Open-book exam", 9.2, 0.25, 3.7, 0.55, fill=RAG_C, size=15)

txt(s, "Retrieval-Augmented Generation: find the right notes, then answer using them.",
    0.5, 0.95, 12.3, 0.5, size=17, color=MUTED)

# steps
rag_steps = [
    ("📄", "Knowledge Base", "6 Markdown files with course notes split into ~80 small chunks"),
    ("🔢", "Embed & Index", "Each chunk → 384-number vector (meaning fingerprint) stored in FAISS"),
    ("🔍", "Search", "Your question → vector → find top-4 closest chunks (semantic search)"),
    ("💬", "Generate", "Chunks + question sent to Llama 3.2 3B (Ollama) → grounded answer"),
]
for i, (icon, title, desc) in enumerate(rag_steps):
    cy = 1.65 + i * 1.3
    box(s, 0.4, cy, 12.4, 1.15, fill_color=CARD_BG)
    txt(s, icon,  0.55, cy+0.05, 0.7, 0.9, size=26, align=PP_ALIGN.CENTER)
    txt(s, f"Step {i+1}:  {title}", 1.35, cy+0.06, 5.5, 0.45, size=16, bold=True, color=RAG_C)
    txt(s, desc, 1.35, cy+0.53, 10.9, 0.55, size=13, color=MUTED)
    label_box(s, str(i+1), 12.0, cy+0.3, 0.5, 0.5, fill=RAG_C, size=13)

txt(s, "✅ Cites sources     ✅ Honest about gaps     ✅ Easy to update (seconds)     ✅ Uses big 3B model",
    0.5, 6.95, 12.3, 0.45, size=14, color=SUCCESS, align=PP_ALIGN.CENTER, bold=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Iteration 2: Fine-tuning
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
box(s, 0, 0, 13.33, 0.08, fill_color=FT_C)
slide_num(s, 6)

txt(s, "Iteration 2 — Fine-tuning", 0.5, 0.2, 8, 0.65, size=32, bold=True, color=WHITE)
label_box(s, "Closed-book exam", 9.0, 0.25, 3.9, 0.55, fill=FT_C, size=15)

txt(s, "LoRA fine-tuning: teach a small model to memorise course Q&A — no retrieval at query time.",
    0.5, 0.95, 12.3, 0.5, size=17, color=MUTED)

# left: training steps
txt(s, "Training  (done once)", 0.4, 1.55, 5.5, 0.45, size=18, bold=True, color=FT_C)
train_steps = [
    "45 Q&A pairs written from course material",
    "Base model: TinyLlama 1.1B  (Apache 2.0)",
    "LoRA adds tiny matrices on attention layers",
    "Only 0.5% of params trained  →  10 MB adapter",
    "Takes 10–30 min on CPU",
]
for i, step in enumerate(train_steps):
    box(s, 0.4, 2.1 + i*0.88, 5.9, 0.75, fill_color=CARD_BG)
    txt(s, f"  {i+1}.  {step}", 0.5, 2.17 + i*0.88, 5.7, 0.6, size=13, color=MUTED)

# right: inference
txt(s, "Inference  (every query)", 7.0, 1.55, 5.8, 0.45, size=18, bold=True, color=FT_C)
inf_steps = [
    ("⚡", "No search step"),
    ("🧠", "TinyLlama + adapter loaded in memory"),
    ("💬", "Generates answer purely from weights"),
    ("🚀", "~2–3s response (faster than RAG)"),
]
for i, (icon, step) in enumerate(inf_steps):
    box(s, 7.0, 2.1 + i*0.88, 5.9, 0.75, fill_color=CARD_BG)
    txt(s, f"  {icon}  {step}", 7.1, 2.17 + i*0.88, 5.7, 0.6, size=13, color=MUTED)

txt(s, "⚠️  Risk: confidently hallucinates on out-of-scope questions — no retrieval = no grounding",
    0.5, 6.88, 12.3, 0.5, size=14, color=WARN, align=PP_ALIGN.CENTER, bold=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — RAG vs Fine-tuning Comparison
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 7)

txt(s, "RAG  vs  Fine-tuning", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "Same question. Same knowledge. Different technique. Very different behaviour.",
    0.5, 0.9, 12.3, 0.45, size=16, color=MUTED)

# header row
label_box(s, "Dimension",   0.3,  1.5,  3.5, 0.5, fill=RGBColor(0x15, 0x20, 0x35), size=14)
label_box(s, "🔵  RAG",     3.9,  1.5,  4.2, 0.5, fill=RAG_C, size=14)
label_box(s, "🟣  Fine-tune", 8.2, 1.5, 4.7, 0.5, fill=FT_C, size=14)

rows = [
    ("Knowledge lives in",  "External index (FAISS)",            "Model weights"),
    ("Cites sources?",       "✅  Yes",                            "❌  No"),
    ("Out-of-scope Q",       "✅  \"I don't have that info\"",     "⚠️  Hallucinates confidently"),
    ("Update knowledge",     "✅  Re-index in seconds",           "🔄  Retrain adapter (30 min)"),
    ("Response speed",       "~4–8 sec",                          "~2–3 sec  (faster)"),
    ("Model size",           "Llama 3.2  3B  (via Ollama)",       "TinyLlama  1.1B  (local)"),
    ("Best when",            "Facts change, provenance matters",  "Fixed domain, speed matters"),
]
row_colors = [CARD_BG, RGBColor(0x17, 0x24, 0x38)]
for i, (dim, rag_val, ft_val) in enumerate(rows):
    cy = 2.1 + i * 0.68
    rc = row_colors[i % 2]
    box(s, 0.3,  cy, 3.5, 0.62, fill_color=rc)
    box(s, 3.9,  cy, 4.2, 0.62, fill_color=rc)
    box(s, 8.2,  cy, 4.7, 0.62, fill_color=rc)
    txt(s, dim,    0.45, cy+0.06, 3.2, 0.5, size=13, color=MUTED, bold=True)
    txt(s, rag_val, 4.0, cy+0.06, 4.0, 0.5, size=13, color=WHITE)
    txt(s, ft_val,  8.35, cy+0.06, 4.5, 0.5, size=13, color=WHITE)

txt(s, "💡  In production: combine both — fine-tune for tone, RAG for current facts.",
    0.5, 6.95, 12.3, 0.45, size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Tech Stack
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 8)

txt(s, "Tech Stack", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "100% free & open-source. Everything runs locally.",
    0.5, 0.9, 12.3, 0.45, size=16, color=MUTED)

stack = [
    ("🎤  Voice In",       "faster-whisper",               "Whisper speech-to-text, MIT, int8 CPU", RAG_C),
    ("🔊  Voice Out",      "macOS say  /  Piper",           "Text-to-speech, no install required",   RAG_C),
    ("🔍  RAG Search",     "FAISS + sentence-transformers", "Vector index + MiniLM-L6 embeddings",   ACCENT),
    ("🧠  RAG LLM",        "Llama 3.2 3B via Ollama",       "Local LLM runtime, Llama Community Lic",ACCENT),
    ("⚙️  Fine-tune",      "TinyLlama 1.1B + PEFT/LoRA",   "Apache 2.0, trains in 30 min on CPU",   FT_C),
    ("🌐  Web Server",     "FastAPI + Uvicorn",             "REST API + static UI, MIT",              FT_C),
    ("🖥️  Frontend",       "Vanilla JS  (no framework)",   "MediaRecorder, Fetch API, Web Audio",   SUCCESS),
]
for i, (layer, tool, desc, col) in enumerate(stack):
    cy = 1.5 + i * 0.77
    box(s, 0.3, cy, 12.7, 0.68, fill_color=CARD_BG)
    box(s, 0.3, cy, 0.07, 0.68, fill_color=col)
    txt(s, layer, 0.5,  cy+0.1, 2.5, 0.5, size=14, bold=True, color=col)
    txt(s, tool,  3.1,  cy+0.1, 4.0, 0.5, size=14, bold=True, color=WHITE)
    txt(s, desc,  7.2,  cy+0.1, 5.6, 0.5, size=13, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Knowledge Base
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 9)

txt(s, "The Knowledge Base", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "6 Markdown files covering the entire M.Tech course — used identically by both approaches.",
    0.5, 0.9, 12.3, 0.45, size=16, color=MUTED)

topics = [
    ("01", "Cloud Native Fundamentals",       "12-factor app, statelessness, elasticity, immutable infra",      ACCENT),
    ("02", "API Design",                      "REST, HTTP verbs, GraphQL, gRPC, versioning, OpenAPI",          RAG_C),
    ("03", "Microservices",                   "Decomposition, saga pattern, event-driven, service discovery",   FT_C),
    ("04", "Containers & Kubernetes",         "Docker, pods, deployments, health probes, service mesh",        SUCCESS),
    ("05", "DevOps & CI/CD",                  "Pipelines, blue-green, canary, GitOps, IaC, DORA metrics",      WARN),
    ("06", "Security, Resilience & Observability", "OAuth2, JWT, circuit breaker, SLOs, RED/USE metrics",     DANGER),
]
for i, (num, title, topics_str, col) in enumerate(topics):
    row = i // 2
    col_n = i % 2
    cx = 0.3 + col_n * 6.5
    cy = 1.55 + row * 1.7
    box(s, cx, cy, 6.2, 1.5, fill_color=CARD_BG)
    box(s, cx, cy, 0.07, 1.5, fill_color=col)
    label_box(s, num, cx+0.15, cy+0.35, 0.55, 0.55, fill=col, size=14)
    txt(s, title,      cx+0.85, cy+0.1,  5.2, 0.5,  size=15, bold=True, color=WHITE)
    txt(s, topics_str, cx+0.85, cy+0.62, 5.2, 0.75, size=12, color=MUTED)

txt(s, "Same 6 files → RAG indexes them | Fine-tuning trains on 45 Q&A pairs generated from them",
    0.5, 6.85, 12.3, 0.5, size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Live Demo / UI
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 10)

txt(s, "Using the UI", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "Open  http://127.0.0.1:4005  in your browser",
    0.5, 0.9, 12.3, 0.45, size=17, color=ACCENT, bold=True)

# UI mockup
box(s, 0.5, 1.5, 12.3, 5.5, fill_color=RGBColor(0x0A, 0x12, 0x22))
# header strip
box(s, 0.5, 1.5, 12.3, 0.6, fill_color=RGBColor(0x12, 0x1C, 0x33))
txt(s, "⬤  Voice Study Assistant  —  RAG vs Fine-tuning",
    0.7, 1.55, 12.0, 0.45, size=13, color=MUTED)

# health bar
box(s, 1.5, 2.25, 10.3, 0.4, fill_color=RGBColor(0x12, 0x1C, 0x33))
txt(s, "STT: base   TTS: say   RAG: ready   Fine-tune: ready",
    1.7, 2.3, 10.0, 0.3, size=11, color=SUCCESS)

# mic button
label_box(s, "🎤  Hold to speak", 4.7, 2.85, 3.9, 0.65, fill=ACCENT, size=16)

# mode selector
txt(s, "Answer with:", 2.3, 3.75, 2.5, 0.4, size=12, color=MUTED)
label_box(s, "RAG",          4.85, 3.75, 1.3, 0.4, fill=RAG_C,              size=12)
label_box(s, "Fine-tuned",   6.25, 3.75, 1.7, 0.4, fill=RGBColor(0x2A,0x1F,0x45), size=12, text_color=MUTED)
label_box(s, "Compare both", 8.05, 3.75, 2.0, 0.4, fill=RGBColor(0x2A,0x1F,0x45), size=12, text_color=MUTED)
label_box(s, "🔊 Audio on",  10.1, 3.75, 1.8, 0.4, fill=RGBColor(0x1E,0x2D,0x45), size=12, text_color=MUTED)

# answer card
box(s, 0.8, 4.35, 11.7, 1.8, fill_color=RGBColor(0x12, 0x1C, 0x33))
txt(s, "🔵  RAG", 1.0, 4.4, 2.0, 0.4, size=13, bold=True, color=RAG_C)
txt(s, "0.4s", 11.8, 4.4, 0.6, 0.4, size=11, color=MUTED, align=PP_ALIGN.RIGHT)
txt(s, "REST stands for Representational State Transfer. It treats everything as a resource...",
    1.0, 4.85, 11.2, 0.5, size=13, color=WHITE)
txt(s, "Sources: 02_api_design.md", 1.0, 5.45, 6.0, 0.4, size=11, color=MUTED)

# steps callouts
steps_ui = [
    (1.5, "Hold mic", "speak your question"),
    (4.8, "Pick mode", "RAG / Fine-tuned / Both"),
    (8.3, "Get answer", "text shown + read aloud"),
]
for x, title, sub in steps_ui:
    txt(s, f"①  {title}" if x < 3 else ("②  " + title if x < 6 else "③  " + title),
        x, 7.1, 3.0, 0.35, size=13, bold=True, color=ACCENT)
    txt(s, sub, x, 7.45, 3.0, 0.35, size=12, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Try these questions
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 11)

txt(s, "Try These Questions", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "Use Compare mode — ask each question to both approaches and observe the difference.",
    0.5, 0.9, 12.3, 0.45, size=16, color=MUTED)

questions = [
    ("In-Domain  ✅",
     ["What is the difference between PUT and PATCH?",
      "What is a circuit breaker pattern?",
      "How does a service mesh differ from an API gateway?",
      "What are the DORA metrics?"],
     RAG_C, "RAG: accurate + cited  |  Fine-tune: good on trained phrasings"),
    ("Paraphrased  🔄",
     ["How do containers save memory compared to VMs?",
      "Why must microservice processes be stateless?"],
     WARN, "RAG: handles well (semantic search)  |  Fine-tune: may struggle"),
    ("Out-of-Scope  ⚠️",
     ["What is the capital of France?",
      "How do you make sourdough bread?"],
     DANGER, "RAG: 'I don't have that information'  |  Fine-tune: HALLUCINATES"),
]

cy = 1.55
for cat, qs, col, note in questions:
    bh = 0.5 + len(qs) * 0.55
    box(s, 0.3, cy, 12.7, bh + 0.55, fill_color=CARD_BG)
    box(s, 0.3, cy, 0.07, bh + 0.55, fill_color=col)
    txt(s, cat, 0.55, cy + 0.1, 4.0, 0.45, size=15, bold=True, color=col)
    for j, q in enumerate(qs):
        txt(s, f'  “{q}”', 0.55, cy + 0.6 + j*0.52, 10.5, 0.47, size=13, color=WHITE, italic=True)
    txt(s, note, 0.55, cy + bh + 0.12, 12.2, 0.38, size=12, color=MUTED, italic=True)
    cy += bh + 0.75


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — Evaluation
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
slide_num(s, 12)

txt(s, "Automated Evaluation", 0.5, 0.2, 9, 0.65, size=32, bold=True, color=WHITE)
txt(s, "Run a 15-question benchmark through both pipelines and get a side-by-side report.",
    0.5, 0.9, 12.3, 0.45, size=16, color=MUTED)

box(s, 0.4, 1.5, 12.5, 0.7, fill_color=RGBColor(0x10, 0x18, 0x2A))
txt(s, "python -m evaluation.compare          # runs all 15 questions, writes evaluation/comparison_report.md",
    0.65, 1.6, 12.0, 0.5, size=15, color=SUCCESS, bold=True)

cats = [
    ("8",  "In-Domain",     "Questions directly answered by the course notes",  RAG_C),
    ("4",  "Paraphrased",   "Same concepts, different wording",                  WARN),
    ("3",  "Out-of-Scope",  "Completely unrelated — tests hallucination risk",   DANGER),
]
for i, (n, cat, desc, col) in enumerate(cats):
    cx = 0.4 + i * 4.2
    box(s, cx, 2.4, 4.0, 2.2, fill_color=CARD_BG)
    txt(s, n,    cx+0.2, 2.5,  3.6, 0.7, size=40, bold=True, color=col, align=PP_ALIGN.CENTER)
    txt(s, cat,  cx+0.2, 3.2,  3.6, 0.4, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txt(s, desc, cx+0.2, 3.65, 3.6, 0.8, size=12, color=MUTED, align=PP_ALIGN.CENTER)

txt(s, "What the report tells you:", 0.5, 4.85, 5.0, 0.45, size=17, bold=True, color=WHITE)
metrics = [
    "Side-by-side answers for every question",
    "Response latency (RAG typically 4–8s, Fine-tune 2–3s)",
    "RAG cites source documents; Fine-tune does not",
    "Out-of-scope: clear hallucination visible in Fine-tune answers",
]
for i, m in enumerate(metrics):
    txt(s, f"  ▸  {m}", 0.5, 5.4 + i*0.5, 12.2, 0.45, size=14, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — Key Takeaways
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s, BG_DARK)
box(s, 0, 0, 13.33, 0.08, fill_color=ACCENT)
slide_num(s, 13)

txt(s, "Key Takeaways", 0.5, 0.3, 9, 0.65, size=36, bold=True, color=WHITE)

takeaways = [
    (ACCENT, "Same knowledge, different technique — fair comparison",
     "Both RAG and Fine-tuning use the exact same 6 course files. Any quality difference is purely due to the technique."),
    (RAG_C, "RAG = open-book exam",
     "Retrieves relevant notes at query time. Honest about gaps. Cites sources. Easy to update."),
    (FT_C, "Fine-tuning = closed-book exam",
     "Memorises during training. Faster. But hallucinates confidently on anything outside the training data."),
    (SUCCESS, "Real-world lesson",
     "Production systems often combine both: fine-tune for tone and format, RAG for up-to-date factual grounding."),
    (WARN, "Everything is local",
     "No cloud APIs, no internet, no data shared. Runs fully on your laptop — privacy-preserving by design."),
]
for i, (col, title, desc) in enumerate(takeaways):
    cy = 1.2 + i * 1.15
    box(s, 0.3, cy, 12.7, 1.0, fill_color=CARD_BG)
    box(s, 0.3, cy, 0.1, 1.0, fill_color=col)
    txt(s, title, 0.6, cy + 0.08, 12.0, 0.4, size=16, bold=True, color=col)
    txt(s, desc,  0.6, cy + 0.5,  12.0, 0.45, size=13, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — Thank you / Q&A
# ══════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s, BG_DARK)
box(s, 0, 0,    13.33, 0.1, fill_color=ACCENT)
box(s, 0, 7.4,  13.33, 0.1, fill_color=ACCENT)

txt(s, "Thank You", 1, 1.6, 11, 1.2, size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(s, "Questions?", 1, 2.85, 11, 0.8, size=30, color=ACCENT, align=PP_ALIGN.CENTER)

links = [
    ("🔗 Repo",   "github.tools.sap/I528794/APIProject"),
    ("🌐 Server", "http://127.0.0.1:4005  (run locally)"),
    ("📋 Docs",   "docs/  folder in the repository"),
]
for i, (label, val) in enumerate(links):
    cx = 1.5 + i * 3.6
    box(s, cx, 4.1, 3.3, 1.0, fill_color=CARD_BG)
    txt(s, label, cx+0.15, 4.18, 3.0, 0.4, size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    txt(s, val,   cx+0.1,  4.62, 3.1, 0.4, size=11, color=MUTED, align=PP_ALIGN.CENTER)

txt(s, "Voice Assistant — RAG vs Fine-tuning  ·  M.Tech Cloud Native Solutions",
    1, 5.5, 11, 0.5, size=14, color=MUTED, align=PP_ALIGN.CENTER, italic=True)


# ── Save ─────────────────────────────────────────────────────────────────────
out = "/Users/I528794/voice-rag-vs-finetune/Voice_RAG_vs_FineTuning.pptx"
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides)} slides)")
