#!/usr/bin/env python3
"""Read-only archive verification; extraction happens only into private scratch."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile

archive = Path(sys.argv[1])
assert archive.is_file() and archive.stat().st_mode & 0o077 == 0, 'archive is not private'
assert archive.parent.stat().st_mode & 0o077 == 0, 'archive directory is not private'
with tarfile.open(archive, 'r:gz') as tar:
    members = tar.getmembers()
    assert all((m.name == 'hermes' or m.name.startswith('hermes/')) and not m.issym() and not m.islnk() and '..' not in Path(m.name).parts for m in members)
    assert all((m.mode & 0o077) == 0 for m in members), 'archive member permissions not private'
    manifest = json.load(tar.extractfile('hermes/manifest.json'))
    listed = {r['path']: r for r in manifest['files']}
    actual = {m.name[len('hermes/'):]: m for m in members if m.isfile() and m.name != 'hermes/manifest.json'}
    assert actual.keys() == listed.keys(), 'manifest/archive mismatch'
    required = {'kanban.db', 'config.yaml', 'cron/jobs.json', 'scripts/ops_snapshot.py', 'hermes-agent/gateway/kanban_watchers_dispatcher.py'}
    assert required <= listed.keys(), f'missing mandatory files: {required - listed.keys()}'
    assert any(p.startswith('profiles/') and p.endswith('/config.yaml') for p in listed)
    assert any(p.startswith('profiles/') and p.endswith('/cron/executions.db') for p in listed)
    assert any(p.startswith('profiles/') and p.endswith('/state.db') for p in listed)
    assert any(p.startswith('hermes-agent/hermes_cli/') and p.endswith('.py') for p in listed)
    jobs = json.load(tar.extractfile('hermes/cron/jobs.json'))
    entries = jobs if isinstance(jobs, list) else jobs['jobs']
    job = next(j for j in entries if j['id'] == '201e9a8d4754')
    assert job['enabled'] is True and job['script'] == 'ops_snapshot.py' and job['no_agent'] is True
    assert job['schedule']['expr'] == '37 3 * * *'
    # For the actual scheduled gate pass --after 2026-09-24T03:37:00+00:00.
    # The archived cron/jobs.json may carry either the imminent or next day's run.
    if len(sys.argv) > 2:
        threshold = dt.datetime.fromisoformat(sys.argv[2])
        assert dt.datetime.strptime(manifest['created'], '%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc) >= threshold
    db_count = 0
    with tempfile.TemporaryDirectory(prefix='ops-restore-', dir=archive.parent) as temporary:
        for name, record in listed.items():
            restored = Path(temporary) / name
            restored.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            size = 0
            with tar.extractfile(actual[name]) as source, restored.open('wb') as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    h.update(chunk)
                    size += len(chunk)
                    target.write(chunk)
            assert size == record['bytes'] and h.hexdigest() == record['sha256'], f'hash/size failure {name}'
            if name.endswith('.db'):
                db_count += 1
                with sqlite3.connect(restored.as_uri() + '?mode=ro', uri=True) as con:
                    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', f'integrity failure {name}'
                    if name == 'kanban.db':
                        assert con.execute("SELECT count(*) FROM tasks WHERE id=?", ('t_80c972ed',)).fetchone()[0] == 1, 'board restore cannot read task'
            restored.unlink()
    created = dt.datetime.strptime(manifest['created'], '%Y%m%dT%H%M%S%fZ').replace(tzinfo=dt.timezone.utc)
    age = (dt.datetime.now(dt.timezone.utc) - created).total_seconds()
    # Historical scheduled snapshots retain integrity/provenance value after an
    # hour. Activation separately requires a fresh (<1h) snapshot as well.
    max_age = 86400 if '--historical' in sys.argv[3:] else 3600
    assert 0 <= age < max_age, 'archive timestamp stale/future'
    archive_hash = hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            archive_hash.update(chunk)
    print(json.dumps({'archive': str(archive), 'archive_sha256': archive_hash.hexdigest(), 'created': manifest['created'], 'age_seconds': round(age, 1), 'file_count': len(listed), 'sqlite_integrity_checked': db_count, 'required_present': sorted(required), 'scheduled_job': job['id'], 'next_run_at': job['next_run_at'], 'restore_board_read': 'ok', 'permissions': 'private'}))
