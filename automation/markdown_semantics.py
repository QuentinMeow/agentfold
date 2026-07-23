"""Small CommonMark-aware helpers shared by repository gates.

Structural helpers expose only source that can carry real Markdown headings, fields,
and links, so examples inside fences or raw HTML cannot satisfy an invariant
accidentally. `rendered_human_text` is a separate detection-only view for prose that
raw HTML makes visible to a human; it must never supply structural evidence.
"""
from html import unescape
from html.parser import HTMLParser
import re
import unicodedata


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
    r"""(?<!!)(?<!\\)\[(?P<label>(?:\\.|[^\]\\])*)\](?<!\\)
        \([ \t]*(?:<(?P<angle>[^<>\r\n]*)>|(?P<bare>[^()\s]+))
        (?:[ \t]+(?:"(?:\\"|[^"])*"|'(?:\\'|[^'])*'|\((?:\\\)|[^)])*\)))?
        [ \t]*\)""",
    re.X,
)
HTML_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
HTML_BREAK_TAGS = {"br", "hr"}
P_IMPLICIT_CLOSE_START_TAGS = {
    "address", "article", "aside", "blockquote", "div", "dl", "fieldset",
    "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",
    "hgroup", "hr", "main", "menu", "nav", "ol", "p", "pre", "search",
    "section", "table", "ul",
}
NON_PROSE_HTML_TAGS = {
    "code", "head", "iframe", "kbd", "object", "pre", "samp", "script",
    "style", "template", "textarea",
}
HIDDEN_STYLE_RE = re.compile(
    r"(?:^|;)[ \t]*"
    r"(?:"
    r"display[ \t]*:[ \t]*none"
    r"|visibility[ \t]*:[ \t]*(?:hidden|collapse)"
    r"|content-visibility[ \t]*:[ \t]*hidden"
    r")"
    r"(?:[ \t]*![ \t]*important)?[ \t]*(?:;|$)",
    re.I,
)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def commonmark_lines(text):
    """Split only on CommonMark line endings; Python also splits on form feed."""
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    pieces = normalized.split("\n")
    lines = [piece + "\n" for piece in pieces[:-1]]
    if pieces[-1]:
        lines.append(pieces[-1])
    return lines


def strip_block_quote_markers(line, limit=None):
    """Return explicit block-quote depth and content after at most `limit` markers."""
    cursor = line
    depth = 0
    while limit is None or depth < limit:
        marker = re.match(r"^[ ]{0,3}>[ \t]?", cursor)
        if not marker:
            break
        cursor = cursor[marker.end():]
        depth += 1
    return depth, cursor


def _semantic_text(text, preserve_visible_html=False):
    """Blank fenced and raw-HTML blocks while preserving source line boundaries."""
    output = []
    fence_char = None
    fence_length = 0
    fence_quote_depth = 0
    html_end = None
    html_quote_depth = 0
    html_until_blank = False
    html_until_blank_quote_depth = 0
    inline_comment = False

    for line in commonmark_lines(text):
        candidate = line[:-1] if line.endswith("\n") else line
        blank = "\n" if line.endswith("\n") else ""
        quote_depth, syntax_candidate = strip_block_quote_markers(candidate)

        if fence_char:
            if quote_depth < fence_quote_depth and candidate.strip():
                fence_char = None
                fence_length = 0
                fence_quote_depth = 0
            else:
                _, closing_candidate = strip_block_quote_markers(
                    candidate, limit=fence_quote_depth
                )
                if re.fullmatch(
                    rf"[ ]{{0,3}}{re.escape(fence_char)}"
                    rf"{{{fence_length},}}[ \t]*",
                    closing_candidate,
                ):
                    fence_char = None
                    fence_length = 0
                    fence_quote_depth = 0
                output.append(blank)
                continue

        if html_end:
            if quote_depth < html_quote_depth and candidate.strip():
                html_end = None
                html_quote_depth = 0
            else:
                _, html_candidate = strip_block_quote_markers(
                    candidate, limit=html_quote_depth
                )
                if html_end.search(html_candidate):
                    html_end = None
                    html_quote_depth = 0
                output.append(line if preserve_visible_html else blank)
                continue

        if html_until_blank:
            if quote_depth < html_until_blank_quote_depth \
                    and candidate.strip():
                html_until_blank = False
                html_until_blank_quote_depth = 0
            else:
                _, html_candidate = strip_block_quote_markers(
                    candidate, limit=html_until_blank_quote_depth
                )
                if re.fullmatch(r"[ \t]*", html_candidate):
                    html_until_blank = False
                    html_until_blank_quote_depth = 0
                output.append(line if preserve_visible_html else blank)
                continue

        if inline_comment:
            comment_end = candidate.find("-->")
            if comment_end < 0:
                output.append(blank)
                continue
            candidate = " " * (comment_end + 3) + candidate[comment_end + 3:]
            inline_comment = False

        opening = FENCE_OPEN_RE.match(syntax_candidate)
        if opening and opening.group("fence").startswith("`"):
            info = syntax_candidate[opening.end("fence"):]
            if "`" in info:
                opening = None
        if opening:
            marker = opening.group("fence")
            fence_char = marker[0]
            fence_length = len(marker)
            fence_quote_depth = quote_depth
            output.append(blank)
            continue

        for start, end in (
            (RAW_HTML_TYPE1_START_RE, RAW_HTML_TYPE1_END_RE),
            (HTML_COMMENT_START_RE, re.compile(r"-->")),
            (HTML_PROCESSING_START_RE, re.compile(r"\?>")),
            (HTML_DECLARATION_START_RE, re.compile(r">")),
            (HTML_CDATA_START_RE, re.compile(r"\]\]>")),
        ):
            if start.match(syntax_candidate):
                html_end = None if end.search(syntax_candidate) else end
                html_quote_depth = quote_depth if html_end else 0
                output.append(line if preserve_visible_html else blank)
                break
        else:
            if RAW_HTML_TYPE6_START_RE.match(syntax_candidate) \
                    or RAW_HTML_TYPE7_START_RE.match(syntax_candidate):
                html_until_blank = True
                html_until_blank_quote_depth = quote_depth
                output.append(line if preserve_visible_html else blank)
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


def semantic_text(text):
    """Blank constructs that cannot supply structural Markdown evidence."""
    return _semantic_text(text)


def _line_endings_only(value):
    return "".join(
        character for character in value if character in "\r\n"
    )


class _RenderedHumanHTMLParser(HTMLParser):
    """Extract rendered prose without treating HTML markup as Markdown evidence."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
        self.stack = []

    @property
    def hidden(self):
        return bool(self.stack and self.stack[-1][1])

    @staticmethod
    def element_is_hidden(tag, attrs):
        values = {
            (name or "").casefold(): value
            for name, value in attrs
        }
        if tag in NON_PROSE_HTML_TAGS or "hidden" in values:
            return True
        aria_hidden = (values.get("aria-hidden") or "").strip().casefold()
        if aria_hidden in {"1", "true"}:
            return True
        style = CSS_COMMENT_RE.sub(" ", values.get("style") or "")
        style = re.sub(r"[ \t\r\n\f]+", " ", style)
        return bool(HIDDEN_STYLE_RE.search(style))

    def close_implicit_element(self, tag):
        targets = set()
        if tag in P_IMPLICIT_CLOSE_START_TAGS:
            targets.add("p")
        targets.update({
            "a": {"a"},
            "button": {"button"},
            "dd": {"dd", "dt"},
            "dt": {"dd", "dt"},
            "li": {"li"},
            "optgroup": {"optgroup", "option"},
            "option": {"option"},
            "tr": {"tr"},
            "td": {"td", "th"},
            "th": {"td", "th"},
        }.get(tag, set()))
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] in targets:
                del self.stack[index:]
                break

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        self.close_implicit_element(tag)
        raw = self.get_starttag_text() or ""
        self.output.append(_line_endings_only(raw))
        if tag in HTML_BREAK_TAGS:
            self.output.append(" ")
        hidden = self.hidden or self.element_is_hidden(tag, attrs)
        if tag not in HTML_VOID_TAGS:
            self.stack.append((tag, hidden))

    def handle_startendtag(self, tag, attrs):
        tag = tag.casefold()
        self.close_implicit_element(tag)
        raw = self.get_starttag_text() or ""
        self.output.append(_line_endings_only(raw))
        if tag in HTML_BREAK_TAGS:
            self.output.append(" ")
        if tag not in HTML_VOID_TAGS:
            hidden = self.hidden or self.element_is_hidden(tag, attrs)
            self.stack.append((tag, hidden))

    def handle_endtag(self, tag):
        tag = tag.casefold()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.output.append(
            _line_endings_only(data) if self.hidden else data
        )

    def append_character_reference(self, source):
        decoded = unescape(source).replace("\r", " ").replace("\n", " ")
        self.output.append(
            _line_endings_only(decoded) if self.hidden else decoded
        )

    def handle_entityref(self, name):
        self.append_character_reference(f"&{name};")

    def handle_charref(self, name):
        self.append_character_reference(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(_line_endings_only(f"<!--{data}-->"))

    def handle_decl(self, decl):
        self.output.append(_line_endings_only(f"<!{decl}>"))

    def handle_pi(self, data):
        self.output.append(_line_endings_only(f"<?{data}>"))

    def unknown_decl(self, data):
        self.output.append(_line_endings_only(f"<![{data}]>"))


def rendered_human_text(text):
    """Return prose a human can read, solely for detecting human-facing asks.

    Unlike `semantic_text`, this retains text rendered by ordinary raw HTML such as
    `<p>`. It still blanks code, comments, scripts, styles, templates, and elements
    hidden by deterministic HTML attributes. Callers must never use this view as
    evidence for Markdown headings, fields, or links.
    """
    parser = _RenderedHumanHTMLParser()
    parser.feed(_semantic_text(text, preserve_visible_html=True))
    parser.close()
    return "".join(
        " " if unicodedata.category(character) == "Zs" else character
        for character in "".join(parser.output)
    )


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


def markdown_links(text):
    """Return visible CommonMark inline-link `(label, destination)` pairs."""
    clean = strip_indented_code(strip_inline_code(semantic_text(text)))
    return [
        (
            matched.group("label"),
            matched.group("angle")
            if matched.group("angle") is not None
            else matched.group("bare"),
        )
        for matched in MARKDOWN_LINK_RE.finditer(clean)
    ]
