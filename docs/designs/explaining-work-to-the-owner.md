# Explaining work to the owner

**Status:** implemented as `skills/explain-to-human/`
**Author:** claude, session 2026-08-01-2317PDT

This document says why the explanation skill is shaped the way it is: what problem it
solves, what was considered instead, and what evidence each rule rests on. The skill itself
is the operating document; this is the reasoning behind it.

## The problem

In this repository an agent does effectively all the work and the human acts as a manager:
they read what the agent produced, approve or redirect it, and answer the questions only
they can answer. That division only functions if the agent's reports are good enough to
decide from. Today they are not, and the failure is consistent enough to name.

The owner's own account of it: *"Every time I have to ask what do I need to do, and I have
to ask what's this and what's that."* Three specific failures sit behind that sentence.

**Mechanism instead of effect.** An agent that has just read a file writes "`resolve_queue`
now calls `freeze`". The reader cannot see either function, does not know what they take or
return, and must guess what changed. A guess about a system you cannot see is worse than no
information, because it feels like information.

**No layering.** Reports arrive as one undifferentiated block, so the decision is wherever
the agent happened to write it. Readers of a screen of text read roughly a quarter of the
words, so a decision below the fold is a decision nobody made.

**No self-containment.** A decision file links four other files and expects the reader to
assemble the question. The owner does not need the root-cause investigation to decide; they
need the effect. Asking them to trace evidence to make a judgment is asking them to redo
the agent's work.

The rules that would fix this were scattered across four documents that each owned one
surface — `handbook/decision-guide.md` for decisions, `handbook/human-action-guide.md` for
queue items generally, `history/AGENTS.md` for handovers, `handbook/git-workflow.md` for
pull requests — and none of them stated the craft that all four need.

## The shape chosen

One skill, `skills/explain-to-human/`, with a short router and one file per surface.

```
skills/explain-to-human/
├── SKILL.md          the rules that hold everywhere, plus a routing table
├── reference.md      the craft in depth, and what each rule prevents
└── scenarios/
    ├── pull-request.md
    ├── chat-reply.md
    ├── queue-item.md
    └── handover.md
```

**Why one skill rather than four.** The craft is the same on every surface; only the
skeleton differs. Four skills would restate the craft four times, and the repository's
single-source-of-truth guardrail forbids exactly that. A router plus leaves keeps one
statement of the craft and one place to change it.

**Why a skill rather than more handbook prose.** The handbook is read at boot, by
everything, forever. This material is only needed at the moment an agent is about to write
something a human reads — that is a task-conditioned pointer, which is what
`handbook/principles/progressive-disclosure.md` says a skill is for. It also means the
material is portable: another repository that adopts AgentFold gets it by copying one
folder.

**Why the scenario files do not restate schemas.** `templates/queue/` owns the fields of a
decision file, `templates/handover.md` owns the handover, and `history/AGENTS.md` owns which
queue items a handover projects. The scenario files own the *prose* that fills those slots
and link the schema rather than repeating it. This keeps the skill correct when a schema
changes.

**Why one level of routing.** A skill file that links a file that links a third file gets
read partially — agents preview rather than read at the second hop. Every route from
`SKILL.md` reaches its destination in one step.

## The three layers

The core rule is that every human-facing artifact is written in three layers, in this
order, and never inverted:

| Layer | Answers | Length | Example location |
|---|---|---|---|
| 1 | Do I need to do anything? | one sentence | PR title, first line of a reply, `Action` field |
| 2 | What is different, and why? | one paragraph, at most four moving parts | the summary block |
| 3 | How exactly, and how do you know? | as long as needed | folded section, linked file |

Layer 2 has a fixed internal order — what was true before, what changed, what is true now,
why that was the right response — because that order is what makes a change judgeable
rather than merely described.

The rule that an agent's execution order is not the reader's priority order is the
counterpart. Agents narrate chronologically by default, because that is the order their
context is in. It is almost never the order the reader needs.

## Evidence

Each rule in the skill comes from a field that solved this problem under pressure. The
short version, with what each contributed:

| Rule | Where it comes from |
|---|---|
| Conclusion first | US Army writing regulation (bottom line up front); the Minto pyramid principle |
| Layered disclosure; readers read ~25% of words | Nielsen Norman Group's progressive-disclosure and reading-behaviour work |
| Narrative over bullet fragments; appendix is not required reading | Amazon's written-memo culture |
| A status report is *explanation*, a distinct genre from tutorial and reference | the Diátaxis documentation framework |
| Concrete language as the antidote to assuming shared knowledge | the curse-of-knowledge result (Camerer, Loewenstein, Weber) |
| One worked example, and when a second stops helping | worked-example effect and expertise-reversal effect in cognitive load theory |
| Sentence and paragraph thresholds, active voice, freeing trapped verbs | Google and Microsoft style guides; plainlanguage.gov; GOV.UK |
| Severity first, contingencies, dead ends, read-back | SBAR and I-PASS clinical handover protocols |
| Calibrated uncertainty: likelihood and confidence stated separately | IPCC uncertainty guidance; Kent's words of estimative probability |
| Two-way versus one-way doors | already this repository's own framing in `handbook/collaboration-modes.md` |

Two findings changed the design rather than merely supporting it:

- **Written handovers survive; verbal ones do not.** In clinical studies, verbal-only
  handover loses effectively all information within three cycles, while a written sheet
  loses almost none. This is the empirical case for the repository's existing rule that
  chat is a projection and files are canonical — the skill therefore never lets the chat
  reply carry state of its own.
- **A decision request that omits any one of seven properties comes back as a question.**
  Named decider, closed question, two to four options, a stated recommendation, assumptions
  separated from facts, the default if nobody answers, and reversibility with its cost. The
  repository's queue templates already carry six of these; the skill's contribution is
  naming the failure each one prevents, so an agent can tell when a slot is filled badly
  rather than merely filled.

## Alternatives considered

**Enforce it mechanically instead.** The reconciler could count sentence length, flag
undefined acronyms, or require a before/after line per change. Rejected for now: the
checkable proxies are weak — a body can pass every mechanical rule and still be
unreadable — and a bad check trains agents to satisfy the check. The one place mechanical
enforcement already exists and works is the pull-request action section, because there the
invariant is structural (one entry, one queue link) rather than semantic. If a specific
readability rule turns out to have a structural proxy, that becomes its own task.

**Put the rules in the root `AGENTS.md`.** Rejected: it is budgeted at 140 lines and read
in full by every agent on every boot. Material needed at one moment in a session is exactly
what progressive disclosure says belongs behind a task-conditioned pointer.

**Write one exemplar and tell agents to imitate it.** Examples do outperform abstract rules
for style, which is why every scenario file carries worked examples. But an exemplar alone
cannot say *why* a choice was made, so an agent facing a case the exemplar does not cover
has nothing to reason from. The skill carries both.

## What this does not do

- It does not change any schema. Every field, status, and lifecycle rule stays where it is.
- It does not decide when a human is asked — that is `handbook/collaboration-modes.md` and
  `message-queue/AGENTS.md`.
- It does not make the reconciler check prose quality. Nothing here is machine-enforced
  except what was already enforced.

The one provider-specific file is
`skills/explain-to-human/scenarios/pull-request.md`; every other scenario file is
provider-neutral.

## Core fit

**Agent substitution:** the skill is plain markdown with no tool-specific syntax; any agent
that can read a file can follow it.
**Provider substitution:** only the pull-request scenario file names a provider, and it names
GitHub's rendering behaviour as the mechanics of one surface. The section order and the
craft are provider-neutral; a different provider needs a different mechanics section, not a
different skill.
**Repository substitution:** every repository whose agents report to a human needs this;
nothing in it is specific to AgentFold's domain.
**User-global writes:** none.
