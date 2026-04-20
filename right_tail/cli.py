from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(name="right-tail", help="AI-driven code-review loop with statistical success criteria.")


class Mode(str, Enum):
    iterative = "iterative"
    gaussian = "gaussian"


@app.command()
def run(
    task: str = typer.Option(..., "--task", "-t", help="Natural language description of the coding task."),
    mode: Mode = typer.Option(Mode.iterative, "--mode", "-m", help="Loop mode: iterative or gaussian."),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Path to the git repository."),
    base: str = typer.Option("", "--base", "-b", help="Base branch to branch off (default: current branch)."),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model", help="Claude model for both agents."),
    max_iterations: int = typer.Option(10, "--max-iterations", help="[iterative] Max revision cycles."),
    samples: int = typer.Option(30, "--samples", help="[gaussian] Maximum number of independent attempts."),
    min_samples: int = typer.Option(10, "--min-samples", help="[gaussian] Minimum samples before checking threshold."),
    p_threshold: float = typer.Option(None, "--p-threshold", help="[gaussian] One-tailed p-value threshold (e.g. 0.05)."),
    z_threshold: float = typer.Option(None, "--z-threshold", help="[gaussian] Z-score threshold (default: 2.0)."),
    keep_branches: bool = typer.Option(False, "--keep-branches", help="Retain all attempt branches after run."),
) -> None:
    """Run the right-tail code-writing loop against a git repository."""
    repo = repo.resolve()

    if not (repo / ".git").exists():
        typer.echo(f"Error: {repo} is not a git repository.", err=True)
        raise typer.Exit(1)

    from .git import get_current_branch
    effective_base = base or get_current_branch(repo)

    if mode == Mode.iterative:
        from .modes.iterative import run_iterative
        run_iterative(
            repo=repo,
            task=task,
            base=effective_base,
            max_iterations=max_iterations,
            model=model,
            keep_branches=keep_branches,
        )
    else:
        from .modes.gaussian import run_gaussian
        run_gaussian(
            repo=repo,
            task=task,
            base=effective_base,
            max_samples=samples,
            min_samples=min_samples,
            z=z_threshold,
            p_threshold=p_threshold,
            model=model,
            keep_branches=keep_branches,
        )


if __name__ == "__main__":
    app()
