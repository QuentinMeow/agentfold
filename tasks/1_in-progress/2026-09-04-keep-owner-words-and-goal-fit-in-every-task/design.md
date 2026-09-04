# Design notes — Keep the owner's words and a goal fit in every task

**Status:** decided

## Problem

The owner asked on 2026-09-04 that every task keep the owner's idea, that owner-stated
requirements be told apart from agent-added ones, that one full picture of the
repository's end goals exist so agents cannot drift toward goals they generated
themselves, and that every non-trivial task compare goal, current state, and request
before work, with a conflict decided by the owner instead of worked around. Constraints:
`templates/` is the only home of a schema and every schema has a reconciler check
(`templates/README.md`); the owner's standing rule that original requirements live
verbatim in a separate file agents only append to; committed records are judged by the
grammar they were written under
(`memory/decisions/2026-08-01-immutable-records-are-judged-at-their-written-grammar.md`);
`tasks/AGENTS.md` sits at its 60-line budget; and the unqueued-ask scanner reads a visible
blockquote as actionable prose while treating fenced code as data.

## Options considered

### Option A — A `## Requested` section inside `task.md`
The owner's words as dated blockquote entries at the top of the file every reader already
opens (the r43 research proposal). Consequence: an agent editing acceptance criteria edits
the file that holds the owner's words, so an accidental rewrite of a quote is one
keystroke away and only a frozen-quote check could catch it; a blockquote is actionable
prose to the unqueued-ask scanner, so an owner sentence such as "let human decide" would
be refused as an unqueued ask.

### Option B — A separate `requirements.md` per task
Owner words only, dated entries in fenced `text` blocks, append-only; interpretation
stays in `task.md`. Consequence: the task folder grows to six files and `tasks/AGENTS.md`
needs a row, but the file agents may not edit is physically separate from the one they
edit daily, and a fence keeps the bytes exact and is data to every scanner.

### Option C — A separate owner-statements ledger under `roadmap/`
One file holding every owner sentence, cited from tasks and goals. Consequence: a quote
that belongs beside its goal or its task lives elsewhere, and the ledger has to be kept
in sync with both, a second source of truth for the same words.

### Option D — Inline `[NEEDS CLARIFICATION]` markers, as spec-kit does
An unclear requirement is marked inline in `task.md`. Consequence: the marker is an ask
with no queue item, which `message-queue/AGENTS.md` forbids, and the person who can answer
it never sees it.

### Option E — Per-requirement fingerprints, as Doorstop does
Each requirement is hashed and a link is marked suspect when the hash changes.
Consequence: a tool and a hash column in every task of a repository whose records are
plain Markdown read by people; the title copy in `Serves:` and a dated entry give the same
suspect-link signal in plain text.

## Chosen

Option B for the owner's words, because the owner's standing rule outranks Option A's
smaller footprint; labelled acceptance criteria and a `## Fit` section in `task.md`; goal
entries with provenance and a confirmation state in `roadmap/desired-state.md`, one per
copy of the goal template; and four reconciler check ids (`task-provenance`,
`task-provenance-advice`, `roadmap-goals`, `roadmap-goals-advice`) activated by task-id
date, so a record written before 2026-09-04 is never asked for bytes its author could not
have written. Option D is replaced by the `unclear` fit value with a queue path, and
Option E by the title copy in `Serves:`. The one rule change, that an owner statement is
transcribed straight into a confirmed goal entry with no decision item, is a two-way door
on a README rule and is recorded in
`memory/decisions/2026-09-04-owner-statements-become-goal-entries.md`.

## Core fit

**Agent substitution:** pass — every mechanism is a Markdown schema plus a stdlib check; any agent that can copy a template and run `reconcile.py --check` meets the same refusals, and no step names a runtime.
**Provider substitution:** not-applicable — nothing here talks to GitHub or any other provider; a provider URL in an entry heading is data, never a call.
**Repository substitution:** pass — an adopted repository with owner requests, tasks, and a roadmap needs exactly this separation, and the checks read only `tasks/`, `roadmap/desired-state.md`, and `message-queue/`, all of which the harness already creates there.
**User-global writes:** none
**Why AgentFold core:** the schema lives in `templates/` and its check in the reconciler, the two places `templates/README.md` says a file format and its enforcement must live; it is neither local configuration, a product service, a private overlay, nor a plugin.
**Thin adapter:** none

## Sources outside the record

The separate per-task `requirements.md` follows the owner's standing preference, stated on
2026-08-28 when the orchestration skill was commissioned and kept in the main agent's memory
as a paraphrase: original requirements are stored verbatim in a separate file agents never
edit except to append new owner words, and derived items are labelled. A paraphrase is not
owner words, so it lives here and not in `requirements.md`.
