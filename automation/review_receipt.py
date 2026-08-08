#!/usr/bin/env python3
"""The one closed core-fit review receipt both gates read.

`memory/decisions/2026-08-04-review-receipt-parser-authorization.md` authorizes exactly
one grammar: one exact top-level `## Review verdicts` heading, one
`**Reviewed revision:** <full commit id>` field as its first line, then one or more
consecutive `- core-fit / <reviewer>: <approve|block> — <finding>` lines. Only blank
lines separate those elements, and the block ends at the first other nonblank line.

Two halves, pointed in opposite directions, and the direction is the whole design.
`VERDICT_RE` is the acceptor and stays exact — widening an acceptor is how the withdrawn
implementation grew. `reaches_for_verdict`, built on `LOOSE_TOKEN_RE`, is the rejector,
and a rejector can only refuse: whatever it newly matches becomes a reported error, never
an accepted verdict. So it is kept loose on purpose, searched anywhere in the line rather
than anchored, tolerant of any decoration around and inside `core-fit`, of any dash, and
of slash-like characters beyond ASCII. It is applied twice — once to the structural view
and once to the section's raw source, because the structural view blanks fenced,
commented, indented and HTML-wrapped lines before any rejector could see them.

**What this module refuses, as a rule rather than a list.** Inside the one receipt
section, a line whose structural *or* raw form the rejector matches, and which the
acceptor does not accept, refuses the whole receipt. A line the rejector does not match
still ends the block silently; the rejector is loose but it is a pattern, not a judgement
about what a writer meant, and the shapes past it are those needing character-similarity
reasoning that
`memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md`
forbids, plus anything else a pattern over `core`/`fit`/slash cannot see.

**What leaves the tally without an error, as rules.** A verdict the receipt never
contained — outside the one section, or on a line the rejector cannot match — is not in
the receipt. A verdict the core-scope gate declines to count — one whose reviewer it
cannot tell apart from the claimant or from another reviewer under
`check_core_scope.identity_key`, or one it replaces under its latest-verdict-per-reviewer
rule — leaves the tally by that gate's rules, not this parser's. Problems past
`ERROR_LIMIT` are counted rather than listed, so a receipt with many of them reports how
many it did not name.

**Refusal-only is not the same as safe.** Both rejector passes can only add an error,
never accept a verdict, so widening either is free. That argument covers what they do —
it does not cover what they fail to do. Declining to refuse is permission: every line
neither pass matches ends the block in silence, so a pass that returns early, a bound
that clips a run, or a view that dropped the line before the pass ran are all fail-open,
whatever the direction of the pass itself.

**What the two gates share, and what they do not.** Both call this parser, so it reaches
the same verdict for whatever text each hands it; everything after that is each gate's
own. They do not necessarily hand it the same bytes — the core-scope gate reads the file
through Git with universal newlines, the action gate decodes it without — which is why
line correspondence here is derived from `commonmark_lines` rather than from a raw split.
The core-scope gate then applies claimant, identity and majority rules this module never
sees, and the action gate additionally requires the artifact path and a rendered line
still carrying the verdict, and blanks nothing when either fails.
"""
import re
import unicodedata
from collections import namedtuple

from markdown_semantics import commonmark_lines, semantic_text

SECTION_RE = re.compile(
    r"^## Review verdicts[ \t]*\r?\n(.*?)(?=^##(?:[ \t]|\r?$)|\Z)",
    re.M | re.S,
)
# Only to explain a refusal: the spelling a writer used when no exact heading matched.
NEAR_SECTION_RE = re.compile(r"^#{1,6}[ \t]+Review verdicts[^\r\n]*$", re.M | re.I)
FULL_COMMIT_PATTERN = r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})"
REVISION_RE = re.compile(
    rf"^\*\*Reviewed revision:\*\*[ \t]*({FULL_COMMIT_PATTERN})[ \t]*$", re.M
)
REVISION_FIELD_RE = re.compile(r"^\*\*Reviewed revision:\*\*", re.M)
# The acceptor. Exact, and deliberately never widened.
VERDICT_RE = re.compile(
    r"- core-fit / (?P<reviewer>[^:\r\n]+):[ \t]*(?P<verdict>approve|block)"
    r"[ \t]+—[ \t]+(?P<finding>.+)$",
    re.I,
)
# The rejector. Neither of its two runs is bounded — the one inside `core…fit` or the one
# before the slash — because a bound on a rejector is a coverage decision, not an
# optimization: an earlier revision capped both at sixteen characters, and seventeen
# zero-width spaces then produced a line visually identical to a canonical verdict that
# neither half would look at. Removing the bounds costs speed rather than saving it, on
# some shapes by more than double; the measurement is in this task's verification record.
# The pattern locates `core…fit`; the slash is then found by plain string search over the
# rest of the line, which cannot backtrack.
SLASH_CHARACTERS = "/／∕⁄"
LOOSE_TOKEN_RE = re.compile(r"core[^A-Za-z\n]*fit", re.I)
# The exemption belongs to the artifact the core-scope gate actually validates. Nothing
# validates a receipt in a worklog, so nothing there may claim one. Matched whole.
RECEIPT_PATH_RE = re.compile(
    r"tasks/\d_[a-z][a-z-]*/\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*/verification\.md"
)
# The same word tokens `check_core_scope.identity_key` counts. A reviewer with none of
# them parses as a verdict and then vanishes from the tally, so it is refused here.
REVIEWER_WORD_RE = re.compile(r"[^\W_]", re.UNICODE)
# One malformed receipt should read like a repair list, not a wall. What is not shown is
# still counted, so the reader knows the list is partial.
ERROR_LIMIT = 5

Verdict = namedtuple("Verdict", "reviewer verdict line number token_start token_end")
ReceiptError = namedtuple("ReceiptError", "line message")
Receipt = namedtuple("Receipt", "revision verdicts errors")

MISSING_SECTION = "needs exactly one exact `## Review verdicts` heading"
MISSING_SECTION_FOUND = MISSING_SECTION + "; found {0}"
MISSING_REVISION = (
    "Review verdicts needs exactly one real `**Reviewed revision:** <commit>` field, "
    "as the first line of the receipt"
)
UNCANONICAL_VERDICT = (
    "Review verdicts refuses a line inside the receipt that reads as a core-fit "
    "verdict but is not one; write it as `- core-fit / <reviewer>: <approve|block> "
    "— <finding>` or move it out of the receipt: {0}"
)
STRANDED_VERDICT = (
    "Review verdicts has a core-fit line outside the contiguous receipt block, "
    "which ended at line {0}: {1}"
)
HIDDEN_VERDICT = (
    "Review verdicts has a core-fit line the structural view does not carry — "
    "indented, fenced, commented, or wrapped in HTML: {0}"
)
EMPTY_REVIEWER = (
    "Review verdicts rejects a core-fit line whose reviewer has no identity: {0}"
)
MORE_PROBLEMS = "Review verdicts has {0} further problem(s) not listed"


def _excerpt(line):
    trimmed = line.strip()
    return trimmed if len(trimmed) <= 80 else trimmed[:77] + "..."


def reaches_for_verdict(line):
    """Whether one line reaches for a core-fit verdict, however it is decorated.

    The rejector, and the only place a line is judged near-miss. Neither half is bounded.
    `core…fit` is located with a pattern, which does backtrack: the run consumes the
    maximal span of non-letters and then retries every shorter one when `fit` does not
    follow, measured at about 2.2x on that failing path. The slash is then looked for in
    the remainder by plain string search, and that half does not backtrack. Cost stays
    linear in the line either way — about 35 ns per character across three orders of
    magnitude — because the run cannot cross a letter and so cannot span the whole line.

    Checking the first `core…fit` is enough: its remainder contains every slash any later
    one could claim.
    """
    matched = LOOSE_TOKEN_RE.search(line)
    if matched is None:
        return False
    remainder = line[matched.end():]
    return any(character in remainder for character in SLASH_CHARACTERS)


class _Problems:
    """Collect receipt problems, keeping the earliest, counting what the cap leaves out.

    Problems arrive in two passes over the section — the structural lines first, then the
    raw lines the structural view dropped — so visit order is not line order. Keeping
    whatever arrived first would report the later half of a broken receipt and hide its
    beginning, which is where a reader starts.
    """

    def __init__(self):
        self.found = []
        self.suppressed = 0
        self.lines = set()

    def add(self, line, message):
        self.lines.add(line)
        self.found.append(ReceiptError(line, message))
        self.found.sort(key=lambda problem: problem.line)
        if len(self.found) > ERROR_LIMIT:
            self.found.pop()
            self.suppressed += 1

    def result(self):
        if not self.suppressed:
            return tuple(self.found)
        return tuple(self.found) + (
            ReceiptError(None, MORE_PROBLEMS.format(self.suppressed)),
        )


def _numbered_lines(text, first_number):
    """Yield (1-based document line number, line without its ending) pairs."""
    for offset, piece in enumerate(text.split("\n")):
        yield first_number + offset, piece.rstrip("\r")


def parse_review_receipt(text):
    """Return the single receipt in one artifact, or the problems that refuse it."""
    source = text or ""
    structural = semantic_text(source)
    sections = list(SECTION_RE.finditer(structural))
    if len(sections) != 1:
        near = NEAR_SECTION_RE.search(structural)
        if len(sections) > 1:
            message = MISSING_SECTION_FOUND.format(f"{len(sections)} of them")
            line = 1 + structural.count("\n", 0, sections[1].start())
        elif near is not None:
            message = MISSING_SECTION_FOUND.format(f"`{near.group(0).strip()}`")
            line = 1 + structural.count("\n", 0, near.start())
        else:
            message, line = MISSING_SECTION, None
        return Receipt(None, (), (ReceiptError(line, "verification.md " + message),))

    body = sections[0].group(1)
    first_number = 1 + structural.count("\n", 0, sections[0].start(1))
    lines = list(_numbered_lines(body, first_number))
    index = 0
    while index < len(lines) and not lines[index][1].strip():
        index += 1
    opening_number, opening = lines[index] if index < len(lines) else (first_number, "")
    revision_match = REVISION_RE.fullmatch(opening)
    if revision_match is None or len(REVISION_FIELD_RE.findall(body)) != 1:
        return Receipt(None, (), (ReceiptError(opening_number, MISSING_REVISION),))

    problems = _Problems()
    verdicts = []
    accepted = set()
    ended_at = None
    for number, line in lines[index + 1:]:
        if not line.strip():
            continue
        matched = VERDICT_RE.fullmatch(line) if ended_at is None else None
        if matched is not None:
            reviewer = matched.group("reviewer")
            if REVIEWER_WORD_RE.search(unicodedata.normalize("NFKC", reviewer)) is None:
                problems.add(number, EMPTY_REVIEWER.format(_excerpt(line)))
                continue
            accepted.add(number)
            verdicts.append(Verdict(
                reviewer,
                matched.group("verdict").lower(),
                line,
                number,
                matched.start("verdict"),
                matched.end("verdict"),
            ))
            continue
        if reaches_for_verdict(line):
            problems.add(number, (
                UNCANONICAL_VERDICT.format(_excerpt(line)) if ended_at is None
                else STRANDED_VERDICT.format(ended_at, _excerpt(line))
            ))
        if ended_at is None:
            ended_at = number

    _refuse_hidden_verdicts(source, first_number, len(lines), accepted, problems)
    errors = problems.result()
    if errors:
        return Receipt(revision_match.group(1), (), errors)
    return Receipt(revision_match.group(1), tuple(verdicts), ())


def _refuse_hidden_verdicts(source, first, count, accepted, problems):
    """Refuse a verdict the structural view dropped before any rejector saw it.

    `semantic_text` blanks fenced, commented, indented and HTML-wrapped lines, so a
    verdict written that way reaches neither the acceptor nor the rejector and would end
    the block in silence. Reading the section's own raw lines is refusal-only: it can add
    an error, never a verdict.

    The raw lines come from `commonmark_lines`, which is what `semantic_text` itself
    splits on, so the two agree line for line by construction rather than by coincidence.
    Splitting the source on `\\n` instead did not: one bare CR anywhere in the document
    shifted every later line, and an earlier revision responded by declining the whole
    scan, which turned one stray byte into permission to hide a verdict.
    """
    raw_lines = [line.rstrip("\n") for line in commonmark_lines(source)]
    for number in range(first, min(first + count, len(raw_lines) + 1)):
        if number in accepted or number in problems.lines:
            continue
        raw = raw_lines[number - 1]
        if raw.strip() and reaches_for_verdict(raw):
            problems.add(number, HIDDEN_VERDICT.format(_excerpt(raw)))


def formatted_errors(receipt, display_path):
    """Render each problem with the file and line a reader can jump straight to."""
    return [
        f"{display_path}:{problem.line}: {problem.message}"
        if problem.line is not None else f"{display_path}: {problem.message}"
        for problem in receipt.errors
    ]


def carries_verdict_prefix(line, entry):
    """Report whether one rendered line opens with exactly this verdict's prefix.

    The boundary test is what stops `approve` from matching a line whose reviewer voted
    `approved`: without it the blanking would erase seven characters of an unrelated
    word on an unrelated line.
    """
    prefix = entry.line[:entry.token_end]
    return (
        line.startswith(prefix)
        and not line[entry.token_end:entry.token_end + 1].isalnum()
    )


def _placement_index(lines, entry, first, last):
    """Find the rendered line one verdict occupies, never leaving the receipt.

    Neither step assumes the two views number lines alike, and they do not always: an
    unterminated HTML comment is one shape where they diverge. The first step tries the
    line the parser recorded and takes it only if that rendered line is the verdict
    character for character, so a shifted view simply fails the test. The second exists
    for a rendered view that rewrote the line, and it is bounded to the receipt's own
    verdict lines, so a lookalike elsewhere in the document can never be blanked in its
    place — which is the bug that bound is there to prevent, not a bound for speed.
    """
    exact = entry.number - 1
    if 0 <= exact < len(lines) and lines[exact].rstrip("\r") == entry.line:
        return exact
    for index in range(max(first - 1, 0), min(last, len(lines))):
        if carries_verdict_prefix(lines[index], entry):
            return index
    return None


def blank_receipt_verdict_tokens(text, source_path, rendered):
    """Blank each accepted verdict's `approve`/`block` token inside a rendered view.

    The receipt is read from the structural view, because `rendered_human_text` is
    explicitly not evidence for headings or fields. Only the token is replaced, always
    with spaces of equal length, so every other offset survives and the reviewer, the
    finding and any line wrapped beneath stay under ordinary human-action detection. A
    verdict whose line the rendered view no longer carries is left alone rather than
    blanked on a guess.
    """
    if RECEIPT_PATH_RE.fullmatch(source_path or "") is None:
        return rendered
    verdicts = parse_review_receipt(text).verdicts
    if not verdicts:
        return rendered
    lines = rendered.split("\n")
    first, last = verdicts[0].number, verdicts[-1].number
    for entry in verdicts:
        index = _placement_index(lines, entry, first, last)
        if index is None:
            continue
        line = lines[index]
        lines[index] = (
            line[:entry.token_start]
            + " " * (entry.token_end - entry.token_start)
            + line[entry.token_end:]
        )
    return "\n".join(lines)
