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
line. Write each `core-fit` line exactly as shown — plain, unindented, on one line, with
no emphasis, code marks, quote marker, checkbox or raw HTML anywhere up to the verdict
word. The finding is ordinary prose on that same line. Delete this section when no review
was run. Every other lens records its verdict below, with the verdict word in a code span,
because a bare one outside the receipt reads as a new human ask and refuses the commit:

- <reviewer / lens>: `<approve | block>` — <one-line finding or "could not break it">
