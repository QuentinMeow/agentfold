#!/usr/bin/env python3
"""The one closed core-fit review receipt both gates read.

`memory/decisions/2026-08-04-review-receipt-parser-authorization.md` authorizes exactly
one grammar: one real top-level `## Review verdicts` heading, one
`**Reviewed revision:** <full commit id>` field as its first line, then one or more
consecutive `- core-fit / <reviewer>: <approve|block> — <finding>` lines. Only blank
lines separate those elements, and the block ends at the first other nonblank line.

`memory/decisions/2026-08-07-withdraw-the-first-review-receipt-implementation.md` adds
the rule this module exists to keep: nothing inside the receipt is ever skipped. The
finding is any nonempty text, so a real sentence is never refused; a line that reaches
for the verdict shape and misses, or a canonical verdict stranded outside the block,
refuses the whole receipt with a reported error. A verdict can therefore never leave the
tally silently, which is the fail-open that withdrew the first implementation.

Callers pass the text view they already scan — `semantic_text` for the core-scope gate,
`rendered_human_text` for the action gate — and token spans come back measured in that
same view, so the action gate can blank the structural token and nothing else. Reviewer
identities and findings stay in the scanned text on purpose.
"""
import re
from collections import namedtuple

SECTION_RE = re.compile(
    r"^## Review verdicts(?:[ \t][^\r\n]*)?\r?\n(.*?)(?=^##(?:[ \t]|\r?$)|\Z)",
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
# Anything that reaches for a verdict and misses. It is deliberately looser than
# VERDICT_RE so a near-miss inside the receipt is reported rather than read as the
# ordinary prose that closes the block.
NEAR_VERDICT_RE = re.compile(r"[ \t]*[-*+][ \t]*core-fit\b", re.I)

Verdict = namedtuple("Verdict", "reviewer verdict finding token_start token_end")
Receipt = namedtuple("Receipt", "revision verdicts errors")

MISSING_SECTION = "verification.md needs exactly one real `## Review verdicts` section"
MISSING_REVISION = (
    "Review verdicts needs exactly one real `**Reviewed revision:** <commit>` field, "
    "as the first line of the receipt"
)
MALFORMED_VERDICT = (
    "Review verdicts rejects a core-fit line that is not "
    "`- core-fit / <reviewer>: <approve|block> — <finding>`: {0}"
)
STRANDED_VERDICT = (
    "Review verdicts has a core-fit verdict outside the contiguous receipt block: {0}"
)


def _excerpt(line):
    trimmed = line.strip()
    return trimmed if len(trimmed) <= 80 else trimmed[:77] + "..."


def _lines(text, base):
    """Yield (offset in the caller's view, line without its ending) pairs."""
    start = base
    for piece in text.split("\n"):
        yield start, piece.rstrip("\r")
        start += len(piece) + 1


def parse_review_receipt(view):
    """Return the single receipt in one text view, or the errors that refuse it."""
    text = view or ""
    sections = list(SECTION_RE.finditer(text))
    if len(sections) != 1:
        return Receipt(None, (), (MISSING_SECTION,))
    body_start, body_end = sections[0].span(1)
    body = text[body_start:body_end]
    lines = list(_lines(body, body_start))
    index = 0
    while index < len(lines) and not lines[index][1].strip():
        index += 1
    opening = lines[index][1] if index < len(lines) else ""
    revision_match = REVISION_RE.fullmatch(opening)
    if revision_match is None or len(REVISION_FIELD_RE.findall(body)) != 1:
        return Receipt(None, (), (MISSING_REVISION,))
    revision = revision_match.group(1)

    errors = []
    verdicts = []
    index += 1
    while index < len(lines):
        offset, line = lines[index]
        if not line.strip():
            index += 1
            continue
        matched = VERDICT_RE.fullmatch(line)
        if matched is not None:
            verdicts.append(Verdict(
                matched.group("reviewer"),
                matched.group("verdict").lower(),
                matched.group("finding"),
                offset + matched.start("verdict"),
                offset + matched.end("verdict"),
            ))
            index += 1
            continue
        if NEAR_VERDICT_RE.match(line) is not None:
            errors.append(MALFORMED_VERDICT.format(_excerpt(line)))
        break
    for _offset, line in lines[index:]:
        if VERDICT_RE.fullmatch(line) is not None:
            errors.append(STRANDED_VERDICT.format(_excerpt(line)))
    if errors:
        return Receipt(revision, (), tuple(errors))
    return Receipt(revision, tuple(verdicts), ())


def accepted_verdict_token_spans(view):
    """Return the `approve`/`block` spans a gate may blank, empty unless whole.

    Only the structural token is offered. The reviewer identity and the finding stay
    where they are, so ordinary human-action detection still reads them.
    """
    receipt = parse_review_receipt(view)
    if receipt.errors:
        return ()
    return tuple(
        (verdict.token_start, verdict.token_end) for verdict in receipt.verdicts
    )


def blank_spans(text, spans):
    """Overwrite each span with spaces, leaving every other offset untouched."""
    blanked = text
    for start, end in spans:
        blanked = blanked[:start] + " " * (end - start) + blanked[end:]
    return blanked
