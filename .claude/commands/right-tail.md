Run `right-tail` against the current repository. The user's task is: $ARGUMENTS

Steps:
1. First verify `right-tail` is installed: run `right-tail --help`. If it fails, tell the user to run `pip install git+https://github.com/ayanopt/right-tail.git` and stop.

2. Identify the current repo root and base branch by running `git rev-parse --show-toplevel` and `git rev-parse --abbrev-ref HEAD`.

3. If $ARGUMENTS is empty, ask the user what coding task they want right-tail to attempt.

4. Ask the user which mode they want:
   - **iterative** — writer revises based on evaluator feedback until no HIGH/CRITICAL comments remain
   - **gaussian** — N independent attempts scored statistically; returns the best (good for exploring solution variance)
   
   If the user seems unsure: suggest iterative for focused tasks, gaussian when you want the best of several independent tries.

5. Ask if they want any non-default flags:
   - Iterative: `--max-iterations` (default 10)
   - Gaussian: `--samples` (default 30), `--p-threshold` (e.g. 0.05), `--min-samples` (default 10)
   - Either: `--model` (default claude-haiku-4-5-20251001), `--keep-branches`

6. Run the command with Bash, streaming output so the user can watch progress:
   ```
   right-tail --mode <mode> --task "<task>" --repo <repo-root> --base <branch> [extra flags]
   ```

7. After it completes, summarize:
   - Winning branch name
   - Final right-tail score (= quality_score − weighted_penalty)
   - How many iterations/samples it took
   - Whether it hit the success threshold or exhausted attempts
   - Top remaining comments from the winning attempt (if any)
