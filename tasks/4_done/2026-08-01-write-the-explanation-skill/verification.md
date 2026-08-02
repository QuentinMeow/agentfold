# Verification — write the explanation skill

## Repository invariants

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

## Full test suite

```
$ python3 automation/run_tests.py
...
PASS automation/tests/test_mine_cochange.py
PASS automation/tests/test_reconcile_queue.py
PASS automation/tests/test_resolve_github_external_sources.py
PASS automation/tests/test_run_tests.py
PASS services/quote-api/tests/test_quote_api.py
PASS services/quote-cli/tests/test_quote_cli.py
tests: 11/11 files passed
test elapsed: 34.25s
```

## Line budgets

`SKILL.md` files are budgeted at 70 lines and leaf `AGENTS.md` files at 60
(`automation/reconcile/reconcile.py`, `SKILL_BUDGET` and `LEAF_AGENTS_BUDGET`). The root
`AGENTS.md` is budgeted at 140.

```
$ wc -l skills/explain-to-human/SKILL.md skills/explain-to-human/reference.md \
        skills/explain-to-human/scenarios/*.md skills/AGENTS.md AGENTS.md
      70 skills/explain-to-human/SKILL.md
     324 skills/explain-to-human/reference.md
     141 skills/explain-to-human/scenarios/chat-reply.md
      92 skills/explain-to-human/scenarios/handover.md
     190 skills/explain-to-human/scenarios/pull-request.md
     117 skills/explain-to-human/scenarios/queue-item.md
      39 skills/AGENTS.md
     128 AGENTS.md
```

Every budgeted file is inside its budget; the unbudgeted reference and scenario files carry
the depth, which is the point of the split.

## Acceptance criteria

- [x] The skill entry point exists, is 70 lines, and routes to one reference per surface.
- [x] The skill states the three-layer rule and the self-containment rule
      (`SKILL.md`, "The three layers" and the last bullet of "Rules that hold on every
      surface"; expanded in `skills/explain-to-human/reference.md`).
- [x] One scenario reference exists per surface — pull request, human queue message, chat
      reply, and handover.
- [x] Every rule is stated as an action rather than an adjective. Checked by reading each
      rule and asking what a reader would do differently; the two that failed that test in
      draft ("be concrete", "keep it short") were replaced by the effect/mechanism test and
      the explicit sentence and paragraph thresholds.
- [x] `skills/AGENTS.md` lists the skill and now permits the `scenarios/` layout it uses.
- [x] The root `AGENTS.md` points at the skill from the message-queue ritual and the
      end-of-session ritual without restating it.
- [x] Reconciler reports 0 blocking findings.
- [x] Test suite passes 11/11.

## Live-use test

The skill's own pull-request scenario was used to write this branch's pull-request body,
and an independent agent was given the skill and this diff and asked to produce a body
without any other instruction. Both results are recorded in `worklog.md`.
