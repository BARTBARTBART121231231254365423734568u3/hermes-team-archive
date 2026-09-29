"""Read-only Agent Watch API, mounted at /api/plugins/agent-watch/.

SPIKE DECISION (2026-09-22, task t_75ea7a33): the pane cannot use
``host.request`` alone. A source scan of the gateway + hermes_cli tree for
``register_method("kanban.*")`` or any ``"kanban.<method>"`` RPC registration
found zero Kanban RPC methods (only sessions/profiles/cron/skills/config).
So this backend reads the local Kanban SQLite board directly (the same
read path the ``hermes kanban list --json`` CLI uses) and serves the
contracted ``GET /summary`` shape. Read-only: SELECT queries only, no
steer/stop/kill, no transcript tails.
"""

from __future__ import annotations

import json
import sys
import time
from contextlib import closing
from typing import Any

from fastapi import APIRouter

from hermes_cli import kanban_db
from hermes_cli import kanban_db_connect as kbc

router = APIRouter()

READY_CAP = 10
BLOCKED_CAP = 20
STALE_HEARTBEAT_S = 300
REASON_MAX_LEN = 240


def _duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def _payload_dict(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _icon_for(title: str, body: str | None) -> str:
    text = f"{title} {body or ''}".lower()
    groups = (
        (("research", "investigate", "search", "spike"), "🔎"),
        (("design", "ui", "ux", "mockup", "visual"), "🎨"),
        (("review", "security", "audit"), "🛡️"),
        (("deploy", "release", "ship"), "🚀"),
        (("code", "build", "implement", "fix", "test", "plugin"), "💻"),
    )
    return next((icon for words, icon in groups if any(word in text for word in words)), "🤖")


def _activity(kind: str | None) -> str:
    labels = {
        "claimed": "Started work",
        "heartbeat": "Working",
        "comment": "Posted an update",
        "attached": "Produced an artifact",
        "review_requested": "Requested review",
        "blocked": "Needs input",
    }
    return labels.get(kind or "", "Working")


def _board_conn():
    board = kanban_db.get_current_board()
    kanban_db.init_db(board=board)
    return board, closing(kbc.connect(board=board))


def _running_rows(conn, checked_at: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT t.id, t.title, t.body, t.assignee, t.tenant, t.branch_name,
               t.workspace_path, t.created_at, t.started_at,
               t.last_heartbeat_at AS task_heartbeat_at, t.current_run_id,
               r.started_at AS run_started_at, r.last_heartbeat_at,
               (SELECT e.kind FROM task_events e WHERE e.task_id = t.id
                ORDER BY e.id DESC LIMIT 1) AS latest_event_kind,
               (SELECT e.created_at FROM task_events e WHERE e.task_id = t.id
                ORDER BY e.id DESC LIMIT 1) AS latest_event_at
        FROM tasks t
        LEFT JOIN task_runs r ON r.id = t.current_run_id
        WHERE t.status = 'running'
        ORDER BY COALESCE(r.started_at, t.started_at, t.created_at) ASC
        """
    ).fetchall()
    agents = []
    for row in rows:
        started_at = int(row["run_started_at"] or row["started_at"] or row["created_at"] or checked_at)
        heartbeat_at = int(
            row["last_heartbeat_at"]
            or row["task_heartbeat_at"]
            or row["latest_event_at"]
            or started_at
        )
        elapsed = max(0, checked_at - started_at)
        heartbeat_age = max(0, checked_at - heartbeat_at)
        agents.append(
            {
                "id": row["id"],
                "task_id": row["id"],
                "title": row["title"],
                "agent": row["assignee"] or "unassigned",
                "assignee": row["assignee"] or "unassigned",
                "tenant": row["tenant"],
                "branch": row["branch_name"],
                "workspace": row["workspace_path"],
                "icon": _icon_for(row["title"], row["body"]),
                "activity": _activity(row["latest_event_kind"]),
                "status_text": f"Working · {_duration(elapsed)}",
                "elapsed_seconds": elapsed,
                "started_at": started_at,
                "heartbeat_age_s": heartbeat_age,
                "heartbeat_text": f"{_duration(heartbeat_age)} ago" if heartbeat_age >= 10 else "just now",
                "stale": heartbeat_age > STALE_HEARTBEAT_S,
            }
        )
    return agents


def _ready_collection(conn) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS c FROM tasks WHERE status = 'ready'").fetchone()["c"]
    rows = conn.execute(
        """
        SELECT id, title, assignee, tenant, priority, created_at
        FROM tasks WHERE status = 'ready'
        ORDER BY priority DESC, created_at ASC LIMIT ?
        """,
        (READY_CAP,),
    ).fetchall()
    return {
        "total": int(total),
        "items": [
            {
                "id": row["id"],
                "task_id": row["id"],
                "title": row["title"],
                "assignee": row["assignee"] or "unassigned",
                "tenant": row["tenant"],
                "priority": row["priority"],
            }
            for row in rows
        ],
    }


def _needs_input_collection(conn, checked_at: int) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT t.id, t.title, t.assignee, t.tenant, t.block_kind,
               t.created_at, t.started_at,
               e.kind AS latest_event_kind, e.payload AS latest_payload,
               e.created_at AS latest_event_at
        FROM tasks t
        LEFT JOIN task_events e ON e.id = (
            SELECT MAX(id) FROM task_events WHERE task_id = t.id
        )
        WHERE t.status = 'blocked'
        ORDER BY t.created_at DESC LIMIT 200
        """
    ).fetchall()
    matched = []
    for row in rows:
        payload = _payload_dict(row["latest_payload"])
        reason = str(payload.get("reason") or "")[:REASON_MAX_LEN]
        is_needs_input = row["block_kind"] == "needs_input" or payload.get("kind") == "needs_input"
        if not is_needs_input:
            continue
        blocked_at = int(row["latest_event_at"] or row["started_at"] or row["created_at"] or checked_at)
        matched.append(
            {
                "id": row["id"],
                "task_id": row["id"],
                "title": row["title"],
                "assignee": row["assignee"] or "unassigned",
                "tenant": row["tenant"],
                "block_kind": row["block_kind"] or payload.get("kind") or "needs_input",
                "reason": reason,
                "blocked_at": blocked_at,
                "age_s": max(0, checked_at - blocked_at),
            }
        )
    return {"total": len(matched), "items": matched[:BLOCKED_CAP]}


def build_summary() -> dict[str, Any]:
    """Assemble the contracted /summary payload (also used by --selftest)."""
    checked_at = int(time.time())
    board, conn_ctx = _board_conn()
    with conn_ctx as conn:
        running = _running_rows(conn, checked_at)
        ready = _ready_collection(conn)
        needs_input = _needs_input_collection(conn, checked_at)
    return {
        "checked_at": checked_at,
        "board": board,
        "running": running,
        "ready": ready,
        "needs_input": needs_input,
    }


@router.get("/summary")
def get_summary() -> dict[str, Any]:
    """Contracted v1 payload: running + ready queue + blocked-needs-input."""
    return build_summary()


@router.get("/agents")
def list_active_agents() -> dict[str, Any]:
    """Legacy compact running-workers snapshot (kept for compatibility)."""
    checked_at = int(time.time())
    board, conn_ctx = _board_conn()
    with conn_ctx as conn:
        running = _running_rows(conn, checked_at)
    agents = [
        {
            "task_id": row["id"],
            "agent": row["assignee"],
            "title": row["title"],
            "icon": row["icon"],
            "activity": row["activity"],
            "status_text": row["status_text"],
            "elapsed_seconds": row["elapsed_seconds"],
            "updated_text": row["heartbeat_text"],
        }
        for row in running
    ]
    return {"agents": agents, "count": len(agents), "checked_at": checked_at, "board": board}


def _selftest() -> int:
    summary = build_summary()
    assert set(summary) == {"checked_at", "board", "running", "ready", "needs_input"}, summary.keys()
    assert isinstance(summary["running"], list)
    assert set(summary["ready"]) == {"total", "items"}
    assert set(summary["needs_input"]) == {"total", "items"}
    for row in summary["running"]:
        for key in ("id", "title", "assignee", "tenant", "branch", "heartbeat_age_s"):
            assert key in row, key
    print(
        json.dumps(
            {
                "board": summary["board"],
                "running": len(summary["running"]),
                "ready_total": summary["ready"]["total"],
                "needs_input_total": summary["needs_input"]["total"],
                "running_ids": [r["id"] for r in summary["running"]],
            }
        )
    )
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print("usage: plugin_api.py --selftest", file=sys.stderr)
    raise SystemExit(2)
