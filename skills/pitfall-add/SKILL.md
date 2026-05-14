---
name: pitfall-add
description: Append a trigger→mitigation pitfall to staging. Use when a mistake just got corrected and the pattern should fire pre-action next time. Also use when user says "remember not to X" or "next time, do Y instead of X".
compatibility: Claude Code
argument-hint: "<trigger> → <mitigation> [→ incident-slug.md]"
---

# /pitfall-add

!```bash
PITFALL_ARG="$(cat <<'__PITFALL_EOF__'
$ARGUMENTS
__PITFALL_EOF__
)"
PITFALL_ARG="$PITFALL_ARG" bash "${CLAUDE_SKILL_DIR}/append.sh"
```
