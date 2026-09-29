#!/usr/bin/env python3
"""No-agent cron script: enforces a retention policy on kanban scratch workspaces.

Every kanban task gets an isolated workspace at
~/.hermes/kanban/workspaces/<task_id> (for tasks created with the default
workspace_kind='scratch' -- 'dir' and 'worktree' tasks point at persistent
paths elsewhere and are never touched here). Nothing currently deletes these
once a task finishes, so they accumulate indefinitely -- a single afternoon
of BiteWise redesign work left 2.3GB behind and filled the volume to 100%.

Two independent rules, mirroring clean_previews.py:
  1. Age: delete a done task's scratch workspace once it's been done longer
     than RETENTION_SECONDS.
  2. Size: if the store still exceeds MAX_BYTES after the age sweep, delete
     oldest-completed-first until back under the cap -- a backstop against a
     burst of large workspaces filling disk between daily runs.

Only ever touches a workspace whose task is status='done' AND
workspace_kind='scratch' in kanban.db -- running/ready/blocked/triage tasks
and dir/worktree workspaces are never candidates, regardless of size or age.

Runs as a pure script (no LLM call) so it keeps working even if the account
is rate-limited. Prints a summary only when it actually removed something;
empty stdout is treated as "nothing to do" by the cron runner.
"""
import os
import shutil
import sqlite3
import time

HERMES_HOME = os.environ.get(
    "HERMES_OPS_HOME",
    os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local")), "hermes"),
)
KANBAN_DB = os.path.join(HERMES_HOME, "kanban.db")
WORKSPACES_DIR = os.path.join(HERMES_HOME, "kanban", "workspaces")
RETENTION_SECONDS = 2 * 86400
MAX_BYTES = 3 * 1024 * 1024 * 1024  # 3 GB


def dir_size(path: str) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for name in filenames:
            fp = os.path.join(dirpath, name)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def done_scratch_workspaces():
    """(task_id, workspace_dir, completed_at) for every done+scratch task
    whose workspace directory actually still exists on disk."""
    con = sqlite3.connect(f"file:{KANBAN_DB}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, completed_at FROM tasks "
            "WHERE status = 'done' AND workspace_kind = 'scratch'"
        )
        rows = cur.fetchall()
    finally:
        con.close()

    out = []
    for task_id, completed_at in rows:
        path = os.path.join(WORKSPACES_DIR, task_id)
        if os.path.isdir(path):
            out.append((task_id, path, completed_at or 0))
    return out


def main() -> None:
    if not os.path.isdir(WORKSPACES_DIR) or not os.path.isfile(KANBAN_DB):
        return

    now = time.time()
    candidates = done_scratch_workspaces()

    removed = []
    remaining = []
    for task_id, path, completed_at in candidates:
        if now - completed_at > RETENTION_SECONDS:
            shutil.rmtree(path, ignore_errors=True)
            removed.append((task_id, "expired"))
        else:
            remaining.append((task_id, path, completed_at))

    remaining.sort(key=lambda e: e[2])
    sized = [(task_id, path, dir_size(path)) for task_id, path, _ in remaining]
    total = sum(size for _, _, size in sized)
    i = 0
    while total > MAX_BYTES and i < len(sized):
        task_id, path, size = sized[i]
        shutil.rmtree(path, ignore_errors=True)
        removed.append((task_id, "size cap"))
        total -= size
        i += 1

    if removed:
        details = ", ".join(f"{tid} ({reason})" for tid, reason in removed)
        print(f"Cleaned {len(removed)} kanban workspace(s): {details}")


if __name__ == "__main__":
    main()
