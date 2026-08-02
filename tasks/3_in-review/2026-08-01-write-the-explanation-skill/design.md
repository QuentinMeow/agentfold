# Design notes — write the explanation skill

**Status:** decided

Full reasoning, the evidence behind each rule, and the alternatives rejected are in
`docs/designs/explaining-work-to-the-owner.md`. This file records the choice and its
core-fit receipt.

## Problem

The rules for writing something a human will read were spread across four documents that
each owned one surface, and none of them stated the craft that all four need: lead with the
conclusion, say what was true before and what is true now, gloss local vocabulary, and make
the file answerable without opening another file.

## Options considered

### Option A — One skill with a router and one file per surface
`SKILL.md` states the craft and routes to `scenarios/<surface>.md`. One statement of the
craft, one place to change it. *Example consequence:* an agent about to open a pull request
reads two files — the router and one scenario — and never loads the other three.

### Option B — Four separate skills
One skill per surface. *Example consequence:* the craft is restated four times, so the
first time a rule changes, three copies silently disagree — which is exactly what
`handbook/principles/single-source-of-truth.md` forbids.

### Option C — More prose in the handbook
Add the rules to `handbook/human-action-guide.md` and `handbook/git-workflow.md`.
*Example consequence:* the material is loaded by every agent on every boot even though it
is needed only when writing, and the root contract's 140-line budget forces it to be cut
down to the abstractions that do not actually change behaviour.

## Chosen

Option A. The craft is identical across surfaces and only the skeleton differs, so a router
plus leaves is the shape that keeps one statement of the craft. Routing stays one level
deep because a second hop gets previewed rather than read.

Nothing here is a one-way door: the skill adds no schema, changes no check, and deleting
the folder returns the repository to its previous behaviour.

## Core fit

**Agent substitution:** pass — the skill is plain markdown with no tool-specific syntax, so
any agent runtime that can read a file can follow it.
**Provider substitution:** pass — only the pull-request scenario names a provider, and it
names GitHub's rendering behaviour as the mechanics of one surface. The section order and
the craft are provider-neutral; another provider needs a different mechanics section, not a
different skill.
**Repository substitution:** pass — every adopted repository whose agents report to a human
needs this, and nothing in it names AgentFold's domain.
**User-global writes:** none
**Why AgentFold core:** the harness already mandates human-facing artifacts — queue items,
handovers, projected pull-request actions — and mandates their schemas. It never said how
to write them, so the quality of every human-facing surface was a function of which agent
happened to write it. That gap is in core's own lifecycle, not in a product or a personal
setup.
**Thin adapter:** none
