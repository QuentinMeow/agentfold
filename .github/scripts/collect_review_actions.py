#!/usr/bin/env python3
"""Collect current GitHub review actions as provider-neutral queue sources."""

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


LATEST_REVIEWS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      latestReviews(first: 100, after: $after) {
        nodes { id body state url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

LATEST_OPINIONS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      latestOpinionatedReviews(first: 100, after: $after) {
        nodes { id body state url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

REVIEW_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        nodes {
          id
          isResolved
          comments(first: 100) {
            nodes { id body updatedAt url }
            pageInfo { hasNextPage endCursor }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

THREAD_COMMENTS_QUERY = """
query($thread: ID!, $after: String) {
  node(id: $thread) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $after) {
        nodes { id body updatedAt url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


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


def response_path(payload, *parts):
    current = require_object(payload, "GraphQL response")
    errors = current.get("errors")
    if errors:
        raise ProviderError("GraphQL response contains errors")
    if "data" not in current:
        raise ProviderError("GraphQL response has no data")
    current = current["data"]
    for part in parts:
        current = require_object(current, f"GraphQL {part} parent").get(part)
        if current is None:
            raise ProviderError(f"GraphQL response has no {part}")
    return require_object(current, "GraphQL connection")


def connection_page(connection, context):
    nodes = connection.get("nodes")
    if not isinstance(nodes, list):
        raise ProviderError(f"{context} nodes must be an array")
    page_info = require_object(
        connection.get("pageInfo"), f"{context} pageInfo"
    )
    has_next = page_info.get("hasNextPage")
    if not isinstance(has_next, bool):
        raise ProviderError(f"{context} hasNextPage must be boolean")
    cursor = page_info.get("endCursor")
    if has_next and (not isinstance(cursor, str) or not cursor):
        raise ProviderError(f"{context} next page needs an endCursor")
    if not has_next and cursor is not None and not isinstance(cursor, str):
        raise ProviderError(f"{context} endCursor must be a string or null")
    return nodes, has_next, cursor


def graphql_request(url, token, query, variables):
    body = json.dumps(
        {"query": query, "variables": variables},
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "agentfold-review-action-adapter",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", 200)
            payload = response.read()
    except (OSError, urllib.error.HTTPError) as error:
        raise ProviderError(f"GitHub GraphQL request failed: {error}") from error
    if status != 200:
        raise ProviderError(f"GitHub GraphQL returned HTTP {status}")
    try:
        return json.loads(payload)
    except (UnicodeDecodeError, ValueError) as error:
        raise ProviderError("GitHub GraphQL returned invalid JSON") from error


def fetch_pull_connection(
    request,
    query,
    connection_name,
    owner,
    name,
    number,
):
    nodes = []
    cursor = None
    seen_cursors = set()
    while True:
        if cursor is not None:
            if cursor in seen_cursors:
                raise ProviderError(
                    f"{connection_name} pagination repeated a cursor"
                )
            seen_cursors.add(cursor)
        payload = request(query, {
            "owner": owner,
            "name": name,
            "number": number,
            "after": cursor,
        })
        connection = response_path(
            payload,
            "repository",
            "pullRequest",
            connection_name,
        )
        page_nodes, has_next, cursor = connection_page(
            connection, connection_name
        )
        nodes.extend(page_nodes)
        if not has_next:
            return nodes


def fetch_thread_comments(request, thread):
    thread = require_object(thread, "review thread")
    thread_id = require_string(thread.get("id"), "review thread id")
    comments = response_path(
        {"data": {"node": {"comments": thread.get("comments")}}},
        "node",
        "comments",
    )
    nodes, has_next, cursor = connection_page(
        comments, f"review thread {thread_id} comments"
    )
    all_nodes = list(nodes)
    seen_cursors = set()
    while has_next:
        if cursor in seen_cursors:
            raise ProviderError(
                f"review thread {thread_id} comments pagination "
                "repeated a cursor"
            )
        seen_cursors.add(cursor)
        payload = request(
            THREAD_COMMENTS_QUERY,
            {"thread": thread_id, "after": cursor},
        )
        comments = response_path(payload, "node", "comments")
        nodes, has_next, cursor = connection_page(
            comments, f"review thread {thread_id} comments"
        )
        all_nodes.extend(nodes)
    return thread_id, all_nodes


def review_source(review, force=False):
    review = require_object(review, "latest review")
    review_id = require_string(review.get("id"), "latest review id")
    body = require_string(
        review.get("body", ""), "latest review body", allow_empty=True
    )
    state = require_string(review.get("state"), "latest review state")
    url = require_string(review.get("url"), "latest review url")
    if state not in {
        "APPROVED",
        "CHANGES_REQUESTED",
        "COMMENTED",
        "DISMISSED",
        "PENDING",
    }:
        raise ProviderError(f"latest review {review_id} has unknown state")
    version = hashlib.sha256(json.dumps(
        {"body": body, "state": state},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "actor": "needs-agent",
        "identity": (
            f"github:pull-request-review:{review_id}:sha256:{version}"
        ),
        "body": body,
        "force": force,
        "url": url,
    }


def thread_source(request, thread):
    thread = require_object(thread, "review thread")
    resolved = thread.get("isResolved")
    if not isinstance(resolved, bool):
        raise ProviderError("review thread isResolved must be boolean")
    thread_id, comments = fetch_thread_comments(request, thread)
    bodies = []
    version_comments = []
    urls = []
    for index, comment in enumerate(comments, start=1):
        comment = require_object(
            comment, f"review thread {thread_id} comment {index}"
        )
        comment_id = require_string(
            comment.get("id"),
            f"review thread {thread_id} comment {index} id",
        )
        body = require_string(
            comment.get("body", ""),
            f"review thread {thread_id} comment {index} body",
            allow_empty=True,
        )
        updated_at = require_string(
            comment.get("updatedAt"),
            f"review thread {thread_id} comment {index} updatedAt",
        )
        url = require_string(
            comment.get("url"),
            f"review thread {thread_id} comment {index} url",
        )
        bodies.append(body)
        urls.append(url)
        version_comments.append({
            "body": body,
            "id": comment_id,
            "updatedAt": updated_at,
        })
    if not comments:
        raise ProviderError(f"review thread {thread_id} has no comments")
    if resolved:
        return None
    version = hashlib.sha256(json.dumps(
        version_comments,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "actor": "needs-agent",
        "identity": (
            f"github:pull-request-review-thread:{thread_id}:sha256:{version}"
        ),
        "body": "\n\n".join(bodies),
        "force": True,
        "url": urls[0],
    }


def collect_sources(request, owner, name, number):
    latest = fetch_pull_connection(
        request,
        LATEST_REVIEWS_QUERY,
        "latestReviews",
        owner,
        name,
        number,
    )
    opinions = fetch_pull_connection(
        request,
        LATEST_OPINIONS_QUERY,
        "latestOpinionatedReviews",
        owner,
        name,
        number,
    )
    threads = fetch_pull_connection(
        request,
        REVIEW_THREADS_QUERY,
        "reviewThreads",
        owner,
        name,
        number,
    )

    by_identity = {}
    for review in latest:
        source = review_source(
            review,
            force=(
                review.get("state") == "COMMENTED"
                and bool(review.get("body", "").strip())
            ),
        )
        if review["state"] not in {"DISMISSED", "PENDING"}:
            by_identity[source["identity"]] = source
    for review in opinions:
        source = review_source(
            review, force=review.get("state") == "CHANGES_REQUESTED"
        )
        if review["state"] in {"DISMISSED", "PENDING"}:
            continue
        existing = by_identity.get(source["identity"])
        if existing is None:
            by_identity[source["identity"]] = source
        elif source["force"]:
            existing["force"] = True
    for thread in threads:
        source = thread_source(request, thread)
        if source is not None:
            by_identity[source["identity"]] = source
    return [by_identity[key] for key in sorted(by_identity)]


def parse_repository(value):
    if not isinstance(value, str) or value.count("/") != 1:
        raise ValueError("repository must be OWNER/NAME")
    owner, name = value.split("/")
    if not owner or not name:
        raise ValueError("repository must be OWNER/NAME")
    return owner, name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, metavar="OWNER/NAME")
    parser.add_argument("--pull-number", required=True, type=int)
    parser.add_argument("--graphql-url", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        owner, name = parse_repository(args.repository)
        if args.pull_number <= 0:
            raise ValueError("pull number must be positive")
        token = os.environ.get(args.token_env, "")
        if not token:
            raise ValueError(f"environment variable {args.token_env!r} is not set")
        request = lambda query, variables: graphql_request(
            args.graphql_url, token, query, variables
        )
        sources = collect_sources(
            request, owner, name, args.pull_number
        )
        output = Path(args.output)
        output.write_text(
            json.dumps(sources, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ProviderError, ValueError) as error:
        print(f"review-action-adapter: {error}", file=sys.stderr)
        return 2
    print(f"review-action-adapter: {len(sources)} current source(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
