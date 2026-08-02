# Nothing a human owes holds a Git edge

**Status:** decided
**Date:** 2026-08-01
**Decided-by:** agent (delegated; reversible grammar restriction, judged against three competing designs and executed stage by stage before landing)
**Description:** A needs-human item may withhold only the start of a 0_backlog task or one act with no undo; merging, moving a task through review, and recording it done are revertible and never wait on an answer, and every human item carries an advisory Answer by date
**Review-by:** 2027-01-28
**Amends:** `memory/decisions/2026-07-23-live-queue-obligations-only-weaken-with-evidence.md` (the merge-receipt cleanup condition; the monotonic timing ratchet and the provider-release clause stand); `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md` (which boundaries a `needs-human/` item may bind; the actor/kind/timing model and the three prefixes stand); `memory/decisions/2026-07-23-requested-review-changes-route-through-agent-repair.md` (the re-review's boundary when the repaired change has already merged; the agent-repair-plus-re-review pair stands)

## Context

This repository declares `**Collaboration mode:** async`, whose merge gate
(`handbook/collaboration-modes.md`) has always read *"tests + reconciler; panel for
one-way doors"* — the human belongs to the `pair` column. The queue's boundary grammar
did not know that. It let any `needs-human/` item write `Blocks at: transition:merge`,
so agents could smuggle `pair` behaviour into an `async` repository one file at a time,
and did: of ten live human items, four bound a Git edge.

That produced a deadlock no commit could clear. Two reviews bound `transition:merge` on
ranges that are already ancestors of `main`. Their cleanup ran through
`approved_review_merge_receipt_problem`, which required an exact two-parent merge *in
already-admitted history* carrying the approved bytes. Once the merge happens before the
answer — the ordinary case when the owner answers late — that condition is unsatisfiable
forever, in both directions: the item cannot be resolved and cannot be deleted. The
decision item filed to escape it then bound `transition:complete` on the same three tasks
it asked about, so filing the escape re-created the trap.

Measured on `main` @ `0e63bbe`: `reconcile --check` reported 0 blocking findings while
`reconcile --check --at-transition merge` reported 4.

## Decision

**Nothing a human owes holds a Git edge.** A `needs-human/` item may withhold exactly two
things: the start of a task still in `0_backlog` (`Blocks at: transition:start
task:<id>`), and one act with no undo (`Blocks now: operation:<name>`).
`transition:merge`, `transition:review`, `transition:complete` and `Blocks now:
task:<id>` are unspellable on a human item, and no human action justifies `2_blocked`.
Everything else is `non-blocking-`, filed and merged with the question still open.

The invariant underneath, which is what generalises: **a queue item may bind only a
boundary all four of whose review outcomes are satisfiable by a commit an agent can make
at any time after filing; no boundary's closure may require text inside a commit the
human did not write.** `approved_review_merge_receipt_problem` violated it and is retired
rather than weakened. Applying the same rule is why `1_in-progress → 0_backlog` became a
legal edge: reject and changes-requested both need the task unstarted, so without that
edge two of the four outcomes of the one surviving gate were unreachable.

The restriction is scoped to `needs-human/`. An agent discharges its own obligation at
any time and agent deletions route through changed evidence, never through a merge
receipt, so an agent boundary cannot strand; eleven live `future-blocking` agent requests
keep working unchanged.

`4_done` becomes an agent-work test: real `verification.md` output and no live
`blocking-*`/`future-blocking-*` `needs-agent/` action. A live human question stays listed
and outlives the task. Done means the agent owes nothing — it never meant the human is
satisfied, and it never could, because `4_done` is an agent's `git mv`.

Every `needs-human/` item carries `**Answer by:**` (UTC). A lapse obliges an agent to
re-surface the item and set a new date with a `**Re-asked:**` line. `stale-queue` is in
`ADVISORY_CHECKS`, so a lapse never blocks a commit or a merge.

## Alternatives considered

- Rename the three timing prefixes to carry the new semantics — the designer's own
  concession plus a measurement killed it: renaming one live item touches up to eight
  link-checked files including recorded `verification.md` output, and the vocabulary
  rename multiplies that across every live item, to buy semantics the reconciler now
  teaches at the moment of violation.
- Add a fourth `deferred-` timing class — `non-blocking-` plus a stated unattended
  outcome already is that class, and has been since 2026-07-23.
- Make `transition:merge` unspellable for `needs-agent/` too — over-broad; an agent
  boundary cannot strand, and eleven live items use it.
- Replace the merge receipt with an ancestry receipt on a `promote:<ref>` boundary — no
  `stable` branch and no adapter exist, so it would be agent attestation labelled as
  assurance.
- Let a lapsed `Answer by` *become* the decision by falling through to the unattended
  outcome — not mechanically legal (deletion needs a concrete response, and an agent
  writing into the human's answer slot violates *never edit text the human wrote* and
  *never fabricate*), and the wrong policy: the owner's model is "I will answer, later",
  not "decide for me if I am slow".

## Consequences

Between a merge and the owner's answer, `main` may carry a change he would have rejected,
and anything merged on top of it unwinds with it. That is the direct price of answering
late, and there is no version of it that is free. It is bounded by the declared `async`
merge gate, by `git revert -m 1`, and — the real cap — by the surviving start gate, which
still stops any *task* depending on the unanswered judgment from beginning.

An agent that genuinely cannot proceed without an answer, on a question that is not a
one-way door, must decide provisionally and record it. The honest technique when the
guess is expensive: stop the task at its current commit, merge what exists, and file the
remainder as a `0_backlog` task with a `transition:start` review — which converts an
unanswerable mid-task question into an answerable pre-task one. That is discipline, not
mechanism.

A `4_done` task is pruned at ~90 days while its question may still be live. Three
mechanisms hold: a `non-blocking-` item contributes no `task:` token so pruning cannot
orphan it; `Filed:` provenance makes exactly one task its owner, so an item that must be
visible from several tasks is several items; and `Full context` must bind a durable
non-task artifact.

`Answer by` is advisory, so a determined backlog can still rot — visibly, with a date, in
every reply and every handover. That is strictly better than the state it replaces, where
two questions sat unanswered for eight days with no mechanism that would ever have
noticed.

Revisit if a merged-but-unanswered change is built on and the unwind is worse than the
start gate predicted, or if the owner asks for a "do not build on this yet" marker for
*files* rather than for tasks.
