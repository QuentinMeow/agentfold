# Verification — single-source the queue delivery-prefix rule

**Verified:** 2026-07-31 by claude

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

The full before/after table for every deleted clause, the reconciler before/after runs,
the test-suite output, and the line-budget check are recorded once in the parent task's
`verification.md` (task 2026-07-31-collapse-restated-contract-rules), because both tasks
close with the same commits. This file records only what is specific to this task.

## The drift this task was filed for is gone

Before, in all five queue templates at line 4:

```
- future-blocking-: work may continue, but must stop at a named date, event, or transition.
```

while line 29 (or 28/33/57) of the same five files already read
`**Blocks at:** <UTC YYYY-MM-DD | event:<name> | transition:<name>>`. Two lines of the same
file disagreed, in five files.

After:

```
$ grep -rn "future-blocking-: " templates/
exit=1
```

No matches. The definition now exists only in `message-queue/AGENTS.md` lines 17-18:
"`future-blocking-<slug>.md`: work continues until an explicit UTC date, event, or
transition; unresolved action stops there." — which agrees with the `Blocks at` field lines
the templates still carry.

## Count: thirteen restatements removed, four left in place

Removed the delivery-prefix definitions from: the five `templates/queue/*.md`,
`templates/README.md`, `handbook/human-action-guide.md`, `handbook/collaboration-modes.md`,
`handbook/decision-guide.md`, all four `skills/*/SKILL.md`, and
`message-queue/needs-human/reviews/README.md`.

Deliberately left alone, with the reason:

- `handbook/naming-conventions.md` — states the queue-item *filename grammar*
  (`blocking-<kebab-slug>.md`, no date or numbering) and lists the prefixes without
  defining what they mean. That grammar is this file's own subject, not a copy of the
  owner's rule. Its "the prefix says when unresolved work stops, not how severe it is"
  half-line does overlap, but removing it would leave a naming rule with no stated
  purpose. Its link-check claim was corrected separately by the parent task.
- Root `AGENTS.md` guardrail — "Its filename says whether it blocks now, at a named future
  boundary, or never … (`message-queue/AGENTS.md`)". This is a one-clause summary plus the
  link, which is exactly the "restate a concept in one sentence, then link" pattern
  `handbook/AGENTS.md` prescribes, and root is required to be self-contained.
- `README.md` collaboration-mode table and `roadmap/current-state.md` line 65 — both use
  the prefixes as vocabulary in a mode table and a state description. Neither defines them.
- `memory/decisions/2026-07-23-queue-owns-pending-actions-and-timing.md` lines 34-36 — the
  full definitions, as the record of what was decided. "Records are immutable" forbids
  editing it, and it is correct to state the rule it established.

`history/` handovers and `tasks/` records also contain the strings, and were not touched:
they are session records, not live contracts.

## Correction to this task's original acceptance criteria

The task claimed that adding `message-queue/AGENTS.md` to the five templates would bring
the reference "inside `link-check`'s reach". That is false:

```
$ grep -n 'LINK_SKIP_DIRS' automation/reconcile/reconcile.py
264:LINK_SKIP_DIRS = {"templates", "history"}  # + memory/decisions (records)
7781:        if parts[0] in LINK_SKIP_DIRS or parts[0].startswith("."):
```

`check_links()` skips the whole `templates/` tree before examining any candidate, so those
five links are worth writing for the reader but are not mechanically verified. The criterion
was rewritten to say so rather than left as an untrue claim.
