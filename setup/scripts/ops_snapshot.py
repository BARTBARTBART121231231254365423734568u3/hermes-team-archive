#!/usr/bin/env python3
"""Private, consistent per-database Hermes snapshots (not fleet-atomic)."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
import tempfile

# This job runs under the default Hermes cron home, not a named profile.
# An explicit override remains available for an isolated test/restore.
ROOT = Path(os.environ.get("HERMES_OPS_HOME", Path.home() / ".hermes"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root=ROOT):
    destination = root / "backups" / "ops"
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    os.umask(0o077)
    with (destination / ".lock").open("a") as lock:
        if os.name != "nt":
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        final = destination / (stamp + ".tar.gz")
        temporary = final.with_suffix(".partial")
        if final.exists() or temporary.exists():
            raise FileExistsError(final)
        with tempfile.TemporaryDirectory(dir=destination) as work:
            work = Path(work)
            records = []
            homes = [root] + sorted((root / "profiles").glob("*"))
            paths = []
            for home in homes:
                if not home.is_dir() or home.is_symlink():
                    continue
                paths += list(home.glob("*.db")) + list(home.glob("*.yaml"))
                paths += [home / name for name in ("SOUL.md", "AGENTS.md", ".env", "auth.json", "cron/jobs.json")]
                paths += list((home / "cron").glob("*.db"))
            # The active board can live at root or in kanban/boards; never
            # recursively walk workspaces, old migrations, caches or backups.
            paths += list((root / "kanban").glob("*.db"))
            paths += list((root / "kanban" / "boards").glob("*.db"))
            paths += [root / "scripts" / "ops_snapshot.py"]
            runtime = root / "hermes-agent"
            paths += [runtime / "gateway" / "kanban_watchers_dispatcher.py",
                      runtime / "hermes_cli" / "config_defaults.py"]
            paths += list((runtime / "hermes_cli").glob("kanban*.py"))
            paths += list((runtime / "hermes_cli").glob("model_routing.py"))
            for path in sorted(set(paths)):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(root)
                target = work / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".db":
                    source = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                    dest = sqlite3.connect(target)
                    try:
                        source.backup(dest)
                        if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            raise RuntimeError("Backup database validation failed: " + str(relative))
                    finally:
                        dest.close()
                        source.close()
                else:
                    shutil.copy2(path, target)
                target.chmod(0o600)
                records.append({"path": str(relative), "sha256": digest(target), "bytes": target.stat().st_size})
            names = {record["path"] for record in records}
            required = {"kanban.db", "config.yaml", "cron/jobs.json", "scripts/ops_snapshot.py",
                        "hermes-agent/gateway/kanban_watchers_dispatcher.py"}
            if not required <= names or not any(name.startswith("profiles/") and name.endswith("/config.yaml") for name in names):
                raise RuntimeError("Missing mandatory active Hermes DB/config/source: " + repr(sorted(required - names)))
            (work / "manifest.json").write_text(json.dumps({"created": stamp, "root": str(root), "files": records}, indent=2))
            (work / "manifest.json").chmod(0o600)
            try:
                with tarfile.open(temporary, "x:gz") as archive:
                    archive.add(work, arcname="hermes", recursive=True)
                temporary.replace(final)
            finally:
                temporary.unlink(missing_ok=True)
        # Retention intentionally disabled: old archives are forensic evidence.
        return {"backup": str(final), "databases_and_config_files": len(records), "bytes": final.stat().st_size}


if __name__ == "__main__":
    print(json.dumps(snapshot()))
