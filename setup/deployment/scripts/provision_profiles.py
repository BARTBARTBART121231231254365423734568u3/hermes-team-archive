#!/usr/bin/env python3
"""Idempotent persistent paths for root and new profile homes; no deletion."""
import os
from pathlib import Path
import subprocess

ROOT = Path(os.environ.get("HERMES_OPS_HOME", "/root/.hermes"))


def ensure_link(link, target):
    target.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() != target.resolve():
            raise RuntimeError("Unexpected existing symlink: " + str(link))
        return
    if link.exists():
        # Preserve pre-existing data. Migration/merge requires explicit handling.
        if any(link.iterdir()):
            raise RuntimeError("Nonempty directory needs migration before linking: " + str(link))
        link.rmdir()
    link.symlink_to(target, target_is_directory=True)


def main():
    ensure_link(Path("/root/projects"), ROOT / "projects")
    ensure_link(Path("/root/.config/gh"), ROOT / "gh-config")
    ensure_link(Path("/root/.cache/ms-playwright"), ROOT / "ms-playwright-cache")
    for home in sorted((ROOT / "profiles").glob("*/home")):
        ensure_link(home / ".cache/ms-playwright", ROOT / "ms-playwright-cache")
        subprocess.run(["git", "config", "--file", str(home / ".gitconfig"), "--replace-all", "credential.helper",
                        "!/usr/bin/env GH_CONFIG_DIR=/root/.hermes/gh-config /usr/bin/gh auth git-credential"], check=True)


if __name__ == "__main__":
    main()
