"""LLM sampling backends: OpenAI, Mock (synthetic), File-based, and Hugging Face Inference."""

from __future__ import annotations

import abc
import csv
import io
import json
import random
from pathlib import Path
from typing import List, Optional


class LLMSampler(abc.ABC):
    """Base class for all samplers."""

    @abc.abstractmethod
    def sample(self, prompt: str, n: int = 10, temperature: float = 0.9) -> List[str]:
        """Return *n* raw text outputs for *prompt*."""


class OpenAISampler(LLMSampler):
    """Calls OpenAI (or configurable model / base URL) to generate candidate outputs."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        import openai

        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**kwargs) if kwargs else openai.OpenAI()
        self.model = model

    def sample(self, prompt: str, n: int = 10, temperature: float = 0.9) -> List[str]:
        results: List[str] = []
        for _ in range(n):
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=512,
            )
            results.append(resp.choices[0].message.content or "")
        return results


class HuggingFaceInferenceSampler(LLMSampler):
    """Generate candidates using Hugging Face Inference API (Qwen, Llama, etc.)."""

    def __init__(
        self,
        model_id: str,
        token: Optional[str] = None,
        api_url: str = "https://api-inference.huggingface.co",
    ):
        self.model_id = model_id
        self.token = token or ""
        self.api_url = api_url.rstrip("/")

    def sample(self, prompt: str, n: int = 10, temperature: float = 0.9) -> List[str]:
        import urllib.request
        import urllib.error

        url = f"{self.api_url}/models/{self.model_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        results: List[str] = []
        for _ in range(n):
            body = json.dumps({
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "temperature": temperature,
                    "return_full_text": False,
                },
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    out = json.loads(resp.read().decode("utf-8"))
                    if isinstance(out, list) and len(out) > 0 and "generated_text" in out[0]:
                        results.append(out[0]["generated_text"].strip())
                    elif isinstance(out, dict) and "generated_text" in out:
                        results.append(out["generated_text"].strip())
                    else:
                        results.append("")
            except urllib.error.HTTPError:
                results.append("")
        return results


class MockSampler(LLMSampler):
    """Generates synthetic JSON outputs for testing without any API calls."""

    def __init__(self, domain: str = "portfolio"):
        self.domain = domain

    def sample(self, prompt: str, n: int = 10, temperature: float = 0.9) -> List[str]:
        if self.domain == "portfolio":
            return [self._gen_portfolio() for _ in range(n)]
        if self.domain == "dosage":
            return [self._gen_dosage() for _ in range(n)]
        return [self._gen_generic() for _ in range(n)]

    def _gen_portfolio(self) -> str:
        tickers = ["AAPL", "GOOG", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM"]
        k = random.randint(2, 6)
        selected = random.sample(tickers, k)

        if random.random() < 0.6:
            raw = [random.random() for _ in selected]
            total = sum(raw)
            weights = {t: round(w / total, 4) for t, w in zip(selected, raw)}
        else:
            weights = {t: round(random.uniform(-0.1, 0.95), 4) for t in selected}

        return json.dumps({"weights": weights})

    def _gen_dosage(self) -> str:
        age = random.choice([5, 8, 10, 15, 25, 40, 60])
        routes = ["oral", "IV", "IM", "subcutaneous", "topical", "rectal"]
        route = random.choice(routes)
        if age < 12:
            dose = random.uniform(50, 400)
        else:
            dose = random.uniform(100, 1200)
        return json.dumps({
            "patient_age_years": age,
            "dosage_mg": round(dose, 1),
            "route": route,
        })

    def _gen_generic(self) -> str:
        return json.dumps({"value": round(random.gauss(50, 20), 2)})


class FileSampler(LLMSampler):
    """Loads candidate outputs from user-provided files (JSONL, CSV, or JSON)."""

    def __init__(self, path: str | Path, text_field: Optional[str] = None):
        self.path = Path(path)
        self.text_field = text_field
        self._data: Optional[List[str]] = None

    def _load(self) -> List[str]:
        if self._data is not None:
            return self._data

        suffix = self.path.suffix.lower()
        if suffix == ".jsonl":
            self._data = self._load_jsonl()
        elif suffix == ".csv":
            self._data = self._load_csv()
        elif suffix == ".json":
            self._data = self._load_json()
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .jsonl, .csv, or .json")
        return self._data

    def _load_jsonl(self) -> List[str]:
        items: List[str] = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if self.text_field and self.text_field in obj:
                    items.append(str(obj[self.text_field]))
                elif isinstance(obj, dict):
                    items.append(json.dumps(obj))
                else:
                    items.append(str(obj))
        return items

    def _load_csv(self) -> List[str]:
        items: List[str] = []
        with open(self.path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.text_field and self.text_field in row:
                    items.append(row[self.text_field])
                else:
                    items.append(json.dumps(dict(row)))
        return items

    def _load_json(self) -> List[str]:
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [json.dumps(item) if isinstance(item, dict) else str(item) for item in data]
        return [json.dumps(data)]

    def sample(self, prompt: str, n: int = 10, temperature: float = 0.9) -> List[str]:
        all_data = self._load()
        if n >= len(all_data):
            return list(all_data)
        return random.sample(all_data, n)


def sampler_from_bytes(content: bytes, filename: str, text_field: Optional[str] = None) -> List[str]:
    """Parse uploaded file bytes into a list of text candidates (for Streamlit uploads)."""
    suffix = Path(filename).suffix.lower()
    text = content.decode("utf-8")

    if suffix == ".jsonl":
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if text_field and text_field in obj:
                items.append(str(obj[text_field]))
            elif isinstance(obj, dict):
                items.append(json.dumps(obj))
            else:
                items.append(str(obj))
        return items

    if suffix == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        items = []
        for row in reader:
            if text_field and text_field in row:
                items.append(row[text_field])
            else:
                items.append(json.dumps(dict(row)))
        return items

    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, list):
            return [json.dumps(item) if isinstance(item, dict) else str(item) for item in data]
        return [json.dumps(data)]

    raise ValueError(f"Unsupported format: {suffix}")
