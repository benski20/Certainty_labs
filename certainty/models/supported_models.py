"""
Supported Hugging Face model families for tokenizer compatibility.

Use the same tokenizer as your LLM (Qwen or Llama) when training the TransEBM
so that tokenization at inference matches. Any HuggingFace model ID that
provides a tokenizer via AutoTokenizer.from_pretrained(...) is supported;
this module documents and normalizes recommended Qwen and Llama IDs.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Recommended tokenizer/model IDs for compatibility with Hugging Face Qwen and Llama.
# Use these as tokenizer_name when training so the EBM matches your candidate-generating LLM.
SUPPORTED_QWEN_IDS: List[str] = [
    "Qwen/Qwen2-0.5B-Instruct",
    "Qwen/Qwen2-1.5B-Instruct",
    "Qwen/Qwen2-7B-Instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
]

SUPPORTED_LLAMA_IDS: List[str] = [
    "meta-llama/Llama-3.2-1B",
    "meta-llama/Llama-3.2-3B",
    "meta-llama/Llama-3.1-8B",
    "meta-llama/Llama-3.1-70B",
    "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
]

# Short aliases -> full HuggingFace ID (for API/docs convenience)
TOKENIZER_ALIASES: Dict[str, str] = {
    "gpt2": "gpt2",
    "qwen2-0.5b": "Qwen/Qwen2-0.5B-Instruct",
    "qwen2-1.5b": "Qwen/Qwen2-1.5B-Instruct",
    "qwen2-7b": "Qwen/Qwen2-7B-Instruct",
    "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "qwen2.5-1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "qwen2.5-3b": "Qwen/Qwen2.5-3B-Instruct",
    "qwen2.5-7b": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2.5-14b": "Qwen/Qwen2.5-14B-Instruct",
    "qwen2.5-32b": "Qwen/Qwen2.5-32B-Instruct",
    "qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
    "llama-3.2-1b": "meta-llama/Llama-3.2-1B-Instruct",
    "llama-3.2-3b": "meta-llama/Llama-3.2-3B-Instruct",
    "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
    "llama-3.1-70b": "meta-llama/Llama-3.1-70B-Instruct",
}


def resolve_tokenizer_name(name_or_alias: str) -> str:
    """
    Resolve a short alias or full HuggingFace ID to the tokenizer model ID.
    If the input is already a full ID (contains '/'), return as-is; else look up alias.
    """
    if not name_or_alias or not name_or_alias.strip():
        return "gpt2"
    s = name_or_alias.strip()
    if "/" in s:
        return s
    return TOKENIZER_ALIASES.get(s.lower(), s)


def list_supported_tokenizers() -> List[str]:
    """Return all supported tokenizer identifiers (aliases + representative Qwen/Llama IDs)."""
    aliases = [k for k in TOKENIZER_ALIASES if k != "gpt2"]
    return ["gpt2"] + aliases
