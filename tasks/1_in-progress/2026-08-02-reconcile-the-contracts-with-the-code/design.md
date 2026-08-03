# Design notes — Correct the contract text that no longer matches the code or itself

**Status:** decided

## Problem

Fourteen audited contradictions between contract text and the code that enforces it. Eleven
are direct repairs with one true answer. Three are not: finding 1 changes a near-immutable
principle and is the owner's, finding 3 is a real two-way choice, and finding 13 is a
judgment about whether a factual correction inside a principle is a principle change.

Every finding was re-verified against `main` at `4e1ffe2` before it was touched. The audit
was taken at `1871d5f` and `main` had moved twelve commits; nothing had been fixed under it,
and nothing in it turned out to be wrong, but two quoted counts had gone stale and are
restated below rather than repeated.

## Finding 3 — how `pair` mode and human-gating v1 are reconciled

### Option A — Rewrite the `pair` documentation to the spellings gating v1 permits

`handbook/collaboration-modes.md` stops describing `pair` as "Merge gate: the human" and
"blocking item before every meaningful step", and says instead that the waiting is the
mode's behaviour while the queue grammar stays mode-blind. `README.md` follows.

*Consequence:* one table cell, one mode note, and one README row change; the reconciler and
the gating ADR are untouched, and a `pair` adopter reads a description that its own
pre-commit hook will accept.

### Option B — Scope `HUMAN_UNSPELLABLE_TRANSITIONS` by collaboration mode

`automation/reconcile/reconcile.py` reads `**Collaboration mode:**` and applies the
restriction only outside `pair`. `message-queue/AGENTS.md` says so. This is `core` code, not
text, so it also needs tests and its own substitution receipt.

*Consequence:* a `pair` repository may file `Blocks at: transition:merge` on a human review
again, and the deadlock that forced gating v1 becomes reachable again in that mode.

## Chosen — Option A

Three reasons, in order of weight.

**The deadlock is not a property of `async`.** The ADR
`memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md` states the invariant
underneath its own rule: *a queue item may bind only a boundary all four of whose review
outcomes are satisfiable by a commit an agent can make at any time after filing.* A human
review bound to `transition:merge` fails that test identically in `pair` mode — once the
merge happens before the answer, its cleanup needs a merge receipt that can never be
produced, so the item can be neither resolved nor deleted. Option B would re-admit a known
unsatisfiable boundary in one mode and call it a feature. The ADR retired
`approved_review_merge_receipt_problem` *rather than weakening it*, for exactly this reason.

**Mode is a mutable line in one file; live items are not.** `**Collaboration mode:**` can be
edited in a single commit, and a task may override it for that task alone. If the grammar
depended on it, flipping the line would retroactively make live items legal or illegal —
against `message-queue/AGENTS.md`'s rule that live timing may only escalate and freezes on a
concrete human response. There is no repair for an item that becomes illegal, because its
visible text is its identity and a committed human response is immutable.

**`pair` loses nothing it actually had.** In `pair` the human is present and is the one who
merges. That is a behavioural gate, and it does not need a queue item to express it — a
queue item records what an *agent* is waiting on, and an agent that does not merge is not
waiting on a filed boundary. What the old text promised was a *mechanical* gate, which the
repository has never had in any mode: `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`
records that no status check is required to merge at all.

**Strongest case against this.** Option A leaves `pair` with no mechanism that stops an agent
merging — only a sentence telling it not to, which is precisely what
`handbook/principles/systems-over-instructions.md` says is worthless. A reviewer who thinks
`pair` mode should be enforceable rather than described should reject Option A. My answer is
that Option B would not have supplied that enforcement either: the boundary it re-legalises
is agent-attested and blocks nothing at the provider, so it would buy a spelling, not a gate.

The ADR needs no edit. Its Decision is already mode-blind and the `pair` row now agrees with
it. The sentence in its Context that places the human "in the `pair` column" describes the
state on 2026-08-01, which is what it was; records are immutable and it stays as written.

## Finding 13 — the hard-coded root budget in a near-immutable principle

`handbook/principles/progressive-disclosure.md` says the root `AGENTS.md` "fits in ~130
lines". The reconciler owns that value at `ROOT_AGENTS_BUDGET = 140`, and the root contract
is 136 lines today, so an agent reading the principle would trim a contract that is inside
budget.

### Option A — Correct the clause directly
Replace the number with "within the reconciler's line budget". No rule in the file changes;
one stale copy of someone else's value disappears.
*Consequence:* the drift is gone today, and `handbook/principles/` has been edited by an
agent that judged its own edit cosmetic.

### Option B — File a decision item and leave the principle unedited
*Consequence:* the wrong number stays until the owner answers, and he is asked a second
question of the same shape as one already waiting since 2026-07-31.

## Chosen — Option B

Filed as `message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md`.

Two contracts, written independently, both say to ask. `handbook/AGENTS.md`: "`principles/`
files are **near-immutable**: changing one requires a human-approved decision … and a
superseding ADR." `handbook/collaboration-modes.md` lists "Changing a file in
`handbook/principles/`" as a one-way door, which in `async` mode must be filed rather than
decided alone. Neither carves out an exception for small or factual changes, and "this edit
is too small to count" is the exact reasoning a bright line exists to refuse.

The precedent is also direct and recent. `message-queue/needs-human/decisions/non-blocking-correct-or-keep-the-auto-filed-retry-loop-in-a-principle.md`
is a live question about a sentence in `handbook/principles/eventual-consistency.md` that is
*simply false* — a stronger case for direct repair than a stale number — and the agent that
found it filed rather than edited, saying so in the item. Repairing mine directly would
overturn that judgment silently, in a commit the owner reads after the fact.

Re-verifying this finding turned up a second instance the audit did not list:
`handbook/principles/design-for-forgetting.md` gives memory entries a `Review-by` date
"(default 90 days…)", while `memory/AGENTS.md` names `templates/memory/` as "the only home
of that number" and those templates set 90 days for facts and known issues but 180 for ADRs
and lessons. Same class, left unedited for the same reason; the filed item carries both,
which is why it asks about the class rather than only the one clause.

**Strongest case against this.** The owner now has two open questions about principle text,
neither of which changes a rule, and the older one has gone unanswered for two days; a
reviewer may reasonably read this as an agent hiding behind procedure while the tree stays
wrong. If the answer to either item is "just fix these", the standing instruction should be
recorded once so no third item is ever filed — which is why Option C of the filed item offers
exactly that general permission.

## The other findings

| # | Outcome | Note |
|---|---|---|
| 1 | routed | `message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md`; principle unedited |
| 2 | repaired | `templates/README.md` human timing column now shows only `operation:<name>` and `transition:start task:<id>` |
| 4 | repaired | link-check exemptions listed by source *and* by target in `handbook/naming-conventions.md`; `README.md` shortened to a pointer |
| 5 | repaired | `roadmap/current-state.md` no longer says the merge-gate decision is pending, and no longer cites the deleted file |
| 6 | repaired | the timing-escalation restatement is gone; the filename grammar stayed and now links `message-queue/AGENTS.md` |
| 7 | repaired | diagram is `0_backlog ↔ 1_in-progress ↔ 3_in-review → 4_done`, matching `TASK_ALLOWED_STATUS_TRANSITIONS` exactly |
| 8 | repaired | the `open` → `in-repair` claim now names its subject: only a task a live `blocking-` item names owes one |
| 9 | repaired | rewritten around `git tag -l 'archive/*'`; the six tags are no longer enumerated, and the scope is no longer only Core admission |
| 10 | repaired | the backlog task now cites the ADR that answered the decision it called open |
| 11 | repaired | the root `AGENTS.md` clause defers to `memory/AGENTS.md` instead of contradicting it |
| 12 | repaired | the retries `README.md` says filing and collection happen only under `--file-retries` |
| 14 | repaired | see below |

Two deliberate non-changes inside repaired findings:

- **Finding 9 keeps its filename.** `archived-refs-outside-core.md` now covers more than
  Core admission, so the slug is imperfect. Renaming it would break the backticked path in
  this task's own `task.md`, which is the audit record and should not be rewritten to suit a
  later rename. The title and description carry the corrected scope.
- **Finding 14 was not empty.** The untracked skills/github-auth-guard directory (unquoted
  deliberately — it is not a repository path) held five .pyc files under two __pycache__
  directories: Python 3.7 bytecode for check, codex_hook, test_check, test_codex_hook, and
  test_install_codex, and no source file, no SKILL.md. All seven
  sources exist on the annotated tag `archive/2026-07-22-prevent-false-github-reauth`, so
  nothing was lost. The directory is gitignored, so removing it is a local cleanup and not a
  commit. Removing it left three dangling adapter symlinks under the gitignored `.claude/`,
  `.cursor/`, and `.agents/` skill directories; those were removed too.

## Findings 15–22, added mid-task from a cold-boot trial

A separate agent cloned the repository fresh, followed `AGENTS.md` with no other context,
and completed a task; the coordinator added what tripped it. All eight were re-verified
here before repair, and one of the coordinator's supporting numbers is wrong.

**15 — the boot sequence never says to run the installer. Repaired, and the worst of the
eight.** `AGENTS.md` asserted "(the pre-commit hook runs it)" while nothing reachable from
`AGENTS.md` told a stranger to create that hook. Demonstrated in a scratch clone: a commit
that adds a broken backticked link to `roadmap/current-state.md` — which `--check` reports
as one blocking finding — was accepted with no hook output at all, because `core.hooksPath`
is unset and `.git/hooks/` holds only samples. `python3 automation/install.py` is now boot
step 1, which is what makes the guardrail's parenthetical true rather than aspirational.

**16 — `CONTRIBUTING.md` unrouted. Repaired, narrowly.** The repo map lists folders, not
files, so its absence there is consistent; what was missing is that the opening paragraph
introduces `README.md` as the human surface and leaves its companion unmentioned. One
clause now names both and says neither carries agent instructions. `CONTRIBUTING.md` does
restate rules that live in `handbook/git-workflow.md`, `tasks/AGENTS.md`, and
`templates/`, which is a single-source finding of its own; it is out of scope here and is
not repaired.

**17 — the ritual's "open only what is relevant" at boot. Repaired; the count is wrong.**
The coordinator reported 36 of 40 `needs-agent/requests/` items as task pickups. On this
branch it is 25 of 41 by `**Request kind:** task-pickup`, and 24 by filename prefix — a
clear majority, not almost all. The repair says "most", which is what the evidence
supports.

**18 — three files disagree about the claim commit. Repaired; the code is the arbiter.**
`check_task_structure` requires `plan.md` and `worklog.md` the moment a task sits in
`1_in-progress`, so the claim commit must create both. This session hit it live: the first
claim attempt reported `missing plan.md` and `missing worklog.md`. `tasks/AGENTS.md` and
both places in `handbook/git-workflow.md` now say so. The live pickup requests that also
state a "Done when" are left alone: an open agent item's action text is its identity.

**19 — the two-lane table never placed the other task files. Repaired.** The lane sentence
now splits one task folder explicitly, which also documents why a plan is born on `main`
and edited on a branch: the reconciler forces the first copy into the claim commit. That is
a file lifecycle, not the two-branches-one-file collision the conflict section forbids.

**20 — `handbook/git-workflow.md` is too long. Repaired by a narrow split.** Only the
GitHub issue/comment/formal-review/diff-thread bullet moved, verbatim, to
`handbook/github-projection.md`; the file went from 172 to 139 lines. The `What to review`
boundary rules stayed, because `templates/README.md` points at `git-workflow.md` for
exactly those and moving them would have broken a live pointer. Nothing cited the moved
bullet by file, and the new file is routed from the repo map, `handbook/AGENTS.md`, and the
`skills/ask-me-anything/` table.

**21 — "repo-relative" means two things. Repaired, including in the code.** A `Full context`
value containing `..` is dropped by `context_path_candidates` and the item is then reported
as having no source, so the two conventions are not interchangeable in the direction that
matters. The phrase is now "root-relative" in the four queue templates and in both
reconciler messages, whose `fix:` line says a `../` path is dropped rather than resolved;
`templates/handover.md` names its own links file-relative; and
`handbook/naming-conventions.md` defines both and says which surface takes which. One test
fixture matched the old placeholder wording and was updated with it.

**22 — ticking acceptance criteria in done tasks. Repaired at the schema, not by a rule in
a contract.** 25 of 48 done tasks have ticked boxes and 23 do not. `templates/task/task.md`
owns this file's schema, so the rule lives there: tick as met, all ticked by `3_in-review`
or `verification.md` names the dropped one, and no check reads them. Stating it in
`tasks/AGENTS.md` instead would have cost a line in a file at 60 of its 60-line budget, to
duplicate a schema.

## Core fit

**Agent substitution:** pass — every tracked change is repository Markdown that any agent
runtime reads through `AGENTS.md`; nothing names a runtime, CLI, model, or vendor.
**Provider substitution:** not-applicable — no adapter, workflow, or provider-bound code is
touched; the only provider-adjacent edit removes a citation of a deleted local file.
**Repository substitution:** pass — an adopted repository copies these contracts verbatim,
and each corrected sentence is one an adopter's agent would otherwise obey into a commit its
own pre-commit hook refuses.
**User-global writes:** none
**Why AgentFold core:** these are the repository's own contracts, templates, and generated
memory index — the files every agent boots from, in every adopting repository. The one
non-tracked action, deleting a gitignored bytecode directory, changes no repository state.
**Thin adapter:** none
