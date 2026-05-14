# PITFALLS NOTEBOOK

Recipes for building and maintaining the pitfalls notebook — pre-mistake recall system.

## PURPOSE

Memory captures durable claims; pitfalls captures **trigger → mitigation** pairs. Loaded into every session via `@pitfalls/pages/index.md` so agent recognizes a mistake pattern BEFORE the action, not after.

## ARCHITECTURE

- `pages/index.md` — flat trigger catalog, always loaded. One line per pitfall: trigger pattern + one-line mitigation + optional incident link.
- `pages/<slug>.md` — incident report. Written only when the "why" is non-obvious or the wrong fix is tempting. Linked from index entry.
- `staging.md` — inbox written by `/pitfall-add`. Drained into index on next distill.

## INDEX ENTRY FORMAT

```
- TRIGGER PATTERN → mitigation one-liner. [→ slug.md]
```

Trigger MUST be matchable pre-action (verb-object or "about to X"). Mitigation MUST be actionable in one sentence. Link only if incident page exists.

Examples:

```
- About to run `rm -rf <path>` with variable → expand var first, paste literal path. → rm-rf-empty-var.md
- About to amend pushed commit → create new commit instead.
- About to use `cat | grep` → drop `cat`, `grep PATTERN file`.
```

## INCIDENT PAGE SCHEMA

```markdown
# <Trigger phrase>

**Date**: YYYY-MM-DD
**Trigger**: <exact pattern from index>

## What happened
<one paragraph: situation + action + outcome>

## Root cause
<why the default behavior fails>

## Wrong fix tried
<tempting band-aids that don't work, if any>

## Correct mitigation
<step-by-step or one-liner>

## Future trigger
<phrase to scan for next time — same as index trigger>
```

## ADDING A PITFALL

1. `/pitfall-add "<trigger> → <mitigation>"` — appends single line to `staging.md`.
2. If incident worth detail, also create `pages/<slug>.md` from schema above and append `→ <slug>.md` to the staged line manually.

## DISTILL INSTRUCTION

Drain `staging.md` into `pages/index.md`:

1. Read `staging.md`. Each line already index-ready.
2. Dedup against existing index entries (same trigger → merge mitigation, keep stricter wording).
3. Group by domain if index exceeds ~50 entries. Buckets suggested: `## Git`, `## Shell`, `## Harness`, `## Coding`, `## User conventions`.
4. Sort within bucket by trigger alphabetically (cheap recall).
5. Truncate `staging.md` to empty.

## KEEP / DROP

KEEP: mistakes user corrected, costly errors that wasted >5 min, AI defaults that violate user convention, harness quirks that bit, irreversible-action near-misses.

DROP: in-flight task notes, one-off env glitches, narrow project state, anything already covered in memory pages.

## REVIEW INSTRUCTION

Quarterly: audit `pages/index.md` for entries that no longer trigger (tool changed, convention updated). Move stale entries to `pages/archive.md` with date. Keep incident pages — they remain historical record.

## FIRST-TIME SETUP

Add `@pitfalls/pages/index.md` to `~/.claude/CLAUDE.md` (path relative to CLAUDE.md directory).
