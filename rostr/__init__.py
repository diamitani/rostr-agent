# ROSTR Core — The Billion-Dollar Agent Operating System
# ============================================================
# ROSTR: Runtime, Orchestration, State, Tools, Reference
# A Unified Architecture for Production-Grade Multi-Agent Systems
# with Phase-Aware Orchestration and Persistent Knowledge Compounding
#
# Author: Patrick Diamitani
# License: MIT
# Version: 1.0.0
# Paper: arXiv:2604.XXXXX

"""
ROSTR Core — the unified agent operating system.

Four pillars, one framework:
  1. PAL  — Prompt Abstraction Layer (LLM Compiler)
  2. RAG  — Retrieval-Augmented Generation Dynamic Acquisition Layer (Knowledge Engine)
  3. NPAO — Navigate, Prioritize, Allocate, Orchestrate (Decision Engine)
  4. HUB  — Rostr Hub (Persistent Reference Architecture)
"""

__version__ = "1.0.0"
__author__ = "Patrick Diamitani"
__license__ = "MIT"

from rostr.pal import PALCompiler, Intent, AgentManifest
from rostr.ragdal import RAGDAL, SourceTier, KnowledgeEntry
from rostr.npao import NPAO, PhaseType, PriorityScore, OrchestrationPattern
from rostr.hub import RostrHub, Namespace, StateLevel, AgentRegistration

__all__ = [
    # PAL
    "PALCompiler", "Intent", "AgentManifest",
    # RAG DAL
    "RAGDAL", "SourceTier", "KnowledgeEntry",
    # NPAO
    "NPAO", "PhaseType", "PriorityScore", "OrchestrationPattern",
    # Hub
    "RostrHub", "Namespace", "StateLevel", "AgentRegistration",
]
