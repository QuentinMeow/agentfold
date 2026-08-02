# Give every pull request one body schema a zero-context reader can act on

**Claimed-by:** claude (session 2026-08-01-2317PDT)
**Filed:** 2026-08-01, by claude, from the owner's chat request to make PR descriptions readable
**Parent:** none
**Repository scope:** core
**Queue actions:** none

## Goal

A pull request is the main place this repository asks its owner to look at something, and
its shape is currently folklore: `handbook/git-workflow.md` mandates only the machine-checked
`What to review` section, and every other section is whatever the authoring agent invented
that day. The owner has to hunt for what changed, what it means, and what they personally
must do.

Fix the shape, not the wording: put one PR body schema in `templates/`, where every other
file schema in this repository already lives, and project it into GitHub's own
pull-request template file so a human opening a PR by hand gets the same skeleton.
The schema must fit the boundary check that already exists — `What to review` stays the
declared action section with one top-level entry per action and exactly one canonical queue
link each — and it must put the reader's own to-do list above the fold, before any detail.

## Acceptance criteria

- [x] The schema file templates/pull-request.md exists and is listed in the `templates/README.md` table.
- [x] The schema orders sections: one-line title, TL;DR (numbered, before → after),
      `What to review` (ranked, each entry naming its consequence if ignored), then folded
      detail, folded change table, folded verification.
- [x] The `What to review` section as specified passes
      `automation/check_action_projection.py` — proven by a test over a filled example,
      not by assertion.
- [x] .github/pull_request_template.md exists, matches the schema, and is registered as
      a thin adapter in `automation/core-scope-paths.txt`.
- [x] `handbook/git-workflow.md` points at the schema instead of describing a body shape.
- [x] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [x] `python3 automation/run_tests.py` passes.

## Links

- `handbook/git-workflow.md` — the merge/review rules the body must satisfy
- `automation/check_action_projection.py` — the boundary check over `What to review`
- `templates/README.md` — every file schema lives in `templates/`
