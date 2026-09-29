#!/usr/bin/env python3
"""Generic preview publisher — any profile, any project, no per-project setup.

Copies a local directory (a built site, a single HTML file, a design mockup)
into the shared previews store under an opaque random ID and prints back a
public, clickable URL. Previews are NOT tied to any project name — the store
is keyed purely by the random ID, so this works identically for a project
that doesn't exist yet.

Retention is handled entirely by a separate cron (clean_previews.py): this
script only ever adds, it never has to know or care about expiry policy.

Usage:
    python3 create_preview.py <local_directory_or_html_file>

Prints a single URL to stdout on success.
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import shutil
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

PREVIEWS_DIR = os.environ.get("HERMES_PREVIEWS_DIR", os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local")), "hermes", "previews"))
BASE_URL_FILE = os.path.join(os.path.dirname(PREVIEWS_DIR), "preview-base-url.txt")
PREVIEW_PORT = 8080
LOCAL_HEALTH_URL = f"http://127.0.0.1:{PREVIEW_PORT}/healthz"
TAILSCALE_EXE = os.environ.get("TAILSCALE_EXE") or shutil.which("tailscale") or r"C:\Program Files\Tailscale\tailscale.exe"
REPARSE_POINT_ATTRIBUTE = 0x400


def local_health_ok(timeout: float = 1.0) -> bool:
    try:
        with urlopen(LOCAL_HEALTH_URL, timeout=timeout) as response:
            return response.status == 200 and response.read(16) == b"ok\n"
    except OSError:
        return False


def ensure_preview_server() -> None:
    if local_health_ok():
        return
    launcher = Path(__file__).with_name("start_preview_server.py")
    result = subprocess.run(
        [sys.executable, str(launcher), "--port", str(PREVIEW_PORT), "--directory", PREVIEWS_DIR],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "preview server could not start on 127.0.0.1:8080; "
            "stop the process already using port 8080 and retry"
        )
    for _ in range(10):
        if local_health_ok():
            return
        time.sleep(0.1)
    raise RuntimeError("preview server started but its local health check failed")


def _funnel_ready(status: str, base_url: str) -> bool:
    host = urlsplit(base_url).hostname or ""
    return host in status and "Funnel on" in status and "proxy http://127.0.0.1:8080" in status


def ensure_funnel(base_url: str) -> None:
    if not base_url.startswith("https://"):
        return
    command = [TAILSCALE_EXE, "funnel", "status"]
    try:
        status = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("could not check Tailscale Funnel status; ensure Tailscale is running and retry") from exc
    if status.returncode == 0 and _funnel_ready(status.stdout, base_url):
        return
    try:
        configured = subprocess.run(
            [TAILSCALE_EXE, "funnel", "--bg", "--yes", str(PREVIEW_PORT)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "Tailscale Funnel needs attention; run 'tailscale funnel 8080' interactively once, then retry"
        ) from exc
    if configured.returncode != 0:
        raise RuntimeError(
            "Tailscale Funnel needs authorization; run 'tailscale funnel 8080' interactively once, then retry"
        )
    verified = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    if verified.returncode != 0 or not _funnel_ready(verified.stdout, base_url):
        raise RuntimeError("Tailscale Funnel configuration could not be verified; check 'tailscale funnel status' and retry")


def validate_https_base_url(value: str, source: str = "configured preview base URL") -> str:
    base_url = value.strip().rstrip("/")
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{source} must be an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{source} must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{source} must not contain a query or fragment")
    return base_url


def configured_base_url() -> str:
    base_url = os.environ.get("PREVIEW_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        try:
            with open(BASE_URL_FILE, encoding="utf-8") as f:
                base_url = f.read().strip().rstrip("/")
        except OSError:
            pass
    if base_url:
        base_url = validate_https_base_url(base_url)
    return base_url


def is_link_or_reparse(path: str | os.PathLike[str]) -> bool:
    entry_stat = os.lstat(path)
    return os.path.islink(path) or bool(getattr(entry_stat, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE)


def copy_tree_without_links(source: str, destination: str) -> None:
    if is_link_or_reparse(source):
        raise ValueError(f"preview source contains a link or reparse point: {source}")
    os.mkdir(destination)
    for entry in os.scandir(source):
        src = entry.path
        dst = os.path.join(destination, entry.name)
        if entry.is_symlink() or is_link_or_reparse(src):
            raise ValueError(f"preview source contains a link or reparse point: {src}")
        if entry.is_dir(follow_symlinks=False):
            copy_tree_without_links(src, dst)
        elif entry.is_file(follow_symlinks=False):
            shutil.copy2(src, dst, follow_symlinks=False)
        else:
            raise ValueError(f"preview source contains an unsupported filesystem entry: {src}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: create_preview.py <local_directory_or_html_file>", file=sys.stderr)
        return 1

    src = os.path.abspath(sys.argv[1])
    if not os.path.exists(src):
        print(f"error: {src} does not exist", file=sys.stderr)
        return 1

    try:
        base_url = configured_base_url()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not base_url:
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        try:
            base_url = validate_https_base_url(f"https://{domain}", "RAILWAY_PUBLIC_DOMAIN fallback") if domain else "http://localhost:8080"
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    os.makedirs(PREVIEWS_DIR, exist_ok=True)
    try:
        ensure_preview_server()
        ensure_funnel(base_url)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    preview_id = secrets.token_hex(8)
    dest = os.path.join(PREVIEWS_DIR, preview_id)

    try:
        if is_link_or_reparse(src):
            raise ValueError(f"preview source contains a link or reparse point: {src}")
        if os.path.isdir(src):
            copy_tree_without_links(src, dest)
            if not os.path.isfile(os.path.join(dest, "index.html")):
                print("warning: no index.html at the top level of that directory — the preview root URL will 404 until one exists (other files are still reachable by name)", file=sys.stderr)
        else:
            os.makedirs(dest)
            name = "index.html" if src.lower().endswith((".html", ".htm")) else os.path.basename(src)
            shutil.copy2(src, os.path.join(dest, name), follow_symlinks=False)
        with open(os.path.join(dest, ".preview_meta.json"), "w", encoding="utf-8") as f:
            json.dump({"created_at": time.time()}, f)
    except (OSError, ValueError) as exc:
        shutil.rmtree(dest, ignore_errors=True)
        print(f"error: preview publication failed: {exc}", file=sys.stderr)
        return 1

    print(f"{base_url}/preview/{preview_id}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
