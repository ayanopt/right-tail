from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..models import Comment


def run_writer(
    repo: Path,
    task: str,
    attempt_id: int,
    prior_comments: list[Comment] | None = None,
    model: str = "claude-haiku-4-5-20251001",
) -> None:
    """Spawn Claude Code CLI to write code and commit it."""
    comments_section = ""
    if prior_comments:
        comments_json = json.dumps(
            [{"file": c.file, "line": c.line, "priority": c.priority, "message": c.message, "suggestion": c.suggestion}
             for c in prior_comments],
            indent=2,
        )
        comments_section = f"\n\nPrevious review comments to address:\n{comments_json}"

    prompt = (
        f"You are a software engineer. Your task:\n\n{task}"
        f"{comments_section}\n\n"
        f"Write or update the implementation to complete the task"
        f"{', addressing all comments above' if prior_comments else ''}. "
        f"Make all necessary file changes, then commit with:\n"
        f"git add -A && git commit -m 'right-tail: attempt {attempt_id}'"
    )

    subprocess.run(
        ["claude", "--print", "--model", model, "--allowedTools", "Edit,Write,Bash"],
        input=prompt,
        cwd=repo,
        text=True,
        check=True,
    )
