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

- core-fit / <reviewer other than Claimed-by>: <approve|block> — <one-line substitution or boundary finding>

When `--require-review` is explicitly selected, the heading, reviewed-revision field,
and one or more consecutive core-fit verdicts above form one contiguous formal block.
Keep only blank lines between those elements. The first nonblank non-verdict ends the
formal block; put explanations and any non-core-fit review notes after it.

Reviewer identities and findings are plain text only. Markdown links (inline, reference,
collapsed, or shortcut), emphasis, inline code, HTML/entities, or invisible formatting
make that line non-formal, end the block, and leave its verdict under ordinary human-action
detection. This restriction keeps displayed prose and formal evidence from disagreeing.
