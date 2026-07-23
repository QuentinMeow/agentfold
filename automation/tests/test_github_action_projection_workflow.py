#!/usr/bin/env python3
"""Static event, trust, candidate, and actor matrix for the GitHub adapter."""
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github/workflows/harness.yml"
JOB_HEADER_RE = re.compile(r"^  (?P<name>[a-z][a-z0-9-]*):\n", re.MULTILINE)


class GitHubActionProjectionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def job(self, name):
        matches = list(JOB_HEADER_RE.finditer(self.workflow))
        for index, match in enumerate(matches):
            if match.group("name") != name:
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) \
                else len(self.workflow)
            return self.workflow[match.start():end]
        self.fail(f"missing workflow job {name!r}")

    def step(self, job_name, step_name):
        job = self.job(job_name)
        marker = f"      - name: {step_name}\n"
        _before, separator, remainder = job.partition(marker)
        self.assertTrue(separator, f"missing workflow step {step_name!r}")
        return remainder.partition("      - name: ")[0]

    def assert_contains_all(self, text, expected_values):
        for expected in expected_values:
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_event_matrix_registers_authoritative_and_advisory_surfaces(self):
        on_block = self.workflow.partition("on:\n")[2].partition(
            "\npermissions:"
        )[0]
        pr_types = (
            "[opened, edited, reopened, synchronize, ready_for_review, "
            "review_requested, review_request_removed, assigned, unassigned]"
        )
        self.assertIn(f"pull_request:\n    types: {pr_types}", on_block)
        self.assertIn(f"pull_request_target:\n    types: {pr_types}", on_block)
        self.assertIn(
            "issues:\n"
            "    types: [opened, edited, reopened, assigned, unassigned]",
            on_block,
        )
        self.assertIn(
            "issue_comment:\n    types: [created, edited]", on_block
        )
        self.assertIn(
            "pull_request_review:\n    types: [submitted, edited]", on_block
        )
        self.assertIn(
            "pull_request_review_comment:\n    types: [created, edited]",
            on_block,
        )

    def test_authoritative_pr_state_uses_target_base_code_and_merge_data(self):
        job = self.job("authoritative-external-action-projection")
        self.assertIn(
            "name: Authoritative action projection from trusted workflow code",
            job,
        )
        checkout = self.step(
            "authoritative-external-action-projection",
            "Checkout trusted PR-base projection gate",
        )
        self.assertIn(
            "if: ${{ github.event_name == 'pull_request_target' }}", checkout
        )
        self.assertIn(
            "ref: ${{ github.event.pull_request.base.sha }}", checkout
        )
        fetch = self.step(
            "authoritative-external-action-projection",
            "Fetch immutable PR candidate without checking it out",
        )
        self.assert_contains_all(fetch, (
            '"refs/pull/$ACTION_PROJECTION_PR_NUMBER/merge"',
            "github.event.pull_request.merge_commit_sha",
            'rev-parse --verify "FETCH_HEAD^{commit}"',
            '>> "$GITHUB_OUTPUT"',
        ))
        projection = self.step(
            "authoritative-external-action-projection",
            "Action projection — pull-request description and state",
        )
        self.assert_contains_all(projection, (
            "if: ${{ github.event_name == 'pull_request_target' }}",
            "ACTION_PROJECTION_BODY: ${{ github.event.pull_request.body }}",
            "ACTION_PROJECTION_TITLE: ${{ github.event.pull_request.title }}",
            "github.event.pull_request.requested_reviewers",
            "github.event.pull_request.requested_teams",
            "github.event.pull_request.assignees",
            "github.event.pull_request.head.ref",
            "ACTION_PROJECTION_BASE_REVISION: "
            "${{ github.event.pull_request.base.sha }}",
            "steps.authoritative-pr-candidate.outputs.revision",
            "--additional-summary-env ACTION_PROJECTION_TITLE",
            "--external-assignment-env ACTION_PROJECTION_ASSIGNMENTS",
            "--queue-actor any",
            "--required-queue-actor needs-human",
            '--base-revision "$ACTION_PROJECTION_BASE_REVISION"',
        ))
        self.assertNotIn(
            "--external-action-env ACTION_PROJECTION_REQUESTED_", projection
        )
        self.assertNotIn(
            "--allow-missing-action-section-if-no-action", projection
        )
        self.assertNotIn(
            "check_action_projection.py", self.job("reconcile-and-test")
        )

    def test_issue_state_allows_link_actor_to_express_mixed_direction(self):
        projection = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue body and assignment state",
        )
        self.assert_contains_all(projection, (
            "ACTION_PROJECTION_BODY: ${{ github.event.issue.body }}",
            "ACTION_PROJECTION_TITLE: ${{ github.event.issue.title }}",
            "github.event.issue.assignees",
            "ACTION_PROJECTION_CANDIDATE_REVISION: ${{ github.sha }}",
            "--additional-prose-env ACTION_PROJECTION_TITLE",
            "--external-assignment-env ACTION_PROJECTION_ASSIGNMENTS",
            "--queue-actor any",
            "--unscoped",
            "--allow-missing-action-section-if-no-action",
        ))

    def test_assignment_adapter_maps_bot_direction_and_fails_unknowns_closed(self):
        pull_request = self.step(
            "authoritative-external-action-projection",
            "Action projection — pull-request description and state",
        )
        self.assert_contains_all(pull_request, (
            '--argjson reviewers "$ACTION_PROJECTION_REQUESTED_REVIEWERS"',
            '--argjson teams "$ACTION_PROJECTION_REQUESTED_TEAMS"',
            '--argjson assignees "$ACTION_PROJECTION_ASSIGNEES"',
            'if .type == "User"',
            '{actor: "needs-human", identity: .login}',
            'elif .type == "Bot"',
            '{actor: "needs-agent", identity: .login}',
            '{actor: "needs-human", identity: .slug}',
            'error("unknown external account actor type")',
            'error("external assignment has no identity")',
        ))
        issue = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue body and assignment state",
        )
        self.assert_contains_all(issue, (
            '--argjson assignees "$ACTION_PROJECTION_ASSIGNEES"',
            'if .type == "User"',
            'elif .type == "Bot"',
            '{actor: "needs-agent", identity: .login}',
            'error("unknown external account actor type")',
            "--external-assignment-env ACTION_PROJECTION_ASSIGNMENTS",
        ))
        self.assertNotIn(
            "--external-action-env ACTION_PROJECTION_ASSIGNEES", issue
        )

    def test_issue_and_pr_conversation_comments_use_distinct_candidates(self):
        issue = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue conversation comment",
        )
        self.assert_contains_all(issue, (
            "github.event_name == 'issue_comment' && "
            "!github.event.issue.pull_request",
            "ACTION_PROJECTION_BODY: ${{ github.event.comment.body }}",
            "ACTION_PROJECTION_CANDIDATE_REVISION: ${{ github.sha }}",
            "--queue-actor any",
            "--unscoped",
        ))
        pull_request = self.step(
            "authoritative-external-action-projection",
            "Action projection — PR conversation comment",
        )
        self.assert_contains_all(pull_request, (
            "github.event_name == 'issue_comment' && "
            "github.event.issue.pull_request",
            "ACTION_PROJECTION_BODY: ${{ github.event.comment.body }}",
            "steps.authoritative-pr-candidate.outputs.revision",
            "--queue-actor any",
            "--unscoped",
        ))
        self.assertNotIn("steps.authoritative-pr-candidate", issue)
        for step in (issue, pull_request):
            self.assertNotIn("--additional-prose-env", step)
            self.assertNotIn("--external-action-env", step)

    def test_review_surfaces_are_explicitly_advisory_and_read_only(self):
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertIn(
            "# GitHub has no pull_request_review_target or "
            "pull_request_review_comment_target.",
            self.workflow,
        )
        job = self.job("advisory-review-action-projection")
        self.assertIn(
            "name: Advisory only — review and review-comment action projection",
            job,
        )
        checkout = self.step(
            "advisory-review-action-projection",
            "Checkout PR-base projection gate for best-effort review",
        )
        self.assertIn(
            "ref: ${{ github.event.pull_request.base.sha }}", checkout
        )
        fetch = self.step(
            "advisory-review-action-projection",
            "Fetch event-bound PR merge candidate without checking it out",
        )
        self.assert_contains_all(fetch, (
            "ACTION_PROJECTION_EXPECTED_REVISION: ${{ github.sha }}",
            '"refs/pull/$ACTION_PROJECTION_PR_NUMBER/merge"',
            'rev-parse --verify "FETCH_HEAD^{commit}"',
        ))
        self.assertNotIn(
            "ref: ${{ github.event.pull_request.head.sha }}", job
        )

    def test_changes_requested_is_agent_action_but_neutral_reviews_may_pass(self):
        review = self.step(
            "advisory-review-action-projection",
            "Advisory action projection — PR review body",
        )
        self.assert_contains_all(review, (
            "ACTION_PROJECTION_BODY: ${{ github.event.review.body }}",
            "github.event.review.state == 'changes_requested'",
            "--external-action-env ACTION_PROJECTION_CHANGES_REQUESTED",
            "--queue-actor needs-agent",
            "--unscoped",
            "--allow-missing-action-section-if-no-action",
            "steps.advisory-pr-candidate.outputs.revision",
        ))
        self.assertNotIn("github.event.pull_request.head.ref", review)
        comment = self.step(
            "advisory-review-action-projection",
            "Advisory action projection — PR review comment",
        )
        self.assert_contains_all(comment, (
            "ACTION_PROJECTION_BODY: ${{ github.event.comment.body }}",
            "--queue-actor needs-agent",
            "--unscoped",
            "--allow-missing-action-section-if-no-action",
            "steps.advisory-pr-candidate.outputs.revision",
        ))
        self.assertNotIn("--external-action-env", comment)
        self.assertNotIn("github.event.pull_request.head.ref", comment)

    def test_no_untrusted_candidate_is_ever_checked_out(self):
        for forbidden in (
            "ref: ${{ github.event.pull_request.head.sha }}",
            "ref: ${{ steps.authoritative-pr-candidate.outputs.revision }}",
            "ref: ${{ steps.advisory-pr-candidate.outputs.revision }}",
            "ref: refs/pull/",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.workflow)


if __name__ == "__main__":
    unittest.main()
