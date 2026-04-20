from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..models import Attempt, Comment


def _gather_repo_context(repo: Path) -> str:
    """Build a compact repo context string for the evaluator prompt."""
    lines: list[str] = []

    # File tree (tracked files only, capped to keep prompt lean)
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        tracked = result.stdout.strip().splitlines()
        # Cap at 80 paths to avoid blowing up the prompt
        shown = tracked[:80]
        tree = "\n".join(f"  {p}" for p in shown)
        if len(tracked) > 80:
            tree += f"\n  ... ({len(tracked) - 80} more files)"
        lines.append(f"Tracked files:\n{tree}")
    except subprocess.CalledProcessError:
        pass

    # Tech-stack hints from key manifest files
    manifests = {
        "requirements.txt": "Python/Django dependencies",
        "Pipfile": "Python/Pipfile dependencies",
        "pyproject.toml": "Python project config",
        "package.json": "Node.js dependencies",
        "go.mod": "Go module",
        "Cargo.toml": "Rust crate",
        "pom.xml": "Java/Maven project",
    }
    found_manifests: list[str] = []
    for filename, label in manifests.items():
        path = repo / filename
        if path.exists():
            try:
                content = path.read_text(errors="replace")[:1500]
                found_manifests.append(f"--- {filename} ({label}) ---\n{content}")
            except OSError:
                pass
    if found_manifests:
        lines.append("Key manifests:\n" + "\n\n".join(found_manifests))

    # README excerpt (first 800 chars) for project-level context
    for readme_name in ("README.md", "README.rst", "README.txt"):
        readme = repo / readme_name
        if readme.exists():
            try:
                excerpt = readme.read_text(errors="replace")[:800]
                lines.append(f"README excerpt:\n{excerpt}")
            except OSError:
                pass
            break

    return "\n\n".join(lines)


def run_evaluator(
    repo: Path,
    diff: str,
    branch: str,
    attempt_id: int,
    model: str = "claude-haiku-4-5-20251001",
) -> Attempt:
    """Spawn Claude Code CLI to review a diff and return a scored Attempt."""
    repo_context = _gather_repo_context(repo)

    prompt = (
        "You are a senior code reviewer with full context of this repository.\n\n"
        "=== REPOSITORY CONTEXT ===\n"
        f"{repo_context}\n\n"
        "=== YOUR TASK ===\n"
        "Review the git diff below. Use the repository context to:\n"
        "- Flag violations of the project's existing patterns and conventions\n"
        "- Catch framework-specific anti-patterns (e.g. Django ORM misuse, Redux best practices)\n"
        "- Identify missing integration points (e.g. missing signal handlers, unconfigured URLs)\n"
        "- Note gaps relative to the project's apparent test strategy\n\n"
        "Output ONLY a JSON object with exactly two keys:\n"
        "1. \"quality_score\": integer 0-100 rating overall quality (correctness, idioms, "
        "security, test coverage, fit with existing codebase).\n"
        "2. \"comments\": array of objects with keys: "
        "\"file\" (string), \"line\" (integer or null), "
        "\"priority\" (low|medium|high|critical), "
        "\"message\" (string describing the issue), "
        "\"suggestion\" (string with concrete fix).\n\n"
        "Output ONLY the JSON object — no markdown fences, no explanation.\n\n"
        "=== DIFF ===\n"
        f"{diff}"
    )

    result = subprocess.run(
        ["claude", "--print", "--model", model],
        input=prompt,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    raw = result.stdout.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    quality_score = int(data["quality_score"])
    comments = [
        Comment(
            file=c["file"],
            line=c.get("line"),
            priority=c["priority"],
            message=c["message"],
            suggestion=c.get("suggestion", ""),
        )
        for c in data.get("comments", [])
    ]

    return Attempt.build(branch, attempt_id, quality_score, comments)
