#!/usr/bin/env python3
"""The one closed core-fit review receipt both gates read.

`memory/decisions/2026-08-04-review-receipt-parser-authorization.md` authorizes exactly
one grammar: one exact top-level `## Review verdicts` heading, one
`**Reviewed revision:** <full commit id>` field as its first line, then one or more
consecutive `- core-fit / <reviewer>: <approve|block> — <finding>` lines. Only blank
lines separate those elements, and the block ends at the first other nonblank line.

Two regexes, pointed in opposite directions. `VERDICT_RE` is the acceptor and stays
exact: widening it is how the withdrawn implementation grew. `LOOSE_VERDICT_RE` is the
rejector, and its only power is to refuse — widening it can never accept anything new,
only report more — so it is as permissive as it can be made. It ignores list markers,
quote markers, checkboxes, emphasis and code decoration, and any short run of non-letters
inside `core-fit` or before the slash. A verdict that misses only on its decoration or
its dash is reported rather than read as the ordinary prose that ends the receipt, which
is the fail-open the 2026-08-07 withdrawal decision named.

The claim this module can make, stated exactly: inside the one receipt section, any line
`LOOSE_VERDICT_RE` matches and `VERDICT_RE` does not is reported with its line number. It
cannot claim more. A line that reaches for the verdict shape but falls outside the
rejector still ends the block in silence — no slash at all (`- core-fit reviewer:
approve — …`), a letter fused to the token (`- core-fitt / …`), or a homoglyph inside the
word itself. Catching those needs character-similarity judgement, which that decision
forbids.

Five further routes out of the tally have nothing to do with this grammar, and all five
are prior design:

- a verdict inside a code fence or an HTML comment is blanked before any gate sees it,
  which `test_fenced_review_example_is_not_a_verdict` requires;
- a second verdict from an identity already recorded replaces the first, under the
  core-scope gate's latest-verdict-per-reviewer rule;
- a verdict whose reviewer matches the task's claimant is dropped by
  `check_core_scope.same_reviewer_as_claimant`;
- two different reviewer names whose word tokens are the same set collapse to one entry,
  because `check_core_scope.identity_key` is order-insensitive;
- a verdict outside the one `## Review verdicts` section is not in the receipt at all.

Both gates parse `semantic_text` of the same bytes, so the action gate never neutralizes
a receipt the core-scope gate would refuse. The converse does not hold, on purpose: the
action gate additionally requires the artifact path and a rendered line that still opens
with the verdict's own prefix, and when either fails it blanks nothing, leaving the
completed verdict visible as an ordinary action.
"""
import re
import unicodedata
from collections import namedtuple

from markdown_semantics import semantic_text

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
# The rejector. Every run below stops at an ASCII letter, and the literals that follow
# them begin with one, so no run can backtrack into another: the match stays linear.
LOOSE_VERDICT_RE = re.compile(
    r"[^A-Za-z\n]*core[^A-Za-z\n]{0,3}fit[^A-Za-z\n]*/", re.I
)
# The exemption belongs to the artifact the core-scope gate actually validates. Nothing
# validates a receipt in a worklog, so nothing there may claim one. Matched whole.
RECEIPT_PATH_RE = re.compile(
    r"tasks/\d_[a-z][a-z-]*/\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*/verification\.md"
)
# The same word tokens `check_core_scope.identity_key` counts. A reviewer with none of
# them parses as a verdict and then vanishes from the tally, so it is refused here.
REVIEWER_WORD_RE = re.compile(r"[^\W_]", re.UNICODE)
# One malformed receipt should read like a repair list, not a wall. The count of what is
# not shown is still reported, so nothing is hidden.
ERROR_LIMIT = 5

Verdict = namedtuple("Verdict", "reviewer verdict line token_start token_end")
ReceiptError = namedtuple("ReceiptError", "line message")
Receipt = namedtuple("Receipt", "revision verdicts errors")

MISSING_SECTION = "needs exactly one exact `## Review verdicts` heading"
MISSING_SECTION_FOUND = MISSING_SECTION + "; found {0}"
MISSING_REVISION = (
    "Review verdicts needs exactly one real `**Reviewed revision:** <commit>` field, "
    "as the first line of the receipt"
)
UNCANONICAL_VERDICT = (
    "Review verdicts rejects a core-fit line that is not "
    "`- core-fit / <reviewer>: <approve|block> — <finding>`: {0}"
)
STRANDED_VERDICT = (
    "Review verdicts has a core-fit line outside the contiguous receipt block, "
    "which ended at line {0}: {1}"
)
EMPTY_REVIEWER = (
    "Review verdicts rejects a core-fit line whose reviewer has no identity: {0}"
)
MORE_PROBLEMS = "Review verdicts has {0} further problem(s) not listed"


def _excerpt(line):
    trimmed = line.strip()
    return trimmed if len(trimmed) <= 80 else trimmed[:77] + "..."


class _Problems:
    """Collect receipt problems, deduplicated and capped, counting the rest."""

    def __init__(self):
        self.found = []
        self.suppressed = 0

    def add(self, line, message):
        if any(
            problem.line == line and problem.message == message
            for problem in self.found
        ):
            return
        if len(self.found) < ERROR_LIMIT:
            self.found.append(ReceiptError(line, message))
        else:
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
    structural = semantic_text(text or "")
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

    body_start = sections[0].start(1)
    body = sections[0].group(1)
    first_number = 1 + structural.count("\n", 0, body_start)
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
            verdicts.append(Verdict(
                reviewer,
                matched.group("verdict").lower(),
                line,
                matched.start("verdict"),
                matched.end("verdict"),
            ))
            continue
        if LOOSE_VERDICT_RE.match(line) is not None:
            problems.add(number, (
                UNCANONICAL_VERDICT.format(_excerpt(line)) if ended_at is None
                else STRANDED_VERDICT.format(ended_at[0], _excerpt(ended_at[1]))
            ))
        if ended_at is None:
            ended_at = (number, line)
    errors = problems.result()
    if errors:
        return Receipt(revision_match.group(1), (), errors)
    return Receipt(revision_match.group(1), tuple(verdicts), ())


def formatted_errors(receipt, display_path):
    """Render each problem with the file and line a reader can jump straight to."""
    return [
        f"{display_path}:{problem.line}: {problem.message}"
        if problem.line is not None else f"{display_path}: {problem.message}"
        for problem in receipt.errors
    ]


def blank_receipt_verdict_tokens(text, source_path, rendered):
    """Blank each accepted verdict's `approve`/`block` token inside a rendered view.

    The receipt is read from the structural view, because `rendered_human_text` is
    explicitly not evidence for headings or fields. Each token is then placed by finding
    the next rendered line that opens with that verdict's own prefix — the marker, the
    reviewer and the token itself — so an entity, autolink or inline tag later in the
    finding cannot move it. Only the token is replaced, always with spaces of equal
    length, so every other offset survives and the reviewer, the finding and any line
    wrapped beneath stay under ordinary human-action detection. A verdict whose prefix no
    rendered line carries is left alone rather than blanked on a guess.
    """
    if RECEIPT_PATH_RE.fullmatch(source_path or "") is None:
        return rendered
    receipt = parse_review_receipt(text)
    if not receipt.verdicts:
        return rendered
    lines = rendered.split("\n")
    index = 0
    for entry in receipt.verdicts:
        prefix = entry.line[:entry.token_end]
        while index < len(lines) and not lines[index].startswith(prefix):
            index += 1
        if index >= len(lines):
            break
        line = lines[index]
        lines[index] = (
            line[:entry.token_start]
            + " " * (entry.token_end - entry.token_start)
            + line[entry.token_end:]
        )
        index += 1
    return "\n".join(lines)
