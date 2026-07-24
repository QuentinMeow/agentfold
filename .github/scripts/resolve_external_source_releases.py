#!/usr/bin/env python3
"""Classify disappearing GitHub action sources from authoritative provider state."""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
AUTOMATION = REPO / "automation"
for import_root in (SCRIPT_DIR, AUTOMATION):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import check_action_projection as projection
import collect_conversation_actions as conversations
import collect_review_actions as reviews


class ProviderError(RuntimeError):
    """Provider state was unavailable, incomplete, or malformed."""


IDENTITY_RE = re.compile(
    r"^github:(?P<kind>issue|issue-comment|pull-request-review|"
    r"pull-request-review-thread):(?P<node>[^:]+):sha256:"
    r"(?P<version>[0-9a-f]{64})$"
)
NODE_QUERY = """
query AgentFoldExternalSource($id: ID!) {
  node(id: $id) {
    __typename
    ... on Issue {
      id
      title
      body
      state
      url
      repository { nameWithOwner }
    }
    ... on IssueComment {
      id
      body
      updatedAt
      url
      repository { nameWithOwner }
    }
    ... on PullRequestReview {
      id
      body
      state
      url
      repository { nameWithOwner }
    }
    ... on PullRequestReviewThread {
      id
      pullRequest {
        number
        repository { nameWithOwner }
      }
    }
  }
}
"""


def require_object(value, context):
    if not isinstance(value, dict):
        raise ProviderError(f"{context} must be an object")
    return value


def require_string(value, context, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "" if allow_empty else " non-empty"
        raise ProviderError(f"{context} must be a{qualifier} string")
    return value


def parse_repository(value):
    if not isinstance(value, str) or value.count("/") != 1:
        raise ProviderError("repository must be OWNER/NAME")
    owner, name = value.split("/")
    if not owner or not name:
        raise ProviderError("repository must be OWNER/NAME")
    return owner, name


def parse_identity(identity):
    if not isinstance(identity, str):
        raise ProviderError("external source identity must be a string")
    match = IDENTITY_RE.fullmatch(identity)
    if match is None:
        raise ProviderError(
            f"unsupported GitHub external source identity {identity!r}"
        )
    return match.groupdict()


def sha256_version(value):
    return hashlib.sha256(json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def node_from_response(payload):
    payload = require_object(payload, "GitHub GraphQL response")
    errors = payload.get("errors")
    if errors:
        raise ProviderError("GitHub GraphQL response contains errors")
    data = require_object(payload.get("data"), "GitHub GraphQL data")
    node = data.get("node")
    if node is None:
        return None
    return require_object(node, "GitHub GraphQL node")


def repository_name(node, context):
    repository = require_object(node.get("repository"), f"{context} repository")
    return require_string(
        repository.get("nameWithOwner"),
        f"{context} repository nameWithOwner",
    )


def require_expected_repository(actual, expected):
    if actual.casefold() != expected.casefold():
        raise ProviderError(
            f"external source repository {actual!r} does not match {expected!r}"
        )


def artifact_number_from_url(url, repository):
    owner, name = parse_repository(repository)
    parsed = urllib.parse.urlsplit(require_string(url, "external source url"))
    parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2] not in {"issues", "pull"}:
        raise ProviderError("external source URL has no issue or pull-request number")
    if parts[0].casefold() != owner.casefold() \
            or parts[1].casefold() != name.casefold():
        raise ProviderError("external source URL belongs to another repository")
    try:
        number = int(parts[3])
    except ValueError as error:
        raise ProviderError("external source URL has an invalid artifact number") \
            from error
    if number <= 0:
        raise ProviderError("external source URL artifact number must be positive")
    return number


def rest_object(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "agentfold-source-release-adapter",
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
        raise ProviderError(f"GitHub artifact request failed: {error}") from error
    return require_object(payload, "GitHub artifact response")


def artifact_state(request, api_url, token, repository, number):
    owner, name = parse_repository(repository)
    root = api_url.rstrip("/")
    url = (
        f"{root}/repos/{urllib.parse.quote(owner, safe='')}/"
        f"{urllib.parse.quote(name, safe='')}/issues/{number}"
    )
    artifact = request(url, token)
    state = require_string(artifact.get("state"), "GitHub artifact state")
    if state not in {"open", "closed"}:
        raise ProviderError(f"unknown GitHub artifact state {state!r}")
    closed_at = artifact.get("closed_at")
    if state == "closed":
        closed_at, closed_instant = conversations.require_timestamp(
            closed_at, "closed GitHub artifact closed_at"
        )
        return state, closed_at, closed_instant
    if closed_at is not None and not isinstance(closed_at, str):
        raise ProviderError("open GitHub artifact closed_at must be null or a string")
    return state, closed_at, None


def review_sources_for_pull(
    request,
    repository,
    number,
    cache,
):
    key = (repository.casefold(), number)
    if key not in cache:
        owner, name = parse_repository(repository)
        cache[key] = {
            source["identity"]
            for source in reviews.collect_sources(
                request, owner, name, number
            )
        }
    return cache[key]


def classify_identity(
    identity,
    node_request,
    review_request,
    artifact_request,
    api_url,
    token,
    repository,
    review_cache,
    candidate_identities=(),
):
    parsed = parse_identity(identity)
    node = node_from_response(node_request(NODE_QUERY, {"id": parsed["node"]}))
    if node is None:
        return "released"
    expected_types = {
        "issue": "Issue",
        "issue-comment": "IssueComment",
        "pull-request-review": "PullRequestReview",
        "pull-request-review-thread": "PullRequestReviewThread",
    }
    typename = require_string(node.get("__typename"), "GitHub node __typename")
    if typename != expected_types[parsed["kind"]]:
        raise ProviderError(
            f"GitHub node type {typename!r} does not match {parsed['kind']!r}"
        )
    node_id = require_string(node.get("id"), "GitHub node id")
    if node_id != parsed["node"]:
        raise ProviderError("GitHub node lookup returned a different id")

    if parsed["kind"] == "issue":
        require_expected_repository(
            repository_name(node, "GitHub issue"), repository
        )
        state = require_string(node.get("state"), "GitHub issue state")
        if state not in {"OPEN", "CLOSED"}:
            raise ProviderError(f"unknown GitHub issue state {state!r}")
        if state == "CLOSED":
            return "released"
        title = require_string(node.get("title"), "GitHub issue title")
        body = node.get("body")
        if body is None:
            body = ""
        body = require_string(body, "GitHub issue body", allow_empty=True)
        version = sha256_version({"body": body, "title": title})
        current_identity = identity.rsplit(":", 1)[0] + ":" + version
        if current_identity == identity:
            return "current"
        return (
            "released"
            if current_identity in candidate_identities
            else "current"
        )

    if parsed["kind"] == "issue-comment":
        require_expected_repository(
            repository_name(node, "GitHub issue comment"), repository
        )
        body = require_string(
            node.get("body"), "GitHub issue comment body", allow_empty=True
        )
        updated_at, updated_instant = conversations.require_timestamp(
            node.get("updatedAt"), "GitHub issue comment updatedAt"
        )
        version = sha256_version({"body": body, "updatedAt": updated_at})
        current_identity = identity.rsplit(":", 1)[0] + ":" + version
        if current_identity != identity:
            return (
                "released"
                if current_identity in candidate_identities
                else "current"
            )
        number = artifact_number_from_url(node.get("url"), repository)
        state, _closed_at, closed_instant = artifact_state(
            artifact_request, api_url, token, repository, number
        )
        if state == "closed" and updated_instant < closed_instant:
            return "released"
        return "current"

    if parsed["kind"] == "pull-request-review":
        require_expected_repository(
            repository_name(node, "GitHub pull-request review"), repository
        )
        number = artifact_number_from_url(node.get("url"), repository)
    else:
        pull_request = require_object(
            node.get("pullRequest"), "GitHub review thread pullRequest"
        )
        require_expected_repository(
            repository_name(pull_request, "GitHub review thread pullRequest"),
            repository,
        )
        number = pull_request.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ProviderError(
                "GitHub review thread pullRequest number must be positive"
            )
    state, _closed_at, _closed_instant = artifact_state(
        artifact_request, api_url, token, repository, number
    )
    if state == "closed":
        return "released"
    current = review_sources_for_pull(
        review_request, repository, number, review_cache
    )
    if identity in current:
        return "current"
    return (
        "released"
        if current.issubset(set(candidate_identities))
        else "current"
    )


def classify_sources(
    identities,
    node_request,
    review_request,
    artifact_request,
    api_url,
    token,
    repository,
    candidate_identities=(),
):
    states = {"current": [], "released": []}
    review_cache = {}
    for identity in sorted(identities):
        classification = classify_identity(
            identity,
            node_request,
            review_request,
            artifact_request,
            api_url,
            token,
            repository,
            review_cache,
            candidate_identities,
        )
        states[classification].append(identity)
    return states


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--graphql-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        parse_repository(args.repository)
        token = os.environ.get(args.token_env)
        if not token:
            raise ProviderError(
                f"environment variable {args.token_env!r} is not set"
            )
        identities = projection.disappearing_external_sources(
            args.base_revision,
            args.candidate_revision,
            repo=REPO,
        )
        candidate_identities = set(projection.external_source_bindings(
            args.candidate_revision, repo=REPO
        ))
        node_request = lambda query, variables: reviews.graphql_request(
            args.graphql_url, token, query, variables
        )
        states = classify_sources(
            identities,
            node_request,
            node_request,
            rest_object,
            args.api_url,
            token,
            args.repository,
            candidate_identities,
        )
        Path(args.output).write_text(
            json.dumps(states, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        ProviderError,
        conversations.ProviderError,
        reviews.ProviderError,
    ) as error:
        print(f"external source release adapter: {error}", file=sys.stderr)
        return 2
    print(
        "external source release adapter: "
        f"{len(states['current'])} current, "
        f"{len(states['released'])} released"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
