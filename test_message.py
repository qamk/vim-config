"""Stdlib unittest suite for the /message dispatcher and secret resolver.

Run:  python3 -m unittest discover -s ~/.claude/skills/message/scripts
  or: python3 ~/.claude/skills/message/scripts/test_message.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import read  # noqa: E402
import send  # noqa: E402
from _secrets import SecretError, resolve_secret  # noqa: E402


class SecretResolutionTests(unittest.TestCase):
    def test_none_scheme_returns_none(self):
        self.assertIsNone(resolve_secret("none"))

    def test_env_scheme(self):
        os.environ["MSG_TEST_TOKEN"] = "xoxb-from-env"
        try:
            self.assertEqual(resolve_secret("env:MSG_TEST_TOKEN"), "xoxb-from-env")
        finally:
            del os.environ["MSG_TEST_TOKEN"]

    def test_env_scheme_unset_raises(self):
        os.environ.pop("MSG_TEST_ABSENT", None)
        with self.assertRaises(SecretError):
            resolve_secret("env:MSG_TEST_ABSENT")

    def test_file_scheme(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("  xoxb-from-file\n")
            name = fh.name
        try:
            self.assertEqual(resolve_secret(f"file:{name}"), "xoxb-from-file")
        finally:
            os.unlink(name)

    def test_file_scheme_missing_raises(self):
        with self.assertRaises(SecretError):
            resolve_secret("file:/no/such/path/secret.txt")

    def test_omitted_raises(self):
        with self.assertRaises(SecretError):
            resolve_secret(None)
        with self.assertRaises(SecretError):
            resolve_secret("   ")

    def test_unknown_scheme_and_raw_token_rejected(self):
        with self.assertRaises(SecretError):
            resolve_secret("xoxb-pasted-raw-token")
        with self.assertRaises(SecretError):
            resolve_secret("vault:foo/bar")


class TargetShapingTests(unittest.TestCase):
    def test_split_target_separates_core_and_blob(self):
        target = {
            "name": "deploy",
            "platform": "slack",
            "secret": "env:X",
            "channel": "#deploys",
            "display_name": "Deploy Bot",
        }
        core, blob = send.split_target(target)
        self.assertEqual(core, {"name": "deploy", "platform": "slack", "secret": "env:X"})
        self.assertEqual(blob, {"channel": "#deploys", "display_name": "Deploy Bot"})

    def test_split_target_folds_guidelines_into_core_not_blob(self):
        target = {
            "name": "reviewer",
            "platform": "slack",
            "secret": "env:X",
            "channel": "C123",
            "guidelines": "Start a new thread per run; reply with follow-ups.",
        }
        core, blob = send.split_target(target)
        self.assertEqual(core["guidelines"], target["guidelines"])
        # Agent-facing metadata must never reach the adapter payload.
        self.assertNotIn("guidelines", blob)
        self.assertEqual(blob, {"channel": "C123"})

    def test_split_target_omits_absent_guidelines(self):
        core, blob = send.split_target(
            {"name": "d", "platform": "slack", "secret": "env:X", "channel": "C1"}
        )
        self.assertNotIn("guidelines", core)
        self.assertNotIn("guidelines", blob)

    def test_apply_overrides_rejects_guidelines(self):
        with self.assertRaises(ValueError):
            send.apply_overrides({}, ["guidelines=do something else"])

    def test_note_guidelines_writes_to_stderr_only(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            send.note_guidelines({"name": "reviewer", "guidelines": "thread per run"})
        self.assertIn("guidelines for reviewer: thread per run", err.getvalue())
        self.assertEqual(out.getvalue(), "")  # never pollutes the result stream

    def test_note_guidelines_silent_when_absent(self):
        import io
        from contextlib import redirect_stderr

        err = io.StringIO()
        with redirect_stderr(err):
            send.note_guidelines({"name": "d", "platform": "slack"})
        self.assertEqual(err.getvalue(), "")

    def test_apply_overrides_adds_and_replaces(self):
        blob = {"channel": "#a"}
        out = send.apply_overrides(blob, ["channel=#b", "thread_ts=123"])
        self.assertEqual(out, {"channel": "#b", "thread_ts": "123"})
        # original untouched
        self.assertEqual(blob, {"channel": "#a"})

    def test_apply_overrides_bad_format_raises(self):
        with self.assertRaises(ValueError):
            send.apply_overrides({}, ["nokey"])
        with self.assertRaises(ValueError):
            send.apply_overrides({}, ["=value"])

    def test_apply_overrides_rejects_core_keys(self):
        for key in ("name", "platform", "secret"):
            with self.assertRaises(ValueError):
                send.apply_overrides({}, [f"{key}=whatever"])

    def test_build_payload_shape(self):
        payload = send.build_payload("tok", "hi", {"channel": "C1"})
        self.assertEqual(
            payload,
            {
                "secret": "tok",
                "op": "send",
                "text": "hi",
                "files": [],
                "target": {"channel": "C1"},
                "options": {},
            },
        )

    def test_build_payload_carries_files(self):
        payload = send.build_payload("tok", "", {"channel": "C1"}, ["/tmp/a.png"])
        self.assertEqual(payload["files"], ["/tmp/a.png"])
        self.assertEqual(payload["text"], "")
        self.assertEqual(payload["op"], "send")

    def test_build_read_payload_shape(self):
        payload = read.build_payload("tok", {"channel": "C1"}, 50)
        self.assertEqual(
            payload,
            {
                "secret": "tok",
                "op": "read",
                "text": "",
                "files": [],
                "target": {"channel": "C1"},
                "options": {"limit": 50},
            },
        )


def _write_targets(path: Path, entries_yaml: str) -> None:
    path.write_text(
        "---\n" + textwrap.dedent(entries_yaml).strip("\n") + "\n---\n\n# notes\n"
    )


class ConfigLoadingTests(unittest.TestCase):
    def test_layered_merge_project_wins(self):
        with tempfile.TemporaryDirectory() as d:
            user = Path(d) / "user.md"
            project = Path(d) / "project.md"
            _write_targets(
                user,
                """
                targets:
                  - name: personal
                    platform: slack
                    secret: env:U
                    channel: CU
                  - name: shared
                    platform: slack
                    secret: env:US
                    channel: CUS
                """,
            )
            _write_targets(
                project,
                """
                targets:
                  - name: shared
                    platform: slack
                    secret: env:PS
                    channel: CPS
                  - name: repo-only
                    platform: slack
                    secret: none
                    channel: CR
                """,
            )
            merged = send.load_targets(user, project)
            self.assertEqual(set(merged), {"personal", "shared", "repo-only"})
            # project entry wins on name clash
            self.assertEqual(merged["shared"]["channel"], "CPS")
            self.assertEqual(merged["shared"]["secret"], "env:PS")

    def test_missing_files_yield_empty(self):
        with tempfile.TemporaryDirectory() as d:
            merged = send.load_targets(Path(d) / "nope.md", Path(d) / "also-nope.md")
            self.assertEqual(merged, {})


class AdapterResolutionTests(unittest.TestCase):
    def test_executable_runs_directly(self):
        with tempfile.TemporaryDirectory() as d:
            ad = Path(d)
            f = ad / "slack"
            f.write_text("#!/usr/bin/env bash\necho '{\"ok\":true}'\n")
            os.chmod(f, 0o755)
            self.assertEqual(send.resolve_adapter_cmd(ad, "slack"), [str(f)])

    def test_non_executable_py_uses_interpreter(self):
        with tempfile.TemporaryDirectory() as d:
            ad = Path(d)
            f = ad / "slack.py"
            f.write_text("print('{}')\n")  # not chmod +x
            cmd = send.resolve_adapter_cmd(ad, "slack")
            self.assertEqual(cmd[-1], str(f))
            self.assertIn("python", cmd[0].lower())

    def test_missing_adapter_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(send.AdapterError):
                send.resolve_adapter_cmd(Path(d), "whatsapp")

    def test_non_executable_unknown_ext_raises(self):
        with tempfile.TemporaryDirectory() as d:
            ad = Path(d)
            (ad / "slack.rb").write_text("puts '{}'\n")  # not chmod, unknown ext
            with self.assertRaises(send.AdapterError):
                send.resolve_adapter_cmd(ad, "slack")


class InvokeAdapterTests(unittest.TestCase):
    def _make_adapter(self, d: str, script: str) -> list[str]:
        f = Path(d) / "fake.py"
        f.write_text(script)
        return [sys.executable, str(f)]

    def test_parses_ok_result(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = self._make_adapter(
                d,
                "import json,sys; json.load(sys.stdin);"
                " print(json.dumps({'ok': True, 'id': '123.45'}))",
            )
            result = send.invoke_adapter(cmd, send.build_payload("t", "hi", {}))
            self.assertTrue(result["ok"])
            self.assertEqual(result["id"], "123.45")

    def test_parses_read_messages_result(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = self._make_adapter(
                d,
                "import json,sys; json.load(sys.stdin);"
                " print(json.dumps({'ok': True,"
                " 'messages': [{'ts': '1.0', 'user': 'U1', 'text': 'hi'}]}))",
            )
            result = send.invoke_adapter(cmd, read.build_payload("t", {}, 20))
            self.assertTrue(result["ok"])
            self.assertEqual(result["messages"][0]["text"], "hi")

    def test_empty_output_raises(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = self._make_adapter(d, "import sys; sys.exit(3)")
            with self.assertRaises(send.AdapterError):
                send.invoke_adapter(cmd, send.build_payload("t", "hi", {}))

    def test_malformed_output_raises(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = self._make_adapter(d, "print('not json')")
            with self.assertRaises(send.AdapterError):
                send.invoke_adapter(cmd, send.build_payload("t", "hi", {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
