"""Small CommonMark-aware helpers shared by repository gates.

These helpers do not try to render Markdown. They expose only source that can carry
real headings, fields, and links, so examples inside fences or raw HTML cannot satisfy
an invariant accidentally.
"""
import re


FENCE_OPEN_RE = re.compile(r"^[ ]{0,3}(?P<fence>`{3,}|~{3,}).*$")
RAW_HTML_TYPE1_TAGS = "pre|script|style|textarea"
RAW_HTML_TYPE1_START_RE = re.compile(
    rf"^[ ]{{0,3}}<(?:{RAW_HTML_TYPE1_TAGS})(?=[ \t>]|$)", re.I
)
RAW_HTML_TYPE1_END_RE = re.compile(rf"</(?:{RAW_HTML_TYPE1_TAGS})>", re.I)
HTML_COMMENT_START_RE = re.compile(r"^[ ]{0,3}<!--")
HTML_PROCESSING_START_RE = re.compile(r"^[ ]{0,3}<\?")
HTML_DECLARATION_START_RE = re.compile(r"^[ ]{0,3}<![A-Za-z]")
HTML_CDATA_START_RE = re.compile(r"^[ ]{0,3}<!\[CDATA\[")
RAW_HTML_TYPE6_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|"
    "dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|"
    "frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|legend|li|link|main|"
    "menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    "table|tbody|td|tfoot|th|thead|title|tr|track|ul"
)
RAW_HTML_TYPE6_START_RE = re.compile(
    rf"^[ ]{{0,3}}</?(?:{RAW_HTML_TYPE6_TAGS})(?=[ \t]|$|/?>)", re.I
)
RAW_HTML_TYPE7_START_RE = re.compile(
    r"^[ ]{0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[\s>/]).*>[ \t]*$", re.I
)
MARKDOWN_LINK_RE = re.compile(
    r"""(?<!!)(?<!\\)\[(?:\\.|[^\]\\])*\](?<!\\)
        \([ \t]*(?:<(?P<angle>[^<>\r\n]*)>|(?P<bare>[^()\s]+))
        (?:[ \t]+(?:"(?:\\"|[^"])*"|'(?:\\'|[^'])*'|\((?:\\\)|[^)])*\)))?
        [ \t]*\)""",
    re.X,
)


def commonmark_lines(text):
    """Split only on CommonMark line endings; Python also splits on form feed."""
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    pieces = normalized.split("\n")
    lines = [piece + "\n" for piece in pieces[:-1]]
    if pieces[-1]:
        lines.append(pieces[-1])
    return lines


def semantic_text(text):
    """Blank fenced and raw-HTML blocks while preserving source line boundaries."""
    output = []
    fence_char = None
    fence_length = 0
    html_end = None
    html_until_blank = False
    inline_comment = False

    for line in commonmark_lines(text):
        candidate = line[:-1] if line.endswith("\n") else line
        blank = "\n" if line.endswith("\n") else ""

        if fence_char:
            if re.fullmatch(
                rf"[ ]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*",
                candidate,
            ):
                fence_char = None
                fence_length = 0
            output.append(blank)
            continue

        if html_end:
            if html_end.search(candidate):
                html_end = None
            output.append(blank)
            continue

        if html_until_blank:
            if re.fullmatch(r"[ \t]*", candidate):
                html_until_blank = False
            output.append(blank)
            continue

        if inline_comment:
            comment_end = candidate.find("-->")
            if comment_end < 0:
                output.append(blank)
                continue
            candidate = " " * (comment_end + 3) + candidate[comment_end + 3:]
            inline_comment = False

        opening = FENCE_OPEN_RE.match(candidate)
        if opening and opening.group("fence").startswith("`"):
            info = candidate[opening.end("fence"):]
            if "`" in info:
                opening = None
        if opening:
            marker = opening.group("fence")
            fence_char = marker[0]
            fence_length = len(marker)
            output.append(blank)
            continue

        for start, end in (
            (RAW_HTML_TYPE1_START_RE, RAW_HTML_TYPE1_END_RE),
            (HTML_COMMENT_START_RE, re.compile(r"-->")),
            (HTML_PROCESSING_START_RE, re.compile(r"\?>")),
            (HTML_DECLARATION_START_RE, re.compile(r">")),
            (HTML_CDATA_START_RE, re.compile(r"\]\]>")),
        ):
            if start.match(candidate):
                html_end = None if end.search(candidate) else end
                output.append(blank)
                break
        else:
            if RAW_HTML_TYPE6_START_RE.match(candidate) \
                    or RAW_HTML_TYPE7_START_RE.match(candidate):
                html_until_blank = True
                output.append(blank)
            else:
                while "<!--" in candidate:
                    comment_start = candidate.find("<!--")
                    comment_end = candidate.find("-->", comment_start + 4)
                    if comment_end < 0:
                        candidate = candidate[:comment_start]
                        inline_comment = True
                        break
                    candidate = (
                        candidate[:comment_start]
                        + " " * (comment_end + 3 - comment_start)
                        + candidate[comment_end + 3:]
                    )
                output.append(candidate + blank)

    return "".join(output)


def strip_inline_code(text):
    """Blank CommonMark code spans while preserving line boundaries."""
    output = list(text or "")
    index = 0
    while index < len(output):
        if output[index] != "`":
            index += 1
            continue
        opening = index
        while index < len(output) and output[index] == "`":
            index += 1
        width = index - opening
        cursor = index
        closing = None
        while cursor < len(output):
            if output[cursor] != "`":
                cursor += 1
                continue
            run_start = cursor
            while cursor < len(output) and output[cursor] == "`":
                cursor += 1
            if cursor - run_start == width:
                closing = cursor
                break
        if closing is None:
            continue
        for position in range(opening, closing):
            if output[position] not in ("\n", "\r"):
                output[position] = " "
        index = closing
    return "".join(output)


def strip_indented_code(text):
    """Blank simple four-space/tab indented code lines."""
    output = []
    for line in commonmark_lines(text):
        candidate = line[:-1] if line.endswith("\n") else line
        blank = "\n" if line.endswith("\n") else ""
        if candidate.startswith("    ") or candidate.startswith("\t"):
            output.append(blank)
        else:
            output.append(line)
    return "".join(output)


def markdown_link_destinations(text):
    """Return visible CommonMark inline-link destinations.

    The angle-bracket form intentionally supports repository paths containing spaces.
    """
    clean = strip_indented_code(strip_inline_code(semantic_text(text)))
    return [
        matched.group("angle")
        if matched.group("angle") is not None
        else matched.group("bare")
        for matched in MARKDOWN_LINK_RE.finditer(clean)
    ]
