# Verification — <task title>

**Verified:** <YYYY-MM-DD> by <who>

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## <check name, e.g. "unit tests">

```
$ <exact command>
<real output, trimmed to the meaningful part>
```

## Review verdicts

**Reviewed revision:** <full immutable commit ID reviewed by every verdict below>

- core-fit / <reviewer other than Claimed-by>: <approve | block> — <substitution or boundary challenged; required only when `--require-review` is explicitly selected>

Those three elements are the closed receipt both gates read. The heading is exact, only
blank lines may separate them, and the receipt ends here, at the first other nonblank
line. Decorating a `core-fit` line refuses the whole receipt rather than dropping just
that verdict. A finding is ordinary one-line prose, kept on one line and free of raw HTML
tags. Delete this section when no review was run. Every other lens records its verdict
below, with the verdict word in a code span, because a bare one outside the receipt reads
as a new human ask and refuses the commit:

- <reviewer / lens>: `<approve | block>` — <one-line finding or "could not break it">
