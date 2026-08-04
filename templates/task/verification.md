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

Claimants, reviewer identities, and findings use a closed ASCII source alphabet: letters,
digits, space, and only `. , ; : ? ! ' " ( ) / @ + -` as punctuation. The em dash is the
structural delimiter outside those components. Every non-ASCII character, tab, control,
invisible character, and other punctuation is invalid. Brackets, angle brackets, backslash,
backtick, asterisk, underscore, tilde, braces, and ampersand therefore exclude every
Markdown link, image, reference, escape, emphasis, code span, HTML tag, and entity by
construction. An invalid claimant has no review identity; an invalid reviewer or finding
ends the formal block and leaves its verdict under ordinary human-action detection.

The claimant comes only from the sole literal field's unchanged raw suffix, at file start
or immediately after an ASCII-blank raw line. A preceding paragraph, blockquote, or list
line makes it a lazy continuation and yields no identity. An immediate raw `---` or `===`
Setext underline also yields no identity. Raw comments, markup, entities,
links, images, code, escapes, invisible characters, non-ASCII characters, and duplicates
also yield no claimant identity; Markdown semantics never repair that suffix. Placeholder
comparison ignores allowed punctuation, so decorated spellings still reject. Authority
comparison uses the sorted multiset of case-folded ASCII alphanumerics: punctuation,
spacing, token boundaries, and word order cannot create another voter. This deliberately
collides anagrams and therefore formal receipts use distinct stable role labels, not
personal or display names. Duplicate-voter replacement uses the same key. Detection of
non-formal human actions separately removes Unicode category-M marks before tokenization.
