#!/usr/bin/env python3
"""Collect GitHub issues and conversation comments as structural action sources."""

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class ProviderError(RuntimeError):
    """Provider state was unavailable or malformed."""


ISSUE_ACTIONS = {
    "opened",
    "edited",
    "closed",
    "reopened",
    "assigned",
    "unassigned",
}
ISSUE_COMMENT_ACTIONS = {"created", "edited", "deleted"}


def require_object(value, context):
    if not isinstance(value, dict):
        raise ProviderError(f"{context} must be an object")
    return value


def require_string(value, context, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "" if allow_empty else " non-empty"
        raise ProviderError(f"{context} must be a{qualifier} string")
    return value


def require_timestamp(value, context):
    value = require_string(value, context)
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProviderError(f"{context} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise ProviderError(f"{context} must include a timezone")
    return value, parsed


def comment_record(comment):
    comment = require_object(comment, "issue comment")
    node_id = require_string(comment.get("node_id"), "issue comment node_id")
    body = require_string(
        comment.get("body", ""), "issue comment body", allow_empty=True
    )
    updated_at, updated_instant = require_timestamp(
        comment.get("updated_at"), "issue comment updated_at"
    )
    url = require_string(comment.get("html_url"), "issue comment html_url")
    return {
        "node_id": node_id,
        "body": body,
        "updated_at": updated_at,
        "updated_instant": updated_instant,
        "url": url,
    }


def comment_source(comment):
    record = comment_record(comment)
    version = hashlib.sha256(json.dumps(
        {
            "body": record["body"],
            "updatedAt": record["updated_at"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "actor": "needs-agent",
        "identity": (
            f"github:issue-comment:{record['node_id']}:sha256:{version}"
        ),
        "body": record["body"],
        "force": bool(record["body"].strip()),
        "url": record["url"],
    }


def issue_source(payload):
    """Return the current open issue as one actor-neutral action source."""
    issue = require_object(payload.get("issue"), "GitHub event issue")
    state = require_string(issue.get("state"), "GitHub event issue state")
    if state not in {"open", "closed"}:
        raise ProviderError(f"unknown GitHub event issue state {state!r}")
    if issue.get("pull_request") is not None or state != "open":
        return []
    node_id = require_string(issue.get("node_id"), "GitHub event issue node_id")
    title = require_string(issue.get("title"), "GitHub event issue title")
    body = issue.get("body")
    if body is None:
        body = ""
    body = require_string(body, "GitHub event issue body", allow_empty=True)
    url = require_string(issue.get("html_url"), "GitHub event issue html_url")
    version = hashlib.sha256(json.dumps(
        {"body": body, "title": title},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return [{
        "actor": "any",
        "identity": f"github:issue:{node_id}:sha256:{version}",
        "body": body,
        "force": True,
        "url": url,
    }]


def validate_event_scope(payload, event_kind, repository, issue_number):
    payload = require_object(payload, "GitHub event")
    if event_kind not in {"issues", "issue_comment"}:
        raise ProviderError(f"unsupported GitHub event kind {event_kind!r}")
    event_repository = require_object(
        payload.get("repository"), "GitHub event repository"
    )
    full_name = require_string(
        event_repository.get("full_name"),
        "GitHub event repository full_name",
    )
    if full_name != repository:
        raise ProviderError(
            f"GitHub event repository {full_name!r} does not match "
            f"{repository!r}"
        )
    issue = require_object(payload.get("issue"), "GitHub event issue")
    number = issue.get("number")
    if not isinstance(number, int) or isinstance(number, bool):
        raise ProviderError("GitHub event issue number must be an integer")
    if number != issue_number:
        raise ProviderError(
            f"GitHub event issue number {number!r} does not match "
            f"{issue_number!r}"
        )
    action = require_string(payload.get("action"), "GitHub event action")
    allowed = ISSUE_ACTIONS if event_kind == "issues" else ISSUE_COMMENT_ACTIONS
    if action not in allowed:
        raise ProviderError(
            f"unsupported {event_kind.replace('_', '-')} action {action!r}"
        )
    return action


def rest_page(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "agentfold-conversation-action-adapter",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        OSError,
        UnicodeError,
        ValueError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ) as error:
        raise ProviderError(f"GitHub issue comments request failed: {error}")
    if not isinstance(payload, list):
        raise ProviderError("GitHub issue comments response must be an array")
    return payload


def validate_repository_and_issue(repository, issue_number):
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise ProviderError("repository must be OWNER/NAME")
    owner, name = repository.split("/")
    if not owner or not name:
        raise ProviderError("repository must be OWNER/NAME")
    if (
        not isinstance(issue_number, int)
        or isinstance(issue_number, bool)
        or issue_number <= 0
    ):
        raise ProviderError("issue number must be positive")
    return owner, name


def current_comments(request, api_url, token, repository, issue_number):
    owner, name = validate_repository_and_issue(repository, issue_number)
    root = api_url.rstrip("/")
    encoded_owner = urllib.parse.quote(owner, safe="")
    encoded_name = urllib.parse.quote(name, safe="")
    comments = []
    for page in range(1, 101):
        url = (
            f"{root}/repos/{encoded_owner}/{encoded_name}/issues/"
            f"{issue_number}/comments?per_page=100&page={page}"
        )
        page_comments = request(url, token)
        if not isinstance(page_comments, list):
            raise ProviderError(
                "GitHub issue comments response must be an array"
            )
        comments.extend(page_comments)
        if len(page_comments) < 100:
            return comments
    raise ProviderError("GitHub issue comments pagination exceeded 100 pages")


def overlay_event_comment(comments, payload, action):
    """Merge the triggering delta with a provider snapshot without dropping peers."""
    by_node = {}
    for comment in comments:
        record = comment_record(comment)
        if record["node_id"] in by_node:
            raise ProviderError(
                "GitHub issue comments snapshot repeats node_id "
                f"{record['node_id']!r}"
            )
        by_node[record["node_id"]] = comment

    event_comment = require_object(
        payload.get("comment"), "GitHub event issue comment"
    )
    event_node = require_string(
        event_comment.get("node_id"), "GitHub event issue comment node_id"
    )
    if action == "deleted":
        by_node.pop(event_node, None)
    else:
        event_record = comment_record(event_comment)
        current = by_node.get(event_node)
        if current is None:
            by_node[event_node] = event_comment
        else:
            current_record = comment_record(current)
            if event_record["updated_instant"] > current_record["updated_instant"]:
                by_node[event_node] = event_comment
            elif (
                event_record["updated_instant"]
                == current_record["updated_instant"]
                and event_record["body"] != current_record["body"]
            ):
                raise ProviderError(
                    "GitHub issue comment event and snapshot disagree at the "
                    f"same updated_at for node_id {event_node!r}"
                )
    return [by_node[node_id] for node_id in sorted(by_node)]


def live_comments_for_issue(comments, payload):
    """Apply the provider artifact's documented closure boundary."""
    issue = require_object(payload.get("issue"), "GitHub event issue")
    state = require_string(issue.get("state"), "GitHub event issue state")
    if state == "open":
        return comments
    if state != "closed":
        raise ProviderError(f"unknown GitHub event issue state {state!r}")
    _closed_at, closed_instant = require_timestamp(
        issue.get("closed_at"), "closed GitHub event issue closed_at"
    )
    live = []
    for comment in comments:
        record = comment_record(comment)
        if record["updated_instant"] >= closed_instant:
            live.append(comment)
    return live


def collect_sources(
    request,
    api_url,
    token,
    repository,
    issue_number,
    payload=None,
    event_kind=None,
):
    sources = []
    if payload is not None:
        action = validate_event_scope(
            payload, event_kind, repository, issue_number
        )
        sources.extend(issue_source(payload))
    elif event_kind is not None:
        raise ProviderError("event kind requires an event payload")
    comments = current_comments(
        request, api_url, token, repository, issue_number
    )
    if payload is not None:
        if event_kind == "issue_comment":
            comments = overlay_event_comment(comments, payload, action)
        comments = live_comments_for_issue(comments, payload)
    sources.extend(comment_source(comment) for comment in comments)
    return sources


def current_sources(request, api_url, token, repository, issue_number):
    return collect_sources(
        request, api_url, token, repository, issue_number
    )


def write_sources(output, sources):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(sources, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-file", metavar="JSON_PATH")
    parser.add_argument(
        "--event-kind", choices=("issues", "issue_comment")
    )
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if bool(args.event_file) != bool(args.event_kind):
            raise ProviderError(
                "--event-file and --event-kind must be provided together"
            )
        token = os.environ.get(args.token_env)
        if not token:
            raise ProviderError(
                f"environment variable {args.token_env!r} is not set"
            )
        payload = None
        if args.event_file:
            payload = json.loads(
                Path(args.event_file).read_text(encoding="utf-8")
            )
        sources = collect_sources(
            rest_page,
            args.api_url,
            token,
            args.repository,
            args.issue_number,
            payload=payload,
            event_kind=args.event_kind,
        )
        write_sources(Path(args.output), sources)
    except (OSError, UnicodeError, ValueError, ProviderError) as error:
        print(f"conversation action collector: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
