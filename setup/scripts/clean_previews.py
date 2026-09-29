#!/usr/bin/env python3
"""No-agent cron script: enforces the preview-hosting retention policy.

Previews (see create_preview.py) are generic across every project — keyed
by an opaque random ID, never a project name — so cleanup is equally
generic: it just walks the store, it never needs to know what project a
given preview belongs to.

Two independent rules:
  1. Age: delete any preview directory older than RETENTION_SECONDS.
  2. Size: if the store still exceeds MAX_BYTES after the age sweep,
     delete oldest-first until back under the cap — a backstop against a
     burst of large previews filling disk between cleanup runs.

Runs as a pure script (no LLM call) so it keeps working even if the
account is rate-limited. Prints a summary only when it actually removed
something; empty stdout is treated as "nothing to do" by the cron runner.
"""
import json
import os
import shutil
import time

PREVIEWS_DIR = os.environ.get("HERMES_PREVIEWS_DIR", os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local")), "hermes", "previews"))
RETENTION_SECONDS = 7 * 86400
MAX_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB


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


def created_at(path: str) -> float:
    meta_path = os.path.join(path, ".preview_meta.json")
    try:
        with open(meta_path) as f:
            return float(json.load(f).get("created_at", 0))
    except Exception:
        try:
            return os.path.getmtime(path)
        except OSError:
            return time.time()


def main() -> None:
    if not os.path.isdir(PREVIEWS_DIR):
        return

    now = time.time()
    entries = []
    for name in os.listdir(PREVIEWS_DIR):
        path = os.path.join(PREVIEWS_DIR, name)
        if os.path.isdir(path):
            entries.append((path, created_at(path)))

    removed = []

    remaining = []
    for path, ts in entries:
        if now - ts > RETENTION_SECONDS:
            shutil.rmtree(path, ignore_errors=True)
            removed.append((os.path.basename(path), "expired"))
        else:
            remaining.append((path, ts))

    remaining.sort(key=lambda e: e[1])
    total = sum(dir_size(p) for p, _ in remaining)
    i = 0
    while total > MAX_BYTES and i < len(remaining):
        path, _ts = remaining[i]
        total -= dir_size(path)
        shutil.rmtree(path, ignore_errors=True)
        removed.append((os.path.basename(path), "size cap"))
        i += 1

    if removed:
        details = ", ".join(f"{pid} ({reason})" for pid, reason in removed)
        print(f"Cleaned {len(removed)} preview(s): {details}")


if __name__ == "__main__":
    main()
