from __future__ import annotations

import uuid
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..agents.evaluator import run_evaluator
from ..agents.writer import run_writer
from ..git import branch_has_commits, checkout, create_branch, get_diff
from ..models import Attempt, Comment

console = Console()


def run_iterative(
    repo: Path,
    task: str,
    base: str,
    max_iterations: int = 10,
    model: str = "claude-sonnet-4-6",
    keep_branches: bool = False,
) -> Attempt | None:
    run_id = uuid.uuid4().hex[:8]
    attempts: list[Attempt] = []
    prior_comments: list[Comment] = []
    branches_created: list[str] = []

    table = Table(title="Iterative Mode Progress", show_lines=True)
    table.add_column("Attempt", style="cyan")
    table.add_column("Quality", style="green")
    table.add_column("Penalty", style="red")
    table.add_column("Right-Tail Score", style="bold yellow")
    table.add_column("High/Critical", style="red")

    for n in range(1, max_iterations + 1):
        branch = f"right-tail/iterative-{run_id}-attempt-{n}"
        branches_created.append(branch)

        console.print(f"\n[bold]Attempt {n}/{max_iterations}[/bold] — branch: [cyan]{branch}[/cyan]")
        checkout(repo, base)
        create_branch(repo, branch, base)

        run_writer(repo, task, n, prior_comments=prior_comments, model=model)

        if not branch_has_commits(repo, branch, base):
            console.print("[yellow]Writer made no commits — skipping evaluation.[/yellow]")
            checkout(repo, base)
            continue

        diff = get_diff(repo, branch, base)
        attempt = run_evaluator(repo, diff, branch, n, model=model)
        attempts.append(attempt)

        blocking = [c for c in attempt.comments if c.priority in ("high", "critical")]
        table.add_row(
            str(n),
            str(attempt.quality_score),
            str(attempt.weighted_penalty),
            str(attempt.right_tail_score),
            str(len(blocking)),
        )
        console.print(table)

        checkout(repo, base)

        if not attempt.has_blocking_comments():
            console.print(f"\n[bold green]SUCCESS[/bold green] — no HIGH/CRITICAL comments on attempt {n}.")
            console.print(f"Winning branch: [cyan]{branch}[/cyan]")
            console.print(f"Right-tail score: [bold yellow]{attempt.right_tail_score}[/bold yellow]")
            _cleanup(repo, branches_created, keep_branches, winner=branch)
            return attempt

        prior_comments = attempt.comments
        console.print(f"[yellow]{len(blocking)} blocking comment(s) — revising...[/yellow]")

    console.print(f"\n[bold red]Max iterations ({max_iterations}) reached without passing.[/bold red]")
    if attempts:
        best = max(attempts, key=lambda a: a.right_tail_score)
        console.print(f"Best attempt: [cyan]{best.branch}[/cyan] (right-tail score: {best.right_tail_score})")
        _cleanup(repo, branches_created, keep_branches, winner=best.branch)
        return best
    return None


def _cleanup(repo: Path, branches: list[str], keep: bool, winner: str) -> None:
    if keep:
        return
    from ..git import delete_branch
    for b in branches:
        if b != winner:
            delete_branch(repo, b)
