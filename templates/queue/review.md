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
6. Recommendation repeats one shown choice's `### ` label text; its counter-case
   sits beside it. The check compares text, so paraphrasing the label fails.
7. No machine field, hash, or token appears above the answer line.
8. Each decisive source is quoted and linked at its heading or selected lines;
   optional background and machine copies stay in For the record. See the source
   excerpt guidance in templates/README.md.
9. Under 800 words before the answer, and you never have to guess where you are:
   `python3 automation/reconcile/reconcile.py --word-count <this file>` prints
   your count against the budget. Four choices cost about 700 on their own, so
   cut background, never a choice, its example consequence, or a quoted source.

Three shapes a checker enforces that nothing else shows you:
- Every **Key:** value and every *Example consequence:* is read one physical line at
  a time. Wrap one onto a second line and the reader sees the whole sentence while
  every check sees only its first half. Keep each on one line, however long.
- Confidence is exactly `high`, `medium` or `low`, then a space, an em dash (U+2014),
  a space, and what you checked and did not. A hyphen or a bare adjective is refused.
- There is no **Look-at:** field. Say where to look in the prose, and put the
  machine copy in Full context.
-->

# <The question the owner can answer, in plain English>

**Action:** <one imperative sentence; handovers copy this verbatim as the link label>
**Why this matters:** <one sentence of consequence in the world, not in the repository>
**If you do nothing:** <one sentence: what stops, and what safely continues>

## What you need to know

**Today:** <what actually happens now — say "nothing is implemented" when that is true>
**What this would change:** <the delta being judged, stated as a proposal>
**What this does not decide:** <adjacent things a reader will assume are in scope>

<One or two short value-neutral paragraphs from zero context. This must stand alone: the
reader should be able to answer without opening anything.>

> <the source's own words — the sentence that decides this, copied, not paraphrased>
>
> — [<what this passage says>](<../../../ path to the file.md#heading-anchor>)

<Quote each decisive source; a comparison quotes both sides. Link a Markdown heading,
or bounded lines with #Lx or #Lx-Ly for text or code. Preserve wording and case; wrapping,
emphasis, and marked omissions in source order are allowed. If no source wording decides
the answer, replace this whole source block with exactly
`> No source document — everything you need is above.` A local-file review still quotes
its target. Put optional background below the answer, inside the fold.>

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

Answer in plain words — one sentence is enough. You never need to copy anything; the agent
that folds it shows you how it read your words before acting. If this page did not give you
enough to decide, say so and say what is missing — that is a complete answer, not a
rejection.

**Your review:** ______

## For the record

<details>
<summary>For the record — bookkeeping the reconciler reads. Nothing here needs you.</summary>

**Status:** waiting  
**Filed:** < YYYY-MM-DD >, by < who >[, from task `<id>`]  
**Full context:** `<root-relative path to the durable source>`  
**Resolution evidence:** `<non-queue path distinct from Review target>`  
**Review target:** `<root-relative path to the exact file being judged>`  
**Review revision:** sha256:<64 hex digits of that file's bytes>  
**Reviewed revision:** ______  
**Review outcome:** pending  
**Answer by:** < UTC YYYY-MM-DD — 90 days from Filed unless something real dates it >

</details>

<!-- Status ships as `waiting` with a local file bound. Before the artifact exists,
file it with **Status:** awaiting-artifact and both target and revision literally
`pending`, then publish the binding in one later commit that moves the status to
`waiting`; the folding agent moves it to `folding` on its claim edge.
A Git range uses **Review target:** git:<base>...<head> with a byte-identical
**Review revision:**, both unbackticked and both naming full 40- or 64-hex object
ids — a branch name or an abbreviated id names something that can move. An HTTPS
artifact uses one URL with a sha256 revision. Full context explains the judgment;
it is never the target.
`Reviewed revision` and `Review outcome` are the folding agent's, written once over
an already-committed response: it copies `Review revision` into `Reviewed revision`
and replaces `pending` with approved, changes-requested, rejected, abandoned, or
unanswerable — the last when your words say the item did not give you enough to
decide; it settles nothing about the subject and obliges a fresh question.
Then exactly one timing field matching the filename:
blocking-*   -> Blocks now: <task:<id> | transition:<name> | operation:<name>>
future-blocking-* -> Blocks at: <UTC YYYY-MM-DD | event:<name> | transition:<name>> [task:<id>]
non-blocking-* -> neither; If you do nothing above is the unattended outcome.
A needs-human item may bind only transition:start on a 0_backlog task, or
operation:<name> for one act with no undo. Merging, moving a task, and recording it
done never wait on an answer (message-queue/AGENTS.md owns this rule).
Add External assignment / External source only for a provider binding. On a
changes-requested resolution add Successor action and Follow-up review here.
For unanswerable, add **Successor action:** `<new needs-human/reviews path>` alone
on the resolving item. Create that distinct, new review in the same resolution
commit, with **Supersedes:** `<old review path>` pointing back. Preserve Full
context and the exact Review target and Review revision. Keep its delivery prefix
and every field the original item's schema uses for dependency timing, including
any task boundary.
The new item is waiting, with a blank Your review, blank Reviewed revision, and
pending Review outcome. An existing, answered, or awaiting-artifact item cannot be
this successor. Supply the missing context without changing the judgment or the
artifact; a later artifact change uses the ordinary retraction/publication path.
The old response stays immutable, and its predeclared Resolution evidence still
changes in the resolving commit. -->
