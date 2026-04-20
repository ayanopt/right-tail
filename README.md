# right-tail

AI-driven code-review loop that closes the gap between AI-generated code and PR-ready quality — before you push.

Two modes:

- **Iterative** — writer writes, evaluator reviews, writer revises. Loops until no HIGH or CRITICAL comments remain.
- **Gaussian** — N independent attempts (no feedback), scored with a statistical threshold. Early exits when the best attempt crosses `z`σ above the mean ([CLT](https://en.wikipedia.org/wiki/Central_limit_theorem) kicks in after ~30 samples).

Both the writer and evaluator are powered by the **Claude Code CLI** (`claude --print`) with full filesystem access. The evaluator receives repo context (file tree, manifests, README) to leave comments grounded in project conventions.

## Install

```bash
# From GitHub (latest)
pip install git+https://github.com/ayanopt/right-tail.git

# Specific version/tag
pip install git+https://github.com/ayanopt/right-tail.git@v0.1.0

# From source (for development)
git clone https://github.com/ayanopt/right-tail.git
cd right-tail && pip install -e .
```

Requires Python 3.11+ and the [Claude Code CLI](https://claude.ai/code) installed and authenticated.

## Claude Code skill

Install a `/right-tail` slash command into any Claude Code session:

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/right-tail.md \
  https://raw.githubusercontent.com/ayanopt/right-tail/main/.claude/commands/right-tail.md
```

Then inside any Claude Code session:

```
/right-tail add JWT auth middleware to the Django API
```

Claude will ask for the mode (iterative/gaussian) and any extra flags, then run right-tail against the current repo.

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

**Repo:** `demos/django-dynamo` — Django REST API backed by PynamoDB + boto3.  
**Task:** Implement `bulk_decrement_stock(items)` using DynamoDB `TransactWriteItems` for atomicity, with pre-validation and rollback. Wire a `POST /api/checkout/` endpoint. Add moto-based tests.  
**Mode:** Iterative, `--max-iterations 5`

Each iteration builds on the previous branch — the writer inherits its own working code and only needs to address the evaluator's comments.

| Attempt | Quality | Penalty | Right-Tail Score | High/Critical |
|---|---|---|---|---|
| 1 | 38 | 18 | **20** | 4 |
| 2 | 62 | 19 | **43** | 3 |
| 3 | 68 | 15 | **53** | 3 |
| 4 | 32 | 21 | **11** | 5 |
| 5 | 72 | 9 | **63** | 1 |

**Result:** Max iterations (5) reached. Best attempt: **#5** (score **63**, 1 remaining blocker).

General trend was upward (20 → 43 → 53 → 63), with one regression at attempt 4 where the writer over-refactored and broke existing assumptions. By attempt 5 the implementation used `TypeSerializer` from boto3 for correct DynamoDB JSON serialization, module-level client caching, `ConditionExpression` for atomic stock enforcement, and a wired `/api/checkout/` endpoint. The single remaining blocker was a reviewer note about TOCTOU window documentation.

**To reproduce:**
```bash
cd demos/django-dynamo && git init && git add -A && git commit -m "baseline"
right-tail --mode iterative \
  --task "Add bulk_decrement_stock using TransactWriteItems with pre-validation, rollback, and a POST /api/checkout/ endpoint. Add moto tests." \
  --repo demos/django-dynamo --base main --max-iterations 5
```

---

### Demo 2 — React + Redux: full login/logout flow

**Repo:** `demos/react-redux` — React 18 + Redux Toolkit + TypeScript.  
**Task:** Add `loginUser` + `logoutUser` async thunks to `authSlice.ts` (localStorage persistence, status/error tracking), wire `LoginForm`, add `LogoutButton` component, write slice tests.  
**Mode:** Gaussian, `--samples 30 --min-samples 10 --p-threshold 0.05` (z = 1.64)

| Attempt | Quality | Penalty | Right-Tail Score | Mean ± Std | Z-Score |
|---|---|---|---|---|---|
| 1 | 78 | 11 | **67** | 67.0 ± 0.0 | — |
| 2 | 72 | 15 | **57** | 62.0 ± 7.1 | -0.71 |
| 3 | 68 | 12 | **56** | 60.0 ± 6.1 | -0.66 |
| 4 | 68 | 11 | **57** | 59.2 ± 5.2 | -0.43 |
| 5 | 76 | 8 | **68** | 61.0 ± 6.0 | +1.17 |
| 6 | 78 | 9 | **69** | 62.3 ± 6.3 | +1.07 |
| 7 | 62 | 17 | **45** | 59.9 ± 8.7 | -1.71 |
| 8 | 70 | 16 | **54** | 59.1 ± 8.3 | -0.62 |
| 9 | 72 | 7 | **65** | 59.8 ± 8.0 | +0.65 |
| 10 | 65 | 20 | **45** | 58.3 ± 8.9 | -1.50 |
| **11** ✓ | **87** | **5** | **82** | 60.5 ± 11.0 | **+1.95** |

**Result:** Early exit at attempt **#11** — z = 1.95 crossed the 1.64σ threshold (p = 0.05). Score **82**, 5 low-priority comments remaining, none blocking.

Attempt 11 scored quality 87 with only 5 low-priority comments. The winning implementation included localStorage hydration on initial load, 30+ test cases covering all reducer states and localStorage side-effects, and a `LogoutButton` component that conditionally renders only when authenticated. The distribution (mean=60.5, std=11.0) shows real variance across attempts — some wrote minimal tests (high penalty), others wrote thorough suites (low penalty, higher quality). The threshold correctly identified an outlier rather than an average run.

**To reproduce:**
```bash
cd demos/react-redux && git init && git add -A && git commit -m "baseline"
right-tail --mode gaussian \
  --task "Add loginUser + logoutUser thunks to authSlice.ts with localStorage, wire LoginForm, add LogoutButton, write tests." \
  --repo demos/react-redux --base main --samples 30 --min-samples 10 --p-threshold 0.05
```

---

## Demo repos

| Repo | Stack | Demo task |
|---|---|---|
| `demos/django-dynamo` | Django 4.2, PynamoDB, boto3, DRF, moto | `bulk_decrement_stock` + checkout endpoint |
| `demos/react-redux` | React 18, Redux Toolkit, TypeScript, Vitest | `loginUser`/`logoutUser` thunks + UI |

Both demos need a local git init before running (the `git init` step is shown in each reproduce block above). The demo files are tracked in this repo as plain source — no submodules.
