"""Vercel AI Gateway routing — no network."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "Tools"))

from system_one.gateway import (  # noqa: E402
    VERCEL_MODELS,
    _effective_model,
    fallbacks_for,
    model_for,
    resolve_gateway,
    route_from_phase,
)


class TestGateway(unittest.TestCase):
    def test_live_catalog_slugs(self):
        self.assertEqual(model_for("frontier"), "spacexai/grok-4.5")
        self.assertEqual(model_for("cheap"), "google/gemini-3.1-flash-lite")
        self.assertEqual(model_for("subagent"), "anthropic/claude-sonnet-4.6")
        self.assertTrue(VERCEL_MODELS["background"].endswith("flash-lite"))

    def test_phase_picks_route(self):
        self.assertEqual(route_from_phase("PreD"), "cheap")
        self.assertEqual(route_from_phase("Debugging"), "frontier")
        self.assertEqual(route_from_phase("Design"), "subagent")

    def test_fallbacks_only_on_vercel_door(self):
        self.assertTrue(fallbacks_for("frontier", "vercel-ai-gateway"))
        self.assertEqual(fallbacks_for("frontier", "xai-direct"), [])

    def test_xai_direct_strips_provider_prefix(self):
        resolved = {"provider": "xai-direct"}
        self.assertEqual(_effective_model("spacexai/grok-4.5", resolved), "grok-4.5")
        self.assertEqual(_effective_model("anthropic/claude-sonnet-4.6", resolved), "grok-4.5")

    def test_resolve_without_keys_is_not_ready(self):
        saved = {
            k: os.environ.pop(k, None)
            for k in ("AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN", "XAI_API_KEY")
        }
        try:
            info = resolve_gateway()
            self.assertEqual(info["provider"], "none")
            self.assertFalse(info["ready"])
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
