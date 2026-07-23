# The queue owns pending actions and filenames expose dependency timing

**Status:** decided
**Date:** 2026-07-23
**Decided-by:** human (directed in chat; transcribed in commits d373243 and 3197f90)
**Description:** Every pending human or durable cross-session agent action has one canonical queue item; its filename says when unresolved work blocks
**Review-by:** 2027-02-15
**Supersedes:** `memory/decisions/2026-07-22-queue-folders-named-by-who-acts-next.md`

## Context

PR #4 asked five detailed human-review questions after its generic queue review had
already been resolved. The PR body became the only copy, so the repository handover
simultaneously reported that nothing needed human attention. Several questions also
bundled unfamiliar terms without alternatives, examples, or source pointers.

The owner required `message-queue/` to become the first-class interaction surface for
human↔agent and durable agent↔agent work. They also chose filename-visible timing:
`blocking-`, `future-blocking-`, and `non-blocking-`.

## Decision

One live queue file owns every pending human action and every action another agent or
session must discover. A PR, issue, chat reply, task, or handover may project that
action by summarizing and linking the live item; it may not originate a durable ask.
Queue files remain projections of durable background stored in tasks, designs, memory,
or code, but they are the canonical identity and delivery state of the pending action.

The path carries three independent dimensions:

- actor folder: `needs-human/` or `needs-agent/`;
- message-kind folder: decision, clarification, review, request, or retry; and
- dependency-timing filename:
  - `blocking-<slug>.md` stops a named task, transition, or operation now;
  - `future-blocking-<slug>.md` permits work until a named date, event, or transition;
  - `non-blocking-<slug>.md` never stops work and states its safe unattended outcome.

The filename is the sole timing class. Class-specific fields name the blocked boundary
or unattended result; there is no duplicate `Blocking` field. A timing change uses
`git mv` and updates all live links in the same coordination commit.

Every human item explains the needed action from zero context, compares meaningful
answers or dispositions, gives a small concrete example, states what happens without
an answer, links a complete durable source, and provides a literal response slot.
Tasks declare their live `Queue actions`; a task in `2_blocked` must reciprocally link
at least one unresolved `blocking-*` item, regardless of whether a human or agent acts
next.

## Alternatives considered

- Keep independent asks in each channel — lower filing cost, but reproduces the PR-only
  action that disappeared from the repository.
- Keep timing only in a metadata field — stable file links, but a zero-context reader
  cannot prioritize from filenames and agents can create contradictory urgency fields.
- Use urgency-first folders — visible ordering, but hides whose move it is and moves
  messages between actor queues when timing changes.
- Require every agent interaction to be live chat — incompatible with independent
  sessions, context compaction, and agent substitution.

## Consequences

Action delivery becomes provider-neutral and mechanically auditable. Renaming an item
when its timing changes requires updating live links, but resolved history remains
untouched. Queue files add small ceremony only for actions that must survive the current
context; agents remain free to choose how they complete the action.

This supersedes
`memory/decisions/2026-07-22-queue-folders-named-by-who-acts-next.md`: actor-first
folders remain, while timing moves from a mutable field into a filename prefix.
