# Pitfalls

When about to do anything matching a trigger below, PAUSE. Read mitigation. Open optional incident page (`→ slug.md`) for detailed explaination.

Format: `- TRIGGER → mitigation. [→ incident-slug.md]`

## Git & commits

- About to `git --amend` or `--no-verify` → create new commit; fix underlying hook issue.
- About to `git push` → never push without explicit user authorization; ask first.
- About to add `.gitignore` pattern like `tmp/` → anchor with `/tmp/` to avoid matching at any depth.

## Shell & Bash

- About to add `2>/dev/null` to a Bash call → drop it; noise cheaper than blindness.

## Harness & Claude internals

- About to call blocking Bash/Agent that may run >5 min → cap timeout; prompt cache expires silently otherwise.
- About to edit CLAUDE.md expecting it to apply now → /clear, /compact, or new session — memoized at startup.

## Hooks

- About to combine `set -euo pipefail` with `grep -qP` in a hook → guard the grep; failed match exits 1 and kills script.
- About to emit `systemMessage` JSON from PostToolUse hook stdout → won't reach Claude; use stderr + exit 2 instead.
- About to use `#!/usr/bin/env bash` in a hook script → use `/usr/bin/bash` per hooks/lib/README.md.

## Skills

- About to hardcode `~/.claude/...` path in a skill script → use `${CLAUDE_PLUGIN_ROOT}` or BASH_SOURCE-relative resolution.

## Pueue & long-running tasks

- About to launch high-resource compute task in daytime → defer to overnight; disrupts user's other sessions.
- About to poll `pueue status`/`pueue log` in a sleep loop → use `pueue follow <id>` in background; notifies on completion.
- About to `pueue add` compute work, build, multi-agent fanout, or uncertain-runtime background bash → run /preflight-check first.

## Coding discipline

- About to declare "ready to deploy" from merged code → verify registry alias, env vars, bundle on target host first.
- About to put `import X` inside a function → hoist to module top, even when avoiding circular import.
- About to write code comment referencing task/fix/caller → drop it; only WHY-comments belong, not WHAT or WHY-NOW.

## Writing & voice

- About to surface tool-result paths, line numbers, grep hits in user-facing prose → stash in thinking; surface only findings user asked for.
- About to write "Actually," or "Wait," mid-response reversing earlier tentative claim → explore in thinking, commit only after evidence.

## Working with user instructions

- About to redeploy/kill/touch OSSH or OSSZ deployment → live trading runs there; code-only follow-up unless explicit auth.
- About to scaffold multi-component plan after user hinted "over-complicated" → quote simpler option back, confirm before scaffolding.

## A-share domain

- About to detect A-share limit-up/down by price equality with `limit_up`/`limit_down` → use orderbook state (empty ask/bid book).
- About to handle A-share 6-digit code as int or unpadded string → cast `str`, `.zfill(6)` before any ClickHouse join.

## Quant methodology

- About to run backtest on OOF / in-sample period → only OOS test period is valid for backtest.
- About to select or rank features by the tune/early-stopping metric → use test-set metric; tune-metric selection is look-ahead bias.

## Scheduling

- About to schedule cron at `0 *` or `30 *` minute → pick `:03`, `:07`, `:57` etc.; fleet collides at `:00`/`:30`.

## Data pipeline (rql2)

- About to `delete_*` then `insert_*` in rql2 daily script → `sys.exit(1)` first if upstream is empty; otherwise blanks partition silently.

## MLflow

- About to download N MLflow runs' artifacts into shared `dst_path` → one `dst_path` per run; otherwise picker silently keeps returning same file.
