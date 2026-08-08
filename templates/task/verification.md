# Verification — <task title>

**Verified:** <YYYY-MM-DD> by <who>

Only commands actually run and their real output — never expected or paraphrased
output (root `AGENTS.md` guardrail). A reader must be able to re-run every line.

## <check name, e.g. "unit tests">

```
$ <exact command>
<real output, trimmed to the meaningful part>
```

## Review verdicts (when a review was explicitly run)

**Reviewed revision:** <full immutable commit ID reviewed by every verdict below>

- core-fit / <reviewer other than Claimed-by>: <approve | block> — <substitution or boundary challenged; required only when `--require-review` is explicitly selected>

Those three elements are the closed receipt both gates read, and only blank lines may
separate them: this heading once, the revision field, then consecutive `core-fit` lines.
The receipt ends here, at the first other nonblank line. A finding is ordinary one-line
prose; a `core-fit` line that misses the shape refuses the whole receipt instead of being
skipped. Every other lens records its verdict below, under ordinary prose rules:

- <reviewer / lens>: <approve | block> — <one-line finding or "could not break it">
