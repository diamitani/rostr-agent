"""System One PAL tests — regex harness regressions plus mixed-intent cases."""

import sys
import unittest
from pathlib import Path

proj_root = Path(__file__).parent.parent
repo_root = proj_root.parent.parent
for p in (proj_root, repo_root / "Tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from skills.pal_skill import PALSkill
from system_one.engine import evaluate_local


class TestSystemOnePAL(unittest.TestCase):
    def setUp(self):
        self.pal = PALSkill()

    def test_research_beats_incidental_build(self):
        result = self.pal.compile("Research whether we should build a billing refund workflow")
        self.assertEqual(result.phase, "PreD")
        self.assertEqual(result.domain, "research")

    def test_gold_cases_still_hold(self):
        cases = [
            ("Research best practices for multi-agent state persistence", "PreD", "research"),
            ("Design UX wireframe and UI color palette tokens", "Design", "design"),
            ("Implement Next.js 15 API route for AI SDK streaming", "Development", "code"),
            ("Deploy production release to Vercel and AWS", "Deploy", "ops"),
            ("Fix error 500 in chat stream handler", "Debugging", "code"),
        ]
        for prompt, phase, domain in cases:
            with self.subTest(prompt=prompt):
                result = self.pal.compile(prompt)
                self.assertEqual(result.phase, phase)
                self.assertEqual(result.domain, domain)

    def test_phase_returns_full_distribution(self):
        answers = evaluate_local("fix the landing page design then ship it").answers
        probs = answers["phase"]["probabilities"]
        self.assertGreaterEqual(len(probs), 5)
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=5)
        self.assertIn(answers["phase"]["choice"], probs)

    def test_deploy_sets_approval_gate(self):
        result = self.pal.compile("Deploy production release to Vercel")
        self.assertIn("production_deploy", result.approval_required)


if __name__ == "__main__":
    unittest.main()
