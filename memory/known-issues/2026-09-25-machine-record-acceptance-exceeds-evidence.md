# Machine-record completion criteria exceed the recorded evidence

**Status:** open
**Severity:** medium
**Description:** The machine-record task checks a zero-unscoped-findings criterion, but its verification records nonzero results and current fold-shape probes still reproduce counterexamples
**Review-by:** 2026-12-24

## Symptom

Task `2026-08-18-fold-the-queue-machine-record` has a checked criterion stating:
"The new predicates report zero findings when run unscoped over every tracked Markdown
file in the repository." Its preserved whole-repository transcript instead reports
38 unscoped results. Later recovery provides unscoped record-swallow evidence, not zero
results for every predicate.

On 2026-09-25, calling `fold_shape_problems` directly on each of
`.github/pull_request_template.md`, `message-queue/open-actions.md`, and
`templates/pull-request.md` returned one finding. These are outside the runtime check's
intended scope; the ordinary reconciler still passes. This is a completion-evidence
mismatch, not a claim that normal queue validation is broken.

## Impact

A status audit can mistake checked boxes and a merged PR for satisfied acceptance.
The task therefore remains in review despite its useful implementation being merged.

## Workaround

Keep the task in review. Preserve original criteria and historical transcripts while the
completion-boundary action owns the discrepancy.

## Suggested fix

[Resolve the machine-record task's zero-unscoped-findings acceptance criterion against the recorded counterexamples before completing the task.](message-queue/needs-agent/requests/future-blocking-resolve-machine-record-acceptance-evidence.md)
