<!--
GitHub adapter. The schema is `templates/pull-request.md`; the craft is
`skills/explain-to-human/scenarios/pull-request.md`. Change the schema first, then this.

Delete every comment, including this one, before submitting.
Title: one complete imperative sentence naming the behaviour that changed.
Write the body after your final push — the queue links below must be pinned to the
commit CI will check.
No question or instruction aimed at the reader may appear outside "What to review".
-->

<!-- Delete unless this pull request is based on another open one. An alert renders only
at the top level, never inside a fold or a list item. -->
> [!NOTE]
> **Layer <n> of <N>.** Stacked on #<parent> (`<parent-branch>`); its base is that branch,
> not `main`. The **Files changed** tab shows only this layer. The stack lands bottom-up.

## TL;DR

<!-- Three to six items. Each one names a state before and a state after. -->

1. **<what is different>.** Before, <old behaviour>. Now, <new behaviour>.
2. **<what is different>.** Before, <old behaviour>. Now, <new behaviour>.

## What to review

<!-- One top-level list item per pending human action, most consequential first, each
carrying exactly one absolute commit-pinned link to its live queue item. Replace this
whole section with exactly `No queued action requested.` when there is none. -->

1. [<the queue item's Action, summarised>](https://github.com/<owner>/<repo>/blob/<full-sha>/message-queue/needs-human/<kind>/<prefixed-name>.md)
   - Why this matters: <copied from the item>
   - If you do nothing: <copied from the item>

## What changed and why

<details>
<summary>The whole picture — no other reading required</summary>

**What this is.**

**How it behaved before.**

**What forced the change.**

**How it behaves now.**

**What was decided, and why.**

**What this does not change.**

</details>

## Changes

<details>
<summary>What a reader would notice, then the files</summary>

- <observable difference>

| Area | Files | Why |
|---|---|---|
| <area> | `<path>`<br>`<path>` | <the one reason these changed together> |

</details>

## Verification

<details>
<summary>Commands actually run, and their real output</summary>

```
$ <command>
<real output>
```

</details>
