import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_config.references import find_references, render_text


class ReferenceTests(unittest.TestCase):
    def test_finds_typed_references_without_consuming_sentence_punctuation(self):
        text = (
            "Read agentic://reports/modifiers.md. "
            "Write to {{ user.reports_dir }} on {{ runtime.current_branch }}."
        )

        references = find_references(text)

        self.assertEqual(
            [(item.kind, item.key) for item in references],
            [
                ("resource", "reports/modifiers.md"),
                ("user", "reports_dir"),
                ("runtime", "current_branch"),
            ],
        )

    def test_escaped_references_are_literal(self):
        text = r"Show \agentic://reports/example and \{{ user.example }}."

        rendered, diagnostics = render_text(
            text,
            resources={},
            values={},
            source="test.md",
        )

        self.assertEqual(
            rendered,
            "Show agentic://reports/example and {{ user.example }}.",
        )
        self.assertEqual(diagnostics, [])

    def test_required_value_fails_while_runtime_value_is_late_bound(self):
        rendered, diagnostics = render_text(
            "{{ user.notes_dir }} {{ runtime.branch }}",
            resources={},
            values={},
            source="test.md",
        )

        self.assertEqual(rendered, "{{ user.notes_dir }} {{ runtime.branch }}")
        self.assertEqual(
            [(item.level, item.code) for item in diagnostics],
            [("error", "unresolved-value"), ("info", "late-bound-value")],
        )

    def test_resource_alias_is_rendered(self):
        rendered, diagnostics = render_text(
            "Read agentic://reports/modifiers.",
            resources={"reports/modifiers": "/target/reports/modifiers.md"},
            values={},
            source="test.md",
        )

        self.assertEqual(rendered, "Read /target/reports/modifiers.md.")
        self.assertEqual(diagnostics, [])

    def test_registered_directory_resolves_dynamic_descendant(self):
        rendered, diagnostics = render_text(
            "Read agentic://projects/<encoded>/architecture.md.",
            resources={"projects": "/target/projects"},
            values={},
            source="test.md",
        )

        self.assertEqual(
            rendered,
            "Read /target/projects/<encoded>/architecture.md.",
        )
        self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
