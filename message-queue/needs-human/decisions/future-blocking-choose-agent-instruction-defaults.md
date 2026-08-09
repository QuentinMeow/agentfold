# Which engineering defaults should every coding project inherit?

**Action:** Choose contract-aware defaults, the screenshot's strict defaults, or a mixed set for the three conflicting areas.
**Why this matters:** These defaults will shape changes across every repository, while a strict reading would also overturn explicit compatibility and dependency promises in AgentFold.
**If you do nothing:** The global file stays unchanged and the repository-instruction refactor remains in backlog; existing projects continue under their current local rules.

## What you need to know

**Today:** The global file contains only GitHub authentication safety rules. AgentFold's
local contracts preserve published interfaces and immutable records, require its examples
and automation to use the Python standard library, and permit staged or experimental work
when its boundary is explicit.
**What this would change:** Seven visible screenshot bullets would become concise global
engineering defaults, with research-backed instruction-hygiene rules added around them.
**What this does not decide:** The GitHub authentication block stays intact, and a closer
repository or folder contract still overrides a personal default when its scope differs.

The screenshot's simplicity, layering, modularity, and reuse principles already agree
with the repository. Three absolutes do not: deleting all backward compatibility, choosing
libraries despite local dependency constraints, and rejecting every temporary
implementation. The [current repository contract](../../../AGENTS.md) records the
portability and immutability constraints behind those conflicts; you do not need to open
it to choose because the concrete effects are below.

## Your choices

The options differ in whether general preferences may override explicit contracts and
whether reversible experiments count as unacceptable stopgaps.

### Option A — Contract-aware defaults
Remove obsolete paths only after callers and stored data are migrated; prefer existing or
maintained libraries only when the repository permits them and they reduce total cost;
avoid disposable production architecture while allowing bounded, reversible experiments
with an exit condition. Cost: the rules need exceptions, so they are less slogan-like.
*Example consequence:* the quote API keeps its promised JSON output, an unused internal
helper is deleted, no package is added to a standard-library-only service, and a small
prototype may be replaced after it proves the boundary.

### Option B — Strict screenshot defaults
Delete compatibility paths instead of carrying migrations, favor maintained libraries
over local implementations, and reject anything intended to be replaced later. Cost:
AgentFold's closer contracts must also be changed or they will override these global
defaults; changing them would break recorded decisions and possibly consumers.
*Example consequence:* a quote-output redesign removes the old shape in one change and
updates the bundled command line at once, even though an external caller may still depend
on the published shape.

### Option C — Mixed defaults
Choose A or B separately for compatibility, dependencies, and temporary implementations.
Cost: the resulting policy is more precise but harder to remember, and an omitted axis
would require another question before implementation.
*Example consequence:* you could choose strict cleanup for obsolete internal code, keep
repository dependency bans, and still allow reversible prototypes with explicit exit
criteria.

## What I recommend

**Recommendation:** Option A — it preserves the screenshot's intent against speculative
complexity without letting a personal preference silently break a public contract or a
repository's portability boundary.
**Strongest case against this:** Option B is sharper for greenfield product code and more
aggressively prevents compatibility baggage that nobody actually needs.
**Confidence:** high — I compared all fourteen tracked contracts with current guidance
from OpenAI, the AGENTS.md standard, GitHub, and Anthropic; I did not find an eighth rule
in the single screenshot supplied.

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your answer:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** waiting
**Filed:** 2026-08-09, by codex, from task `2026-08-09-refactor-agent-instructions`
**Full context:** `AGENTS.md`
**Resolution evidence:** `memory/decisions/2026-08-09-agent-instruction-defaults.md`
**Answer by:** 2026-11-07
**Blocks at:** transition:start task:2026-08-09-refactor-agent-instructions
