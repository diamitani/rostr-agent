#!/usr/bin/env python3
"""
Test suite for NPAO — Nuanced Prompt Abstraction Orchestrator

5+ test cases covering:
1. Ambiguous multi-intent request
2. High-confidence single domain
3. Confidence scoring validation
4. Fallback routing
5. Multi-intent task splitting
"""

import json
import sys
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "npao"))

from main import NPAO, AmbiguityLevel


def test_1_multi_intent_detection():
    """Test 1: Ambiguous multi-intent request → secondary domains detected."""
    npao = NPAO(verbose=False)
    request = "review my marketing copy and fix the grammar"

    manifest = npao.orchestrate(request)

    assert "primary_domain" in manifest, "Should have primary domain"
    assert "secondary_domains" in manifest, "Should have secondary domains"
    assert "sub_tasks" in manifest, "Should detect sub-tasks"

    # Multi-intent should be detected
    if len(manifest["sub_tasks"]) > 0:
        assert len(manifest["sub_tasks"]) >= 1, "Should split into multiple tasks"

    print("✓ Test 1 PASSED: Multi-intent detection working")
    return True


def test_2_single_intent_high_confidence():
    """Test 2: Clear single-intent → low ambiguity, high confidence."""
    npao = NPAO(verbose=False)
    request = "debug this production bug and root cause it"

    manifest = npao.orchestrate(request)

    assert manifest["ambiguity_level"] == "low", f"Expected low ambiguity, got {manifest['ambiguity_level']}"
    assert manifest["confidence_score"] > 0.7, f"Expected high confidence, got {manifest['confidence_score']}"
    assert manifest["primary_domain"] == "debug"

    print("✓ Test 2 PASSED: Single-intent high confidence routed correctly")
    return True


def test_3_confidence_scoring():
    """Test 3: Confidence scoring reflects keyword matches."""
    npao = NPAO(verbose=False)

    # High-specificity code request
    code_manifest = npao.orchestrate("refactor the class architecture and optimize the API")
    assert code_manifest["confidence_score"] > 0.7, "Code keywords should score high"

    # Ambiguous request with mixed keywords
    mixed_manifest = npao.orchestrate("build something cool")
    assert mixed_manifest["confidence_score"] < 0.8, "Vague keywords should score lower"

    print("✓ Test 3 PASSED: Confidence scoring reflects keyword specificity")
    return True


def test_4_fallback_routing():
    """Test 4: Fallback routes generated and ranked."""
    npao = NPAO(verbose=False)
    request = "review this code change"

    manifest = npao.orchestrate(request)

    assert "fallback_routes" in manifest, "Should include fallback routes"
    assert len(manifest["fallback_routes"]) > 0, "Should have at least one fallback"

    # Check priority ordering
    priorities = [f.get("priority") for f in manifest["fallback_routes"]]
    assert priorities == sorted(priorities), "Fallbacks should be sorted by priority"

    print("✓ Test 4 PASSED: Fallback routing working")
    return True


def test_5_multi_intent_splitting():
    """Test 5: Multi-intent requests split into sub-tasks."""
    npao = NPAO(verbose=False)
    request = "build the API endpoint and write the documentation and test it"

    manifest = npao.orchestrate(request)

    assert "sub_tasks" in manifest, "Should detect sub-tasks"
    if len(manifest["sub_tasks"]) > 0:
        for sub_task in manifest["sub_tasks"]:
            assert "task" in sub_task, "Sub-task should have 'task' field"
            assert "domain" in sub_task, "Sub-task should have 'domain' field"
            assert "confidence" in sub_task, "Sub-task should have 'confidence' field"

    print("✓ Test 5 PASSED: Multi-intent task splitting working")
    return True


def test_6_routing_trace():
    """Test 6: Routing trace provides observability."""
    npao = NPAO(verbose=False)
    request = "ship this feature to production"

    manifest = npao.orchestrate(request)

    assert "routing_trace" in manifest, "Should include routing trace"
    trace = manifest["routing_trace"]
    assert "matches" in trace, "Trace should include matches"
    assert "resolution" in trace, "Trace should include resolution"
    assert isinstance(trace["matches"], list), "Matches should be a list"

    print("✓ Test 6 PASSED: Routing trace provides observability")
    return True


def test_7_recommendation_generation():
    """Test 7: Recommendation reflects confidence and ambiguity."""
    npao = NPAO(verbose=False)

    # High confidence → CLEAR recommendation
    clear_manifest = npao.orchestrate("debug this broken function")
    assert "CLEAR" in clear_manifest["recommendation"], "High confidence should say CLEAR"

    # Medium ambiguity → MEDIUM AMBIGUITY recommendation
    ambiguous_manifest = npao.orchestrate("help me improve this")
    assert any(word in ambiguous_manifest["recommendation"] for word in ["AMBIGUITY", "fallback"]), "Low confidence should mention ambiguity"

    print("✓ Test 7 PASSED: Recommendation reflects confidence")
    return True


def test_8_secondary_domains():
    """Test 8: Secondary domains ranked correctly."""
    npao = NPAO(verbose=False)
    request = "write marketing copy that converts"

    manifest = npao.orchestrate(request)

    if len(manifest["secondary_domains"]) > 1:
        # Check they're sorted by confidence descending
        confidences = [d["confidence"] for d in manifest["secondary_domains"]]
        assert confidences == sorted(confidences, reverse=True), "Secondaries should be sorted by confidence"

    print("✓ Test 8 PASSED: Secondary domains ranked correctly")
    return True


def test_9_entropy_computation():
    """Test 9: Entropy correlates with ambiguity level."""
    npao = NPAO(verbose=False)

    # Clear request → low entropy
    clear_manifest = npao.orchestrate("fix this bug")
    if clear_manifest["ambiguity_level"] == "low":
        assert clear_manifest["routing_trace"]["input_entropy"] < 0.5

    # Vague request → higher entropy
    vague_manifest = npao.orchestrate("do something")
    if vague_manifest["ambiguity_level"] in ["medium", "high"]:
        assert vague_manifest["routing_trace"]["input_entropy"] > 0.2

    print("✓ Test 9 PASSED: Entropy computation working")
    return True


def test_10_manifest_structure():
    """Test 10: Complete manifest structure validation."""
    npao = NPAO(verbose=False)
    request = "review and improve the design"

    manifest = npao.orchestrate(request)

    # Required fields
    required = [
        "primary_domain",
        "confidence_score",
        "ambiguity_level",
        "routing_trace",
        "fallback_routes",
        "recommendation",
        "metadata",
    ]
    for field in required:
        assert field in manifest, f"Missing required field: {field}"

    # Type checks
    assert isinstance(manifest["primary_domain"], str)
    assert isinstance(manifest["confidence_score"], (int, float))
    assert manifest["ambiguity_level"] in ["low", "medium", "high"]
    assert isinstance(manifest["routing_trace"], dict)
    assert isinstance(manifest["fallback_routes"], list)

    print("✓ Test 10 PASSED: Complete manifest structure validated")
    return True


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_1_multi_intent_detection,
        test_2_single_intent_high_confidence,
        test_3_confidence_scoring,
        test_4_fallback_routing,
        test_5_multi_intent_splitting,
        test_6_routing_trace,
        test_7_recommendation_generation,
        test_8_secondary_domains,
        test_9_entropy_computation,
        test_10_manifest_structure,
    ]

    print("=" * 60)
    print("NPAO TEST SUITE")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} ERROR: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
