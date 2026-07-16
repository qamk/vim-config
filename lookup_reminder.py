#!/usr/bin/env python3
"""UserPromptSubmit hook: detects phrasing that signals /lookup intent and
injects a reminder to invoke the skill before reaching for Read/ls/find.

Fast path: single stdin read, compiled regex union, early exit on no match.
"""
from __future__ import annotations

import json
import re
import sys

# Patterns that signal the user is asking about a prior artefact
# (note / report / playbook / ground-audit) rather than arbitrary work.
_ARTEFACT = r"(?:note|plan|report|playbook|investigation|ground[- ]?audit|audit|finding)"

_PATTERNS = [
    # "read the note", "pull up the report", "find that playbook"
    rf"\b(?:read|review|find|pull\s+up|grab|fetch|show\s+me|open)\s+(?:the|that|my|our|a|an)?\s*{_ARTEFACT}s?\b",
    # "prior investigation", "previous finding", "earlier note"
    rf"\b(?:prior|previous|earlier|past|existing)\s+{_ARTEFACT}s?\b",
    # "the note that created/informed/led to X"
    rf"\b{_ARTEFACT}\s+that\s+(?:created|informed|produced|led|generated|described|documented|inspired|started)\b",
    # "the note on/about/for/related to X"
    rf"\bthe\s+{_ARTEFACT}s?\s+(?:on|about|for|related\s+to|concerning|regarding|from)\b",
    # "what did we write/say/decide/find/document about X"
    r"\bwhat\s+(?:did|have|do)\s+we\s+(?:write|wrote|say|said|decide|decided|find|found|learn|learned|discover|discovered|note|noted|document|documented|conclude|concluded)\b",
    # "look up X" / "lookup X" / "look this up"
    r"\blook(?:ed)?\s+(?:up|this\s+up|that\s+up)\b|\blookup\b",
    # "refer to the note" / "check the playbook"
    rf"\b(?:refer\s+to|check|consult|reference)\s+(?:the|that|my|our|a|an)?\s*{_ARTEFACT}s?\b",
]

_TRIGGER = re.compile("|".join(_PATTERNS), re.IGNORECASE)

_REMINDER = (
    "The user's prompt looks like it references a prior artefact (note, report, "
    "playbook, or ground-audit). Before reaching for filesystem tools (Read, ls, "
    "Glob, Grep) to locate it by path, invoke the /lookup skill — it searches the "
    "unified artefact index across $NOTES_DIR, $REPORTS_DIR, $PLAYBOOKS_DIR by "
    "keyword/ticket/scope and is the correct first step. Skip this reminder only "
    "if the exact path is already known."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input — never block

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str) or not prompt:
        return 0

    if not _TRIGGER.search(prompt):
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": _REMINDER,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
