# right-tail

AI-driven code-review loop that closes the gap between AI-generated code and PR-ready quality — before you push.

Two modes:

- **Iterative** — writer writes, evaluator reviews, writer revises. Loops until no HIGH or CRITICAL comments remain.
- **Gaussian** — N independent attempts (no feedback), scored with a statistical threshold. Early exits when the best attempt crosses `z`σ above the mean ([CLT](https://en.wikipedia.org/wiki/Central_limit_theorem) kicks in after ~30 samples).

Both the writer and evaluator are powered by the **Claude Code CLI** (`claude --print`) with full filesystem access. The evaluator receives repo context (file tree, manifests, README) to leave comments grounded in project conventions.

## Install

```bash
pip install right-tail           # PyPI (coming soon)
# or from source:
pip install -e .
```

Requires Python 3.11+ and the [Claude Code CLI](https://claude.ai/code) installed and authenticated.

## Usage

### Iterative mode

```bash
right-tail \
  --mode iterative \
  --task "Add JWT authentication middleware to the Django API" \
  --repo /path/to/your/repo \
  --base main \
  --max-iterations 10
```

### Gaussian mode

```bash
right-tail \
  --mode gaussian \
  --task "Refactor the product search endpoint to use a GSI" \
  --repo /path/to/your/repo \
  --base main \
  --samples 30 \
  --p-threshold 0.05 \
  --min-samples 10
```

### All flags

| Flag | Default | Description |
|---|---|---|
| `--task` | required | Natural language description of the coding task |
| `--mode` | `iterative` | `iterative` or `gaussian` |
| `--repo` | `.` | Path to the target git repository |
| `--base` | current branch | Base branch to create attempt branches from |
| `--model` | `claude-haiku-4-5-20251001` | Claude model for both writer and evaluator |
| `--max-iterations` | `10` | [iterative] Max revision cycles before giving up |
| `--samples` | `30` | [gaussian] Max independent attempts |
| `--min-samples` | `10` | [gaussian] Minimum samples before checking threshold |
| `--p-threshold` | — | [gaussian] One-tailed p-value (e.g. `0.05`); converted to z internally |
| `--z-threshold` | `2.0` | [gaussian] Direct z-score threshold |
| `--keep-branches` | `false` | Retain all attempt branches (not just the winner) |

## The Right-Tail Score

Every attempt is scored by the evaluator using:

```
right_tail_score = quality_score − weighted_penalty
```

| Component | Description |
|---|---|
| `quality_score` | 0–100, holistic rating: correctness, idioms, security, test coverage, fit with codebase |
| `weighted_penalty` | Sum of per-comment weights: `low=1`, `medium=2`, `high=3`, `critical=4` |
| `right_tail_score` | Net score. Higher = better. Can go negative if issues are severe. |

The name comes from the statistical goal: in Gaussian mode, we hunt for attempts that land in the **right tail** of the score distribution — significantly better than average.

## How it works

```
right-tail
  ├─ git.py           — branch per attempt: right-tail/{mode}-{id}-attempt-{n}
  ├─ agents/
  │   ├─ writer.py    — spawns: claude --print --allowedTools Edit,Write,Bash
  │   └─ evaluator.py — spawns: claude --print; injects repo context + diff
  ├─ modes/
  │   ├─ iterative.py — loops writer→evaluator until no blocking comments
  │   └─ gaussian.py  — N independent attempts, z-test for early exit
  └─ stats.py         — check_threshold(), p_to_z() (scipy optional)
```

The evaluator prompt includes: tracked file tree, key manifest files (`requirements.txt`, `package.json`, etc.), and a README excerpt — so comments reference real project conventions rather than generic advice.

Failed attempt branches are deleted on exit. Pass `--keep-branches` to retain them all.

---

## Benchmarks

Benchmarks run with `--model claude-haiku-4-5-20251001` (default).

### Demo 1 — Django + DynamoDB: `bulk_decrement_stock`

**Repo:** `demos/django-dynamo` — Django REST API backed by PynamoDB (DynamoDB).  
**Task:** Implement `bulk_decrement_stock(items)` with rollback on insufficient stock, plus tests.  
**Mode:** Iterative, `--max-iterations 3`

| Attempt | Quality | Penalty | Right-Tail Score | High/Critical |
|---|---|---|---|---|
| 1 | 35 | 44 | **-9** | 10 |
| 2 | 68 | 9 | **59** | 1 |
| 3 | 35 | 20 | **15** | 5 |

**Result:** Max iterations reached. Best attempt: **#2** (score **59**).

Attempt 1 was penalized heavily for missing error chaining, bare exception handling, no `.gitignore`, and race condition risks. Attempt 2 addressed most issues (added `version` attribute for optimistic locking, proper `UpdateError` chaining, `.gitignore`), with only one remaining blocking comment about DynamoDB `TransactWriteItems` for true atomicity. Attempt 3 regressed — a reminder that iterative mode is not guaranteed to improve monotonically.

---

### Demo 2 — React + Redux: login state

**Repo:** `demos/react-redux` — React 18 + Redux Toolkit + TypeScript.  
**Task:** Implement `loginUser` async thunk, wire `LoginForm` to dispatch it, add slice tests.  
**Mode:** Gaussian, `--samples 5 --min-samples 3 --p-threshold 0.1` (z ≈ 1.28)

| Attempt | Quality | Penalty | Right-Tail Score | Mean ± Std | Z-Score |
|---|---|---|---|---|---|
| 1 | 80 | 7 | **73** | 73.0 ± 0.0 | — |
| 2 | 72 | 8 | **64** | 68.5 ± 6.4 | -0.71 |
| 3 | 70 | 10 | **60** | 65.7 ± 6.7 | -0.85 |
| 4 | 83 | 6 | **77** | 68.5 ± 7.9 | +1.08 |
| 5 | 78 | 8 | **70** | 68.8 ± 6.8 | +0.18 |

**Result:** Completed all 5 samples without crossing z ≥ 1.28. Best attempt: **#4** (score **77**).

Variance across attempts was 6.8 points of std — typical for a well-defined task where the model consistently handles the core implementation but differs in test depth and TypeScript strictness. Attempt 4 scored highest with quality 83 and only 2 low-priority comments (missing `logout` thunk, no loading skeleton in `LoginForm`). With 30 samples the distribution would stabilize and the threshold would more reliably fire on genuine outliers.

---

## Demo repos

| Repo | Stack | Demo task |
|---|---|---|
| `demos/django-dynamo` | Django 4.2, PynamoDB, DRF, moto | `bulk_decrement_stock` with rollback |
| `demos/react-redux` | React 18, Redux Toolkit, TypeScript, Vitest | Full `loginUser` async thunk + UI wiring |

Both repos are self-contained with git initialized. Run `right-tail` directly against them as shown above.
