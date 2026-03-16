"""Negative synthesis: programmatic corruption strategies to generate constraint violations."""

from __future__ import annotations

import copy
import json
import random
from typing import Callable, Dict, List, Any, Optional


class NegativeSynthesizer:
    """
    Generates constraint-violating examples from valid ones.
    Five strategies that inspect data structure dynamically.
    """

    def __init__(self, energy_fn: Callable[[dict], float]):
        self.energy_fn = energy_fn
        self.strategies = [
            self.corrupt_sum,
            self.corrupt_sign,
            self.corrupt_concentration,
            self.corrupt_count,
            self.corrupt_json,
        ]

    def synthesize(
        self,
        positives: List[Dict[str, Any]],
        n_needed: int,
    ) -> List[Dict[str, Any]]:
        """Generate up to *n_needed* synthetic negatives from positive examples."""
        negatives: List[Dict[str, Any]] = []
        attempts = 0
        max_attempts = n_needed * 10

        while len(negatives) < n_needed and attempts < max_attempts:
            source = random.choice(positives)
            strategy = random.choice(self.strategies)
            corrupted = strategy(source)
            if corrupted is not None:
                negatives.append(corrupted)
            attempts += 1

        return negatives

    def corrupt_sum(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Multiply one numeric value by 1.5 to break sum constraints."""
        parsed = self._get_parsed(example)
        if parsed is None:
            return None
        corrupted = copy.deepcopy(parsed)
        numeric_paths = self._find_numeric_collections(corrupted)
        if not numeric_paths:
            return None

        collection = random.choice(numeric_paths)
        if isinstance(collection, dict):
            key = random.choice(list(collection.keys()))
            collection[key] = collection[key] * 1.5
        elif isinstance(collection, list):
            idx = random.randint(0, len(collection) - 1)
            collection[idx] = collection[idx] * 1.5

        text = json.dumps(corrupted)
        energy = self.energy_fn(corrupted)
        if energy > 0.1:
            return {"text": text, "parsed": corrupted, "energy": energy,
                    "label": "negative", "parse_error": False, "synthetic": True}
        return None

    def corrupt_sign(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Negate one numeric value to create range violations."""
        parsed = self._get_parsed(example)
        if parsed is None:
            return None
        corrupted = copy.deepcopy(parsed)
        numeric_paths = self._find_numeric_collections(corrupted)
        if not numeric_paths:
            return None

        collection = random.choice(numeric_paths)
        if isinstance(collection, dict):
            key = random.choice(list(collection.keys()))
            collection[key] = -abs(collection[key])
        elif isinstance(collection, list):
            idx = random.randint(0, len(collection) - 1)
            collection[idx] = -abs(collection[idx])

        text = json.dumps(corrupted)
        energy = self.energy_fn(corrupted)
        if energy > 0.1:
            return {"text": text, "parsed": corrupted, "energy": energy,
                    "label": "negative", "parse_error": False, "synthetic": True}
        return None

    def corrupt_concentration(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Set one value to 0.95 to exceed per-item limits."""
        parsed = self._get_parsed(example)
        if parsed is None:
            return None
        corrupted = copy.deepcopy(parsed)
        numeric_paths = self._find_numeric_collections(corrupted)
        if not numeric_paths:
            return None

        collection = random.choice(numeric_paths)
        if isinstance(collection, dict):
            key = random.choice(list(collection.keys()))
            collection[key] = 0.95
        elif isinstance(collection, list):
            idx = random.randint(0, len(collection) - 1)
            collection[idx] = 0.95

        text = json.dumps(corrupted)
        energy = self.energy_fn(corrupted)
        if energy > 0.1:
            return {"text": text, "parsed": corrupted, "energy": energy,
                    "label": "negative", "parse_error": False, "synthetic": True}
        return None

    def corrupt_count(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Duplicate entries to exceed count limits."""
        parsed = self._get_parsed(example)
        if parsed is None:
            return None
        corrupted = copy.deepcopy(parsed)

        for key, val in corrupted.items():
            if isinstance(val, dict) and len(val) >= 2:
                extra_keys = [f"EXTRA_{i}" for i in range(3)]
                for ek in extra_keys:
                    corrupted[key][ek] = random.uniform(0.01, 0.5)
                text = json.dumps(corrupted)
                energy = self.energy_fn(corrupted)
                if energy > 0.1:
                    return {"text": text, "parsed": corrupted, "energy": energy,
                            "label": "negative", "parse_error": False, "synthetic": True}
            elif isinstance(val, list) and len(val) >= 2:
                corrupted[key] = val + val[:3]
                text = json.dumps(corrupted)
                energy = self.energy_fn(corrupted)
                if energy > 0.1:
                    return {"text": text, "parsed": corrupted, "energy": energy,
                            "label": "negative", "parse_error": False, "synthetic": True}
        return None

    def corrupt_json(self, example: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Produce invalid JSON strings that fail parsing (worst energy)."""
        text = example.get("text", "{}")
        corruptions = [
            text[:-1],  # remove closing brace
            text.replace(":", "=", 1),  # swap colon for equals
            text + "}}",  # extra braces
            "{" + text,  # double open
        ]
        corrupted_text = random.choice(corruptions)
        return {
            "text": corrupted_text,
            "parsed": None,
            "energy": float("inf"),
            "label": "negative",
            "parse_error": True,
            "synthetic": True,
        }

    @staticmethod
    def _get_parsed(example: Dict[str, Any]) -> Optional[dict]:
        parsed = example.get("parsed")
        if isinstance(parsed, dict):
            return parsed
        try:
            return json.loads(example.get("text", ""))
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _find_numeric_collections(d: dict) -> list:
        """Find dicts/lists containing numeric values."""
        results = []
        for val in d.values():
            if isinstance(val, dict):
                if any(isinstance(v, (int, float)) for v in val.values()):
                    results.append(val)
            elif isinstance(val, list):
                if any(isinstance(v, (int, float)) for v in val):
                    results.append(val)
        return results
