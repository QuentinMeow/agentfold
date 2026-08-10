# Correct the contract text that no longer matches the code or itself

**Claimed-by:** claude (session 2026-08-02, branch task/2026-08-02-reconcile-the-contracts-with-the-code)
**Filed:** 2026-08-02, by claude, from a contract-drift audit of every AGENTS.md, handbook file, template, and roadmap line
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/decisions/non-blocking-choose-the-gate-for-externally-changed-instruction-files.md`; `message-queue/needs-human/decisions/non-blocking-stop-a-principle-from-copying-the-line-budget.md`

## Goal

The contracts are this repository's API, and an audit on 2026-08-02 confirmed fourteen
places where they no longer describe what the code does, or contradict each other. The
reconciler reports `0 blocking finding(s)` through every one of them, because none of these
is a shape a check can see.

Three are severe enough that an agent obeying the written contract produces a commit the
pre-commit hook refuses. The rest mislead a reader without stopping them.

Every finding below was verified at revision `1871d5f` with both sides quoted. Re-verify
each one before you change it — quoting is not the same as still being true, and other
agents are landing work on `main` while you read this.

## The findings, grouped by the repair they need

### A. The human-gating story, told three incompatible ways (the severe group)

Gating v1 says a human answer never holds a Git edge: `transition:merge|review|complete`
and `Blocks now: task:<id>` are unspellable on a `needs-human/` item
(`message-queue/AGENTS.md`, enforced at `HUMAN_UNSPELLABLE_TRANSITIONS` in
`automation/reconcile/reconcile.py`). Three places still describe the world before that.

1. **`handbook/principles/provenance-over-position.md`** requires that external changes to
   instruction-bearing files get human review "before an agent treats them as instructions
   **or they merge**", via a canonical timing-prefixed queue item. There is no legal
   spelling for that item: `needs-human/` rejects the merge binding, and routing it to
   `needs-agent/` would make a human ask that does not live in `needs-human/`.
   **This one is not yours to fix by editing.** `handbook/AGENTS.md` makes `principles/`
   near-immutable — changing one needs a human-approved decision and a superseding ADR. File
   a `needs-human/decisions/` item from `templates/queue/decision.md`, written to
   `skills/explain-to-human/scenarios/queue-item.md`, asking whether the instruction-file
   review becomes a `transition:start` gate on the task that adopts the external change —
   the surviving spelling — or something else. List it in this task's `Queue actions`. Do
   not edit the principle, and do not block this task on the answer.
2. **`templates/README.md`** publishes a timing-field table whose `needs-human/` column
   still offers the rejected tokens, while all three human-facing templates in
   `templates/queue/` carry the correct restriction. `templates/README.md` claims ownership
   of that grammar and two other templates route agents to it, so the wrong copy is the
   authoritative one.
3. **`handbook/collaboration-modes.md`** describes `pair` mode as "Merge gate: the human"
   and "blocking item before every meaningful step", and `README.md` mirrors it. Neither is
   spellable. Note the asymmetry that proves it is drift rather than intent: the `async`
   cell in the same table *was* updated for gating v1 and the `pair` cell was not.
   Reconciling this is a real choice — rewrite the `pair` column to the spellings gating v1
   permits, or scope the restriction by mode in the reconciler and say so in
   `message-queue/AGENTS.md`. Record which you chose and why in `design.md`. The existing
   ADR `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md` reasons from the
   old premise and imposes a mode-blind rule; whichever way this goes, the `pair` row and
   that ADR must end up agreeing.

### B. Statements that are simply false now (direct repairs)

4. **`handbook/naming-conventions.md` and `README.md`** describe the link check's exemptions
   as a list of source directories. The largest exemption is target-based: every citation of
   any `message-queue/` path, from anywhere, is unchecked. Two smaller undocumented skips
   compound it — `../`-relative links, and candidates with no known extension whose
   top-level entry is untracked. Document what the check actually exempts, and shorten the
   `README.md` copy to a pointer.
5. **`roadmap/current-state.md`** says every merge gate stays advisory "until the owner
   answers" a decision file — then says sixteen lines later that the owner decided it on
   2026-08-02. The named file was deleted when that answer was folded. One fact, two live
   statements, one of them a dead path.
6. **`handbook/naming-conventions.md`** restates the queue timing-escalation rule that
   `roadmap/current-state.md` claims now lives only in `message-queue/AGENTS.md`. Keep the
   filename grammar there; link for the rest, the way `templates/README.md` and
   `handbook/human-action-guide.md` already do.
7. **`tasks/AGENTS.md`**'s lifecycle diagram omits two transitions the reconciler allows in
   `TASK_ALLOWED_STATUS_TRANSITIONS`: `1_in-progress → 0_backlog` and
   `3_in-review → 1_in-progress`. The first is required by the gating model — the reconciler
   tells an agent to take it — and an agent reading only the diagram believes it is illegal.
8. **`tasks/AGENTS.md`** states unconditionally that `1_in-progress` is valid only after a
   committed `open` → `in-repair` agent claim. The code applies that only to a task named by
   a live `blocking-` agent item. Fourteen tasks currently sit in `1_in-progress` with no
   such claim and the tree is green, so the literal reading is provably false. Make the
   subject explicit.
9. **`memory/facts/archived-refs-outside-core.md`** enumerates one of the six `archive/*`
   tags that exist, and its scope has silently broadened: only the first is a core-admission
   refusal, and the other five preserve unmerged or orphaned work. Facts are freely editable
   current truth (`memory/AGENTS.md`), so rewrite it — and prefer the `git tag -l` command it
   already gives over an enumeration that goes stale again.
10. **The task `2026-08-01-stop-the-merge-ref-recompute-from-failing-a-stack`** (find it with
    `ls tasks/*/<id>`; its status folder may move under you) cites a decision in its
    `task.md` as still open and still recommending. It was answered and deleted; the
    outcome is in `memory/decisions/2026-08-02-the-merge-gate-stays-advisory-while-the-repository-is-immature.md`.
    An unclaimed backlog task is read cold, so its false premise is the whole context its
    next reader gets.
11. **The root `AGENTS.md`** says a decided ADR is "never rewritten" and a reversal only
    links it, while `memory/AGENTS.md` requires the old ADR to gain `Superseded-by:` or
    `Amended-by:`. Five ADRs on `main` carry those fields. Under
    `handbook/principles/folder-as-a-service.md` a conflict is a bug in the child, so an
    agent applying precedence literally refuses to write the back-link. The root clause is
    the one that is wrong.
12. **`message-queue/needs-agent/retries/README.md`** claims reconciler-filed items are
    garbage-collected automatically; collection happens only under an explicit
    `--file-retries`, which neither the pre-commit hook nor CI passes. (The same over-claim
    in `handbook/principles/eventual-consistency.md` is already filed as a decision and is
    **not** yours — leave the principle alone.)
13. **`handbook/principles/progressive-disclosure.md`** states the root `AGENTS.md` budget
    as a number, a third copy of a value the reconciler owns, and it is already wrong. Say
    "within the reconciler's line budget". This is a one-clause factual correction inside a
    near-immutable file — if you judge that it still needs the decision route, say so in
    `design.md` and file it rather than editing.
14. **An empty untracked skills directory named github-auth-guard** survives from refused
    work — it is untracked, so do not write its path as a link. It holds
    no tracked files, so Git cannot see it and `skills/AGENTS.md` does not list it. Confirm
    it is genuinely empty of content before removing it, and say what you found.

### C. Added mid-task, from a cold-boot trial (findings 15-22)

An agent cloned the repository fresh, followed `AGENTS.md` with no other context, and
completed a task. What tripped it is the same class, so the coordinator added it here.

15. **The boot sequence never says to run the installer**, and then the guardrail asserts
    the hook exists. A fresh clone has `core.hooksPath` unset and only sample hooks, so no
    gate runs at all. Every file that documents the installer is unreachable from this
    contract.
16. **`CONTRIBUTING.md` is in neither the repo map nor the router.** Route it or say why it
    is human-only.
17. **The message-queue ritual says "open only what is relevant"** at boot, before a task is
    chosen, when most agent requests are task pickups that are not yet relevant.
18. **Three files disagree about what the claim commit contains** — `tasks/AGENTS.md`,
    the pickup requests' own "Done when", and `handbook/git-workflow.md`'s milestone list.
19. **The two-lane table never says where `plan.md`, `worklog.md`, and `verification.md`
    live**, so a task's plan can be born on `main` and then edited on a branch by guess.
20. **`handbook/git-workflow.md` is 172 lines** and a stranger needs about 34 of them; one
    bullet is a GitHub provider-adapter spec inside the file you open to learn how to commit.
21. **Two templates use "repo-relative" to mean opposite things** — from the repository root
    in `templates/queue/`, from the file's own folder in `templates/handover.md`.
22. **Done tasks disagree about ticking acceptance criteria** and no rule says which is right.

## Acceptance criteria

- [ ] Each of findings 2 and 4–14 is either repaired or explicitly declined in `design.md`
      with the reason. Nothing is silently dropped.
- [ ] Finding 1 has a filed `needs-human/decisions/` item listed in this task's
      `Queue actions`, and the principle itself is unedited.
- [ ] Finding 3 is resolved in one direction, with the choice and its argument in
      `design.md`, and the `pair` row, `README.md`, `message-queue/AGENTS.md`, and the
      gating ADR all agree afterwards.
- [ ] WHEN an agent reads `templates/README.md`'s timing table and files a `needs-human`
      item exactly as described, THE RECONCILER SHALL accept it. Demonstrate this with a
      real item written from the corrected table, run against `--check`.
- [ ] Every quoted "both sides" pair in this task is re-verified before its repair, and any
      finding that turns out to be already fixed or wrong is reported as such rather than
      repaired.
- [ ] `python3 automation/reconcile/reconcile.py --check` passes, and every leaf `AGENTS.md`
      stays inside its line budget after the edits — several of these repairs add words to
      files that are already near the limit.
- [ ] `python3 automation/run_tests.py` passes, real output in `verification.md`.
- [ ] `design.md` carries the completed core-fit receipt from `templates/task/design.md`.
- [ ] Each of findings 15-22 is repaired or refuted in `design.md`, and finding 15 is
      demonstrated: a scratch clone shows a commit the reconciler refuses landing with no
      hook, and the boot sequence's first step then makes the guardrail's parenthetical true.

## Links

- Enforcement of the gating rule: `HUMAN_UNSPELLABLE_TRANSITIONS` in `automation/reconcile/reconcile.py`
- The ADR whose premise finding 3 contradicts: `memory/decisions/2026-08-01-human-answers-never-gate-a-git-edge.md`
- Near-immutability of principles: `handbook/AGENTS.md`
- Precedence when a leaf contract conflicts: `handbook/principles/folder-as-a-service.md`
