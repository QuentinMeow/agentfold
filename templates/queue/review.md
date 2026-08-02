<!--
Filename: one delivery prefix, then a kebab-case slug. The three prefixes, what each
one means, and the rule that the filename is canonical (so no separate **Blocking:**
field exists) are stated once in `message-queue/AGENTS.md`, under "Routing: three
independent axes". Slug grammar: `handbook/naming-conventions.md`.

Before you file, check all nine. Lifecycle law lives in handbook/human-action-guide.md.
1. The title is a question the owner can answer without knowing this repository.
2. Exactly three fields above the first heading: Action, Why this matters, If you do nothing.
3. Today / What this would change / What this does not decide are true and specific.
4. Two or more choices, each with a cost and a concrete *Example consequence:*.
5. The axis sentence opens Your choices and says what the choices differ on.
6. Recommendation names one choice shown; its counter-case sits beside it.
7. No machine field, hash, or token appears above the answer line.
8. The source is linked once in the prose; For the record keeps the machine copies.
9. Under 700 words before the answer. Cut background, not choices.
-->

# <The question the owner can answer, in plain English>

**Action:** <one imperative sentence; handovers copy this verbatim as the link label>
**Why this matters:** <one sentence of consequence in the world, not in the repository>
**If you do nothing:** <one sentence: what stops, and what safely continues>

## What you need to know

**Today:** <what actually happens now — say "nothing is implemented" when that is true>
**What this would change:** <the delta being judged, stated as a proposal>
**What this does not decide:** <adjacent things a reader will assume are in scope>

<One or two short value-neutral paragraphs from zero context. Link the source exactly
once, here, as [<descriptive label>](<../../../ path to the file>). This must stand
alone: the reader should be able to answer without opening anything.>

## Your choices

<One sentence naming the axis the choices differ on. Not a restatement of them.>

### Approve
<What this accepts, and the state the repository enters. Name at least one cost.>
*Example consequence:* <a concrete scenario of life after this answer>

### Request changes
<The boundary stays closed; an agent repairs the named thing, publishes one exact
revision, and a fresh review returns to the owner. Name at least one cost.>
*Example consequence:* <a concrete scenario of life after this answer>

### Reject
<Only if declining is genuinely available. If it is not, drop this heading and say so
in the axis sentence — never pad an outcome nobody would pick.>
*Example consequence:* <a concrete scenario of life after this answer>

## What I recommend

**Recommendation:** <exactly one of the choices above> — <one sentence why>
**Strongest case against this:** <the best argument for a different answer>
**Confidence:** <high | medium | low> — <what you checked, and what you did not>

Answer in plain words — one sentence is enough. You do not need to copy anything or use
particular vocabulary; the agent that folds your answer does the bookkeeping and will
show you how it read your words before acting.

**Your review:** ______

## For the record

Bookkeeping the reconciler reads. Nothing here needs you.

**Status:** <awaiting-artifact | waiting | folding>
**Filed:** <YYYY-MM-DD>, by <who>[, from task `<id>`]
**Full context:** `<repo-relative path to the durable source>`
**Resolution evidence:** `<non-queue path distinct from Review target>`
**Review target:** <pending | `repo/path` | git:<full id or base...head> | one HTTPS link>
**Review revision:** <pending | sha256:<64 hex> | git:<full id> | git:<base>...<head>>
**Reviewed revision:** ______
**Review outcome:** <pending | approved | changes-requested | rejected | abandoned>
**Answer by:** <UTC YYYY-MM-DD — 90 days from Filed unless something real dates it>
<!-- Then exactly one timing field matching the filename:
blocking-*   -> Blocks now: <task:<id> | transition:<name> | operation:<name>>
future-blocking-* -> Blocks at: <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
non-blocking-* -> neither; If you do nothing above is the unattended outcome.
A needs-human item may bind only transition:start on a 0_backlog task, or
operation:<name> for one act with no undo. Merging, moving a task, and recording it
done never wait on an answer (message-queue/AGENTS.md owns this rule).
Add External assignment / External source only for a provider binding. On a
changes-requested resolution add Successor action and Follow-up review here. -->
