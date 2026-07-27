"""Small CommonMark-aware helpers shared by repository gates.

Structural helpers expose only source that can carry real Markdown headings, fields,
and links, so examples inside fences or raw HTML cannot satisfy an invariant
accidentally. `rendered_human_text` is a separate detection-only view for prose that
raw HTML makes visible to a human; it must never supply structural evidence.
"""
import bisect
import heapq
from html import unescape as html_unescape
from html.entities import html5 as HTML5_CHARACTER_REFERENCES
from html.parser import HTMLParser
from dataclasses import dataclass
import re
from typing import Optional
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
INLINE_BLOCK_BOUNDARY_RE = re.compile(
    r"(?:[ ]{4}|\t|[ ]{0,3}(?:"
    r"#{1,6}(?:[ \t]+|$)|>|`{3,}|~{3,}|"
    r"[-+*][ \t]+|\d+[.)][ \t]+|"
    r"(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})$|"
    r"(?:=+|-+)[ \t]*$|\[(?:\\.|[^\]\\])+\]:"
    r"))"
)
GFM_TABLE_DELIMITER_RE = re.compile(
    r"[ ]{0,3}\|?[ \t]*:?-{3,}:?[ \t]*(?:\|[ \t]*:?-{3,}:?[ \t]*)*"
    r"\|?[ \t]*$"
)
INLINE_LINK_PAREN_NESTING_LIMIT = 32
COMMONMARK_CHARACTER_REFERENCE_RE = re.compile(
    r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]+);"
)
COMMONMARK_ESCAPE_OR_REFERENCE_RE = re.compile(
    r"\\(?P<escaped>[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])"
    r"|(?P<reference>"
    r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]+);"
    r")"
)


def _is_backslash_escaped(source, index):
    count = 0
    cursor = index - 1
    while cursor >= 0 and source[cursor] == "\\":
        count += 1
        cursor -= 1
    return count % 2 == 1


def _linear_inline_code_spans(source, start=0, limit=None):
    """Return CommonMark code-span ranges after one pass over backtick runs."""
    limit = len(source) if limit is None else min(limit, len(source))
    runs = []
    cursor = max(0, start)
    while cursor < limit:
        opening = source.find("`", cursor, limit)
        if opening < 0:
            break
        cursor = opening + 1
        while cursor < limit and source[cursor] == "`":
            cursor += 1
        runs.append((opening, cursor, cursor - opening))

    next_same_width = [None] * len(runs)
    nearest = {}
    for index in range(len(runs) - 1, -1, -1):
        width = runs[index][2]
        next_same_width[index] = nearest.get(width)
        nearest[width] = index

    spans = []
    index = 0
    while index < len(runs):
        if _is_backslash_escaped(source, runs[index][0]):
            index += 1
            continue
        closing_index = next_same_width[index]
        if closing_index is None:
            index += 1
            continue
        spans.append((runs[index][0], runs[closing_index][1]))
        index = closing_index + 1
    return spans


def _balanced_label_closings(source, start=0, limit=None, scan_counter=None):
    """Map unescaped label openers to closers in one bounded source pass."""
    limit = len(source) if limit is None else min(limit, len(source))
    code_spans = {
        opening: closing
        for opening, closing in _linear_inline_code_spans(source, start, limit)
    }
    stack = []
    closings = {}
    cursor = max(0, start)
    while cursor < limit:
        if scan_counter is not None:
            scan_counter[0] += 1
        code_end = code_spans.get(cursor)
        if code_end is not None:
            cursor = code_end
            continue
        character = source[cursor]
        if character == "\\" and cursor + 1 < limit:
            cursor += 2
            continue
        if character == "[":
            stack.append(cursor)
        elif character == "]" and stack:
            closings[stack.pop()] = cursor
        cursor += 1
    return closings


class _InlineLinkMatch:
    """Minimal re.Match-compatible view used by the Markdown helpers."""

    _GROUP_ORDER = ("label", "angle", "bare")

    def __init__(self, source, start, end, spans):
        self._source = source
        self._start = start
        self._end = end
        self._spans = spans

    def _span(self, group):
        if group in (0, None):
            return self._start, self._end
        if isinstance(group, int):
            if not 1 <= group <= len(self._GROUP_ORDER):
                raise IndexError("no such group")
            group = self._GROUP_ORDER[group - 1]
        if group not in self._spans:
            raise IndexError("no such group")
        return self._spans[group]

    def group(self, group=0):
        start, end = self._span(group)
        return None if start is None else self._source[start:end]

    def start(self, group=0):
        return self._span(group)[0]

    def end(self, group=0):
        return self._span(group)[1]


class _InlineLinkPattern:
    """Balanced inline-link scanner with the small API callers need."""

    def __init__(self, image=False):
        self.image = image

    def _match_at(self, source, start, limit, label_closings=None):
        if self.image:
            if start + 1 >= limit or source[start:start + 2] != "![" \
                    or _is_backslash_escaped(source, start):
                return None
            bracket = start + 1
        else:
            if source[start] != "[" or _is_backslash_escaped(source, start):
                return None
            if start and source[start - 1] == "!" \
                    and not _is_backslash_escaped(source, start - 1):
                return None
            bracket = start

        if label_closings is None:
            label_closings = _balanced_label_closings(source, start, limit)
        label_end = label_closings.get(bracket)
        if label_end is None:
            return None

        cursor = label_end + 1
        if cursor >= limit or source[cursor] != "(":
            return None
        cursor += 1
        while cursor < limit and source[cursor] in " \t":
            cursor += 1

        angle_span = (None, None)
        bare_span = (None, None)
        if cursor < limit and source[cursor] == "<":
            destination_start = cursor + 1
            cursor = destination_start
            while cursor < limit:
                if source[cursor] in "\r\n":
                    return None
                if source[cursor] == "<" \
                        and not _is_backslash_escaped(source, cursor):
                    return None
                if source[cursor] == ">" \
                        and not _is_backslash_escaped(source, cursor):
                    break
                cursor += 1
            if cursor >= limit or source[cursor] != ">":
                return None
            angle_span = (destination_start, cursor)
            cursor += 1
        else:
            destination_start = cursor
            depth = 0
            while cursor < limit:
                character = source[cursor]
                if character.isspace() or ord(character) < 0x20 \
                        or ord(character) == 0x7F:
                    break
                if character == "\\" and cursor + 1 < limit:
                    cursor += 2
                    continue
                if character == "(":
                    depth += 1
                    if depth > INLINE_LINK_PAREN_NESTING_LIMIT:
                        return None
                elif character == ")":
                    if depth == 0:
                        break
                    depth -= 1
                cursor += 1
            if depth:
                return None
            bare_span = (destination_start, cursor)

        had_spacing = cursor < limit and source[cursor] in " \t"
        while cursor < limit and source[cursor] in " \t":
            cursor += 1
        if had_spacing and cursor < limit and source[cursor] in "\"'(":
            opening = source[cursor]
            closing = ")" if opening == "(" else opening
            cursor += 1
            while cursor < limit:
                if source[cursor] == "\\" and cursor + 1 < limit:
                    cursor += 2
                    continue
                if source[cursor] == closing:
                    cursor += 1
                    break
                cursor += 1
            else:
                return None
            while cursor < limit and source[cursor] in " \t":
                cursor += 1
        if cursor >= limit or source[cursor] != ")":
            return None
        end = cursor + 1
        return _InlineLinkMatch(
            source, start, end,
            {
                "label": (bracket + 1, label_end),
                "angle": angle_span,
                "bare": bare_span,
            },
        )

    def finditer(self, source, pos=0, endpos=None):
        limit = len(source) if endpos is None else min(endpos, len(source))
        cursor = max(0, pos)
        label_closings = _balanced_label_closings(source, cursor, limit)
        opening = "!" if self.image else "["
        while cursor < limit:
            candidate = source.find(opening, cursor, limit)
            if candidate < 0:
                return
            matched = self._match_at(
                source, candidate, limit, label_closings=label_closings
            )
            if matched is None:
                cursor = candidate + 1
                continue
            yield matched
            cursor = matched.end()

    def match(self, source, pos=0, endpos=None):
        limit = len(source) if endpos is None else min(endpos, len(source))
        if pos >= limit:
            return None
        label_closings = _balanced_label_closings(source, pos, limit)
        return self._match_at(
            source, pos, limit, label_closings=label_closings
        )

    def sub(self, replacement, source, count=0):
        output = []
        cursor = 0
        replaced = 0
        for matched in self.finditer(source):
            if count and replaced >= count:
                break
            output.append(source[cursor:matched.start()])
            output.append(
                replacement(matched) if callable(replacement) else replacement
            )
            cursor = matched.end()
            replaced += 1
        output.append(source[cursor:])
        return "".join(output)


MARKDOWN_LINK_RE = _InlineLinkPattern()
MARKDOWN_IMAGE_RE = _InlineLinkPattern(image=True)
REFERENCE_DEFINITION_RE = re.compile(
    r"^[ ]{0,3}\[(?P<label>(?:\\.|[^\]\\])+)\]:[ \t]*(?P<rest>.*)$"
)
REFERENCE_USE_RE = re.compile(
    r"(?<!\\)(?P<image>!)?\[(?P<text>(?:\\.|[^\]\\])*)\]"
    r"\[(?P<label>(?:\\.|[^\]\\])*)\]"
)
REFERENCE_SHORTCUT_RE = re.compile(
    r"(?<!\\)(?P<image>!)?\[(?P<label>(?:\\.|[^\]\\])+)\]"
)
URI_AUTOLINK_RE = re.compile(
    r"<(?P<destination>"
    r"[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\x00-\x20]*)>"
)
EMAIL_AUTOLINK_RE = re.compile(
    r"<(?P<address>"
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)>"
)
GFM_EXTENDED_URL_TRIGGER_RE = re.compile(
    r"(?:https?|ftp)://|www\.", re.I
)
GFM_EXTENDED_EMAIL_RE = re.compile(
    r"(?:(?P<protocol>mailto:|xmpp:))?"
    r"(?P<local>[A-Za-z0-9.+_-]+)@"
    r"(?P<domain>[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+)"
    r"(?P<resource>/[A-Za-z0-9_./-]*)?",
    re.I,
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


def is_default_ignorable_character(character):
    """Recognize one default-ignorable code point without normalizing it."""
    codepoint = ord(character)
    return (
        unicodedata.category(character) == "Cf"
        or any(
            start <= codepoint <= end
            for start, end in DEFAULT_IGNORABLE_NONFORMAT_RANGES
        )
    )


@dataclass(frozen=True)
class MarkdownReferenceDefinition:
    """One usable CommonMark reference definition."""

    label: str
    normalized_label: str
    destination: str
    start: int
    end: int


@dataclass(frozen=True)
class VisibleMarkdownReference:
    """One rendered link or image and its resolved destination."""

    label: str
    destination: str
    is_image: bool
    syntax: str
    start: int
    end: int
    definition_start: Optional[int] = None


@dataclass(frozen=True)
class MarkdownReferenceResolution:
    """Resolved rendered references plus fail-closed syntax diagnostics."""

    references: tuple
    definitions: tuple
    duplicate_labels: tuple
    unresolved: tuple


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
        decoded = html_unescape(source).replace("\r", " ").replace("\n", " ")
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
        if is_default_ignorable_character(character):
            continue
        output.append(character)
    return "".join(output)


def inline_code_spans(text):
    """Return the source ranges occupied by closed CommonMark code spans."""
    return _linear_inline_code_spans(text or "")


def commonmark_source_lines(value):
    """Return source-preserving physical CommonMark lines with their offsets."""
    source = value or ""
    lines = []
    cursor = 0
    for matched in re.finditer(r"\r\n|[\r\n]", source):
        lines.append((cursor, matched.end(), source[cursor:matched.start()]))
        cursor = matched.end()
    if cursor < len(source):
        lines.append((cursor, len(source), source[cursor:]))
    return tuple(lines)


def _gfm_table_row_parts(value, require_pipe=True):
    """Return GFM cells and inline ranges using pre-inline pipe escaping rules."""
    source = value or ""
    indentation = len(source) - len(source.lstrip(" "))
    if indentation > 3 or source[indentation:].startswith("\t"):
        return None
    row_start = indentation
    row_end = len(source)
    while row_end > row_start and source[row_end - 1] in " \t":
        row_end -= 1
    if row_start == row_end:
        return None

    separators = [
        position
        for position in range(row_start, row_end)
        if source[position] == "|"
        and not _is_backslash_escaped(source, position)
    ]
    if require_pipe and not separators:
        return None
    if not separators:
        return ((source[row_start:row_end].strip(" \t"),), ((row_start, row_end),))

    content_start = row_start
    content_end = row_end
    inner_separators = separators
    if inner_separators[0] == row_start:
        content_start += 1
        inner_separators = inner_separators[1:]
    if inner_separators and inner_separators[-1] == row_end - 1:
        content_end -= 1
        inner_separators = inner_separators[:-1]
    boundaries = [content_start, *inner_separators, content_end]
    cells = []
    ranges = []
    for index in range(len(boundaries) - 1):
        start = boundaries[index] + (1 if index else 0)
        end = boundaries[index + 1]
        while start < end and source[start] in " \t":
            start += 1
        while end > start and source[end - 1] in " \t":
            end -= 1
        cells.append(source[start:end])
        if start < end:
            ranges.append((start, end))
    return tuple(cells), tuple(ranges)


def gfm_table_row_cells(value):
    """Split one possible GFM table row at every unescaped pipe."""
    parts = _gfm_table_row_parts(value)
    return None if parts is None else parts[0]


def gfm_table_delimiter_cells(value):
    """Return delimiter cells for one complete GFM table delimiter row."""
    parts = _gfm_table_row_parts(value, require_pipe=False)
    cells = None if parts is None else parts[0]
    if cells is None or not cells:
        return None
    if any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in cells):
        return None
    return cells


def _starts_raw_html_block(value):
    """Return whether a physical line begins a CommonMark raw-HTML block."""
    return bool(
        RAW_HTML_TYPE1_START_RE.match(value)
        or HTML_COMMENT_START_RE.match(value)
        or HTML_PROCESSING_START_RE.match(value)
        or HTML_DECLARATION_START_RE.match(value)
        or HTML_CDATA_START_RE.match(value)
        or RAW_HTML_TYPE6_START_RE.match(value)
        or RAW_HTML_TYPE7_START_RE.match(value)
    )


def _starts_non_table_block(value):
    """Return whether a line starts a block that terminates a GFM table."""
    return bool(
        INLINE_BLOCK_BOUNDARY_RE.match(value)
        or _starts_raw_html_block(value)
    )


def gfm_table_block_ranges(value):
    """Return top-level GFM table blocks, including every ordinary body row."""
    lines = commonmark_source_lines(value)
    ranges = []
    index = 0
    while index + 1 < len(lines):
        header_start, _header_end, header = lines[index]
        _delimiter_start, delimiter_end, delimiter = lines[index + 1]
        header_cells = gfm_table_row_cells(header)
        delimiter_cells = gfm_table_delimiter_cells(delimiter)
        if _starts_non_table_block(header) \
                or header_cells is None \
                or delimiter_cells is None \
                or len(header_cells) != len(delimiter_cells):
            index += 1
            continue

        table_end = delimiter_end
        body_index = index + 2
        while body_index < len(lines):
            _body_start, body_end, body = lines[body_index]
            if not body.strip() or _starts_non_table_block(body):
                break
            table_end = body_end
            body_index += 1
        ranges.append((header_start, table_end))
        index = body_index
    return tuple(ranges)


def gfm_table_scan_source(value):
    """Blank GFM table blocks while preserving their physical line boundaries."""
    output = list(value or "")
    for start, end in gfm_table_block_ranges(value):
        for position in range(start, end):
            if output[position] not in "\r\n":
                output[position] = " "
    return "".join(output)


def _gfm_table_inline_ranges(value, start, end):
    """Return each table cell as its own CommonMark inline-content range."""
    ranges = []
    for line_start, _line_end, content in commonmark_source_lines(value[start:end]):
        parts = _gfm_table_row_parts(content, require_pipe=False)
        if parts is None:
            continue
        ranges.extend(
            (start + line_start + cell_start, start + line_start + cell_end)
            for cell_start, cell_end in parts[1]
        )
    return tuple(ranges)


def commonmark_inline_block_ranges(value):
    """Return conservative ranges that cannot pair inline code across blocks/cells."""
    source = value or ""
    table_ranges = {
        start: end for start, end in gfm_table_block_ranges(source)
    }
    ranges = []
    current_start = None
    current_end = None

    def finish_current():
        nonlocal current_start, current_end
        if current_start is not None and current_end is not None:
            ranges.append((current_start, current_end))
        current_start = None
        current_end = None

    table_end = None
    for start, end, content in commonmark_source_lines(source):
        if table_end is not None and start < table_end:
            continue
        table_end = table_ranges.get(start)
        if table_end is not None:
            finish_current()
            ranges.extend(_gfm_table_inline_ranges(source, start, table_end))
            continue
        if not content.strip():
            finish_current()
            continue
        is_block_boundary = bool(
            _starts_non_table_block(content)
            or GFM_TABLE_DELIMITER_RE.match(content)
        )
        if is_block_boundary:
            finish_current()
            ranges.append((start, end))
            continue
        if current_start is None:
            current_start = start
        current_end = end
    finish_current()
    return tuple(ranges)


def block_aware_inline_code_spans(value):
    """Parse code spans independently inside each Markdown inline-content range."""
    source = value or ""
    spans = []
    for start, end in commonmark_inline_block_ranges(source):
        spans.extend(
            (start + opening, start + closing)
            for opening, closing in inline_code_spans(source[start:end])
        )
    return tuple(spans)


def strip_block_aware_inline_code(text):
    """Blank code spans without allowing delimiters to pair across blocks/cells."""
    output = list(text or "")
    for opening, closing in block_aware_inline_code_spans(text):
        for position in range(opening, closing):
            if output[position] not in ("\n", "\r"):
                output[position] = " "
    return "".join(output)


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


def _is_unicode_whitespace(character):
    """Return CommonMark's Unicode-whitespace classification."""
    return bool(
        character
        and (character in "\t\n\f\r" or unicodedata.category(character) == "Zs")
    )


def _is_unicode_punctuation(character):
    """Return CommonMark's ASCII-or-Unicode punctuation classification."""
    return bool(
        character
        and (
            character in "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
            or unicodedata.category(character) in {
                "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps",
            }
        )
    )


def _emphasis_run_flanking(source, start, end, marker):
    """Return GFM can-open/can-close state for one delimiter run."""
    before_index = start - 1
    after_index = end
    if marker in "*_":
        # cmark-gfm registers strikethrough as an emphasis extension, so its
        # scanner skips adjacent tildes when classifying star/underscore runs.
        while before_index >= 0 and source[before_index] == "~":
            before_index -= 1
        while after_index < len(source) and source[after_index] == "~":
            after_index += 1
    before = source[before_index] if before_index >= 0 else "\n"
    after = source[after_index] if after_index < len(source) else "\n"
    before_whitespace = _is_unicode_whitespace(before)
    after_whitespace = _is_unicode_whitespace(after)
    before_punctuation = _is_unicode_punctuation(before)
    after_punctuation = _is_unicode_punctuation(after)
    left_flanking = not after_whitespace and (
        not after_punctuation or before_whitespace or before_punctuation
    )
    right_flanking = not before_whitespace and (
        not before_punctuation or after_whitespace or after_punctuation
    )
    if marker in "*~":
        return left_flanking, right_flanking
    return (
        left_flanking and (not right_flanking or before_punctuation),
        right_flanking and (not left_flanking or after_punctuation),
    )


def _emphasis_render_plan(text, ignored_spans=()):
    """Return consumed emphasis/strikethrough positions and ambiguous runs.

    Candidate openers are indexed by marker, closer capability, and length modulo
    three for emphasis, or exact one/two-tilde width for strikethrough. Selecting
    the nearest compatible group implements both rules in bounded work; every
    candidate is pushed and invalidated only a constant number of times.
    """
    source = text or ""
    delimiters = []
    ignored = iter(ignored_spans)
    ignored_span = next(ignored, None)
    cursor = 0
    while cursor < len(source):
        while ignored_span is not None and ignored_span[1] <= cursor:
            ignored_span = next(ignored, None)
        if ignored_span is not None \
                and ignored_span[0] <= cursor < ignored_span[1]:
            cursor = ignored_span[1]
            continue
        marker = source[cursor]
        if marker not in "*_~":
            cursor += 1
            continue
        if _is_backslash_escaped(source, cursor):
            cursor += 1
            continue
        start = cursor
        cursor += 1
        while cursor < len(source) and source[cursor] == marker:
            cursor += 1
        if marker == "~" and cursor - start > 2:
            continue
        can_open, can_close = _emphasis_run_flanking(
            source, start, cursor, marker
        )
        delimiters.append({
            "marker": marker,
            "start": start,
            "original_length": cursor - start,
            "remaining": cursor - start,
            "consumed_left": 0,
            "can_open": can_open,
            "can_close": can_close,
            "active": True,
            "generation": 0,
        })

    removed = bytearray(len(source))
    open_stack = []
    groups = {
        (marker, can_close, modulo): []
        for marker in "*_"
        for can_close in (False, True)
        for modulo in range(3)
    }
    groups.update({
        ("~", can_close, width): []
        for can_close in (False, True)
        for width in (1, 2)
    })

    def group_key(delimiter):
        return (
            delimiter["marker"],
            delimiter["can_close"],
            delimiter["original_length"]
            if delimiter["marker"] == "~"
            else delimiter["original_length"] % 3,
        )

    def push_opener(index):
        delimiter = delimiters[index]
        delimiter["generation"] += 1
        groups[group_key(delimiter)].append(
            (index, delimiter["generation"])
        )

    def group_top(key):
        candidates = groups[key]
        while candidates:
            index, generation = candidates[-1]
            delimiter = delimiters[index]
            if delimiter["active"] \
                    and delimiter["generation"] == generation \
                    and delimiter["remaining"] \
                    and group_key(delimiter) == key:
                return index
            candidates.pop()
        return None

    def compatible(opener, closer):
        if closer["marker"] == "~":
            return (
                opener["original_length"]
                == closer["original_length"]
            )
        return not (
            (closer["can_open"] or opener["can_close"])
            and (
                opener["original_length"] + closer["original_length"]
            ) % 3 == 0
            and (
                opener["original_length"] % 3 != 0
                or closer["original_length"] % 3 != 0
            )
        )

    for closer_index, closer in enumerate(delimiters):
        while closer["can_close"] and closer["remaining"]:
            opener_index = None
            for can_close in (False, True):
                widths = (
                    (closer["original_length"],)
                    if closer["marker"] == "~"
                    else range(3)
                )
                for modulo in widths:
                    candidate_index = group_top(
                        (closer["marker"], can_close, modulo)
                    )
                    if candidate_index is None:
                        continue
                    candidate = delimiters[candidate_index]
                    if compatible(candidate, closer) \
                            and (
                                opener_index is None
                                or candidate_index > opener_index
                            ):
                        opener_index = candidate_index
            if opener_index is None:
                break

            while open_stack and open_stack[-1] != opener_index:
                discarded = delimiters[open_stack.pop()]
                discarded["active"] = False
            opener = delimiters[opener_index]
            use = (
                opener["remaining"]
                if closer["marker"] == "~"
                else 2
                if opener["remaining"] >= 2
                and closer["remaining"] >= 2
                else 1
            )
            opener_start = (
                opener["start"] + opener["consumed_left"]
                + opener["remaining"] - use
            )
            closer_start = closer["start"] + closer["consumed_left"]
            for position in range(opener_start, opener_start + use):
                removed[position] = 1
            for position in range(closer_start, closer_start + use):
                removed[position] = 1
            opener["remaining"] -= use
            closer["remaining"] -= use
            closer["consumed_left"] += use
            if opener["remaining"]:
                push_opener(opener_index)
            else:
                opener["active"] = False
                open_stack.pop()

        if closer["can_open"] and closer["remaining"]:
            open_stack.append(closer_index)
            push_opener(closer_index)

    ambiguous = any(
        delimiter["remaining"]
        and (delimiter["can_open"] or delimiter["can_close"])
        for delimiter in delimiters
    )
    return removed, ambiguous


def _render_emphasis_delimiters(text, ignored_spans=()):
    """Remove GFM emphasis/strikethrough in one delimiter-stack pass."""
    source = text or ""
    removed, _ambiguous = _emphasis_render_plan(source, ignored_spans)
    return "".join(
        character
        for index, character in enumerate(source)
        if not removed[index]
    )


def strict_commonmark_character_reference(value):
    """Decode one exact CommonMark character reference, or return it unchanged."""
    token = value or ""
    if not COMMONMARK_CHARACTER_REFERENCE_RE.fullmatch(token):
        return token
    if token.startswith("&#"):
        return html_unescape(token)
    return HTML5_CHARACTER_REFERENCES.get(token[1:], token)


def render_commonmark_inline_tokens(text):
    """Render escapes and exact character references in one source-token pass."""
    def replace(matched):
        escaped = matched.group("escaped")
        if escaped is not None:
            return escaped
        return strict_commonmark_character_reference(matched.group("reference"))

    return COMMONMARK_ESCAPE_OR_REFERENCE_RE.sub(replace, text or "")


def rendered_link_destination(text):
    """Render escapes and character references in a Markdown destination."""
    return render_commonmark_inline_tokens(text)


def _merged_source_spans(spans):
    """Return sorted, merged half-open source ranges."""
    merged = []
    for start, end in sorted(spans):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return tuple(merged)


def _source_position_is_occupied(position, spans):
    """Return whether position belongs to sorted half-open spans."""
    index = bisect.bisect_right(spans, (position, float("inf"))) - 1
    return index >= 0 and position < spans[index][1]


def _gfm_valid_host_character(character):
    return bool(
        character
        and not _is_unicode_whitespace(character)
        and not _is_unicode_punctuation(character)
    )


def _gfm_valid_host_byte(data, index):
    """Apply cmark-gfm's UTF-8 host check at one byte offset.

    The C scanner advances its domain cursor one byte at a time even though the
    host classifier consumes a complete UTF-8 code point.  A cursor on a UTF-8
    continuation byte is therefore invalid.  Preserving that behavior matters
    because it determines where the later path scan resumes.
    """
    for width in range(1, min(4, len(data) - index) + 1):
        try:
            decoded = data[index:index + width].decode("utf-8")
        except UnicodeDecodeError:
            continue
        if len(decoded) == 1:
            return _gfm_valid_host_character(decoded)
    return False


def _source_index_after_utf8_byte_offset(value, byte_offset):
    """Map a possibly mid-codepoint C byte offset to its source boundary."""
    consumed = 0
    for index, character in enumerate(value):
        consumed += len(character.encode("utf-8"))
        if consumed >= byte_offset:
            return index + 1
    return len(value)


def _gfm_domain_end(value, allow_short):
    """Port cmark-gfm's byte-oriented extended-autolink domain scan."""
    data = value.encode("utf-8")
    size = len(data)
    index = 1
    periods = 0
    prior_segment_underscores = 0
    current_segment_underscores = 0
    while index < size - 1:
        if data[index] == ord("\\") and index < size - 2:
            index += 1
        character = data[index]
        if character == ord("_"):
            current_segment_underscores += 1
        elif character == ord("."):
            prior_segment_underscores = current_segment_underscores
            current_segment_underscores = 0
            periods += 1
        elif not _gfm_valid_host_byte(data, index) \
                and character != ord("-"):
            break
        index += 1
    if (prior_segment_underscores or current_segment_underscores) \
            and periods <= 10:
        return 0
    if not allow_short and not periods:
        return 0
    return _source_index_after_utf8_byte_offset(value, index)


def _gfm_extended_autolink_end(value, end):
    """Trim punctuation using cmark-gfm's extended-autolink delimiter rules."""
    opening = 0
    closing = 0
    for index, character in enumerate(value[:end]):
        if character == "<":
            end = index
            break
        if character == "(":
            opening += 1
        elif character == ")":
            closing += 1
    while end:
        character = value[end - 1]
        if character == ")":
            if closing <= opening:
                return end
            closing -= 1
            end -= 1
            continue
        if character in "?!.,:*_~'\"":
            end -= 1
            continue
        if character == ";":
            cursor = end - 2
            while cursor > 0 and value[cursor].isascii() \
                    and value[cursor].isalpha():
                cursor -= 1
            end = cursor if cursor < end - 2 and value[cursor] == "&" else end - 1
            continue
        return end
    return end


def _bracket_content_spans(source, ignored_spans=()):
    """Return source regions where the inline parser is inside brackets."""
    ignored_spans = _merged_source_spans(ignored_spans)
    ignored_index = 0
    stack = []
    spans = []
    cursor = 0
    while cursor < len(source):
        while ignored_index < len(ignored_spans) \
                and ignored_spans[ignored_index][1] <= cursor:
            ignored_index += 1
        if ignored_index < len(ignored_spans) \
                and ignored_spans[ignored_index][0] <= cursor \
                < ignored_spans[ignored_index][1]:
            cursor = ignored_spans[ignored_index][1]
            continue
        if source[cursor] == "\\" and cursor + 1 < len(source):
            cursor += 2
            continue
        if source[cursor] == "[":
            stack.append(cursor)
        elif source[cursor] == "]" and stack:
            opening = stack.pop()
            spans.append((opening + 1, cursor))
        cursor += 1
    spans.extend((opening + 1, len(source)) for opening in stack)
    return _merged_source_spans(spans)


def _gfm_extended_url_candidates(source, ignored_spans=()):
    """Yield GFM URL/www autolinks before email postprocessing."""
    ignored_spans = _merged_source_spans(ignored_spans)
    bracket_spans = _bracket_content_spans(source, ignored_spans)
    cursor = 0
    while cursor < len(source):
        matched = GFM_EXTENDED_URL_TRIGGER_RE.search(source, cursor)
        if matched is None:
            return
        start = matched.start()
        trigger = matched.group()
        if _source_position_is_occupied(start, ignored_spans) \
                or _source_position_is_occupied(start, bracket_spans):
            cursor = start + 1
            continue
        is_www = trigger == "www."
        if trigger.lower() == "www." and not is_www:
            cursor = start + 1
            continue
        if is_www:
            if start and source[start - 1] not in "*_~(" \
                    and not _is_unicode_whitespace(source[start - 1]):
                cursor = start + 1
                continue
            domain_source = source[start:]
            domain_end = _gfm_domain_end(domain_source, allow_short=False)
            prefix_length = 0
        else:
            if start and source[start - 1].isascii() \
                    and source[start - 1].isalpha():
                cursor = start + 1
                continue
            prefix_length = trigger.index("://") + 3
            domain_source = source[start + prefix_length:]
            if not domain_source or not _gfm_valid_host_character(
                domain_source[0]
            ):
                cursor = start + 1
                continue
            domain_end = _gfm_domain_end(domain_source, allow_short=True)
        if not domain_end:
            cursor = start + 1
            continue
        end = start + prefix_length + domain_end
        while end < len(source) \
                and not _is_unicode_whitespace(source[end]) \
                and source[end] != "<":
            end += 1
        end = start + _gfm_extended_autolink_end(source[start:end], end - start)
        if end <= start:
            cursor = start + 1
            continue
        label = source[start:end]
        destination = "http://" + label if is_www else label
        yield start, end, label, destination
        cursor = end


def _rendered_text_segments_with_source_map(
    source, ignored_spans=(), removed_positions=()
):
    """Render ordinary text while retaining source ranges and AST boundaries.

    ``removed_positions`` identifies consumed inline delimiters.  Each consumed
    position splits the rendered segment because cmark-gfm's autolink
    postprocessor sees the text nodes on either side of emphasis structure, not
    one concatenated source string.
    """
    ignored_spans = _merged_source_spans(ignored_spans)
    ignored_index = 0
    characters = []
    mappings = []
    segments = []

    def flush():
        if characters:
            segments.append(("".join(characters), tuple(mappings)))
            characters.clear()
            mappings.clear()

    cursor = 0
    while cursor < len(source):
        while ignored_index < len(ignored_spans) \
                and ignored_spans[ignored_index][1] <= cursor:
            ignored_index += 1
        if ignored_index < len(ignored_spans) \
                and ignored_spans[ignored_index][0] <= cursor \
                < ignored_spans[ignored_index][1]:
            flush()
            cursor = ignored_spans[ignored_index][1]
            continue
        if removed_positions and removed_positions[cursor]:
            flush()
            cursor += 1
            continue
        matched = COMMONMARK_ESCAPE_OR_REFERENCE_RE.match(source, cursor)
        if matched is None:
            characters.append(source[cursor])
            mappings.append((cursor, cursor + 1))
            cursor += 1
            continue
        rendered = (
            matched.group("escaped")
            if matched.group("escaped") is not None
            else strict_commonmark_character_reference(matched.group("reference"))
        )
        characters.extend(rendered)
        mappings.extend([matched.span()] * len(rendered))
        cursor = matched.end()
    flush()
    return tuple(segments)


def _gfm_extended_email_candidates(source, ignored_spans=()):
    """Yield GFM email autolinks after escapes/entities become text."""
    emphasis_removed, _ambiguous = _emphasis_render_plan(
        source, ignored_spans
    )
    for rendered, mappings in _rendered_text_segments_with_source_map(
        source, ignored_spans, emphasis_removed
    ):
        for matched in GFM_EXTENDED_EMAIL_RE.finditer(rendered):
            protocol = (matched.group("protocol") or "").lower()
            resource = matched.group("resource") or ""
            if resource and protocol != "xmpp:":
                end = matched.start("resource")
            else:
                end = matched.end()
            label = rendered[matched.start():end]
            trimmed = _gfm_extended_autolink_end(label, len(label))
            end = matched.start() + trimmed
            label = rendered[matched.start():end]
            if not label:
                continue
            domain = matched.group("domain")
            if not domain[-1].isascii() or not domain[-1].isalpha():
                continue
            source_start = mappings[matched.start()][0]
            source_end = mappings[end - 1][1]
            destination = label if protocol else "mailto:" + label
            yield source_start, source_end, label, destination


def _render_noncode_inline_segment(source, removed, offset):
    """Render one ordinary inline segment without revisiting emitted text."""
    visible = "".join(
        character
        for index, character in enumerate(source, start=offset)
        if not removed[index]
    )
    return render_commonmark_inline_tokens(visible)


def _unescaped_autolink_candidates(source):
    """Return autolinks after CommonMark backslash-parity escape handling."""
    candidates = heapq.merge(
        (
            (
                matched,
                matched.group("destination"),
                matched.group("destination"),
            )
            for matched in URI_AUTOLINK_RE.finditer(source or "")
        ),
        (
            (
                matched,
                matched.group("address"),
                "mailto:" + matched.group("address"),
            )
            for matched in EMAIL_AUTOLINK_RE.finditer(source or "")
        ),
        key=lambda item: item[0].start(),
    )
    for matched, label, destination in candidates:
        start, end = matched.span()
        if _is_backslash_escaped(source, start):
            continue
        yield start, end, label, destination


def _inline_opaque_segments(
    source, include_extended=True, suppress_extended=False
):
    """Resolve code-span and autolink ownership in GFM source order.

    An earlier code-span opener owns any angle text before its closer. At an
    earlier angle or extended URL opener, the whole autolink is opaque, including
    backticks that would otherwise form a code span. Email recognition runs over
    the remaining rendered text, as cmark-gfm's postprocessor does. Every source
    class is scanned a bounded number of times.
    """
    source = source or ""
    runs = []
    cursor = 0
    while cursor < len(source):
        opening = source.find("`", cursor)
        if opening < 0:
            break
        cursor = opening + 1
        while cursor < len(source) and source[cursor] == "`":
            cursor += 1
        runs.append((opening, cursor, cursor - opening))

    next_same_width = [None] * len(runs)
    nearest = {}
    for index in range(len(runs) - 1, -1, -1):
        width = runs[index][2]
        next_same_width[index] = nearest.get(width)
        nearest[width] = index

    next_code_opener = [None] * (len(runs) + 1)
    nearest_code_opener = None
    for index in range(len(runs) - 1, -1, -1):
        if next_same_width[index] is not None \
                and not _is_backslash_escaped(source, runs[index][0]):
            nearest_code_opener = index
        next_code_opener[index] = nearest_code_opener

    autolinks = tuple(_unescaped_autolink_candidates(source))
    extended_urls = (
        tuple(_gfm_extended_url_candidates(source))
        if include_extended and not suppress_extended
        else ()
    )
    run_index = 0
    autolink_index = 0
    extended_url_index = 0
    cursor = 0
    segments = []
    while run_index < len(runs) or autolink_index < len(autolinks) \
            or extended_url_index < len(extended_urls):
        while run_index < len(runs) and runs[run_index][0] < cursor:
            run_index += 1
        while autolink_index < len(autolinks) \
                and autolinks[autolink_index][0] < cursor:
            autolink_index += 1
        while extended_url_index < len(extended_urls) \
                and extended_urls[extended_url_index][0] < cursor:
            extended_url_index += 1

        candidate_run_index = next_code_opener[run_index]
        closing_run_index = (
            next_same_width[candidate_run_index]
            if candidate_run_index is not None
            else None
        )
        code_start = (
            runs[candidate_run_index][0]
            if candidate_run_index is not None
            else len(source) + 1
        )
        autolink_start = (
            autolinks[autolink_index][0]
            if autolink_index < len(autolinks)
            else len(source) + 1
        )
        extended_url_start = (
            extended_urls[extended_url_index][0]
            if extended_url_index < len(extended_urls)
            else len(source) + 1
        )

        if code_start < autolink_start and code_start < extended_url_start:
            closing = runs[closing_run_index][1]
            segments.append((code_start, closing, "code", None, None))
            cursor = closing
            run_index = closing_run_index + 1
            continue
        if autolink_start < extended_url_start:
            opening, closing, label, destination = autolinks[autolink_index]
            segments.append(
                (opening, closing, "autolink", label, destination)
            )
            cursor = closing
            autolink_index += 1
            continue
        if extended_url_index < len(extended_urls):
            opening, closing, label, destination = extended_urls[
                extended_url_index
            ]
            segments.append((
                opening, closing, "extended_autolink", label, destination
            ))
            cursor = closing
            extended_url_index += 1
            continue
        break

    if include_extended and not suppress_extended:
        link_spans = tuple(
            (matched.start(), matched.end())
            for matched in MARKDOWN_LINK_RE.finditer(source)
        )
        email_ignored = _merged_source_spans(
            [(opening, closing) for opening, closing, *_rest in segments]
            + list(link_spans)
        )
        segments.extend(
            (opening, closing, "extended_autolink", label, destination)
            for opening, closing, label, destination
            in _gfm_extended_email_candidates(source, email_ignored)
        )
        segments.sort(key=lambda segment: segment[0])
    return tuple(segments)


def rendered_inline_text(text, suppress_extended_autolinks=False):
    """Return rendered inline prose while preserving every Unicode code point.

    Code-span contents are retained literally, emphasis delimiters are removed,
    character references are decoded, and CommonMark escapes are rendered. This
    deliberately performs no NFC/NFKC normalization: callers that promise exact text
    identity may normalize whitespace but must retain every non-whitespace code point.
    """
    source = text or ""
    opaque_segments = _inline_opaque_segments(
        source, suppress_extended=suppress_extended_autolinks
    )
    segments = tuple(
        (opening, closing, kind, value)
        for opening, closing, kind, value, _destination in opaque_segments
    )
    ignored_spans = tuple(
        (opening, closing)
        for opening, closing, _kind, _value in segments
    )
    removed, _ambiguous = _emphasis_render_plan(source, ignored_spans)
    output = []
    cursor = 0
    for opening, closing, kind, value in segments:
        output.append(_render_noncode_inline_segment(
            source[cursor:opening], removed, cursor
        ))
        output.append(
            render_inline_code(source[opening:closing])
            if kind == "code"
            else value
        )
        cursor = closing
    output.append(_render_noncode_inline_segment(source[cursor:], removed, cursor))
    return "".join(output)


def rendered_link_label_text(text):
    """Render exact label source inside its owning CommonMark brackets."""
    rendered = rendered_inline_text(
        "[" + (text or "") + "]", suppress_extended_autolinks=True
    )
    return rendered[1:-1]


def ambiguous_inline_markup_reason(text, suppress_extended_autolinks=False):
    """Return why inline source has an unclosed rendering delimiter, if any."""
    source = text or ""
    opaque_segments = _inline_opaque_segments(
        source, suppress_extended=suppress_extended_autolinks
    )
    opaque_spans = tuple(
        (opening, closing)
        for opening, closing, _kind, _value, _destination in opaque_segments
    )
    cursor = 0
    for opening, closing in opaque_spans:
        while cursor < opening:
            if source[cursor] == "`" and not _is_backslash_escaped(source, cursor):
                return "contains an unclosed or ambiguous code span"
            cursor += 1
        cursor = closing
    while cursor < len(source):
        if source[cursor] == "`" and not _is_backslash_escaped(source, cursor):
            return "contains an unclosed or ambiguous code span"
        cursor += 1

    without_code = list(source)
    for opening, closing in opaque_spans:
        for index in range(opening, closing):
            if without_code[index] not in "\r\n":
                without_code[index] = " "
    visible_source = "".join(without_code)
    bracket_stack = []
    cursor = 0
    while cursor < len(visible_source):
        if visible_source[cursor] == "\\" and cursor + 1 < len(visible_source):
            cursor += 2
            continue
        if visible_source[cursor] == "[":
            bracket_stack.append(cursor)
        elif visible_source[cursor] == "]":
            if not bracket_stack:
                return "contains an unbalanced literal bracket"
            bracket_stack.pop()
            if cursor + 1 < len(visible_source) \
                    and visible_source[cursor + 1] == "(":
                return "contains malformed or ambiguous inline-link syntax"
        cursor += 1
    if bracket_stack:
        return "contains an unbalanced literal bracket"

    _removed, ambiguous_emphasis = _emphasis_render_plan(
        source, opaque_spans
    )
    if ambiguous_emphasis:
        return "contains an unclosed or ambiguous emphasis delimiter"
    return None


def text_without_invisible_format_characters(text):
    """Remove whitespace and default-ignorable format code points, without NFKC."""
    output = []
    for character in text or "":
        if character.isspace() or is_default_ignorable_character(character):
            continue
        output.append(character)
    return "".join(output)


def rendered_inline_text_has_visible_content(text):
    """Return whether rendered inline prose contains a visible code point."""
    return bool(text_without_invisible_format_characters(rendered_inline_text(text)))


def rendered_link_label_text_has_visible_content(text):
    """Return whether label source renders visibly inside link brackets."""
    return bool(
        text_without_invisible_format_characters(rendered_link_label_text(text))
    )


class _SpanIndex:
    """A read-only overlap index for normalized half-open source ranges."""

    def __init__(self, spans=()):
        merged = []
        for start, end in sorted(spans):
            if start >= end:
                continue
            if merged and start < merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        self.spans = tuple(merged)
        self.starts = tuple(start for start, _end in merged)

    def overlaps(self, start, end):
        if start >= end or not self.spans:
            return False
        index = bisect.bisect_right(self.starts, start) - 1
        if index >= 0 and self.spans[index][1] > start:
            return True
        index += 1
        return index < len(self.spans) and self.spans[index][0] < end

    def contains(self, start, end):
        if start >= end or not self.spans:
            return False
        index = bisect.bisect_right(self.starts, start) - 1
        return index >= 0 and self.spans[index][1] >= end


def _markdown_angle_destination_spans(source):
    """Return angle destinations that are syntax, not raw HTML or autolinks."""
    spans = []
    for pattern in (MARKDOWN_LINK_RE, MARKDOWN_IMAGE_RE):
        for matched in pattern.finditer(source or ""):
            if matched.group("angle") is not None:
                spans.append(
                    (matched.start("angle") - 1, matched.end("angle") + 1)
                )
    return tuple(spans)


def contains_raw_html(text):
    """Conservatively detect raw HTML outside fenced and inline code.

    Callers that require a closed Markdown shape can fail closed on this signal
    instead of trying to reproduce a browser's handling of arbitrary tags and
    attributes.
    """
    clean = strip_block_aware_inline_code(
        _semantic_text(text or "", preserve_visible_html=True)
    )
    angle_destinations = _SpanIndex(_markdown_angle_destination_spans(clean))
    return any(
        not angle_destinations.contains(matched.start(), matched.end())
        for matched in RAW_HTML_TOKEN_RE.finditer(clean)
    )


def contains_html_comment_outside_inline_code(text):
    """Detect an HTML-comment opener without cross-block code-span masking."""
    return "<!--" in strip_block_aware_inline_code(text or "")


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


def inline_raw_html_spans(text):
    """Return conservative inline raw-HTML ranges in one bounded source pass.

    Once a token owns source through its closing delimiter, later token-looking text
    inside that range cannot start another independent tag. A malformed token owns
    the rest of its source line. This keeps adversarial opener floods linear while
    preserving quoted ``>`` characters in valid tags.
    """
    source = text or ""
    spans = []
    covered_until = 0
    for token in RAW_HTML_TOKEN_RE.finditer(source):
        start = token.start()
        if start < covered_until:
            continue
        if source.startswith("<!--", start):
            end = source.find("-->", start + 4)
            if end >= 0:
                covered_until = end + 3
                spans.append((start, covered_until))
            else:
                covered_until = len(source)
            continue
        cursor = token.end()
        quote = None
        while cursor < len(source):
            character = source[cursor]
            if quote:
                if character == quote:
                    quote = None
            elif character in "\"'":
                quote = character
            elif character == ">":
                covered_until = cursor + 1
                spans.append((start, covered_until))
                break
            elif character in "\r\n":
                covered_until = cursor + 1
                break
            cursor += 1
        else:
            covered_until = len(source)
    return tuple(spans)


def normalized_reference_label(label):
    """Apply CommonMark's case-insensitive, whitespace-collapsing label match."""
    unescaped = re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", label)
    return " ".join(unescaped.split()).casefold()


def _parse_reference_definition_rest(rest):
    """Return a destination when the rest is one complete definition value."""
    source = (rest or "").strip()
    if not source:
        return None
    if source.startswith("<"):
        closing = source.find(">", 1)
        if closing < 0 or "<" in source[1:closing] or "\n" in source[1:closing]:
            return None
        destination = source[1:closing]
        remainder = source[closing + 1:].strip()
    else:
        cursor = 0
        depth = 0
        while cursor < len(source) and not source[cursor].isspace():
            character = source[cursor]
            if character == "\\" and cursor + 1 < len(source):
                cursor += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    return None
                depth -= 1
            cursor += 1
        if cursor == 0 or depth:
            return None
        destination = source[:cursor]
        remainder = source[cursor:].strip()
    if remainder and not re.fullmatch(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\((?:\\.|[^)\\])*\)',
        remainder,
    ):
        return None
    return rendered_link_destination(destination)


def _reference_definitions(clean):
    """Return first-wins definitions, all definitions, duplicate labels and spans."""
    first = {}
    definitions = []
    duplicates = set()
    spans = []
    offset = 0
    for line in clean.splitlines(keepends=True):
        candidate = line.rstrip("\r\n")
        matched = REFERENCE_DEFINITION_RE.fullmatch(candidate)
        if matched:
            destination = _parse_reference_definition_rest(matched.group("rest"))
            label = matched.group("label")
            normalized = normalized_reference_label(label)
            if destination is not None and normalized:
                definition = MarkdownReferenceDefinition(
                    label, normalized, destination, offset, offset + len(candidate)
                )
                definitions.append(definition)
                spans.append((definition.start, definition.end))
                if normalized in first:
                    duplicates.add(normalized)
                else:
                    first[normalized] = definition
        offset += len(line)
    return first, tuple(definitions), tuple(sorted(duplicates)), tuple(spans)


def _inline_candidate_overlaps_nonlabel_source(matched, occupied):
    """Return whether occupied syntax crosses an inline link outside its label."""
    return (
        occupied.overlaps(matched.start(), matched.start("label"))
        or occupied.overlaps(matched.end("label"), matched.end())
    )


def visible_markdown_reference_resolution(text):
    """Resolve visible inline and reference-style Markdown links and images.

    Fenced code, indented code, raw HTML, and inline code cannot provide either a
    rendered reference or a definition. Reference labels match case-insensitively,
    collapse whitespace, and use the first definition as CommonMark does. Explicit
    full, collapsed, and shortcut constructs without a definition are reported as
    unresolved or ambiguous so strict callers can fail closed.
    """
    clean = strip_indented_code(semantic_text(text or ""))
    opaque_segments = _inline_opaque_segments(clean, include_extended=False)
    code_spans = tuple(
        (opening, closing)
        for opening, closing, kind, _label, _destination in opaque_segments
        if kind == "code"
    )
    first, definitions, duplicates, definition_spans = _reference_definitions(clean)
    markdown_angle_destination_spans = _markdown_angle_destination_spans(clean)
    markdown_angle_destination_index = _SpanIndex(
        markdown_angle_destination_spans
    )
    raw_html_spans = [
        span
        for span in inline_raw_html_spans(clean)
        if not markdown_angle_destination_index.contains(span[0], span[1])
    ]
    initial_spans = (
        list(code_spans)
        + list(definition_spans)
        + raw_html_spans
    )
    initial_occupied = _SpanIndex(initial_spans)
    references = []
    unresolved = []
    autolink_candidates = [
        (opening, closing, label, destination)
        for opening, closing, kind, label, destination in opaque_segments
        if kind == "autolink"
        and not initial_occupied.overlaps(opening, closing)
    ]
    autolink_spans = [
        (opening, closing)
        for opening, closing, _label, _destination in autolink_candidates
    ]
    autolink_index = _SpanIndex(autolink_spans)

    accepted_inline_spans = []
    for matched in MARKDOWN_LINK_RE.finditer(clean):
        if autolink_index.overlaps(
            matched.start("label"), matched.end("label")
        ):
            continue
        if _inline_candidate_overlaps_nonlabel_source(
            matched, initial_occupied
        ):
            continue
        destination = matched.group("angle")
        if destination is None:
            destination = matched.group("bare")
        destination = rendered_link_destination(destination)
        references.append(VisibleMarkdownReference(
            matched.group("label"), destination, False, "inline",
            matched.start(), matched.end(),
        ))
        accepted_inline_spans.append((matched.start(), matched.end()))

    link_occupied = _SpanIndex(initial_spans + accepted_inline_spans)
    for matched in MARKDOWN_IMAGE_RE.finditer(clean):
        if autolink_index.contains(matched.start(), matched.end()):
            continue
        if _inline_candidate_overlaps_nonlabel_source(
            matched, link_occupied
        ):
            continue
        destination = matched.group("angle")
        if destination is None:
            destination = matched.group("bare")
        destination = rendered_link_destination(destination)
        references.append(VisibleMarkdownReference(
            matched.group("label"), destination, True, "inline",
            matched.start(), matched.end(),
        ))
        accepted_inline_spans.append((matched.start(), matched.end()))

    inline_occupied = _SpanIndex(initial_spans + accepted_inline_spans)
    accepted_autolink_spans = []
    for opening, closing, label, destination in autolink_candidates:
        if inline_occupied.overlaps(opening, closing):
            continue
        references.append(VisibleMarkdownReference(
            label, destination, False, "autolink", opening, closing,
        ))
        accepted_autolink_spans.append((opening, closing))

    occupied_spans = (
        initial_spans + accepted_inline_spans + accepted_autolink_spans
    )
    occupied = _SpanIndex(occupied_spans)
    accepted_reference_spans = []
    resolved_reference_spans = []
    for matched in REFERENCE_USE_RE.finditer(clean):
        if occupied.overlaps(matched.start(), matched.end()):
            continue
        label = matched.group("label") or matched.group("text")
        normalized = normalized_reference_label(label)
        definition = first.get(normalized)
        if definition is None:
            unresolved.append(clean[matched.start():matched.end()])
        else:
            references.append(VisibleMarkdownReference(
                matched.group("text"), definition.destination,
                bool(matched.group("image")),
                "collapsed" if not matched.group("label") else "full",
                matched.start(), matched.end(), definition.start,
            ))
            resolved_reference_spans.append((matched.start(), matched.end()))
        accepted_reference_spans.append((matched.start(), matched.end()))

    occupied = _SpanIndex(occupied_spans + accepted_reference_spans)
    resolved_shortcut_spans = []
    for matched in REFERENCE_SHORTCUT_RE.finditer(clean):
        if occupied.overlaps(matched.start(), matched.end()):
            continue
        normalized = normalized_reference_label(matched.group("label"))
        definition = first.get(normalized)
        if definition is None:
            unresolved.append(clean[matched.start():matched.end()])
            continue
        references.append(VisibleMarkdownReference(
            matched.group("label"), definition.destination,
            bool(matched.group("image")), "shortcut",
            matched.start(), matched.end(), definition.start,
        ))
        resolved_shortcut_spans.append((matched.start(), matched.end()))

    extended_ignored = _merged_source_spans(
        initial_spans
        + accepted_inline_spans
        + accepted_autolink_spans
        + resolved_reference_spans
        + resolved_shortcut_spans
    )
    extended_urls = tuple(
        _gfm_extended_url_candidates(clean, extended_ignored)
    )
    for opening, closing, label, destination in extended_urls:
        references.append(VisibleMarkdownReference(
            label, destination, False, "extended-autolink", opening, closing,
        ))
    extended_email_ignored = _merged_source_spans(
        list(extended_ignored)
        + [(opening, closing) for opening, closing, *_rest in extended_urls]
    )
    for opening, closing, label, destination \
            in _gfm_extended_email_candidates(clean, extended_email_ignored):
        references.append(VisibleMarkdownReference(
            label, destination, False, "extended-autolink", opening, closing,
        ))

    references.sort(key=lambda reference: reference.start)
    return MarkdownReferenceResolution(
        tuple(references), definitions, duplicates, tuple(unresolved)
    )


def visible_markdown_reference_destinations(text):
    """Return destinations for all visible links and images in source order."""
    return [
        reference.destination
        for reference in visible_markdown_reference_resolution(text).references
    ]


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
    """Replace rendered link syntax, leaving link-like code and images untouched."""
    clean = strip_indented_code(semantic_text(text))
    matches = [
        reference
        for reference in visible_markdown_reference_resolution(text).references
        if not reference.is_image
    ]
    output = []
    cursor = 0
    for matched in matches:
        output.extend((clean[cursor:matched.start], matched.label))
        cursor = matched.end
    output.append(clean[cursor:])
    return "".join(output)


def markdown_link_destinations(text):
    """Return visible CommonMark link destinations.

    The angle-bracket form intentionally supports repository paths containing spaces.
    """
    return [
        reference.destination
        for reference in visible_markdown_reference_resolution(text).references
        if not reference.is_image
    ]


def markdown_links(text):
    """Return visible CommonMark link `(label, destination)` pairs."""
    return [
        (reference.label, reference.destination)
        for reference in visible_markdown_reference_resolution(text).references
        if not reference.is_image
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
