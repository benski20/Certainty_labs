"""Data generation pipeline: sample -> label -> synthesize negatives -> save."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional

import jsonlines

from .sampler import LLMSampler
from .labeler import SymbolicLabeler, LabelConfig
from .negatives import NegativeSynthesizer


@dataclass
class GeneratorConfig:
    n_samples: int = 500
    min_positives: int = 100
    min_negatives: int = 200
    positive_threshold: float = 0.01
    negative_threshold: float = 0.50
    temperature: float = 0.9
    max_new_tokens: int = 256


class DataGenerator:
    """Orchestrates the full data generation pipeline."""

    def __init__(
        self,
        energy_fn: Callable[[dict], float],
        sampler: LLMSampler,
        config: Optional[GeneratorConfig] = None,
    ):
        self.energy_fn = energy_fn
        self.sampler = sampler
        self.config = config or GeneratorConfig()
        label_cfg = LabelConfig(
            positive_threshold=self.config.positive_threshold,
            negative_threshold=self.config.negative_threshold,
        )
        self.labeler = SymbolicLabeler(energy_fn, label_cfg)
        self.synthesizer = NegativeSynthesizer(energy_fn)

    def generate(self, prompt: str, output_dir: str) -> Dict[str, Any]:
        """
        Full pipeline: sample -> label -> synthesize negatives if needed -> save.
        Returns stats dict.
        """
        os.makedirs(output_dir, exist_ok=True)

        print(f"Sampling {self.config.n_samples} candidates...")
        raw_outputs = self.sampler.sample(
            prompt, n=self.config.n_samples, temperature=self.config.temperature
        )

        print("Labeling with symbolic energy function...")
        labeled = self.labeler.label_all(raw_outputs)
        positives = [x for x in labeled if x["label"] == "positive"]
        negatives = [x for x in labeled if x["label"] == "negative"]

        if len(negatives) < self.config.min_negatives:
            deficit = self.config.min_negatives - len(negatives)
            print(f"Only {len(negatives)} natural negatives. Synthesizing {deficit} more...")
            if positives:
                synthetic = self.synthesizer.synthesize(positives, n_needed=deficit)
                negatives.extend(synthetic)

        pos_path = os.path.join(output_dir, "positives.jsonl")
        neg_path = os.path.join(output_dir, "negatives.jsonl")
        self._save(positives, pos_path)
        self._save(negatives, neg_path)

        natural_neg = len([x for x in labeled if x["label"] == "negative"])
        stats = {
            "n_positives": len(positives),
            "n_negatives": len(negatives),
            "n_total_sampled": len(labeled),
            "natural_neg_rate": natural_neg / max(len(labeled), 1),
        }
        print(f"Data generation complete: {stats}")
        return stats

    def generate_eorm_format(
        self, prompt: str, output_path: str
    ) -> Dict[str, Any]:
        """
        Generate data in EORM-compatible JSONL format:
        {"question": ..., "label": 0|1, "gen_text": ...}
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        print(f"Sampling {self.config.n_samples} candidates...")
        raw_outputs = self.sampler.sample(
            prompt, n=self.config.n_samples, temperature=self.config.temperature
        )

        print("Labeling with symbolic energy function...")
        labeled = self.labeler.label_all(raw_outputs)

        positives = [x for x in labeled if x["label"] == "positive"]
        negatives = [x for x in labeled if x["label"] == "negative"]

        if len(negatives) < self.config.min_negatives and positives:
            deficit = self.config.min_negatives - len(negatives)
            print(f"Synthesizing {deficit} additional negatives...")
            synthetic = self.synthesizer.synthesize(positives, n_needed=deficit)
            negatives.extend(synthetic)

        # Assign items to groups of ~8 candidates to create meaningful train/val groups.
        # EORM expects groups with mixed pos/neg labels for Bradley-Terry loss.
        group_size = 8
        all_items = [(item, 1) for item in positives] + [(item, 0) for item in negatives]
        import random as _rng
        _rng.shuffle(all_items)

        eorm_records = []
        for i, (item, label) in enumerate(all_items):
            group_id = i // group_size
            eorm_records.append({
                "question": f"{prompt} [group_{group_id}]",
                "label": label,
                "gen_text": item["text"],
            })

        with jsonlines.open(output_path, mode="w") as writer:
            writer.write_all(eorm_records)

        stats = {
            "n_positives": len(positives),
            "n_negatives": len(negatives),
            "output_path": output_path,
        }
        print(f"EORM-format data saved: {stats}")
        return stats

    @staticmethod
    def _save(data: List[Dict], path: str) -> None:
        with jsonlines.open(path, mode="w") as writer:
            writer.write_all(data)
