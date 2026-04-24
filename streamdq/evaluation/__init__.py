"""
StreamDQ Evaluation Module.

Components:
- complementarity: Conditional Coverage (CC) and Complementarity Index (CI).
  Measures P(StreamDQ catches | Existing misses) via McNemar's test with bootstrap CI.
"""
from __future__ import annotations

from streamdq.evaluation.complementarity import (
    ComplementarityResult,
    run_complementarity_evaluation,
    run_multi_framework_evaluation,
)

__all__ = [
    "ComplementarityResult",
    "run_complementarity_evaluation",
    "run_multi_framework_evaluation",
]
