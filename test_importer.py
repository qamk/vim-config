import hashlib
import json
import tempfile
import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_config.importer import execute_import, plan_claude_import


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ClaudeImporterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source = self.base / ".claude"
        self.root = self.base / ".agentic-config"
        (self.source / "skills" / "report").mkdir(parents=True)
        (self.source / "agents").mkdir()
        (self.source / "hooks").mkdir()
        (self.source / "projects" / "-project").mkdir(parents=True)
        (self.source / "sessions").mkdir()
        (self.source / "plugins" / "cache").mkdir(parents=True)
        (self.source / "CLAUDE.md").write_text(
            "Read @~/.claude/reports/modifiers.md and ~/.claude/CLAUDE.md.\n",
            encoding="utf-8",
        )
        (self.source / "skills" / "report" / "SKILL.md").write_text(
            "---\nname: report\ndescription: Report.\n---\n"
            "Use ~/.claude/schemas/artefact_frontmatter.md.\n",
            encoding="utf-8",
        )
        (self.source / "hooks" / "check.py").write_text(
            'ROOT = "~/.claude"\n',
            encoding="utf-8",
        )
        (self.source / "projects" / "-project" / "architecture.md").write_text(
            "# Architecture\n",
            encoding="utf-8",
        )
        (self.source / "projects" / "-project" / "transcript.jsonl").write_text(
            "runtime\n",
            encoding="utf-8",
        )
        (self.source / "sessions" / "history.jsonl").write_text(
            "runtime\n",
            encoding="utf-8",
        )
        (self.source / "plugins" / "cache" / "state.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        (self.source / "settings.json").write_text(
            json.dumps(
                {
                    "hooks": {"UserPromptSubmit": []},
                    "permissions": {"allow": ["Read(*)"]},
                    "env": {"SECRET": "must-not-copy"},
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_dry_run_does_not_create_destination_or_modify_source(self):
        before = {
            str(path.relative_to(self.source)): digest(path)
            for path in self.source.rglob("*")
            if path.is_file()
        }
        entries, diagnostics = plan_claude_import(self.source, self.root)
        report, execution = execute_import(
            entries,
            root=self.root,
            source=self.source,
            apply=False,
        )
        after = {
            str(path.relative_to(self.source)): digest(path)
            for path in self.source.rglob("*")
            if path.is_file()
        }

        self.assertEqual(before, after)
        self.assertFalse(self.root.exists())
        self.assertEqual(report["counts"]["new"], len(entries))
        self.assertTrue(any(item.code == "plugins-deferred" for item in diagnostics))
        self.assertEqual(execution, [])

    def test_apply_copies_only_authored_files_and_normalizes_markdown(self):
        entries, diagnostics = plan_claude_import(self.source, self.root)
        report, execution = execute_import(
            entries,
            root=self.root,
            source=self.source,
            apply=True,
        )

        self.assertEqual(
            (self.root / "core" / "instructions.md").read_text(),
            "Read agentic://reports/modifiers.md and agentic://core/instructions.\n",
        )
        self.assertIn(
            "agentic://schemas/artefact_frontmatter.md",
            (self.root / "skills" / "report" / "SKILL.md").read_text(),
        )
        self.assertTrue(
            (self.root / "projects" / "-project" / "architecture.md").exists()
        )
        self.assertFalse(
            (self.root / "projects" / "-project" / "transcript.jsonl").exists()
        )
        self.assertFalse((self.root / "sessions").exists())
        self.assertFalse((self.root / "plugins").exists())
        settings = json.loads(
            (self.root / "imports" / "claude" / "settings-selected.json").read_text()
        )
        self.assertNotIn("env", settings)
        self.assertTrue(any(item.code == "hardcoded-claude-path" for item in diagnostics))
        self.assertEqual(execution, [])
        self.assertGreater(report["counts"]["new"], 0)

    def test_reimport_refuses_to_overwrite_canonical_drift(self):
        entries, _ = plan_claude_import(self.source, self.root)
        execute_import(entries, root=self.root, source=self.source, apply=True)
        canonical = self.root / "core" / "instructions.md"
        canonical_skill = self.root / "skills" / "report" / "SKILL.md"
        original_skill = canonical_skill.read_text()
        canonical.write_text("manual canonical edit\n", encoding="utf-8")
        (self.source / "skills" / "report" / "SKILL.md").write_text(
            "---\nname: report\ndescription: Changed.\n---\n",
            encoding="utf-8",
        )
        entries, _ = plan_claude_import(self.source, self.root)

        _, diagnostics = execute_import(
            entries,
            root=self.root,
            source=self.source,
            apply=True,
        )

        self.assertEqual(canonical.read_text(), "manual canonical edit\n")
        self.assertEqual(canonical_skill.read_text(), original_skill)
        self.assertTrue(any(item.code == "destination-conflict" for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
