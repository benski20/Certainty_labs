"""
TransEBM trainer -- matches the EORM training procedure exactly.

Reference: https://github.com/ericjiang18/EnergyORM/blob/main/step1_train_ebm.py

Training loop:
  - Load EORM-format JSONL via load_q2cands_from_jsonl
  - Diversity-filtered train/val split via TrainValChunkDS
  - Bradley-Terry loss with all (pos, neg) pairs per group
  - FP16 AMP on CUDA, gradient clipping, cosine warmup
  - Validation every N epochs with EBM + naive accuracy
  - Save best-val-acc state_dict + tokenizer

Default data: results_gsm8k_llama_train_n4_temp0.7_p0.9_train_corrected.jsonl
"""

from __future__ import annotations

import copy
import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, List, Optional

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from transformers import get_cosine_schedule_with_warmup
from tqdm import tqdm

from .ebm_model import TransEBM
from .dataset import TrainValChunkDS, collate_fn
from .utils import (
    get_device_and_amp_helpers,
    setup_tokenizer,
    bradley_terry_loss,
    evaluate,
    load_q2cands_from_jsonl,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

DEFAULT_TRAIN_DATA = os.path.join(
    _PROJECT_ROOT,
    "demo_dataset",
    "results_gsm8k_llama3_train_n4_temp0.7_p0.9_train (2).jsonl",
)

DEFAULT_TEST_DATA = os.path.join(
    _PROJECT_ROOT,
    "demo_dataset",
    "results_gsm8k_llama3_test_n4_temp0.7_p0.9_test (2).jsonl",
)


@dataclass
class TrainingConfig:
    tokenizer_name: str = "gpt2"
    d_model: int = 768
    n_heads: int = 4
    n_layers: int = 2
    dropout: float = 0.2
    max_length: int = 2048
    epochs: int = 20
    batch_size: int = 1
    lr: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    fp16: bool = True
    device: str = "auto"
    val_holdout: float = 0.2
    validate_every: int = 1
    save_prefix: str = "ebm_certainty"
    num_workers: int = 0


class EBMTrainer:
    """
    End-to-end TransEBM trainer matching the EORM procedure.

    Supports:
      - EORM JSONL data (question/label/gen_text) -- default GSM8K-Llama
      - In-memory records from the Certainty pipeline/demo
      - Progress callbacks for Streamlit / API integration
    """

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        cfg = self.config

        self.device, self.use_amp, self.autocaster, self.scaler = (
            get_device_and_amp_helpers(cfg.device, cfg.fp16)
        )
        self.tok, self.pad_id, self.cls_id = setup_tokenizer(
            cfg.tokenizer_name, cfg.max_length
        )

    def train(
        self,
        data_path: Optional[str] = None,
        data_records: Optional[List[Dict[str, Any]]] = None,
        output_dir: str = "./model_artifacts",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Train TransEBM following the EORM procedure.

        Args:
            data_path: Path to EORM-format JSONL. Falls back to GSM8K-Llama demo
                       dataset at demo_dataset/results_gsm8k_llama_train_*.jsonl.
            data_records: In-memory records [{question, label, gen_text}, ...].
            output_dir: Directory for model, tokenizer, and metrics output.
            progress_callback: Optional fn(epoch, loss, val_acc) for UI updates.

        Returns:
            dict with best_val_acc, final_loss, epochs_trained, elapsed_seconds,
            model_path, tokenizer_path, history.
        """
        os.makedirs(output_dir, exist_ok=True)
        cfg = self.config

        # ── Load data into q2cands format (matching EnergyORM) ──────────
        q2cands = self._load_data(data_path, data_records)
        if not q2cands:
            raise ValueError(
                "No valid data found. Provide data_path or data_records with "
                "{question, label, gen_text} entries. "
                f"Default EORM demo data expected at: {DEFAULT_TRAIN_DATA}"
            )

        print(f"Total unique questions loaded: {len(q2cands)}")

        # ── Create train/val datasets (matching EnergyORM) ─────────────
        train_ds = TrainValChunkDS(
            self.tok,
            cfg.max_length,
            self.cls_id,
            self.pad_id,
            q2cands_data=copy.deepcopy(q2cands),
            split="train",
            holdout=cfg.val_holdout,
            dataset_name_log_prefix="certainty_",
        )
        val_ds = TrainValChunkDS(
            self.tok,
            cfg.max_length,
            self.cls_id,
            self.pad_id,
            q2cands_data=copy.deepcopy(q2cands),
            split="val",
            holdout=cfg.val_holdout,
            dataset_name_log_prefix="certainty_",
        )

        if len(train_ds) == 0:
            raise ValueError(
                "Training dataset is empty after diversity filtering. "
                "Need groups with both positive (label=1) and negative (label=0) candidates."
            )

        print(f"Training groups: {len(train_ds)}, Validation groups: {len(val_ds)}")

        # ── DataLoaders ─────────────────────────────────────────────────
        collate_with_pad = partial(collate_fn, pad_id=self.pad_id)
        pin_mem = self.device.type == "cuda"

        train_dl = DataLoader(
            train_ds,
            batch_size=cfg.batch_size,
            shuffle=True,
            collate_fn=collate_with_pad,
            pin_memory=pin_mem,
            num_workers=cfg.num_workers,
        )
        val_dl = None
        if len(val_ds) > 0:
            val_dl = DataLoader(
                val_ds,
                batch_size=cfg.batch_size,
                shuffle=False,
                collate_fn=collate_with_pad,
                pin_memory=pin_mem,
                num_workers=cfg.num_workers,
            )

        # Oracle accuracy on val set
        if val_ds and hasattr(val_ds, "groups") and val_ds.groups:
            oracle_hits = sum(
                1
                for g in val_ds.groups
                if isinstance(g, dict)
                and "meta" in g
                and g["meta"].get("has_correct", False)
            )
            oracle_acc = 100.0 * oracle_hits / len(val_ds.groups)
            print(
                f"Oracle accuracy on val set: {oracle_acc:.2f}% "
                f"({oracle_hits}/{len(val_ds.groups)} groups have a correct answer)"
            )

        # ── Model setup (matching EnergyORM) ───────────────────────────
        model = TransEBM(
            vocab_size=len(self.tok),
            d_model=cfg.d_model,
            n_heads=cfg.n_heads,
            n_layers=cfg.n_layers,
            dropout=cfg.dropout,
        ).to(self.device)

        if len(self.tok) != model.emb.num_embeddings:
            model.resize_token_embeddings(len(self.tok))

        opt = optim.AdamW(
            model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
        )

        num_train_batches = len(train_dl)
        if num_train_batches == 0:
            raise ValueError("Training DataLoader has zero batches.")

        total_steps = cfg.epochs * num_train_batches
        warmup_steps = int(cfg.warmup_ratio * total_steps)
        sched = get_cosine_schedule_with_warmup(
            opt,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        print(
            f"\nConfig: d_model={cfg.d_model}, n_layers={cfg.n_layers}, "
            f"n_heads={cfg.n_heads}, dropout={cfg.dropout}, max_len={cfg.max_length}"
        )
        print(
            f"Tokenizer: {cfg.tokenizer_name}, "
            f"CLS_ID: {self.cls_id}, PAD_ID: {self.pad_id}"
        )
        print(f"Device: {self.device}, FP16 (AMP): {self.use_amp}")
        print(
            f"Epochs: {cfg.epochs}, Batch Size: {cfg.batch_size}, "
            f"LR: {cfg.lr}, Weight Decay: {cfg.weight_decay}"
        )
        print(f"Validate every {cfg.validate_every} epoch(s).")

        # ── Training loop (matching EnergyORM step1_train_ebm.py) ──────
        best_val_acc = 0.0
        best_state = None
        history: List[Dict[str, float]] = []
        start_time = time.time()

        for ep in range(1, cfg.epochs + 1):
            model.train()
            total_ep_loss = 0.0
            batches_processed = 0

            pbar = tqdm(
                train_dl,
                desc=f"Epoch {ep}/{cfg.epochs} Training",
                unit="batch",
            )
            for idsL, maskL, labL in pbar:
                opt.zero_grad(set_to_none=True)
                batch_losses = []

                for ids_b, mask_b, lab_b in zip(idsL, maskL, labL):
                    if ids_b.numel() == 0:
                        continue
                    ids_b = ids_b.to(self.device)
                    mask_b = mask_b.to(self.device)
                    lab_b = lab_b.to(self.device)

                    with self.autocaster():
                        e = model(ids_b, mask_b)
                        loss_group = bradley_terry_loss(e, lab_b)

                    if loss_group is not None and torch.isfinite(loss_group):
                        batch_losses.append(loss_group)

                if not batch_losses:
                    continue

                loss = torch.stack(batch_losses).mean()

                if self.use_amp and self.scaler is not None:
                    self.scaler.scale(loss).backward()
                    self.scaler.unscale_(opt)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    self.scaler.step(opt)
                    self.scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    opt.step()

                sched.step()
                total_ep_loss += loss.item()
                batches_processed += 1
                pbar.set_postfix(
                    loss=f"{loss.item():.4f}",
                    lr=f"{sched.get_last_lr()[0]:.2e}",
                )

            avg_ep_loss = total_ep_loss / max(batches_processed, 1)
            print(f"Epoch {ep} finished. Average Training Loss: {avg_ep_loss:.4f}")

            # ── Validation (matching EnergyORM validate_every) ─────────
            val_acc = 0.0
            if ep % cfg.validate_every == 0 and val_dl is not None:
                naive_acc, val_acc = evaluate(
                    model, val_dl, self.device, self.autocaster, eval_type="Validation"
                )
                print(
                    f"Epoch {ep} Validation -> "
                    f"EBM Acc: {val_acc:.2f}% | Naive Acc: {naive_acc:.2f}%"
                )
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    best_state = copy.deepcopy(model.state_dict())
                    print(f"New best validation accuracy: {best_val_acc:.2f}%")
                else:
                    print(f"(Current best val acc: {best_val_acc:.2f}%)")

            history.append({"epoch": ep, "loss": avg_ep_loss, "val_acc": val_acc})

            if progress_callback:
                progress_callback(ep, avg_ep_loss, val_acc)

        elapsed = time.time() - start_time
        print(f"\nTraining finished in {elapsed:.1f}s.")

        # ── Save model and tokenizer (matching EnergyORM) ──────────────
        model_path = os.path.join(output_dir, f"{cfg.save_prefix}_model.pt")
        tokenizer_path = os.path.join(output_dir, f"{cfg.save_prefix}_tokenizer")

        if best_state is not None:
            print(
                f"Saving best model (Val Acc: {best_val_acc:.2f}%) to {model_path}"
            )
            model.load_state_dict(best_state)
        else:
            print(f"Saving final model to {model_path}")

        model.save(model_path)

        os.makedirs(tokenizer_path, exist_ok=True)
        self.tok.save_pretrained(tokenizer_path)

        metrics = {
            "best_val_acc": best_val_acc,
            "final_loss": history[-1]["loss"] if history else 0,
            "epochs_trained": len(history),
            "elapsed_seconds": round(elapsed, 1),
            "model_path": model_path,
            "tokenizer_path": tokenizer_path,
            "history": history,
        }
        metrics_path = os.path.join(
            output_dir, f"{cfg.save_prefix}_metrics.json"
        )
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"Training complete. Best val acc: {best_val_acc:.1f}%")
        return metrics

    def _load_data(
        self,
        data_path: Optional[str],
        data_records: Optional[List[Dict[str, Any]]],
    ) -> Optional[Dict[str, List[dict]]]:
        """
        Load data into q2cands format.

        Priority: data_records > data_path > default EORM demo dataset.
        """
        if data_records is not None:
            q2cands: Dict[str, List[dict]] = defaultdict(list)
            for item in data_records:
                q = item.get("question", "")
                if not q:
                    continue

                # Option 1: full EORM-style record with explicit label
                if "label" in item and (
                    "gen_text" in item or "generated_full_text" in item
                ):
                    q2cands[q].append(item)
                    continue

                # Option 2: preference-style record:
                #   { question, preferred: str, unpreferred: str, ...meta }
                # Convert into two EORM candidates with labels 1/0.
                if "preferred" in item and "unpreferred" in item:
                    pref_text = item.get("preferred")
                    unpref_text = item.get("unpreferred")
                    if isinstance(pref_text, str) and isinstance(unpref_text, str):
                        base_meta = {
                            k: v
                            for k, v in item.items()
                            if k not in {"preferred", "unpreferred"}
                        }
                        pos = {
                            **base_meta,
                            "question": q,
                            "label": 1,
                            "gen_text": pref_text,
                        }
                        neg = {
                            **base_meta,
                            "question": q,
                            "label": 0,
                            "gen_text": unpref_text,
                        }
                        q2cands[q].extend([pos, neg])

            if q2cands:
                print(
                    f"Loaded {sum(len(v) for v in q2cands.values())} in-memory records"
                )
                return dict(q2cands)
            return None

        if data_path is not None:
            return load_q2cands_from_jsonl(data_path, "training")

        if os.path.exists(DEFAULT_TRAIN_DATA):
            print(f"Using default EORM demo dataset: {DEFAULT_TRAIN_DATA}")
            return load_q2cands_from_jsonl(
                DEFAULT_TRAIN_DATA, "EORM demo (GSM8K-Llama)"
            )

        return None
