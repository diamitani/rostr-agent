"""ROSTR System One decision layer.

Jev (or a local/adapter stand-in) answers typed questions over unstructured
state. Specialists still generate strings. This package is the decision
hot path for PAL, NPAO, allocation, and approval gates.
"""

from .client import SystemOneClient, evaluate
from .pal import compile_pal, PALCompilation
from .npao import score_npao, NPAOResult

__all__ = [
    "SystemOneClient",
    "evaluate",
    "compile_pal",
    "PALCompilation",
    "score_npao",
    "NPAOResult",
]
