# Verification

Every block below is a command actually run on 2026-08-21 and its real output.

## The reconciler accepts the change, and adds exactly one advisory finding

```
$ python3 automation/reconcile/reconcile.py --check | tail -1
reconcile: 0 blocking finding(s), 15 advisory (not blocking)
exit=0
```

Before this change the same command reported `14 advisory`. The one added finding
names a directory, not an item, and its fix names a new file rather than an edit.

## The test suite passes

```
$ python3 automation/run_tests.py | tail -2
tests: 15/15 files passed
test elapsed: 19.07s
```

## The line budget holds

```
$ wc -l skills/explain-to-human/SKILL.md skills/explain-to-human/scenarios/queue-item.md
      70 skills/explain-to-human/SKILL.md
     129 skills/explain-to-human/scenarios/queue-item.md
     199 total
```

`SKILL_BUDGET` is 70 and `check_agents_budget` enforces it. `scenarios/` is not
budgeted by any check; 129 is held as policy.

## A wrong anchor in a queue item is silently accepted without this change

```
$ python3 - <<'PY'
import sys; sys.path.insert(0, "automation")
from reconcile import reconcile as R
cand = "../../../docs/designs/risk-tiered-agent-guardrails.md#no-such-heading"
print("skipped by check_links:", cand.startswith(R.LINK_SKIP_PREFIXES))
PY
skipped by check_links: True
```

This is why the new check resolves anchors itself. Removing `"../"` from
`LINK_SKIP_PREFIXES` is not the cheaper repair: 816 `../` destinations exist
repository-wide and none carries a fragment, so nearly all of them sit in
immutable history naming paths that have legitimately moved.

## 2026-08-31 — verified replacement publication

The useful implementation and original commit history are retained and repaired in [PR91](https://github.com/QuentinMeow/agentfold/pull/91), stacked above PR90. The conflicting original PR89 is closed. Recovery child `2026-08-30-repair-human-question-evidence` owns the current checks; [its verification](../2026-08-30-repair-human-question-evidence/verification.md) records the actual output and review limits. Existing questions and human-authored responses are unchanged. Neither replacement is merged to main.
