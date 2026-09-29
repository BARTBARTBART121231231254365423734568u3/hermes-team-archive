#!/usr/bin/env python3
"""Debounces the github-push webhook so a burst of rapid pushes to the same
repo spawns at most one security-review kanban task per cooldown window,
instead of one per push. Several concurrent review sessions (plus whatever
else is already running) hitting the same Claude account at once was
tripping Anthropic's request-rate limit, independent of total plan usage.

Generic across repos: state is keyed by repository full_name, so any
project using this webhook gets the same protection, not just one.
"""
import json
import sys
import time
from pathlib import Path

COOLDOWN_SECONDS = 600  # at most one review per repo per 10 minutes

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "webhook_throttle_github_push.json"


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    body = payload.get("payload", payload) if isinstance(payload, dict) else {}
    repo = "unknown"
    if isinstance(body, dict):
        repo = (body.get("repository") or {}).get("full_name") or "unknown"

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    except (json.JSONDecodeError, OSError):
        state = {}

    now = time.time()
    last = state.get(repo, 0)

    if now - last < COOLDOWN_SECONDS:
        print("[SILENT]")
        return

    state[repo] = now
    try:
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass

    # Let it through with the payload unchanged.
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
