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
Keep only blank lines between those elements. Before the first valid verdict, an immediate
second `**Reviewed revision:**` field fails closed. The first valid verdict ends that
prologue. Afterward, the first nonblank non-verdict ends the formal block, including an
exact revision field immediately after the verdict; it does not erase verdicts already
collected. Put explanations and non-core-fit review notes after that terminator. Exact
historical revision fields there are ordinary history and do not join or invalidate the
already-closed receipt.

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
Composite claimants use literal `/`, `+`, `;`, `,`, and standalone case-insensitive ASCII
`and` as co-claimant separators. ASCII spaces around each component are ignored. Every
component must be nonempty, source-valid, and non-placeholder or the entire claimant has no
authority. The whole key is the sorted multiset union of all component keys, excluding
separators but preserving repeated-component multiplicity; the claimant exposes that key
and every distinct component key. `D/B/T`, `D and B and T`, `N/A`, adjacent separators,
punctuation-only components, and `C++` therefore fail closed.

Reviewer keys remain sorted multisets of case-folded ASCII alphanumerics. A reviewer is not
independent when its key equals, contains, is contained by, or differs by at most one
balanced character substitution from any whole or component claimant key. This catches
punctuation, spacing, word-order, anagram, prefix, suffix, and nearby-spelling aliases.
Duplicate reviewer votes still replace only the same exact key; different stable role
labels are not merged by containment. These rules deliberately create false collisions,
so formal receipts use stable role labels rather than personal or display names.
Detection of
non-formal human actions separately removes Unicode category-M marks before tokenization.

Receipt heading candidates are collected in one source/structural/rendered line scan.
Zero or multiple visible candidates fail before any HTML-prefix parse; the sole candidate
checks its prefix once. The heading, revision field, and every verdict line must keep the
same literal line body at the same logical index in both structural and rendered-human
views, so invisible receipt evidence never receives the exception.
Verdict neutralization builds semantic line-start offsets once and maps the already
ordered verdict matches in one pass; it never rescans the growing document prefix for
each verdict.
