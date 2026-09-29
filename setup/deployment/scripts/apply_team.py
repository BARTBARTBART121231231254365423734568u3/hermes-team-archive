#!/usr/bin/env python3
"""Explicit, versioned live migration; never run implicitly on every boot."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys

import yaml

ROOT = Path(os.environ.get("HERMES_OPS_HOME", "/root/.hermes"))
SOURCE = Path(__file__).resolve().parent
TEAM = Path("/opt/hermes-team")
VERSION = "2026-09-team-v1"
ROLES = {
    "default": ("Team coordinator", "Own the user outcome, route implementation to specialists, track handoffs, and give Thomas one consolidated update. Answer small questions directly. Use the board for durable work; do not make Thomas manage the team."),
    "planner": ("Delivery planner", "Turn complex requests into acceptance criteria and dependency-linked tasks. Keep one owner per card and remove ambiguity before dispatch. Check existing work before creating tasks. Escalate only decisions the team cannot resolve."),
    "coder": ("Software engineer", "Implement and debug in isolated task worktrees, validate behavior, and hand reviewable commits to security. Use your configured model and tools; do not assume old instructions describe the current provider. Coordinate visual work with designer and releases with devops."),
    "designer": ("Product designer", "Own interaction design, visual quality and clickable previews. Preserve the user's visual references and required design approval. Give coder concrete assets and acceptance criteria. Check rendered output and working controls before claiming fidelity."),
    "researcher": ("Research analyst", "Investigate with primary sources and evidence, distinguish findings from inference, and return concise recommendations tied to the task. Verify time-sensitive claims. Hand implementation to the appropriate specialist."),
    "security": ("Quality and security reviewer", "Independently review correctness, regressions, security and validation evidence. Read actual changes and run proportionate checks. Request concrete changes or record approval; do not silently implement a different design. Send fixes to coder and releases to devops."),
    "devops": ("Release operator", "Own target manifests, deployment, readiness and recovery. Verify exact project/environment/service/repository/commit, use the deployment guard, and record the previous deployment before publishing. Test application behavior after deployment. Never overwrite Hermes with another project."),
    "scheduler": ("Scheduling assistant", "Create and verify purposeful reminders and recurring tasks in Europe/Amsterdam unless the user specifies otherwise. Prefer deterministic scripts for maintenance. Never schedule an LLM just to poll status or repeatedly unblock every task."),
}


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".team-tmp")
    temporary.write_text(text)
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def compact_soul(profile, original):
    role, mission = ROLES[profile]
    # Preserve project-specific and design constraints instead of overwriting
    # those with generic team policy. The complete original is backed up.
    sections = re.split(r"(?=^## )", original, flags=re.MULTILINE)
    retained = []
    for section in sections:
        title = section.splitlines()[0].lower() if section.strip() else ""
        if any(term in title for term in ("your role: designer", "design-driven", "mockups get", "legal and business", "publishing a real clickable", "langfuse", "defaults for anything beyond")):
            retained.append(section.strip())
    return (f"You are the Hermes {role}, working with Thomas and the specialist team.\n\n"
            f"{mission}\n\n"
            "Read /root/.hermes/team/TEAM.md before substantive work. It defines the\n"
            "team roles, task contract, deployment guard, and handoff procedure. Follow\n"
            "the user's current instructions and already-granted authorization.\n\n"
            "Be direct and evidence-driven. Take authorized work through completion,\n"
            "hand off internally when appropriate, and never fabricate test or deployment\n"
            "results. Do not put credentials in chat, task cards, reports, or memory.\n\n"
            "Use `hermes project list` to find existing projects. Repositories live under\n"
            "/root/projects on persistent storage. Native Kanban tools are preferred;\n"
            "outside a dispatched task, pass an explicit task ID. Retain the origin of\n"
            "the request so completion reaches the initiating conversation.\n\n"
            + "\n\n".join(retained) + "\n")


def configure_local_browser(homes):
    changed = []
    for name, home in homes.items():
        config_file = home / "config.yaml"
        config = yaml.safe_load(config_file.read_text()) or {}
        browser = config.setdefault("browser", {})
        # `off` disables browser-use's implicit uvx fallback, selecting Hermes's
        # built-in browser_* tools backed by the pinned agent-browser + Chromium.
        # Respect an explicitly selected alternative backend.
        if not browser.get("backend"):
            browser["backend"] = "off"
            atomic_write(config_file, yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
            changed.append(name)
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--refresh-browser", action="store_true", help="Select the tested local browser for profiles still using automatic backend detection")
    args = parser.parse_args()
    marker = ROOT / "ops" / (VERSION + ".json")
    if marker.exists() and not args.refresh_browser:
        print(marker.read_text())
        return
    homes = {name: ROOT if name == "default" else ROOT / "profiles" / name for name in ROLES}
    plan = {"version": VERSION, "profiles": list(homes), "max_workers": 2, "retry_policy": "transient-only", "apply": args.apply}
    print(json.dumps(plan))
    if not args.apply:
        return
    os.umask(0o077)
    from ops_snapshot import snapshot
    backup = snapshot(ROOT)
    browser_profiles = configure_local_browser(homes)
    if args.refresh_browser:
        print(json.dumps({"backup": backup, "local_browser_profiles": browser_profiles}))
        return
    (ROOT / "team").mkdir(exist_ok=True)
    shutil.copytree(TEAM, ROOT / "team", dirs_exist_ok=True)
    for name, home in homes.items():
        if not (home / "config.yaml").exists():
            raise RuntimeError("Expected existing profile missing: " + name)
        soul = home / "SOUL.md"
        original = soul.read_text() if soul.exists() else ""
        atomic_write(soul, compact_soul(name, original))
    config_file = ROOT / "config.yaml"
    config = yaml.safe_load(config_file.read_text()) or {}
    config.setdefault("kanban", {}).update(max_in_progress=2, max_in_progress_per_profile=1, failure_limit=2)
    atomic_write(config_file, yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    for name in ("rate_limit_unblock.py", "team_status.py", "ops_snapshot.py"):
        shutil.copy2(SOURCE / name, ROOT / "scripts" / name)
    sys.path.insert(0, "/opt/hermes-agent")
    from cron.jobs import list_jobs, update_job, create_job
    jobs = list_jobs(include_disabled=True)
    for job in jobs:
        if job.get("script") == "rate_limit_unblock.py":
            update_job(job["id"], {"name": "Bounded transient-task recovery", "schedule": "17 * * * *", "no_agent": True, "prompt": "", "deliver": "local"})
        if job.get("name") == "System Health Watchdog":
            update_job(job["id"], {"name": "Team health report", "schedule": "7 * * * *", "script": "team_status.py", "no_agent": True, "prompt": "", "deliver": "local"})
    if not any(job.get("script") == "ops_snapshot.py" for job in jobs):
        create_job(prompt="", schedule="37 3 * * *", name="Verified configuration and database snapshot", script="ops_snapshot.py", no_agent=True, deliver="local")
    # Seed project knowledge without inventing missing deployment destinations.
    with sqlite3.connect(f"file:{ROOT / 'projects.db'}?mode=ro", uri=True) as connection:
        projects = connection.execute("SELECT slug,name,primary_path FROM projects WHERE archived=0").fetchall()
    for slug, name, path in projects:
        if not re.fullmatch(r"[a-z0-9_-]+", slug):
            continue
        record = ROOT / "team" / "projects" / (slug + ".md")
        if not record.exists():
            atomic_write(record, f"# {name}\n\nRegistered repository path: {path}\n\n"
                         "Verify git origin and the current branch before work. Record architecture\n"
                         "and decisions only after inspecting this project. Deployment target must\n"
                         "come from a verified manifest; never infer it from the container environment.\n")
    plan.update(backup=backup, applied_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    atomic_write(marker, json.dumps(plan, indent=2))
    print(json.dumps(plan))


if __name__ == "__main__":
    main()
