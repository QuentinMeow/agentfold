# Migrate the eight live asks only after the owner countersigns each rewrite

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from the human-action format redesign — `handbook/human-action-guide.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-countersign-the-live-human-item-migration.md`

## Goal

The human-attention format now governs every new ask, but the eight items already sitting
in `message-queue/needs-human/` were left exactly as they are and will age out as they
resolve. That is deliberate: the redesign first tried to migrate them under a fenced
carve-out in `queue_mutation_problem`, and the carve-out was proven exploitable.

The exploit is the reason this task exists, so record it rather than rediscover it. With
all seventeen byte-frozen fields identical, both path-frozen fields identical, both
projected sentences whitespace-normalised prefixes of their committed values, and
`reconcile.py --check` reporting zero findings, a migration was still able to change the
H1 question, invert `What this does not decide` — erasing a real scope limit the owner had
set — delete one of the offered choices, flip the recommendation from "Request changes"
to "Approve", and raise the stated confidence. The fences guard field labels. The ask a
human actually reads is the title, the context block, the choices, and the
recommendation, and every one of those is outside any such fence by construction. Adding
more frozen fields cannot close it.

So the only safe migration is one the owner countersigns. Publish a queue item that shows
the per-file before and after, get an answer, commit that answer, and only then commit the
rewrite — in that order, so the record of what was approved predates what was done.

Three defects in the live files are worth fixing in the same countersigned pass, because
each is a change to text the owner reads and none of them may be made silently:

- `future-blocking-review-layered-development-workspace.md`,
  `future-blocking-review-revised-assurance-profile-scope-and-egress.md`, and
  `future-blocking-review-test-runner-git-environment-isolation.md` each tell the reader
  not to answer while the item is `awaiting-artifact`, while `**Status:**` on each is
  already `waiting`. The prose tells him to wait for a state he is already past.
- `non-blocking-review-template-first-explanation.md` states its unattended outcome
  twice and differently, once in `**If unanswered:**` and once in `**If-you-do-nothing:**`.
- `message-queue/needs-human/reviews/README.md` still tells a human to copy
  `Review revision` into `Reviewed revision`, and so does that same item's closing
  sentence. The templates no longer ask for it; the live files and their leaf README
  still do. Rewriting the README belongs with the files it describes, not before them.

## Acceptance criteria

- [ ] One `needs-human/` queue item shows, per file, the exact before and after of every
      line a human reads, and asks for one answer covering the whole set
- [ ] That answer is committed while the item's status is `waiting`, in a commit that
      precedes the commit performing any rewrite
- [ ] The migration commit changes no file the answer did not show, proved by a diff in
      `verification.md` against the bytes quoted in the queue item
- [ ] `future-blocking-review-detector-failure-state.md` — the one item carrying a
      committed human response — is byte-identical afterwards, proved by its blob id
- [ ] The three status-contradicting sentences and the duplicated unattended-outcome
      field are gone, and `message-queue/needs-human/reviews/README.md` no longer tells
      anyone to copy a hash
- [ ] `design.md` states how `queue_mutation_problem` admits the rewrite, and why that
      mechanism cannot be replayed or aimed at any file the answer did not cover
- [ ] `design.md` accounts for the one-way property recorded in task
      `2026-08-01-record-that-a-format-migration-is-one-way`
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 findings and
      `python3 automation/run_tests.py` passes every file, with both real outputs in
      `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/reconcile.py` is a core path

## Links

- The format the migrated files would move to: `templates/queue/review.md`
- What a human action must achieve: `handbook/human-action-guide.md`
- The identity rule any migration must satisfy: `automation/reconcile/reconcile.py`
- The queue contract and its lifecycle: `message-queue/AGENTS.md`
- The redesign that deferred this: task `2026-07-31-redesign-human-action-files`
