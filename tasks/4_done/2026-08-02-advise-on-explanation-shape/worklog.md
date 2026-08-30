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

## 2026-08-02 (continued) — the repair an independent review found (claude)

This entry continues the session above, which ended when the machine it ran on crashed. The
work below was in the worktree uncommitted at that point, with its `design.md` and
`verification.md` sections already written; it is committed here with this entry and no
change to what it found.

- **The agent-side carve-out was a hole, not a carve-out.** A review probe filed a
  brand-new `needs-agent` request dated today, omitted `## What you need to know`, and
  copied one line — `**Why-you-might-care:**` — from the single live legacy request. The
  rule reported nothing. The legacy request is precisely the file an agent copies as a
  model, and for an agent request nothing else has ever read its sections, because
  `check_queue_schema` scopes every section rule behind `if actor != "needs-human"`.
- The carve-out now needs the legacy field **and** a `Filed` date before
  `EXPLANATION_SHAPE_ACTIVATION`. Two alternatives lost, both recorded in `design.md`:
  keying on the creation commit is the more principled signal but returns nothing in a
  plain `--check`, which is the pre-commit path where this check does most of its work, so
  the rule would have gone silently inert exactly where it matters; and dropping the
  carve-out entirely would report the one genuine legacy request forever, against a file
  whose only repair is rewriting a record. The 43/11 governed split is unchanged by the
  narrowing — the one grandfathered agent request is filed 2026-07-24 and still qualifies.
- **The workflow probes for the flag instead of passing it unconditionally.** A
  `pull_request_target` run resolves workflow code and checked-out gate code separately,
  and a pull request's `base.sha` demonstrably lags the base branch tip. A workflow that
  hard-codes `--pull-request-body-shape` can therefore meet a gate that predates it, and
  argparse answers with `error: unrecognized arguments` and **exit 2** — the status this
  repository reserves for a check that could not run at all. An advisory readability line
  would have been failing pull requests with nothing wrong with them, which is the outcome
  the decision behind this task forbids.
- **One test pin was one-directional and is now bidirectional.** The optional-section pin
  only asserted `Notes` was in the tuple, so a probe could add a second deletable section
  to the schema and watch every test stay green while the gate began demanding it of a
  conforming body. It now derives the deletable set from the schema and asserts set
  equality.
- Recorded three shapes the rules deliberately do not see under `design.md` → *Known
  limits*, so nobody re-discovers them as bugs: a `##` heading nested in a `<details>` fold
  counts as present, a duplicated `## TL;DR` is deduplicated rather than reported, and a
  bulleted `## TL;DR` counts as zero items. The last now says so in the finding text.
- Six tests added across `test_reconcile_queue.py`, `test_pull_request_schema.py`, and
  `test_github_action_projection_workflow.py`. `python3 automation/run_tests.py` green,
  12/12 files; `reconcile.py --check` 0 blocking.
- The task stays in `1_in-progress` for the owner to move; pull request #66 is updated in
  place rather than reopened.

## 2026-08-09 — close-tasks-whose-work-already-merged (claude)

- The work merged to `main` in pull request #66 on 2026-08-03; only the folder never moved,
  so its status has misreported reality since. Moved to `4_done` to match.
- Verified before moving: `verification.md` holds real command output,
  `automation/check_action_projection.py` and the advisory rules are present on `main`, and
  no live blocking agent action names this task.
