#!/usr/bin/env python3
"""Retry only explicitly transient failures, with cooldown and a lifetime cap."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

ROOT = Path(os.environ.get("HERMES_OPS_HOME", Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "hermes"))
COOLDOWN = 1800
MAX_RETRIES = 2


def eligible(task, record, now):
    if task["status"] != "blocked" or task["block_kind"] != "transient":
        return False
    attempts = record.get("attempts", 0)
    return attempts < MAX_RETRIES and now - record.get("last_attempt", task["blocked_at"] or now) >= COOLDOWN * (2 ** attempts)


def main():
    state_dir = ROOT / "ops"
    state_dir.mkdir(exist_ok=True, mode=0o700)
    with (state_dir / "retry.lock").open("w") as lock:
        if os.name != "nt":
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_file = state_dir / "retry-state.json"
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        with sqlite3.connect(f"file:{ROOT / 'kanban.db'}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            tasks = connection.execute("""SELECT t.id,t.status,t.block_kind,
                (SELECT MAX(created_at) FROM task_events WHERE task_id=t.id AND kind='blocked') AS blocked_at
                FROM tasks t WHERE t.status='blocked'""").fetchall()
        now = time.time()
        retried = []
        for task in tasks:
            record = state.get(task["id"], {})
            if not eligible(task, record, now):
                continue
            # Persist intent before invoking the CLI: a crash must not erase retry limits.
            state[task["id"]] = {"attempts": record.get("attempts", 0) + 1, "last_attempt": now}
            temporary = state_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(state))
            temporary.replace(state_file)
            result = subprocess.run(["hermes", "kanban", "unblock", task["id"], "--reason",
                                     "Bounded transient recovery after cooldown"], capture_output=True, text=True, timeout=45)
            if result.returncode == 0:
                retried.append(task["id"])
            # At most one retry per pass: do not create a burst after provider recovery.
            break
        print(json.dumps({"retried": retried, "policy": "transient-only; two retries maximum"}))


if __name__ == "__main__":
    main()
