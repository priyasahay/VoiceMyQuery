"""LoRA fine-tuning (Iteration 2).

Fine-tunes a small, permissively-licensed base model (TinyLlama-1.1B, Apache 2.0)
on the course Q/A dataset using parameter-efficient LoRA adapters. Only the small
adapter is trained and saved, so this runs on a laptop (CPU, CUDA, or Apple MPS).

    python -m finetune.prepare_dataset     # first, build the dataset
    python -m finetune.train_lora          # then train

The result is written to finetune/adapter/ and loaded at inference by
finetune_pipeline.py. This is the opposite of RAG: knowledge is stored in the
adapter weights, not retrieved at query time.
"""
from __future__ import annotations

import sys
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


def train() -> None:
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    data_path = config.FINETUNE_DATA_DIR / "train.jsonl"
    if not data_path.exists():
        raise SystemExit("Dataset missing. Run:  python -m finetune.prepare_dataset")

    device = _select_device()
    print(f"[train] base={config.FINETUNE_BASE_MODEL} device={device}")

    tokenizer = AutoTokenizer.from_pretrained(config.FINETUNE_BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config.FINETUNE_BASE_MODEL,
        torch_dtype=torch.float32 if device != "cuda" else torch.float16,
    )
    model.to(device)

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def format_and_tokenize(example):
        # Render the chat into the model's own chat template, then tokenize.
        text = tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )
        out = tokenizer(text, truncation=True, max_length=config.FINETUNE_MAX_LEN, padding="max_length")
        return out

    dataset = load_dataset("json", data_files=str(data_path), split="train")
    dataset = dataset.map(format_and_tokenize, remove_columns=dataset.column_names)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args = TrainingArguments(
        output_dir=str(config.FINETUNE_ADAPTER_DIR / "_checkpoints"),
        num_train_epochs=config.FINETUNE_EPOCHS,
        per_device_train_batch_size=config.FINETUNE_BATCH_SIZE,
        gradient_accumulation_steps=4,
        learning_rate=config.FINETUNE_LR,
        logging_steps=5,
        save_strategy="no",
        report_to=[],
        use_cpu=(device == "cpu"),
    )

    trainer = Trainer(model=model, args=args, train_dataset=dataset, data_collator=collator)
    trainer.train()

    config.FINETUNE_ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(config.FINETUNE_ADAPTER_DIR))
    tokenizer.save_pretrained(str(config.FINETUNE_ADAPTER_DIR))
    print(f"[train] saved LoRA adapter to {config.FINETUNE_ADAPTER_DIR}")


if __name__ == "__main__":
    train()
