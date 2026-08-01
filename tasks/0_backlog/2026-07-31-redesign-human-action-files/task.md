# Redesign every file that asks a human for attention

**Claimed-by:** unclaimed
**Filed:** 2026-07-31, by claude, from the live redesign request — `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-redesign-human-action-files.md`

## Goal

The owner rejected the current human-attention format: the English is broken, past and
current and proposed behavior are indistinguishable, choices are ambiguous, and
parser-style labels, excessive metadata, and duplicate links obscure the decision. This
task lands the decided action-first format — an ask-first three-field header, a
`Today` / `What this would change` / `What this does not decide` context block, explicit
choices with per-choice example consequences, an evidence-backed recommendation with its
own counter-case and a graded confidence, and every machine field moved below the answer
line — and enforces it in `automation/reconcile/reconcile.py`.

It also migrates every live unanswered `message-queue/needs-human/` item to that format
without touching the one item that already carries the owner's committed answer, which
stays byte-identical and keeps the schema it was written under.

An earlier attempt is design input, not a merge candidate: it rewrote
`automation/markdown_semantics.py` by 1,849 lines to reason about rendered prose and was
blocked three times by its own adversarial panel. This task enforces structure only and
leaves `automation/markdown_semantics.py` untouched.

## Acceptance criteria

- [ ] `templates/queue/review.md`, `templates/queue/decision.md`, and
      `templates/queue/clarification.md` describe one action-first format with exactly
      three fields above the first heading and all bookkeeping below the answer line
- [ ] `handbook/human-action-guide.md` states the shape of a human-attention file once,
      and `message-queue/needs-human/reviews/README.md` no longer tells a human to copy
      a hash
- [ ] The reconciler gains a `human-attention` check that rejects a fourth header field,
      any machine field above the answer line, a missing or ungraded recommendation, a
      recommendation naming a choice that was never shown, raw HTML, a resurrected
      `Look-at`, more than 700 words above the answer line, and state-dependent prose
      that contradicts `Status`
- [ ] `Why-you-might-care` and `If-you-do-nothing` are renamed to `Why this matters` and
      `If you do nothing`, with a permanent legacy alias and a `Queue action-entry
      schema: v3` handover suffix, so no record created under v1/v2 is retroactively
      invalidated
- [ ] Every live unanswered `needs-human/` item is migrated in one commit, and
      `message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`
      — the only item carrying a committed human response — is byte-identical to the
      baseline afterwards, proved in `verification.md`
- [ ] The migration carve-out fires only on the one-shot activation edge, refuses any
      item carrying a human answer, freezes 17 fields byte-exactly and 2 more by resolved
      path set, and permits only appending to the two projected sentences; adversarial
      mutations against each fence are recorded with their real output
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The request this repairs: `message-queue/needs-agent/requests/future-blocking-redesign-human-action-files.md`
- The promised follow-up judgment: `message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md`
- What a human action must achieve: `handbook/human-action-guide.md`
- The queue contract and its lifecycle: `message-queue/AGENTS.md`
- Why the queue owns pending actions: `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md`
