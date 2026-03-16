"""
Bradley-Terry loss for energy-based ranking.

Matches the real EORM implementation:
https://github.com/ericjiang18/EnergyORM/blob/main/utils.py

For every (positive, negative) pair within a group:
  L = mean( softplus(E_pos - E_neg) )

Lower energy = better, so we want E_pos < E_neg.
When E_pos < E_neg, the difference is negative and softplus is small.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from typing import Optional


def bradley_terry_loss(
    energies: torch.Tensor,
    labels: torch.Tensor,
) -> Optional[torch.Tensor]:
    """
    Compute Bradley-Terry pairwise loss over all (pos, neg) combinations.

    energies : (N,) energy scores for candidates in one group
    labels   : (N,) 1 = correct/positive, 0 = incorrect/negative

    Returns scalar loss or None if the group lacks both positive and negative examples.
    """
    pos_indices = torch.where(labels == 1)[0]
    neg_indices = torch.where(labels == 0)[0]

    if len(pos_indices) == 0 or len(neg_indices) == 0:
        return None

    pos_scores = energies[pos_indices]
    neg_scores = energies[neg_indices]

    # (|P|, |N|) matrix of E_pos - E_neg
    energy_diffs = pos_scores.unsqueeze(1) - neg_scores.unsqueeze(0)
    loss_matrix = F.softplus(energy_diffs)
    return loss_matrix.mean()
