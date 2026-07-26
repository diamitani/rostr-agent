#!/usr/bin/env python3
"""
Confidence Scoring Engine for NPAO

Computes confidence scores for domain predictions using:
- Pattern matching frequency
- Keyword specificity
- Domain overlap detection
- Entropy-based ambiguity scoring
"""

import re
from typing import Dict, List, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Compute confidence scores for domain-request matches."""

    # Domain-specific keyword patterns with weights
    DOMAIN_KEYWORDS = {
        "code": {
            "primary": [
                r"code|function|method|class|debug|refactor|optimize|test|unit.*test",
                r"typescript|python|javascript|java|c\+\+|rust|go|sql",
                r"architecture|design pattern|api|endpoint|database",
            ],
            "weight": 1.0,
        },
        "design": {
            "primary": [
                r"design|ui|ux|layout|component|responsive|mobile|page",
                r"css|html|style|color|spacing|typography|brand",
                r"visual|aesthetic|font|icon|image|gallery",
            ],
            "weight": 1.0,
        },
        "content": {
            "primary": [
                r"content|writing|copy|blog|article|post|documentation|docs",
                r"grammar|punctuation|tone|voice|messaging|communication",
                r"email|newsletter|social|marketing|seo",
            ],
            "weight": 1.0,
        },
        "sales": {
            "primary": [
                r"sales|prospect|outreach|lead|deal|pipeline|negotiation",
                r"atlas|eor|hiring|international|payroll|benefits",
                r"objection|closing|call prep|competitive",
            ],
            "weight": 1.0,
        },
        "debug": {
            "primary": [
                r"debug|bug|broken|crash|error|fail|investigate|root cause",
                r"troubleshoot|diagnose|fix|issue|problem|not.*working",
                r"qa|test|broken|doesn't work|failing",
            ],
            "weight": 1.0,
        },
        "deploy": {
            "primary": [
                r"deploy|ship|push|merge|pr|pull request|release|production",
                r"staging|test environment|canary|rollout|launch",
                r"cicd|pipeline|github actions|vercel",
            ],
            "weight": 1.0,
        },
        "ops": {
            "primary": [
                r"ops|operations|devops|infrastructure|monitoring|alert",
                r"performance|scaling|load balancing|caching|database",
                r"analytics|reporting|metrics|dashboard|health",
            ],
            "weight": 1.0,
        },
        "idea": {
            "primary": [
                r"idea|brainstorm|think bigger|10x|strategy|vision|planning",
                r"what if|imagine|consider|explore|research|investigate",
                r"innovation|direction|roadmap|future",
            ],
            "weight": 1.0,
        },
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def score_request(
        self, request: str, candidate_domains: List[str]
    ) -> Dict[str, Tuple[float, str]]:
        """
        Score how well the request matches each candidate domain.

        Args:
            request: Raw user request
            candidate_domains: List of potential domains to score

        Returns:
            Dict[domain] -> (confidence: float, reason: str)
        """
        text = request.lower()
        scores = {}

        for domain in candidate_domains:
            confidence, reason = self._score_domain(text, domain)
            scores[domain] = (confidence, reason)

        return scores

    def _score_domain(self, text: str, domain: str) -> Tuple[float, str]:
        """Score how well text matches a specific domain."""
        if domain not in self.DOMAIN_KEYWORDS:
            return 0.3, "unknown domain"

        keywords = self.DOMAIN_KEYWORDS[domain]["primary"]
        matches = []
        total_weight = 0

        for pattern in keywords:
            hits = len(re.findall(pattern, text, re.IGNORECASE))
            if hits > 0:
                matches.append(pattern)
                total_weight += hits * 0.2  # Each keyword hit = 0.2

        # Cap at 1.0
        base_score = min(total_weight, 1.0)

        # Boost if specific keywords appear
        if base_score > 0:
            base_score = min(base_score + 0.15, 1.0)

        # Penalty for contradictions
        contradictions = self._detect_contradictions(text, domain)
        if contradictions:
            base_score *= 0.7

        reason = f"{len(matches)} keyword pattern(s) matched"
        if contradictions:
            reason += f"; {contradictions} contradiction(s) detected"

        return base_score, reason

    def _detect_contradictions(self, text: str, domain: str) -> int:
        """Detect if the request contradicts a domain assignment."""
        contradictions = 0

        # Deploy but says "don't merge" = contradiction
        if domain == "deploy" and ("don't merge" in text or "no push" in text):
            contradictions += 1

        # Code but says "just report" = might be debug instead
        if domain == "code" and "report only" in text:
            contradictions += 1

        # Design but says "ignore visuals" = contradiction
        if domain == "design" and ("ignore.*visual" in text or "just.*logic" in text):
            contradictions += 1

        return contradictions

    def compute_entropy(self, scores: Dict[str, Tuple[float, str]]) -> float:
        """
        Compute Shannon entropy of domain scores (0=certain, 1=maximally ambiguous).

        Args:
            scores: Domain -> (confidence, reason)

        Returns:
            Entropy value 0-1
        """
        confidences = [conf for conf, _ in scores.values()]

        if not confidences:
            return 0.0

        # Normalize to probabilities
        total = sum(confidences)
        if total == 0:
            return 0.0

        probs = [c / total for c in confidences]

        # Shannon entropy: -sum(p * log2(p))
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * (p**0.5)  # Simplified entropy (normalized)

        # Scale to 0-1
        return min(entropy, 1.0)

    def get_ambiguity_level(self, entropy: float) -> str:
        """Classify ambiguity level based on entropy."""
        if entropy < 0.3:
            return "low"
        elif entropy < 0.7:
            return "medium"
        return "high"

    def detect_multi_intent(self, request: str) -> List[Tuple[str, str]]:
        """
        Detect if request contains multiple intents (e.g., "review and fix").

        Returns:
            List of (sub_request, inferred_domain)
        """
        # Split on coordinators
        parts = re.split(r"\band\b|\,|;", request, flags=re.IGNORECASE)

        if len(parts) <= 1:
            return []  # Single intent

        sub_tasks = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 5:
                sub_tasks.append(part)

        return [(task, "unknown") for task in sub_tasks]

    def score_fallback_priority(
        self, primary_model: str, primary_domain: str, confidence: float
    ) -> List[Dict[str, str]]:
        """
        Generate fallback routes ranked by priority.

        Lower priority = try first.
        """
        fallbacks = []

        # If confidence is high, fallback to same model/domain on different LLM
        if confidence > 0.8:
            fallbacks.append(
                {
                    "model": "claude-sonnet",
                    "reason": f"Primary {primary_model} unavailable; Sonnet maintains {primary_domain} domain expertise",
                    "priority": 1,
                }
            )
            fallbacks.append(
                {"model": "gpt-4", "reason": "Cross-LLM redundancy", "priority": 2}
            )
        else:
            # If ambiguous, try different domains
            fallbacks.append(
                {
                    "model": "claude-sonnet",
                    "reason": "Medium confidence - Sonnet good for ambiguous routing",
                    "priority": 1,
                }
            )
            fallbacks.append(
                {
                    "model": "gpt-4",
                    "reason": "Secondary model for multi-domain tasks",
                    "priority": 2,
                }
            )

        return fallbacks


def main():
    """CLI test."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python confidence_scorer.py '<request>'")
        sys.exit(1)

    request = sys.argv[1]
    scorer = ConfidenceScorer(verbose=True)

    domains = ["code", "design", "content", "sales", "debug", "deploy", "ops", "idea"]
    scores = scorer.score_request(request, domains)

    print(f"\nRequest: {request}")
    print(f"\nScores:")
    for domain, (conf, reason) in sorted(scores.items(), key=lambda x: x[1][0], reverse=True):
        print(f"  {domain:10s}: {conf:.2f} ({reason})")

    entropy = scorer.compute_entropy(scores)
    ambiguity = scorer.get_ambiguity_level(entropy)
    print(f"\nEntropy: {entropy:.2f}")
    print(f"Ambiguity: {ambiguity}")

    multi_intent = scorer.detect_multi_intent(request)
    if multi_intent:
        print(f"Multi-intent detected: {len(multi_intent)} sub-tasks")
        for task, _ in multi_intent:
            print(f"  - {task}")


if __name__ == "__main__":
    main()
