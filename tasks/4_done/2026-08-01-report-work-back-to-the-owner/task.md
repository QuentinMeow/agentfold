# Make "publish it and report it" the required end of every task

**Claimed-by:** claude (session 2026-08-01-2317PDT)
**Filed:** 2026-08-01, by claude, from the owner's chat request to stop having to ask what was done
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-human/decisions/non-blocking-re-ask-the-older-questions-in-plainer-words.md`

## Goal

Finishing the work is not finishing the job. Today an agent can move a task to
`3_in-review`, write a handover, and stop — leaving the change unpublished and the owner
with no idea what was decided or what they now owe. The end-of-session ritual in the root
`AGENTS.md` says to write files; it never says to publish the branch or to tell the human
what happened in a form they can act on.

This task closes that gap. Publishing the branch as a pull request becomes part of
finishing a task, and the final chat reply gets a stated shape that the chat-reply
scenario in skills/explain-to-human/ owns: the outcome, the decisions and their reasons,
and the owner's own open items in priority order, each already carrying its consequence
and its queue link. That last part is a projection of the handover's "Needs your
attention" section, which is a projection of the queue, so this ritual originates nothing.

## Acceptance criteria

- [ ] The root `AGENTS.md` end-of-session ritual requires publishing the task branch and
      reporting in the shape the chat-reply scenario defines.
- [ ] `skills/session-handover/SKILL.md` ends at the same place: publish, then report.
- [ ] `handbook/git-workflow.md` states when a task opens its own pull request and when it
      stacks on another, in terms a reader can apply without asking.
- [x] The live `message-queue/needs-human/` items were examined for rewriting. Nine
      unanswered ones were drafted in the readable shape and the reconciler refused all
      nine: a live question's visible text is its identity and an agent may not reword it.
      The drafts are kept as a session artifact and the choice is filed for the owner.
- [ ] An ADR records the reporting decision in `memory/decisions/`.
- [ ] `roadmap/current-state.md` and `README.md` reflect what now exists.
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [ ] `python3 automation/run_tests.py` passes.

## Links

- `AGENTS.md` — the end-of-session ritual this changes
- `skills/session-handover/SKILL.md` — the walkthrough that must end the same way
- `handbook/collaboration-modes.md` — `async` means never block and never go silent
