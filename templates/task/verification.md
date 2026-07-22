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

**Reviewed revision:** <immutable commit reviewed by every verdict below>

- <reviewer / lens>: <approve | block> — <one-line finding or "could not break it">
- core-fit / <reviewer other than Claimed-by>: <approve | block> — <substitution or boundary challenged; required only when `--require-review` is explicitly selected>
