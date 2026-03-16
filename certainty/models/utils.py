"""
Utility functions for TransEBM training and evaluation.

Ported from the reference EORM implementation:
https://github.com/ericjiang18/EnergyORM/blob/main/utils.py

Provides:
  - Device and AMP resolution
  - Tokenizer setup with CLS/PAD handling
  - Bradley-Terry loss
  - Evaluation (naive + EBM accuracy)
  - JSONL data loading into q2cands format
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from contextlib import nullcontext
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer
from tqdm import tqdm


def get_device_and_amp_helpers(
    device_arg: str = "auto",
    fp16_arg: bool = False,
) -> Tuple[torch.device, bool, type, Optional[torch.cuda.amp.GradScaler]]:
    """Resolve compute device and configure AMP helpers."""
    if device_arg == "auto":
        if torch.cuda.is_available():
            dev = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            dev = torch.device("mps")
        else:
            dev = torch.device("cpu")
    else:
        dev = torch.device(device_arg)

    use_amp = fp16_arg and dev.type == "cuda"
    autocaster = torch.cuda.amp.autocast if use_amp else nullcontext
    scaler = torch.cuda.amp.GradScaler() if use_amp else None
    return dev, use_amp, autocaster, scaler


def setup_tokenizer(
    tokenizer_name_or_path: str = "gpt2",
    max_length: int = 2048,
) -> Tuple[AutoTokenizer, int, int]:
    """
    Set up tokenizer with CLS and PAD tokens.

    Handles GPT-2 and other tokenizers that may lack pad/cls tokens.
    Returns (tokenizer, pad_id, cls_id).
    """
    tok = AutoTokenizer.from_pretrained(tokenizer_name_or_path)
    tok.model_max_length = max_length

    if tok.pad_token_id is None:
        if tok.eos_token_id is not None:
            tok.pad_token = tok.eos_token
        elif tok.unk_token_id is not None:
            tok.pad_token = tok.unk_token
        else:
            tok.add_special_tokens({"pad_token": "[PAD]"})
    pad_id = tok.pad_token_id

    cls_id = None
    if hasattr(tok, "bos_token_id") and tok.bos_token_id is not None:
        cls_id = tok.bos_token_id
    elif hasattr(tok, "cls_token_id") and tok.cls_token_id is not None:
        cls_id = tok.cls_token_id
    elif tok.eos_token_id is not None:
        cls_id = tok.eos_token_id

    if cls_id is None or pad_id is None:
        raise ValueError(
            "Tokenizer lacks required special tokens. "
            "Need at least one of BOS/CLS/EOS for CLS_ID and a PAD token."
        )

    return tok, pad_id, cls_id


def bradley_terry_loss(
    e: torch.Tensor,
    l: torch.Tensor,
) -> Optional[torch.Tensor]:
    """
    Bradley-Terry pairwise ranking loss.

    For every (positive, negative) pair: L = mean(softplus(E_pos - E_neg)).
    Lower energy = better, so we want E_pos < E_neg.
    """
    pos_indices = torch.where(l == 1)[0]
    neg_indices = torch.where(l == 0)[0]
    if len(pos_indices) == 0 or len(neg_indices) == 0:
        return None
    pos_scores = e[pos_indices]
    neg_scores = e[neg_indices]
    energy_diffs = pos_scores.unsqueeze(1) - neg_scores.unsqueeze(0)
    loss_matrix = F.softplus(energy_diffs)
    return loss_matrix.mean()


@torch.no_grad()
def evaluate(
    model,
    loader,
    device: torch.device,
    autocaster,
    eval_type: str = "Validation",
) -> Tuple[float, float]:
    """
    Evaluate selection accuracy on grouped data.

    Returns (naive_acc, ebm_acc) as percentages.
    Naive accuracy: fraction where the first candidate is correct.
    EBM accuracy: fraction where argmin(energy) selects a correct candidate.
    """
    model.eval()
    total_groups = 0
    naive_correct = 0
    ebm_correct = 0

    if loader is None:
        return 0.0, 0.0

    pbar = tqdm(loader, desc=f"Evaluating ({eval_type})", leave=False, unit="batch")
    for idsL, maskL, labL in pbar:
        for ids, mask, lab in zip(idsL, maskL, labL):
            if ids.numel() == 0 or lab.numel() == 0:
                continue
            ids, mask, lab = ids.to(device), mask.to(device), lab.to(device)
            with autocaster():
                e = model(ids, mask)
            if e.numel() == 0:
                continue

            best_idx = torch.argmin(e)
            if lab.numel() > best_idx and lab[best_idx].item() == 1:
                ebm_correct += 1
            if lab.numel() > 0 and lab[0].item() == 1:
                naive_correct += 1

            total_groups += 1
            if total_groups > 0:
                pbar.set_postfix(acc=f"{100.0 * ebm_correct / total_groups:.2f}%")

    if total_groups == 0:
        return 0.0, 0.0
    return 100.0 * naive_correct / total_groups, 100.0 * ebm_correct / total_groups


def load_q2cands_from_jsonl(
    path: str,
    description: str = "data",
) -> Optional[Dict[str, List[dict]]]:
    """
    Load question-to-candidates mapping from EORM-format JSONL.

    Each line: {"question": ..., "label": 0|1, "gen_text": ...}
    Returns dict mapping question -> list of candidate dicts, or None on failure.
    """
    if not path or not os.path.exists(path) or not os.path.isfile(path):
        return None

    q2cands: Dict[str, List[dict]] = defaultdict(list)
    entries = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                ex = json.loads(line)
                if (
                    "question" in ex
                    and "label" in ex
                    and ("gen_text" in ex or "generated_full_text" in ex)
                ):
                    q2cands[ex["question"]].append(ex)
                    entries += 1
            except json.JSONDecodeError:
                continue

    if not q2cands:
        return None

    print(
        f"Loaded {description}: {entries} candidates across "
        f"{len(q2cands)} unique questions from {path}"
    )
    return dict(q2cands)
