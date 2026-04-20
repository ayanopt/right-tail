from __future__ import annotations

import uuid
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..agents.evaluator import run_evaluator
from ..agents.writer import run_writer
from ..git import branch_has_commits, checkout, create_branch, get_diff
from ..models import Attempt
from ..stats import check_threshold, p_to_z, summary_stats

console = Console()


def run_gaussian(
    repo: Path,
    task: str,
    base: str,
    max_samples: int = 30,
    min_samples: int = 10,
    z: float | None = None,
    p_threshold: float | None = None,
    model: str = "claude-sonnet-4-6",
    keep_branches: bool = False,
) -> Attempt | None:
    if z is None:
        z = p_to_z(p_threshold) if p_threshold is not None else 2.0

    run_id = uuid.uuid4().hex[:8]
    attempts: list[Attempt] = []
    branches_created: list[str] = []

    table = Table(title=f"Gaussian Mode (z={z:.2f}, min_samples={min_samples})", show_lines=True)
    table.add_column("Attempt", style="cyan")
    table.add_column("Quality", style="green")
    table.add_column("Penalty", style="red")
    table.add_column("Right-Tail Score", style="bold yellow")
    table.add_column("Mean ± Std", style="dim")
    table.add_column("Z-Score", style="magenta")

    winner: Attempt | None = None

    for i in range(max_samples):
        branch = f"right-tail/gaussian-{run_id}-attempt-{i + 1}"
        branches_created.append(branch)

        console.print(f"\n[bold]Sample {i + 1}/{max_samples}[/bold] — branch: [cyan]{branch}[/cyan]")
        checkout(repo, base)
        create_branch(repo, branch, base)

        # No feedback loop in gaussian mode — each attempt is independent
        run_writer(repo, task, i + 1, prior_comments=None, model=model)

        if not branch_has_commits(repo, branch, base):
            console.print("[yellow]Writer made no commits — skipping.[/yellow]")
            checkout(repo, base)
            continue

        diff = get_diff(repo, branch, base)
        attempt = run_evaluator(repo, diff, branch, i + 1, model=model)
        attempts.append(attempt)

        stats = summary_stats(attempts)
        z_score = _current_z(attempt, attempts)
        table.add_row(
            str(i + 1),
            str(attempt.quality_score),
            str(attempt.weighted_penalty),
            str(attempt.right_tail_score),
            f"{stats.get('mean', 0):.1f} ± {stats.get('std', 0):.1f}",
            f"{z_score:.2f}" if z_score is not None else "—",
        )
        console.print(table)
        checkout(repo, base)

        if len(attempts) >= min_samples:
            candidate = check_threshold(attempts, z)
            if candidate is not None:
                console.print(f"\n[bold green]EARLY EXIT[/bold green] — attempt {candidate.attempt_id} "
                              f"crossed {z:.2f}σ threshold.")
                console.print(f"Winning branch: [cyan]{candidate.branch}[/cyan]")
                console.print(f"Right-tail score: [bold yellow]{candidate.right_tail_score}[/bold yellow]")
                winner = candidate
                break

    if winner is None:
        console.print(f"\n[yellow]Completed {len(attempts)} samples without crossing threshold.[/yellow]")
        if attempts:
            winner = max(attempts, key=lambda a: a.right_tail_score)
            console.print(f"Best attempt: [cyan]{winner.branch}[/cyan] (right-tail score: {winner.right_tail_score})")

    _print_final_stats(attempts)
    _cleanup(repo, branches_created, keep_branches, winner=winner.branch if winner else None)
    return winner


def _current_z(attempt: Attempt, all_attempts: list[Attempt]) -> float | None:
    if len(all_attempts) < 2:
        return None
    from ..stats import summary_stats
    import math
    stats = summary_stats(all_attempts)
    if stats["std"] == 0:
        return None
    return (attempt.right_tail_score - stats["mean"]) / stats["std"]


def _print_final_stats(attempts: list[Attempt]) -> None:
    if not attempts:
        return
    stats = summary_stats(attempts)
    console.print(
        f"\n[dim]Stats — n={int(stats['n'])} | mean={stats['mean']:.1f} | "
        f"std={stats['std']:.1f} | min={stats['min']:.0f} | max={stats['max']:.0f}[/dim]"
    )


def _cleanup(repo: Path, branches: list[str], keep: bool, winner: str | None) -> None:
    if keep:
        return
    from ..git import delete_branch
    for b in branches:
        if b != winner:
            delete_branch(repo, b)
