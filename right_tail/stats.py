from __future__ import annotations

import math

from .models import Attempt


def check_threshold(attempts: list[Attempt], z: float) -> Attempt | None:
    """Return the best attempt if its right_tail_score is z-sigma above the mean."""
    if len(attempts) < 2:
        return None
    scores = [a.right_tail_score for a in attempts]
    mu = sum(scores) / len(scores)
    variance = sum((s - mu) ** 2 for s in scores) / (len(scores) - 1)
    sigma = math.sqrt(variance)
    if sigma == 0:
        return None
    best = max(attempts, key=lambda a: a.right_tail_score)
    z_score = (best.right_tail_score - mu) / sigma
    if z_score >= z:
        return best
    return None


def p_to_z(p: float) -> float:
    """Convert a one-tailed p-value to a z-score using scipy if available."""
    try:
        from scipy.stats import norm  # type: ignore
        return float(norm.ppf(1 - p))
    except ImportError:
        # Rough approximation for common values
        table = {0.05: 1.645, 0.025: 1.96, 0.01: 2.326, 0.005: 2.576}
        closest = min(table, key=lambda k: abs(k - p))
        return table[closest]


def summary_stats(attempts: list[Attempt]) -> dict[str, float]:
    if not attempts:
        return {}
    scores = [a.right_tail_score for a in attempts]
    mu = sum(scores) / len(scores)
    if len(scores) > 1:
        variance = sum((s - mu) ** 2 for s in scores) / (len(scores) - 1)
        sigma = math.sqrt(variance)
    else:
        sigma = 0.0
    return {"mean": mu, "std": sigma, "min": min(scores), "max": max(scores), "n": len(scores)}
