#!/usr/bin/env python3
"""Consistent per-database snapshots plus configuration, with bounded retention.

Stored on the volume for fast rollback; Railway volume snapshots provide the
separate disaster-recovery layer. This does not claim an atomic fleet snapshot.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
import tempfile

ROOT = Path(os.environ.get("HERMES_OPS_HOME", "/root/.hermes"))


def snapshot(root=ROOT):
    import fcntl
    destination = root / "backups" / "ops"
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (destination / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        final = destination / (stamp + ".tar.gz")
        temporary = final.with_suffix(".partial")
        os.umask(0o077)
        with tempfile.TemporaryDirectory(dir=destination) as work:
            work = Path(work)
            records = []
            homes = [root] + sorted((root / "profiles").glob("*"))
            for home in homes:
                if not home.is_dir() or home.is_symlink():
                    continue
                paths = list(home.glob("*.db")) + list(home.glob("*.yaml"))
                paths += [home / name for name in ("SOUL.md", "AGENTS.md", ".env", "auth.json", "cron/jobs.json")]
                for path in paths:
                    if not path.is_file() or path.is_symlink():
                        continue
                    relative = path.relative_to(root)
                    target = work / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if path.suffix == ".db":
                        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as source, sqlite3.connect(target) as dest:
                            source.backup(dest)
                            if dest.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                                raise RuntimeError("Backup database validation failed: " + str(relative))
                    else:
                        shutil.copy2(path, target)
                    records.append(str(relative))
            (work / "manifest.json").write_text(json.dumps({"created": stamp, "files": records}, indent=2))
            with tarfile.open(temporary, "w:gz") as archive:
                archive.add(work, arcname="hermes", recursive=True)
            temporary.replace(final)
        # Only archives owned by this script, after a new backup validated successfully.
        for old in sorted(destination.glob("????????T????????????Z.tar.gz"))[:-7]:
            old.unlink()
        return {"backup": str(final), "databases_and_config_files": len(records), "bytes": final.stat().st_size}


if __name__ == "__main__":
    print(json.dumps(snapshot()))
