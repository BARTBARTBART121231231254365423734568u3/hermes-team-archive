#!/usr/bin/env python3
"""Read-only team report: no model calls, credentials, or external messages."""
import collections
import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import urllib.request

ROOT = Path(os.environ.get("HERMES_OPS_HOME", "/root/.hermes"))


def report(root=ROOT):
    issues = []
    try:
        with urllib.request.urlopen("http://127.0.0.1:" + os.environ.get("PORT", "8080") + "/api/health", timeout=5) as response:
            health = json.load(response)
        if health.get("application") != "hermes-agent" or health.get("status") != "ready":
            issues.append("Hermes readiness/identity check failed")
        if health.get("ticket_errors_last_5m", 0) >= 5:
            issues.append("Repeated WebSocket ticket failures in the last five minutes")
    except Exception as exc:
        health = {"error": type(exc).__name__}
        issues.append("Hermes ingress is unavailable")
    with sqlite3.connect(f"file:{root / 'kanban.db'}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        tasks = [dict(row) for row in connection.execute("SELECT id,title,status,assignee,block_kind,last_heartbeat_at FROM tasks WHERE status NOT IN ('done','archived')")]
        done = connection.execute("SELECT count(*) FROM tasks WHERE status='done' AND completed_at > strftime('%s','now')-86400").fetchone()[0]
    profiles = {"default"} | {p.name for p in (root / "profiles").iterdir() if p.is_dir()}
    for task in tasks:
        if task["assignee"] and task["assignee"] not in profiles:
            issues.append(f"{task['id']}: unknown assignee {task['assignee']}")
    with sqlite3.connect(f"file:{root / 'projects.db'}?mode=ro", uri=True) as connection:
        for slug, path in connection.execute("SELECT slug,primary_path FROM projects WHERE archived=0"):
            if not path or not Path(path).exists():
                issues.append(f"Project repository missing: {slug}")
    disk = shutil.disk_usage(root)
    if disk.free / disk.total < 0.15:
        issues.append("Persistent volume has less than 15% free space")
    return {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "health": health, "completed_last_24h": done,
            "counts": dict(collections.Counter(t['status'] for t in tasks)),
            "attention": [t for t in tasks if t['status'] in ('blocked','triage','review')],
            "issues": issues, "volume_free_bytes": disk.free}


if __name__ == "__main__":
    result = report()
    destination = ROOT / "ops"
    destination.mkdir(exist_ok=True, mode=0o700)
    temporary = destination / "team-status.tmp"
    temporary.write_text(json.dumps(result, indent=2))
    temporary.replace(destination / "team-status.json")
    print(json.dumps(result, indent=2))
