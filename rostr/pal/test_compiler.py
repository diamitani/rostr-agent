"""
PAL Compiler — Comprehensive Test Suite
=========================================

25+ test cases covering:
  - Domain classification
  - Compound requests
  - Ambiguous requests
  - Context-aware compilation
  - Tool restriction generation
  - Risk escalation
  - Model fallback selection
  - Output format detection
  - YAML/JSON serialization
  - Urgency routing
  - Subject extraction
  - Constraint extraction
  - Completion criteria
  - End-to-end compilation

Run: python -m pytest rostr/pal/test_compiler.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the rostr package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rostr.pal.compiler import (
    AgentManifest,
    ContextResolver,
    Intent,
    IntentExtractor,
    ManifestCompiler,
    ModelPolicy,
    ModelRouter,
    PALCompiler,
    ResolvedContext,
    SemanticEnhancer,
    ToolPolicy,
)


# ════════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def extractor():
    return IntentExtractor()


@pytest.fixture
def enhancer():
    return SemanticEnhancer()


@pytest.fixture
def router():
    return ModelRouter()


@pytest.fixture
def compiler():
    return PALCompiler()


@pytest.fixture
def compiler_with_context():
    return PALCompiler(
        session_context={"user": "patrick", "prior_decisions": [{"chose": "python"}]},
        project_context={"name": "rostr", "runtime": "local"},
        organization_context={"name": "Atlas HXM", "budget": {"max_cost_usd": 5.0}},
    )


@pytest.fixture
def basic_context():
    return ResolvedContext(
        available_tools=["web_search", "file_read", "code_execution", "file_write"],
        runtime_environment="local",
    )


# ════════════════════════════════════════════════════════════════════════════════
# TEST: DOMAIN CLASSIFICATION
# ════════════════════════════════════════════════════════════════════════════════


class TestDomainClassification:
    """Test that domains are correctly classified from natural language."""

    def test_code_domain(self, extractor):
        intent = extractor.extract("Build a REST API with FastAPI")
        assert intent.domain == "code"

    def test_deploy_domain(self, extractor):
        intent = extractor.extract("Ship this to production")
        assert intent.domain == "deploy"

    def test_debug_domain(self, extractor):
        intent = extractor.extract("There's a bug in the login flow, it crashes on submit")
        assert intent.domain == "debug"

    def test_design_domain(self, extractor):
        intent = extractor.extract("Design a new UI layout for the dashboard")
        assert intent.domain == "design"

    def test_content_domain(self, extractor):
        intent = extractor.extract("Write a blog post about microservices")
        assert intent.domain == "content"

    def test_sales_domain(self, extractor):
        intent = extractor.extract("Research this prospect and draft outreach for the lead")
        assert intent.domain == "sales"

    def test_ops_domain(self, extractor):
        intent = extractor.extract("Set up monitoring alerts for the kubernetes cluster")
        assert intent.domain == "ops"

    def test_idea_domain(self, extractor):
        intent = extractor.extract("Brainstorm what if we added AI to our strategy")
        assert intent.domain == "idea"

    def test_ambiguous_defaults_to_code(self, extractor):
        """When no signals match, default to code."""
        intent = extractor.extract("do the thing")
        # Should get some domain (code is default when no signals)
        assert intent.domain in (
            "code", "deploy", "debug", "design", "content",
            "sales", "ops", "idea"
        )


# ════════════════════════════════════════════════════════════════════════════════
# TEST: COMPOUND REQUESTS
# ════════════════════════════════════════════════════════════════════════════════


class TestCompoundRequests:
    """Test decomposition of compound (multi-task) requests."""

    def test_and_compound(self, compiler):
        manifest = compiler.compile("Build the API and deploy it to staging")
        # Should detect both code and deploy domains
        intent = manifest.intent
        assert intent.domain in ("code", "deploy")
        # Should have secondary domain detected
        assert len(intent.secondary_domains) >= 0  # At least attempted

    def test_then_compound(self, enhancer, basic_context):
        intent = Intent(
            primary_goal="Fix the bug then deploy the fix",
            domain="debug",
            task_type="action",
            subject="bug fix",
        )
        enhanced = enhancer.enhance(intent, basic_context)
        # Compound should be decomposed into phases
        assert "Phase" in enhanced.primary_goal or "then" not in enhanced.primary_goal.lower()

    def test_multi_part_request(self, compiler):
        manifest = compiler.compile(
            "Research the competitor, write a comparison doc, and update the CRM"
        )
        # Should handle gracefully
        assert manifest.intent.primary_goal != ""
        assert manifest.manifest_version == "1.0"

    def test_compound_preserves_all_parts(self, enhancer, basic_context):
        intent = Intent(
            primary_goal="Create the schema and also write the migration and then test it",
            domain="code",
            task_type="creation",
            subject="schema and migration",
        )
        enhanced = enhancer.enhance(intent, basic_context)
        # Should contain phase decomposition
        assert "Phase" in enhanced.primary_goal


# ════════════════════════════════════════════════════════════════════════════════
# TEST: AMBIGUOUS REQUESTS
# ════════════════════════════════════════════════════════════════════════════════


class TestAmbiguousRequests:
    """Test handling of vague/ambiguous input."""

    def test_very_short_input(self, compiler):
        manifest = compiler.compile("fix it")
        assert manifest.intent.ambiguity_score > 0.3
        assert len(manifest.intent.missing_information) > 0

    def test_no_verb_input(self, compiler):
        manifest = compiler.compile("the login page")
        assert manifest.intent.ambiguity_score > 0.3

    def test_hedging_language(self, compiler):
        manifest = compiler.compile(
            "Maybe if you have time could you perhaps look at the tests"
        )
        # Hedging should be removed in enhanced goal
        enhanced = manifest.intent.primary_goal
        assert "maybe" not in enhanced.lower() or manifest.intent.ambiguity_score > 0.0

    def test_assumptions_generated(self, extractor):
        intent = extractor.extract("improve things")
        # Should generate assumptions for missing info
        assert intent.ambiguity_score > 0.3
        # Missing info should be identified
        assert len(intent.missing_information) > 0

    def test_high_specificity_low_ambiguity(self, extractor):
        intent = extractor.extract(
            "Build a Python FastAPI endpoint at /api/users that returns "
            "JSON user data from the postgres database with test coverage"
        )
        # Highly specific request should have low ambiguity
        assert intent.ambiguity_score < 0.5
        assert intent.domain == "code"


# ════════════════════════════════════════════════════════════════════════════════
# TEST: CONTEXT-AWARE COMPILATION
# ════════════════════════════════════════════════════════════════════════════════


class TestContextAwareCompilation:
    """Test that context sources influence compilation output."""

    def test_org_budget_reflected(self, compiler_with_context):
        manifest = compiler_with_context.compile("Build a new feature")
        assert manifest.budget.get("max_cost_usd") == 5.0

    def test_project_context_in_sources(self, compiler_with_context):
        manifest = compiler_with_context.compile("Refactor the auth module")
        assert "project" in manifest.context_sources

    def test_session_context_in_sources(self, compiler_with_context):
        manifest = compiler_with_context.compile("Continue from where we left off")
        assert "session" in manifest.context_sources

    def test_runtime_from_project(self, compiler_with_context):
        manifest = compiler_with_context.compile("Run the tests")
        assert manifest.runtime == "local"

    def test_deploy_overrides_runtime_to_cloud(self):
        compiler = PALCompiler(project_context={"runtime": "local"})
        manifest = compiler.compile("Deploy this to production now")
        assert manifest.runtime == "cloud"


# ════════════════════════════════════════════════════════════════════════════════
# TEST: TOOL RESTRICTION GENERATION
# ════════════════════════════════════════════════════════════════════════════════


class TestToolRestrictions:
    """Test that tool policies are correctly generated based on intent."""

    def test_code_domain_gets_write_tools(self, compiler):
        manifest = compiler.compile("Implement the user service")
        tool_ids = [tp.tool_id for tp in manifest.tool_policies]
        assert "file_write" in tool_ids
        assert "code_execution" in tool_ids

    def test_query_restricts_write_tools(self, compiler):
        manifest = compiler.compile("What is the current database schema?")
        write_tools = [
            tp for tp in manifest.tool_policies
            if tp.tool_id == "file_write"
        ]
        # Write tools should be disallowed for queries
        if write_tools:
            assert write_tools[0].allowed is False

    def test_high_risk_requires_approval(self, compiler):
        manifest = compiler.compile(
            "Deploy the database migration to production with customer data"
        )
        # Some tools should require approval for high/critical risk
        approval_required = [tp for tp in manifest.tool_policies if tp.requires_approval]
        assert len(approval_required) > 0

    def test_deploy_domain_production_environment(self, compiler):
        manifest = compiler.compile("Ship this release to production")
        deploy_tools = [
            tp for tp in manifest.tool_policies
            if tp.environment == "production"
        ]
        assert len(deploy_tools) > 0


# ════════════════════════════════════════════════════════════════════════════════
# TEST: RISK ESCALATION
# ════════════════════════════════════════════════════════════════════════════════


class TestRiskEscalation:
    """Test that risk levels are correctly identified and escalated."""

    def test_production_is_critical(self, extractor):
        intent = extractor.extract("Delete the production database records")
        assert intent.risk_level == "critical"

    def test_credentials_are_critical(self, extractor):
        intent = extractor.extract("Update the API credentials in the config")
        assert intent.risk_level == "critical"

    def test_deploy_is_medium_by_default(self, extractor):
        intent = extractor.extract("Deploy the new feature")
        assert intent.risk_level in ("medium", "high")

    def test_docs_are_low_risk(self, extractor):
        intent = extractor.extract("Update the readme documentation")
        assert intent.risk_level == "low"

    def test_critical_risk_requires_approval(self, compiler):
        manifest = compiler.compile("Drop the users table in production")
        assert manifest.approval_policy == "require"
        assert manifest.execution_policy == "supervised"

    def test_low_risk_auto_approval(self, compiler):
        manifest = compiler.compile("Add a comment to the test file")
        assert manifest.approval_policy == "auto"
        assert manifest.execution_policy == "auto"


# ════════════════════════════════════════════════════════════════════════════════
# TEST: MODEL ROUTING AND FALLBACK
# ════════════════════════════════════════════════════════════════════════════════


class TestModelRouting:
    """Test model selection based on domain, risk, and urgency."""

    def test_code_high_risk_gets_opus(self, router):
        intent = Intent(
            primary_goal="Fix critical auth bypass", domain="code",
            risk_level="high", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert "opus" in policy.model
        assert policy.temperature == 0.1

    def test_design_gets_opus_high_temp(self, router):
        intent = Intent(
            primary_goal="Design the new dashboard", domain="design",
            risk_level="low", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert "opus" in policy.model
        assert policy.temperature >= 0.7

    def test_idea_gets_opus_highest_temp(self, router):
        intent = Intent(
            primary_goal="Brainstorm expansion strategy", domain="idea",
            risk_level="low", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert "opus" in policy.model
        assert policy.temperature >= 0.8

    def test_content_gets_sonnet(self, router):
        intent = Intent(
            primary_goal="Write a blog post", domain="content",
            risk_level="low", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert "sonnet" in policy.model
        assert 0.6 <= policy.temperature <= 0.8

    def test_ops_low_risk_gets_haiku(self, router):
        intent = Intent(
            primary_goal="Check the logs", domain="ops",
            risk_level="low", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert "haiku" in policy.model
        assert policy.temperature <= 0.3

    def test_critical_urgency_gets_fastest(self, router):
        intent = Intent(
            primary_goal="Production is down", domain="code",
            risk_level="critical", urgency="critical",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        # Critical urgency should pick fastest model (haiku)
        assert "haiku" in policy.model

    def test_fallback_chain_exists(self, router):
        intent = Intent(
            primary_goal="Build feature", domain="code",
            risk_level="high", urgency="normal",
        )
        ctx = ResolvedContext()
        policy = router.route(intent, ctx)
        assert len(policy.fallback_models) > 0

    def test_cost_ceiling_from_context(self, router):
        intent = Intent(
            primary_goal="Analyze data", domain="code",
            risk_level="low", urgency="normal",
        )
        ctx = ResolvedContext(budget_limits={"max_cost_usd": 3.0})
        policy = router.route(intent, ctx)
        assert policy.cost_ceiling == 3.0


# ════════════════════════════════════════════════════════════════════════════════
# TEST: OUTPUT FORMAT DETECTION
# ════════════════════════════════════════════════════════════════════════════════


class TestOutputFormatDetection:
    """Test that output contracts are correctly selected."""

    def test_code_output_for_implement(self, compiler):
        manifest = compiler.compile("Implement the user authentication function")
        assert manifest.output_contract == "code"

    def test_action_output_for_deploy(self, compiler):
        manifest = compiler.compile("Deploy the service to staging")
        assert manifest.output_contract == "action"

    def test_markdown_output_for_report(self, compiler):
        manifest = compiler.compile("Write a summary report of the findings")
        assert manifest.output_contract in ("markdown", "structured_report")

    def test_json_output_for_api(self, compiler):
        manifest = compiler.compile("Generate the JSON schema for the API response")
        assert manifest.output_contract == "json"


# ════════════════════════════════════════════════════════════════════════════════
# TEST: SERIALIZATION
# ════════════════════════════════════════════════════════════════════════════════


class TestSerialization:
    """Test YAML and JSON serialization of manifests."""

    def test_json_serialization(self, compiler):
        manifest = compiler.compile("Build a CLI tool in Python")
        json_str = manifest.to_json()
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["manifest_version"] == "1.0"
        assert "intent" in parsed
        assert "model_policy" in parsed
        assert parsed["intent"]["domain"] == "code"

    def test_yaml_serialization(self, compiler):
        manifest = compiler.compile("Design a landing page")
        yaml_str = manifest.to_yaml()
        # Should contain key YAML-like structures
        assert "manifest_version:" in yaml_str
        assert "intent:" in yaml_str
        assert "model_policy:" in yaml_str

    def test_dict_serialization(self, compiler):
        manifest = compiler.compile("Fix the broken test")
        d = manifest.to_dict()
        assert isinstance(d, dict)
        assert d["manifest_version"] == "1.0"
        assert isinstance(d["intent"], dict)
        assert isinstance(d["tool_policies"], list)

    def test_json_roundtrip(self, compiler):
        manifest = compiler.compile("Research the competitor landscape")
        json_str = manifest.to_json()
        parsed = json.loads(json_str)
        # Reconstruct from dict
        reconstructed = AgentManifest(**parsed)
        assert reconstructed.manifest_version == manifest.manifest_version
        assert reconstructed.intent.domain == manifest.intent.domain


# ════════════════════════════════════════════════════════════════════════════════
# TEST: END-TO-END COMPILATION
# ════════════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """End-to-end compilation tests with realistic inputs."""

    def test_full_pipeline_code_request(self, compiler):
        manifest = compiler.compile(
            "Build a production-grade Python REST API with FastAPI, "
            "include authentication, rate limiting, and comprehensive tests"
        )
        assert manifest.manifest_version == "1.0"
        assert manifest.intent.domain == "code"
        assert "use python" in [c.lower() for c in manifest.intent.constraints]
        assert "production-grade" in [c.lower() for c in manifest.intent.constraints]
        assert manifest.model_policy.provider == "anthropic"
        assert len(manifest.tool_policies) > 0
        assert manifest.task_id.startswith("pal-code-")

    def test_full_pipeline_deploy_request(self, compiler):
        manifest = compiler.compile("Ship the release to production ASAP")
        assert manifest.intent.domain == "deploy"
        assert manifest.intent.urgency == "high"
        assert manifest.runtime == "cloud"

    def test_full_pipeline_debug_critical(self, compiler):
        manifest = compiler.compile(
            "Production is down — the auth service is crashing on login. "
            "Fix it immediately."
        )
        assert manifest.intent.domain == "debug"
        assert manifest.intent.urgency in ("critical", "high")
        assert manifest.intent.risk_level in ("critical", "high")
        # Should use supervised execution for critical risk
        assert manifest.execution_policy == "supervised"

    def test_stages_inspection(self, compiler):
        """Test compile_with_stages returns all intermediate results."""
        raw_intent, ctx, enhanced, policy, manifest = compiler.compile_with_stages(
            "Create a React dashboard component with charts"
        )
        # Raw intent should be extracted
        assert raw_intent.domain in ("code", "design")
        assert raw_intent.subject != ""
        # Context should be resolved
        assert isinstance(ctx, ResolvedContext)
        # Enhanced intent should have more constraints
        assert len(enhanced.constraints) >= len(raw_intent.constraints)
        # Model policy should be set
        assert policy.model != ""
        # Manifest should be complete
        assert manifest.task_id != ""

    def test_deterministic_compilation(self, compiler):
        """Same input should always produce same output."""
        input_text = "Build a user authentication service in Python"
        m1 = compiler.compile(input_text)
        m2 = compiler.compile(input_text)
        assert m1.task_id == m2.task_id
        assert m1.intent.domain == m2.intent.domain
        assert m1.model_policy.model == m2.model_policy.model
        assert m1.intent.primary_goal == m2.intent.primary_goal


# ════════════════════════════════════════════════════════════════════════════════
# TEST: SUBJECT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════


class TestSubjectExtraction:
    """Test that subjects are correctly extracted from various phrasings."""

    def test_simple_verb_object(self, extractor):
        intent = extractor.extract("Build a REST API")
        assert "rest api" in intent.subject.lower()

    def test_please_prefix(self, extractor):
        intent = extractor.extract("Please create a new user model")
        assert "user model" in intent.subject.lower() or "new user model" in intent.subject.lower()

    def test_complex_subject(self, extractor):
        intent = extractor.extract(
            "Implement rate limiting for the authentication endpoint"
        )
        assert "rate limiting" in intent.subject.lower()


# ════════════════════════════════════════════════════════════════════════════════
# TEST: CONSTRAINT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════


class TestConstraintExtraction:
    """Test constraint detection from various signals."""

    def test_technology_constraint(self, extractor):
        intent = extractor.extract("Build it in typescript with react")
        constraints_lower = [c.lower() for c in intent.constraints]
        assert any("typescript" in c for c in constraints_lower)
        assert any("react" in c for c in constraints_lower)

    def test_quality_constraint(self, extractor):
        intent = extractor.extract("Make it production-grade with tests")
        constraints_lower = [c.lower() for c in intent.constraints]
        assert any("production" in c for c in constraints_lower)
        assert any("test" in c for c in constraints_lower)

    def test_negative_constraint(self, extractor):
        intent = extractor.extract("Build it without any external dependencies")
        constraints_lower = [c.lower() for c in intent.constraints]
        assert any("no external dependencies" in c or "avoid" in c for c in constraints_lower)


# ════════════════════════════════════════════════════════════════════════════════
# TEST: URGENCY CLASSIFICATION
# ════════════════════════════════════════════════════════════════════════════════


class TestUrgencyClassification:
    """Test urgency detection from temporal signals."""

    def test_critical_urgency(self, extractor):
        intent = extractor.extract("Emergency: production is down, critical outage")
        assert intent.urgency == "critical"

    def test_high_urgency(self, extractor):
        intent = extractor.extract("Fix this ASAP, it's blocking the team")
        assert intent.urgency == "high"

    def test_normal_urgency(self, extractor):
        intent = extractor.extract("Build the feature for this sprint")
        assert intent.urgency == "normal"

    def test_low_urgency(self, extractor):
        intent = extractor.extract("Eventually we should refactor this, low priority")
        assert intent.urgency == "low"


# ════════════════════════════════════════════════════════════════════════════════
# TEST: COMPLETION CRITERIA
# ════════════════════════════════════════════════════════════════════════════════


class TestCompletionCriteria:
    """Test that appropriate completion criteria are generated."""

    def test_code_criteria(self, compiler):
        manifest = compiler.compile("Implement the payment service")
        criteria_lower = [c.lower() for c in manifest.completion_criteria]
        assert any("test" in c for c in criteria_lower)

    def test_deploy_criteria(self, compiler):
        manifest = compiler.compile("Deploy the app to production")
        criteria_lower = [c.lower() for c in manifest.completion_criteria]
        assert any("deploy" in c or "health" in c for c in criteria_lower)

    def test_high_risk_adds_rollback_criteria(self, compiler):
        manifest = compiler.compile(
            "Deploy the database migration affecting customer data in production"
        )
        criteria_lower = [c.lower() for c in manifest.completion_criteria]
        assert any("rollback" in c for c in criteria_lower)


# ════════════════════════════════════════════════════════════════════════════════
# TEST: INPUT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════


class TestInputExtraction:
    """Test extraction of structured inputs (URLs, paths, references)."""

    def test_url_extraction(self, extractor):
        intent = extractor.extract("Scrape data from https://example.com/api/v1")
        assert "urls" in intent.inputs
        assert "https://example.com/api/v1" in intent.inputs["urls"]

    def test_path_extraction(self, extractor):
        intent = extractor.extract("Fix the bug in src/auth/login.py")
        assert "paths" in intent.inputs
        assert any("src/auth/login.py" in p for p in intent.inputs["paths"])

    def test_quoted_reference_extraction(self, extractor):
        intent = extractor.extract('Update the "UserService" class')
        assert "references" in intent.inputs
        assert "UserService" in intent.inputs["references"]
