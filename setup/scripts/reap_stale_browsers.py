#!/usr/bin/env python3
"""No-agent cron script: kills browser processes that outlived their task.

Agents launch Chromium (via agent-browser / Playwright) to visually verify
their work -- rendering a page, checking a deploy, comparing against a
mockup. Nothing tears those sessions down when the task ends, so they
accumulate: 30 browser processes holding 25-55 threads each consumed 727 of
this container's 1000-PID cgroup budget, at which point the kanban
dispatcher could no longer fork workers ("0 workers spawned") and agent
tool calls hung with a stuck callback. Everything looked "down" while the
gateway itself was perfectly healthy.

Kills any chromium/agent-browser process older than MAX_AGE_SECONDS. A
browser genuinely in use by a running task is far younger than the
threshold, so active work is not disturbed -- only sessions that were
abandoned hours ago.

SIGTERM first, then SIGKILL for anything that ignores it. Child processes
of a killed browser die with it, so killing the oldest few usually frees
most of the budget.

Runs as a pure script (no LLM call) so it keeps working even when the
account is rate-limited -- and, importantly, when PID exhaustion has
already broken the agent path. Prints a summary only when it actually
killed something; empty stdout is treated as "nothing to do".
"""
import os
import signal
import time

MAX_AGE_SECONDS = 3600
PATTERNS = ("chromium", "agent-browser", "chrome_crashpad")
CLOCK_TICKS = os.sysconf("SC_CLK_TCK")


def uptime_seconds() -> float:
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def process_age(pid: str, up: float):
    """Seconds since this pid started, or None if it can't be read."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            data = f.read()
        # comm field can contain spaces/parens -- everything after the last
        # ')' is the stable part, where starttime is field 22 overall (index
        # 19 counting from the field right after comm).
        after = data[data.rindex(")") + 2:].split()
        starttime_ticks = int(after[19])
        return up - (starttime_ticks / CLOCK_TICKS)
    except (OSError, ValueError, IndexError):
        return None


def cmdline(pid: str) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""


def stale_browser_pids():
    up = uptime_seconds()
    me = os.getpid()
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        cmd = cmdline(pid)
        if not any(p in cmd for p in PATTERNS):
            continue
        age = process_age(pid, up)
        if age is not None and age > MAX_AGE_SECONDS:
            out.append((int(pid), age, cmd[:60]))
    return out


def main() -> None:
    targets = stale_browser_pids()
    if not targets:
        return

    killed = []
    for pid, age, cmd in targets:
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append((pid, age))
        except ProcessLookupError:
            continue  # already gone (likely a child of one we just killed)
        except OSError:
            continue

    time.sleep(3)

    for pid, _age in killed:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except OSError:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    if killed:
        oldest = max(age for _pid, age in killed)
        print(
            f"Reaped {len(killed)} stale browser process(es) "
            f"(oldest {oldest / 3600:.1f}h). "
            f"PIDs now {open('/sys/fs/cgroup/pids.current').read().strip()}"
            f"/{open('/sys/fs/cgroup/pids.max').read().strip()}."
        )


if __name__ == "__main__":
    main()
