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
An immediate second `**Reviewed revision:**` field inside that contiguous prologue fails
closed. Exact historical revision fields after the first terminator are ordinary history
and do not join or invalidate the already-closed receipt.

Claimants and reviewer identities use a closed ASCII source alphabet: letters, digits,
space, and only `. , ; ? ! ' " ( ) / @ + -` as punctuation. Colon is excluded because it
terminates the reviewer handle. Findings use the same alphabet plus colon. The em dash is
the structural delimiter outside those components. Every non-ASCII character, tab,
control, invisible character, and other punctuation is invalid. Brackets, angle brackets,
backslash, backtick, asterisk, underscore, tilde, braces, and ampersand therefore exclude
every Markdown link, image, reference, escape, emphasis, code span, HTML tag, and entity
by construction. An invalid claimant has no review identity; an invalid reviewer or
finding ends the formal block and leaves its verdict under ordinary human-action detection.

The claimant comes only from the sole literal field's unchanged raw suffix, at file start
or immediately after an ASCII-blank raw line. A preceding paragraph, blockquote, or list
line makes it a lazy continuation and yields no identity. An immediate raw `---` or `===`
Setext underline also yields no identity. Raw comments, markup, entities,
links, images, code, escapes, invisible characters, non-ASCII characters, and duplicates
also yield no claimant identity. The literal line body must remain character-for-character
unchanged at the same logical line index in both the structural Markdown view and the
rendered-human view; neither view
may supply or repair characters. The claimant and the exact review heading must also begin
outside every still-open raw HTML container. A closed container or an HTML-looking example
inside fenced, indented, or inline code does not interfere; any unclosed visible, hidden,
non-prose, or custom container fails closed even when a blank line made later Markdown
structurally visible again. An incomplete HTML-like start, end, comment, declaration, or
processing marker also fails closed while parser input remains pending at the authority
line, even if a later line eventually supplies `>`.
Placeholder rejection, claimant comparison, and duplicate-voter replacement all use the
same sorted multiset of case-folded ASCII alphanumerics. Punctuation, spacing, token
boundaries, word order, reordered placeholders such as `yet none`, and anagram placeholders
such as `D B T` cannot create another voter. This deliberately collides anagrams and
therefore formal receipts use distinct stable role labels, not personal or display names.
Detection of
non-formal human actions separately removes Unicode category-M marks before tokenization.

Receipt heading candidates are collected in one source/structural/rendered line scan.
Zero or multiple visible candidates fail before any HTML-prefix parse; the sole candidate
checks its prefix once. The heading, revision field, and every verdict line must keep the
same literal line body at the same logical index in both structural and rendered-human
views, so invisible receipt evidence never receives the exception.
