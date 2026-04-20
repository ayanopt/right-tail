from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_current_branch(repo: Path) -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)


def create_branch(repo: Path, name: str, base: str) -> None:
    _run(["git", "checkout", "-b", name, base], repo)


def checkout(repo: Path, branch: str) -> None:
    _run(["git", "checkout", branch], repo)


def get_diff(repo: Path, branch: str, base: str) -> str:
    return _run(["git", "diff", f"{base}...{branch}"], repo)


def delete_branch(repo: Path, name: str) -> None:
    try:
        _run(["git", "branch", "-D", name], repo)
    except subprocess.CalledProcessError:
        pass


def branch_has_commits(repo: Path, branch: str, base: str) -> bool:
    out = _run(["git", "rev-list", "--count", f"{base}..{branch}"], repo)
    return int(out) > 0
