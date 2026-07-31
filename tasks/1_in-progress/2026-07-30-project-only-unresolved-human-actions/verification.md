# Verification — project only the human actions that still await the human

**Verified:** 2026-07-30 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## Reconciler

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## Full repository test suite

```
$ python3 automation/run_tests.py
test lane: full
test reason: full suite requested
selected test files:
  automation/tests/test_check_action_projection.py
  automation/tests/test_check_core_scope.py
  automation/tests/test_collect_github_review_actions.py
  automation/tests/test_github_action_projection_workflow.py
  automation/tests/test_inspect_workspace_boundaries.py
  automation/tests/test_mine_cochange.py
  automation/tests/test_reconcile_queue.py
  automation/tests/test_resolve_github_external_sources.py
  automation/tests/test_run_tests.py
  services/quote-api/tests/test_quote_api.py
  services/quote-cli/tests/test_quote_cli.py
test workers: 8
test shards: 49
...
PASS automation/tests/test_check_action_projection.py
PASS automation/tests/test_check_core_scope.py
PASS automation/tests/test_collect_github_review_actions.py
PASS automation/tests/test_github_action_projection_workflow.py
PASS automation/tests/test_inspect_workspace_boundaries.py
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 121.84s
```

## Reconciler queue tests, unsharded

```
$ python3 -m unittest automation.tests.test_reconcile_queue
Ran 311 tests in 201.428s

OK
```

The nine tests this task added, by name:

```
$ python3 -m unittest automation.tests.test_reconcile_queue -v 2>&1 \
    | grep -E "^test_(v3|v2|entry_schema|unresolved)"
test_entry_schema_upgrade_to_v3_is_not_a_v2_downgrade (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_entry_schema_v3_is_sticky_after_activation (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_unresolved_human_state_predicate_fails_open (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_v2_handover_keeps_projecting_every_live_human_action (automation.tests.test_reconcile_queue.ReconcileQueueTests)
test_v3_handover_accepts_none_when_every_action_is_resolved (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_v3_handover_projects_only_unresolved_human_actions (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_v3_handover_rejects_a_projected_resolved_human_action (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_v3_handover_still_requires_every_unresolved_human_action (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
test_v3_still_projects_an_unreadable_or_unknown_human_state (automation.tests.test_reconcile_queue.ReconcileQueueTests) ... ok
```

(`test_v2_handover_keeps_projecting_every_live_human_action` prints its `ok` on the
following line because its subtests emit their own line first; the run above is `OK`
with no failures.)

## Effect on the repository's own queue

`tmp/live_split.py` loads the reconciler as a module and partitions the live
`needs-human` queue with the new predicate. Its source is at the end of this file.

```
$ python3 tmp/live_split.py
path-only live needs-human items (old rule): 8
unresolved (new rule, still projected): 7
  KEEP  message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md  [waiting/no-response]
  KEEP  message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md  [waiting/no-response]
resolved (new rule, dropped): 1
  DROP  message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md  [folding/Your review]
```

## End to end against the real queue

A throwaway conversation record was staged with the exact eight-bullet
`Needs your attention` block that every recent handover has carried, checked, trimmed to
seven, checked again, and then deleted unstaged and untracked. It was never committed.

Eight bullets — the block as handovers have been writing it:

```
$ git add history/conversations/2026-07-30-2300PDT-verify-unresolved-projection
$ python3 automation/reconcile/reconcile.py --check
[handover-queue-projection] history/conversations/2026-07-30-2300PDT-verify-unresolved-projection/handover.md: Needs your attention entry 1 links `message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md`, which was not live at handover creation
    fix: use one top-level list entry per live human action; put an exact Action-labeled queue link first and keep context declarative
[handover-queue-projection] history/conversations/2026-07-30-2300PDT-verify-unresolved-projection/handover.md: new handover is not an exact projection of the live human queue: not live message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md
    fix: list every live needs-human item once; omit resolved or invented asks
reconcile: 2 finding(s)
```

The same record with the resolved review's bullet removed:

```
$ git add history/conversations/2026-07-30-2300PDT-verify-unresolved-projection
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 finding(s)
```

## No retroactive redness across `history/`

`tmp/sweep_history.py` re-runs `check_handover_queue_projection()` at the creation commit
of every handover reachable from `--all`, which is what the reconciler's own history
recheck does per commit. It was run once against the pre-change module and once against
the post-change module, and both runs wrote their complete per-event finding sets to JSON
for comparison. Source at the end of this file.

Before (module as of `6cd2de9`, the branch point):

```
$ python3 tmp/sweep_history.py tmp/before.json
handover creation events: 67
  ...10/67 (1s)
  ...20/67 (57s)
  ...30/67 (156s)
  ...40/67 (342s)
  ...50/67 (687s)
  RED history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md @ 4d26cf30
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 1 `message-queue/needs-human/reviews/future-blocking-review-guardrail-authority-boundary.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 2 `message-queue/needs-human/reviews/future-blocking-review-layered-development-workspace.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 3 `message-queue/needs-human/reviews/future-blocking-review-revised-assurance-profile-scope-and-egress.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 4 `message-queue/needs-human/reviews/future-blocking-review-sensitive-data-recovery.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 5 `message-queue/needs-human/reviews/future-blocking-review-test-runner-git-environment-isolation.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|Needs your attention entry 6 `message-queue/needs-human/reviews/non-blocking-review-template-first-explanation.md` must contain exactly one **Why-you-might-care:**
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|new handover is not an exact projection of the live human queue: missing message-queue/needs-human/reviews/future-blocking-rereview-human-action-files.md, message-queue/needs-human/reviews/future-blocking-review-detector-failure-state.md, message-queue/needs-human/reviews/future-blocking-review-first-class-message-queue.md
      handover-queue-projection|history/conversations/2026-07-26-1158PDT-human-action-ux/handover.md|new handover human entries are not in canonical timing-and-filename order
  ...60/67 (1429s)
total findings across 67 creation events: 8
wrote tmp/before.json
```

Those eight are pre-existing and unrelated: commit `4d26cf3` lives only on the unmerged
branch task/2026-07-23-first-class-message-queue, so the reconciler running at `main`
never reaches it. This sweep is deliberately wider than the reconciler's own recheck.

After (this branch):

TO_BE_FILLED_AFTER

## Scripts used above

`tmp/` is git-ignored scratch, so both scripts are reproduced here verbatim.

`tmp/live_split.py`:

```python
"""Scratch: split the repository's live needs-human queue by the new liveness rule."""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "reconcile", pathlib.Path("automation/reconcile/reconcile.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

R.start_git_snapshot_cache()
try:
    paths = sorted(R.live_human_queue_paths())
    print(f"path-only live needs-human items (old rule): {len(paths)}")
    unresolved, resolved = [], []
    for path in paths:
        text = (R.REPO / path).read_text(encoding="utf-8")
        fields = R.text_fields(text)
        state = "{}/{}".format(
            fields.get("Status", "<absent>").strip(),
            R.first_concrete_response(R.human_response_fields(text)) or "no-response",
        )
        (unresolved if R.human_action_unresolved(text) else resolved).append(
            (path, state))
    print(f"unresolved (new rule, still projected): {len(unresolved)}")
    for path, state in unresolved:
        print(f"  KEEP  {path}  [{state}]")
    print(f"resolved (new rule, dropped): {len(resolved)}")
    for path, state in resolved:
        print(f"  DROP  {path}  [{state}]")
finally:
    R.stop_git_snapshot_cache()
```

`tmp/sweep_history.py`:

```python
"""Scratch sweep: re-run the handover projection check at every handover's creation commit.

This mirrors the reconciler's own history recheck loop (the
``_HANDOVER_HISTORY_RECHECK_ACTIVE`` block in ``check_handover_queue_projection``),
which evaluates each committed handover against the queue snapshot of the commit that
created it. Running it before and after a rule change proves whether the change
retroactively reddens any already-committed record.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path(".").resolve()
spec = importlib.util.spec_from_file_location(
    "reconcile", REPO / "automation/reconcile/reconcile.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def creation_events():
    """Every (handover path, commit that added it) reachable from HEAD."""
    log = subprocess.run(
        ["git", "log", "--all", "--full-history", "--diff-filter=A",
         "--format=%H", "--name-only", "-z", "--", "history/conversations"],
        cwd=REPO, stdout=subprocess.PIPE, text=True, check=True,
    )
    events = []
    commit = None
    for chunk in log.stdout.split("\0"):
        for line in chunk.splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
                commit = line
            elif line.endswith("/handover.md"):
                events.append((line, commit))
    return sorted(set(events))


def main():
    out = pathlib.Path(sys.argv[1])
    events = creation_events()
    print(f"handover creation events: {len(events)}")
    R.start_git_snapshot_cache()
    R._HANDOVER_HISTORY_RECHECK_ACTIVE = True
    results = {}
    start = time.time()
    try:
        for index, (rel, commit) in enumerate(events, 1):
            with R.git_revision_candidate(commit):
                findings = [
                    f"{f.check}|{f.subject}|{f.message}"
                    for f in R.check_handover_queue_projection()
                    if str(f.subject) == rel
                ]
            results[f"{rel}@{commit}"] = findings
            if findings:
                print(f"  RED {rel} @ {commit[:8]}")
                for finding in findings:
                    print(f"      {finding}")
            if index % 10 == 0:
                print(f"  ...{index}/{len(events)} ({time.time()-start:.0f}s)")
    finally:
        R.stop_git_snapshot_cache()
    total = sum(len(v) for v in results.values())
    print(f"total findings across {len(events)} creation events: {total}")
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {out}")


main()
```
