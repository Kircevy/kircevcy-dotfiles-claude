#!/usr/bin/env bash
set -euo pipefail

ARG="${PITFALL_ARG:-}"

if [ -z "$ARG" ]; then
  echo "ERROR: /pitfall-add requires '<trigger> → <mitigation>' as argument."
  exit 1
fi

if [[ "$ARG" == *$'\n'* ]]; then
  echo "ERROR: /pitfall-add bullet must be a single line. Multi-line input is not allowed (one pitfall per invocation)."
  exit 1
fi

if [[ "$ARG" != *"→"* && "$ARG" != *"->"* ]]; then
  echo "ERROR: /pitfall-add expects 'TRIGGER → MITIGATION' (use → or ->). Got: $ARG"
  exit 1
fi

ARG="${ARG//->/→}"

mkdir -p ~/.claude/pitfalls
printf -- '- %s\n' "$ARG" >> ~/.claude/pitfalls/staging.md
echo "Staged to ~/.claude/pitfalls/staging.md. Drain into pages/index.md on next distill."
