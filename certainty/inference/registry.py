"""Head registry -- manages versioned TransEBM model artifacts."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..models.ebm_model import TransEBM


@dataclass
class HeadInfo:
    version: str
    model_path: str
    tokenizer_path: Optional[str]
    metrics: Optional[Dict]
    created_at: str


class HeadRegistry:
    """Manage versioned .pt model files in a directory."""

    def __init__(self, base_dir: str = "./model_artifacts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.base_dir / "registry.json"
        self._index: Dict[str, Dict] = self._load_index()

    def _load_index(self) -> Dict[str, Dict]:
        if self._index_path.exists():
            with open(self._index_path) as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        with open(self._index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    def register(
        self,
        version: str,
        model_path: str,
        tokenizer_path: Optional[str] = None,
        metrics: Optional[Dict] = None,
    ) -> HeadInfo:
        """Register a new model version in the registry."""
        import datetime

        dest_dir = self.base_dir / version
        dest_dir.mkdir(exist_ok=True)

        dest_model = str(dest_dir / "model.pt")
        shutil.copy2(model_path, dest_model)

        dest_tok = None
        if tokenizer_path and Path(tokenizer_path).exists():
            dest_tok = str(dest_dir / "tokenizer")
            if Path(tokenizer_path).is_dir():
                if Path(dest_tok).exists():
                    shutil.rmtree(dest_tok)
                shutil.copytree(tokenizer_path, dest_tok)
            else:
                shutil.copy2(tokenizer_path, dest_tok)

        info = {
            "version": version,
            "model_path": dest_model,
            "tokenizer_path": dest_tok,
            "metrics": metrics,
            "created_at": datetime.datetime.now().isoformat(),
        }
        self._index[version] = info
        self._save_index()
        return HeadInfo(**info)

    def load(self, version: str, device: str = "cpu") -> TransEBM:
        """Load a specific model version."""
        if version not in self._index:
            raise KeyError(f"Version '{version}' not found. Available: {list(self._index.keys())}")
        info = self._index[version]
        return TransEBM.load(info["model_path"], device=device)

    def list_versions(self) -> List[HeadInfo]:
        """List all registered versions."""
        return [HeadInfo(**v) for v in self._index.values()]

    def latest(self) -> Optional[str]:
        """Return the latest registered version string, or None."""
        if not self._index:
            return None
        return max(self._index.keys())
