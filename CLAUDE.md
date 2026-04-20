# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup & Commands

```bash
pip install -e ".[dev]"        # install in editable mode
right-tail --help              # verify CLI works
```

Run iterative mode against a repo:
```bash
right-tail --mode iterative --task "add a sum() function to utils.py" --repo .
```

Run gaussian mode with a custom p-value:
```bash
right-tail --mode gaussian --task "..." --samples 30 --p-threshold 0.05 --min-samples 10
```

## Architecture

`right-tail` orchestrates two Claude Code CLI subprocesses — a **writer** and an **evaluator** — against a target git repo. It has two modes:

- **Iterative** (`modes/iterative.py`): writer writes code → evaluator reviews → repeat until no HIGH/CRITICAL comments
- **Gaussian** (`modes/gaussian.py`): N independent writer attempts, each scored, early exit when best score crosses `z`σ above the running mean

### The Right-Tail Score

Core metric: `right_tail_score = quality_score - weighted_penalty`

- `quality_score` (0–100): holistic rating from the evaluator agent (correctness, clarity, idioms, tests)
- `weighted_penalty`: sum of per-comment weights — `low=1, medium=2, high=3, critical=4`
- Higher score = better. The gaussian mode hunts for attempts in the **right tail** of the score distribution (2σ above mean by default).

Defined in `models.py` as `Attempt.build()` which computes both fields automatically.

### Data flow

```
CLI (cli.py)
  └─ modes/iterative.py or modes/gaussian.py
       ├─ git.py          — branch create/diff/cleanup via subprocess git
       ├─ agents/writer.py   — spawns: claude --print --allowedTools Edit,Write,Bash (prompt via stdin)
       ├─ agents/evaluator.py — spawns: claude --print (prompt via stdin), injects repo context + diff, parses JSON {quality_score, comments}
       └─ stats.py         — z-score + p_to_z conversion (scipy optional)
```

Each attempt gets its own branch: `right-tail/{mode}-{run_id}-attempt-{n}`. Failed branches are deleted on exit unless `--keep-branches` is set.

### Evaluator JSON contract

The evaluator prompt demands this exact structure:
```json
{
  "quality_score": 85,
  "comments": [
    {"file": "src/foo.py", "line": 12, "priority": "high", "message": "...", "suggestion": "..."}
  ]
}
```
Parsing lives in `agents/evaluator.py` — strips markdown fences before `json.loads`.

### Statistical threshold (gaussian mode)

`stats.py:check_threshold()` computes a one-sample z-test over `right_tail_score` values. Needs `len(attempts) >= min_samples` (default 10) before firing. `p_to_z()` uses `scipy.stats.norm.ppf` when available, falls back to a lookup table.
