#!/usr/bin/env python3
"""Require external action sections to project live queue items."""
import argparse
from collections import Counter
import contextlib
import functools
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
    indentation_width,
    markdown_links,
    normalized_action_tokens,
    render_inline_code,
    rendered_human_text,
    semantic_text,
    strip_default_ignorable_characters,
    strip_indented_code,
    strip_inline_code,
    visible_markdown_link_source,
)

REPO = Path(__file__).resolve().parents[1]
# Every Git read in this gate goes through this prefix, so a `refs/replace/*` entry
# cannot substitute a forged commit, tree, or blob for the real one the gate was asked
# about. `git_output` prepends it for its callers; the two direct spawns below spell it
# out. The source-level guard in `automation/tests/test_reconcile_queue.py` holds that
# line for this file too.
RAW_GIT = ("git", "--no-replace-objects")
QUEUE_ACTORS = ("needs-human", "needs-agent")
QUEUE_ACTOR_CHOICES = (*QUEUE_ACTORS, "any")
QUEUE_TYPED_ITEM_PATTERN = (
    r"[a-z0-9][a-z0-9-]*/"
    r"(?:blocking|future-blocking|non-blocking)-"
    r"[a-z0-9][a-z0-9-]*\.md"
)
QUEUE_ITEM_PATH_PATTERN = (
    r"message-queue/(?:needs-human|needs-agent)/"
    + QUEUE_TYPED_ITEM_PATTERN
)
QUEUE_ITEM_RE = re.compile(
    r"^message-queue/(?P<actor>needs-human|needs-agent)/"
    + QUEUE_TYPED_ITEM_PATTERN
    + r"$"
)
QUEUE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    + QUEUE_ITEM_PATH_PATTERN
    + r"(?![A-Za-z0-9_.-])"
)
TASK_QUEUE_ACTION_TOKEN_PATTERN = rf"`{QUEUE_ITEM_PATH_PATTERN}`"
TASK_QUEUE_ACTION_VALUE_RE = re.compile(
    rf"{TASK_QUEUE_ACTION_TOKEN_PATTERN}"
    rf"(?:[ \t]*(?:;|,)[ \t]*{TASK_QUEUE_ACTION_TOKEN_PATTERN})*"
)
TASK_QUEUE_ACTION_FIELD_RE = re.compile(
    r"^\*\*Queue actions:\*\*[ \t]*(.*)$",
    re.M,
)
TASK_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
TASK_COMMIT_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])task:\s*"
    r"(?P<task>\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*)"
    r"(?![A-Za-z0-9-])",
)
HEADING_RE = re.compile(
    r"^(?P<quote>(?:>[ \t]?)*)(?P<level>#{1,6})[ \t]+"
    r"(?P<title>.*?)[ \t]*#*[ \t]*$"
)
LIST_ITEM_RE = re.compile(
    r"^(?P<indent>[ ]{0,3})(?P<marker>[-+*]|\d+[.)])"
    r"(?P<spacing>[ \t]+)"
)
TASK_LIST_ITEM_RE = re.compile(
    r"^[ ]{0,3}(?:[-+*]|\d+[.)])[ \t]+"
    r"\[(?P<state>[ xX])\](?=[ \t]|$)"
)
NO_ACTION_TEXT_BY_ACTOR = {
    "needs-human": "No human action requested.",
    "needs-agent": "No agent action requested.",
    "any": "No queued action requested.",
}
NO_ACTION_TEXT = NO_ACTION_TEXT_BY_ACTOR["needs-human"]
CLEAR_ACTION_VERB_PATTERN = (
    r"(?:accept|approve|authorize|choose|confirm|consider|"
    r"(?:chime|weigh)[ \t]+in|"
    r"(?:have|take)[ \t]+"
    r"(?:(?:a|an|another|one|your)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z'-]*[ \t]+){0,2}look|"
    r"ping[ \t]+(?:me|us)|"
    r"decide|deploy|(?:give|provide)"
    r"(?:[ \t]+(?:me|our|us|your))?[ \t]+feedback|inspect|"
    r"(?:add|leave)(?:[ \t]+(?:a|your))?[ \t]+comment|merge|"
    r"release|review|select|"
    r"sign[ \t]+off|tell|verify|vote)"
)
UNAMBIGUOUS_CLEAR_COMMAND_PATTERN = (
    r"(?:accept|approve|authorize|choose|confirm|consider|decide|deploy|"
    r"(?:chime|weigh)[ \t]+in|"
    r"(?:have|take)[ \t]+"
    r"(?:(?:a|an|another|one|your)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z'-]*[ \t]+){0,2}look|"
    r"ping[ \t]+(?:me|us)|"
    r"(?:give|provide)(?:[ \t]+(?:me|our|us|your))?[ \t]+feedback|inspect|"
    r"(?:add|leave)(?:[ \t]+(?:a|your))?[ \t]+comment|select|"
    r"sign[ \t]+off|tell|verify)"
)
LET_KNOW_PATTERN = r"let[ \t]+(?:me|us)[ \t]+know"
KEEP_POSTED_PATTERN = (
    r"keep[ \t]+(?:me|us)[ \t]+(?:informed|posted|updated)"
)
REQUEST_ACTION_VERB_PATTERN = (
    r"(?:add|address|analy[sz]e|assess|audit|benchmark|bisect|"
    r"(?:[A-Za-z][A-Za-z'-]*-)?check|debug|diagnose|document|evaluate|"
    r"examine|fix|implement|investigate|measure|profile|proofread|reproduce|"
    r"repair|resolve|retry|run|test|trace|triage|update|validate)"
)
UNAMBIGUOUS_WORK_COMMAND_PATTERN = (
    r"(?:add|analy[sz]e|assess|bisect|diagnose|evaluate|examine|fix|implement|"
    r"investigate|proofread|repair|reproduce|resolve|validate)"
)
AMBIGUOUS_WORK_COMMAND_PATTERN = (
    r"(?:address|audit|benchmark|check|debug|document|measure|profile|retry|"
    r"run|test|trace|triage|update)"
)
SUMMARY_PREDICATE_PATTERN = (
    r"(?:appears?|are|contains?|describes?|documents?|has|have|includes?|is|"
    r"lists?|records?|remains?|shows?|tracks?|uses?|was|were)"
)
SUMMARY_SUBJECT_WORD_PATTERN = (
    r"(?!(?:that|which|who)\b)[A-Za-z0-9][A-Za-z0-9_./#'-]*"
)
NONCOMMAND_SUMMARY_GUARD = (
    rf"(?![ \t]+(?:{SUMMARY_SUBJECT_WORD_PATTERN}[ \t]+){{1,4}}"
    rf"{SUMMARY_PREDICATE_PATTERN}\b)"
)
WORK_DIRECTIVE_PATTERN = (
    rf"(?:{UNAMBIGUOUS_WORK_COMMAND_PATTERN}|"
    rf"{AMBIGUOUS_WORK_COMMAND_PATTERN}{NONCOMMAND_SUMMARY_GUARD}"
    r"(?=[.!?;,:)]|$|[ \t]+\S))"
)
AMBIGUOUS_CLEAR_COMMAND_PATTERN = (
    rf"(?:(?:merge|release|review|vote){NONCOMMAND_SUMMARY_GUARD}"
    r"(?=[.!?;,:)]|$|[ \t]+\S))"
)
CLEAR_DIRECTIVE_ACTION_PATTERN = (
    rf"(?:{UNAMBIGUOUS_CLEAR_COMMAND_PATTERN}|"
    rf"{AMBIGUOUS_CLEAR_COMMAND_PATTERN})"
)
ACTION_VERB_PATTERN = (
    rf"(?:{CLEAR_ACTION_VERB_PATTERN}|{LET_KNOW_PATTERN}|"
    rf"{KEEP_POSTED_PATTERN}|"
    rf"{REQUEST_ACTION_VERB_PATTERN}|answer|comment|reply|respond)"
)
PASSIVE_ACTION_VERB_PATTERN = (
    r"(?:accepted|added|addressed|analy[sz]ed|approved|assessed|audited|"
    r"authorized|benchmarked|bisected|"
    r"(?:[A-Za-z][A-Za-z'-]*-)?checked|debugged|diagnosed|documented|"
    r"confirmed|deployed|evaluated|examined|fixed|implemented|inspected|"
    r"investigated|measured|merged|profiled|proofread|released|repaired|"
    r"reproduced|resolved|retried|reviewed|run|selected|tested|traced|"
    r"triaged|updated|validated|verified)"
)
ACTION_GERUND_PATTERN = (
    r"(?:adding|addressing|analy[sz]ing|approving|assessing|auditing|"
    r"authorizing|benchmarking|checking|confirming|debugging|deploying|"
    r"diagnosing|documenting|evaluating|examining|fixing|implementing|"
    r"inspecting|investigating|measuring|merging|profiling|proofreading|"
    r"releasing|repairing|reproducing|resolving|retrying|reviewing|running|"
    r"selecting|testing|tracing|triaging|updating|validating|verifying)"
)
NONWORK_DIRECTIVE_ACTION_PATTERN = (
    rf"(?:{CLEAR_DIRECTIVE_ACTION_PATTERN}"
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
DIRECTIVE_ACTION_PATTERN = (
    rf"(?:{NONWORK_DIRECTIVE_ACTION_PATTERN}|{WORK_DIRECTIVE_PATTERN})"
)
DIRECTIVE_PREFIX_PATTERN = r"(?:(?:and|also|then)[ \t]+)*"
OPEN_COMMAND_WORD_PATTERN = r"[A-Za-z][A-Za-z'-]*"
OBLIGATION_MODIFIER_PATTERN = (
    r"(?:(?:also|always|carefully|currently|definitely|directly|explicitly|"
    r"first|generally|independently|manually|normally|now|often|personally|"
    r"probably|really|simply|sometimes|still|typically|usually)[ \t]+)*"
)
REQUEST_WORK_VERB_PATTERN = (
    r"(?!(?:also|always|be|currently|generally|have|never|normally|not|"
    r"often|remain|see|sometimes|still|typically|usually)\b"
    rf"){OPEN_COMMAND_WORD_PATTERN}"
)
PLEASE_COMMAND_PATTERN = (
    rf"{DIRECTIVE_PREFIX_PATTERN}please"
    r"(?:[ \t]*,[ \t]*|[ \t]+)"
    rf"{DIRECTIVE_PREFIX_PATTERN}"
    rf"{OPEN_COMMAND_WORD_PATTERN}"
)
KINDLY_COMMAND_PATTERN = (
    rf"{DIRECTIVE_PREFIX_PATTERN}kindly"
    r"(?:[ \t]*,[ \t]*|[ \t]+)"
    rf"{DIRECTIVE_PREFIX_PATTERN}"
    rf"{DIRECTIVE_ACTION_PATTERN}"
)
COURTESY_COMMAND_PATTERN = (
    rf"(?:{PLEASE_COMMAND_PATTERN}|{KINDLY_COMMAND_PATTERN})"
)
HUMAN_ACTION_NOUN_PATTERN = (
    r"(?:advice|approval|authorization|choice|clarification|comments?|"
    r"confirmation|decision|feedback|guidance|input|opinions?|perspective|"
    r"repl(?:y|ies)|responses?|review|sign[ -]?off|takes?|thoughts?|"
    r"verification|views?|vote)"
)
HUMAN_ACTOR_PATTERN = r"(?:human|maintainer|owner|reviewer)s?"
NAMED_HUMAN_GROUP_PATTERN = (
    r"(?:(?:a|an|the)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z0-9&'._-]*[ \t]+){0,3}"
    r"(?:committee|council|crew|department|group|office|staff|squad|team)"
)
NAMED_HUMAN_ROLE_PATTERN = (
    r"(?:(?:a|an|the)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z0-9&'._-]*[ \t]+){0,3}"
    r"(?:architect|director|engineer|lead|manager|officer)s?"
)
NAMED_HUMAN_IDENTITY_PATTERN = (
    r"(?:@[A-Za-z0-9][A-Za-z0-9_.-]*|anyone|somebody|someone|"
    r"(?-i:[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)?))"
)
FREEFORM_ADDRESSEE_TOKEN_PATTERN = (
    r"(?:@?[A-Za-z0-9][A-Za-z0-9&'._/-]*)"
)
FREEFORM_ADDRESSEE_PATTERN = (
    rf"(?:{FREEFORM_ADDRESSEE_TOKEN_PATTERN}[ \t]+){{1,6}}?"
)
FREEFORM_OBLIGATION_SUBJECT_PATTERN = (
    r"(?:(?!(?:are|been|did|do|does|had|has|have|is|must|needs?|never|"
    r"no|not|longer|previously|required|requested|should|was|were)\b)"
    rf"{FREEFORM_ADDRESSEE_TOKEN_PATTERN}[ \t]+){{1,6}}?"
)
REPORTED_SPEECH_CUE_PATTERN = (
    r"(?:described|documented|explained|explains|noted|notes|recorded|"
    r"reported|said|says|stated|wrote)"
)
AUTOMATION_ACTOR_PATTERN = (
    r"(?:(?:a|an|the)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z0-9_-]*[ \t]+){0,3}"
    r"(?:agent|assistant|bot|worker)s?"
)
ACTION_SOURCE_PATTERN = (
    rf"(?:you|{NAMED_HUMAN_IDENTITY_PATTERN}|{NAMED_HUMAN_GROUP_PATTERN}|"
    rf"{NAMED_HUMAN_ROLE_PATTERN}|"
    r"(?:(?:a|an|the)[ \t]+)?"
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
    rf"{COURTESY_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
ADDITIONAL_DIRECTIVE_RE = re.compile(
    r"(?:^|(?:[,.!;:—]|[ \t]+-)[ \t]+)"
    r"(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{COURTESY_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
SUMMARY_DIRECTIVE_RE = re.compile(
    r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{COURTESY_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{NONWORK_DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
ADDITIONAL_SUMMARY_DIRECTIVE_RE = re.compile(
    r"(?:^|(?:[,.!;:—]|[ \t]+-)[ \t]+)"
    r"(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{COURTESY_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}{NONWORK_DIRECTIVE_ACTION_PATTERN}"
    r")\b",
    re.I | re.M,
)
TODO_RE = re.compile(r"\bTODO\b", re.I)
QUESTION_MARK_RE = re.compile(r"""\?(?=$|[\s)\]}>.,!;:'"’”])""")
QUOTED_QUESTION_LITERAL_RE = re.compile(
    r"""(?:'\?'|"\?"|‘\?’|“\?”)"""
)
SELF_ANSWERED_EXPLANATORY_QUESTION_RE = re.compile(
    r"^[ \t]*(?:how|what|why)\b"
    r"(?!(?:[^?!\n]{0,120}\b"
    r"(?:choice|could|must|need(?:s)?|opinion|prefer(?:ence)?|"
    r"recommendation|should|think|you|your|we|will|would)\b))"
    r"[^?!\n]{0,120}\?"
    r"(?=(?:[ \t]+|\n[ \t]*)\S)",
    re.I | re.M,
)
SELF_ANSWERED_POLAR_QUESTION_RE = re.compile(
    r"^[ \t]*(?:is|are|can|could|did|do|does|has|have|"
    r"was|were|will|would)\b[^?!\n]{0,120}\?"
    r"(?=(?:[ \t]+|\n[ \t]*)(?:yes|no|it|they|this|that|the)\b)",
    re.I | re.M,
)
EMPHASIS_MARKER_RE = re.compile(r"(?<!\\)(?:\*{1,3}|_{1,3})")
FULL_OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$")
QUEUE_ACTION_RE = re.compile(
    r"^\*\*Action:\*\*[ \t]*(?P<action>\S(?:.*\S)?)[ \t]*$",
    re.M,
)
QUEUE_EXTERNAL_ASSIGNMENT_RE = re.compile(
    r"^\*\*External assignment:\*\*[ \t]*"
    r"(?P<binding>\S(?:.*\S)?)[ \t]*$",
    re.M,
)
QUEUE_EXTERNAL_SOURCE_RE = re.compile(
    r"^\*\*External source:\*\*[ \t]*"
    r"(?P<binding>\S(?:.*\S)?)[ \t]*$",
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
    rf"{REQUEST_WORK_VERB_PATTERN}\b",
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
    rf"\b{ACTION_SOURCE_PATTERN}\b[ \t]+"
    r"(?!(?:(?:do|does|is|are)[ \t]+not)\b)"
    r"(?:must|should|needs?[ \t]+to|(?:is|are)[ \t]+requested[ \t]+to|"
    r"requested[ \t]+to)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:not|never)\b)"
    rf"{REQUEST_WORK_VERB_PATTERN}\b",
    re.I,
)
AUTOMATION_ACTOR_OBLIGATION_RE = re.compile(
    rf"\b{AUTOMATION_ACTOR_PATTERN}\b[ \t]+"
    r"(?!(?:(?:do|does|is|are)[ \t]+not)\b)"
    r"(?:must|should|needs?[ \t]+to|(?:is|are)[ \t]+requested[ \t]+to|"
    r"requested[ \t]+to)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:not|never)\b)"
    rf"{REQUEST_WORK_VERB_PATTERN}\b",
    re.I,
)
FREEFORM_ACTOR_OBLIGATION_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    rf"{FREEFORM_OBLIGATION_SUBJECT_PATTERN}"
    r"(?!(?:(?:do|does|is|are)[ \t]+not)\b)"
    r"(?:must|needs?[ \t]+to|(?:has|have)[ \t]+to|"
    r"(?:is|are)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}(?:requested|required)[ \t]+to|"
    r"(?:requested|required)[ \t]+to)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:not|never)\b)"
    rf"{ACTION_VERB_PATTERN}\b",
    re.I | re.M,
)
FREEFORM_PASSIVE_OBLIGATION_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    rf"{FREEFORM_OBLIGATION_SUBJECT_PATTERN}"
    r"(?!(?:(?:do|does|is|are)[ \t]+not)\b)"
    r"(?:must|needs?[ \t]+to|(?:has|have)[ \t]+to|"
    r"(?:is|are)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}(?:requested|required)[ \t]+to|"
    r"(?:requested|required)[ \t]+to)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:not|never)\b)"
    r"be[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    rf"{PASSIVE_ACTION_VERB_PATTERN}\b",
    re.I | re.M,
)
FREEFORM_LIFECYCLE_OBLIGATION_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    rf"{FREEFORM_OBLIGATION_SUBJECT_PATTERN}"
    r"(?!(?:(?:do|does|is|are)[ \t]+not)\b)"
    r"(?:must|should|ought[ \t]+to|"
    r"needs?(?:[ \t]+to|(?![ \t]+to\b))|"
    r"requires?(?:[ \t]+to|(?![ \t]+to\b))|"
    r"(?:has|have)[ \t]+to|"
    r"(?:is|are)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?:(?:requested|required|expected)[ \t]+to|to))[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!no\b)"
    r"(?!be[ \t]+(?:able[ \t]+to|"
    r"(?:[A-Za-z][A-Za-z'-]*[ \t]+){0,2}"
    r"[A-Za-z][A-Za-z'-]*(?:able|ible)\b))"
    r"[^.!?\n]{1,160}\b(?:before|by|prior[ \t]+to)[ \t]+"
    r"(?:(?:a|an|the|this|that)[ \t]+)?"
    r"(?:deploy(?:ing|ment)|merg(?:e|ing)|publication|publish(?:ing)?|"
    r"releas(?:e|ing)|ship(?:ping)?)\b",
    re.I | re.M,
)
PREDICATE_LIFECYCLE_REQUIREMENT_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    r"(?!no\b)"
    r"[^.!?\n]{1,120}\b"
    r"(?:are|is|remains?|stays?)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:no[ \t]+longer|not)\b)"
    r"(?:mandatory|necessary|needed|outstanding|pending|required)\b"
    r"[^.!?\n]{0,80}\b(?:before|by|prior[ \t]+to)[ \t]+"
    r"(?:(?:a|an|the|this|that)[ \t]+)?"
    r"(?:deploy(?:ing|ment)|merg(?:e|ing)|publication|publish(?:ing)?|"
    r"releas(?:e|ing)|ship(?:ping)?)\b",
    re.I | re.M,
)
FREEFORM_ACTION_OBJECT_OBLIGATION_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    rf"{FREEFORM_OBLIGATION_SUBJECT_PATTERN}"
    r"(?:needs?|requires?)[ \t]+"
    r"(?!no\b|to\b)"
    r"(?:"
    rf"{ACTION_GERUND_PATTERN}"
    r"|(?:(?:a|an|another|the)[ \t]+)?"
    rf"(?:{HUMAN_ACTION_NOUN_PATTERN}|fix|repair|test)"
    r")\b"
    r"[ \t]*[.!]?[ \t]*(?=$|\n)",
    re.I | re.M,
)
PREDICATE_ACTION_REQUIREMENT_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    r"(?!no\b)"
    r"[^.!?\n]{0,100}\b"
    rf"(?:{ACTION_GERUND_PATTERN}|{HUMAN_ACTION_NOUN_PATTERN})\b"
    r"[^.!?\n]{0,80}\b"
    r"(?:are|is|remains?|stays?)[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?!(?:no[ \t]+longer|not)\b)"
    r"(?:mandatory|necessary|needed|outstanding|pending|required)\b",
    re.I | re.M,
)
NEGATIVE_IMPERATIVE_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    rf"(?![^.!?\n]*\b{REPORTED_SPEECH_CUE_PATTERN}\b)"
    r"(?:please[ \t]+)?(?:do[ \t]+not|don['’]t|never)[ \t]+"
    rf"{ACTION_VERB_PATTERN}\b",
    re.I | re.M,
)
ACTOR_HARD_PROHIBITION_RE = re.compile(
    rf"\b(?:{ACTION_SOURCE_PATTERN}|{AUTOMATION_ACTOR_PATTERN})\b[ \t]+"
    r"must[ \t]+"
    rf"{OBLIGATION_MODIFIER_PATTERN}"
    r"(?:not|never)[ \t]+"
    rf"{OPEN_COMMAND_WORD_PATTERN}\b",
    re.I,
)
NAMED_ASSIGNMENT_RE = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?:assigned[ \t]+to|assignee[ \t]*:)[ \t]+"
    r"(?P<negation>nobody|no[ \t]+one)?"
    r"(?(negation)|(?:@?[A-Za-z0-9][A-Za-z0-9_.-]*"
    r"(?:[ \t]+[A-Za-z][A-Za-z'.-]*){0,3}))"
    r"(?:[ \t]*[:—-][^\n]*)?[.!]?[ \t]*(?=$|\n)",
    re.I | re.M,
)
BOUNDARY_VERB_PATTERN = (
    r"(?:continue|deploy(?:ed)?|merge(?:d)?|proceed|publish(?:ed)?|"
    r"release(?:d)?|ship(?:ped)?)"
)
BOUNDARY_SUBJECT_PATTERN = (
    r"(?:change|deployment|implementation|merge|merging|pr|publication|"
    r"pull[ \t]+request|release|shipping|task|work)"
)
HUMAN_COMPLETION_VERB_PATTERN = (
    r"(?:approves?|confirms?|inspects?|looks?[ \t]+over|reviews?|"
    r"signs?[ \t]+off|verif(?:y|ies))"
)
BOUNDARY_UNTIL_HUMAN_ACTION_RE = re.compile(
    r"\b(?:"
    r"(?:(?:can[ \t]*not|can['’]t|may[ \t]+not|must[ \t]+not|"
    r"will[ \t]+not|won['’]t)[ \t]+(?:be[ \t]+)?"
    rf"{BOUNDARY_VERB_PATTERN})"
    rf"|(?:{BOUNDARY_SUBJECT_PATTERN}[ \t]+"
    r"(?:(?:is|remains|stays)|will[ \t]+(?:be|remain|stay))"
    r"[ \t]+blocked)"
    rf"|(?:{BOUNDARY_SUBJECT_PATTERN}[ \t]+(?:stops|waits)"
    r"(?:[ \t]+at[ \t]+(?:deployment|merge|release))?)"
    r")"
    r"[ \t]+(?:pending|until)[ \t]+"
    r"(?:"
    rf"{ACTION_SOURCE_PATTERN}[ \t]+"
    r"(?:(?:has|have)[ \t]+)?"
    rf"{HUMAN_COMPLETION_VERB_PATTERN}"
    r"|"
    r"(?:(?:a|an|the)[ \t]+)?"
    rf"{HUMAN_ACTOR_PATTERN}(?:['’]s)?[ \t]+"
    r"(?:approval|confirmation|review|sign[ -]?off)\b"
    r"|"
    r"(?:approval|confirmation|review|sign[ -]?off)"
    r"[ \t]+by[ \t]+"
    rf"{ACTION_SOURCE_PATTERN}\b"
    r")",
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
    r"(?!(?:be|have)\b)"
    rf"{OPEN_COMMAND_WORD_PATTERN}\b",
    re.I,
)
MODAL_FREEFORM_ADDRESSEE_REQUEST_RE = re.compile(
    r"\b(?:can|could|may|might|should|will|would)[ \t]+"
    r"(?!(?:be|have)\b)"
    rf"(?!(?:{FREEFORM_ADDRESSEE_TOKEN_PATTERN}[ \t]+){{0,7}}"
    r"(?:not|never)\b)"
    rf"{FREEFORM_ADDRESSEE_PATTERN}"
    r"(?:please[ \t]+)?"
    rf"{DIRECTIVE_ACTION_PATTERN}\b",
    re.I,
)
TASK_MODAL_FREEFORM_ADDRESSEE_REQUEST_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    r"(?:can|could|may|might|should|will|would)[ \t]+"
    r"(?!(?:be|have)\b)"
    rf"(?!(?:{FREEFORM_ADDRESSEE_TOKEN_PATTERN}[ \t]+){{0,7}}"
    r"(?:not|never)\b)"
    rf"{FREEFORM_ADDRESSEE_PATTERN}"
    r"(?:please[ \t]+)?"
    rf"{DIRECTIVE_ACTION_PATTERN}\b",
    re.I | re.M,
)
COURTESY_ACTION_NOUN_PATTERN = r"(?:feedback|input|reviews?)"
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
PASSIVE_WORK_APPRECIATION_RE = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?![^\n]*\b(?:reported|said|says|stated|wrote)\b"
    r"[^\n]*\bwould[ \t]+be\b)"
    r"(?P<negation>(?:(?:no|not)[ \t]+)?)"
    r"(?:(?:a|an|the|this|that)[ \t]+)?"
    r"(?:[A-Za-z][A-Za-z'-]*[ \t]+){0,4}"
    r"[A-Za-z][A-Za-z'-]*[ \t]+would[ \t]+be[ \t]+"
    r"(?:(?:especially|greatly|much|really|very)[ \t]+)?"
    r"(?:appreciated|better|good|great|helpful|ideal|nice|preferable|"
    r"useful|valued|welcome)"
    r"(?:[ \t]+(?:before|if|when)[ \t]+[^.!?\n]{1,80})?"
    r"[ \t]*[.!]?[ \t]*(?=$|\n)",
    re.I | re.M,
)
HUMAN_HANDOFF_RE = re.compile(
    r"(?:^|[.!?][ \t]+|\n)[ \t]*"
    r"(?:please[ \t]+)?"
    r"(?:ask|consult|contact|notify|ping)[ \t]+"
    rf"{ACTION_SOURCE_PATTERN}\b"
    r"[^.!?\n]{0,120}\b"
    rf"{ACTION_VERB_PATTERN}\b",
    re.I | re.M,
)
TASK_AUTHORITY_DIRECTIVE_RE = re.compile(
    r"(?:^|(?:[,.!;:—]|[ \t]+-)[ \t]+)"
    r"[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?"
    r"(?:"
    rf"{COURTESY_COMMAND_PATTERN}"
    r"|"
    rf"{DIRECTIVE_PREFIX_PATTERN}"
    r"(?:accept|approve|authorize|"
    r"(?:give|provide)(?:[ \t]+(?:me|our|us|your))?[ \t]+feedback|"
    r"let[ \t]+(?:me|us)[ \t]+know|"
    r"keep[ \t]+(?:me|us)[ \t]+(?:informed|posted|updated)|"
    r"ping[ \t]+(?:me|us)|sign[ \t]+off)"
    r")\b",
    re.I | re.M,
)
ADDRESSED_HUMAN_DIRECTIVE_RE = re.compile(
    r"(?:^|[.!?\n])[ \t]*"
    rf"(?:{ACTION_SOURCE_PATTERN})[ \t]*(?:,|:|—)[ \t]*"
    rf"(?:please[ \t]+)?{DIRECTIVE_ACTION_PATTERN}\b",
    re.I | re.M,
)
PENDING_HUMAN_ACTION_RE = re.compile(
    rf"(?:^|[.!?\n])[ \t]*(?:pending|awaiting)[ \t]+"
    rf"(?:{ACTION_SOURCE_PATTERN}(?:['’]s)?[ \t]+)?"
    rf"{HUMAN_ACTION_NOUN_PATTERN}\b",
    re.I | re.M,
)
TABLE_HUMAN_ACTION_RE = re.compile(
    rf"^[ \t]*\|[ \t]*(?:{ACTION_SOURCE_PATTERN})[ \t]*\|"
    rf"[ \t]*(?:{DIRECTIVE_ACTION_PATTERN}|{HUMAN_ACTION_NOUN_PATTERN})\b",
    re.I | re.M,
)
IMPERSONAL_WORK_APPRECIATION_RE = re.compile(
    r"(?:^|\n)[ \t]*it[ \t]+would[ \t]+"
    r"(?P<negation>not[ \t]+)?be[ \t]+"
    r"(?:(?:especially|greatly|much|really|very)[ \t]+)?"
    r"(?:appreciated|better|good|great|helpful|ideal|nice|preferable|"
    r"useful|valued|welcome)[ \t]+"
    r"(?:if|when)[ \t]+"
    r"(?:you|(?:(?:a|an|the)[ \t]+)?"
    rf"{HUMAN_ACTOR_PATTERN})[ \t]+"
    rf"{OPEN_COMMAND_WORD_PATTERN}\b"
    r"[^.!?\n]{0,80}[.!]?[ \t]*(?=$|\n)",
    re.I | re.M,
)
ELLIPTICAL_COURTESY_REQUEST_RE = re.compile(
    r"(?:^|(?<=[.!;:—]))[ \t]*"
    r"(?:(?:any|some|your)[ \t]+)?"
    rf"{COURTESY_ACTION_NOUN_PATTERN}[ \t]+"
    r"(?:(?:is|are)[ \t]+(?P<negation>not[ \t]+)?)?"
    r"(?:appreciated|valued|welcome)[ \t]*[.!]?[ \t]*(?=$|\n)",
    re.I | re.M,
)
HUMAN_POSSESSIVE_SOURCE_PATTERN = (
    rf"(?:your|"
    r"(?:(?:(?:a|an|the)[ \t]+)?"
    r"(?:(?:authorized|code|designated|lead|project|responsible|senior)"
    r"[ \t]+){0,2}"
    rf"{HUMAN_ACTOR_PATTERN})(?:['’]s|['’]))"
)
INDIRECT_SOLICITATION_TARGET_PATTERN = (
    r"(?:"
    rf"(?:what|whether)[ \t]+(?:do[ \t]+|does[ \t]+)?"
    rf"{ACTION_SOURCE_PATTERN}[ \t]+(?:think|thinks)\b"
    r"|"
    rf"how[ \t]+{ACTION_SOURCE_PATTERN}[ \t]+"
    r"(?:think|thinks|(?:would|could|might|will)[ \t]+"
    r"(?:approach|handle|proceed|respond|solve))\b"
    r"|"
    rf"{HUMAN_POSSESSIVE_SOURCE_PATTERN}[ \t]+"
    r"(?:feedback|input|opinions?|perspective|take|thoughts?|views?)\b"
    r")"
)
FIRST_PERSON_CURIOSITY_RE = re.compile(
    r"\b(?:i[ \t]*(?:am|['’]m)|we[ \t]*(?:are|['’]re))[ \t]+"
    r"(?P<negation>(?:not|no[ \t]+longer)[ \t]+)?"
    r"(?:curious|interested|wondering)\b"
    r"[^.!?;\n]{0,160}?"
    rf"{INDIRECT_SOLICITATION_TARGET_PATTERN}",
    re.I,
)
FIRST_PERSON_WONDER_RE = re.compile(
    r"\b(?:i|we)[ \t]+"
    r"(?P<negation>(?:(?:do[ \t]+not|don['’]t|no[ \t]+longer)[ \t]+)?)"
    r"wonder\b"
    r"[^.!?;\n]{0,160}?"
    rf"{INDIRECT_SOLICITATION_TARGET_PATTERN}",
    re.I,
)
ELLIPTICAL_CURIOSITY_RE = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?P<negation>(?:(?:not|no[ \t]+longer)[ \t]+)?)"
    r"(?:curious|interested|wondering)\b"
    r"[^.!?;\n]{0,160}?"
    rf"{INDIRECT_SOLICITATION_TARGET_PATTERN}",
    re.I | re.M,
)
DECLARATIVE_REFERENCE_CUE_RE = re.compile(
    r"(?:^|[\n.!?;])[ \t]*"
    r"(?:(?:for[ \t]+)?context|details|reference|source)[ \t]*:[ \t]*$",
    re.I,
)
REFERENCE_LINK_LINE_END_RE = re.compile(
    r"^[ \t]*[,.!?:;]?[ \t]*(?:\n|$)"
)
AMBIGUOUS_COMMAND_WORD_PATTERN = (
    rf"(?:{AMBIGUOUS_WORK_COMMAND_PATTERN}|merge|release|review|vote)"
)
SUMMARY_AND_COMMAND_RE = re.compile(
    rf"(?:^|[.!?;:\n][ \t]+)(?:the[ \t]+)?"
    rf"{AMBIGUOUS_COMMAND_WORD_PATTERN}\b[ \t]+"
    rf"(?:{SUMMARY_SUBJECT_WORD_PATTERN}[ \t]+){{1,4}}"
    rf"{SUMMARY_PREDICATE_PATTERN}\b"
    r"[^.!?;:\n]*?\band[ \t]+(?P<command>[^.!?;:\n]+)",
    re.I | re.M,
)
REFERENCE_TITLE_WORD_PATTERN = (
    r"(?!(?:and|or|please|that|then|todo|which|who)\b)"
    r"[A-Za-z0-9][A-Za-z0-9_./#'-]*"
)
AMBIGUOUS_REFERENCE_TITLE_RE = re.compile(
    rf"^[ \t]*{AMBIGUOUS_COMMAND_WORD_PATTERN}[ \t]+"
    rf"(?:{REFERENCE_TITLE_WORD_PATTERN}(?:[ \t]+|(?=[.!]?[ \t]*$)))"
    r"{1,5}[.!]?[ \t]*$",
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


# The pull-request body schema. Its sections and their order are read from the file
# at run time, so the schema keeps living in exactly one place. Two facts it states
# only inside HTML comments cannot be read that way — `templates/README.md` requires
# that nothing a check reads is hidden in a comment, and every parser here blanks
# them — so they are named once, here, and pinned against the schema by
# `automation/tests/test_pull_request_schema.py`.
PULL_REQUEST_SCHEMA_PATH = "templates/pull-request.md"
PULL_REQUEST_OPTIONAL_SECTIONS = ("Notes",)
PULL_REQUEST_SUMMARY_SECTION = "TL;DR"
PULL_REQUEST_SUMMARY_RANGE = (3, 6)
ORDERED_LIST_ITEM_RE = re.compile(r"^[ ]{0,3}\d+[.)][ \t]+")
BODY_SHAPE_CHECK = "explanation-shape"


def normalized_title(value):
    return " ".join((value or "").strip().casefold().split())


def normalized_queue_actor(value):
    actor = (value or "").strip().casefold()
    if actor not in QUEUE_ACTOR_CHOICES:
        raise ValueError(
            "queue actor must be `needs-human`, `needs-agent`, or `any`"
        )
    return actor


def allowed_queue_actors(queue_actor):
    actor = normalized_queue_actor(queue_actor)
    return set(QUEUE_ACTORS) if actor == "any" else {actor}


def queue_item_actor(path):
    matched = QUEUE_ITEM_RE.fullmatch(path or "")
    return matched.group("actor") if matched else None


def parse_task_queue_action_value(value):
    """Parse the closed Queue actions value grammar."""
    clean = (value or "").strip()
    if clean == "none":
        return ()
    if not TASK_QUEUE_ACTION_VALUE_RE.fullmatch(clean):
        raise ValueError(
            "must be exactly `none` or backticked canonical queue paths "
            "separated by `;` or `,`"
        )
    paths = tuple(QUEUE_PATH_RE.findall(clean))
    if len(paths) != len(set(paths)):
        raise ValueError("must not repeat a canonical queue path")
    return paths


def task_queue_action_paths_from_text(text):
    """Return paths from the task's sole structural Queue actions field."""
    values = TASK_QUEUE_ACTION_FIELD_RE.findall(semantic_text(text or ""))
    if len(values) != 1:
        raise ValueError("must contain exactly one Queue actions field")
    return parse_task_queue_action_value(values[0])


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


def body_sections(text):
    """Return the visible unquoted level-two headings of a body, in order."""
    headings = []
    for line in semantic_text(text).splitlines():
        matched = HEADING_RE.match(line)
        if not matched or matched.group("quote").count(">"):
            continue
        if len(matched.group("level")) != 2:
            continue
        title = " ".join(matched.group("title").split())
        if title:
            headings.append(title)
    return headings


def pull_request_schema_sections(repo=REPO):
    """Return the sections `templates/pull-request.md` declares, in its order.

    Returns an empty list when the schema is not in this checkout. The rules it
    feeds are advisory, so a checkout without the template loses a readability
    opinion and nothing else; failing the run instead would turn a missing
    document into a refused pull request.
    """
    try:
        text = (repo / PULL_REQUEST_SCHEMA_PATH).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return body_sections(text)


def summary_item_count(text):
    """Return how many numbered top-level items the summary section carries."""
    bodies = action_sections(text, [PULL_REQUEST_SUMMARY_SECTION])
    if not bodies:
        return None
    entries, _outside = section_entries(bodies[0])
    return sum(
        1 for entry in entries
        if ORDERED_LIST_ITEM_RE.match(entry.splitlines()[0] if entry else "")
    )


def body_shape_findings(text, repo=REPO):
    """Report the pull-request body rules a program can see, and only those.

    This is the half of `skills/explain-to-human/` that lives outside the
    repository: a pull-request body is a provider artifact, so the reconciler —
    which is a function of repository files — never reads one, and this gate is
    the only tracked program that does. What it can see is which sections are
    present, what order they come in, and how many items the summary holds. What
    it cannot see is whether any of them was worth reading, so every finding here
    is advisory and none of them changes this program's exit status
    (`memory/decisions/2026-08-02-readability-enforcement-disposition.md`).
    """
    schema = pull_request_schema_sections(repo)
    if not schema:
        return []
    findings = []
    present = body_sections(text)
    for heading in schema:
        if heading in PULL_REQUEST_OPTIONAL_SECTIONS or heading in present:
            continue
        findings.append(
            f"missing section `## {heading}`; "
            f"`{PULL_REQUEST_SCHEMA_PATH}` is the skeleton to copy"
        )
    # Compare only the schema sections the body actually carries, so a missing
    # one is reported once as missing rather than again as disorder.
    ordered = list(dict.fromkeys(
        heading for heading in present if heading in schema
    ))
    expected = [heading for heading in schema if heading in ordered]
    for found, wanted in zip(ordered, expected):
        if found != wanted:
            findings.append(
                f"section `## {found}` comes before `## {wanted}`; a reader "
                f"scans these in one order and `{PULL_REQUEST_SCHEMA_PATH}` "
                "sets it"
            )
            break
    low, high = PULL_REQUEST_SUMMARY_RANGE
    count = summary_item_count(text)
    if count is not None and not low <= count <= high:
        findings.append(
            f"`## {PULL_REQUEST_SUMMARY_SECTION}` carries {count} numbered "
            f"item(s); the schema asks for {low} to {high}, each naming a state "
            "before and a state after"
            + ("; a bulleted list counts as none" if not count else "")
        )
    return findings


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


def copied_prose_without_links(entry):
    """Return visible prose outside Markdown links, keeping code-span contents.

    Verbatim-copy comparisons normalize both sides through `render_inline_code`,
    the same view `normalized_action_tokens` already uses for Action labels, so a
    field carrying an inline code span stays comparable instead of being blanked
    on one side only. Detection-only callers keep `prose_without_links`.
    """
    clean = strip_indented_code(render_inline_code(semantic_text(entry)))
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


def strip_action_list_markers(text):
    """Remove visible Markdown list/heading markers before classifying prose."""
    return "\n".join(
        re.sub(
            r"^[ ]{0,3}#{1,6}[ \t]+",
            "",
            LIST_ITEM_RE.sub("", line, count=1),
            count=1,
        )
        for line in (text or "").split("\n")
    )


def unchecked_task_list_item(text):
    """Return whether visible Markdown contains an explicit pending task."""
    return any(
        matched and matched.group("state") == " "
        for matched in (
            TASK_LIST_ITEM_RE.match(line)
            for line in (text or "").split("\n")
        )
    )


def strip_checked_task_list_items(text):
    """Blank completed task-list lines before ordinary command classification."""
    output = []
    for line in (text or "").split("\n"):
        matched = TASK_LIST_ITEM_RE.match(line)
        output.append(
            ""
            if matched and matched.group("state").casefold() == "x"
            else line
        )
    return "\n".join(output)


DECLARATIVE_ACTION_PATTERNS = (
    DECLARATIVE_ACTION_RE,
    HUMAN_REQUEST_RE,
    FIRST_PERSON_REQUEST_RE,
    ACTOR_HARD_PROHIBITION_RE,
    NAMED_ASSIGNMENT_RE,
    ACTOR_OBLIGATION_RE,
    AUTOMATION_ACTOR_OBLIGATION_RE,
    FREEFORM_ACTOR_OBLIGATION_RE,
    FREEFORM_PASSIVE_OBLIGATION_RE,
    FREEFORM_LIFECYCLE_OBLIGATION_RE,
    PREDICATE_LIFECYCLE_REQUIREMENT_RE,
    FREEFORM_ACTION_OBJECT_OBLIGATION_RE,
    PREDICATE_ACTION_REQUIREMENT_RE,
    NEGATIVE_IMPERATIVE_RE,
    FIRST_PERSON_VERB_REQUEST_RE,
    MODAL_ACTOR_REQUEST_RE,
    MODAL_FREEFORM_ADDRESSEE_REQUEST_RE,
    FIRST_PERSON_COURTESY_REQUEST_RE,
    PASSIVE_COURTESY_REQUEST_RE,
    PASSIVE_WORK_APPRECIATION_RE,
    IMPERSONAL_WORK_APPRECIATION_RE,
    ELLIPTICAL_COURTESY_REQUEST_RE,
    FIRST_PERSON_CURIOSITY_RE,
    FIRST_PERSON_WONDER_RE,
    ELLIPTICAL_CURIOSITY_RE,
    HUMAN_HANDOFF_RE,
)
TASK_HUMAN_ACTION_PATTERNS = (
    DECLARATIVE_ACTION_RE,
    HUMAN_REQUEST_RE,
    FIRST_PERSON_REQUEST_RE,
    ACTOR_HARD_PROHIBITION_RE,
    NAMED_ASSIGNMENT_RE,
    NEGATIVE_IMPERATIVE_RE,
    ACTOR_OBLIGATION_RE,
    FIRST_PERSON_VERB_REQUEST_RE,
    MODAL_ACTOR_REQUEST_RE,
    TASK_MODAL_FREEFORM_ADDRESSEE_REQUEST_RE,
    FIRST_PERSON_COURTESY_REQUEST_RE,
    PASSIVE_COURTESY_REQUEST_RE,
    PASSIVE_WORK_APPRECIATION_RE,
    IMPERSONAL_WORK_APPRECIATION_RE,
    ELLIPTICAL_COURTESY_REQUEST_RE,
    FIRST_PERSON_CURIOSITY_RE,
    FIRST_PERSON_WONDER_RE,
    ELLIPTICAL_CURIOSITY_RE,
    HUMAN_HANDOFF_RE,
)


def declarative_action_request(clean, patterns=DECLARATIVE_ACTION_PATTERNS):
    """Recognize narrow declarative/courtesy requests, excluding local negation."""
    for pattern in patterns:
        for matched in pattern.finditer(clean):
            if matched.groupdict().get("negation"):
                continue
            if pattern in {
                FREEFORM_ACTOR_OBLIGATION_RE,
                FREEFORM_PASSIVE_OBLIGATION_RE,
                FREEFORM_LIFECYCLE_OBLIGATION_RE,
                PREDICATE_LIFECYCLE_REQUIREMENT_RE,
                FREEFORM_ACTION_OBJECT_OBLIGATION_RE,
                PREDICATE_ACTION_REQUIREMENT_RE,
                NEGATIVE_IMPERATIVE_RE,
            }:
                clause_prefix = re.split(
                    r"(?:[.!?][ \t]+|\n[ \t]*\n)",
                    clean[:matched.start()],
                )[-1]
                if re.search(
                    rf"\b{REPORTED_SPEECH_CUE_PATTERN}\b",
                    clause_prefix,
                    re.I,
                ):
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


def summary_followed_by_command(clean):
    """Recognize a noun-summary clause followed by an explicit new command."""
    return any(
        DIRECTIVE_RE.search("and " + matched.group("command"))
        for matched in SUMMARY_AND_COMMAND_RE.finditer(clean or "")
    )


def summary_conjoined_authority_request(clean):
    """Recognize an authority request appended to a change-summary clause."""
    return any(
        SUMMARY_DIRECTIVE_RE.search("and " + suffix)
        for suffix in re.split(r"\band[ \t]+", clean or "", flags=re.I)[1:]
    )


def action_like_clean_text(
    clean,
    strip_leading_symbols=False,
    summary_context=False,
    allow_self_answered_explanations=False,
):
    """Classify already-visible prose with the deterministic action grammar."""
    clean = strip_default_ignorable_characters(clean)
    if unchecked_task_list_item(clean):
        return True
    clean = strip_checked_task_list_items(clean)
    clean = strip_action_list_markers(clean)
    if strip_leading_symbols:
        clean = "\n".join(
            re.sub(r"^[^\w]+", "", line)
            for line in clean.split("\n")
        )
    if allow_self_answered_explanations:
        clean = SELF_ANSWERED_EXPLANATORY_QUESTION_RE.sub(
            lambda matched: matched.group(0)[:-1] + ".",
            clean,
        )
    if question_mark_count(clean) or TODO_RE.search(clean):
        return True
    directive = SUMMARY_DIRECTIVE_RE if summary_context else DIRECTIVE_RE
    additional_directive = (
        ADDITIONAL_SUMMARY_DIRECTIVE_RE
        if summary_context
        else ADDITIONAL_DIRECTIVE_RE
    )
    return any(
        directive.search(variant)
        or additional_directive.search(variant)
        or declarative_action_request(variant)
        or BOUNDARY_UNTIL_HUMAN_ACTION_RE.search(variant)
        or (
            summary_context
            and summary_conjoined_authority_request(variant)
        )
        or (not summary_context and summary_followed_by_command(variant))
        for variant in action_prose_variants(clean)
    )


def action_like_prose(text, allow_self_answered_explanations=False):
    """Recognize deterministic human-action grammar in visible Markdown prose.

    A fragment is action-like when it contains question punctuation, a standalone
    TODO, an authority verb in command position at the start of a line/list item,
    or a narrow present-tense declaration that human approval/review/confirmation
    is requested or required. Query-token prefixes such as `?foo` are not question
    punctuation. Markdown destinations and code are not prose; callers inspect link
    labels separately. In explanatory regions outside a declared action section,
    callers may allow a short `how`/`what`/`why` question that is immediately answered;
    explicit directives and obligation grammar still apply to that prose.
    """
    clean = strip_prose_quote_markers(semantic_text(text))
    clean = strip_indented_code(strip_inline_code(clean))
    clean = MARKDOWN_LINK_RE.sub(
        lambda matched: matched.group("label"),
        clean,
    )
    return action_like_clean_text(
        strip_action_emphasis(clean),
        allow_self_answered_explanations=allow_self_answered_explanations,
    )


def action_like_plain_prose(text):
    """Recognize actions in provider text that has no Markdown semantics."""
    clean = strip_prose_quote_markers(text or "")
    return action_like_clean_text(
        strip_action_emphasis(clean),
        strip_leading_symbols=True,
        allow_self_answered_explanations=True,
    )


def action_like_summary_prose(text):
    """Recognize asks in a provider summary without treating work verbs as commands."""
    clean = strip_prose_quote_markers(text or "")
    return action_like_clean_text(
        strip_action_emphasis(clean),
        strip_leading_symbols=True,
        summary_context=True,
        allow_self_answered_explanations=True,
    )


def action_like_rendered_prose(text):
    """Recognize asks exposed by rendered HTML without granting it structure."""
    clean = strip_prose_quote_markers(rendered_human_text(text or ""))
    clean = strip_indented_code(strip_inline_code(clean))
    clean = MARKDOWN_LINK_RE.sub(
        lambda matched: matched.group("label"),
        clean,
    )
    return action_like_clean_text(
        strip_action_emphasis(clean),
        allow_self_answered_explanations=True,
    )


@functools.lru_cache(maxsize=8192)
def action_like_task_record_prose(text):
    """Recognize human/authority asks without treating ordinary task work as one.

    A task checklist is already agent-owned work state, so its checkbox and a bare
    work directive such as ``Run tests`` or ``Review changed files`` do not create a
    human action. Questions, TODOs, courtesy requests, authority verbs, explicit
    human obligations, and indirect human handoffs still do. The regex vocabulary
    remains the same centralized grammar used by provider projection checks.

    The verdict is a pure function of the exact unit text, so an edge checker that
    compares a parent snapshot with a candidate — and every later edge that carries
    the same unchanged record — reads it from the memo instead of re-running the
    whole grammar.
    """
    clean = rendered_human_text(text or "")
    clean = strip_indented_code(strip_inline_code(clean))
    clean = MARKDOWN_LINK_RE.sub(
        lambda matched: matched.group("label"),
        clean,
    )
    task_lines = []
    for line in clean.split("\n"):
        matched = TASK_LIST_ITEM_RE.match(line)
        task_lines.append(line[matched.end():] if matched else line)
    clean = "\n".join(task_lines)
    clean = strip_default_ignorable_characters(
        strip_action_emphasis(clean)
    )
    clean = re.sub(r"(?m)^[ \t]*#{1,6}[ \t]+", "", clean)
    clean = SELF_ANSWERED_EXPLANATORY_QUESTION_RE.sub(
        lambda matched: matched.group(0)[:-1] + ".",
        clean,
    )
    clean = SELF_ANSWERED_POLAR_QUESTION_RE.sub(
        lambda matched: matched.group(0)[:-1] + ".",
        clean,
    )
    if question_mark_count(clean) or TODO_RE.search(clean):
        return True
    return any(
        TASK_AUTHORITY_DIRECTIVE_RE.search(variant)
        or ADDRESSED_HUMAN_DIRECTIVE_RE.search(variant)
        or PENDING_HUMAN_ACTION_RE.search(variant)
        or TABLE_HUMAN_ACTION_RE.search(variant)
        or declarative_action_request(
            variant, patterns=TASK_HUMAN_ACTION_PATTERNS
        )
        or BOUNDARY_UNTIL_HUMAN_ACTION_RE.search(variant)
        for variant in action_prose_variants(clean)
    )


def _without_explicit_block_quotes(text):
    """Keep visible blockquotes actionable; fenced/inline code remains data."""
    return text or ""


def task_queue_path_from_destination(destination, source_path):
    """Resolve one source-relative Markdown destination to a human queue path."""
    parsed = urlsplit((destination or "").strip())
    if parsed.scheme or parsed.netloc:
        return None
    raw = unquote(parsed.path)
    if not raw or raw.startswith("/") or "\\" in raw or any(
        ord(character) < 32 or ord(character) == 127
        for character in raw
    ):
        return None
    source = Path(source_path)
    if source.is_absolute() or ".." in source.parts:
        return None
    combined = source.parent / raw
    normalized = []
    for part in combined.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not normalized:
                return None
            normalized.pop()
            continue
        normalized.append(part)
    path = Path(*normalized).as_posix()
    return path if queue_item_actor(path) == "needs-human" else None


def _task_projection_stripped_text(
    text,
    source_path,
    allowed_queue_paths,
    repo=REPO,
    candidate_revision=None,
):
    """Return rendered task prose with only exact task-owned actions removed."""
    source = _without_explicit_block_quotes(text)
    _semantic_source, matches = visible_markdown_link_source(source)
    allowed = set(allowed_queue_paths or ())
    valid_sources = []
    invalid_human_projections = []
    for matched in matches:
        destination = (
            matched.group("angle")
            if matched.group("angle") is not None
            else matched.group("bare")
        )
        label = matched.group("label")
        queue_path = task_queue_path_from_destination(
            destination, source_path
        )
        if queue_path is None:
            raw_destination = unquote(
                urlsplit((destination or "").strip()).path
            )
            if "message-queue/needs-human/" in raw_destination:
                invalid_human_projections.append(
                    "Invalid human-action projection: " + label.strip()
                )
            continue
        valid = queue_path in allowed and tracked_regular_file(
            queue_path,
            repo=repo,
            candidate_revision=candidate_revision,
        )
        canonical = (
            canonical_queue_action(
                queue_path,
                repo=repo,
                candidate_revision=candidate_revision,
            )
            if valid else None
        )
        exact_action = bool(
            canonical is not None
            and normalized_action_tokens(label)
            == normalized_action_tokens(canonical)
        )
        valid = bool(
            valid
            and canonical is not None
            and exact_action
        )
        if valid:
            valid_sources.append(matched.group(0))
        else:
            invalid_human_projections.append(
                "Invalid human-action projection: " + label.strip()
            )

    rendered = rendered_human_text(source)
    for projection_source in valid_sources:
        offset = rendered.find(projection_source)
        if offset < 0:
            continue
        rendered = (
            rendered[:offset]
            + " " * len(projection_source)
            + rendered[offset + len(projection_source):]
        )
    return rendered, invalid_human_projections


def task_action_prose_units(text):
    """Split rendered task prose into stable paragraphs and list-item units."""
    units = []
    current = []

    def flush():
        if current and any(line.strip() for line in current):
            units.append("\n".join(current).strip())
        current[:] = []

    for line in (text or "").splitlines():
        if not line.strip():
            flush()
            continue
        if LIST_ITEM_RE.match(line) or HEADING_RE.match(line):
            flush()
        current.append(line)
        if HEADING_RE.match(line):
            flush()
    flush()
    combined = []
    offset = 0
    while offset < len(units):
        unit = units[offset]
        heading = re.fullmatch(
            r"#{1,6}[ \t]+(?:how|what|why)\b[^\n?]{0,120}\?",
            unit,
            flags=re.I,
        )
        if heading and offset + 1 < len(units):
            combined.append(unit + "\n" + units[offset + 1])
            offset += 2
            continue
        combined.append(unit)
        offset += 1
    return tuple(combined)


def task_action_unit_counts(
    text,
    source_path,
    allowed_queue_paths=(),
    repo=REPO,
    candidate_revision=None,
):
    """Return a multiset of unprojected human-action units in one task artifact.

    Counter keys are normalized visible excerpts, so an edge checker can subtract
    the parent multiset from the candidate multiset without losing duplicate asks.
    """
    rendered, invalid_projections = _task_projection_stripped_text(
        text,
        source_path,
        allowed_queue_paths,
        repo=repo,
        candidate_revision=candidate_revision,
    )
    units = list(task_action_prose_units(rendered))
    units.extend(invalid_projections)
    actionable = []
    for unit in units:
        if not (
            unit.startswith("Invalid human-action projection:")
            or action_like_task_record_prose(unit)
        ):
            continue
        normalized = re.sub(
            r"\s+",
            " ",
            strip_default_ignorable_characters(unit),
        ).strip()
        if normalized:
            actionable.append(normalized)
    return Counter(actionable)


def question_mark_count(text):
    """Count punctuation questions, excluding query tokens and quoted `?` literals."""
    clean = QUOTED_QUESTION_LITERAL_RE.sub("", text or "")
    return len(QUESTION_MARK_RE.findall(clean))


def link_label_action_count(label):
    """Count actions in a short label using the visible command grammar."""
    clean = strip_action_emphasis(label or "")
    action_like = action_like_plain_prose(clean)
    verbs = len(ACTION_VERB_RE.findall(clean)) if action_like else 0
    if action_like and not verbs:
        verbs = 1
    questions = question_mark_count(label)
    todos = len(TODO_RE.findall(label or ""))
    return max(verbs, questions, todos)


def ambiguous_reference_title(label):
    """Return whether a short verb-like label can be a declarative field title."""
    clean = strip_action_emphasis(label or "")
    return bool(
        AMBIGUOUS_REFERENCE_TITLE_RE.fullmatch(clean)
        and len(ACTION_VERB_RE.findall(clean)) == 1
        and not question_mark_count(clean)
        and not TODO_RE.search(clean)
    )


def supporting_link_labels(entry, owning_destination):
    """Return non-owning labels and whether a field cue makes each a reference."""
    source, matches = visible_markdown_link_source(entry)
    supporting = []
    for matched in matches:
        destination = (
            matched.group("angle")
            if matched.group("angle") is not None
            else matched.group("bare")
        )
        if destination == owning_destination:
            continue
        prefix = source[:matched.start()]
        suffix = source[matched.end():]
        is_reference = bool(
            DECLARATIVE_REFERENCE_CUE_RE.search(prefix)
            and REFERENCE_LINK_LINE_END_RE.match(suffix)
        )
        supporting.append((matched.group("label"), is_reference))
    return supporting


def additional_action_like_prose(text):
    """Recognize a second action in prose surrounding an owning queue link."""
    clean = strip_prose_quote_markers(semantic_text(text))
    clean = strip_indented_code(strip_inline_code(clean))
    clean = strip_action_emphasis(clean)
    return action_like_clean_text(clean)


def label_projects_action(
    label,
    canonical_action,
    queue_path,
    queue_actor=None,
):
    """Bind a projected label to one Action without fuzzy semantic borrowing.

    A small neutral vocabulary remains usable per queue leaf. Every descriptive
    alternative must be an exact leading token prefix of canonical Action, so it
    cannot append an unrelated subject or stronger request.
    """
    label_tokens = normalized_action_tokens(label)
    action_tokens = normalized_action_tokens(canonical_action)
    if not label_tokens or not action_tokens:
        return False
    path_actor = queue_item_actor(queue_path)
    if queue_actor is not None \
            and path_actor not in allowed_queue_actors(queue_actor):
        return False
    if path_actor == "needs-agent":
        return label_tokens == action_tokens
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


def queue_path_from_destination(
    destination,
    allowed_url_prefixes=(),
    queue_actor="needs-human",
):
    """Resolve one unambiguous canonical queue path for the selected actor."""
    actors = allowed_queue_actors(queue_actor)
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
    valid = [
        candidate for candidate in candidates
        if queue_item_actor(candidate) in actors
    ]
    return valid[0] if len(valid) == 1 and len(candidates) == 1 else None


def git_output(args, repo=REPO):
    result = subprocess.run(
        [*RAW_GIT, *args],
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
        ["rev-parse", "--verify", f"{revision}^{{commit}}"],
        repo=repo,
    ).decode("ascii", errors="replace").strip()
    if output.casefold() != revision.casefold():
        raise ValueError("candidate revision must name its exact commit object")
    return output


def inferred_changed_task_ids(base_revision, candidate_revision, repo=REPO):
    """Infer every task a candidate carries, from records and commit audit tags.

    A candidate routinely carries more than one task and cannot be refused for
    it. `check_queue_task_reciprocity` requires a live queue item declaring
    `task:<id>` to be listed in that task's `Queue actions`, so filing one
    necessarily edits another task's record; a task that files a follow-up task,
    checks off a criterion it shipped for another task, or is claimed together
    with its child produces the same plural scope. The scope is therefore a set,
    and the projection covers all of it rather than picking one member.
    """
    base = candidate_revision_oid(base_revision, repo=repo)
    candidate = candidate_revision_oid(candidate_revision, repo=repo)
    ancestor = subprocess.run(
        [*RAW_GIT, "merge-base", "--is-ancestor", base, candidate],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if ancestor.returncode:
        raise ValueError(
            "base revision must be an ancestor of the candidate revision"
        )
    changed = git_output(
        ["diff", "--name-only", "-z", base, candidate, "--", "tasks"],
        repo=repo,
    )
    task_ids = {
        parts[2]
        for record in changed.split(b"\0")
        if record
        for parts in [
            Path(record.decode(
                "utf-8", errors="surrogateescape"
            )).parts
        ]
        if len(parts) >= 4
        and parts[0] == "tasks"
        and TASK_ID_RE.fullmatch(parts[2])
    }
    messages = git_output(
        ["log", "--format=%B%x00", f"{base}..{candidate}"],
        repo=repo,
    ).decode("utf-8", errors="replace")
    task_ids.update(
        matched.group("task")
        for matched in TASK_COMMIT_TOKEN_RE.finditer(messages)
    )
    return frozenset(task_ids)


class RepositoryView:
    """One read of one repository view, answering every path in a run.

    The index and a candidate tree are each immutable for the length of a
    single check run, so asking Git about one path at a time buys nothing and
    costs one process per question. Reading the whole view once and matching
    paths in memory returns the same verdicts: a path absent from the listing
    is the pathspec that matched nothing, and a path carrying more than one
    record is the merge-staged entry the per-path read also refused.
    """

    def __init__(self, repo=REPO, candidate_revision=None):
        self.repo = repo
        self.candidate_revision = candidate_revision
        self._records = None
        self._paths = None
        self._sizes = None
        self._texts = {}

    def _load(self):
        if self._records is not None:
            return
        if self.candidate_revision is None:
            output = git_output(["ls-files", "--stage", "-z"], repo=self.repo)
        else:
            output = git_output(
                [
                    "ls-tree", "-r", "-z",
                    self.candidate_revision,
                ],
                repo=self.repo,
            )
        records = {}
        paths = []
        for record in output.split(b"\0"):
            if not record:
                continue
            metadata, separator, encoded_path = record.partition(b"\t")
            parts = metadata.decode("ascii", errors="replace").split()
            if not separator or len(parts) != 3:
                continue
            path = encoded_path.decode("utf-8", errors="surrogateescape")
            records.setdefault(path, []).append(parts)
            paths.append(path)
        self._records = records
        self._paths = paths

    def record(self, path):
        """Return the one record naming exactly `path`, or None."""
        self._load()
        found = self._records.get(path)
        return found[0] if found is not None and len(found) == 1 else None

    def paths_under(self, prefix):
        """List every recorded path a literal directory pathspec would match.

        An empty prefix is refused rather than read as "everything": Git
        refuses it too, and a snapshot must not invent a meaning the per-path
        read never had.
        """
        if not prefix:
            raise ValueError("a candidate path prefix must not be empty")
        self._load()
        return [
            path for path in self._paths
            if path == prefix or path.startswith(prefix + "/")
        ]

    def text(self, path):
        """Return one path's decoded blob, read once per run.

        Several checks read the same queue item for different fields, so the
        blob a run needs is usually asked for more than once.
        """
        if path not in self._texts:
            object_name = (
                f":{path}" if self.candidate_revision is None
                else f"{self.candidate_revision}:{path}"
            )
            output = git_output(["show", object_name], repo=self.repo)
            try:
                self._texts[path] = output.decode("utf-8")
            except UnicodeDecodeError as error:
                raise RuntimeError(f"`{path}` is not valid UTF-8") from error
        return self._texts[path]

    def size(self, object_id):
        self._load()
        if self._sizes is None:
            self._sizes = self._read_sizes()
        if object_id not in self._sizes:
            raise RuntimeError("Git returned an invalid candidate object size")
        return self._sizes[object_id]

    def _read_sizes(self):
        """Read every recorded object's size in one batch instead of one each."""
        object_ids = []
        seen = set()
        for parts_list in self._records.values():
            for parts in parts_list:
                object_id = (
                    parts[2] if self.candidate_revision is not None else parts[1]
                )
                if object_id not in seen:
                    seen.add(object_id)
                    object_ids.append(object_id)
        if not object_ids:
            return {}
        result = subprocess.run(
            [*RAW_GIT, "cat-file", "--batch-check"],
            cwd=self.repo,
            input=("\n".join(object_ids) + "\n").encode("ascii"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                result.stderr.decode("utf-8", errors="replace").strip()
                or "could not inspect the Git candidate"
            )
        sizes = {}
        for line in result.stdout.decode("ascii", errors="replace").splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue  # a `missing` line names no size
            try:
                sizes[fields[0]] = int(fields[2])
            except ValueError:
                continue
        return sizes


_REPOSITORY_VIEWS = None


@contextlib.contextmanager
def repository_views():
    """Share one read of each repository view for the length of one run.

    Reentrant, so a caller that already opened a run is never handed a second
    view that could disagree with the first. Outside every scope each lookup
    reads Git again: a snapshot must never answer for a repository that has
    moved on since it was taken.
    """
    global _REPOSITORY_VIEWS
    if _REPOSITORY_VIEWS is not None:
        yield
        return
    _REPOSITORY_VIEWS = {}
    try:
        yield
    finally:
        _REPOSITORY_VIEWS = None


def repository_view(repo=REPO, candidate_revision=None):
    if _REPOSITORY_VIEWS is None:
        return RepositoryView(repo, candidate_revision)
    key = (str(repo), candidate_revision)
    view = _REPOSITORY_VIEWS.get(key)
    if view is None:
        view = RepositoryView(repo, candidate_revision)
        _REPOSITORY_VIEWS[key] = view
    return view


def within_one_repository_view(function):
    """Run `function` inside one shared repository-view scope."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        with repository_views():
            return function(*args, **kwargs)
    return wrapper


def candidate_record(path, repo=REPO, candidate_revision=None):
    parts = repository_view(repo, candidate_revision).record(path)
    if parts is None:
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
    return repository_view(repo, candidate_revision).size(object_id) > 0


def candidate_paths(prefix, repo=REPO, candidate_revision=None):
    return repository_view(repo, candidate_revision).paths_under(prefix)


def live_queue_paths(
    queue_actor="needs-human",
    repo=REPO,
    candidate_revision=None,
):
    actors = allowed_queue_actors(queue_actor)
    return {
        path
        for actor in actors
        for path in candidate_paths(
            f"message-queue/{actor}",
            repo=repo,
            candidate_revision=candidate_revision,
        )
        if queue_item_actor(path) == actor
        and tracked_regular_file(
            path, repo=repo, candidate_revision=candidate_revision
        )
    }


def live_human_queue_paths(repo=REPO, candidate_revision=None):
    """Backward-compatible human-only queue listing."""
    return live_queue_paths(
        "needs-human",
        repo=repo,
        candidate_revision=candidate_revision,
    )


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
    return repository_view(repo, candidate_revision).text(path)


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


def canonical_queue_external_assignment(
    path,
    repo=REPO,
    candidate_revision=None,
):
    """Return one exact opaque provider-assignment binding, if declared."""
    matches = QUEUE_EXTERNAL_ASSIGNMENT_RE.findall(
        semantic_text(
            candidate_text(
                path,
                repo=repo,
                candidate_revision=candidate_revision,
            )
        )
    )
    return matches[0].strip() if len(matches) == 1 else None


def canonical_queue_external_source(
    path,
    repo=REPO,
    candidate_revision=None,
):
    """Return one exact opaque provider-source binding, if declared."""
    matches = QUEUE_EXTERNAL_SOURCE_RE.findall(
        semantic_text(
            candidate_text(
                path,
                repo=repo,
                candidate_revision=candidate_revision,
            )
        )
    )
    return matches[0].strip() if len(matches) == 1 else None


def external_source_bindings(revision, repo=REPO):
    """Return exact External-source bindings in one immutable queue tree."""
    revision = candidate_revision_oid(revision, repo=repo)
    bindings = {}
    for path in sorted(live_queue_paths(
        "any", repo=repo, candidate_revision=revision
    )):
        matches = QUEUE_EXTERNAL_SOURCE_RE.findall(semantic_text(
            candidate_text(
                path, repo=repo, candidate_revision=revision
            )
        ))
        if len(matches) > 1:
            raise ValueError(
                f"`{path}` has more than one External source binding"
            )
        if not matches:
            continue
        identity = matches[0].strip()
        if not identity or any(
            ord(character) < 32 or ord(character) == 127
            for character in identity
        ):
            raise ValueError(
                f"`{path}` has an invalid External source binding"
            )
        bindings.setdefault(identity, set()).add(path)
    return bindings


def disappearing_external_sources(
    base_revision,
    candidate_revision,
    repo=REPO,
):
    """Return identities whose final live queue binding leaves the candidate."""
    before = external_source_bindings(base_revision, repo=repo)
    after = external_source_bindings(candidate_revision, repo=repo)
    return sorted(set(before) - set(after))


def external_source_release_states(value):
    """Validate one adapter's closed current/released source classification."""
    try:
        state = json.loads(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "external source release state must be valid JSON"
        ) from error
    if not isinstance(state, dict):
        raise ValueError("external source release state must be an object")
    unknown = sorted(set(state) - {"current", "released"})
    if unknown:
        raise ValueError(
            "external source release state has unknown field(s): "
            + ", ".join(unknown)
        )
    if set(state) != {"current", "released"}:
        raise ValueError(
            "external source release state requires current and released arrays"
        )
    parsed = {}
    all_identities = set()
    for classification in ("current", "released"):
        values = state[classification]
        if not isinstance(values, list):
            raise ValueError(
                f"external source release {classification} must be an array"
            )
        identities = set()
        for number, identity in enumerate(values, start=1):
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError(
                    f"external source release {classification} entry "
                    f"{number} must be a non-empty string"
                )
            identity = identity.strip()
            if any(
                ord(character) < 32 or ord(character) == 127
                for character in identity
            ):
                raise ValueError(
                    f"external source release {classification} entry "
                    f"{number} must be a control-free single line"
                )
            if identity in identities:
                raise ValueError(
                    f"external source release {classification} duplicates "
                    f"`{identity}`"
                )
            if identity in all_identities:
                raise ValueError(
                    f"external source release state classifies `{identity}` "
                    "more than once"
                )
            identities.add(identity)
            all_identities.add(identity)
        parsed[classification] = identities
    return parsed


@within_one_repository_view
def external_source_release_findings(
    state_value,
    base_revision,
    candidate_revision,
    repo=REPO,
):
    """Require provider release before the final canonical binding disappears."""
    state = external_source_release_states(state_value)
    disappearing = disappearing_external_sources(
        base_revision, candidate_revision, repo=repo
    )
    classified = state["current"] | state["released"]
    extras = sorted(classified - set(disappearing))
    if extras:
        raise ValueError(
            "external source release state classifies identity not disappearing "
            "from this exact base/candidate pair: "
            + ", ".join(f"`{identity}`" for identity in extras)
        )
    findings = []
    for identity in disappearing:
        if identity in state["released"]:
            continue
        if identity in state["current"]:
            findings.append(
                f"current external source `{identity}` loses its final live "
                "canonical queue binding"
            )
        else:
            findings.append(
                f"external source `{identity}` loses its final live canonical "
                "queue binding without an authoritative current/released "
                "classification"
            )
    return findings


def task_queue_paths(
    task_id,
    queue_actor="needs-human",
    repo=REPO,
    candidate_revision=None,
):
    actors = allowed_queue_actors(queue_actor)
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
    try:
        queue_paths = set(task_queue_action_paths_from_text(candidate_text(
            task_path, repo=repo, candidate_revision=candidate_revision
        )))
    except ValueError as error:
        raise RuntimeError(
            f"`{task_path}` has an invalid Queue actions field: {error}"
        ) from error
    if not queue_paths:
        return set()
    actor_paths = {
        path for path in queue_paths
        if queue_item_actor(path) in actors
    }
    non_live = sorted(
        path for path in actor_paths
        if not tracked_regular_file(
            path, repo=repo, candidate_revision=candidate_revision
        )
    )
    if non_live:
        raise RuntimeError(
            f"`{task_path}` links non-live {queue_actor} queue item(s): "
            + ", ".join(non_live)
        )
    return actor_paths


def task_human_queue_paths(task_id, repo=REPO, candidate_revision=None):
    """Backward-compatible human-only task queue listing."""
    return task_queue_paths(
        task_id,
        "needs-human",
        repo=repo,
        candidate_revision=candidate_revision,
    )


def task_scope_ids(task_scope):
    """Normalize one task scope: absent, one task id, or a set of them."""
    if task_scope is None:
        return None
    if isinstance(task_scope, str):
        task_scope = (task_scope,)
    return tuple(sorted({normalized_task_id(value) for value in task_scope}))


def task_scope_queue_paths(
    task_scope,
    queue_actor="needs-human",
    repo=REPO,
    candidate_revision=None,
):
    """Union one scope's task-owned queue paths for the selected actor."""
    paths = set()
    for task_id in task_scope_ids(task_scope) or ():
        paths.update(task_queue_paths(
            task_id,
            queue_actor,
            repo=repo,
            candidate_revision=candidate_revision,
        ))
    return paths


def required_queue_paths(
    task_scope=None,
    queue_actor="needs-human",
    repo=REPO,
    require_all_live=True,
    candidate_revision=None,
):
    if task_scope is not None:
        return task_scope_queue_paths(
            task_scope,
            queue_actor,
            repo=repo,
            candidate_revision=candidate_revision,
        )
    return (
        live_queue_paths(
            queue_actor,
            repo=repo,
            candidate_revision=candidate_revision,
        )
        if require_all_live else set()
    )


def required_human_queue_paths(
    task_scope=None,
    repo=REPO,
    require_all_live=True,
    candidate_revision=None,
):
    """Backward-compatible human-only required queue listing."""
    return required_queue_paths(
        task_scope=task_scope,
        queue_actor="needs-human",
        repo=repo,
        require_all_live=require_all_live,
        candidate_revision=candidate_revision,
    )


def external_action_state_count(value):
    """Count material top-level external actions without provider policy.

    A serialized array exposes one action per material top-level element. Any
    other material object or scalar exposes one action. Nested structure only
    determines whether its owning top-level value is empty; it does not invent
    provider-specific identities or roles.
    """
    text = (value or "").strip()
    if not text:
        return 0
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return 1

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

    if isinstance(parsed, list):
        return sum(1 for item in parsed if material(item))
    return int(material(parsed))


def material_external_action_state(value):
    """Backward-compatible boolean view of external assignment state."""
    return external_action_state_count(value) > 0


def external_assignment_states(values):
    """Return provider-neutral assignments with actor and opaque binding.

    Every input is a JSON array of objects with a non-empty opaque `identity`
    and an exact `actor` of `needs-human` or `needs-agent`. Provider adapters
    own the mapping into this closed shape and must bind a stable artifact,
    role, actor kind, and principal so another artifact cannot reuse the item.
    """
    states = []
    for input_number, value in enumerate(values, start=1):
        try:
            assignments = json.loads(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"external assignment input {input_number} must be valid JSON"
            ) from error
        if not isinstance(assignments, list):
            raise ValueError(
                f"external assignment input {input_number} must be a JSON array"
            )
        for assignment_number, assignment in enumerate(assignments, start=1):
            if not isinstance(assignment, dict):
                raise ValueError(
                    f"external assignment input {input_number}, entry "
                    f"{assignment_number} must be an object"
                )
            actor = assignment.get("actor")
            if actor not in QUEUE_ACTORS:
                raise ValueError(
                    f"external assignment input {input_number}, entry "
                    f"{assignment_number} has unknown actor {actor!r}; "
                    "expected `needs-human` or `needs-agent`"
                )
            identity = assignment.get("identity")
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError(
                    f"external assignment input {input_number}, entry "
                    f"{assignment_number} needs a non-empty string identity"
                )
            states.append((actor, identity.strip()))
    return states


def external_action_source_states(value):
    """Validate provider-neutral durable action sources.

    Each source carries its allowed next actor, an opaque provider identity,
    rendered provider prose, and an optional force flag for provider states that
    require disposition even without prose (for example, changes requested).
    Directionless provider artifacts use `any`; their bound queue paths still
    name the concrete next actor.
    """
    try:
        sources = json.loads(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "external action sources must be valid JSON"
        ) from error
    if not isinstance(sources, list):
        raise ValueError("external action sources must be a JSON array")
    states = []
    seen = set()
    for source_number, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(
                f"external action source {source_number} must be an object"
            )
        allowed_keys = {"actor", "identity", "body", "force", "url"}
        unknown = sorted(set(source) - allowed_keys)
        if unknown:
            raise ValueError(
                f"external action source {source_number} has unknown field(s): "
                + ", ".join(unknown)
            )
        actor = source.get("actor")
        if actor not in QUEUE_ACTOR_CHOICES:
            raise ValueError(
                f"external action source {source_number} has unknown actor "
                f"{actor!r}; expected `needs-human`, `needs-agent`, or `any`"
            )
        identity = source.get("identity")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError(
                f"external action source {source_number} needs a non-empty "
                "string identity"
            )
        identity = identity.strip()
        if any(ord(character) < 32 or ord(character) == 127
               for character in identity):
            raise ValueError(
                f"external action source {source_number} identity must be "
                "a control-free single line"
            )
        key = (actor, identity)
        if key in seen:
            raise ValueError(
                f"external action source {source_number} duplicates "
                f"`{identity}` for {actor}"
            )
        seen.add(key)
        body = source.get("body", "")
        if not isinstance(body, str):
            raise ValueError(
                f"external action source {source_number} body must be a string"
            )
        force = source.get("force", False)
        if not isinstance(force, bool):
            raise ValueError(
                f"external action source {source_number} force must be boolean"
            )
        url = source.get("url", "")
        if not isinstance(url, str) or any(
            ord(character) < 32 or ord(character) == 127
            for character in url
        ):
            raise ValueError(
                f"external action source {source_number} url must be a "
                "control-free single-line string"
            )
        states.append({
            "actor": actor,
            "identity": identity,
            "body": body,
            "force": force,
            "url": url.strip(),
        })
    return states


@within_one_repository_view
def projection_findings(
    text,
    titles,
    repo=REPO,
    allowed_url_prefixes=(),
    task_scope=None,
    require_all_live=True,
    candidate_revision=None,
    external_actions=(),
    external_assignments=(),
    additional_prose=(),
    additional_summaries=(),
    allow_missing_action_section_if_no_action=False,
    queue_actor="needs-human",
    required_queue_actor=None,
    require_one_action_projection=False,
):
    queue_actor = normalized_queue_actor(queue_actor)
    required_queue_actor = normalized_queue_actor(
        required_queue_actor or queue_actor
    )
    if not allowed_queue_actors(required_queue_actor).issubset(
            allowed_queue_actors(queue_actor)):
        raise ValueError(
            "required queue actor must be allowed by the projection queue actor"
        )
    no_action_text = NO_ACTION_TEXT_BY_ACTOR[queue_actor]
    actor_description = (
        "human" if queue_actor == "needs-human"
        else "agent" if queue_actor == "needs-agent"
        else "queued"
    )
    queue_link_description = (
        f"canonical {queue_actor} queue link"
        if queue_actor != "any"
        else "canonical needs-human or needs-agent queue link"
    )
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
    required_paths = required_queue_paths(
        task_scope=task_scope,
        queue_actor=required_queue_actor,
        repo=repo,
        require_all_live=require_all_live,
        candidate_revision=candidate_revision,
    )
    task_all_paths = (
        task_scope_queue_paths(
            task_scope,
            queue_actor="any",
            repo=repo,
            candidate_revision=candidate_revision,
        )
        if task_scope is not None else None
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
    for input_number, prose in enumerate(additional_summaries, start=1):
        if action_like_summary_prose(prose):
            findings.append(
                f"additional summary input {input_number} contains an action-like "
                "question or authority request outside the declared action section"
            )
    legacy_external_action_count = sum(
        external_action_state_count(value) for value in external_actions
    )
    if queue_actor == "any" and legacy_external_action_count:
        raise ValueError(
            "directionless external action state cannot be used with queue actor "
            "`any`; pass provider-neutral external assignments with actor and "
            "identity"
        )
    external_assignment_state = external_assignment_states(
        external_assignments
    )
    external_action_counts = {actor: 0 for actor in QUEUE_ACTORS}
    for actor, _identity in external_assignment_state:
        external_action_counts[actor] += 1
    if queue_actor in QUEUE_ACTORS:
        external_action_counts[queue_actor] += legacy_external_action_count
    disallowed_external_actors = [
        actor for actor, count in external_action_counts.items()
        if count and actor not in allowed_queue_actors(queue_actor)
    ]
    if disallowed_external_actors:
        raise ValueError(
            "external assignments require actor(s) not allowed by the "
            "projection queue actor: "
            + ", ".join(disallowed_external_actors)
        )
    external_action_count = sum(external_action_counts.values())
    has_external_actions = external_action_count > 0
    if not sections:
        if allow_missing_action_section_if_no_action \
                and not findings \
                and not has_external_actions \
                and not require_one_action_projection \
                and not action_like_rendered_prose(text):
            return []
        requirement = (
            "queue-linked actions"
            if require_one_action_projection
            else f"queue-linked actions or exactly `{no_action_text}`"
        )
        findings.append(
            "missing a declared action section; add `What to review` with "
            + requirement
        )
        return findings
    linked_paths = set()
    saw_entries = False
    saw_no_action = False
    invalid_projection = False
    outside_action_prose = visible_outside_action_sections(text, titles)
    if action_like_prose(
        outside_action_prose,
        allow_self_answered_explanations=True,
    ):
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
        if body.strip() == no_action_text:
            saw_no_action = True
            if required_paths:
                findings.append(
                    f"action section {section_number} claims no "
                    f"{actor_description} action "
                    "but scoped live queue item(s) exist: "
                    + ", ".join(sorted(required_paths))
                )
            elif has_external_actions:
                findings.append(
                    f"action section {section_number} claims no "
                    f"{actor_description} action "
                    "but externally assigned action state contains "
                    f"{external_action_count} action(s); project at least "
                    f"{external_action_count} distinct live canonical queue "
                    "link(s)"
                )
            elif require_one_action_projection:
                findings.append(
                    f"action section {section_number} claims no "
                    f"{actor_description} action but this provider source "
                    "structurally requires at least one live canonical queue "
                    "link"
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
                    queue_actor=queue_actor,
                )
                for _label, destination in queue_looking
            ]
            if len(queue_looking) != 1 \
                    or any(path is None for path in paths):
                invalid_projection = True
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    f"must contain exactly one valid {queue_link_description}"
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
                label
                for label, is_reference in supporting_link_labels(
                    entry, queue_looking[0][1]
                )
                if not (
                    is_reference and ambiguous_reference_title(label)
                )
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
                    queue_label,
                    canonical_action,
                    queue_path,
                    queue_actor=queue_actor):
                invalid_projection = True
                label_requirement = (
                    "exactly match"
                    if queue_item_actor(queue_path) == "needs-agent"
                    else "summarize"
                )
                findings.append(
                    f"action section {section_number}, entry {entry_number} "
                    "has a queue-link label that does not "
                    f"{label_requirement} the linked "
                    f"queue item's canonical `Action` in `{queue_path}`"
                )
                continue
            linked_paths.update(paths)
    if saw_no_action and saw_entries:
        invalid_projection = True
        findings.append(
            "a no-action acknowledgement cannot appear beside listed actions"
        )
    if not saw_no_action:
        assignment_paths = (
            linked_paths
            if task_all_paths is None
            else linked_paths.intersection(task_all_paths)
        )
        linked_action_counts = {
            actor: sum(
                queue_item_actor(path) == actor for path in assignment_paths
            )
            for actor in QUEUE_ACTORS
        }
        unmatched_assignment_paths = set(assignment_paths)
        for actor, identity in external_assignment_state:
            matches = sorted(
                path for path in unmatched_assignment_paths
                if queue_item_actor(path) == actor
                and canonical_queue_external_assignment(
                    path,
                    repo=repo,
                    candidate_revision=candidate_revision,
                ) == identity
            )
            if matches:
                unmatched_assignment_paths.remove(matches[0])
            else:
                findings.append(
                    "external assignment "
                    f"`{identity}` for {actor} has no distinct "
                    "task-owned queue action with an exact "
                    "`External assignment` binding"
                    if task_all_paths is not None else
                    "external assignment "
                    f"`{identity}` for {actor} has no distinct live queue "
                    "action with an exact `External assignment` binding"
                )
        for actor, external_count in external_action_counts.items():
            linked_count = linked_action_counts[actor]
            if linked_count < external_count:
                findings.append(
                    "externally assigned action state for "
                    f"{actor} contains {external_count} action(s), but the "
                    "declared action section projects only "
                    f"{linked_count} distinct live {actor} canonical queue "
                    "action(s)"
                )
    missing = sorted(required_paths - linked_paths)
    if missing and not saw_no_action and not invalid_projection:
        findings.append(
            "action sections omit scoped live queue item(s): " + ", ".join(missing)
        )
    return findings


@within_one_repository_view
def external_action_source_findings(
    value,
    titles,
    repo=REPO,
    allowed_url_prefixes=(),
    candidate_revision=None,
):
    """Require each active provider source to have a durable queue binding.

    A provider body may directly project its canonical queue action, but that
    presentation link does not identify the source in repository state. Every
    active source therefore also needs an actor-correct live queue item whose
    External source field carries the exact opaque identity.
    """
    states = external_action_source_states(value)
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

    all_paths = live_queue_paths(
        "any",
        repo=repo,
        candidate_revision=candidate_revision,
    )
    findings = []
    for source_number, source in enumerate(states, start=1):
        if not (
            source["force"]
            or action_like_rendered_prose(source["body"])
        ):
            continue
        direct_findings = projection_findings(
            source["body"],
            titles,
            repo=repo,
            allowed_url_prefixes=allowed_url_prefixes,
            candidate_revision=candidate_revision,
            allow_missing_action_section_if_no_action=True,
            queue_actor=source["actor"],
            require_all_live=False,
            require_one_action_projection=source["force"],
        )
        matching_paths = sorted(
            path for path in all_paths
            if canonical_queue_external_source(
                path,
                repo=repo,
                candidate_revision=candidate_revision,
            ) == source["identity"]
        )
        allowed_actors = allowed_queue_actors(source["actor"])
        actor_matches = [
            path for path in matching_paths
            if queue_item_actor(path) in allowed_actors
        ]
        context = (
            f" ({json.dumps(source['url'])})" if source["url"] else ""
        )
        if actor_matches and len(actor_matches) == len(matching_paths):
            continue
        actor_requirement = (
            source["actor"]
            if source["actor"] != "any"
            else "needs-human or needs-agent"
        )
        if matching_paths:
            findings.append(
                f"external action source {source_number} "
                f"`{source['identity']}`{context} must bind one or more live "
                f"{actor_requirement} queue items and no other actor; found: "
                + ", ".join(matching_paths)
            )
        elif not direct_findings:
            findings.append(
                f"external action source {source_number} "
                f"`{source['identity']}`{context} is directly projected but "
                f"must also bind one or more live {actor_requirement} queue "
                "items so source release remains enforceable; add "
                f"`**External source:** {source['identity']}`"
            )
        else:
            findings.append(
                f"external action source {source_number} "
                f"`{source['identity']}`{context} is not durably bound: add "
                f"one or more live {actor_requirement} queue items with "
                f"`**External source:** {source['identity']}`"
            )
    return findings


def read_input(args):
    if args.external_source_release_state_file is not None:
        try:
            return Path(args.external_source_release_state_file).read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError) as error:
            raise ValueError(str(error)) from error
    if args.external_action_sources_file is not None:
        try:
            return Path(args.external_action_sources_file).read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError) as error:
            raise ValueError(str(error)) from error
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


@within_one_repository_view
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-env", metavar="NAME")
    source.add_argument("--file", metavar="PATH|-")
    source.add_argument(
        "--external-action-sources-file",
        metavar="JSON_PATH",
        help=(
            "check provider-neutral durable action sources from one JSON array; "
            "each active source must have one exact actor-correct opaque "
            "External source binding; a direct queue link remains a projection "
            "and does not replace that durable binding"
        ),
    )
    source.add_argument(
        "--external-source-release-state-file",
        metavar="JSON_PATH",
        help=(
            "check exact base/candidate queue bindings against a trusted "
            "adapter's closed current/released source classification"
        ),
    )
    parser.add_argument(
        "--action-section", action="append", default=[], metavar="TITLE"
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
            "require distinct queue-linked projections for named external "
            "action state: each material top-level JSON array element counts "
            "once, each material object/scalar counts once, and repeated "
            "inputs add their counts; direction inherits a concrete queue actor"
        ),
    )
    parser.add_argument(
        "--external-assignment-env",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "require actor-preserving external assignment projections from a "
            "JSON array of objects with exact actor and opaque identity fields"
        ),
    )
    parser.add_argument(
        "--queue-actor",
        choices=QUEUE_ACTOR_CHOICES,
        default="needs-human",
        help=(
            "who must act next: constrain links to needs-human or needs-agent, "
            "or let each canonical path select either actor with any"
        ),
    )
    parser.add_argument(
        "--required-queue-actor",
        choices=QUEUE_ACTOR_CHOICES,
        help=(
            "optionally narrow which live queue actions task/global scope "
            "requires while allowing a broader projection actor set"
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
    parser.add_argument(
        "--additional-summary-env",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "check provider summary metadata for questions, TODOs, explicit "
            "requests, and authority commands while allowing conventional "
            "imperative change summaries"
        ),
    )
    parser.add_argument(
        "--allow-missing-action-section-if-no-action",
        action="store_true",
        help=(
            "allow ordinary provider prose to omit an action section only "
            "when the rendered body, additional prose, and external action "
            "state contain no queued-action signal"
        ),
    )
    parser.add_argument(
        "--pull-request-body-shape",
        action="store_true",
        help=(
            "also report the readability rules templates/pull-request.md makes "
            "visible — sections present and in order, summary length — as "
            "advisory lines that never change this program's exit status; only "
            "a pull-request description has that schema, so an issue body or a "
            "conversation comment never passes this"
        ),
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--task-id",
        metavar="ID|task/ID",
        help="scope required selected-actor queue links to one canonical task record",
    )
    scope.add_argument(
        "--branch",
        metavar="NAME",
        help=(
            "derive task scope from task/<id>, or from --base-revision plus "
            "changed task records/commit tags on another branch"
        ),
    )
    scope.add_argument(
        "--unscoped",
        action="store_true",
        help=(
            "explicitly check one inbound provider surface without requiring "
            "a task's complete Queue actions projection"
        ),
    )
    parser.add_argument(
        "--base-revision",
        metavar="FULL_OBJECT_ID",
        help=(
            "trusted PR base used with a non-task --branch to infer task scope "
            "from the immutable candidate"
        ),
    )
    parser.add_argument("--label", default="external projection")
    args = parser.parse_args(argv)
    try:
        text = read_input(args)
        if args.external_source_release_state_file is not None:
            incompatible = (
                args.action_section
                or args.allowed_url_prefix
                or args.external_action_env
                or args.external_assignment_env
                or args.additional_prose_env
                or args.additional_summary_env
                or args.allow_missing_action_section_if_no_action
                or args.pull_request_body_shape
                or args.task_id
                or args.branch
                or args.unscoped
                or args.required_queue_actor
                or args.queue_actor != "needs-human"
            )
            if incompatible:
                raise ValueError(
                    "--external-source-release-state-file cannot be combined "
                    "with projection, assignment, prose, or scope inputs"
                )
            if not args.base_revision or not args.candidate_revision:
                raise ValueError(
                    "--external-source-release-state-file requires exact "
                    "--base-revision and --candidate-revision"
                )
            findings = external_source_release_findings(
                text,
                args.base_revision,
                args.candidate_revision,
                repo=REPO,
            )
            for finding in findings:
                print(f"[action-projection] {args.label}: {finding}")
            print(f"action-projection: {len(findings)} finding(s)")
            return 1 if findings else 0
        if not args.action_section:
            raise ValueError(
                "projection modes require at least one --action-section"
            )
        if args.external_action_sources_file is not None:
            incompatible = (
                args.external_action_env
                or args.external_assignment_env
                or args.additional_prose_env
                or args.additional_summary_env
                or args.pull_request_body_shape
                or args.task_id
                or args.branch
                or args.unscoped
                or args.base_revision
            )
            if incompatible:
                raise ValueError(
                    "--external-action-sources-file cannot be combined with "
                    "ordinary prose, assignment, or task-scope inputs"
                )
            if not args.candidate_revision:
                raise ValueError(
                    "--external-action-sources-file requires "
                    "--candidate-revision"
                )
            findings = external_action_source_findings(
                text,
                args.action_section,
                repo=REPO,
                allowed_url_prefixes=args.allowed_url_prefix,
                candidate_revision=args.candidate_revision,
            )
            for finding in findings:
                print(f"[action-projection] {args.label}: {finding}")
            print(f"action-projection: {len(findings)} finding(s)")
            return 1 if findings else 0
        external_actions = read_env_values(args.external_action_env)
        external_assignments = read_env_values(args.external_assignment_env)
        additional_prose = read_env_values(args.additional_prose_env)
        additional_summaries = read_env_values(args.additional_summary_env)
        task_scope = args.task_id
        require_all_live = True
        if args.branch and args.branch.startswith("task/"):
            task_scope = args.branch
            if args.base_revision:
                if not args.candidate_revision:
                    raise ValueError(
                        "--base-revision requires --candidate-revision"
                    )
                inferred = inferred_changed_task_ids(
                    args.base_revision,
                    args.candidate_revision,
                    repo=REPO,
                )
                if not inferred:
                    raise ValueError(
                        "immutable candidate has no task scope evidence; "
                        "change its task record or include a `task:` commit token"
                    )
                branch_task_id = normalized_task_id(args.branch)
                if branch_task_id not in inferred:
                    raise ValueError(
                        "task branch is absent from the immutable candidate "
                        f"scope: {branch_task_id} is not in "
                        + ", ".join(sorted(inferred))
                    )
                task_scope = inferred
        elif args.branch:
            if not args.base_revision or not args.candidate_revision:
                raise ValueError(
                    "a non-task branch requires --base-revision and "
                    "--candidate-revision; use --unscoped only for an "
                    "intentionally inbound surface"
                )
            task_scope = inferred_changed_task_ids(
                args.base_revision,
                args.candidate_revision,
                repo=REPO,
            )
            if not task_scope:
                raise ValueError(
                    "immutable candidate has no task scope evidence; "
                    "change its task record or include a `task:` commit token"
                )
        elif args.unscoped:
            require_all_live = False
        elif args.base_revision:
            raise ValueError("--base-revision requires --branch")
        findings = projection_findings(
            text,
            args.action_section,
            repo=REPO,
            allowed_url_prefixes=args.allowed_url_prefix,
            task_scope=task_scope,
            require_all_live=require_all_live,
            candidate_revision=args.candidate_revision,
            external_actions=external_actions,
            external_assignments=external_assignments,
            additional_prose=additional_prose,
            additional_summaries=additional_summaries,
            allow_missing_action_section_if_no_action=(
                args.allow_missing_action_section_if_no_action
            ),
            queue_actor=args.queue_actor,
            required_queue_actor=args.required_queue_actor,
        )
    except (RuntimeError, ValueError) as error:
        print(f"action-projection: input error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(f"[action-projection] {args.label}: {finding}")
    print(f"action-projection: {len(findings)} finding(s)")
    if args.pull_request_body_shape:
        # Printed and counted on their own line, never added to the total above:
        # a readability opinion is put in front of the agent that broke it and is
        # not allowed to refuse the change.
        advisory = body_shape_findings(text)
        for finding in advisory:
            print(f"[{BODY_SHAPE_CHECK}] {args.label}: {finding}  (advisory)")
        print(
            f"{BODY_SHAPE_CHECK}: {len(advisory)} advisory finding(s) "
            "(not blocking)"
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
