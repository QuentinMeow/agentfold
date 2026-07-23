#!/usr/bin/env python3
"""Require external human-action sections to project live queue items."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

AUTOMATION = Path(__file__).resolve().parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from markdown_semantics import (
    MARKDOWN_LINK_RE,
    markdown_links,
    normalized_action_tokens,
    rendered_human_text,
    semantic_text,
    strip_indented_code,
    strip_inline_code,
)

REPO = Path(__file__).resolve().parents[1]
QUEUE_ITEM_RE = re.compile(
    r"^message-queue/needs-human/[a-z0-9][a-z0-9-]*/"
    r"(?:blocking|future-blocking|non-blocking)-"
    r"[a-z0-9][a-z0-9-]*\.md$"
)
QUEUE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"message-queue/(?:needs-human|needs-agent)/[a-z0-9][a-z0-9-]*/"
    r"(?:blocking|future-blocking|non-blocking)-"
    r"[a-z0-9][a-z0-9-]*\.md"
    r"(?![A-Za-z0-9_.-])"
)
TASK_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
HEADING_RE = re.compile(
    r"^(?P<quote>(?:>[ \t]?)*)(?P<level>#{1,6})[ \t]+"
    r"(?P<title>.*?)[ \t]*#*[ \t]*$"
)
LIST_ITEM_RE = re.compile(
    r"^(?P<indent>[ ]{0,3})(?P<marker>[-+*]|\d+[.)])"
    r"(?P<spacing>[ \t]+)"
)
NO_ACTION_TEXT = "No human action requested."
CLEAR_ACTION_VERB_PATTERN = (
    r"(?:accept|approve|authorize|choose|confirm|consider|"
    r"decide|deploy|(?:give|provide)"
    r"(?:[ \t]+(?:me|our|us|your))?[ \t]+feedback|inspect|"
    r"(?:add|leave)(?:[ \t]+(?:a|your))?[ \t]+comment|merge|"
    r"release|review|select|"
    r"sign[ \t]+off|tell|verify|vote)"
)
LET_KNOW_PATTERN = r"let[ \t]+(?:me|us)[ \t]+know"
KEEP_POSTED_PATTERN = (
    r"keep[ \t]+(?:me|us)[ \t]+(?:informed|posted|updated)"
)
REQUEST_ACTION_VERB_PATTERN = (
    r"(?:benchmark|check|fix|reproduce|run|test|triage|update)"
)
ACTION_VERB_PATTERN = (
    rf"(?:{CLEAR_ACTION_VERB_PATTERN}|{LET_KNOW_PATTERN}|"
    rf"{KEEP_POSTED_PATTERN}|"
    rf"{REQUEST_ACTION_VERB_PATTERN}|answer|comment|reply|respond)"
)
DIRECTIVE_ACTION_PATTERN = (
    rf"(?:{CLEAR_ACTION_VERB_PATTERN}"
    rf"|{LET_KNOW_PATTERN}"
    rf"|{KEEP_POSTED_PATTERN}"
    r"|answer(?="
    r"[.!?;,:)]|$|[ \t]+(?:how|that|the|this|what|when|whether|which|"
    r"who|why|with)\b)"
    r"|(?:reply|respond)(?="
    r"[.!?;,:)]|$|[ \t]+(?:after|before|below|by|here|if|in|no|now|"
    r"on|promptly|to|tomorrow|via|when|with|yes)\b)"
    r"|comment(?="
    r"[.!?;,:)]|$|[ \t]+(?:about|after|before|below|here|if|now|on|"
    r"promptly|tomorrow|when)\b))"
)
DIRECTIVE_PREFIX_PATTERN = r"(?:(?:and|also|then)[ \t]+)*"
OPEN_COMMAND_WORD_PATTERN = r"[A-Za-z][A-Za-z'-]*"
PLEASE_COMMAND_PATTERN = (
    rf"{DIRECTIVE_PREFIX_PATTERN}please"
    r"(?:[ \t]*,[ \t]*|[ \t]+)"
    rf"{DIRECTIVE_PREFIX_PATTERN}"
    rf"{OPEN_COMMAND_WORD_PATTERN}"
)
HUMAN_ACTION_NOUN_PATTERN = (
    r"(?:approval|authorization|choice|clarification|comments?|confirmation|"
    r"decision|feedback|input|repl(?:y|ies)|responses?|review|"
    r"sign[ -]?off|verification|vote)"
)
HUMAN_ACTOR_PATTERN = r"(?:human|maintainer|owner|reviewer)s?"
ACTION_SOURCE_PATTERN = (
    rf"(?:you|(?:(?:a|an|the)[ \t]+)?"
    r"(?:(?:authorized|code|designated|lead|project|responsible|senior)"
    r"[ \t]+){0,2}"
    rf"{HUMAN_ACTOR_PATTERN})"
)
ACTION_VERB_RE = re.compile(
    rf"\b{ACTION_VERB_PATTERN}\b",
    re.I,
)
DIRECTIVE_RE = re.compile(
    r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{PLEASE_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
ADDITIONAL_DIRECTIVE_RE = re.compile(
    r"(?:^|[,.!;:—][ \t]+)"
    r"(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{PLEASE_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
TODO_RE = re.compile(r"\bTODO\b", re.I)
EMPHASIS_MARKER_RE = re.compile(r"(?<!\\)(?:\*{1,3}|_{1,3})")
FULL_OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$")
QUEUE_ACTION_RE = re.compile(
    r"^\*\*Action:\*\*[ \t]*(?P<action>\S(?:.*\S)?)[ \t]*$",
    re.M,
)
DECLARATIVE_ACTION_RE = re.compile(
    r"\b"
    r"(?:(?:explicit|additional|separate|formal|manual)[ \t]+)*"
    rf"(?:(?:your|{HUMAN_ACTOR_PATTERN}(?:['’]s)?)[ \t]+)?"
    rf"{HUMAN_ACTION_NOUN_PATTERN}"
    rf"(?:[ \t]+(?:from|by)[ \t]+{ACTION_SOURCE_PATTERN})?"
    r"[ \t]+"
    r"(?:(?:is|are|remains?|will[ \t]+be|must[ \t]+be)[ \t]+)?"
    r"(?:(?:also|now|still)[ \t]+)?"
    r"(?:(?:currently)[ \t]+)?"
    r"(?P<negation>not[ \t]+)?"
    r"(?:awaited|needed|outstanding|pending|requested|required)\b",
    re.I,
)
HUMAN_REQUEST_RE = re.compile(
    rf"\b{HUMAN_ACTOR_PATTERN}\b"
    r"[ \t]+(?:is|are)[ \t]+"
    r"(?P<negation>not[ \t]+)?(?:requested|required)[ \t]+to[ \t]+"
    rf"{ACTION_VERB_PATTERN}\b",
    re.I,
)
FIRST_PERSON_REQUEST_RE = re.compile(
    r"\b(?:we|i)[ \t]+"
    r"(?P<negation>do[ \t]+not[ \t]+)?"
    r"(?:await|need|request|require)[ \t]+"
    rf"(?:(?:your|{HUMAN_ACTOR_PATTERN}(?:['’]s)?)[ \t]+)?"
    rf"{HUMAN_ACTION_NOUN_PATTERN}"
    rf"(?:[ \t]+(?:from|by)[ \t]+{ACTION_SOURCE_PATTERN})?\b",
    re.I,
)
ACTOR_OBLIGATION_RE = re.compile(
    rf"\b(?:you|{HUMAN_ACTOR_PATTERN})\b[ \t]+"
    r"(?P<negation>(?:(?:do|does|is|are)[ \t]+not)[ \t]+)?"
    r"(?:must|needs?[ \t]+to|(?:is|are)[ \t]+requested[ \t]+to|"
    r"requested[ \t]+to)[ \t]+"
    rf"{ACTION_VERB_PATTERN}\b",
    re.I,
)
FIRST_PERSON_VERB_REQUEST_RE = re.compile(
    r"\b(?:we|i)[ \t]+"
    r"(?P<negation>do[ \t]+not[ \t]+)?"
    r"(?:ask|need|request|require)[ \t]+(?:that[ \t]+)?"
    rf"{ACTION_SOURCE_PATTERN}[ \t]+(?:to[ \t]+)?"
    rf"{OPEN_COMMAND_WORD_PATTERN}\b",
    re.I,
)
MODAL_ACTOR_REQUEST_RE = re.compile(
    r"\b(?:can|could|will|would)[ \t]+"
    rf"{ACTION_SOURCE_PATTERN}[ \t]+"
    r"(?:please[ \t]+)?"
    r"(?P<negation>)(?:(?:not|never)[ \t]+)?"
    rf"{OPEN_COMMAND_WORD_PATTERN}\b",
    re.I,
)
COURTESY_ACTION_NOUN_PATTERN = r"(?:feedback|input|review)"
FIRST_PERSON_COURTESY_REQUEST_RE = re.compile(
    r"\b(?:we|i)"
    r"(?:"
    r"(?P<negation>"
    r"(?:['’]d|[ \t]+would)[ \t]+not"
    r"|[ \t]+wouldn['’]t"
    r")"
    r"|(?:['’]d|[ \t]+would)"
    r")"
    r"[ \t]+(?:appreciate|value|welcome)[ \t]+"
    r"(?:(?:a|any|some|the|your)[ \t]+)?"
    rf"{COURTESY_ACTION_NOUN_PATTERN}\b",
    re.I,
)
PASSIVE_COURTESY_REQUEST_RE = re.compile(
    r"\b(?:(?:any|some|your)[ \t]+)?"
    rf"{COURTESY_ACTION_NOUN_PATTERN}[ \t]+"
    r"(?:"
    r"(?P<negation>"
    r"(?:would[ \t]+not|wouldn['’]t)[ \t]+be"
    r")"
    r"|would[ \t]+be"
    r")"
    r"[ \t]+(?:appreciated|valued|welcome)\b",
    re.I,
)
GENERIC_ACTION_LABELS = {
    ("action", "request"),
    ("human", "action"),
    ("queue", "action"),
    ("requested", "action"),
}
LEAF_GENERIC_ACTION_LABELS = {
    "clarifications": {
        ("clarification",),
        ("clarification", "request"),
        ("human", "clarification"),
    },
    "decisions": {
        ("decision",),
        ("decision", "request"),
        ("human", "decision"),
    },
    "reviews": {
        ("human", "review"),
        ("review",),
        ("review", "request"),
    },
}


def normalized_title(value):
    return " ".join((value or "").strip().casefold().split())


def quote_depth(line):
    matched = re.match(r"^(?P<quote>(?:>[ \t]?)*)", line)
    return matched.group("quote").count(">") if matched else 0


def strip_quote(line, depth):
    cursor = line
    for _ in range(depth):
        matched = re.match(r"^>[ \t]?", cursor)
        if not matched:
            break
        cursor = cursor[matched.end():]
    return cursor


def action_section_spans(text, titles):
    """Return visible configured ATX action sections as `(start, end, body)`."""
    lines = semantic_text(text).splitlines()
    wanted = {normalized_title(title) for title in titles}
    sections = []
    for index, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if not heading or normalized_title(heading.group("title")) not in wanted:
            continue
        depth = heading.group("quote").count(">")
        level = len(heading.group("level"))
        body = []
        for following in lines[index + 1:]:
            if following.strip() and quote_depth(following) < depth:
                break
            visible = strip_quote(following, depth)
            next_heading = HEADING_RE.match(following)
            if next_heading \
                    and next_heading.group("quote").count(">") <= depth \
                    and len(next_heading.group("level")) <= level:
                break
            body.append(visible)
        sections.append((index, index + len(body) + 1, "\n".join(body).strip()))
    return sections


def action_sections(text, titles):
    """Return visible bodies of every configured ATX action heading."""
    return [body for _start, _end, body in action_section_spans(text, titles)]


def visible_outside_action_sections(text, titles):
    """Return human-readable prose outside every configured action section."""
    lines = rendered_human_text(text).splitlines()
    for start, end, _body in action_section_spans(text, titles):
        for index in range(start, min(end, len(lines))):
            lines[index] = ""
    return "\n".join(lines)


def rendered_action_section_body(text, start, end):
    """Return human-readable section prose without granting HTML structure."""
    structural_lines = semantic_text(text).splitlines()
    rendered_lines = rendered_human_text(text).splitlines()
    heading = (
        HEADING_RE.match(structural_lines[start])
        if start < len(structural_lines)
        else None
    )
    depth = heading.group("quote").count(">") if heading else 0
    return "\n".join(
        strip_quote(rendered_lines[index], depth)
        for index in range(start + 1, min(end, len(rendered_lines)))
    ).strip()


def indentation_width(value):
    """Return leading indentation in CommonMark columns."""
    width = 0
    for character in value:
        if character == " ":
            width += 1
        elif character == "\t":
            width += 4 - (width % 4)
        else:
            break
    return width


def section_entries(body):
    """Return strict top-level actions and any content outside their list.

    Wrapped prose and nested lists must be indented under their owning action. This
    intentionally rejects a second, unlisted ask after a linked list item.
    """
    lines = body.splitlines()
    entries = []
    current = []
    current_content_indent = None
    top_level_indent = None
    outside = []
    for line in lines:
        item = LIST_ITEM_RE.match(line)
        item_indent = (
            indentation_width(item.group("indent")) if item else None
        )
        if item and (
            top_level_indent is None or item_indent == top_level_indent
        ):
            if current:
                entries.append("\n".join(current).strip())
            if top_level_indent is None:
                top_level_indent = item_indent
            current = [line]
            current_content_indent = (
                item_indent
                + len(item.group("marker"))
                + indentation_width(item.group("spacing"))
            )
        elif not line.strip():
            if current:
                current.append(line)
        elif current and indentation_width(line) >= current_content_indent:
            current.append(line)
        else:
            outside.append(line)
    if current:
        entries.append("\n".join(current).strip())
    return entries, "\n".join(outside).strip()


def prose_without_links(entry):
    """Return visible prose outside Markdown links and code examples."""
    clean = strip_indented_code(strip_inline_code(semantic_text(entry)))
    return MARKDOWN_LINK_RE.sub("", clean)


def strip_prose_quote_markers(text):
    """Remove CommonMark quote prefixes before classifying rendered prose."""
    output = []
    for line in (text or "").split("\n"):
        while True:
            marker = re.match(r"^[ ]{0,3}>[ \t]?", line)
            if not marker:
                break
            line = line[marker.end():]
        output.append(line)
    return "\n".join(output)


def action_prose_variants(text):
    """Return source lines and their rendered soft-line-break equivalent."""
    source = text or ""
    softened = re.sub(r"(?<!\n)\n(?!\n)", " ", source)
    return (source,) if softened == source else (source, softened)


def strip_action_emphasis(text):
    """Remove visible Markdown emphasis delimiters before ask classification."""
    return EMPHASIS_MARKER_RE.sub("", text or "")


def declarative_action_request(clean):
    """Recognize narrow declarative/courtesy requests, excluding local negation."""
    for pattern in (
        DECLARATIVE_ACTION_RE,
        HUMAN_REQUEST_RE,
        FIRST_PERSON_REQUEST_RE,
        ACTOR_OBLIGATION_RE,
        FIRST_PERSON_VERB_REQUEST_RE,
        MODAL_ACTOR_REQUEST_RE,
        FIRST_PERSON_COURTESY_REQUEST_RE,
        PASSIVE_COURTESY_REQUEST_RE,
    ):
        for matched in pattern.finditer(clean):
            if matched.group("negation"):
                continue
            prefix = clean[max(0, matched.start() - 64):matched.start()]
            if re.search(
                r"\b(?:no|without)[ \t]+"
                r"(?:[A-Za-z][A-Za-z'-]*[ \t]+){0,4}$",
                prefix,
                re.I,
            ):
                continue
            return True
    return False


def action_like_clean_text(clean):
    """Classify already-visible prose with the deterministic action grammar."""
    if "?" in clean or TODO_RE.search(clean):
        return True
    return any(
        DIRECTIVE_RE.search(variant)
        or ADDITIONAL_DIRECTIVE_RE.search(variant)
        or declarative_action_request(variant)
        for variant in action_prose_variants(clean)
    )


def action_like_prose(text):
    """Recognize deterministic human-action grammar in visible Markdown prose.

    A fragment is action-like when it contains a question mark, a standalone TODO,
    an authority verb in command position at the start of a line/list item, or a
    narrow present-tense declaration that human approval/review/confirmation is
    requested or required. Markdown destinations and code are not prose; callers
    inspect link labels separately. Ordinary descriptive prose remains accepted.
    """
    clean = strip_prose_quote_markers(semantic_text(text))
    clean = strip_indented_code(strip_inline_code(clean))
    clean = MARKDOWN_LINK_RE.sub(
        lambda matched: matched.group("label"),
        clean,
    )
    return action_like_clean_text(strip_action_emphasis(clean))


def action_like_plain_prose(text):
    """Recognize actions in provider text that has no Markdown semantics."""
    clean = strip_prose_quote_markers(text or "")
    clean = "\n".join(
        re.sub(r"^[^\w]+", "", line)
        for line in clean.split("\n")
    )
    return action_like_clean_text(strip_action_emphasis(clean))


def link_label_action_count(label):
    """Count authority actions in a short link label conservatively."""
    verbs = len(ACTION_VERB_RE.findall(label or ""))
    questions = (label or "").count("?")
    todos = len(TODO_RE.findall(label or ""))
    return max(verbs, questions, todos)


def additional_action_like_prose(text):
    """Recognize a second action in prose surrounding an owning queue link."""
    clean = strip_prose_quote_markers(semantic_text(text))
    clean = strip_indented_code(strip_inline_code(clean))
    clean = strip_action_emphasis(clean)
    return bool(
        "?" in clean
        or TODO_RE.search(clean)
        or any(
            ADDITIONAL_DIRECTIVE_RE.search(variant)
            or declarative_action_request(variant)
            for variant in action_prose_variants(clean)
        )
    )


def label_projects_action(label, canonical_action, queue_path):
    """Bind a projected label to one Action without fuzzy semantic borrowing.

    A small neutral vocabulary remains usable per queue leaf. Every descriptive
    alternative must be an exact leading token prefix of canonical Action, so it
    cannot append an unrelated subject or stronger request.
    """
    label_tokens = normalized_action_tokens(label)
    action_tokens = normalized_action_tokens(canonical_action)
    if not label_tokens or not action_tokens:
        return False
    leaf = Path(queue_path).parts[2]
    generic_labels = GENERIC_ACTION_LABELS | LEAF_GENERIC_ACTION_LABELS.get(
        leaf, set()
    )
    if label_tokens in generic_labels:
        return True
    if label_tokens == action_tokens:
        return True
    return (
        len(ACTION_VERB_RE.findall(label or "")) == 1
        and len(label_tokens) <= len(action_tokens)
        and label_tokens == action_tokens[:len(label_tokens)]
    )


def normalized_url_prefix(value, candidate_revision=None):
    """Validate and normalize one explicitly trusted HTTPS repository prefix."""
    parsed = urlsplit((value or "").strip())
    if parsed.scheme.casefold() != "https" or not parsed.netloc:
        raise ValueError("allowed URL prefixes must be absolute HTTPS URLs")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("allowed URL prefixes cannot contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("allowed URL prefixes cannot contain a query or fragment")
    path = unquote(parsed.path).rstrip("/")
    if ".." in Path(path).parts:
        raise ValueError("allowed URL prefixes cannot contain `..` path segments")
    if candidate_revision is not None and candidate_revision.casefold() not in {
        part.casefold() for part in Path(path).parts
    }:
        raise ValueError(
            "allowed URL prefixes must contain the exact candidate revision"
        )
    return parsed.scheme.casefold(), parsed.netloc.casefold(), path


def queue_path_from_destination(destination, allowed_url_prefixes=()):
    """Resolve one unambiguous canonical queue path from a link destination."""
    destination = (destination or "").strip()
    parsed = urlsplit(destination)
    candidates = []
    if parsed.scheme:
        if (
            parsed.scheme.casefold() != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
        ):
            return None
        path = unquote(parsed.path)
        if ".." in Path(path).parts:
            return None
        remainders = [
            path[len(prefix_path) + 1:]
            for scheme, netloc, prefix_path in allowed_url_prefixes
            if parsed.scheme.casefold() == scheme
            and parsed.netloc.casefold() == netloc
            and path.startswith(prefix_path + "/")
        ]
        if len(remainders) != 1:
            return None
        candidates = remainders
    else:
        if parsed.netloc:
            return None
        raw = unquote(destination.split("#", 1)[0].split("?", 1)[0])
        while raw.startswith("./"):
            raw = raw[2:]
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts:
            return None
        candidates = [path.as_posix()]
    valid = [candidate for candidate in candidates if QUEUE_ITEM_RE.fullmatch(candidate)]
    return valid[0] if len(valid) == 1 and len(candidates) == 1 else None


def git_output(args, repo=REPO):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or "could not inspect the Git candidate"
        )
    return result.stdout


def candidate_revision_oid(value, repo=REPO):
    """Resolve one explicitly full commit object id without replacement refs."""
    revision = (value or "").strip()
    if not FULL_OBJECT_ID_RE.fullmatch(revision):
        raise ValueError("candidate revision must be one full Git object id")
    output = git_output(
        ["--no-replace-objects", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        repo=repo,
    ).decode("ascii", errors="replace").strip()
    if output.casefold() != revision.casefold():
        raise ValueError("candidate revision must name its exact commit object")
    return output


def candidate_record(path, repo=REPO, candidate_revision=None):
    if candidate_revision is None:
        output = git_output(["ls-files", "--stage", "-z", "--", path], repo=repo)
    else:
        output = git_output(
            [
                "--no-replace-objects", "ls-tree", "-z",
                candidate_revision, "--", path,
            ],
            repo=repo,
        )
    records = [record for record in output.split(b"\0") if record]
    if len(records) != 1:
        return None
    metadata, separator, encoded_path = records[0].partition(b"\t")
    parts = metadata.decode("ascii", errors="replace").split()
    if not (
        separator
        and encoded_path.decode("utf-8", errors="surrogateescape") == path
        and len(parts) == 3
    ):
        return None
    if candidate_revision is not None and parts[1] != "blob":
        return None
    return parts


def tracked_regular_file(path, repo=REPO, candidate_revision=None):
    parts = candidate_record(
        path, repo=repo, candidate_revision=candidate_revision
    )
    if not parts or parts[0] not in ("100644", "100755"):
        return False
    if candidate_revision is None and parts[2] != "0":
        return False
    object_id = parts[2] if candidate_revision is not None else parts[1]
    size = git_output(
        ["--no-replace-objects", "cat-file", "-s", object_id],
        repo=repo,
    )
    try:
        return int(size.strip()) > 0
    except ValueError as error:
        raise RuntimeError("Git returned an invalid candidate object size") from error


def candidate_paths(prefix, repo=REPO, candidate_revision=None):
    if candidate_revision is None:
        output = git_output(["ls-files", "-z", "--", prefix], repo=repo)
    else:
        output = git_output(
            [
                "--no-replace-objects", "ls-tree", "-r", "--name-only", "-z",
                candidate_revision, "--", prefix,
            ],
            repo=repo,
        )
    return [
        record.decode("utf-8", errors="surrogateescape")
        for record in output.split(b"\0")
        if record
    ]


def live_human_queue_paths(repo=REPO, candidate_revision=None):
    return {
        path
        for path in candidate_paths(
            "message-queue/needs-human",
            repo=repo,
            candidate_revision=candidate_revision,
        )
        if QUEUE_ITEM_RE.fullmatch(path)
        and tracked_regular_file(
            path, repo=repo, candidate_revision=candidate_revision
        )
    }


def normalized_task_id(value):
    task_id = (value or "").strip()
    if task_id.startswith("task/"):
        task_id = task_id[len("task/"):]
    if not TASK_ID_RE.fullmatch(task_id):
        raise ValueError(
            "task id must be YYYY-MM-DD-kebab-slug or task/<that-id>"
        )
    return task_id


def candidate_text(path, repo=REPO, candidate_revision=None):
    object_name = f":{path}" if candidate_revision is None \
        else f"{candidate_revision}:{path}"
    output = git_output(
        ["--no-replace-objects", "show", object_name],
        repo=repo,
    )
    try:
        return output.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"`{path}` is not valid UTF-8") from error


def canonical_queue_action(path, repo=REPO, candidate_revision=None):
    """Return the queue item's single non-empty canonical Action, if present."""
    matches = QUEUE_ACTION_RE.findall(
        semantic_text(
            candidate_text(
                path,
                repo=repo,
                candidate_revision=candidate_revision,
            )
        )
    )
    return matches[0].strip() if len(matches) == 1 else None


def task_human_queue_paths(task_id, repo=REPO, candidate_revision=None):
    task_id = normalized_task_id(task_id)
    task_paths = [
        path for path in candidate_paths(
            "tasks", repo=repo, candidate_revision=candidate_revision
        )
        if Path(path).parts[:1] == ("tasks",)
        and len(Path(path).parts) == 4
        and Path(path).parts[2] == task_id
        and Path(path).parts[3] == "task.md"
        and tracked_regular_file(
            path, repo=repo, candidate_revision=candidate_revision
        )
    ]
    if len(task_paths) != 1:
        raise RuntimeError(
            f"expected one live task record for `{task_id}`, found {len(task_paths)}"
        )
    task_path = task_paths[0]
    matched = re.search(
        r"^\*\*Queue actions:\*\*[ \t]*(.*)$",
        candidate_text(
            task_path, repo=repo, candidate_revision=candidate_revision
        ),
        flags=re.M,
    )
    if not matched:
        raise RuntimeError(f"`{task_path}` has no Queue actions field")
    value = matched.group(1).strip()
    queue_paths = set(QUEUE_PATH_RE.findall(value))
    if value.casefold() == "none":
        return set()
    if not queue_paths:
        raise RuntimeError(f"`{task_path}` has an invalid Queue actions field")
    human_paths = {path for path in queue_paths if QUEUE_ITEM_RE.fullmatch(path)}
    non_live = sorted(
        path for path in human_paths
        if not tracked_regular_file(
            path, repo=repo, candidate_revision=candidate_revision
        )
    )
    if non_live:
        raise RuntimeError(
            f"`{task_path}` links non-live human queue item(s): "
            + ", ".join(non_live)
        )
    return human_paths


def required_human_queue_paths(
    task_id=None,
    repo=REPO,
    require_all_live=True,
    candidate_revision=None,
):
    if task_id is not None:
        return task_human_queue_paths(
            task_id, repo=repo, candidate_revision=candidate_revision
        )
    return (
        live_human_queue_paths(
            repo=repo, candidate_revision=candidate_revision
        )
        if require_all_live else set()
    )


def material_external_action_state(value):
    """Treat empty serialized containers as no assignment, without provider policy."""
    text = (value or "").strip()
    if not text:
        return False
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return True

    def material(candidate):
        if candidate is None:
            return False
        if isinstance(candidate, str):
            return bool(candidate.strip())
        if isinstance(candidate, bool):
            return candidate
        if isinstance(candidate, (int, float)):
            return candidate != 0
        if isinstance(candidate, list):
            return any(material(item) for item in candidate)
        if isinstance(candidate, dict):
            return any(material(item) for item in candidate.values())
        return True

    return material(parsed)


def projection_findings(
    text,
    titles,
    repo=REPO,
    allowed_url_prefixes=(),
    task_id=None,
    require_all_live=True,
    candidate_revision=None,
    external_actions=(),
    additional_prose=(),
):
    if candidate_revision is not None:
        candidate_revision = candidate_revision_oid(
            candidate_revision, repo=repo
        )
    if candidate_revision is None:
        if not (repo / "message-queue").exists():
            return []
    elif not candidate_paths(
            "message-queue",
            repo=repo,
            candidate_revision=candidate_revision,
    ):
        return []
    normalized_prefixes = tuple(
        normalized_url_prefix(
            prefix, candidate_revision=candidate_revision
        )
        for prefix in allowed_url_prefixes
    )
    required_paths = required_human_queue_paths(
        task_id=task_id,
        repo=repo,
        require_all_live=require_all_live,
        candidate_revision=candidate_revision,
    )
    section_spans = action_section_spans(text, titles)
    sections = [body for _start, _end, body in section_spans]
    rendered_sections = [
        rendered_action_section_body(text, start, end)
        for start, end, _body in section_spans
    ]
    findings = []
    for input_number, prose in enumerate(additional_prose, start=1):
        if action_like_plain_prose(prose):
            findings.append(
                f"additional prose input {input_number} contains an action-like "
                "question or directive outside the declared action section"
            )
    if not sections:
        findings.append(
            "missing a declared action section; add `What to review` with "
            f"queue-linked actions or exactly `{NO_ACTION_TEXT}`"
        )
        return findings
    has_external_actions = any(
        material_external_action_state(value) for value in external_actions
    )
    linked_paths = set()
    saw_entries = False
    saw_no_action = False
    invalid_projection = False
    outside_action_prose = visible_outside_action_sections(text, titles)
    if action_like_prose(outside_action_prose):
        invalid_projection = True
        findings.append(
            "visible action-like question or directive exists outside the "
            "declared action section"
        )
    for section_number, (body, rendered_body) in enumerate(
            zip(sections, rendered_sections), start=1):
        if not body:
            invalid_projection = True
            findings.append(f"action section {section_number} is empty")
            continue
        rendered_only_action = (
            additional_action_like_prose(prose_without_links(rendered_body))
            and not additional_action_like_prose(prose_without_links(body))
        )
        if rendered_only_action:
            invalid_projection = True
            findings.append(
                f"action section {section_number} contains an additional "
                "unlinked request in rendered HTML; put the single action in "
                "the queue-link label"
            )
        if body.strip() == NO_ACTION_TEXT:
            saw_no_action = True
            if required_paths:
                findings.append(
                    f"action section {section_number} claims no human action "
                    "but scoped live queue item(s) exist: "
                    + ", ".join(sorted(required_paths))
                )
            elif has_external_actions:
                findings.append(
                    f"action section {section_number} claims no human action "
                    "but externally assigned human-action state is non-empty; "
                    "project at least one live canonical queue link"
                )
            continue
        entries, outside = section_entries(body)
        if outside:
            invalid_projection = True
            findings.append(
                f"action section {section_number} contains content outside "
                "the top-level action list; make every action a list item and "
                "indent wrapped explanation under it"
            )
        if not entries:
            invalid_projection = True
            if not outside:
                findings.append(
                    f"action section {section_number} has no queue-linked action"
                )
            continue
        saw_entries = True
        for entry_number, entry in enumerate(entries, start=1):
            links = markdown_links(entry)
            queue_looking = [
                (label, destination)
                for label, destination in links
                if "message-queue/" in unquote(destination)
            ]
            paths = [
                queue_path_from_destination(
                    destination,
                    allowed_url_prefixes=normalized_prefixes,
                )
                for _label, destination in queue_looking
            ]
            if len(queue_looking) != 1 \
                    or any(path is None for path in paths):
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "must contain exactly one valid canonical needs-human queue link"
                )
                continue
            queue_label = queue_looking[0][0]
            if link_label_action_count(queue_label) > 1:
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "contains multiple actions in its queue-link label"
                )
                continue
            supporting_action_labels = [
                label for label, destination in links
                if destination != queue_looking[0][1]
                and link_label_action_count(label)
            ]
            if supporting_action_labels:
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "contains an action-like supporting link; every action needs "
                    "its own canonical queue link"
                )
                continue
            if additional_action_like_prose(prose_without_links(entry)):
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "contains an additional unlinked question or decision request; "
                    "put the single action in the queue-link label and keep "
                    "surrounding prose declarative"
                )
                continue
            dead = [
                path for path in paths
                if not tracked_regular_file(
                    path,
                    repo=repo,
                    candidate_revision=candidate_revision,
                )
            ]
            if dead:
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "links non-live queue item(s): " + ", ".join(dead)
                )
                continue
            queue_path = paths[0]
            canonical_action = canonical_queue_action(
                queue_path,
                repo=repo,
                candidate_revision=candidate_revision,
            )
            if canonical_action is None:
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    f"links `{queue_path}`, which must contain exactly one "
                    "non-empty canonical `Action` field"
                )
                continue
            if not label_projects_action(
                    queue_label, canonical_action, queue_path):
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "has a queue-link label that does not summarize the linked "
                    f"queue item's canonical `Action` in `{queue_path}`"
                )
                continue
            linked_paths.update(paths)
    if saw_no_action and saw_entries:
        invalid_projection = True
        findings.append(
            "a no-action acknowledgement cannot appear beside listed actions"
        )
    missing = sorted(required_paths - linked_paths)
    if missing and not saw_no_action and not invalid_projection:
        findings.append(
            "action sections omit scoped live queue item(s): " + ", ".join(missing)
        )
    return findings


def read_input(args):
    if args.from_env is not None:
        if args.from_env not in os.environ:
            raise ValueError(f"environment variable {args.from_env!r} is not set")
        return os.environ[args.from_env]
    if args.file == "-":
        return sys.stdin.read()
    try:
        return Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(str(error)) from error


def read_env_values(names):
    """Read explicitly named environment inputs without evaluating their contents."""
    values = []
    for name in names:
        if name not in os.environ:
            raise ValueError(f"environment variable {name!r} is not set")
        values.append(os.environ[name])
    return values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-env", metavar="NAME")
    source.add_argument("--file", metavar="PATH|-")
    parser.add_argument(
        "--action-section", action="append", required=True, metavar="TITLE"
    )
    parser.add_argument(
        "--allowed-url-prefix",
        action="append",
        default=[],
        metavar="HTTPS_URL",
        help="allow absolute queue links only below this repository URL prefix",
    )
    parser.add_argument(
        "--candidate-revision",
        metavar="FULL_OBJECT_ID",
        help="read queue and task state from this exact commit instead of the index",
    )
    parser.add_argument(
        "--external-action-env",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "require a queue-linked projection when any named external "
            "human-action state is non-empty"
        ),
    )
    parser.add_argument(
        "--additional-prose-env",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "reject action-like questions or directives in additional "
            "provider prose outside the declared action section"
        ),
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--task-id",
        metavar="ID|task/ID",
        help="scope required human queue links to one canonical task record",
    )
    scope.add_argument(
        "--branch",
        metavar="NAME",
        help="derive task scope from task/<id>; other branches stay unscoped",
    )
    parser.add_argument("--label", default="external projection")
    args = parser.parse_args(argv)
    try:
        text = read_input(args)
        external_actions = read_env_values(args.external_action_env)
        additional_prose = read_env_values(args.additional_prose_env)
        task_id = args.task_id
        require_all_live = True
        if args.branch and args.branch.startswith("task/"):
            task_id = args.branch
        elif args.branch:
            require_all_live = False
        findings = projection_findings(
            text,
            args.action_section,
            repo=REPO,
            allowed_url_prefixes=args.allowed_url_prefix,
            task_id=task_id,
            require_all_live=require_all_live,
            candidate_revision=args.candidate_revision,
            external_actions=external_actions,
            additional_prose=additional_prose,
        )
    except (RuntimeError, ValueError) as error:
        print(f"action-projection: input error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(f"[action-projection] {args.label}: {finding}")
    print(f"action-projection: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
