# Pick up stopping indented prose from hiding from the checks

**Status:** open
**Filed:** 2026-08-02, by claude, from a reported guardrail bypass — `automation/markdown_semantics.py`
**Action:** When this backlog item is selected, claim it and remove this completed pickup request in the same coordination commit.
**Full context:** `tasks/0_backlog/2026-08-02-stop-indented-prose-from-hiding-from-the-checks/task.md`
**Request kind:** task-pickup
**If unanswered:** Every gate that reads `semantic_text` keeps ignoring prose written as a four-space continuation under a list item; no committed record is known to exploit it today, so nothing stops.

## What you need to know

`strip_indented_code` blanks any line starting with four spaces or a tab. CommonMark
blanks such a line only when it does not interrupt a paragraph and when it sits four
columns past the enclosing list item's content column. The gap makes an ordinary list
continuation invisible to `queue-resolution`, `task-action-origin` and `link-check`, and
to every other consumer of the semantic view.

The rule to land: blank a line as indented code only where CommonMark parses one, and
correct the `semantic_text` docstring, which today claims that only genuine indented-code
lines change.

## Done when

The task has a claimant, has moved to `1_in-progress` with a plan and worklog, and this
request and its reciprocal `Queue actions` link have been removed in the claim commit.
