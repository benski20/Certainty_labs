"""
Group-based dataset for TransEBM training.

Ported from the reference EORM implementation:
https://github.com/ericjiang18/EnergyORM/blob/main/dataset.py

Dataset classes:
  - BaseChunkDS: Base with data loading and tokenization
  - TrainValChunkDS: Diversity filtering + deterministic train/val split
  - TestChunkDS: All groups, no filtering or splitting
  - GroupedCandidateDataset: Backward-compatible wrapper for pipeline/demo
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional

import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset
from tqdm import tqdm


class BaseChunkDS(Dataset):
    """Base class for loading and tokenizing grouped candidate data."""

    def __init__(
        self,
        tokenizer,
        max_length: int,
        cls_id: int,
        pad_id: int,
        path: Optional[str] = None,
        q2cands_data: Optional[dict] = None,
        dataset_name: str = "",
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.cls_id = cls_id
        self.pad_id = pad_id
        self.groups: list = []
        self.q2cands: dict = defaultdict(list)

        if q2cands_data:
            self.q2cands = q2cands_data
        elif path:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        ex = json.loads(line)
                        if (
                            "question" in ex
                            and "label" in ex
                            and ("gen_text" in ex or "generated_full_text" in ex)
                        ):
                            self.q2cands[ex["question"]].append(ex)
                    except json.JSONDecodeError:
                        continue

    def _process_and_tokenize(self):
        """Tokenize all q2cands into groups of {ids, lab} dicts."""
        if not self.q2cands:
            self.groups = []
            return

        sep_token_str = self.tokenizer.eos_token or "\n"

        for q, cands in tqdm(
            self.q2cands.items(),
            desc="Tokenizing Groups",
            total=len(self.q2cands),
            unit="group",
        ):
            enc_grp = []
            group_meta = {"has_correct": False}

            for e in cands:
                if e["label"] == 1:
                    group_meta["has_correct"] = True

                answer_text = e.get("gen_text") or e.get("generated_full_text")
                if answer_text is None:
                    continue
                try:
                    combined = f"{q}{sep_token_str}{answer_text}"
                    ids = self.tokenizer.encode(
                        combined,
                        add_special_tokens=False,
                        truncation=True,
                        max_length=self.max_length - 1,
                    )
                    enc_grp.append(
                        {
                            "ids": torch.tensor(
                                [self.cls_id] + ids, dtype=torch.long
                            ),
                            "lab": torch.tensor(e["label"], dtype=torch.float),
                        }
                    )
                except Exception:
                    continue

            if enc_grp:
                self.groups.append({"candidates": enc_grp, "meta": group_meta})

    def __len__(self):
        return len(self.groups)

    def __getitem__(self, idx):
        return self.groups[idx]["candidates"]


class TrainValChunkDS(BaseChunkDS):
    """
    Training/Validation dataset with diversity filtering and deterministic splitting.

    Only keeps groups that have both positive (label=1) and negative (label=0)
    candidates. Splits into train/val by group using a fixed seed.
    """

    def __init__(
        self,
        tokenizer,
        max_length: int,
        cls_id: int,
        pad_id: int,
        q2cands_data: dict,
        split: str = "train",
        holdout: float = 0.2,
        dataset_name_log_prefix: str = "",
    ):
        super().__init__(
            tokenizer,
            max_length,
            cls_id,
            pad_id,
            q2cands_data=q2cands_data,
            dataset_name=f"{dataset_name_log_prefix}{split}",
        )

        filtered = {}
        if self.q2cands:
            for q, cands_list in self.q2cands.items():
                has_pos = any(e["label"] == 1 for e in cands_list)
                has_neg = any(e["label"] == 0 for e in cands_list)
                if has_pos and has_neg:
                    filtered[q] = cands_list
            self.q2cands = filtered

        if not self.q2cands:
            self.groups = []
        else:
            self._process_and_tokenize()

            random.seed(42)
            all_groups = list(self.groups)
            random.shuffle(all_groups)

            if all_groups:
                cut = int((1.0 - holdout) * len(all_groups))
                if split == "train":
                    self.groups = all_groups[:cut]
                elif split == "val":
                    self.groups = all_groups[cut:]
                else:
                    self.groups = []
            else:
                self.groups = []


class TestChunkDS(BaseChunkDS):
    """Test dataset: loads and tokenizes all groups without filtering or splitting."""

    def __init__(
        self,
        tokenizer,
        max_length: int,
        cls_id: int,
        pad_id: int,
        path: str,
        dataset_name: str = "test_dataset",
    ):
        super().__init__(
            tokenizer,
            max_length,
            cls_id,
            pad_id,
            path=path,
            dataset_name=dataset_name,
        )
        if self.q2cands:
            self._process_and_tokenize()
        else:
            self.groups = []


class GroupedCandidateDataset(Dataset):
    """
    Backward-compatible dataset wrapper for pipeline and demo usage.

    Accepts either in-memory records or a JSONL path, groups by question,
    and exposes a split() method for train/val partitioning.
    """

    def __init__(
        self,
        tokenizer,
        max_length: int,
        cls_id: int,
        pad_id: int,
        data: Optional[List[Dict[str, Any]]] = None,
        path: Optional[str] = None,
        require_diversity: bool = True,
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.cls_id = cls_id
        self.pad_id = pad_id
        self.groups: List[List[Dict[str, Any]]] = []

        q2cands: Dict[str, List[Dict]] = defaultdict(list)

        if data is not None:
            for item in data:
                q2cands[item["question"]].append(item)
        elif path is not None:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        q = item.get("question", "")
                        if "label" in item and (
                            "gen_text" in item or "generated_full_text" in item
                        ):
                            q2cands[q].append(item)
                    except json.JSONDecodeError:
                        continue

        if require_diversity:
            q2cands = {
                q: cands
                for q, cands in q2cands.items()
                if any(c["label"] == 1 for c in cands)
                and any(c["label"] == 0 for c in cands)
            }

        sep_token = tokenizer.eos_token or "\n"
        for q, cands in q2cands.items():
            group = []
            for c in cands:
                answer = c.get("gen_text") or c.get("generated_full_text", "")
                combined = f"{q}{sep_token}{answer}"
                ids = tokenizer.encode(
                    combined,
                    add_special_tokens=False,
                    truncation=True,
                    max_length=max_length - 1,
                )
                group.append(
                    {
                        "ids": torch.tensor([cls_id] + ids, dtype=torch.long),
                        "lab": torch.tensor(float(c["label"]), dtype=torch.float),
                    }
                )
            if group:
                self.groups.append(group)

    def __len__(self) -> int:
        return len(self.groups)

    def __getitem__(self, idx: int) -> List[Dict[str, Any]]:
        return self.groups[idx]

    def split(self, val_ratio: float = 0.2, seed: int = 42) -> tuple:
        """Return (train_groups, val_groups) lists."""
        rng = random.Random(seed)
        groups = list(self.groups)
        rng.shuffle(groups)

        if len(groups) <= 1:
            if not groups:
                return [], []
            candidates = groups[0]
            rng.shuffle(candidates)
            cut = max(1, int((1.0 - val_ratio) * len(candidates)))
            train_cands = candidates[:cut]
            val_cands = (
                candidates[cut:]
                if cut < len(candidates)
                else candidates[: max(1, len(candidates) // 5)]
            )
            return [train_cands], [val_cands]

        cut = max(1, int((1.0 - val_ratio) * len(groups)))
        return groups[:cut], groups[cut:]


def collate_fn(
    batch: List[Any],
    pad_id: int,
) -> tuple:
    """
    Collate groups into padded tensors.

    Returns (idsL, maskL, labL) where each is a list of tensors (one per group).
    """
    ids_list, mask_list, lab_list = [], [], []
    for grp in batch:
        if not isinstance(grp, (list, tuple)) or not grp:
            continue
        valid = [e for e in grp if isinstance(e, dict) and "ids" in e and "lab" in e]
        if not valid:
            continue
        ids = [e["ids"].cpu() for e in valid]
        labs = [e["lab"] for e in valid]
        try:
            padded = pad_sequence(ids, batch_first=True, padding_value=pad_id)
            mask = (padded != pad_id).long()
            ids_list.append(padded)
            mask_list.append(mask)
            lab_list.append(torch.stack(labs))
        except Exception:
            continue
    return ids_list, mask_list, lab_list


def setup_tokenizer(name: str = "gpt2", max_length: int = 2048):
    """Backward-compatible tokenizer setup (delegates to utils)."""
    from .utils import setup_tokenizer as _setup

    return _setup(name, max_length)
