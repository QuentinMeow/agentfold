import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github/scripts/collect_review_actions.py"
)
SPEC = importlib.util.spec_from_file_location(
    "collect_review_actions", MODULE_PATH
)
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


def payload(connection_name, nodes, has_next=False, cursor=None):
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    connection_name: {
                        "nodes": nodes,
                        "pageInfo": {
                            "hasNextPage": has_next,
                            "endCursor": cursor,
                        },
                    },
                },
            },
        },
    }


def review(review_id, body="", state="COMMENTED"):
    return {
        "id": review_id,
        "body": body,
        "state": state,
        "url": f"https://github.invalid/review/{review_id}",
    }


def thread(thread_id, resolved=False, comments=None, has_next=False):
    return {
        "id": thread_id,
        "isResolved": resolved,
        "comments": {
            "nodes": comments or [{
                "id": f"{thread_id}-comment-one",
                "body": "Please fix the race.",
                "updatedAt": "2026-07-23T20:00:00Z",
                "url": f"https://github.invalid/thread/{thread_id}",
            }],
            "pageInfo": {
                "hasNextPage": has_next,
                "endCursor": "comment-page-2" if has_next else None,
            },
        },
    }


class CollectGitHubReviewActionsTests(unittest.TestCase):
    def test_effective_formal_reviews_are_forced_structurally(self):
        body = "This needs to be repaired before merge."

        def request(query, variables):
            if query == COLLECTOR.LATEST_REVIEWS_QUERY:
                return payload("latestReviews", [
                    review("commented-action", body, "COMMENTED"),
                    review("approved-prose", "Looks good.", "APPROVED"),
                    review("changes-empty", "", "CHANGES_REQUESTED"),
                    review("empty-comment", "", "COMMENTED"),
                ])
            if query == COLLECTOR.LATEST_OPINIONS_QUERY:
                return payload("latestOpinionatedReviews", [
                    review(
                        "opinion-approved",
                        "One remaining typo should be fixed.",
                        "APPROVED",
                    ),
                    review("opinion-blank", "   ", "APPROVED"),
                ])
            return payload("reviewThreads", [])

        sources = COLLECTOR.collect_sources(
            request, "owner", "repo", 42
        )
        by_body = {source["body"]: source for source in sources}
        self.assertEqual("needs-agent", by_body[body]["actor"])
        self.assertTrue(by_body[body]["force"])
        self.assertTrue(by_body["Looks good."]["force"])
        self.assertTrue(
            by_body["One remaining typo should be fixed."]["force"]
        )
        self.assertFalse(by_body["   "]["force"])
        empty_sources = [
            source for source in sources if source["body"] == ""
        ]
        self.assertEqual(2, len(empty_sources))
        self.assertEqual(
            [False, True],
            sorted(source["force"] for source in empty_sources),
        )
        changes_source = next(
            source for source in empty_sources
            if ":changes-empty:" in source["identity"]
        )
        empty_comment_source = next(
            source for source in empty_sources
            if ":empty-comment:" in source["identity"]
        )
        self.assertTrue(changes_source["force"])
        self.assertFalse(empty_comment_source["force"])

    def test_collects_paginated_latest_reviews_opinions_and_threads(self):
        calls = []

        def request(query, variables):
            calls.append((query, variables.copy()))
            cursor = variables.get("after")
            if query == COLLECTOR.LATEST_REVIEWS_QUERY:
                if cursor is None:
                    return payload(
                        "latestReviews",
                        [review("review-one", "Please check the migration.")],
                        has_next=True,
                        cursor="review-page-2",
                    )
                self.assertEqual("review-page-2", cursor)
                return payload(
                    "latestReviews",
                    [review("review-two", state="APPROVED")],
                )
            if query == COLLECTOR.LATEST_OPINIONS_QUERY:
                return payload(
                    "latestOpinionatedReviews",
                    [review(
                        "review-three",
                        state="CHANGES_REQUESTED",
                    )],
                )
            if query == COLLECTOR.REVIEW_THREADS_QUERY:
                return payload(
                    "reviewThreads",
                    [
                        thread("thread-open", has_next=True),
                        thread("thread-resolved", resolved=True),
                    ],
                )
            if query == COLLECTOR.THREAD_COMMENTS_QUERY:
                self.assertEqual("thread-open", variables["thread"])
                self.assertEqual("comment-page-2", cursor)
                return {
                    "data": {
                        "node": {
                            "comments": {
                                "nodes": [{
                                    "id": "thread-open-comment-two",
                                    "body": "The exact case is login.",
                                    "updatedAt": "2026-07-23T20:01:00Z",
                                    "url": (
                                        "https://github.invalid/"
                                        "thread/thread-open#reply"
                                    ),
                                }],
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": None,
                                },
                            },
                        },
                    },
                }
            self.fail("unexpected query")

        sources = COLLECTOR.collect_sources(
            request, "owner", "repo", 42
        )
        identities = {source["identity"]: source for source in sources}
        expected_prefixes = {
            "github:pull-request-review:review-one:sha256:",
            "github:pull-request-review:review-two:sha256:",
            "github:pull-request-review:review-three:sha256:",
            "github:pull-request-review-thread:thread-open:sha256:",
        }
        self.assertEqual(
            expected_prefixes,
            {
                identity.rsplit(":", 1)[0] + ":"
                for identity in identities
            },
        )
        opinion = next(
            source for identity, source in identities.items()
            if identity.startswith(
                "github:pull-request-review:review-three:sha256:"
            )
        )
        self.assertTrue(
            opinion["force"]
        )
        thread_source = next(
            source for identity, source in identities.items()
            if identity.startswith(
                "github:pull-request-review-thread:thread-open:sha256:"
            )
        )
        self.assertTrue(thread_source["force"])
        self.assertIn("The exact case is login.", thread_source["body"])
        self.assertFalse(any(
            identity.startswith(
                "github:pull-request-review-thread:thread-resolved:"
            )
            for identity in identities
        ))
        self.assertGreaterEqual(len(calls), 5)

    def test_opinion_force_merges_with_same_latest_review(self):
        same = review("same", "One remaining typo should be fixed.", "APPROVED")

        def request(query, variables):
            name = (
                "latestReviews"
                if query == COLLECTOR.LATEST_REVIEWS_QUERY
                else "latestOpinionatedReviews"
                if query == COLLECTOR.LATEST_OPINIONS_QUERY
                else "reviewThreads"
            )
            return payload(
                name,
                [] if name == "reviewThreads" else [same],
            )

        sources = COLLECTOR.collect_sources(
            request, "owner", "repo", 9
        )
        self.assertEqual(1, len(sources))
        self.assertTrue(sources[0]["force"])

    def test_dismissed_and_pending_reviews_are_not_current_sources(self):
        def request(query, variables):
            if query == COLLECTOR.LATEST_REVIEWS_QUERY:
                return payload("latestReviews", [
                    review("dismissed", "Please fix.", "DISMISSED"),
                    review("pending", "Please fix.", "PENDING"),
                ])
            if query == COLLECTOR.LATEST_OPINIONS_QUERY:
                return payload("latestOpinionatedReviews", [])
            return payload("reviewThreads", [])

        self.assertEqual(
            [],
            COLLECTOR.collect_sources(request, "owner", "repo", 3),
        )

    def test_edits_version_sources_and_reopened_threads_resurface(self):
        first = COLLECTOR.review_source(
            review("same-review", "Please fix A.")
        )
        edited = COLLECTOR.review_source(
            review("same-review", "Please fix B.")
        )
        self.assertNotEqual(first["identity"], edited["identity"])

        open_thread = thread("same-thread")
        reopened = COLLECTOR.thread_source(
            lambda _query, _variables: {},
            open_thread,
        )
        self.assertIsNotNone(reopened)
        resolved = {**open_thread, "isResolved": True}
        self.assertIsNone(COLLECTOR.thread_source(
            lambda _query, _variables: {},
            resolved,
        ))
        edited_thread = thread("same-thread", comments=[{
            "id": "same-thread-comment-one",
            "body": "Please fix a different race.",
            "updatedAt": "2026-07-23T21:00:00Z",
            "url": "https://github.invalid/thread/same-thread",
        }])
        edited_source = COLLECTOR.thread_source(
            lambda _query, _variables: {},
            edited_thread,
        )
        self.assertNotEqual(
            reopened["identity"], edited_source["identity"]
        )

    def test_provider_shapes_fail_closed(self):
        malformed = (
            {},
            {"errors": [{"message": "no"}]},
            {"data": {"repository": None}},
            payload("latestReviews", "not-a-list"),
            payload(
                "latestReviews",
                [],
                has_next=True,
                cursor=None,
            ),
        )
        for response in malformed:
            with self.subTest(response=response), self.assertRaises(
                COLLECTOR.ProviderError
            ):
                COLLECTOR.fetch_pull_connection(
                    lambda _query, _variables: response,
                    COLLECTOR.LATEST_REVIEWS_QUERY,
                    "latestReviews",
                    "owner",
                    "repo",
                    1,
                )
        repeated = payload(
            "latestReviews",
            [],
            has_next=True,
            cursor="same-cursor",
        )
        with self.assertRaises(COLLECTOR.ProviderError):
            COLLECTOR.fetch_pull_connection(
                lambda _query, _variables: repeated,
                COLLECTOR.LATEST_REVIEWS_QUERY,
                "latestReviews",
                "owner",
                "repo",
                1,
            )

    def test_record_fields_fail_closed(self):
        bad_reviews = (
            {},
            review("", state="COMMENTED"),
            {**review("id"), "body": 4},
            {**review("id"), "state": "FUTURE_STATE"},
            {**review("id"), "url": None},
        )
        for value in bad_reviews:
            with self.subTest(value=value), self.assertRaises(
                COLLECTOR.ProviderError
            ):
                COLLECTOR.review_source(value)
        with self.assertRaises(COLLECTOR.ProviderError):
            COLLECTOR.thread_source(
                lambda _query, _variables: {},
                {"id": "thread", "isResolved": "false", "comments": {}},
            )

    def test_cli_writes_sources_without_local_gh_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sources.json"
            with mock.patch.dict(
                "os.environ", {"GITHUB_TOKEN": "ephemeral-token"}
            ), mock.patch.object(
                COLLECTOR,
                "collect_sources",
                return_value=[],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    COLLECTOR.main([
                        "--repository", "owner/repo",
                        "--pull-number", "7",
                        "--graphql-url", "https://api.github.invalid/graphql",
                        "--output", str(output),
                    ]),
                )
            self.assertEqual([], json.loads(output.read_text(encoding="utf-8")))

    def test_cli_fails_without_ephemeral_workflow_token(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            "os.environ", {}, clear=True
        ), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                2,
                COLLECTOR.main([
                    "--repository", "owner/repo",
                    "--pull-number", "7",
                    "--graphql-url", "https://api.github.invalid/graphql",
                    "--output", str(Path(tmp) / "sources.json"),
                ]),
            )


if __name__ == "__main__":
    unittest.main()
