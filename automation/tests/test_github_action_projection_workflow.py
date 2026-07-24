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

    def test_event_matrix_registers_authoritative_and_review_surfaces(self):
        on_block = self.workflow.partition("on:\n")[2].partition(
            "\npermissions:"
        )[0]
        pr_types = (
            "[opened, edited, reopened, synchronize, ready_for_review, "
            "review_requested, review_request_removed, assigned, unassigned, "
            "enqueued]"
        )
        self.assertIn(f"pull_request:\n    types: {pr_types}", on_block)
        self.assertIn(f"pull_request_target:\n    types: {pr_types}", on_block)
        self.assertIn(
            "issues:\n"
            "    types: [opened, edited, reopened, assigned, unassigned]",
            on_block,
        )
        self.assertIn(
            "issue_comment:\n    types: [created, edited, deleted]", on_block
        )
        self.assertIn(
            "pull_request_review:\n"
            "    types: [submitted, edited, dismissed]",
            on_block,
        )
        self.assertIn(
            "pull_request_review_comment:\n"
            "    types: [created, edited, deleted]",
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
            "ACTION_PROJECTION_ARTIFACT_ID: "
            "${{ github.event.pull_request.node_id }}",
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
            "ACTION_PROJECTION_ARTIFACT_ID: "
            "${{ github.event.issue.node_id }}",
            "steps.authoritative-default-candidate.outputs.revision",
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
            '--arg artifact_id "$ACTION_PROJECTION_ARTIFACT_ID"',
            'if .type == "User"',
            '"github:pull-request:node:" + artifact + ":" +',
            '$role + ":user:" + .login',
            'elif .type == "Bot"',
            '$role + ":bot:" + .login',
            '":requested-team:team:" + .slug',
            'account("requested-reviewer")',
            'account("assignee")',
            'error("unknown external account actor type")',
            'error("external assignment has no artifact identity")',
            'error("external assignment has no identity")',
        ))
        issue = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue body and assignment state",
        )
        self.assert_contains_all(issue, (
            '--argjson assignees "$ACTION_PROJECTION_ASSIGNEES"',
            '--arg artifact_id "$ACTION_PROJECTION_ARTIFACT_ID"',
            'if .type == "User"',
            'elif .type == "Bot"',
            '"github:issue:node:" + artifact +',
            '":assignee:user:" + .login',
            '":assignee:bot:" + .login',
            'error("external assignment has no artifact identity")',
            'error("unknown external account actor type")',
            "--external-assignment-env ACTION_PROJECTION_ASSIGNMENTS",
        ))
        self.assertNotIn(
            "--external-action-env ACTION_PROJECTION_ASSIGNEES", issue
        )

    def test_conversation_comments_are_structural_and_use_distinct_candidates(self):
        checkout = self.step(
            "authoritative-external-action-projection",
            "Checkout default-branch projection gate",
        )
        self.assertIn(
            "ref: ${{ github.event.repository.default_branch }}", checkout
        )
        capture = self.step(
            "authoritative-external-action-projection",
            "Capture immutable default-branch candidate",
        )
        self.assert_contains_all(capture, (
            'rev-parse --verify "HEAD^{commit}"',
            '>> "$GITHUB_OUTPUT"',
        ))
        collect = self.step(
            "authoritative-external-action-projection",
            "Collect event conversation comment",
        )
        self.assert_contains_all(collect, (
            "collect_conversation_actions.py",
            '--event-file "$GITHUB_EVENT_PATH"',
            "agentfold-conversation-actions.json",
        ))
        issue = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue or closed-PR conversation comment",
        )
        self.assert_contains_all(issue, (
            "!github.event.issue.pull_request",
            "github.event.issue.state != 'open'",
            "steps.authoritative-default-candidate.outputs.revision",
            "--external-action-sources-file",
            "agentfold-conversation-actions.json",
        ))
        pull_request = self.step(
            "authoritative-external-action-projection",
            "Action projection — open-PR conversation comment",
        )
        self.assert_contains_all(pull_request, (
            "github.event.issue.pull_request",
            "github.event.issue.state == 'open'",
            "steps.authoritative-pr-candidate.outputs.revision",
            "--external-action-sources-file",
            "agentfold-conversation-actions.json",
        ))
        self.assertNotIn("steps.authoritative-pr-candidate", issue)
        for step in (issue, pull_request):
            self.assertNotIn("--from-env", step)
            self.assertNotIn("--allow-missing-action-section-if-no-action", step)
            self.assertNotIn("--queue-actor", step)
            self.assertNotIn("--unscoped", step)
            self.assertNotIn("--additional-prose-env", step)
            self.assertNotIn("--external-action-env", step)

    def test_review_surfaces_enforce_actions_with_honest_trust_ceiling(self):
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertIn("  issues: read", self.workflow)
        self.assertIn("  pull-requests: read", self.workflow)
        self.assertIn(
            "# GitHub has no pull_request_review_target, "
            "pull_request_review_comment_target, or",
            self.workflow,
        )
        self.assertIn(
            "# supported review/PR events, including merge-queue enqueue.",
            self.workflow,
        )
        self.assertIn(
            "provider-native conversation-",
            self.workflow,
        )
        self.assertIn(
            "without it, evidence is only current at the last supported event",
            self.workflow,
        )
        self.assertNotIn("pull_request_review_thread:", self.workflow)
        job = self.job("review-state-action-projection")
        self.assertIn(
            "name: Current review-state action projection",
            job,
        )
        self.assert_contains_all(job, (
            "github.event_name == 'pull_request'",
            "github.event_name == 'pull_request_review'",
            "github.event_name == 'pull_request_review_comment'",
        ))
        checkout = self.step(
            "review-state-action-projection",
            "Checkout PR-base projection gate for review state",
        )
        self.assertIn(
            "ref: ${{ github.event.pull_request.base.sha }}", checkout
        )
        fetch = self.step(
            "review-state-action-projection",
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

    def test_current_review_state_replays_in_target_and_candidate_contexts(self):
        target_collect = self.step(
            "authoritative-external-action-projection",
            "Collect current formal reviews and unresolved diff threads",
        )
        candidate_collect = self.step(
            "review-state-action-projection",
            "Collect current formal reviews and unresolved diff threads",
        )
        for step in (target_collect, candidate_collect):
            self.assert_contains_all(step, (
                "GITHUB_TOKEN: ${{ github.token }}",
                "ACTION_PROJECTION_REPOSITORY: ${{ github.repository }}",
                "github.event.pull_request.number",
                "ACTION_PROJECTION_GRAPHQL_URL: ${{ github.graphql_url }}",
                "python3 .github/scripts/collect_review_actions.py",
                '--output "$RUNNER_TEMP/agentfold-review-actions.json"',
            ))
        self.assertIn(
            "if: ${{ github.event_name == 'pull_request_target' }}",
            target_collect,
        )

        target_projection = self.step(
            "authoritative-external-action-projection",
            "Action projection — current review state",
        )
        candidate_projection = self.step(
            "review-state-action-projection",
            "Action projection — current review state",
        )
        self.assert_contains_all(target_projection, (
            "steps.authoritative-pr-candidate.outputs.revision",
            "--external-action-sources-file",
            "--candidate-revision",
            "--allowed-url-prefix",
        ))
        self.assert_contains_all(candidate_projection, (
            "steps.review-state-pr-candidate.outputs.revision",
            "--external-action-sources-file",
            "--candidate-revision",
            "--allowed-url-prefix",
        ))

        target_comments = self.step(
            "authoritative-external-action-projection",
            "Collect current PR conversation comments",
        )
        candidate_comments = self.step(
            "review-state-action-projection",
            "Collect current PR conversation comments",
        )
        for step in (target_comments, candidate_comments):
            self.assert_contains_all(step, (
                "GITHUB_TOKEN: ${{ github.token }}",
                "github.event.pull_request.number",
                "ACTION_PROJECTION_API_URL: ${{ github.api_url }}",
                "collect_conversation_actions.py",
                '--issue-number "$ACTION_PROJECTION_PR_NUMBER"',
                "agentfold-conversation-actions.json",
            ))
        target_comment_projection = self.step(
            "authoritative-external-action-projection",
            "Action projection — current PR conversation state",
        )
        candidate_comment_projection = self.step(
            "review-state-action-projection",
            "Action projection — current PR conversation state",
        )
        for step in (
            target_comment_projection,
            candidate_comment_projection,
        ):
            self.assert_contains_all(step, (
                "--external-action-sources-file",
                "agentfold-conversation-actions.json",
                "--label github-current-pull-request-conversation-state",
            ))

    def test_no_untrusted_candidate_is_ever_checked_out(self):
        for forbidden in (
            "ref: ${{ github.event.pull_request.head.sha }}",
            "ref: ${{ steps.authoritative-pr-candidate.outputs.revision }}",
            "ref: ${{ steps.review-state-pr-candidate.outputs.revision }}",
            "ref: refs/pull/",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.workflow)


if __name__ == "__main__":
    unittest.main()
