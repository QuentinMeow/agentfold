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

CONVERSATION_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github/scripts/collect_conversation_actions.py"
)
CONVERSATION_SPEC = importlib.util.spec_from_file_location(
    "collect_conversation_actions", CONVERSATION_MODULE_PATH
)
CONVERSATION = importlib.util.module_from_spec(CONVERSATION_SPEC)
CONVERSATION_SPEC.loader.exec_module(CONVERSATION)


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


def issue_comment(index, body="Looks good.", updated_at=None, user_type="User"):
    return {
        "node_id": f"IC_{index}",
        "body": body,
        "updated_at": updated_at or (
            f"2026-07-23T{20 + index // 60:02d}:{index % 60:02d}:00Z"
        ),
        "html_url": f"https://github.invalid/comment/{index}",
        "user": {"type": user_type},
    }


def github_event(
    action,
    comment=None,
    *,
    event_kind="issue_comment",
    issue_number=42,
    issue_state="open",
    pull_request=False,
    issue_title="Triage this issue",
    issue_body="Please investigate.",
):
    issue = {
        "number": issue_number,
        "node_id": "I_kwDOIssue",
        "state": issue_state,
        "title": issue_title,
        "body": issue_body,
        "html_url": f"https://github.invalid/issues/{issue_number}",
    }
    if issue_state == "closed":
        issue["closed_at"] = "2026-07-23T20:00:30Z"
    if pull_request:
        issue["pull_request"] = {
            "url": f"https://api.github.invalid/pulls/{issue_number}"
        }
    payload = {
        "action": action,
        "repository": {"full_name": "owner/repo"},
        "issue": issue,
    }
    if event_kind == "issue_comment":
        payload["comment"] = comment
    return payload


class CollectGitHubConversationActionsTests(unittest.TestCase):
    def test_nonempty_comments_are_structural_agent_triage(self):
        bodies = (
            "I would love your feedback.",
            "Needs owner signoff before merge.",
            "Kindly ensure the login race is fixed.",
            "Looks good.",
        )
        for index, body in enumerate(bodies):
            with self.subTest(body=body):
                source = CONVERSATION.comment_source(
                    issue_comment(index, body=body)
                )
                self.assertEqual("needs-agent", source["actor"])
                self.assertTrue(source["force"])
                self.assertEqual(body, source["body"])

        bot = CONVERSATION.comment_source(
            issue_comment(9, body="Bot handoff.", user_type="Bot")
        )
        self.assertEqual("needs-agent", bot["actor"])
        self.assertTrue(bot["force"])

    def test_blank_comment_is_inactive_and_delete_removes_only_that_node(self):
        blank = CONVERSATION.comment_source(
            issue_comment(1, body=" \n ")
        )
        self.assertFalse(blank["force"])
        retained = issue_comment(1, body="Earlier action.")
        deleted = issue_comment(2, body="Old action.")
        self.assertEqual(
            [
                CONVERSATION.comment_source(retained),
            ],
            CONVERSATION.collect_sources(
                lambda _url, _token: [retained, deleted],
                "https://api.github.invalid",
                "token",
                "owner/repo",
                42,
                payload=github_event(
                    "deleted", deleted, pull_request=True
                ),
                event_kind="issue_comment",
            ),
        )

    def test_edit_versions_identity_including_same_body_reversion(self):
        first = CONVERSATION.comment_source(issue_comment(
            1, body="A", updated_at="2026-07-23T20:00:00Z"
        ))
        edited = CONVERSATION.comment_source(issue_comment(
            1, body="B", updated_at="2026-07-23T20:01:00Z"
        ))
        reverted = CONVERSATION.comment_source(issue_comment(
            1, body="A", updated_at="2026-07-23T20:02:00Z"
        ))
        self.assertEqual(3, len({
            first["identity"],
            edited["identity"],
            reverted["identity"],
        }))

    def test_event_overlay_and_api_records_have_the_same_identity(self):
        comment = issue_comment(1, body="Review the fallback.")
        event = CONVERSATION.collect_sources(
            lambda _url, _token: [comment],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event(
                "edited", comment, pull_request=True
            ),
            event_kind="issue_comment",
        )
        api = CONVERSATION.current_sources(
            lambda _url, _token: [comment],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
        )
        self.assertEqual(event, api)

    def test_snapshot_replays_prior_comment_with_triggering_delta(self):
        prior = issue_comment(
            1,
            body="Please preserve this earlier action.",
            updated_at="2026-07-23T20:00:00Z",
        )
        triggering = issue_comment(
            2,
            body="Later comment.",
            updated_at="2026-07-23T20:01:00Z",
        )
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [prior],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event(
                "created", triggering, pull_request=True
            ),
            event_kind="issue_comment",
        )
        self.assertEqual(
            [
                CONVERSATION.comment_source(prior),
                CONVERSATION.comment_source(triggering),
            ],
            sources,
        )

    def test_event_overlay_keeps_newer_snapshot_version(self):
        event_comment = issue_comment(
            1,
            body="Old event body.",
            updated_at="2026-07-23T20:00:00Z",
        )
        current = issue_comment(
            1,
            body="Current provider body.",
            updated_at="2026-07-23T20:01:00Z",
        )
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [current],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event(
                "edited", event_comment, pull_request=True
            ),
            event_kind="issue_comment",
        )
        self.assertEqual([CONVERSATION.comment_source(current)], sources)

    def test_event_overlay_supplies_newer_version_during_api_lag(self):
        stale = issue_comment(
            1,
            body="Stale provider body.",
            updated_at="2026-07-23T20:00:00Z",
        )
        event_comment = issue_comment(
            1,
            body="Current event body.",
            updated_at="2026-07-23T20:01:00Z",
        )
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [stale],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event(
                "edited", event_comment, pull_request=True
            ),
            event_kind="issue_comment",
        )
        self.assertEqual(
            [CONVERSATION.comment_source(event_comment)], sources
        )

    def test_open_issue_event_adds_actor_neutral_artifact_source(self):
        payload = github_event(
            "edited",
            event_kind="issues",
            issue_title="Migration failure",
            issue_body="I would like the agent to investigate.",
        )
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=payload,
            event_kind="issues",
        )
        self.assertEqual(1, len(sources))
        source = sources[0]
        self.assertEqual("any", source["actor"])
        self.assertTrue(source["force"])
        self.assertEqual(payload["issue"]["body"], source["body"])
        self.assertRegex(
            source["identity"],
            r"^github:issue:I_kwDOIssue:sha256:[0-9a-f]{64}$",
        )

    def test_issue_source_versions_title_and_body_content(self):
        original = CONVERSATION.issue_source(github_event(
            "edited",
            event_kind="issues",
            issue_title="Original title",
            issue_body="Original body",
        ))[0]
        retitled = CONVERSATION.issue_source(github_event(
            "edited",
            event_kind="issues",
            issue_title="Changed title",
            issue_body="Original body",
        ))[0]
        rewritten = CONVERSATION.issue_source(github_event(
            "edited",
            event_kind="issues",
            issue_title="Original title",
            issue_body="Changed body",
        ))[0]
        self.assertEqual(3, len({
            original["identity"],
            retitled["identity"],
            rewritten["identity"],
        }))
        null_body = github_event(
            "edited",
            event_kind="issues",
            issue_title="Original title",
            issue_body=None,
        )
        source = CONVERSATION.issue_source(null_body)[0]
        self.assertEqual("", source["body"])
        self.assertTrue(source["force"])

    def test_issue_comment_event_replays_issue_artifact_and_comments(self):
        prior = issue_comment(1, body="Prior request.")
        triggering = issue_comment(2, body="New request.")
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [prior, triggering],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event("created", triggering),
            event_kind="issue_comment",
        )
        self.assertEqual("any", sources[0]["actor"])
        self.assertEqual(
            [
                CONVERSATION.comment_source(prior),
                CONVERSATION.comment_source(triggering),
            ],
            sources[1:],
        )

    def test_pull_request_and_closed_issue_do_not_emit_issue_artifact(self):
        for payload in (
            github_event(
                "created", issue_comment(1), pull_request=True
            ),
            github_event(
                "created", issue_comment(1), issue_state="closed"
            ),
        ):
            with self.subTest(issue=payload["issue"]):
                sources = CONVERSATION.collect_sources(
                    lambda _url, _token: [],
                    "https://api.github.invalid",
                    "token",
                    "owner/repo",
                    42,
                    payload=payload,
                    event_kind="issue_comment",
                )
                self.assertEqual(
                    [CONVERSATION.comment_source(payload["comment"])],
                    sources,
                )

    def test_closed_artifact_replays_only_post_closure_comment_versions(self):
        before_close = issue_comment(
            1,
            body="Resolved by closure.",
            updated_at="2026-07-23T20:00:00Z",
        )
        after_close = issue_comment(
            2,
            body="New action after closure.",
            updated_at="2026-07-23T20:01:00Z",
        )
        sources = CONVERSATION.collect_sources(
            lambda _url, _token: [before_close, after_close],
            "https://api.github.invalid",
            "token",
            "owner/repo",
            42,
            payload=github_event(
                "edited",
                after_close,
                issue_state="closed",
                pull_request=True,
            ),
            event_kind="issue_comment",
        )
        self.assertEqual(
            [CONVERSATION.comment_source(after_close)],
            sources,
        )

    def test_rest_collection_paginates(self):
        calls = []
        first = [issue_comment(index) for index in range(100)]
        last = [issue_comment(100)]

        def request(url, token):
            calls.append((url, token))
            return first if url.endswith("page=1") else last

        sources = CONVERSATION.current_sources(
            request,
            "https://api.github.invalid/",
            "token",
            "owner/repo",
            42,
        )
        self.assertEqual(101, len(sources))
        self.assertEqual(2, len(calls))
        self.assertIn("per_page=100&page=2", calls[1][0])

    def test_malformed_comment_and_event_fail_closed(self):
        bad_comments = (
            {},
            {**issue_comment(1), "body": None},
            {**issue_comment(1), "node_id": ""},
            {**issue_comment(1), "updated_at": None},
            {**issue_comment(1), "html_url": None},
        )
        for value in bad_comments:
            with self.subTest(value=value), self.assertRaises(
                CONVERSATION.ProviderError
            ):
                CONVERSATION.comment_source(value)
        bad_events = (
            github_event("future", issue_comment(1)),
            {
                **github_event("deleted", issue_comment(1)),
                "comment": {},
            },
            {
                **github_event("created", issue_comment(1)),
                "repository": {"full_name": "other/repo"},
            },
            {
                **github_event("created", issue_comment(1)),
                "issue": {
                    **github_event(
                        "created", issue_comment(1)
                    )["issue"],
                    "number": 41,
                },
            },
        )
        for payload in bad_events:
            with self.subTest(payload=payload), self.assertRaises(
                CONVERSATION.ProviderError
            ):
                CONVERSATION.collect_sources(
                    lambda _url, _token: [],
                    "https://api.github.invalid",
                    "token",
                    "owner/repo",
                    42,
                    payload=payload,
                    event_kind="issue_comment",
                )

    def test_same_timestamp_with_different_bodies_fails_closed(self):
        snapshot = issue_comment(
            1,
            body="Snapshot body.",
            updated_at="2026-07-23T20:00:00Z",
        )
        event = issue_comment(
            1,
            body="Event body.",
            updated_at="2026-07-23T20:00:00Z",
        )
        with self.assertRaises(CONVERSATION.ProviderError):
            CONVERSATION.collect_sources(
                lambda _url, _token: [snapshot],
                "https://api.github.invalid",
                "token",
                "owner/repo",
                42,
                payload=github_event(
                    "edited", event, pull_request=True
                ),
                event_kind="issue_comment",
            )


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
