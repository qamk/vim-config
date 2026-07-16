import tempfile
import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_config.targets import load_target


class TargetTests(unittest.TestCase):
    def test_unmapped_features_are_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "partial.toml"
            path.write_text(
                """
[target]
id = "partial"
adapter = "test"
schema_version = 1

[features.instructions]
status = "native"
destination = "/tmp/instructions.md"
""",
                encoding="utf-8",
            )

            target, diagnostics = load_target(path)

        self.assertIsNotNone(target)
        unmapped = [item for item in diagnostics if item.code == "unmapped-feature"]
        self.assertEqual(len(unmapped), 8)

    def test_repository_targets_have_complete_coverage(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("claude", "codex"):
            with self.subTest(name=name):
                target, diagnostics = load_target(root / "targets" / f"{name}.toml")
                self.assertIsNotNone(target)
                self.assertEqual(
                    [item for item in diagnostics if item.level == "error"],
                    [],
                )
                self.assertEqual(target.coverage()["unmapped"], [])


if __name__ == "__main__":
    unittest.main()

