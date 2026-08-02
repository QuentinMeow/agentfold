# Scenario — the pull-request body

A pull request is where this repository asks its owner to look at something. The reader
opens it on a phone, has not seen the branch, and wants to know three things in this
order: what is different now, what they personally have to do, and whether they can trust
that it works. Everything else is optional depth and belongs behind a fold.

Read `../reference.md` for the craft. This file owns the section order, the folding rules,
and the GitHub mechanics that make the body render the way you intend.

## Section order

Fixed. A reader who stops after any section has a coherent picture of everything above it.

| # | Section | Folded? | Owns |
|---|---|---|---|
| 0 | Title | — | one imperative sentence naming the change |
| 1 | Stack note | no | which layer of a stack this is, if it is one |
| 2 | `## TL;DR` | no | numbered list, each item a before → after |
| 3 | `## What to review` | no | the reader's own to-do list, ranked |
| 4 | `## What changed and why` | yes | the self-contained full explanation |
| 5 | `## Changes` | yes | the summary list and the file table |
| 6 | `## Verification` | yes | real commands and their real output |
| 7 | `## Notes` | yes | dead ends, follow-ups, anything optional |

Sections 4 to 7 open with `<details>`. Nothing above section 4 is folded, because a folded
section is a section most readers never open.

## Title

One complete sentence in the imperative, no trailing period, naming the change in terms of
behaviour. It is layer 1 of the three-layer rule, so it must stand alone.

- No: `Fix bug`, `Update reconciler`, `Moving code from A to B`.
- Yes: `Stop a branch from blocking itself on a review it filed`.

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
3. **Nothing that was already answered is skipped.** A review filed before the branch was
   cut still blocks exactly as it did.
```

Bold the first clause of each item so the list is readable at a glance. If an item cannot
be written as a before and an after, it is not a summary item — move it to `## Changes`.

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

```markdown
## What to review

1. [Approve or reject the merge-gate change](https://github.com/OWNER/REPO/blob/<sha>/message-queue/needs-human/reviews/non-blocking-review-merge-gate.md)
   - Why this matters: three branches cannot merge until this behaviour is settled.
   - If you do nothing: the change stays merged and the review stays answerable; nothing stops.
2. [Choose how the three stranded reviews are disposed of](https://github.com/OWNER/REPO/blob/<sha>/message-queue/needs-human/decisions/non-blocking-dispose-stranded-reviews.md)
   - Why this matters: three tasks cannot leave review while their gate is unsatisfiable.
   - If you do nothing: the items stay live and answerable, and the tasks complete without them.
```

**Links here must be absolute and pinned to a commit.** A relative link in a pull-request
body is not rewritten by GitHub — it resolves against the pull-request URL and 404s — and
the boundary check accepts a URL only under the candidate's own
`https://<host>/<owner>/<repo>/blob/<full-sha>/` prefix. Use that exact form.

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

## Done when

A reader who opens the pull request, reads only the title, the TL;DR, and
`What to review`, and never expands a fold, knows what changed, whether it is safe, and
exactly what they owe — and none of those answers required opening another page.
