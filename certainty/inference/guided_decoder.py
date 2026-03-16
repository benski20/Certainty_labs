"""
Guided decoder -- V2 stub.

The guided decoding approach uses Langevin dynamics (from IRED, Du et al. 2024)
to bias logits during autoregressive generation. At each decoding step:
  1. Forward pass -> logits + hidden_states
  2. EBMHead(hidden_states) -> energy
  3. Compute dE/d(hidden) via autograd
  4. Project gradient to logit space via lm_head.weight
  5. biased_logits = logits + (-scale * gradient_projection)
  6. Sample next token from biased distribution

This requires open-weight model access (Llama 3, Mistral).
Not implemented in V1 -- reranking is the primary inference mode.
"""

from __future__ import annotations

from typing import Optional


class GuidedDecoder:
    """Guided decoding via energy-gradient logit biasing. V2 only."""

    def __init__(
        self,
        model_name: str = "meta-llama/Meta-Llama-3-8B",
        head_path: Optional[str] = None,
        guidance_scale: float = 1.0,
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.head_path = head_path
        self.guidance_scale = guidance_scale
        self.device = device

    def guided_generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text with energy-guided logit biasing.

        Raises NotImplementedError -- this is a V2 feature.
        Reference: IRED Algorithm 2 (Du, Mao, Tenenbaum 2024)
        """
        raise NotImplementedError(
            "Guided decoding is a V2 feature. Use ConstraintReranker for V1 inference. "
            "See: https://github.com/yilundu/ired_code_release for the reference implementation."
        )
