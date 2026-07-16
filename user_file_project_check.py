#!/usr/bin/env python3
"""PostToolUse hook: warn when Write/Edit to ~/.claude/ (non-projects) contains project-specific language.

Patterns are loaded from the current project's terms file at:
  ~/.claude/projects/<encoded-cwd>/project_terms.txt

This file is populated by /init-project during project setup.
If no terms file exists for the current project, the hook does nothing.
"""

import json
import os
import re
import sys

CLAUDE_DIR = os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")


def _encode_cwd(cwd: str) -> str:
    return cwd.replace("/", "-")


def _find_patterns_file() -> str | None:
    cwd = os.getcwd()
    encoded = _encode_cwd(cwd)
    candidate = os.path.join(PROJECTS_DIR, encoded, "project_terms.txt")
    if os.path.isfile(candidate):
        return candidate
    return None


def load_patterns() -> list[re.Pattern]:
    path = _find_patterns_file()
    if not path:
        return []
    patterns = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                patterns.append(re.compile(line, re.IGNORECASE))
            except re.error:
                pass
    return patterns


def main() -> None:
    raw = sys.stdin.read()
    if not raw:
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return

    file_path = os.path.expanduser(file_path)

    if not file_path.startswith(CLAUDE_DIR + "/"):
        return
    if file_path.startswith(PROJECTS_DIR + "/"):
        return

    tool = data.get("tool_name", "")
    if tool == "Write":
        content = data.get("tool_input", {}).get("content", "")
    elif tool == "Edit":
        content = data.get("tool_input", {}).get("new_string", "")
    else:
        return

    if not content:
        return

    patterns = load_patterns()
    if not patterns:
        return

    matches = []
    for pat in patterns:
        found = pat.findall(content)
        if found:
            matches.append((pat.pattern, found[:3]))

    if not matches:
        return

    details = "; ".join(f"'{p}' matched {m}" for p, m in matches[:5])
    msg = (
        f"User-level file contains project-specific language: {details}. "
        f"Files under ~/.claude/ (excluding projects/) must use generic placeholder examples. "
        f"Edit the project's project_terms.txt to manage patterns."
    )

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
