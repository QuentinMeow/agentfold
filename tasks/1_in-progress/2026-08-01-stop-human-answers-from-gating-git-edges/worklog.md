# Worklog — Stop a human answer from holding any Git edge

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-01 — human-gating-model (claude)

- Claimed the task and reproduced the deadlock on `main` @ `0e63bbe`: plain
  `--check` is clean, `--check --at-transition merge` reports four boundary
  findings.
- Confirmed the live inventory differs from the design's: the first-class-queue
  review was folded before this task started, and PR #56 added a new merge-bound
  human re-review, so four human items migrate rather than the design's four
  originals.
- Found one instruction in the design that current `main` cannot execute: the
  dangling `Depends on:` on the revised-assurance review is not a lifecycle-mutable
  field, so editing it on a live item changes action identity and is refused.
  Recorded as a known issue instead of forced.
- Three things the design did not predict, each found by running the code rather
  than reading it. Removing a human item's boundary removes one of its two
  ownership proofs, and the survivor — `Filed:` provenance — was matched by a
  regex requiring the literal word "from" before "task", so an item reading "from
  the owner's review of task `x`" could prove nothing and could never be reworded
  to (`8e908b1`). The weakening also falsifies the item's own unattended-outcome
  sentence, so the migration edge had to be allowed to correct exactly that field
  and nothing else (`540361d`). And rehearsing the full fold in a clone showed a
  `non-blocking-` human review deleting with nothing outside the queue changing —
  the contract had always required changed evidence, but only the boundary-bearing
  branches enforced it, and this model makes `non-blocking-` the ordinary timing
  for a human review (`0747f54`).
- Deliberately did not force `--at-transition merge` to zero. The one survivor is
  an agent request, its boundary is legitimate under the model, and clearing it
  would mean either extending the restriction to `needs-agent/` — which the design
  rejects, and which would break eleven live items — or finishing someone else's
  in-flight task. Recorded in `verification.md` §3 and §8 instead.
- The lifecycle demonstration ran in a throwaway clone, never here: it needs an
  owner's answer to exist, and inventing one in the repository would leave
  fabricated human text in it permanently. Both stranded reviews are still
  `**Your review:** ______` on this branch.
