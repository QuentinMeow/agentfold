"""Small CommonMark-aware helpers shared by repository gates.

Structural helpers expose only source that can carry real Markdown headings, fields,
and links, so examples inside fences or raw HTML cannot satisfy an invariant
accidentally. `rendered_human_text` is a separate detection-only view for prose that
raw HTML makes visible to a human; it must never supply structural evidence.
"""
from html import unescape
from html.parser import HTMLParser
import functools
import re
import unicodedata

# These views are pure functions of their exact source text, so the same document
# analysed again — by another check, or by the same check at another Git revision
# that did not change the file — has the same answer. Repository gates re-derive
# them thousands of times per run, so each is memoised on its input text. The
# bound keeps a long history walk from retaining every document it ever read.
_TEXT_VIEW_CACHE_SIZE = 512


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
# Block starts that end an open paragraph, matched against a line whose leading
# indentation has already been consumed. A paragraph matters here because an indented
# code block cannot interrupt one: after a paragraph line, four more spaces are wrapped
# prose, not code.
ATX_HEADING_RE = re.compile(r"#{1,6}(?:[ \t]|$)")
THEMATIC_BREAK_RE = re.compile(
    r"(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})"
)
SETEXT_UNDERLINE_RE = re.compile(r"(?:=+|-+)[ \t]*")
LIST_MARKER_RE = re.compile(
    r"(?P<marker>[-+*]|(?P<number>\d{1,9})[.)])(?=[ \t]|$)"
)
# CommonMark measures an indented code block four columns past the content column of
# whatever container it sits in, and uses the same four columns as the widest run of
# spaces that can still separate a list marker from its own content.
INDENTED_CODE_MARGIN = 4
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
    "style", "template",
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
RAW_HTML_TOKEN_RE = re.compile(
    r"<(?:!--|!\[CDATA\[|\?|![A-Za-z]|/?[A-Za-z][A-Za-z0-9-]*(?=[\s/>]))",
    re.I,
)
DEFAULT_IGNORABLE_NONFORMAT_RANGES = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180D),
    (0x180F, 0x180F),
    (0x2065, 0x2065),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0xE0000, 0xE0FFF),
)


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


@functools.lru_cache(maxsize=_TEXT_VIEW_CACHE_SIZE)
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


@functools.lru_cache(maxsize=_TEXT_VIEW_CACHE_SIZE)
def semantic_text(text):
    """Blank constructs that cannot supply structural Markdown evidence.

    Indented code blocks are blanked too, via `strip_indented_code`, for the same
    reason fences and raw HTML are: an example path or field inside one must not
    satisfy a structural check. This runs after fence/HTML blanking, so a fenced block
    nested in a list item — whose content lines are already blank by then — is
    unaffected. What `strip_indented_code` changes is only what CommonMark parses as an
    indented code block, which is narrower than "the line starts with four spaces":
    that width has to be four columns past the enclosing list item's content column,
    and it cannot interrupt a paragraph. Prose in a wrapped paragraph or under a list
    item stays visible, because a human reads it.
    """
    return strip_indented_code(_semantic_text(text))


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
        if tag in NON_PROSE_HTML_TAGS or "hidden" in values \
                or (
                    tag == "input"
                    and (values.get("type") or "").strip().casefold() == "hidden"
                ):
            return True
        aria_hidden = (values.get("aria-hidden") or "").strip().casefold()
        if aria_hidden in {"1", "true"}:
            return True
        style = CSS_COMMENT_RE.sub(" ", values.get("style") or "")
        style = re.sub(r"[ \t\r\n\f]+", " ", style)
        return bool(HIDDEN_STYLE_RE.search(style))

    @staticmethod
    def visible_attribute_text(tag, attrs):
        """Return conservative text exposed visually or accessibly by a tag."""
        values = {
            (name or "").casefold(): value
            for name, value in attrs
        }
        names = ("alt", "aria-label", "title")
        if tag in {"input", "textarea"}:
            names = (*names, "placeholder")
        if tag == "input":
            names = (*names, "value")
        visible = []
        for name in names:
            value = values.get(name)
            if isinstance(value, str) and value.strip():
                visible.append(value.strip())
        return " ".join(visible)

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

    def append_visible_attribute_text(self, value):
        if not value:
            return
        previous = next(
            (piece[-1] for piece in reversed(self.output) if piece),
            "",
        )
        if previous and not previous.isspace():
            self.output.append(" ")
        self.output.extend((value, " "))

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        self.close_implicit_element(tag)
        raw = self.get_starttag_text() or ""
        self.output.append(_line_endings_only(raw))
        if tag in HTML_BREAK_TAGS:
            self.output.append(" ")
        hidden = self.hidden or self.element_is_hidden(tag, attrs)
        attribute_text = self.visible_attribute_text(tag, attrs)
        if attribute_text and not hidden:
            self.append_visible_attribute_text(attribute_text)
        if tag not in HTML_VOID_TAGS:
            self.stack.append((tag, hidden))

    def handle_startendtag(self, tag, attrs):
        tag = tag.casefold()
        self.close_implicit_element(tag)
        raw = self.get_starttag_text() or ""
        self.output.append(_line_endings_only(raw))
        if tag in HTML_BREAK_TAGS:
            self.output.append(" ")
        hidden = self.hidden or self.element_is_hidden(tag, attrs)
        attribute_text = self.visible_attribute_text(tag, attrs)
        if attribute_text and not hidden:
            self.append_visible_attribute_text(attribute_text)
        if tag not in HTML_VOID_TAGS:
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


@functools.lru_cache(maxsize=_TEXT_VIEW_CACHE_SIZE)
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


@functools.lru_cache(maxsize=_TEXT_VIEW_CACHE_SIZE)
def strip_default_ignorable_characters(text):
    """Remove invisible Unicode controls from an already isolated prose view.

    Format controls and the non-format characters in Unicode's
    Default_Ignorable_Code_Point set can split an otherwise visible command word.
    Callers must first remove Markdown destinations and code so this detection-only
    normalization cannot change structural evidence or literal examples.
    """
    output = []
    normalized = unicodedata.normalize("NFKC", text or "")
    for character in normalized:
        codepoint = ord(character)
        if unicodedata.category(character) == "Cf":
            continue
        if any(
                start <= codepoint <= end
                for start, end in DEFAULT_IGNORABLE_NONFORMAT_RANGES):
            continue
        output.append(character)
    return "".join(output)


def inline_code_spans(text):
    """Return the source ranges occupied by closed CommonMark code spans."""
    source = text or ""
    spans = []
    index = 0
    while index < len(source):
        if source[index] != "`":
            index += 1
            continue
        opening = index
        while index < len(source) and source[index] == "`":
            index += 1
        width = index - opening
        cursor = index
        closing = None
        while cursor < len(source):
            if source[cursor] != "`":
                cursor += 1
                continue
            run_start = cursor
            while cursor < len(source) and source[cursor] == "`":
                cursor += 1
            if cursor - run_start == width:
                closing = cursor
                break
        if closing is None:
            continue
        spans.append((opening, closing))
        index = closing
    return spans


def strip_inline_code(text):
    """Blank CommonMark code spans while preserving line boundaries."""
    output = list(text or "")
    for opening, closing in inline_code_spans(text):
        for position in range(opening, closing):
            if output[position] not in ("\n", "\r"):
                output[position] = " "
    return "".join(output)


def render_inline_code(text):
    """Remove code-span delimiters while retaining their rendered text."""
    source = text or ""
    output = []
    cursor = 0
    for opening, closing in inline_code_spans(source):
        width = 1
        while opening + width < closing \
                and source[opening + width] == "`":
            width += 1
        content = source[opening + width:closing - width]
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        content = content.replace("\n", " ")
        if content.startswith(" ") and content.endswith(" ") \
                and content.strip(" "):
            content = content[1:-1]
        output.extend((source[cursor:opening], content))
        cursor = closing
    output.append(source[cursor:])
    return "".join(output)


def contains_raw_html(text):
    """Conservatively detect raw HTML outside fenced and inline code.

    Callers that require a closed Markdown shape can fail closed on this signal
    instead of trying to reproduce a browser's handling of arbitrary tags and
    attributes.
    """
    clean = strip_inline_code(
        _semantic_text(text or "", preserve_visible_html=True)
    )
    return bool(RAW_HTML_TOKEN_RE.search(clean))


def split_indentation(value):
    """Return leading indentation in CommonMark columns and the rest of the line."""
    width = 0
    index = 0
    for character in value:
        if character == " ":
            width += 1
        elif character == "\t":
            width += INDENTED_CODE_MARGIN - (width % INDENTED_CODE_MARGIN)
        else:
            break
        index += 1
    return width, value[index:]


def indentation_width(value):
    """Return leading indentation in CommonMark columns."""
    return split_indentation(value)[0]


def list_item_content_column(marker_end, spacing, content):
    """Return the column a list item's own content starts at.

    Ordinarily the content column is where the run of spaces after the marker ends.
    CommonMark pins it to one column past the marker in the two cases where that run
    is not separation: an item that is empty after its marker, and an item followed by
    five or more spaces, whose first line is itself an indented code block.
    """
    if not content or spacing > INDENTED_CODE_MARGIN:
        return marker_end + 1
    return marker_end + spacing


def _paragraph_continuation(rest, paragraph_open):
    """Whether this line is an open paragraph's own text rather than a new block.

    `rest` is one visible line with its indentation already removed. A continuation
    line stays with its paragraph however far left it sits, so it neither closes the
    list items around it nor opens an indented code block.
    """
    if not paragraph_open:
        return False
    if THEMATIC_BREAK_RE.fullmatch(rest) or ATX_HEADING_RE.match(rest) \
            or FENCE_OPEN_RE.match(rest):
        return False
    item = LIST_MARKER_RE.match(rest)
    if item is None:
        return True
    spacing, content = split_indentation(rest[item.end("marker"):])
    number = item.group("number")
    # Only a non-empty item, and among ordered items only one numbered 1, may
    # interrupt a paragraph; anything else is that paragraph's own text.
    return not content or (number is not None and number.lstrip("0") != "1")


def _block_state_after(width, rest, content_columns, paragraph_open):
    """Open any list items this line starts and report whether a paragraph is open.

    `content_columns` is mutated in place: it holds the content column of every list
    item still open, innermost last, which is what moves the indented-code threshold
    away from column zero inside a list.
    """
    while True:
        if THEMATIC_BREAK_RE.fullmatch(rest) or ATX_HEADING_RE.match(rest) \
                or FENCE_OPEN_RE.match(rest):
            return False
        if paragraph_open and SETEXT_UNDERLINE_RE.fullmatch(rest):
            return False
        item = LIST_MARKER_RE.match(rest)
        if item is None or _paragraph_continuation(rest, paragraph_open):
            return bool(rest.strip())
        spacing, content = split_indentation(rest[item.end("marker"):])
        column = list_item_content_column(
            width + len(item.group("marker")), spacing, content
        )
        while content_columns and content_columns[-1] > width:
            content_columns.pop()
        content_columns.append(column)
        if not content or spacing > INDENTED_CODE_MARGIN:
            # An empty item opens no paragraph, and an item whose own first line is
            # indented code opens a code block rather than one.
            return False
        paragraph_open = False
        width = column
        rest = content


@functools.lru_cache(maxsize=_TEXT_VIEW_CACHE_SIZE)
def strip_indented_code(text):
    """Blank the lines CommonMark reads as an indented code block.

    A line is one when it is indented at least four columns past the content column
    of the innermost open list item — column zero when no list is open — and no
    paragraph is open above it, because an indented code block cannot interrupt a
    paragraph. Anything else is prose a human reads, including the two shapes a
    width-only rule got wrong: a wrapped paragraph line and a continuation line under
    a list item.

    Two shapes keep their historical answer rather than CommonMark's. A line carrying
    its own list marker is never blanked, even where the marker is followed by five or
    more spaces and so opens the item with code. A block-quoted line is never blanked
    either; it only updates paragraph state, so how quoted source reads is unchanged.
    """
    output = []
    content_columns = []
    paragraph_open = False
    for line in commonmark_lines(text):
        candidate = line[:-1] if line.endswith("\n") else line
        ending = "\n" if line.endswith("\n") else ""
        quote_depth, quoted = strip_block_quote_markers(candidate)
        if quote_depth:
            paragraph_open = bool(quoted.strip())
            output.append(line)
            continue
        width, rest = split_indentation(candidate)
        if not rest.strip():
            paragraph_open = False
            output.append(line)
            continue
        if not _paragraph_continuation(rest, paragraph_open):
            while content_columns and width < content_columns[-1]:
                content_columns.pop()
        base = content_columns[-1] if content_columns else 0
        if not paragraph_open and width - base >= INDENTED_CODE_MARGIN:
            output.append(ending)
            continue
        output.append(line)
        paragraph_open = _block_state_after(
            width, rest, content_columns, paragraph_open
        )
    return "".join(output)


def visible_markdown_link_source(text):
    """Return semantic source and structural links outside code spans."""
    clean = strip_indented_code(semantic_text(text))
    code_spans = inline_code_spans(clean)
    matches = []
    for matched in MARKDOWN_LINK_RE.finditer(clean):
        label_start = matched.start("label")
        label_end = matched.end("label")
        invalid_overlap = any(
            start < matched.end()
            and end > matched.start()
            and not (label_start <= start and end <= label_end)
            for start, end in code_spans
        )
        if not invalid_overlap:
            matches.append(matched)
    return clean, matches


def visible_markdown_link_matches(text):
    """Return structural links, preserving code spans rendered inside labels."""
    return visible_markdown_link_source(text)[1]


def replace_markdown_links_with_labels(text):
    """Replace only structural link syntax, leaving link-like code untouched."""
    clean, matches = visible_markdown_link_source(text)
    output = []
    cursor = 0
    for matched in matches:
        output.extend((clean[cursor:matched.start()], matched.group("label")))
        cursor = matched.end()
    output.append(clean[cursor:])
    return "".join(output)


def markdown_link_destinations(text):
    """Return visible CommonMark inline-link destinations.

    The angle-bracket form intentionally supports repository paths containing spaces.
    """
    return [
        matched.group("angle")
        if matched.group("angle") is not None
        else matched.group("bare")
        for matched in visible_markdown_link_matches(text)
    ]


def markdown_links(text):
    """Return visible CommonMark inline-link `(label, destination)` pairs."""
    return [
        (
            matched.group("label"),
            matched.group("angle")
            if matched.group("angle") is not None
            else matched.group("bare"),
        )
        for matched in visible_markdown_link_matches(text)
    ]


def normalized_action_tokens(text):
    """Normalize visible action words and symbols without dropping code contents."""
    clean = replace_markdown_links_with_labels(text or "")
    clean = render_inline_code(clean)
    normalized = unicodedata.normalize("NFKC", clean).casefold()
    tokens = []
    word = []
    for character in normalized:
        category = unicodedata.category(character)
        if character.isalnum() or category.startswith("M"):
            word.append(character)
            continue
        if word:
            tokens.append("".join(word))
            word = []
        if category.startswith("S"):
            tokens.append(character)
    if word:
        tokens.append("".join(word))
    return tuple(tokens)
