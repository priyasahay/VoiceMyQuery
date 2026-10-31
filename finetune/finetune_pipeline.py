"""Fine-tuned inference (Iteration 2).

Loads the base model + the trained LoRA adapter and answers from the knowledge
baked into its weights. There is NO retrieval and NO external context: this is
the direct contrast to the RAG pipeline.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def _select_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def is_trained() -> bool:
    return (config.FINETUNE_ADAPTER_DIR / "adapter_config.json").exists()


@lru_cache(maxsize=1)
def _load():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not is_trained():
        raise SystemExit(
            "No fine-tuned adapter found. Train it first:\n"
            "  python -m finetune.prepare_dataset && python -m finetune.train_lora"
        )

    device = _select_device()
    tokenizer = AutoTokenizer.from_pretrained(str(config.FINETUNE_ADAPTER_DIR))
    base = AutoModelForCausalLM.from_pretrained(
        config.FINETUNE_BASE_MODEL,
        torch_dtype=torch.float32 if device != "cuda" else torch.float16,
    )
    model = PeftModel.from_pretrained(base, str(config.FINETUNE_ADAPTER_DIR))
    model.to(device).eval()
    return tokenizer, model, device


def answer(question: str, max_new_tokens: int = 160) -> dict:
    import torch

    tokenizer, model, device = _load()
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.2,
            repetition_penalty=1.3,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )
    text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return {"mode": "finetune", "answer": text, "sources": [], "retrieved": []}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is a circuit breaker?"
    print(answer(q)["answer"])
