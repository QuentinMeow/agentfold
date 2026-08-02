# Worklog — Report the structurally visible readability rules as advisory findings

Append-only; newest at the bottom. One entry per session that touched this task.

## 2026-08-02 — advise-on-explanation-shape (claude)

- Claimed the task: moved it from `0_backlog` to `1_in-progress`, named the claimant, and
  deleted `message-queue/needs-agent/requests/non-blocking-pick-up-advise-on-explanation-shape.md`
  in the same coordination commit, leaving `Queue actions: none`.
- Work continues on branch `task/2026-08-02-advise-on-explanation-shape`.
- Split the work by what each program can see (`design.md`): the reconciler gets one new
  advisory check id, `explanation-shape`, for queue items; `automation/check_action_projection.py`
  gets an opt-in `--pull-request-body-shape` flag for the body it alone ever holds. The
  flag exists because the same program also checks issue bodies and conversation comments,
  which have no section schema and would have collected pure noise.
- **What running the rule against the tree as it stands found.** Ten of the thirteen live
  `needs-human` items and one of the forty-one live `needs-agent` requests are written in
  the pre-rename field spelling (`Why-you-might-care` / `If-you-do-nothing`) and carry the
  older section names (`## Differences`, `## Options`, `## Example`) instead of today's
  (`## Your choices`, `## What I recommend`, `## For the record`). A first cut of the rule
  reported all eleven. They are not wrong: `check_human_attention` already decides that a
  live item written under the earlier spelling keeps the schema it was written under,
  because a record is immutable and the only repair for such a finding would be rewriting
  one. The rule was narrowed to match that existing judgment rather than the files being
  changed — `current_queue_template_governs` is that gate, extended to the agent side
  where the one legacy request lives. The remaining forty-three live items pass as written.
- The per-choice example-consequence rule is strictly finer than the blocking rule beside
  it. `check_queue_schema` requires two concrete consequences *anywhere* in a human item's
  choices, so an item with three choices and two consequences passes it; the advisory line
  names the third choice. That case is the regression test.
- Two facts about the pull-request schema live in the gate's source rather than being
  derived: `## Notes` is optional, and `## TL;DR` holds three to six items.
  `templates/pull-request.md` states both only inside HTML comments, which
  `templates/README.md` requires every parser to blank. They are pinned against the schema
  by `test_the_two_unreadable_schema_facts_still_say_what_the_gate_assumes`. This is the
  weakest part of the split; `design.md` records the alternative it beat and why.
- Verified end to end and recorded in `verification.md`: clean tree `0 blocking finding(s)`
  with no advisory noise; one deliberate violation exits `0` printing `(advisory)`;
  `--fail-on-advisory` exits `1` on that same tree; the boundary gate reports all three
  body rules and still exits `0`; `python3 automation/run_tests.py` green, 12/12 files.
- Published as [pull request #66](https://github.com/QuentinMeow/agentfold/pull/66), based
  on `main`, with no stack under it. Its body was run through
  `check_action_projection.py --pull-request-body-shape` before the pull request existed
  and came back at `0 finding(s)` and `0 advisory finding(s)` — the first use of the new
  rule was on the change that added it. Two sentences had to be rewritten first: the
  existing action-detector reads line-first, so a wrapped line beginning `repair for such
  a finding …` scanned as a bare imperative. The task is left in `1_in-progress` for the
  owner to move.
