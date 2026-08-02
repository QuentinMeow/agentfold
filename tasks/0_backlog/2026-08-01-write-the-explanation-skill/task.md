# Ship a skill that makes an agent explain its work so a non-expert can decide

**Claimed-by:** unclaimed
**Filed:** 2026-08-01, by claude, from the owner's chat request to make messages and PR bodies readable
**Parent:** none
**Repository scope:** core
**Queue actions:** `message-queue/needs-agent/requests/non-blocking-pick-up-write-the-explanation-skill.md`

## Goal

Every human-facing surface in this repository — queue items, handovers, PR bodies, the
final chat reply — is written by an agent that already knows everything and for a reader
who knows nothing. Today each surface has its own scattered rules (`handbook/decision-guide.md`
for decisions, `handbook/human-action-guide.md` for queue items, `history/AGENTS.md` for
handovers, `handbook/git-workflow.md` for PR bodies), and none of them states the shared
craft: lead with one sentence, then a paragraph of context, then the depth; say what the
behaviour was before and what it is after; gloss every uncommon word in parentheses at
first use; make the file answerable without opening another file.

Ship one canonical skill that states that craft once, and route it to the four surfaces
that need it. The skill is agent-agnostic prose so Claude Code, Cursor, or Codex can
follow it, and it must not restate rules that `templates/` or the handbook already own —
it links them and adds only the explanation layer.

## Acceptance criteria

- [ ] The skill entry point skills/explain-to-human/SKILL.md exists, is at most 70 lines (the reconciler's
      `SKILL_BUDGET`), and routes to one reference per surface.
- [ ] The skill states the three-layer rule (one sentence → one paragraph → full depth)
      and the self-containment rule (a decision file carries the effect; evidence is linked).
- [ ] One scenario reference exists per surface: pull request, human queue message,
      chat reply, and handover.
- [ ] Every rule in the skill is mechanically checkable by a reader — no rule reads
      "be clear" without saying what to do instead.
- [ ] `skills/AGENTS.md` lists the skill in its shipped-skills table.
- [ ] The root `AGENTS.md` points at the skill from the message-queue ritual and the
      end-of-session ritual, without restating its content.
- [ ] `python3 automation/reconcile/reconcile.py --check` reports 0 blocking findings.
- [ ] `python3 automation/run_tests.py` passes.

## Links

- `handbook/principles/progressive-disclosure.md` — short core, linked depth
- `handbook/human-action-guide.md` — what a human action must contain
- `handbook/decision-guide.md` — decision-specific content rules
- `skills/AGENTS.md` — skill layout and portability contract
