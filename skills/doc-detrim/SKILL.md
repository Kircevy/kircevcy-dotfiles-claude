---
name: doc-detrim
description: Audit agent-written documentation (CLAUDE.md, SKILL.md, README, agent memory) for over-description and propose trims. Use when the user says "trim this doc", "any over-description", "this is over-explained", "clean up over-explanation", or hands over an agent-written doc that reads as bloated or defensive.
argument-hint: "[doc files to trim]"
---

$ARGUMENTS
Audit this doc for over-description. The reader is a capable agent that can reason from naming and read referenced code. Flag and propose to trim: rationale repeated >1×; rules / tag-sets / lists restated across sections; justifying parentheticals after self-evident statements; defensive prose against dead or hypothetical workflows; behavior the code self-documents; symbol explanations the naming makes obvious. Bias toward trimming — keep only what changes behavior or removes real ambiguity.
