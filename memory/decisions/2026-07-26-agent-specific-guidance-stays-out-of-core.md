# Agent-runtime-specific guidance stays outside this repository

**Status:** decided
**Date:** 2026-07-26
**Decided-by:** human (owner instruction in chat, transcribed below)
**Description:** AgentFold stays free of agent choice, so runtime-specific instruction sets, hooks, and installers are never checked in — the portable mechanism may be, its runtime adapter may not
**Review-by:** 2027-02-08

## Context

Branch `task/2026-07-22-prevent-false-github-reauth` carried a complete, working guard
against a real defect: inside an agent sandbox `gh auth status` fails for lack of network
or keychain access, and an agent misreads "I cannot see the credential" as "the credential
is invalid," then tells the human to run `gh auth login`. The upstream cause is
`openai/codex#19262`. The branch added a portable classifier plus Codex-specific hooks, a
Codex installer, persistent Codex guidance, and edits to root `AGENTS.md`, `skills/`, and
`automation/`. Three commits, 26 files, all six acceptance criteria met. It was never
merged and no pull request was ever opened for it.

The owner ruled on it in chat: "we should be free of agent choice, so agent specific
instructions shouldn't live in this repo. That branch should never checked in, but worth
keep a copy for migrating to other places."

The rule that excludes it was already written before the branch existed. Root `AGENTS.md`
**Core admission** requires tracked harness mechanisms to be useful across agent runtimes
and forbids "personal setup, user-global state, and single-provider/product workflows" in
core; `automation/AGENTS.md` says "personal installers stay outside AgentFold." The branch
fails that rule on two independently checkable counts:

- `skills/github-auth-guard/scripts/install_codex.py:348` resolves its install root from
  `CODEX_HOME` defaulting to `~/.codex`, so the receipt field `**User-global writes:**
  none` in `templates/task/design.md` cannot be filled honestly.
- Its `design.md` carries no `## Core fit` section at all, which the Git boundary gate
  requires for a core-scope task.

The gate never fired only because the work never crossed a reviewed boundary. That is the
finding worth keeping: the check was correct and the branch would have failed it.

## Decision

Runtime-specific instruction sets, hooks, and installers are not admitted to this
repository, however well built and whatever real defect they fix. The branch is not
merged and is not to be re-proposed.

The boundary falls between mechanism and adapter, not at the whole subject. A
runtime-neutral mechanism remains admissible on its own merits — the classifier
`check.py` is agent-agnostic by the branch's own design note. What is refused is the
Codex hook, the Codex installer, and any guidance that only one runtime reads.

The work is preserved for migration elsewhere as annotated tag
`archive/2026-07-22-prevent-false-github-reauth` at `f4cc1a2`. A tag rather than a branch
because merged-branch cleanup sweeps branches and does not touch tags; this branch was
nearly deleted during exactly such a sweep. The tag message carries the reasoning, the
portable-versus-runtime-only file split, and an explicit instruction not to re-propose the
merge, so a future agent that finds the ref learns its status from the ref itself.

## Alternatives considered

- Merge the branch — rejected: it fails Core admission, and `main` is 192 commits ahead
  across the same core paths, so this was never a clean merge in any case.
- Salvage the portable classifier now — rejected as out of scope for the owner's
  instruction, which was to ignore the branch, not to re-home it. Recorded as available
  rather than done, so a later task may pick it up without re-deriving the analysis.
- Delete the branch outright — rejected: the owner asked for a copy kept for migrating
  elsewhere.
- Keep it as a live branch — rejected: a live branch reads as pending work, and routine
  cleanup deletes branches, which would lose the copy.

## Consequences

Agent adapters in this repository stay thin, policy-free forwarders that write only inside
the repository. Any future guard of this kind splits in two: the portable half may be
proposed here with a complete `## Core fit` receipt, and the runtime-specific half lives
in the runtime's own configuration, outside AgentFold.

The review item `message-queue/needs-human/reviews/trust-codex-github-auth-guard.md`
exists only on that branch, never reached `main`, and was therefore never surfaced by the
queue ritual. This decision voids it: trusting hooks that install outside the repository
is what the decision declines. It is left in place on the archived ref as part of the
historical record rather than answered.

What would revisit this: an agent-neutral standard for runtime hooks that several runtimes
implement, which would make such a guard portable rather than single-product. The original
reasoning about evidence-gated authentication survives on the archived ref as its own ADR,
dated 2026-07-22; this decision does not dispute that reasoning, only its home.
