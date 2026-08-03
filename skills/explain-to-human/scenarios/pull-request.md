# Scenario — the pull-request body

A pull request is where this repository asks its owner to look at something. The reader
opens it on a phone, has not seen the branch, and wants to know three things in this
order: what is different now, what they personally have to do, and whether they can trust
that it works. Everything else is optional depth and belongs behind a fold.

Read `../reference.md` for the craft. This file owns the section order, the folding rules,
and the GitHub mechanics that make the body render the way you intend. The skeleton to
copy is `templates/pull-request.md`; GitHub pre-fills it from
`.github/pull_request_template.md`.

## Section order

The order of the sections that appear is fixed. Two of them are conditional: the stack
note only when this is a stacked pull request, and `Notes` only when it has content.

| # | Section | Present | Folded | Rough budget |
|---|---|---|---|---|
| 0 | Title | always | — | one sentence |
| 1 | Stack note | only when stacked | no | 5 lines |
| 2 | `## TL;DR` | always | no | 3–6 items |
| 3 | `## What to review` | always | no | 1–5 entries, or the no-action sentence |
| 4 | `## What changed and why` | always | yes | under 600 words |
| 5 | `## Changes` | always | yes | one row per reason |
| 6 | `## Verification` | always | yes | real output, uncut |
| 7 | `## Notes` | only when non-empty | yes | short |

Three rows of this table are reported back at the pull-request boundary: a required section
missing, a section out of this order, and a `## TL;DR` outside three to six numbered items.
`automation/check_action_projection.py --pull-request-body-shape` prints each one with an
`(advisory)` marker and never changes its own exit status because of it, so a body that
breaks one still merges — the line is there to be seen, not to refuse
(`memory/decisions/2026-08-02-readability-enforcement-disposition.md`). Whether the prose
in a section was worth reading is not checked anywhere.

**How a folded section is written.** Its `##` heading stays *outside* the fold, and the
`<details>` block opens immediately under it:

```markdown
## What changed and why

<details>
<summary>The whole picture — no other reading required</summary>

…content…

</details>
```

The heading outside is what a reader scans and what tells them the section exists without
expanding it. It is also load-bearing for the boundary check, which treats a section as
running until the next heading of the same or higher level: a fold with no heading above it
is parsed as part of `What to review` and rejected. The `<summary>` line is not a second
title — it says what expanding buys, in a few words.

Nothing above section 4 is folded, because a folded section is one most readers never open.

## Title

One complete sentence in the imperative, no trailing period, naming the change in terms of
behaviour. It is layer 1 of the three-layer rule, so it must stand alone.

- No: `Fix bug`, `Update reconciler`, `Moving code from A to B`.
- Yes: `Stop a branch from blocking itself on a review it filed`.

**The title is not the commit subject.** A commit subject is written for someone reading
`git log` who will look at the diff next; the title is written for someone who will not.
`Judge a handover at the grammar it was written under` is a good commit subject and a bad
title; `Stop a format change from making every older branch unmergeable` is the title for
the same commit.

## TL;DR

Numbered, three to six items, each one short enough to read in a breath. Every item names
the state before and the state after — that pairing is what makes the list a summary
rather than a changelog.

```markdown
## TL;DR

1. **A branch no longer blocks itself.** Before, a pull request that filed its own review
   could never merge, because the merge check counted that review as unanswered. Now the
   check skips an action the range itself created, and reports it at the next boundary.
2. **Three stuck branches can merge.** Before: `task/…-let-a-human-answer` and two others
   were permanently refused. After: all three pass the merge probe.
3. **Nothing already answered is skipped.** Before and after, a review filed before the
   branch was cut blocks exactly as it did.
```

Bold the first **sentence** of each item — a fragment in bold reads as a broken heading.
The 25-word ceiling is per sentence, not per item: an item is two or three short sentences,
and splitting the before from the after into separate items breaks the pairing.

If an item cannot be written as a before and an after, it is not a summary item — move it
to `## Changes`. The one exception is a *no-change* claim, which is written as "Before and
after, X" so the reader can see it was checked rather than forgotten.

**When the change has no observable behaviour** — a records-only commit, a documentation
edit, a rename — say that in the first item rather than manufacturing a before and an after.
"Nothing behaves differently; this only changes what the repository records about X" is a
complete and honest summary, and the `Verification` section then says what was checked
instead of what was tested.

## What to review

This is the reader's to-do list, and it is the only part of the body they are obliged to
act on. It is also machine-checked at the provider boundary, so its shape is not free:

- The heading text is exactly `What to review`.
- Every action is one **top-level list item**. Nothing else may sit at the top level of
  this section — no preamble paragraph, no closing sentence.
- Each item contains **exactly one** link to a live canonical queue item, and no other
  action-shaped link. The link label summarises that item's `Action` field.
- Explanation goes **indented under** its own item, and stays declarative. A question or
  a directive that is not the queue-link label fails the check.
- When there is genuinely nothing, the section body is exactly
  `No queued action requested.` and nothing else.

Order the items so the most consequential is first. For each one, indent two lines: why it
matters, and what happens if it is ignored. Both are copied from the queue item itself, so
this section originates nothing — it projects.

> Careful: a handover projects the same two fields, but with a byte-exact grammar that a
> check enforces (`history/AGENTS.md`). Here the wording is free prose. Do not copy a
> pull-request entry into a handover, or the reverse — they look almost identical and only
> one of them is checked.

```markdown
## What to review

1. [Approve or reject the merge-gate change](https://github.com/OWNER/REPO/blob/<sha>/message-queue/needs-human/reviews/non-blocking-review-merge-gate.md)
   - Why this matters: three branches cannot merge until this behaviour is settled.
   - If you do nothing: the change stays merged and the review stays answerable; nothing stops.
2. [Choose how the three stranded reviews are disposed of](https://github.com/OWNER/REPO/blob/<sha>/message-queue/needs-human/decisions/non-blocking-dispose-stranded-reviews.md)
   - Why this matters: three tasks cannot leave review while their gate is unsatisfiable.
   - If you do nothing: the items stay live and answerable, and the tasks complete without them.
```

**Links here must be absolute and pinned to one specific commit.** A relative link in a
pull-request body is not rewritten by GitHub — it resolves against the pull-request URL and
404s — and the boundary check accepts a URL only under the candidate's own
`https://<host>/<owner>/<repo>/blob/<full-sha>/` prefix.

That commit is not your branch head. For a pull request the candidate is the commit GitHub
computes at `refs/pull/<number>/merge`, so it does not exist until the pull request does and
no local revision matches it. The order that works:

1. Push the branch and open the pull request.
2. `git ls-remote origin refs/pull/<number>/merge` — that SHA is the prefix.
3. Write the body with those links; editing the body re-runs the check.

The merge commit is recomputed whenever the head or the base moves, so links pinned to an
old one go stale — most often when a parent in a stack merges and the child's base changes.
The check reports it, and refreshing the body is the whole fix.

### Everywhere else in the body is indicative

The same check refuses any sentence outside this section that reads as a request or a
grant of permission. That is deliberate — an ask that lives only in a pull-request body is
an ask with no file behind it — but it catches innocent phrasings too, so write the rest of
the body in the indicative with a named subject.

| Refused | Accepted |
|---|---|
| A branch that filed its own review can now merge. | A branch is no longer blocked by a review it filed itself. |
| Merge from the bottom up. | The stack lands bottom-up. |
| Please look at the caching change. | The caching change is the one with real risk. |
| Let me know if the wording is wrong. | *(file a clarification item and link it above)* |

The pattern is that "can now <verb>" and bare imperatives read as permission or
instruction. Naming the subject and using the present or past indicative fixes it without
losing anything.

## What changed and why

Folded, and **self-contained**: a reader who opens only this section and nothing else must
end up with the whole picture. Assume general software engineering knowledge and nothing
about this repository.

Cover, in this order:

1. **What the thing is.** One paragraph explaining the component in plain language, with
   every local term glossed.
2. **How it behaved before.** Concrete, with an example of the old behaviour.
3. **What went wrong, or what forced the change.** The effect, not the investigation.
4. **How it behaves now.** Concrete, with the same example replayed.
5. **What was decided, and why.** Each choice, the alternative rejected, and the reason.
6. **What this does not change.** The adjacent things a reader will assume are in scope.

Where a workflow changed, show both workflows end to end, not only the changed step. A
before/after table is usually enough; a `mermaid` fenced block renders natively on GitHub
when the change is genuinely about ordering or branching.

## Changes

Folded. Two parts, in this order.

**The list** — one line per change, each naming an observable difference. This is not the
file list; it is what a reader would notice.

**The file table** — three columns: what area, which files, why they changed. Group by
reason, not by directory: several files that changed for one reason are one row, and one
directory whose files changed for two different reasons is two rows.

```markdown
| Area | Files | Why |
|---|---|---|
| Merge boundary | `automation/reconcile/reconcile.py`<br>`automation/check_action_projection.py` | Skips an action the candidate range itself filed. |
| Contract | `handbook/git-workflow.md` | States the new rule where agents already look for merge rules. |
| Tests | `automation/tests/test_reconcile_queue.py` | Four cases covering self-filed, pre-existing, answered, and re-reported. |
```

Use `<br>` to stack file names in a cell; a fenced code block does not render inside a
table cell. Never leave a cell empty — write `none`.

The `Why` column is the one place mechanism is allowed, because the row already names the
files it is about. Say what the change makes those files do, in one clause; the effect for
the reader belongs in the list above the table, not repeated per row.

## Verification

Folded. Real commands and their real output, copied, never summarised into a claim. If
something was not run, say it was not run. If something failed, paste the failure and say
what it means.

## GitHub mechanics that decide whether this renders

These are empirically verified behaviours, not style preferences.

- **Alerts only at the top level.** `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`,
  `> [!WARNING]`, `> [!CAUTION]` render only when the marker is alone on the first line of
  the blockquote. They **do not render inside `<details>`** and do not render inside a list
  item — in both cases the reader sees the literal text `[!NOTE]`. Custom titles are not
  supported. Use at most one or two per body.
- **`<details>` needs a blank line after `</summary>`**, or the markdown inside is treated
  as raw HTML and renders literally. Leave a blank line before `</details>` too.
- **Headings in a pull-request body have no anchors.** A table of contents built from
  `#section` links silently goes nowhere. Do not build one.
- **Relative links do not work.** Use absolute URLs; pin file links to a commit SHA.
- Tables, fenced code, `mermaid` blocks, images, and nested `<details>` all render inside a
  `<details>`. Screenshots should stay outside it — a reader only compares what they can
  see without clicking.
- `<script>`, `<style>`, `<iframe>`, `class`, `style`, and event handlers are stripped.

## Stacked pull requests

When this branch is based on another open pull request rather than on `main`, the first
thing in the body is a top-level alert saying so. Without it, a reviewer reads the wrong
diff and reviews work that is already approved below.

```markdown
> [!NOTE]
> **Layer 2 of 4.** This is stacked on #61 (`task/2026-08-01-write-the-explanation-skill`)
> and its base is that branch, not `main`. The **Files changed** tab shows only this
> layer; the **Commits** tab also lists the commits it inherits from #61.
>
> | # | Pull request | Scope |
> |---|---|---|
> | 1 | #61 | the explanation skill |
> | 2 | **#62 ← you are here** | the pull-request body schema |
> | 3 | #63 | the guidance rewrite |
> | 4 | #64 | the publish-and-report ritual |
>
> Merge from the bottom up.
```

If the stack members all target `main` instead, say that the diff includes the layers
below and give a compare link scoped to this layer:
`https://github.com/OWNER/REPO/compare/<base-branch>...<this-branch>`.

## One complete body, end to end

Every rule above is visible in this example. The seams between sections are what a rule
list cannot show, so read this before drafting your first one.

````markdown
TITLE: Stop a format change from making every older branch unmergeable

## TL;DR

1. **A branch cut before a format change can be merged again.** Before, the merge check
   judged a handover (the record an agent leaves at the end of a session) against the
   newest format anywhere in history. Now it judges each record against the format its own
   commit declared.
2. **One open pull request and one record already on `main` were the live casualties.**
   Before: #44 was refused outright and a record on `main` carried the same latent failure.
   After: both pass, judged at the format they were written under.
3. **Cutting a branch early still escapes nothing.** Before and after, the rules that
   *reject* a record come from the highest format the merge itself reaches.
4. **Nothing already refused is now accepted.** A record written under the current format
   is checked exactly as it was.

## What to review

1. [Say whether judging a record at its own format is the right rule](https://github.com/OWNER/REPO/blob/<sha>/message-queue/needs-human/reviews/non-blocking-review-record-grammar.md)
   - Why this matters: it decides whether an old record can ever be re-judged by a newer rule.
   - If you do nothing: the rule stands and the two blocked branches merge; nothing stops.

## What changed and why

<details>
<summary>The whole picture — no other reading required</summary>

**What this is.** Every session leaves a handover: a short file recording what happened,
written once and never edited afterwards. A checker validates each handover's wording
against a numbered format, and the format number is bumped when the wording rules change.

**How it behaved before.** The checker picked the highest format number it could reach
anywhere in Git history and judged every handover against it — including handovers written
months earlier. A record written under format 1 was told to use wording invented in format
3, and the only repair the checker named was editing the file, which this repository
forbids.

**What forced the change.** Two branches became permanently unmergeable. Neither had done
anything wrong: both were cut before a format bump and carried correct records for their
time.

**How it behaves now.** Each record is judged against the format declared in the commit
that created it. The same two branches now pass.

**What was decided, and why.** Judging by creation format could have been done by
re-writing old records instead; that was rejected because committed records are immutable
here, and rewriting them would destroy the audit trail the records exist for.

**What this does not change.** Rules that *reject* content still come from the newest
format the merge reaches, so cutting a branch early is not a way to escape a new
restriction. Only the required wording is pinned to creation.

</details>

## Changes

<details>
<summary>What a reader would notice, then the files</summary>

- Two blocked branches pass the merge check.
- An old record is no longer told to use wording invented after it was written.

| Area | Files | Why |
|---|---|---|
| Format resolution | `automation/reconcile/reconcile.py` | Reads the format marker from the record's creation commit rather than the newest reachable one. |
| Tests | `automation/tests/test_reconcile_queue.py` | Four cases: withdrawn format, parallel-history format, early branch cannot evade a rejection, current record unchanged. |

</details>

## Verification

<details>
<summary>Commands actually run, and their real output</summary>

```
$ python3 automation/run_tests.py
tests: 12/12 files passed
```

The four new cases were also run against the previous checker by extracting the parent
commit's tree; all four fail there, which is what makes them a regression test rather than
a description. CI was not run — this is a local result only.

</details>
````

## Done when

A reader who opens the pull request, reads only the title, the TL;DR, and
`What to review`, and never expands a fold, knows what changed, whether it is safe, and
exactly what they owe — and none of those answers required opening another page.
