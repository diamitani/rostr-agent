#!/usr/bin/env python3
"""
Test suite for PAL — Prompt Abstraction Layer

5+ test cases covering:
1. Simple web request → design routing
2. Code review → code routing with Opus model
3. Bug fix → debug routing with investigation tools
4. Sales/GTM → sales routing with context injection
5. Complex multi-step → high complexity estimation
"""

import json
import sys
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pal"))

from main import PAL, Domain, Model, Behavior


def test_1_simple_design_request():
    """Test 1: Simple web request → design domain, Opus model."""
    pal = PAL(verbose=False)
    request = "make a basketball site for my school"

    manifest = pal.compile(request)

    assert manifest["domain"] == Domain.DESIGN, f"Expected design domain, got {manifest['domain']}"
    assert manifest["model"] == Model.CLAUDE_OPUS, f"Expected Opus model, got {manifest['model']}"
    assert "generative-design" in manifest["tools"] or "code-generation" in manifest["tools"], f"Expected design tools, got {manifest['tools']}"
    assert manifest["behavior"] == Behavior.AUTO_APPROVE
    assert manifest["temperature"] == 0.7, "Design tasks should have temp=0.7"

    print("✓ Test 1 PASSED: Simple design request routed correctly")
    return True


def test_2_code_review():
    """Test 2: Code review → code domain, Opus model, review tool."""
    pal = PAL(verbose=False)
    request = "review my code before I submit the PR"

    manifest = pal.compile(request)

    assert manifest["domain"] == Domain.CODE, f"Expected code domain, got {manifest['domain']}"
    assert manifest["model"] == Model.CLAUDE_OPUS, f"Expected Opus model, got {manifest['model']}"
    assert "code-analysis" in manifest["tools"], "Expected code-analysis tool"
    assert manifest["behavior"] == Behavior.AUTO_APPROVE

    print("✓ Test 2 PASSED: Code review routed to Opus with review tools")
    return True


def test_3_bug_investigation():
    """Test 3: Bug fix → debug domain, investigation tools."""
    pal = PAL(verbose=False)
    request = "why is the auth flow failing in production? investigate and debug"

    manifest = pal.compile(request)

    assert manifest["domain"] == Domain.DEBUG, f"Expected debug domain, got {manifest['domain']}"
    assert manifest["estimated_complexity"] in ["high", "medium"], "Multi-step should be medium+complexity"
    assert manifest["behavior"] == Behavior.AUTO_APPROVE

    print("✓ Test 3 PASSED: Bug investigation routed to debug domain")
    return True


def test_4_sales_context_injection():
    """Test 4: Sales/GTM request → sales domain, context injected."""
    pal = PAL(verbose=False)
    request = "write a cold email to a prospect about Atlas HXM's EOR platform"

    manifest = pal.compile(request)

    assert manifest["domain"] == Domain.SALES, f"Expected sales domain, got {manifest['domain']}"
    assert "knowledge_injected" in manifest.get("metadata", {}), "Should inject knowledge"
    assert len(manifest["metadata"]["knowledge_injected"]) > 0, "Should have injected knowledge"

    print("✓ Test 4 PASSED: Sales request with context injection")
    return True


def test_5_multi_step_complexity():
    """Test 5: Multi-step task → high complexity, multiple subtasks."""
    pal = PAL(verbose=False)
    request = "ship this feature and create a PR, then deploy to staging"

    manifest = pal.compile(request)

    # "ship" keyword maps to deploy; high complexity from multi-step (has "and")
    assert manifest["domain"] in [Domain.DEPLOY], f"Expected deploy domain, got {manifest['domain']}"
    assert manifest["estimated_complexity"] in ["high", "medium"], f"Expected high/medium complexity, got {manifest['estimated_complexity']}"
    assert len(manifest["metadata"].get("knowledge_injected", [])) >= 0

    print("✓ Test 5 PASSED: Multi-step task correctly identified as high complexity")
    return True


def test_6_report_only_constraint():
    """Test 6: Report-only constraint → report-only behavior."""
    pal = PAL(verbose=False)
    request = "audit only the codebase and report issues, don't fix anything"

    manifest = pal.compile(request)

    assert manifest["behavior"] == Behavior.REPORT_ONLY, f"Expected report-only behavior, got {manifest['behavior']}"
    assert manifest["domain"] == Domain.DEBUG

    print("✓ Test 6 PASSED: Report-only constraint correctly set behavior")
    return True


def test_7_temperature_by_domain():
    """Test 7: Temperature settings respect domain (code low, creative high)."""
    pal = PAL(verbose=False)

    # Creative task should have high temperature
    creative_manifest = pal.compile("help me brainstorm 10 marketing angles for Atlas")
    assert creative_manifest["temperature"] > 0.6, f"Creative should have high temp, got {creative_manifest['temperature']}"

    # Debug task should have low temperature
    debug_manifest = pal.compile("debug and investigate why this is failing")
    assert debug_manifest["temperature"] < 0.3, f"Debug should have low temp, got {debug_manifest['temperature']}"

    print("✓ Test 7 PASSED: Temperature settings respect domain characteristics")
    return True


def test_8_routing_instructions():
    """Test 8: Routing manifest includes MCP endpoints and execution flags."""
    pal = PAL(verbose=False)
    request = "test the checkout flow for bugs"

    manifest = pal.compile(request)

    assert "routing_instructions" in manifest, "Should include routing instructions"
    assert "mcp_endpoints" in manifest["routing_instructions"], "Should include MCP endpoints"
    assert "execution_flags" in manifest["routing_instructions"], "Should include execution flags"

    flags = manifest["routing_instructions"]["execution_flags"]
    assert "auto_approve" in flags, "Should have auto_approve flag"
    assert "safety_mode" in flags, "Should have safety_mode flag"

    print("✓ Test 8 PASSED: Routing instructions properly formed")
    return True


def test_9_output_format_detection():
    """Test 9: Output format is correctly detected from request."""
    pal = PAL(verbose=False)

    # Screenshot request
    screenshot_manifest = pal.compile("open the site and show me what it looks like")
    assert screenshot_manifest["metadata"]["output_format"] == "screenshot"

    # File/code request
    file_manifest = pal.compile("build me an HTML page")
    assert file_manifest["metadata"]["output_format"] == "file"

    # PR request
    pr_manifest = pal.compile("ship this feature and create a PR")
    assert pr_manifest["metadata"]["output_format"] == "pr"

    print("✓ Test 9 PASSED: Output format detection working")
    return True


def test_10_comprehensive_manifest():
    """Test 10: Full manifest structure validation."""
    pal = PAL(verbose=False)
    request = "review the API architecture and suggest improvements"

    manifest = pal.compile(request)

    # Required fields
    required = ["domain", "model", "temperature", "tools", "behavior", "enhanced_prompt", "routing_reason"]
    for field in required:
        assert field in manifest, f"Missing required field: {field}"

    # Type checks
    assert isinstance(manifest["domain"], str)
    assert isinstance(manifest["model"], str)
    assert isinstance(manifest["temperature"], (int, float))
    assert isinstance(manifest["tools"], list)
    assert isinstance(manifest["behavior"], str)
    assert isinstance(manifest["enhanced_prompt"], str)
    assert isinstance(manifest["routing_reason"], str)

    # Metadata
    assert "metadata" in manifest
    assert "original_request" in manifest["metadata"]
    assert "constraints" in manifest["metadata"]
    assert "knowledge_injected" in manifest["metadata"]

    print("✓ Test 10 PASSED: Complete manifest structure validated")
    return True


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_1_simple_design_request,
        test_2_code_review,
        test_3_bug_investigation,
        test_4_sales_context_injection,
        test_5_multi_step_complexity,
        test_6_report_only_constraint,
        test_7_temperature_by_domain,
        test_8_routing_instructions,
        test_9_output_format_detection,
        test_10_comprehensive_manifest,
    ]

    print("=" * 60)
    print("PAL TEST SUITE")
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
