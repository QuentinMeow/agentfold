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

Claimants, reviewer identities, and findings use a closed source-text alphabet: Unicode
letters, marks, and numbers; ASCII space; and only `. , ; : ? ! ' " ( ) / @ + - —` as
punctuation. Tabs, non-ASCII separators, controls, invisible characters, and every other
character are invalid. Brackets, angle brackets, backslash, backtick, asterisk, underscore,
tilde, braces, and ampersand therefore exclude every Markdown link, image, reference,
escape, emphasis, code span, HTML tag, and entity by construction. An invalid claimant has
no review identity; an invalid reviewer or finding ends the formal block and leaves its
verdict under ordinary human-action detection.

The claimant comes only from the sole literal top-level field's unchanged raw suffix.
Raw comments, markup, entities, links, images, code, escapes, invisible characters, and
duplicate fields yield no claimant identity; Markdown semantics never repair that suffix.
After source validation, identity comparison and human-action token recognition apply NFKD
and remove every Unicode category-M mark. Composed and decomposed names compare equally,
accent-only distinctions conservatively collide, and marks cannot split voter names,
placeholders, or action keywords.
