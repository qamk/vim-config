---
name: message
description: Send an outbound message or notification as a bot to a configured destination (Slack, etc.), or read recent messages from a channel the bot is in. Platform-agnostic — a shared dispatcher resolves a named target and its credential, then hands off to a thin per-platform adapter. Use when asked to post/notify/send to a channel or chat as a bot (not as the user), to alert when something finishes, or to read what's in a channel. Triggers - "message the team", "notify me on Slack", "post this to <channel> as the bot", "send an alert", "read the <channel> channel", "what's in <channel>".
---

# /message

Send messages as a bot to a named destination, or read recent messages from one. Two operations, both bot-scoped (never as the user).

The skill is a thin layer over scripts sharing one core (`scripts/_dispatch.py`) — it resolves a named **target** and its **secret**, then hands a JSON payload to a per-platform **adapter**. Two CLIs sit on top:

- **`scripts/send.py`** — outbound (`op: "send"`): post text and/or files.
- **`scripts/read.py`** — inbound (`op: "read"`): read a channel's recent messages, or a thread's replies.

The dispatcher only understands three universal fields — `name`, `platform`, `secret`. Everything else on a target is platform-specific and passed through untouched for the adapter to interpret.

## Invocation

Run the dispatcher; do not reimplement its logic here.

```
python3 agentic://skills/message/scripts/send.py --target <name> --text "..."
python3 agentic://skills/message/scripts/send.py --target <name> --stdin          # content from stdin (long/multiline)
python3 agentic://skills/message/scripts/send.py --target <name> --file ./shot.png                 # attach a file
python3 agentic://skills/message/scripts/send.py --target <name> --text "caption" --file a.png --file b.png
python3 agentic://skills/message/scripts/send.py --target <name> --text "..." --set channel=#other --set thread_ts=123
python3 agentic://skills/message/scripts/send.py --list                            # show targets (never secrets)
python3 agentic://skills/message/scripts/send.py --target <name> --text "..." --dry-run
```

- `--file <path>` (repeatable) attaches a local file. With `--text` (or `--stdin`) the text becomes the caption; text is optional when files are given. Content is required either way — pass at least one of `--text`/`--stdin`/`--file`.
- `--set key=value` (repeatable) overrides/adds a platform-specific field for this send only. **Posting into a thread:** set `thread_ts` (e.g. `--set thread_ts=1720000000.001`) — works for both text and file sends. It can also live on the target if a bot always posts to one thread.
- `--dry-run` shows the processed payload and which adapter would run, with the **secret masked** — use it to check a target before sending.
- Always prefer `--dry-run` first when sending to a new target.

### Reading (`read.py`)

```
python3 agentic://skills/message/scripts/read.py --target <name>                    # latest messages in the channel
python3 agentic://skills/message/scripts/read.py --target <name> --limit 50
python3 agentic://skills/message/scripts/read.py --target <name> --set thread_ts=1720000000.001   # a thread's replies
python3 agentic://skills/message/scripts/read.py --target <name> --json             # raw message JSON
python3 agentic://skills/message/scripts/read.py --list
python3 agentic://skills/message/scripts/read.py --target <name> --dry-run
```

- Reads the same targets as `send.py`; the bot must be a member of the channel (`/invite @bot`) and hold the platform's history read scope.
- `--limit N` caps how many messages are fetched (default 20); messages print oldest-first as `[ts] user: text`. `--json` emits the structured list instead.
- `--set thread_ts=<ts>` reads that thread's replies rather than the channel.

## Targets config

Targets live in `message_targets.md` files, layered (both optional):

- **User-level** (cross-project bots): `agentic://references/message_targets`
- **Project-level** (per-repo): `agentic://projects/<encoded-cwd>/message_targets.md`

The dispatcher loads the user file, then merges the project file; **project wins** on a name collision. `<encoded-cwd>` is the cwd with every `/` replaced by `-`.

Targets are a **YAML block-list of flat dicts** inside the frontmatter (parsed by the shared stdlib parser — one level of nesting only, so do not nest dicts):

```markdown
---
targets:
  - name: e2e-screenshots
    platform: slack
    secret: op://Private/slack-e2e-bot/token
    channel: C0BEB4H5GAV
    display_name: E2E Bot      # optional; needs chat:write.customize
    icon: ":camera:"           # optional
    guidelines: "Start a new thread per test run; post screenshots and follow-ups as replies."  # optional; see below
  - name: deploy-bot
    platform: slack
    secret: env:SLACK_DEPLOY_TOKEN
    channel: "#deploys"        # quote any value starting with # (a bare # reads as a comment)
---

# Message targets   ← human notes go below the frontmatter
```

Only `name`, `platform`, `secret` are universal. `channel`, `display_name`, `icon`, `thread_ts`, … are Slack-specific and interpreted by the Slack adapter. `guidelines` is agent-facing metadata (see below) — the one other field the dispatcher recognises.

## Per-target guidelines

A target may carry an optional `guidelines` field: a short, one-line string describing how *you* (the model) should compose and deliver messages to that target. They are **guidelines, not rules** — habits to follow unless the user's request gives you reason to do otherwise. The user can always prompt in defiance of them, and that is fine.

- **Agent-facing, not platform-facing.** Guidelines are surfaced back to you, **never** sent to the adapter, and never affect delivery mechanics. They shape *what* you send and *how you structure a conversation*, not how the platform transmits it.
- **Always surfaced on use.** You never read `message_targets.md` yourself — the dispatcher parses it — so guidelines reach you only when a script prints them. They appear in `--list` and `--dry-run`, **and on every live `send`/`read`** they are echoed to **stderr** (`guidelines for <name>: …`), so a bare invocation that skips `--dry-run` still shows them. The stderr note is advisory: it never touches the payload or the stdout result line.
- **How to honour them.** Follow a target's guidelines by default — e.g. capture a posted message's `ts` from the result and thread subsequent sends under it with `--set thread_ts=<ts>`. If the user asks for something that conflicts, the user wins; note the deviation if it's material.
- **One line only.** The frontmatter parser has no multi-line scalars, so keep `guidelines` to a single quoted string. Avoid a literal `#` (it reads as a trailing comment). For multi-clause guidance, join clauses with `;`.

Example: `e2e-reviewer` carries a guideline to start a fresh thread per test run — a summary as the root message, with screenshots and follow-ups posted as replies in that thread — which formalises the E2E review-comms convention.

## Secret references

`secret` is a reference, **never a raw token**. Schemes:

| Scheme | Resolves to |
|---|---|
| `op://Vault/item/field` | 1Password via `op read` |
| `env:NAME` | environment variable |
| `file:~/path` | file contents (trimmed) |
| `none` | no token (the adapter decides if that is acceptable) |

An omitted, unknown, or raw-token value is rejected — which also stops a live token being committed to a targets file. Each target picks its own scheme; storage is not forced to unify.

## Adding a platform (adapter)

An adapter is any **OS-executable file** at `scripts/adapters/<platform>` (extensionless binary) or `scripts/adapters/<platform>.<ext>`. The contract is a process boundary, not a language. The `op` field selects the operation — `"send"` (default if absent) or `"read"`:

- **stdin:** `{ "secret": <token|null>, "op": "send"|"read", "text": <string>, "files": [<abs path>, …], "target": {<platform fields>}, "options": {<op params, e.g. "limit">} }` — `files` is a (possibly empty) list of absolute paths; an adapter that does not support attachments (or the `read` op) ignores or rejects what it can't do.
- **stdout (send):** `{ "ok": true, "id": "<id>", "permalink": "<url>" }`
- **stdout (read):** `{ "ok": true, "messages": [ { "ts": …, "user": …, "text": … }, … ] }`
- **stdout (error):** `{ "ok": false, "error": "<reason>" }`
- **exit:** `0` on success, non-zero on failure.

A `send`-only adapter can simply fail on `op: "read"`; only `name`/`platform`/`secret` and this contract are mandatory. Make it executable (`chmod +x` + a shebang) and it can be Python, bash, node, Ruby, a compiled binary, anything. As a convenience, a non-executable `.py`/`.sh`/`.js` adapter is still run via the matching interpreter. Adding a platform requires **no dispatcher changes** — drop in the adapter and a target entry.

## Security

- Secrets travel on the adapter's **stdin, never argv** — kept out of `ps` and shell history.
- Tokens are **never printed or logged**; `--list` and `--dry-run` mask them.
- Targets files hold **references, not tokens**, so they are safe to commit.
- `op://` needs an authenticated `op` CLI; if it is signed out the dispatcher says so.
- **Slack:** the bot must be **invited to a channel** (including private: `/invite @bot`) before it can post there or read it, and needs the `chat:write` scope (`chat:write.customize` for `display_name`/`icon`). **Sending files** additionally needs `files:write`; the channel must be a **channel ID** (`C…`/`G…`), not a `#name`, and `display_name`/`icon` are ignored (uploads post under the bot's own identity). **Reading** needs the matching history scope — `channels:history` (public) or `groups:history` (private).

## Tests

`python3 agentic://skills/message/scripts/test_message.py`
