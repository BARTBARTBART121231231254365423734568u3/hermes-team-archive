#!/usr/bin/env python3
"""Start, inspect, or stop the hardened localhost preview server."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

LOCAL_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "hermes"
STATE_FILE = LOCAL_ROOT / "preview-server.json"


def health_ok(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
            return response.status == 200 and response.read(16) == b"ok\n"
    except OSError:
        return False


def read_state() -> dict:
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def wait_until_listening(process: subprocess.Popen, port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"preview server exited during startup with code {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"preview server did not listen on 127.0.0.1:{port}")


def stop_server() -> int:
    state = read_state()
    pid = state.get("pid")
    if not isinstance(pid, int):
        print("preview server is not managed (no PID state)", file=sys.stderr)
        return 1
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, 15)
            result = subprocess.CompletedProcess([], 0)
        except OSError:
            result = subprocess.CompletedProcess([], 1)
    STATE_FILE.unlink(missing_ok=True)
    return 0 if result.returncode == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", choices=("start", "status", "stop"), default="start")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--directory")
    parser.add_argument("--log-file")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.action == "stop":
        return stop_server()
    if args.action == "status":
        ok = health_ok(args.port)
        print(json.dumps({"healthy": ok, **read_state()}))
        return 0 if ok else 1
    if not args.directory:
        parser.error("--directory is required when starting")

    root = Path(args.directory).resolve()
    if not root.is_dir():
        parser.error(f"directory does not exist: {root}")
    if health_ok(args.port):
        print(json.dumps({"reused": True, "host": "127.0.0.1", "port": args.port, **read_state()}))
        return 0

    default_log = LOCAL_ROOT / "logs" / "preview-server.log"
    log_path = Path(args.log_file).resolve() if args.log_file else default_log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(Path(__file__).with_name("preview_server.py")), "--bind", "127.0.0.1", "--port", str(args.port), "--directory", str(root)]
    creationflags = 0
    popen_options = {}
    if os.name == "nt":
        # Hermes workers run in a kill-on-close Job. BREAKAWAY is essential: the
        # other detached flags alone do not survive the launcher's Job teardown.
        creationflags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS |
                         subprocess.CREATE_NO_WINDOW | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000))
    else:
        popen_options["start_new_session"] = True

    with open(log_path, "ab", buffering=0) as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   close_fds=True, creationflags=creationflags, **popen_options)
    try:
        wait_until_listening(process, args.port)
        if not health_ok(args.port):
            raise RuntimeError("preview server listened but failed its health check")
    except Exception:
        process.terminate()
        raise

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {"pid": process.pid, "host": "127.0.0.1", "port": args.port,
             "directory": str(root), "log": str(log_path)}
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    print(json.dumps(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
