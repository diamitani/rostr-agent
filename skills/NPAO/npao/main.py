#!/usr/bin/env python3
"""
NPAO — Nuanced Prompt Abstraction Orchestrator

Extends PAL with:
- Multi-domain confidence scoring
- Ambiguity detection and resolution
- Fallback routing with priorities
- Routing trace for observability
- Multi-intent task splitting

Usage:
    npao = NPAO()
    manifest = npao.orchestrate("review my marketing copy and fix the grammar")
    print(json.dumps(manifest, indent=2))
"""

import json
import sys
import re
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import logging

try:
    from confidence_scorer import ConfidenceScorer
except ImportError:
    # Fallback if running from different directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AmbiguityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NPAO:
    """Nuanced Prompt Abstraction Orchestrator."""

    DOMAINS = ["code", "design", "content", "sales", "ops", "idea", "debug", "deploy"]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.scorer = ConfidenceScorer(verbose=verbose)

    def orchestrate(self, request: str, pal_manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Full orchestration pipeline.

        Args:
            request: User request
            pal_manifest: Optional PAL output to enhance

        Returns:
            Enhanced manifest with confidence, ambiguity, fallback routing
        """
        if self.verbose:
            logger.info(f"[NPAO] Orchestrating: {request[:50]}...")

        # Stage 1: Score all domains
        if self.verbose:
            logger.info("[NPAO] Stage 1: Scoring all domains...")
        scores = self.scorer.score_request(request, self.DOMAINS)

        # Stage 2: Rank domains
        if self.verbose:
            logger.info("[NPAO] Stage 2: Ranking domains...")
        ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

        # Stage 3: Detect multi-intent
        if self.verbose:
            logger.info("[NPAO] Stage 3: Detecting multi-intent...")
        multi_intent = self.scorer.detect_multi_intent(request)

        # Stage 4: Compute ambiguity
        if self.verbose:
            logger.info("[NPAO] Stage 4: Computing ambiguity...")
        entropy = self.scorer.compute_entropy(scores)
        ambiguity = self.scorer.get_ambiguity_level(entropy)

        # Stage 5: Build manifest
        if self.verbose:
            logger.info("[NPAO] Stage 5: Building enhanced manifest...")
        manifest = self._build_manifest(
            request,
            ranked,
            scores,
            entropy,
            ambiguity,
            multi_intent,
            pal_manifest,
        )

        if self.verbose:
            logger.info(f"[NPAO] Complete. Primary={manifest['primary_domain']}, Confidence={manifest['confidence_score']:.2f}")

        return manifest

    def _build_manifest(
        self,
        request: str,
        ranked: List[Tuple[str, Tuple[float, str]]],
        scores: Dict[str, Tuple[float, str]],
        entropy: float,
        ambiguity: str,
        multi_intent: List[Tuple[str, str]],
        pal_manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build enhanced AgentManifest."""
        primary_domain = ranked[0][0] if ranked else "idea"
        primary_confidence = ranked[0][1][0] if ranked else 0.0

        # Secondary domains
        secondary = []
        for domain, (conf, reason) in ranked[1:]:
            if conf > 0.3:  # Only include if non-trivial confidence
                secondary.append({"domain": domain, "confidence": conf, "reason": reason})

        # Routing trace
        matches = self._extract_matches(request)
        trace = {
            "matches": matches,
            "resolution": self._generate_resolution(ranked),
            "input_entropy": entropy,
        }

        # Fallback routes
        primary_model = "claude-opus" if primary_confidence > 0.7 else "claude-sonnet"
        fallbacks = self.scorer.score_fallback_priority(primary_model, primary_domain, primary_confidence)

        # Sub-tasks if multi-intent
        sub_tasks = []
        if multi_intent:
            sub_tasks = self._score_sub_tasks(multi_intent)

        # Recommendation
        recommendation = self._generate_recommendation(
            primary_domain, primary_confidence, ambiguity, multi_intent
        )

        # Inherit from PAL if provided
        pal_tools = []
        if pal_manifest:
            pal_tools = pal_manifest.get("tools", [])

        manifest = {
            "primary_domain": primary_domain,
            "secondary_domains": secondary,
            "confidence_score": primary_confidence,
            "ambiguity_level": ambiguity,
            "routing_trace": trace,
            "fallback_routes": fallbacks,
            "sub_tasks": sub_tasks,
            "recommendation": recommendation,
            "metadata": {
                "original_request": request,
                "scored_domains": {domain: conf for domain, (conf, _) in scores.items()},
                "pal_enriched": pal_manifest is not None,
            },
        }

        return manifest

    def _extract_matches(self, request: str) -> List[Dict[str, Any]]:
        """Extract keyword matches from request."""
        matches = []
        text = request.lower()

        # Content markers
        content_patterns = [
            (r"grammar|spelling|punctuation|tone", ["content"]),
            (r"marketing|copy|messaging", ["content", "sales"]),
            (r"blog|article|post|documentation", ["content"]),
        ]

        code_patterns = [
            (r"code|function|class|debug|refactor", ["code"]),
            (r"api|endpoint|database|architecture", ["code"]),
        ]

        design_patterns = [
            (r"ui|ux|design|layout|component|responsive", ["design"]),
            (r"css|html|style|visual|brand", ["design"]),
        ]

        sales_patterns = [
            (r"sales|prospect|outreach|lead|deal", ["sales"]),
            (r"atlas|eor|hiring|international", ["sales"]),
        ]

        debug_patterns = [
            (r"debug|bug|broken|crash|error|fail", ["debug"]),
            (r"troubleshoot|investigate|root cause", ["debug"]),
        ]

        deploy_patterns = [
            (r"deploy|ship|push|merge|pr|release", ["deploy"]),
            (r"staging|production|launch|rollout", ["deploy"]),
        ]

        all_patterns = (
            content_patterns
            + code_patterns
            + design_patterns
            + sales_patterns
            + debug_patterns
            + deploy_patterns
        )

        for pattern, domains in all_patterns:
            if re.search(pattern, text):
                matches.append(
                    {
                        "pattern": pattern[:30],
                        "domains": domains,
                        "score": 0.8,
                    }
                )

        return matches[:10]  # Limit to 10

    def _generate_resolution(self, ranked: List[Tuple[str, Tuple[float, str]]]) -> str:
        """Generate explanation of domain resolution."""
        if not ranked:
            return "No domains scored; defaulting to 'idea'"

        primary = ranked[0][0]
        primary_score = ranked[0][1][0]

        if len(ranked) > 1:
            secondary_score = ranked[1][1][0]
            gap = primary_score - secondary_score

            if gap > 0.3:
                return f"Strong winner: '{primary}' ({primary_score:.2f}) significantly ahead of '{ranked[1][0]}' ({secondary_score:.2f})"
            elif gap > 0.1:
                return f"Chosen '{primary}' ({primary_score:.2f}) by margin over '{ranked[1][0]}' ({secondary_score:.2f})"
            else:
                return f"Ambiguous choice: '{primary}' ({primary_score:.2f}) barely ahead; consider multi-intent handling"

        return f"Only match: '{primary}' ({primary_score:.2f})"

    def _score_sub_tasks(self, multi_intent: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Score each sub-task independently."""
        sub_tasks = []

        for task, _ in multi_intent:
            scores = self.scorer.score_request(task, self.DOMAINS)
            ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

            if ranked:
                domain = ranked[0][0]
                confidence = ranked[0][1][0]
                sub_tasks.append(
                    {
                        "task": task,
                        "domain": domain,
                        "confidence": confidence,
                    }
                )

        return sub_tasks

    def _generate_recommendation(
        self, domain: str, confidence: float, ambiguity: str, multi_intent: List[Tuple[str, str]]
    ) -> str:
        """Generate high-level routing recommendation."""
        parts = []

        if ambiguity == "high":
            parts.append("HIGH AMBIGUITY: Consider splitting into independent sub-agents")
        elif ambiguity == "medium":
            parts.append(f"MEDIUM AMBIGUITY: Route to {domain.upper()} with fallback enabled")
        else:
            parts.append(f"CLEAR: Route to {domain.upper()}")

        if confidence < 0.6:
            parts.append(f"Low confidence ({confidence:.2f}); fallback recommended")

        if multi_intent and len(multi_intent) > 1:
            parts.append(f"Multi-intent detected ({len(multi_intent)} tasks); handle sequentially")

        return "; ".join(parts)


def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python main.py '<request>'")
        print("Example: python main.py 'review my marketing copy and fix the grammar'")
        sys.exit(1)

    request = sys.argv[1]
    npao = NPAO(verbose=True)
    manifest = npao.orchestrate(request)
    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
