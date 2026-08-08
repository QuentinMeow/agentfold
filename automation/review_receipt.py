#!/usr/bin/env python3
"""The one closed core-fit review receipt both gates read.

`memory/decisions/2026-08-04-review-receipt-parser-authorization.md` authorizes exactly
one grammar: one exact top-level `## Review verdicts` heading, one
`**Reviewed revision:** <full commit id>` field as its first line, then one or more
consecutive `- core-fit / <reviewer>: <approve|block> — <finding>` lines. Only blank
lines separate those elements, and the block ends at the first other nonblank line.

Both gates parse the same structural view of the same bytes, so neither can accept a
receipt the other refuses. `rendered_human_text` is never the parse view: its own
docstring forbids reading headings or fields from it, and raw HTML renders text there
that no Markdown structure supports. The action gate instead locates each accepted
verdict's own line in the rendered view by literal search, the way it already locates a
projected queue link, and blanks the structural token at that offset.

What this module guarantees, and nothing more: inside the one receipt section, a line
that reaches for the verdict shape and misses is reported rather than skipped. The loose
recognizer is deliberately blind to the list marker and the dash, because a verdict
written `1. core-fit / …` or with an ASCII hyphen is still a verdict reaching for the
shape, and reading it as ordinary prose would end the receipt and drop it together with
every verdict after it. That was the fail-open the 2026-08-07 withdrawal decision named.

Three things still leave the tally without an error, all of them by prior design and
none of them this module's to change. A verdict inside a code fence or an HTML comment
is blanked before any gate sees it, which `test_fenced_review_example_is_not_a_verdict`
requires. A second verdict from an identity already recorded replaces the first, which is
the core-scope gate's "latest verdict per reviewer" rule. A verdict outside the one
`## Review verdicts` section is not in the receipt at all.
"""
import re
import unicodedata
from collections import namedtuple

from markdown_semantics import semantic_text

SECTION_RE = re.compile(
    r"^## Review verdicts[ \t]*\r?\n(.*?)(?=^##(?:[ \t]|\r?$)|\Z)",
    re.M | re.S,
)
FULL_COMMIT_PATTERN = r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})"
REVISION_RE = re.compile(
    rf"^\*\*Reviewed revision:\*\*[ \t]*({FULL_COMMIT_PATTERN})[ \t]*$", re.M
)
REVISION_FIELD_RE = re.compile(r"^\*\*Reviewed revision:\*\*", re.M)
VERDICT_RE = re.compile(
    r"- core-fit / (?P<reviewer>[^:\r\n]+):[ \t]*(?P<verdict>approve|block)"
    r"[ \t]+—[ \t]+(?P<finding>.+)$",
    re.I,
)
# The one recognizer for "this line is reaching for a verdict", used for both the line
# that fails inside the block and the line stranded after it, so the two can never drift
# apart again. It ignores the list marker entirely — `-`, `*`, `+`, `1.`, `1)`, `•`, or
# none — and stops before the delimiter, so an en dash or ASCII hyphen is caught too.
LOOSE_VERDICT_RE = re.compile(
    r"[ \t]*(?:\d{1,9}[.)]|[^\w\s])?[ \t]*core-fit[ \t]*/", re.I
)
# The exemption belongs to the artifact the core-scope gate actually validates. Nothing
# validates a receipt in `worklog.md` or `design.md`, so nothing there may claim it. The
# shape is matched whole, never by basename.
RECEIPT_PATH_RE = re.compile(
    r"tasks/\d_[a-z][a-z-]*/\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*/verification\.md"
)
# The same word tokens `check_core_scope.identity_key` counts. A reviewer with none of
# them parses as a verdict and then vanishes from the tally, so it is refused here.
REVIEWER_WORD_RE = re.compile(r"[^\W_]", re.UNICODE)

Verdict = namedtuple("Verdict", "reviewer verdict line token_start token_end")
Receipt = namedtuple("Receipt", "revision verdicts errors")

MISSING_SECTION = "verification.md needs exactly one exact `## Review verdicts` heading"
MISSING_REVISION = (
    "Review verdicts needs exactly one real `**Reviewed revision:** <commit>` field, "
    "as the first line of the receipt"
)
UNCANONICAL_VERDICT = (
    "Review verdicts rejects a core-fit line that is not "
    "`- core-fit / <reviewer>: <approve|block> — <finding>`: {0}"
)
STRANDED_VERDICT = (
    "Review verdicts has a core-fit line outside the contiguous receipt block: {0}"
)
EMPTY_REVIEWER = (
    "Review verdicts rejects a core-fit line whose reviewer has no identity: {0}"
)


def _excerpt(line):
    trimmed = line.strip()
    return trimmed if len(trimmed) <= 80 else trimmed[:77] + "..."


def _lines(text):
    """Yield (offset from the start of `text`, line without its ending) pairs."""
    start = 0
    for piece in text.split("\n"):
        yield start, piece.rstrip("\r")
        start += len(piece) + 1


def parse_review_receipt(text):
    """Return the single receipt in one artifact, or the errors that refuse it."""
    structural = semantic_text(text or "")
    sections = SECTION_RE.findall(structural)
    if len(sections) != 1:
        return Receipt(None, (), (MISSING_SECTION,))
    body = sections[0]
    lines = list(_lines(body))
    index = 0
    while index < len(lines) and not lines[index][1].strip():
        index += 1
    opening = lines[index][1] if index < len(lines) else ""
    revision_match = REVISION_RE.fullmatch(opening)
    if revision_match is None or len(REVISION_FIELD_RE.findall(body)) != 1:
        return Receipt(None, (), (MISSING_REVISION,))

    errors = []
    verdicts = []
    in_block = True
    for _offset, line in lines[index + 1:]:
        if not line.strip():
            continue
        matched = VERDICT_RE.fullmatch(line) if in_block else None
        if matched is not None:
            reviewer = matched.group("reviewer")
            if REVIEWER_WORD_RE.search(unicodedata.normalize("NFKC", reviewer)) is None:
                errors.append(EMPTY_REVIEWER.format(_excerpt(line)))
                continue
            verdicts.append(Verdict(
                reviewer,
                matched.group("verdict").lower(),
                line,
                matched.start("verdict"),
                matched.end("verdict"),
            ))
            continue
        if LOOSE_VERDICT_RE.match(line) is not None:
            errors.append(
                (UNCANONICAL_VERDICT if in_block else STRANDED_VERDICT)
                .format(_excerpt(line))
            )
        in_block = False
    if errors:
        return Receipt(revision_match.group(1), (), tuple(errors))
    return Receipt(revision_match.group(1), tuple(verdicts), ())


def blank_receipt_verdict_tokens(text, source_path, rendered):
    """Blank each accepted verdict's `approve`/`block` token inside a rendered view.

    Only the structural token is replaced, and always with spaces of equal length, so
    every other offset survives and the reviewer identity, the finding, and any line
    wrapped beneath it stay under ordinary human-action detection. A verdict line the
    rendered view does not carry verbatim is left alone rather than blanked on a guess.
    """
    if RECEIPT_PATH_RE.fullmatch(source_path or "") is None:
        return rendered
    output = rendered
    cursor = 0
    for entry in parse_review_receipt(text).verdicts:
        found = output.find(entry.line, cursor)
        if found < 0:
            continue
        start = found + entry.token_start
        end = found + entry.token_end
        output = output[:start] + " " * (end - start) + output[end:]
        cursor = found + len(entry.line)
    return output
