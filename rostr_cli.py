#!/usr/bin/env python3
"""
ROSTR Agent CLI — Multi-agent framework combining Hermes + ROSTR intelligence.
"""
import sys
import json
import argparse
from pathlib import Path

__version__ = "0.1.0"

class RostrCLI:
    def __init__(self):
        self.root = Path(__file__).parent
        self.skills = self._load_skills()

    def _load_skills(self):
        """Load 41 generalized skills from MARKETPLACE.md"""
        skills = {
            "gtm": [
                "atlas-agent-factory",
                "clay-prospecting-engine",
                "atlas-gtm-insider",
                "gtm-architect",
                "atlas-use-case-builder",
                "jtbd-builder",
                "asana-organizer",
                "atlas-prospect-video-builder",
            ],
            "dev": [
                "pal-compiler",
                "context-engine",
                "rostr-agent-builder",
                "prompt-rewriter",
                "n8n-engineer",
                "n8n-workflow-architect",
                "n8n-execution-analyst",
                "n8n-csv-router",
            ],
            "content": [
                "video-editor-hyperframes",
                "atlas-video-studio",
                "atlas-video-render",
                "case-study-builder",
                "daily-session-recap",
                "project-instructions-builder",
            ],
            "data": [
                "hubspot-data-analyst",
                "dashboard-builder",
                "token-spend-analyzer",
                "clay-credit-estimator",
                "clay-credit-calculator",
                "clay-csv-enricher",
            ],
            "automation": [
                "workflow-builder",
                "executive-assistant",
                "file-organizer",
                "project-closeout-report",
                "project-handoff",
                "new-project-system",
                "saas-architect",
                "product-builder",
            ],
        }

        flat = {}
        for category, skill_list in skills.items():
            for skill in skill_list:
                flat[skill] = {"category": category, "name": skill}
        return flat

    def cmd_version(self, args):
        """Show version"""
        print(f"ROSTR Agent {__version__}")

    def cmd_skills_list(self, args):
        """List all available skills"""
        categories = {}
        for skill_id, skill in self.skills.items():
            cat = skill["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill_id)

        for category in sorted(categories.keys()):
            print(f"\n{category.upper()} ({len(categories[category])} skills)")
            for skill_id in sorted(categories[category]):
                print(f"  - {skill_id}")

        print(f"\nTotal: {len(self.skills)} skills")

    def cmd_skill_invoke(self, args):
        """Invoke a skill"""
        skill_id = args.skill
        if skill_id not in self.skills:
            print(f"Error: Skill '{skill_id}' not found", file=sys.stderr)
            return 1

        # Placeholder: in real implementation, would load and execute skill
        print(f"Invoking {skill_id}...")
        print(json.dumps({
            "status": "placeholder",
            "skill": skill_id,
            "message": "Skill execution requires full implementation"
        }, indent=2))
        return 0

    def cmd_eval_run(self, args):
        """Run evaluation against benchmark tasks"""
        eval_file = self.root / "eval_runner.py"
        if not eval_file.exists():
            print(f"Error: eval_runner.py not found", file=sys.stderr)
            return 1

        print("Running ROSTR vs Hermes evaluation...")
        print("(See eval_runner.py for benchmark details)")
        # Placeholder: would import and run eval_runner.main()
        return 0

    def cmd_eval_tasks(self, args):
        """Show benchmark tasks"""
        tasks_file = self.root / "benchmark_tasks.json"
        if not tasks_file.exists():
            print(f"Error: benchmark_tasks.json not found", file=sys.stderr)
            return 1

        with open(tasks_file) as f:
            tasks = json.load(f)

        print(f"Benchmark Tasks ({len(tasks['tasks'])} total)")
        print(f"Domains: {', '.join(tasks['domains'])}")
        print("")

        by_domain = {}
        for task in tasks['tasks']:
            domain = task['domain']
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(task)

        for domain in sorted(by_domain.keys()):
            print(f"{domain.upper()} ({len(by_domain[domain])} tasks)")
            for task in by_domain[domain][:3]:  # Show first 3
                print(f"  - {task['name']}")
            if len(by_domain[domain]) > 3:
                print(f"  ... and {len(by_domain[domain]) - 3} more")

    def run(self, args=None):
        """Main entry point"""
        parser = argparse.ArgumentParser(
            description="ROSTR Agent — Multi-agent framework with Hermes + intelligence layer"
        )
        parser.add_argument("--version", action="store_true", help="Show version")

        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # version
        subparsers.add_parser("version", help="Show version")

        # skills
        skills_parser = subparsers.add_parser("skills", help="Manage skills")
        skills_subparsers = skills_parser.add_subparsers(dest="skill_command")
        skills_subparsers.add_parser("list", help="List all skills")

        invoke_parser = skills_subparsers.add_parser("invoke", help="Invoke a skill")
        invoke_parser.add_argument("skill", help="Skill ID")
        invoke_parser.add_argument("--input", help="Input data")

        # eval
        eval_parser = subparsers.add_parser("eval", help="Run evaluations")
        eval_subparsers = eval_parser.add_subparsers(dest="eval_command")
        eval_subparsers.add_parser("run", help="Run benchmark evaluation")
        eval_subparsers.add_parser("tasks", help="Show benchmark tasks")

        args = parser.parse_args(args)

        # Handle version flag
        if args.version or args.command == "version":
            self.cmd_version(args)
            return 0

        # Handle subcommands
        if args.command == "skills":
            if args.skill_command == "list":
                self.cmd_skills_list(args)
            elif args.skill_command == "invoke":
                return self.cmd_skill_invoke(args)
        elif args.command == "eval":
            if args.eval_command == "run":
                return self.cmd_eval_run(args)
            elif args.eval_command == "tasks":
                return self.cmd_eval_tasks(args)
        else:
            parser.print_help()

        return 0

if __name__ == "__main__":
    cli = RostrCLI()
    sys.exit(cli.run())
