import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github/scripts/resolve_external_source_releases.py"
)
SPEC = importlib.util.spec_from_file_location(
    "resolve_external_source_releases", MODULE_PATH
)
RESOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOLVER)


REPOSITORY = "owner/repo"
API_URL = "https://api.github.invalid"
TOKEN = "token"


def identity(kind, node_id, version):
    return f"github:{kind}:{node_id}:sha256:{version}"


def node_response(node):
    return {"data": {"node": node}}


def artifact(state="open", closed_at=None):
    return {"state": state, "closed_at": closed_at}


class GitHubExternalSourceReleaseTests(unittest.TestCase):
    def classify(
        self,
        source_identity,
        node,
        artifact_payload=None,
        candidate_identities=(),
    ):
        return RESOLVER.classify_identity(
            source_identity,
            lambda _query, _variables: node_response(node),
            lambda _query, _variables: {},
            lambda _url, _token: artifact_payload or artifact(),
            API_URL,
            TOKEN,
            REPOSITORY,
            {},
            candidate_identities,
        )

    def test_open_issue_exact_version_is_current(self):
        version = RESOLVER.sha256_version({
            "body": "Please investigate.",
            "title": "Unexpected result",
        })
        source_identity = identity("issue", "ISSUE_1", version)
        node = {
            "__typename": "Issue",
            "id": "ISSUE_1",
            "title": "Unexpected result",
            "body": "Please investigate.",
            "state": "OPEN",
            "url": "https://github.invalid/owner/repo/issues/1",
            "repository": {"nameWithOwner": REPOSITORY},
        }
        self.assertEqual("current", self.classify(source_identity, node))
        node["body"] = "Edited request."
        self.assertEqual("current", self.classify(source_identity, node))
        replacement = identity(
            "issue",
            "ISSUE_1",
            RESOLVER.sha256_version({
                "body": "Edited request.",
                "title": "Unexpected result",
            }),
        )
        self.assertEqual(
            "released",
            self.classify(
                source_identity,
                node,
                candidate_identities={replacement},
            ),
        )
        node["state"] = "CLOSED"
        self.assertEqual("released", self.classify(source_identity, node))

    def test_issue_null_body_matches_empty_body_identity(self):
        version = RESOLVER.sha256_version({"body": "", "title": "Triage"})
        source_identity = identity("issue", "ISSUE_2", version)
        node = {
            "__typename": "Issue",
            "id": "ISSUE_2",
            "title": "Triage",
            "body": None,
            "state": "OPEN",
            "url": "https://github.invalid/owner/repo/issues/2",
            "repository": {"nameWithOwner": REPOSITORY},
        }
        self.assertEqual("current", self.classify(source_identity, node))

    def test_issue_comment_uses_version_and_artifact_closure_boundary(self):
        version = RESOLVER.sha256_version({
            "body": "Please fix this.",
            "updatedAt": "2026-07-23T20:00:00Z",
        })
        source_identity = identity("issue-comment", "COMMENT_1", version)
        node = {
            "__typename": "IssueComment",
            "id": "COMMENT_1",
            "body": "Please fix this.",
            "updatedAt": "2026-07-23T20:00:00Z",
            "url": (
                "https://github.invalid/owner/repo/issues/"
                "7#issuecomment-1"
            ),
            "repository": {"nameWithOwner": REPOSITORY},
        }
        self.assertEqual("current", self.classify(source_identity, node))
        self.assertEqual(
            "released",
            self.classify(
                source_identity,
                node,
                artifact("closed", "2026-07-23T20:01:00Z"),
            ),
        )
        self.assertEqual(
            "current",
            self.classify(
                source_identity,
                node,
                artifact("closed", "2026-07-23T19:59:00Z"),
            ),
        )
        node["body"] = "Edited request."
        self.assertEqual("current", self.classify(source_identity, node))
        replacement = identity(
            "issue-comment",
            "COMMENT_1",
            RESOLVER.sha256_version({
                "body": "Edited request.",
                "updatedAt": "2026-07-23T20:00:00Z",
            }),
        )
        self.assertEqual(
            "released",
            self.classify(
                source_identity,
                node,
                candidate_identities={replacement},
            ),
        )

    def test_deleted_node_is_released_and_wrong_node_type_fails(self):
        version = "a" * 64
        source_identity = identity("issue-comment", "COMMENT_2", version)
        self.assertEqual(
            "released",
            self.classify(source_identity, None),
        )
        with self.assertRaises(RESOLVER.ProviderError):
            self.classify(source_identity, {
                "__typename": "Issue",
                "id": "COMMENT_2",
            })

    def test_review_and_thread_replay_current_pr_state(self):
        review_version = RESOLVER.sha256_version({
            "body": "Please adjust this.",
            "state": "COMMENTED",
        })
        review_identity = identity(
            "pull-request-review", "REVIEW_1", review_version
        )
        review_node = {
            "__typename": "PullRequestReview",
            "id": "REVIEW_1",
            "body": "Please adjust this.",
            "state": "COMMENTED",
            "url": (
                "https://github.invalid/owner/repo/pull/"
                "9#pullrequestreview-1"
            ),
            "repository": {"nameWithOwner": REPOSITORY},
        }
        thread_identity = identity(
            "pull-request-review-thread", "THREAD_1", "b" * 64
        )
        thread_node = {
            "__typename": "PullRequestReviewThread",
            "id": "THREAD_1",
            "pullRequest": {
                "number": 9,
                "repository": {"nameWithOwner": REPOSITORY},
            },
        }
        for source_identity, node in (
            (review_identity, review_node),
            (thread_identity, thread_node),
        ):
            with self.subTest(identity=source_identity), mock.patch.object(
                RESOLVER,
                "review_sources_for_pull",
                return_value={source_identity},
            ):
                self.assertEqual(
                    "current", self.classify(source_identity, node)
                )
            with mock.patch.object(
                RESOLVER,
                "review_sources_for_pull",
                return_value=set(),
            ):
                self.assertEqual(
                    "released", self.classify(source_identity, node)
                )

    def test_superseding_review_must_be_bound_before_old_release(self):
        old = identity("pull-request-review", "REVIEW_3", "c" * 64)
        replacement = identity(
            "pull-request-review", "REVIEW_4", "d" * 64
        )
        node = {
            "__typename": "PullRequestReview",
            "id": "REVIEW_3",
            "body": "Old request.",
            "state": "COMMENTED",
            "url": (
                "https://github.invalid/owner/repo/pull/"
                "11#pullrequestreview-3"
            ),
            "repository": {"nameWithOwner": REPOSITORY},
        }
        with mock.patch.object(
            RESOLVER,
            "review_sources_for_pull",
            return_value={replacement},
        ):
            self.assertEqual("current", self.classify(old, node))
            self.assertEqual(
                "released",
                self.classify(
                    old,
                    node,
                    candidate_identities={replacement},
                ),
            )

    def test_closed_pull_releases_review_without_replay(self):
        version = RESOLVER.sha256_version({
            "body": "Please adjust this.",
            "state": "COMMENTED",
        })
        source_identity = identity(
            "pull-request-review", "REVIEW_2", version
        )
        node = {
            "__typename": "PullRequestReview",
            "id": "REVIEW_2",
            "body": "Please adjust this.",
            "state": "COMMENTED",
            "url": (
                "https://github.invalid/owner/repo/pull/"
                "10#pullrequestreview-2"
            ),
            "repository": {"nameWithOwner": REPOSITORY},
        }
        with mock.patch.object(
            RESOLVER, "review_sources_for_pull"
        ) as replay:
            self.assertEqual(
                "released",
                self.classify(
                    source_identity,
                    node,
                    artifact("closed", "2026-07-23T20:00:00Z"),
                ),
            )
            replay.assert_not_called()

    def test_unknown_identity_and_provider_failures_fail_closed(self):
        with self.assertRaises(RESOLVER.ProviderError):
            RESOLVER.parse_identity(
                "other:issue:ISSUE_1:sha256:" + ("a" * 64)
            )
        with self.assertRaises(RESOLVER.ProviderError):
            RESOLVER.node_from_response({"errors": [{"message": "denied"}]})
        with self.assertRaises(RESOLVER.ProviderError):
            RESOLVER.artifact_state(
                lambda _url, _token: {"state": "future"},
                API_URL,
                TOKEN,
                REPOSITORY,
                1,
            )

    def test_classification_output_is_closed_and_sorted(self):
        first = identity("issue", "A", "a" * 64)
        second = identity("issue", "B", "b" * 64)
        nodes = {
            "A": None,
            "B": {
                "__typename": "Issue",
                "id": "B",
                "title": "Title",
                "body": "Body",
                "state": "CLOSED",
                "url": "https://github.invalid/owner/repo/issues/2",
                "repository": {"nameWithOwner": REPOSITORY},
            },
        }
        output = RESOLVER.classify_sources(
            [second, first],
            lambda _query, variables: node_response(nodes[variables["id"]]),
            lambda _query, _variables: {},
            lambda _url, _token: artifact(),
            API_URL,
            TOKEN,
            REPOSITORY,
            set(),
        )
        self.assertEqual({"current": [], "released": [first, second]}, output)


if __name__ == "__main__":
    unittest.main()
