<!--
The schema for a pull-request body. Copy it, fill it, delete every comment.

How to write the prose that goes in these slots — and the GitHub rendering rules that
decide whether it displays at all — is `skills/explain-to-human/scenarios/pull-request.md`.
This file is only the skeleton and the order.

Four rules the shape exists to serve:
1. Nothing above "What changed and why" is folded. A folded section is one most readers
   never open, so the summary and the reader's own to-do list stay visible.
2. Every section below it keeps its heading outside its fold. The heading is what a
   reader scans, and it is also what ends the machine-read action section: a fold with
   no heading above it is parsed as part of "What to review" and fails the boundary
   check.
3. "What to review" is checked at the provider boundary. Its heading text is exact,
   every action is one top-level list item carrying exactly one live canonical queue
   link, and any explanation is indented under its item and stays declarative. Nowhere
   else in the body may contain a question or an instruction aimed at the reader —
   including a stack note, so write "the stack lands bottom-up", never "merge bottom-up".
4. Links must be absolute. GitHub does not rewrite a relative link in a pull-request
   body, and the boundary check accepts a URL only under the candidate's own
   `https://<host>/<owner>/<repo>/blob/<full-sha>/` prefix. Write the body after the
   final push, so that revision is the one CI will check.

Title (not part of the body): one complete imperative sentence naming the behaviour that
changed. Not `Fix bug`, not `Update the reconciler`.
-->

<!--
Delete this alert unless this pull request is based on another open one. An alert renders
only at the top level: inside a fold or a list item, the reader sees literal `[!NOTE]`
text.
-->
> [!NOTE]
> **Layer <n> of <N>.** This is stacked on #<parent> (`<parent-branch>`), and its base is
> that branch rather than `main`. The **Files changed** tab shows only this layer.
>
> | # | Pull request | Scope |
> |---|---|---|
> | 1 | #<n> | <what that layer does> |
> | 2 | **#<this> ← you are here** | <what this layer does> |
>
> The stack lands bottom-up: #<n> first, then each layer above it.

## TL;DR

<!-- Three to six numbered items. Each names a state before and a state after; bold the
first clause. An item that cannot be written as a before and an after belongs in
"Changes", not here. -->

1. **<what is different, in one clause>.** Before, <old behaviour>. Now, <new behaviour>.
2. **<…>.** Before, <…>. Now, <…>.
3. **<…>.** Before, <…>. Now, <…>.

## What to review

<!-- The reader's own to-do list, most consequential first. One top-level list item per
action; nothing else at this level. The link label summarises the queue item's `Action`,
and the two indented lines copy its `Why this matters` and `If you do nothing`.
When there is genuinely nothing, this whole section is exactly the sentence
`No queued action requested.` and nothing else. -->

1. [<the queue item's Action, summarised>](https://github.com/<owner>/<repo>/blob/<full-sha>/message-queue/needs-human/<kind>/<prefixed-name>.md)
   - Why this matters: <copied from the item>
   - If you do nothing: <copied from the item>

## What changed and why

<details>
<summary>The whole picture — no other reading required</summary>

<!-- A blank line after `</summary>` is required, or everything below renders as raw
text. This section is self-contained: assume general software engineering knowledge and
nothing about this repository. Gloss every local term at first use. -->

**What this is.** <One paragraph naming the component and what it does, in plain
language.>

**How it behaved before.** <Concrete, with one example of the old behaviour.>

**What forced the change.** <The effect that made the old behaviour untenable — not the
investigation that found it.>

**How it behaves now.** <Concrete, replaying the same example.>

**What was decided, and why.** <Each choice, the alternative rejected, and the reason.>

**What this does not change.** <The adjacent things a reader will assume are in scope and
are not.>

</details>

## Changes

<details>
<summary>What a reader would notice, then the files</summary>

<!-- The list is observable differences, not file names. The table groups by reason:
several files changed for one reason are one row; one directory changed for two reasons
is two rows. Use `<br>` to stack file names — a fenced code block does not render in a
table cell. Never leave a cell empty; write `none`. -->

- <observable difference>
- <observable difference>

| Area | Files | Why |
|---|---|---|
| <area> | `<path>`<br>`<path>` | <the one reason these changed together> |

</details>

## Verification

<details>
<summary>Commands actually run, and their real output</summary>

<!-- Real output only. If something was not run, say so. If something failed, paste the
failure and say what it means. Never summarise a run into a claim. -->

```
$ <command>
<real output>
```

</details>

## Notes

<details>
<summary>Dead ends, follow-ups, anything optional</summary>

<!-- Delete this section, heading included, if it would be empty. -->

</details>
