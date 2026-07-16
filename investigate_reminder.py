#!/usr/bin/env python3
"""UserPromptSubmit hook: detects phrasing that signals /investigate intent
(ticket / incident investigation) and injects a reminder to invoke the skill.

Triggers on either:
  - An explicit ticket reference (gh:/github:/jira:/linear:/pylon: prefix,
    or a bare uppercase ticket code like PROJ-1234), OR
  - An investigate verb AND an incident noun co-occurring in the prompt.

Fast path: single stdin read, compiled regexes, early exit on no match.
"""
from __future__ import annotations

import json
import re
import sys

# Explicit ticket refs (case-insensitive source prefix, case-sensitive bare codes).
_TICKET_REF_PREFIXED = re.compile(
    r"\b(?:gh|github|jira|linear|pylon):[\w/#\-]+\b",
    re.IGNORECASE,
)
_TICKET_REF_CODE = re.compile(r"\b[A-Z]{3,}-\d{2,}\b")

# Investigate verbs — must co-occur with an incident noun to trigger.
_VERB = re.compile(
    r"\b(?:investigate|look\s+into|dig\s+into|figure\s+out\s+why|"
    r"root[-\s]?cause|RCA|diagnose)\b",
    re.IGNORECASE,
)

# Incident / failure-context nouns.
_NOUN = re.compile(
    r"(?:"
    r"\b(?:ticket|issue|bug|incident|failure|outage|error|broken)\b"
    r"|\bnot\s+working\b"
    # "cannot sign in", "can't log in", "unable to authenticate", etc.
    r"|\b(?:cannot|can'?t|unable\s+to)\s+"
    r"(?:sign\s+in|log\s+in|login|access|connect|reach|authenticate|load)\b"
    # "user X cannot/can't/unable ..." within a short window (catches "user that cannot")
    r"|\buser\b.{0,40}?\b(?:cannot|can'?t|unable)\b"
    r")",
    re.IGNORECASE,
)

_REMINDER = (
    "The user's prompt looks like a ticket or incident investigation. "
    "Consider invoking `/investigate <ticket-ref-or-description>` — the skill "
    "runs complexity verification, checks for a matching playbook via `/lookup`, "
    "then drives structured evidence gathering and recommends `/note`, "
    "`/report`, and `/playbook` downstream. Skip this reminder if the "
    "investigation is already in progress or does not need structured output."
)


def _should_trigger(prompt: str) -> bool:
    if _TICKET_REF_PREFIXED.search(prompt):
        return True
    if _TICKET_REF_CODE.search(prompt):
        return True
    return bool(_VERB.search(prompt) and _NOUN.search(prompt))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input — never block

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str) or not prompt:
        return 0

    if not _should_trigger(prompt):
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
