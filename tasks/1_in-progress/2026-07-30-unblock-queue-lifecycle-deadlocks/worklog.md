# Worklog — give claimed agent queue items and generated retries a legal way out

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-07-30 — unblock-queue-lifecycle-deadlocks (claude)

- Claimed the task on branch task/2026-07-30-unblock-queue-lifecycle-deadlocks in an
  isolated worktree.
- Reproduced both defects before changing anything, then turned each reproduction into a
  regression test so the "before" state stays re-runnable; the real output is in
  `verification.md`.
- The sub-case the audit marked suspected does hold, and it is worse than the claimed
  case: `immutable_action_text` rejects even *adding* `**Resolution evidence:**` to a live
  agent request, so one filed without the field is undeletable from birth. That decided
  the shape of the fix — dropping the field from `claim_identity` alone would have left
  the ordinary-request half of the deadlock in place.
- Chose to treat `Resolution evidence` as owned by whoever must act: mutable for
  `needs-agent`, frozen for `needs-human` exactly as before. Non-transferability of a
  claim receipt is unaffected because what *defines* an action stays immutable; there is
  now a test proving a post-claim `Action` or `Full context` edit is still rejected.
- Two deliberate departures from the audit's suggested fixes, both recorded in
  `design.md`. Garbage collection was *not* widened to every check name: a
  `queue-resolution` retry can never certify its own deletion, so collecting it would
  replace a stale retry with an uncertified deletion. And `stale-task` was registered
  rather than renamed, because check ids are load-bearing in retry filenames
  (`memory/lessons/automation/deterministic-finding-keys.md`) and two backlog task records
  already name it.
- Registering a second id on one function meant the runner had to deduplicate by function
  identity, or every `task-structure` finding would have been reported twice. The durable
  guard is `test_every_emitted_check_id_is_registered`, which scans the reconciler source
  for emitted ids and fails if one is missing from `CHECKS` — that is the check that would
  have caught this defect the day it was introduced.
- Dead end worth not repeating: "establish the field once, then freeze it" cannot be
  expressed in `immutable_action_text`. It compares one text at a time, so an
  absent-to-present transition is indistinguishable from a retarget without seeing both
  sides; encoding direction there is impossible, and the comparator that does see both
  sides belongs to another region.
- Left `--file-retries` unwired, as it was. It is now safe to wire up — collection no
  longer strands retries, refiling preserves a rejection, and every filed retry has a
  legal exit — but the timing semantics of a generated retry (`blocking-*` at
  `transition:merge`, with no `task:` token, so repo-wide) are a design question that
  outlives this defect and is not changed here.
