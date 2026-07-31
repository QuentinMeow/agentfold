# Give claimed agent queue items and generated retries a legal way out

**Claimed-by:** unclaimed
**Filed:** 2026-07-30, by claude, from an audit of the queue lifecycle checks in `automation/reconcile/reconcile.py`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-unblock-queue-lifecycle-deadlocks.md`

## Goal

Two reproduced defects in `automation/reconcile/reconcile.py` can make the repository
permanently unmergeable with no legal escape, and they compound each other.

**The claim-before-evidence deadlock.** `claim_identity` counts `Resolution evidence`
among the fields frozen by a committed `open` -> `in-repair` claim. An agent who claims a
`needs-agent` item first and works out its resolution evidence second has no exit: deleting
with the field added fails as `action identity or response changed after it was claimed`,
deleting with the field absent fails as `missing non-queue **Resolution evidence:** file
path`, and resetting `Status` to `open` to re-claim fails as `committed in-repair lifecycle
claim regressed to open`. For an ordinary agent request item it is worse:
`immutable_action_text` does not treat `Resolution evidence` as agent-mutable, so even
adding the field while the item is live fails as `action identity changed while the queue
item remained live`, and such an item is undeletable from the moment it is filed. A
`blocking-*` item stuck this way stops every merge.

**Generated retries that outlive their finding.** Two check names escape retry garbage
collection: `queue-resolution` is excluded on purpose, and `stale-task` is excluded by
accident because it is emitted but never registered in the `CHECKS` map, so
`check not in CHECKS` holds. Retries are filed as `blocking-*` with
`**Blocks now:** transition:merge` and carry no `Resolution evidence`, so a `stale-task`
retry survives forever after its finding is fixed and then reports
`unresolved blocking action reached transition:merge` under the exact arguments PR CI
uses. It carries no `task:` token, so `active_task_scope_matches` returns `True`
unconditionally and it blocks every pull request, not only the originating task. Its only
manual exit runs straight into the claim-before-evidence deadlock above.

Nothing runs `--file-retries` today — the pre-commit hook and CI both run `--check` only —
so the fix must also leave that command safe to wire up, including preserving an agent's
rejection text when a deleted retry is refiled while its finding is still live.

## Acceptance criteria

- [ ] A `needs-agent` item claimed `open` -> `in-repair` and then given its
      `**Resolution evidence:**` can be resolved and deleted with no `queue-resolution`
      finding, and the same holds for a reconciler-generated retry
- [ ] An ordinary agent request item can have `**Resolution evidence:**`
      established while it is live, without an `action identity changed while the queue
      item remained live` finding
- [ ] A claim receipt still cannot be transferred to a different action: changing
      `**Action:**` after a claim is still rejected, and a newly added identical item
      still cannot borrow another item's receipt. The existing receipt-transferability
      tests keep passing unchanged
- [ ] `stale-task` is a key in `CHECKS`, so its generated retry is garbage-collected when
      the finding clears and its deletion can be certified; the reconciler reports each
      `stale-task` finding exactly once
- [ ] No check id the reconciler emits is missing from `CHECKS`, enforced by a test that
      fails if a new emitted id is left unregistered
- [ ] `retry_text` emits a `**Resolution evidence:**` line and `refresh_retry_text` adds
      it to an already-filed retry without overwriting an agent's concrete value
- [ ] `--file-retries` preserves an agent's `## Agent notes` and `**Status:**` when a
      deleted retry is refiled while its finding is still live
- [ ] Regression tests exist for each defect, at least one of which fails without the fix;
      `python3 automation/run_tests.py` passes and
      `python3 automation/reconcile/reconcile.py --check` reports 0 findings, both with
      real output in `verification.md`
- [ ] `design.md` carries a complete `## Core fit` receipt, because
      `automation/reconcile/` is a core path

## Links

- Owning contract for the queue lifecycle: `message-queue/AGENTS.md`
- Owning contract for the reconciler and its check registry: `automation/AGENTS.md`
- Guardrail this repairs — nothing blocks or waits silently: `AGENTS.md`
- Retry identity rule the garbage collector depends on:
  `memory/lessons/automation/deterministic-finding-keys.md`
