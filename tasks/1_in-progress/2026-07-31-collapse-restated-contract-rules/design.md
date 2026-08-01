# Design notes — collapse restated, circular, and unenforced contract rules

**Status:** decided

## Problem

Three judgment calls had no obvious answer.

**Which precedence sentence dies.** Root `AGENTS.md` said the closest `AGENTS.md` wins;
`handbook/AGENTS.md` said the root wins over anything in `handbook/`. For any file under
`handbook/` the closest contract is `handbook/AGENTS.md`, which hands authority to root,
which hands it back. A third statement sits in `handbook/principles/folder-as-a-service.md`,
which is near-immutable.

**Whether adding a metadata field to a decided ADR is a rewrite.** "Records are immutable"
is a root guardrail, but two ADR chains are missing exactly the metadata that tells a
reader what happened to them.

**Whether a partial reversal is a supersession.** Two edge-graph ADRs each overturn one
clause of a third and leave the rest standing. Marking the third `superseded` would retire
six clauses that still bind; leaving it unmarked keeps advertising two clauses that do not.

## Options considered

### Option A — Delete root's precedence sentence, keep the handbook's
Precedence would then be stated only for `handbook/`. Every other leaf — `tasks/`,
`memory/`, `automation/`, `services/` — would have no precedence rule at all.
*Example consequence:* an agent hits a conflict between `tasks/AGENTS.md` and root and
finds nothing anywhere telling it which to obey.

### Option B — Delete the handbook's inverted clause, keep root's
The universal rule survives and governs `handbook/` like every other folder. Root's
remaining self-defeating half — a tie-breaker followed by a denial that ties occur — is
resolved by deleting that half and linking the principle that already carries both the
rule and the repair.

### Option C — Rewrite the amended ADRs' prose to match reality
Directly contradicts the immutability guardrail, and both amending ADRs already rejected
exactly this in their own Alternatives sections.

### Option D — Add lineage fields only, and teach the index to read them
`templates/memory/adr.md` already declares `**Superseded-by:**` + `**Status:** superseded`
to be permitted edits to an existing ADR. Extending that carve-out to a partial reversal
keeps every sentence of every decision untouched.

## Chosen

**B and D.**

On precedence: `handbook/AGENTS.md`'s inverted clause is the whole bug — it is the only
sentence that points authority *upward* while root points it *downward*. Deleting it makes
`handbook/` obey the same rule as every other leaf, and the loop cannot re-form because no
file states precedence except `handbook/principles/folder-as-a-service.md`, which root now
links instead of restating. The half of root's sentence that denied conflicts can occur was
deleted rather than reworded, because the principle already states both the rule and the
remedy ("a conflict is a bug in the child") and root's job is to point at it.

On ADR metadata: **adding `Superseded-by:` is not a rewrite, and the schema says so.**
`templates/memory/adr.md` names that field plus `**Status:** superseded` and a `Review-by:`
bump as "the only edits an existing ADR may receive". The guardrail forbids changing what
was decided; these fields record what later happened *to* the decision, which is not part
of it. `**Amends:**`/`**Amended-by:**` is the same kind of fact about a smaller unit, so it
enters through the same declared carve-out rather than a new exception. No sentence of any
Context, Decision, Alternatives, or Consequences section was touched.

On partial reversal: an amended ADR keeps `Status: decided`, because the clauses nobody
overturned still bind. `generated_index()` gains one branch so those entries print
`**[amended]**` — visible to a booting agent, without falsely retiring the rest.

One thing I could not repair without your call, and did not fake: the successor of
`2026-07-23-queue-resolution-preserves-review-intent.md` declares `Supersedes:` while its
own prose keeps that decision's review-binding, terminal-outcome, and displaced-tip rules
in force. That is substantively an amendment wearing a supersession label. Changing the
successor's `Supersedes:` to `Amends:` would edit a recorded claim, which the carve-out does
not permit, so I honoured the declared relationship: the old ADR now carries
`Status: superseded` + `Superseded-by:`, which makes the file agree with both the generated
index and its successor. The over-claim is noted here rather than silently reclassified.

## Core fit

**Agent substitution:** pass — every change is markdown contract text plus one branch in
`generated_index()`; no agent runtime, model, or prompt format is referenced by any of it.
**Provider substitution:** not-applicable — nothing here reads or writes a provider surface.
**Repository substitution:** pass — an unrelated adopted repository inherits the same
`AGENTS.md` nesting rule, the same ADR schema, and the same generated memory index, and each
of the three defects (circular precedence, present-tense vaporware, unlinked ADR chains)
reproduces there identically because they live in the copied contract text.
**User-global writes:** none
**Why AgentFold core:** contract precedence, ADR lineage, and the memory index are harness
mechanisms every adopter gets; the `Amends:` field is a schema in `templates/`, which the
root contract names as the single source of truth for file formats.
**Thin adapter:** none
