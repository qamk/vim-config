import json
import tempfile
import tomllib
import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_config.compiler import Builder, install_build
from agentic_config.targets import load_target


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / ".agentic-config"
        (self.root / "core").mkdir(parents=True)
        (self.root / "resources" / "reports").mkdir(parents=True)
        (self.root / "skills" / "report").mkdir(parents=True)
        (self.root / "agents" / "claude-source").mkdir(parents=True)
        (self.root / "targets").mkdir()
        (self.root / "core" / "instructions.md").write_text(
            "Read agentic://reports/modifiers.\n",
            encoding="utf-8",
        )
        (self.root / "resources" / "reports" / "modifiers.md").write_text(
            "# Modifiers\n",
            encoding="utf-8",
        )
        (self.root / "skills" / "report" / "SKILL.md").write_text(
            "---\nname: report\ndescription: Report.\n---\n",
            encoding="utf-8",
        )
        (self.root / "agents" / "claude-source" / "reviewer.md").write_text(
            "---\nname: reviewer\ndescription: Review carefully.\nmodel: opus\n---\n"
            "Review the result.\n",
            encoding="utf-8",
        )
        self.live = Path(self.temporary.name) / "live"
        target_text = f"""
[target]
id = "test"
adapter = "codex"
schema_version = 1

[features.instructions]
status = "native"
destination = "{self.live}/AGENTS.md"

[features.skills]
status = "native"
destination = "{self.live}/skills"

[features.subagents]
status = "transformed"
destination = "{self.live}/agents"

[features.hooks]
status = "disabled"
reason = "Not used in this fixture."

[features.rules]
status = "disabled"
reason = "Not used in this fixture."

[features.plugins]
status = "disabled"
reason = "Not used in this fixture."

[features.resources]
status = "native"
destination = "{self.live}/resources"

[features.projects]
status = "disabled"
reason = "Not used in this fixture."

[features.content]
status = "disabled"
reason = "Not used in this fixture."

[models]
fast = "fast-model"
default = "default-model"
deep = "deep-model"
"""
        (self.root / "targets" / "test.toml").write_text(
            target_text,
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_build_resolves_resources_and_converts_agents(self):
        target, diagnostics = load_target(self.root / "targets" / "test.toml")
        self.assertEqual([d for d in diagnostics if d.level == "error"], [])
        build = self.root / "build" / "test"

        manifest, diagnostics = Builder(self.root, target).build(build)

        instructions = build / "payload" / "instructions" / "instructions.md"
        self.assertEqual(
            instructions.read_text(),
            f"Read {self.live}/resources/reports/modifiers.md.\n",
        )
        agent = build / "payload" / "subagents" / "reviewer.toml"
        parsed = tomllib.loads(agent.read_text())
        self.assertEqual(parsed["name"], "reviewer")
        self.assertEqual(parsed["model"], "deep-model")
        self.assertEqual(parsed["model_reasoning_effort"], "high")
        self.assertGreater(len(manifest["files"]), 3)
        self.assertTrue(manifest["valid"])
        self.assertEqual([d for d in diagnostics if d.level == "error"], [])

    def test_invalid_build_cannot_be_installed(self):
        (self.root / "core" / "instructions.md").write_text(
            "Read agentic://missing/resource.\n",
            encoding="utf-8",
        )
        target, _ = load_target(self.root / "targets" / "test.toml")
        build = self.root / "build" / "test"
        manifest, _ = Builder(self.root, target).build(build)

        counts, diagnostics = install_build(build, apply=True)

        self.assertFalse(manifest["valid"])
        self.assertEqual(counts["copied"], 0)
        self.assertTrue(any(item.code == "invalid-build" for item in diagnostics))

    def test_install_is_dry_run_by_default_and_refuses_unowned_overwrite(self):
        target, _ = load_target(self.root / "targets" / "test.toml")
        build = self.root / "build" / "test"
        Builder(self.root, target).build(build)

        counts, diagnostics = install_build(build, apply=False)
        self.assertGreater(counts["new"], 0)
        self.assertFalse(self.live.exists())
        self.assertEqual(diagnostics, [])

        self.live.mkdir()
        (self.live / "AGENTS.md").write_text("user-owned\n", encoding="utf-8")
        counts, diagnostics = install_build(build, apply=True)
        self.assertEqual((self.live / "AGENTS.md").read_text(), "user-owned\n")
        self.assertGreater(counts["conflict"], 0)
        self.assertFalse((self.live / "skills").exists())
        self.assertTrue(any(item.code == "destination-conflict" for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
