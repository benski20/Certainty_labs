"""Symbolic labeling: run compiled energy function on raw outputs to classify positive/negative."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Optional


@dataclass
class LabelConfig:
    positive_threshold: float = 0.01
    negative_threshold: float = 0.50


class SymbolicLabeler:
    """Labels raw LLM outputs using a compiled energy function."""

    def __init__(
        self,
        energy_fn: Callable[[dict], float],
        config: Optional[LabelConfig] = None,
    ):
        self.energy_fn = energy_fn
        self.config = config or LabelConfig()

    def label_one(self, raw_output: str) -> Dict[str, Any]:
        """Parse and label a single output string."""
        try:
            parsed = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return {
                "text": raw_output,
                "parsed": None,
                "energy": float("inf"),
                "label": "negative",
                "parse_error": True,
            }

        energy = self.energy_fn(parsed)
        if energy <= self.config.positive_threshold:
            label = "positive"
        elif energy >= self.config.negative_threshold:
            label = "negative"
        else:
            label = "ambiguous"

        return {
            "text": raw_output,
            "parsed": parsed,
            "energy": energy,
            "label": label,
            "parse_error": False,
        }

    def label_all(self, raw_outputs: List[str]) -> List[Dict[str, Any]]:
        """Label a batch of outputs."""
        return [self.label_one(out) for out in raw_outputs]
