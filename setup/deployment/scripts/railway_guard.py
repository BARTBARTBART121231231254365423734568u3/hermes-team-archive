#!/usr/bin/env python3
"""Prevent ambient Railway credentials/context from deploying the wrong project.

This is an accident-prevention guard, not an OS security boundary. Production
credentials must ultimately be scoped at the Railway account/project level.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REAL_CLI = "/opt/railway/railway"
READ_COMMANDS = {
    "status", "logs", "whoami", "list", "version", "help",
}
READ_PAIRS = {("deployment", "list"), ("deployment", "ls"), ("service", "status")}


def read_only(args):
    # Never pass combined help/mutation arguments through an allowlist.
    return args in (["--version"], ["--help"]) or (
        bool(args) and (args[0] in READ_COMMANDS or tuple(args[:2]) in READ_PAIRS)
    )


def clean_environment():
    return {k: v for k, v in os.environ.items() if k not in {
        "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID", "RAILWAY_SERVICE_NAME",
        "RAILWAY_ENVIRONMENT_ID", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_ENVIRONMENT",
    }}


def normalize_repo(value):
    value = value.strip().removesuffix(".git")
    for prefix in ("https://github.com/", "git@github.com:"):
        value = value.removeprefix(prefix)
    return value.lower()


def verify_status(status, target):
    if status["id"] != target["project_id"]:
        raise ValueError("Railway project does not match target manifest")
    environments = [e["node"] for e in status["environments"]["edges"]
                    if e["node"]["id"] == target["environment_id"]]
    if len(environments) != 1:
        raise ValueError("Railway environment does not match target manifest")
    services = [s["node"] for s in environments[0]["serviceInstances"]["edges"]
                if s["node"]["serviceId"] == target["service_id"]]
    if len(services) != 1 or normalize_repo((services[0].get("source") or {}).get("repo") or "") != normalize_repo(target["repository"]):
        raise ValueError("Railway service source does not match target repository")


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, capture_output=True, timeout=90, **kwargs).stdout.strip()


def deploy(manifest, commit, apply=False):
    target = json.loads(Path(manifest).read_text())
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full verified Git commit is required")
    env = clean_environment()
    repo = normalize_repo(run(["git", "remote", "get-url", "origin"]))
    if repo != normalize_repo(target["repository"]):
        raise ValueError("Working directory repository does not match deployment target")
    branch = target["branch"]
    remote = run(["git", "ls-remote", "origin", "refs/heads/" + branch])
    if not remote or remote.split()[0] != commit:
        raise ValueError("Remote branch is not at the requested commit; nothing deployed")
    # Isolated CLI context: never modify a user's/project's shared railway link.
    with tempfile.TemporaryDirectory(prefix="hermes-deploy-") as directory:
        run([REAL_CLI, "link", "--project", target["project_id"],
             "--service", target["service_id"], "--environment", target["environment_id"]], cwd=directory, env=env)
        status = json.loads(run([REAL_CLI, "status", "--json"], cwd=directory, env=env))
        verify_status(status, target)
        print(json.dumps({"verified_target": target, "commit": commit, "apply": apply}))
        if apply:
            print(run([REAL_CLI, "deployment", "redeploy", "--from-source", "--yes",
                       "--project", target["project_id"], "--service", target["service_id"],
                       "--environment", target["environment_id"], "--json"], cwd=directory, env=env))


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if args and args[0] == "deploy-verified":
        parser = argparse.ArgumentParser()
        parser.add_argument("manifest")
        parser.add_argument("--commit", required=True)
        parser.add_argument("--apply", action="store_true")
        options = parser.parse_args(args[1:])
        profile = os.environ.get("HERMES_PROFILE", "")
        home = Path(os.environ.get("HERMES_HOME", os.environ.get("HOME", ""))).as_posix()
        if options.apply and (profile not in ("", "default", "devops") or ("/profiles/" in home and "/profiles/devops" not in home)):
            raise ValueError("Deployment belongs to the devops profile; hand off the task")
        deploy(options.manifest, options.commit, options.apply)
        return 0
    if not read_only(args):
        print("Blocked unverified Railway mutation. Use: railway deploy-verified <target.json> --commit <full-sha> [--apply]. Raw uploads, variable edits, SSH, and target changes require an external operator session.", file=sys.stderr)
        return 2
    return subprocess.call([REAL_CLI, *args])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, subprocess.SubprocessError) as exc:
        print("Deployment guard: " + str(exc), file=sys.stderr)
        sys.exit(2)
