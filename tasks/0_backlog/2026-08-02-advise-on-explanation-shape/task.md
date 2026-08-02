# Report the structurally visible readability rules as advisory findings

**Claimed-by:** unclaimed
**Filed:** 2026-08-02, by claude, from the owner's answer folded in `memory/decisions/2026-08-02-readability-enforcement-disposition.md`
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-advise-on-explanation-shape.md`

## Goal

`skills/explain-to-human/` states how every human-facing message is written, and almost
none of it is checked. The owner chose to surface the machine-visible part of that standard
as **advisory** findings: they print, they are counted, and they never fail a commit
(`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).

Build that. Three rule families have a shape a program can see:

1. **Sections present and in order** — a queue item's headings and their order
   (`templates/queue/`), and a pull-request body's sections and their order
   (`templates/pull-request.md`).
2. **Every choice carries an example consequence** — each `### Option …` in a decision or
   clarification item ends with an `*Example consequence:*` line.
3. **Summary length in range** — a pull-request `## TL;DR` carries three to six numbered
   items.

Queue items are repository files, so the reconciler sees them. A pull-request body is a
provider artifact the reconciler never reads, so the second and third families live at the
boundary gate that already parses a body (`automation/check_action_projection.py`). Deciding
that split, and whether the boundary gate's advisory output is reported the same way the
reconciler's is, is this task's design work — record it in `design.md` before implementing.

Nothing semantic is in scope. Whether an explanation is clear, or whether a counter-case is
real rather than hedged, stays a reviewer's job; the decision says so explicitly.

## Acceptance criteria

- [ ] WHEN a queue item under `message-queue/` is missing a required heading, or carries its
      headings out of template order, THE RECONCILER SHALL emit one finding naming the file
      and the heading, and that finding SHALL print with the `(advisory)` marker.
- [ ] WHEN a decision or clarification item has an `### Option …` heading whose section has
      no `*Example consequence:*` line, THE RECONCILER SHALL emit one advisory finding
      naming the file and the option.
- [ ] WHEN every queue item is well formed, THE RECONCILER SHALL emit no finding from this
      check — verified by running it against the tree as it stands, which must stay at
      `0 blocking finding(s)` and must not gain advisory noise on already-correct files.
- [ ] `python3 automation/reconcile/reconcile.py --check` SHALL exit 0 on a tree whose only
      violation is one of these rules, and `--fail-on-advisory` SHALL exit non-zero on that
      same tree.
- [ ] WHEN a pull-request body is missing a required section, carries its sections out of
      order, or has a `## TL;DR` outside three to six items, THE BOUNDARY GATE SHALL report
      it as advisory and SHALL NOT change its own exit status because of it.
- [ ] Every new check id is a key in `CHECKS` and a member of `ADVISORY_CHECKS`, and
      `automation/AGENTS.md` no longer describes the advisory tier as age-driven only.
- [ ] New tests in `automation/tests/` cover: a violation of each rule family, a correct
      file emitting nothing, and the exit-code contract above. `python3 automation/run_tests.py`
      passes, with its real output recorded in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.

## Links

- Decision: `memory/decisions/2026-08-02-readability-enforcement-disposition.md`
- Standard being checked: `skills/explain-to-human/SKILL.md` and its `scenarios/`
- Schemas that define the shapes: `templates/queue/`, `templates/pull-request.md`
- Design background: `docs/designs/explaining-work-to-the-owner.md`
