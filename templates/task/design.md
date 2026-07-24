# Design notes — <task title>

**Status:** <exploring | decided>

## Problem

<What choice this task had to make, and the constraints.>

## Options considered

### Option A — <name>
<What it means; concrete example consequence.>

### Option B — <name>
<Same.>

## Chosen

<Which and why, in a few sentences. If this was a one-way door, link the
message-queue decision item / resulting ADR instead of deciding here.>

## Core fit

**Agent substitution:** <pass — why another agent runtime preserves the behavior>
**Provider substitution:** <pass | not-applicable — why another provider preserves it>
**Repository substitution:** <pass — why an unrelated adopted repository needs it>
**User-global writes:** none
**Why AgentFold core:** <why this is not local config, a product service, private overlay, or separate plugin/repository>
**Thin adapter:** <none | canonical=<path>; optional=yes; policy=none; writes=repo-only>
