# Queue resolution without a one-commit window

**Status:** proposal, not an accepted decision
**Explored:** 2026-07-30, by claude, with nine independent agents (three research, four design, three adversarial)
**Supersedes nothing.** The governing decisions remain
`memory/decisions/2026-07-23-queue-resolution-is-git-evidence.md` and its successor chain.

This document keeps the choice space visible. Four materially different approaches were
designed and then attacked. Three failed. The recommendation is the smallest one, and the
reason it is smallest is itself the main finding.

## The invariant, and what breaks it

A queue item is resolved by deleting its file. `resolution_evidence_problem`
(`automation/reconcile/reconcile.py:2722`) gates that deletion: the file named in the item's
`Resolution evidence` field must differ between the deletion commit and its immediate parent.

The window is exactly one commit wide. Work that landed earlier is byte-identical on both
sides of the deletion edge, so it reads as unchanged and the item can never be deleted
honestly. `message-queue/needs-agent/requests/blocking-repair-handover-projection-code-span-copy.md`
has been in that state on `main` since 2026-07-26. Its repair merged in `6d4e337`, before the
deletion could be attempted. The task that would fix it is itself pinned by it.

## Finding 1 — the gate is already empty

Appending `\n# probe\n` to the declared evidence file and staging it clears the finding
completely: `reconcile: 0 finding(s)`. Reproduced independently twice, on disposable clones.

The gate proves *the deletion commit also touched the named file*. It has never proved that
the work happened, and it cannot: the checker lives in the same writable tree as the agents,
the pre-commit hook is one flag away from being skipped, and there is one identity for
everyone. The governing decision already concedes the ceiling — "this proves repository
transitions, not human identity" — and a 2026-07-22 adversarial panel already ruled
self-authored acknowledgement forgeable.

So the honest frame is not *how do we make the proof stronger*. It is *how much friction is
worth paying, given that proof is unavailable*.

## Finding 2 — the strictness is concentrated in the wrong place

Of the 14 live ordinary requests under `message-queue/needs-agent/requests/`, **11 declare
`roadmap/current-state.md`**
as resolution evidence, 2 declare `automation/AGENTS.md`, and 1 declares
`automation/reconcile/reconcile.py`. Every one of those is a file the end-of-session ritual
touches routinely; `roadmap/current-state.md` changed in 23 of 317 commits.

This is chosen at **filing** time, and it is what makes every widening dangerous. Two
independent verification agents each proved, on two different designs, that widening the
window to "the evidence changed at some point since the item was created" makes **14 of 14**
live ordinary requests deletable with no work at all — including five gates whose stated
precondition is a task still sitting unclaimed in `tasks/0_backlog/`.

The deletion-time rule is not where the weakness lives. A generic evidence path declared at
filing time is.

## Finding 3 — every redesign failed in the same place

Four approaches were designed in full and three were then attacked by independent adversarial
reviewers. Deep documents are in this session's `artifacts/` folder under `history/`.

| Approach | Core idea | Verdict |
|---|---|---|
| **A. Lineage baseline** (already implemented on an unmerged branch) | Compare evidence against the item's unique creation snapshot instead of the deletion edge | **Do not ship as-is** |
| **B. Level-triggered predicates** | Items declare a `Done when:` predicate from a closed grammar, evaluated against current state rather than an edge | **Do not ship** |
| **C. Commit-pinned receipts** | The deletion commit names the commit or digest where the work landed | Not attacked; its author conceded "the pin is decorative, the digest is the invariant" |
| **D. Recorded state, not deletion** | Append-only resolution log inside the item; deletion becomes later mechanical compaction | **Do not ship** |

Every failing design failed for the same three reasons:

1. **It kept a gate satisfiable without doing the work.** Measured at 14/14 for both A and B.
2. **It added a new field to items governed by a whole-text identity check, manufacturing a
   fresh way to brick the repository.** Adding `Done when:` to a live item reports "action
   identity changed while the queue item remained live"; so does adding a `## Resolution log`
   section. In both cases the commit that would repair a malformed value is the one commit
   that cannot land — a reproduction of the exact deadlock class being removed.
3. **It paid for the residue with an escape hatch its own author called load-bearing.** One
   design leaned on its hatch in 11 of 17 scenarios.

Three designs, three independent reviewers, one shared failure mode. That convergence is
stronger evidence than any single verdict.

### Approach A, specifically

Approach A is finished and tested on the unmerged branch named for task
2026-07-26-resolve-queue-items-whose-evidence-already-merged. Verification found:

- It is **faster on the hot path**: `queue-resolution` inside `--check` drops from 0.32s to
  0.12s, because a persistent `cat-file --batch` plus a tree cache replaces per-path `ls-tree`
  spawns. That caching is worth keeping regardless of the rule.
- Its claimed range speedup was **confounded**: it compared a 246-commit branch history against
  a 317-commit main. De-confounded, it is **51–60% slower** over full history, and 80% slower
  for `queue-resolution` alone.
- It introduces **an unrepairable finding on immutable history**. Replaying real history
  produces "queue action creation lineage is not unique: found 2 creation roots" for
  `future-blocking-publish-layered-workspace-follow-ups.md`, filed independently on two
  lineages that later merged. History cannot be edited, so the finding cannot be cleared, and
  the shape generalizes to any future item created on two lineages.
- On a shallow clone an honest deletion exits 2 with **zero findings**, silencing every other
  check and filing no retry, while the hook's `set -e` blocks every commit.

The first two are fine. The last two are new hard-failure paths with no escape, which the
repository's own repair constraint forbids.

## Also found, independent of any redesign

- The belief that "the queue check takes 92–312 seconds" is a **misattribution**. That range is
  the runtime of the test file `automation/tests/test_reconcile_queue.py`. The check itself
  costs 0.12–0.34s. Recorded in a handover and repeated since.
- Replaying full history on `main` today already reports **55 findings**, including one
  `queue-resolution` finding that is unfixable by the rules that produced it, and about 20
  task-admission findings whose own text says a later revert cannot erase them.
- `message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md`
  declares `Depends on:` a path that has never existed in any commit on any branch. The
  reconciler reports zero findings, because the queue's own reciprocal fields are stripped
  before link validation.
- Filing a retry for a `queue-resolution` finding manufactures a second undeletable item: the
  generated retry carries no `Resolution evidence` field, and `generated_retry_clear` refuses
  its own check name.
- Three live items name `transition:merge` boundaries whose ranges are already ancestors of
  `main`. Git evidence cannot un-cross a boundary, so three tasks are stranded in `3_in-review`.

## Recommendation

**Do not ship a redesign. Ship the smallest change that unsticks honest work, and stop
pretending the gate carries assurance it does not.**

In order:

1. **Widen the window, and nothing else.** Replace the edge comparison in
   `resolution_evidence_problem` with: the evidence path exists in the candidate, and some
   commit reachable from the candidate has touched it since the item was created. One function.
   No new field, no schema marker, no migration, no waiver, no new frozen text — therefore no
   new brick vector. This is honest about being a lateral move: attacker cost goes from one
   trivial append to zero, while honest cost goes from impossible to free.
2. **Move the remaining strictness to filing time.** Reject a generic or absent evidence path
   *when the item is created*, not when it is deleted. A filing-time rule cannot deadlock,
   because the item is not yet live and the commit that fixes it is always legal. This is the
   one place where strictness is both effective and safe, and no explored design centred it.
3. **Keep Approach A's caching, discard its rule.** The `cat-file --batch` and tree cache are a
   2.7x win on the hot path and are independent of the baseline question.
4. **Repair the stuck items by hand** in the existing retire-and-refile idiom: the blocked
   code-span request, and the three stranded `transition:merge` reviews.
5. **Record what the gate buys.** A new decision file stating plainly that resolution evidence
   is anti-forgetting friction and an audit trail, not proof of work. The repository's own
   principle is that a strict-looking mechanism creating false confidence is worse than a
   lenient one, because it substitutes for review.

### The alternative worth deciding on the record

**Delete `resolution_evidence_problem` entirely** and rely on the claim edge, review, and
history. No design explored this, and it is the only option that reduces surface rather than
adding to it. Given that the gate is cleared by a probe newline, the assurance lost is close
to zero and the complexity removed is real. It should be rejected deliberately if it is
rejected, rather than by default.

## Non-goals

Preventing a determined agent from laundering a completion claim. With a bypassable hook, one
shared identity, and the checker inside the writable tree, prevention is unavailable. The
achievable goals are order-independence, tamper-evidence, and cheap honest paths.

## How reality gets verified

The live stuck item is the acceptance test. Deleting
`blocking-repair-handover-projection-code-span-copy.md`, together with its reciprocal task
link, must pass with no evidence file touched — while an item whose evidence never changed
anywhere in its lineage must still be refused. Both cases exist today and reach opposite
verdicts under the recommendation.
