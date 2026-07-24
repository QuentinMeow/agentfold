#!/usr/bin/env python3
"""Collect GitHub issue/PR conversation comments as structural action sources."""

import argparse
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


def require_object(value, context):
    if not isinstance(value, dict):
        raise ProviderError(f"{context} must be an object")
    return value


def require_string(value, context, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "" if allow_empty else " non-empty"
        raise ProviderError(f"{context} must be a{qualifier} string")
    return value


def comment_source(comment):
    comment = require_object(comment, "issue comment")
    node_id = require_string(comment.get("node_id"), "issue comment node_id")
    body = require_string(
        comment.get("body", ""), "issue comment body", allow_empty=True
    )
    updated_at = require_string(
        comment.get("updated_at"), "issue comment updated_at"
    )
    url = require_string(
        comment.get("html_url"), "issue comment html_url"
    )
    version = hashlib.sha256(json.dumps(
        {"body": body, "updatedAt": updated_at},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "actor": "needs-agent",
        "identity": (
            f"github:issue-comment:{node_id}:sha256:{version}"
        ),
        "body": body,
        "force": bool(body.strip()),
        "url": url,
    }


def event_sources(payload):
    payload = require_object(payload, "GitHub event")
    action = require_string(payload.get("action"), "GitHub event action")
    if action not in {"created", "edited", "deleted"}:
        raise ProviderError(f"unsupported issue-comment action {action!r}")
    if action == "deleted":
        return []
    return [comment_source(payload.get("comment"))]


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


def current_sources(request, api_url, token, repository, issue_number):
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise ProviderError("repository must be OWNER/NAME")
    owner, name = repository.split("/")
    if not owner or not name:
        raise ProviderError("repository must be OWNER/NAME")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ProviderError("issue number must be positive")
    root = api_url.rstrip("/")
    encoded_owner = urllib.parse.quote(owner, safe="")
    encoded_name = urllib.parse.quote(name, safe="")
    sources = []
    for page in range(1, 101):
        url = (
            f"{root}/repos/{encoded_owner}/{encoded_name}/issues/"
            f"{issue_number}/comments?per_page=100&page={page}"
        )
        comments = request(url, token)
        sources.extend(comment_source(comment) for comment in comments)
        if len(comments) < 100:
            return sources
    raise ProviderError("GitHub issue comments pagination exceeded 100 pages")


def write_sources(output, sources):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(sources, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--event-file", metavar="JSON_PATH")
    source.add_argument("--issue-number", type=int)
    parser.add_argument("--repository")
    parser.add_argument("--api-url")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.event_file:
            if args.repository or args.api_url:
                raise ProviderError(
                    "event mode cannot be combined with REST arguments"
                )
            payload = json.loads(
                Path(args.event_file).read_text(encoding="utf-8")
            )
            sources = event_sources(payload)
        else:
            if not args.repository or not args.api_url:
                raise ProviderError(
                    "REST mode requires --repository and --api-url"
                )
            token = os.environ.get(args.token_env)
            if not token:
                raise ProviderError(
                    f"environment variable {args.token_env!r} is not set"
                )
            sources = current_sources(
                rest_page,
                args.api_url,
                token,
                args.repository,
                args.issue_number,
            )
        write_sources(Path(args.output), sources)
    except (OSError, UnicodeError, ValueError, ProviderError) as error:
        print(f"conversation action collector: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
