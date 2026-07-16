#!/usr/bin/env python3
"""Slack adapter for the /message skill.

Reads a JSON payload on stdin, posts via Slack's Web API, and writes a JSON
result on stdout. Pure stdlib (urllib).

The ``op`` field selects the operation (default ``"send"``):

  send, no files -> chat.postMessage (plain text; supports display_name/icon)
  send, files    -> the external-upload flow (files.getUploadURLExternal ->
                    POST bytes to the returned URL -> files.completeUploadExternal),
                    with ``text`` used as the file's initial_comment.
  read           -> conversations.history for the channel, or
                    conversations.replies when ``thread_ts`` is set.

Payload (stdin):
  {
    "secret": "<bot token xoxb-...>" | null,
    "op":     "send" | "read",              # defaults to "send" if absent
    "text":   "<message text / caption>",   # send: optional when files given
    "files":  ["/abs/path/one.png", ...],   # send: optional; absolute paths
    "target": { "channel": "...", "display_name": "...", "icon": "...",
                "thread_ts": "..." },   # all but "channel" optional
    "options": { "limit": 20 }              # read: max messages
  }

Result (stdout):
  send: { "ok": true, "id": "<ts|file_id>", "permalink": "<url>" }
  read: { "ok": true, "messages": [ { "ts": ..., "user": ..., "text": ... }, ... ] }
        { "ok": false, "error": "<reason>" }

Requires a Slack app bot token with `chat:write` (and `chat:write.customize`
to use display_name/icon). Sending files additionally needs `files:write`;
reading needs the matching history scope (`channels:history` for public
channels, `groups:history` for private). The bot must be a member of the
target channel (including private channels: `/invite @bot`). For file uploads
the channel must be a channel ID (C…/G…), not a #name, and display_name/icon
are ignored (Slack posts uploads under the bot's own identity).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://slack.com/api"

# Fixed multipart boundary — stdlib has no random available here, and the
# upload endpoint only cares that the boundary matches the Content-Type header.
_BOUNDARY = "----messageskillMIMEboundaryZ9x7Qk"


def _emit(result: dict) -> None:
    sys.stdout.write(json.dumps(result))


def fail(message: str) -> None:
    _emit({"ok": False, "error": message})
    sys.exit(1)


def _call(method: str, token: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{API}/{method}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_form(method: str, token: str, params: dict) -> dict:
    """GET a Slack method with query params (used by getUploadURLExternal)."""
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{API}/{method}?{qs}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _multipart(filename: str, content: bytes) -> bytes:
    """Build a minimal multipart/form-data body wrapping one file."""
    return b"".join(
        [
            f"--{_BOUNDARY}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; '
                f'filename="{filename}"\r\n'
            ).encode(),
            b"Content-Type: application/octet-stream\r\n\r\n",
            content,
            f"\r\n--{_BOUNDARY}--\r\n".encode(),
        ]
    )


def _upload_files(token: str, paths: list[str]) -> list[dict]:
    """Upload each file's bytes and return [{id, title}] for completion."""
    uploaded: list[dict] = []
    for path in paths:
        filename = os.path.basename(path)
        try:
            with open(path, "rb") as fh:
                content = fh.read()
        except OSError as exc:
            fail(f"cannot read file {path!r}: {exc}")

        info = _call_form(
            "files.getUploadURLExternal",
            token,
            {"filename": filename, "length": len(content)},
        )
        if not info.get("ok"):
            fail(f"slack files.getUploadURLExternal error: {info.get('error', 'unknown')}")

        req = urllib.request.Request(
            info["upload_url"],
            data=_multipart(filename, content),
            headers={"Content-Type": f"multipart/form-data; boundary={_BOUNDARY}"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as exc:
            fail(f"slack file upload HTTP {exc.code}: {exc.reason}")
        except urllib.error.URLError as exc:
            fail(f"slack file upload failed: {exc.reason}")

        uploaded.append({"id": info["file_id"], "title": filename})
    return uploaded


def _send_files(token: str, channel: str, text: str, target: dict, files: list[str]) -> None:
    """Upload files, then post them into the channel as a single message."""
    uploaded = _upload_files(token, files)

    body: dict = {"files": uploaded, "channel_id": channel}
    if text:
        body["initial_comment"] = text
    if target.get("thread_ts"):
        body["thread_ts"] = target["thread_ts"]

    try:
        data = _call("files.completeUploadExternal", token, body)
    except urllib.error.HTTPError as exc:
        fail(f"slack HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        fail(f"slack request failed: {exc.reason}")

    if not data.get("ok"):
        fail(f"slack API error: {data.get('error', 'unknown')}")

    posted = data.get("files") or []
    first = posted[0] if posted else {}
    result = {"ok": True, "id": first.get("id") or uploaded[0]["id"]}
    if first.get("permalink"):
        result["permalink"] = first["permalink"]
    _emit(result)


# Fields kept from each Slack message; the rest of the (large) object is dropped.
_MSG_FIELDS = ("ts", "user", "username", "bot_id", "subtype", "text", "thread_ts")


def _read_channel(token: str, channel: str, target: dict, options: dict) -> None:
    """Read recent messages (or a thread's replies) and emit them chronologically."""
    limit = int(options.get("limit") or 20)
    thread_ts = target.get("thread_ts")

    params = {"channel": channel, "limit": limit}
    if thread_ts:
        params["ts"] = thread_ts
        method = "conversations.replies"
    else:
        method = "conversations.history"

    try:
        data = _call_form(method, token, params)
    except urllib.error.HTTPError as exc:
        fail(f"slack HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        fail(f"slack request failed: {exc.reason}")

    if not data.get("ok"):
        fail(f"slack API error: {data.get('error', 'unknown')}")

    # Slack returns newest-first; present oldest-first and keep only useful fields.
    raw = data.get("messages") or []
    messages = [
        {k: m[k] for k in _MSG_FIELDS if k in m}
        for m in reversed(raw)
    ]
    _emit({"ok": True, "messages": messages})


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        fail(f"invalid JSON payload on stdin: {exc}")

    token = payload.get("secret")
    if not token:
        fail("slack requires a bot token, but the target's secret resolved to none")

    op = payload.get("op") or "send"
    text = payload.get("text") or ""
    files = payload.get("files") or []

    target = payload.get("target") or {}
    channel = target.get("channel")
    if not channel:
        fail("slack target needs a 'channel' (channel id like C0… or #name)")

    if op == "read":
        _read_channel(token, channel, target, payload.get("options") or {})
        return
    if op != "send":
        fail(f"slack adapter does not support op {op!r} (expected 'send' or 'read')")

    if files:
        _send_files(token, channel, text, target, files)
        return

    if not text:
        fail("slack requires non-empty 'text' (or one or more 'files')")

    body: dict = {"channel": channel, "text": text}
    if target.get("display_name"):
        body["username"] = target["display_name"]
    icon = target.get("icon")
    if icon:
        body["icon_emoji" if str(icon).startswith(":") else "icon_url"] = icon
    if target.get("thread_ts"):
        body["thread_ts"] = target["thread_ts"]

    try:
        data = _call("chat.postMessage", token, body)
    except urllib.error.HTTPError as exc:
        fail(f"slack HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        fail(f"slack request failed: {exc.reason}")

    if not data.get("ok"):
        fail(f"slack API error: {data.get('error', 'unknown')}")

    ts = data.get("ts")
    posted_channel = data.get("channel", channel)
    result = {"ok": True, "id": ts}

    # Best-effort permalink; non-fatal if it fails.
    try:
        link = _call(
            "chat.getPermalink", token, {"channel": posted_channel, "message_ts": ts}
        )
        if link.get("ok") and link.get("permalink"):
            result["permalink"] = link["permalink"]
    except (urllib.error.URLError, json.JSONDecodeError):
        pass

    _emit(result)


if __name__ == "__main__":
    main()
