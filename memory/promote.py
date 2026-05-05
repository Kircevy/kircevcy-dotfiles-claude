#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""promote: merge a triaged nugget library into per-status memory files.

Reads ~/.claude/memory/distilled/extracted/_triaged.md (each new bullet
prefixed with `[+]`/`[-]`/`[?]`) and merges into:
  ~/.claude/memory/promoted.md  — accepted, citations stripped (compact)
  ~/.claude/memory/pending.md   — needs review, citations + [?] markers kept
  ~/.claude/memory/rejected.md  — explicitly dropped, citations kept

Merge rules (priority high→low; first claim wins for dedup):
  1. _triaged.md           — new bullets and explicit re-flips
  2. pending.md            — in-place re-flips ([?]→[+]/[-]); bare bullets default to [?]
  3. promoted.md, rejected.md — stable carryover (bare bullets, marker implied by file)

For a fresh rebuild from _triaged.md alone, delete the destination files first.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path.home() / ".claude" / "memory" / "distilled" / "extracted" / "_triaged.md"
OUT = Path.home() / ".claude" / "memory"

H2_RE = re.compile(r"^## (.+)$")
MARKED_BULLET_RE = re.compile(r"^- \[([+\-?])\] (.+)$")
BARE_BULLET_RE = re.compile(r"^- (.+)$")
META_TAIL_RE = re.compile(r"\s*(?:\[[^\]]+\]\s*)*\(×\d+\s+sources?\)\s*$")


def _parse(text: str, default_marker: str | None):
    """Yield (theme, [marker, primary_line, continuation_lines]).

    If default_marker is None: only marker'd bullets `- [+/-/?]` are accepted.
    Otherwise: marker'd bullets win; bare `- ...` bullets fall back to default_marker.
    """
    theme = None
    cur = None  # [marker, primary, [cont_lines]]
    for line in text.splitlines():
        m = H2_RE.match(line)
        if m:
            if cur:
                yield theme, cur
                cur = None
            theme = m.group(1)
            continue
        m = MARKED_BULLET_RE.match(line)
        if m:
            if cur:
                yield theme, cur
            cur = [m.group(1), m.group(2), []]
            continue
        if default_marker is not None:
            m = BARE_BULLET_RE.match(line)
            if m:
                if cur:
                    yield theme, cur
                cur = [default_marker, m.group(1), []]
                continue
        if cur is not None:
            if line.startswith("  ") and line.strip():
                cur[2].append(line)
            else:
                yield theme, cur
                cur = None
    if cur:
        yield theme, cur


def claim_key(primary: str) -> str:
    return META_TAIL_RE.sub("", primary).strip()


def render(buckets: dict[str, list[tuple[str, list[str]]]], header: str, with_cites: bool, with_marker: str | None) -> str:
    lines = [header, ""]
    for theme, items in buckets.items():
        if not items:
            continue
        lines.append(f"## {theme}")
        lines.append("")
        for primary, cont in items:
            text = primary if with_cites else META_TAIL_RE.sub("", primary)
            prefix = f"[{with_marker}] " if with_marker else ""
            lines.append(f"- {prefix}{text}")
            if with_cites:
                lines.extend(cont)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    triaged_text = SRC.read_text()

    # Pass 1: collect claim keys from highest-priority sources for dedup.
    triaged_entries: list[tuple[str, str, str, list[str]]] = []
    triaged_keys: set[str] = set()
    for theme, (mk, primary, cont) in _parse(triaged_text, default_marker=None):
        if not theme or theme.startswith("dropped"):
            continue
        triaged_entries.append((theme, mk, primary, cont))
        triaged_keys.add(claim_key(primary))

    pending_entries: list[tuple[str, str, str, list[str]]] = []
    pending_keys: set[str] = set()
    pending_path = OUT / "pending.md"
    if pending_path.exists():
        for theme, (mk, primary, cont) in _parse(pending_path.read_text(), default_marker="?"):
            if not theme or theme.startswith("dropped"):
                continue
            key = claim_key(primary)
            if key in triaged_keys:
                continue
            pending_entries.append((theme, mk, primary, cont))
            pending_keys.add(key)

    skip_keys = triaged_keys | pending_keys

    # Pass 2: build buckets in render order — stable carryover first, then pending re-flips, then new triaged.
    buckets: dict[str, dict[str, list]] = {
        "+": defaultdict(list),
        "-": defaultdict(list),
        "?": defaultdict(list),
    }

    for marker, name in [("+", "promoted.md"), ("-", "rejected.md")]:
        path = OUT / name
        if not path.exists():
            continue
        for theme, (mk, primary, cont) in _parse(path.read_text(), default_marker=marker):
            if not theme or theme.startswith("dropped"):
                continue
            if claim_key(primary) in skip_keys:
                continue
            buckets[marker][theme].append((primary, cont))

    for theme, mk, primary, cont in pending_entries:
        buckets[mk][theme].append((primary, cont))

    for theme, mk, primary, cont in triaged_entries:
        buckets[mk][theme].append((primary, cont))

    plan = [
        ("+", "promoted.md", "# Promoted memory", False, None),
        ("?", "pending.md", "# Pending review", True, "?"),
        ("-", "rejected.md", "# Rejected (audit)", True, None),
    ]
    counts = {}
    for mk, name, hdr, cites, marker in plan:
        (OUT / name).write_text(render(buckets[mk], hdr, cites, marker))
        counts[mk] = sum(len(v) for v in buckets[mk].values())

    print(f"[+] {counts['+']:>3}  ->  {OUT}/promoted.md  (citations stripped)")
    print(f"[?] {counts['?']:>3}  ->  {OUT}/pending.md   ([?] markers kept)")
    print(f"[-] {counts['-']:>3}  ->  {OUT}/rejected.md")
    if counts["?"]:
        print(f"\n{counts['?']} pending — flip [?] markers in {OUT}/pending.md or {SRC} and re-run.")


if __name__ == "__main__":
    main()
