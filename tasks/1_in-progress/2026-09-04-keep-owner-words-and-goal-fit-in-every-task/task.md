# Keep the owner's words and a goal fit in every task

**Claimed-by:** claude
**Filed:** 2026-09-04, by claude, from chat — the owner's request is quoted verbatim in `requirements.md` beside this file
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

Make every task record carry the owner's own words, mark which requirements the owner
stated and which an agent added, keep one full picture of the repository's desired end
goals with provenance, and require a stated fit between goal, current state, and request
before a behaviour-changing task starts. The reconciler (the script that checks repository
invariants before a commit) enforces the shape so that an agent cannot lose the goal
halfway through to requirements it generated itself.

## Acceptance criteria

- [ ] [user 2026-09-04] WHEN a task is filed, ITS FOLDER SHALL hold the owner's words for it verbatim and dated in `requirements.md`, appended never edited, or state plainly that there are none; the reconciler refuses a new task without that file.
- [ ] [user 2026-09-04] WHEN an acceptance criterion is written, IT SHALL open with `[user <date>]` (tracing to a dated owner entry) or `[derived]` (agent-added, with its reason); the reconciler refuses a new task whose criteria carry no label.
- [ ] [user 2026-09-04] THE REPOSITORY SHALL keep one full picture of its desired end goals in `roadmap/desired-state.md`, each goal recording who asked, when, the owner's words, and whether the owner confirmed it; the multi-agent workflow requested on 2026-08-31 and this feature are recorded there from the owner's words.
- [ ] [user 2026-09-04] WHEN a `core` or `service:` task is claimed, ITS `task.md` SHALL state the goal it serves, the current-state fact it changes, and how the request fits; a `conflicts` or `unclear` fit lists a needs-human clarification or decision in `Queue actions` and is never worked around; the reconciler refuses the claim otherwise.
- [ ] [derived] Records are judged by the schema they were written under: done tasks are exempt, live pre-activation tasks receive advisory findings only, and backlog tasks adopt the new files at their own claim commit — because the written-grammar decision forbids obligations a record's author could not have met.
- [ ] [derived] Every new check is observed green on an undamaged fixture, red on a damaged one for its own reason, and present in the runner's output; `PYTHONDONTWRITEBYTECODE=1 python3 automation/run_tests.py --jobs 1` and `python3 automation/reconcile/reconcile.py --check` pass with real output in `verification.md` — because the root guardrails forbid fabricated results.
- [ ] [derived] `design.md` carries the completed core-fit receipt from `templates/task/design.md` — because this task changes core.

## Fit

**Serves:** G10 — Every task keeps the owner's words, labels what the agent added, and states its fit to a confirmed goal
**Today:** a task records where it was filed from, never the owner's words; acceptance criteria carry no provenance; `roadmap/desired-state.md` holds eight lines with no provenance, last updated 2026-07-24, and no line for the owner's 2026-08-31 multi-agent request; nothing checks that a task traces to a goal.
**Fit:** aligned — G10 is transcribed from the owner's 2026-09-04 words by this task, and G9 from the 2026-08-31 words, so the two live workflow tasks trace to a confirmed goal.

## Links

- Full picture: `roadmap/desired-state.md` (G9, G10 once this task lands)
- Schema owners: `templates/task/task.md` today; the task-requirements and roadmap-goal templates this task adds under `templates/`
- Precedent for a verbatim owner file inside a task: task `2026-08-30-rebuild-the-open-pr-stack`
