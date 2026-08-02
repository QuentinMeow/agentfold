# Design notes — standardize pull-request bodies

**Status:** decided

## Problem

A pull request is where this repository asks its owner to look at something, and only one
part of its body had a defined shape: the `What to review` section, because a check reads
it. Everything else was invented per pull request, so the owner had to hunt through prose
of varying quality for what changed and what they personally owed.

The constraint that made this non-obvious is that the body is not a repository file. It is
provider metadata, written once and edited in a web form, so "copy the template and fill
it" needed somewhere to copy *from*.

## Options considered

### Option A — Schema in `templates/`, projected into a GitHub template file
`templates/pull-request.md` is the single source of truth, as it is for every other file
schema here. `.github/pull_request_template.md` is a thin adapter that GitHub uses to
pre-fill a new pull request.
*Example consequence:* an agent copies the schema; a human who opens a pull request in the
browser gets the same skeleton without knowing the schema exists. Changing the shape means
editing two files that a test holds in agreement.

### Option B — Only `.github/pull_request_template.md`
One file, no duplication.
*Example consequence:* the shape becomes GitHub's, so a fork that uses another provider
inherits nothing, and `templates/README.md`'s claim to be the single source of truth for
every schema becomes false.

### Option C — Describe the shape in `handbook/git-workflow.md`
*Example consequence:* the git workflow document, which is already the longest thing in the
handbook, absorbs a schema; and there is still nothing to copy, so agents keep improvising.

## Chosen

Option A. The duplication is real but bounded — two files, held in agreement by
`automation/tests/test_pull_request_schema.py`, which asserts the sections and their order
in both.

Writing the tests changed the schema three times, which is the argument for having written
them:

1. **Folded sections need headings above them.** The first draft opened `<details>` blocks
   with no heading. The boundary check treats a section as running until the next heading
   of the same or higher level, so the whole folded half of the body was parsed as part of
   `What to review` and rejected as "content outside the top-level action list". Each
   folded section now carries its own `##` heading outside the fold.
2. **Alerts cannot live inside a fold.** Verified against GitHub's own rendering: an alert
   marker inside `<details>` renders as the literal text `[!NOTE]`. The schema keeps the
   stack note at the top level, and the test asserts no alert marker appears after the
   first fold in either file.
3. **Ordinary prose can read as an ask.** "A branch that filed its own review can now
   merge" is refused by the boundary check as a directive outside the action section, while
   "A branch is no longer blocked by a review it filed itself" passes. The schema and the
   skill both now say to write the rest of the body in the indicative with a named subject,
   and a test documents the exact pair.

## What this does not change

The boundary check itself is untouched. No rule about what must be projected, or which
actor owns an item, moved. This task changed what an agent writes, not what is enforced.

## Core fit

**Agent substitution:** pass — the schema is markdown with no tool-specific syntax, and the
test drives the existing standalone checker rather than any agent runtime.
**Provider substitution:** pass — `templates/pull-request.md` is provider-neutral;
`.github/pull_request_template.md` is the GitHub projection of it and is registered as a
thin adapter in `automation/core-scope-paths.txt`. A repository on another provider keeps
the schema and writes its own one-file adapter.
**Repository substitution:** pass — every adopted repository that opens pull requests needs
a body shape, and nothing in the schema names AgentFold's domain.
**User-global writes:** none
**Why AgentFold core:** the harness already enforces one section of the body at the
provider boundary and already claims in `templates/README.md` to own every file schema. The
shape of the artifact that carries that enforced section belongs in the same place.
**Thin adapter:** canonical=templates/pull-request.md; optional=yes; policy=none; writes=repo-only
