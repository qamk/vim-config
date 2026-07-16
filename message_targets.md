---
targets:
  - name: e2e-reviewer
    platform: slack
    secret: env:SLACK_E2E_REVIEWER_TOKEN
    channel: C0BEB4H5GAV
    guidelines: "Start a new thread per test run: post a one-message summary as the root, then attach screenshots and post any follow-ups as replies in that thread (capture the root ts and pass --set thread_ts=<ts>)."
---

# Message targets (user-level)

Cross-project `/message` targets.

- `e2e-reviewer` → E2E review channel (Slack `C0BEB4H5GAV`). Token from
  `SLACK_E2E_REVIEWER_TOKEN` (auto-loaded into the Bash shell via ~/.zshenv).
  Carries a `guidelines` note (thread-per-test-run containment) — soft guidance
  surfaced in `--list`/`--dry-run`; see the skill's "Per-target guidelines".
