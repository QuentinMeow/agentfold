#!/usr/bin/env python3
"""Static event, trust, candidate, and actor matrix for the GitHub adapter."""
import unittest
from pathlib import Path

if __package__:
    from .trusted_gate_snapshots import (
        HARD_WORKFLOW_SHA256,
        MANUAL_WORKFLOW_SHA256,
        TRUSTED_GATE_JOBS,
        decode_workflow,
        manual_fixture_contract_errors,
        manual_workflow_fixture,
        manualize_hard_workflow,
        migration_mutations,
        trusted_gate_regime,
        workflow_digest,
        workflow_job,
    )
else:
    from trusted_gate_snapshots import (
        HARD_WORKFLOW_SHA256,
        MANUAL_WORKFLOW_SHA256,
        TRUSTED_GATE_JOBS,
        decode_workflow,
        manual_fixture_contract_errors,
        manual_workflow_fixture,
        manualize_hard_workflow,
        migration_mutations,
        trusted_gate_regime,
        workflow_digest,
        workflow_job,
    )


REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github/workflows/harness.yml"


class GitHubActionProjectionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_bytes = WORKFLOW.read_bytes()
        cls.trusted_gate_regime = trusted_gate_regime(cls.workflow_bytes)
        if cls.trusted_gate_regime not in ("present", "absent"):
            raise AssertionError("workflow is outside both admitted byte snapshots")
        cls.workflow = decode_workflow(cls.workflow_bytes)

    def job(self, name):
        job = workflow_job(self.workflow, name)
        if not job:
            self.fail(f"missing workflow job {name!r}")
        return job

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

    def require_hard_gate(self):
        if self.trusted_gate_regime == "absent":
            self.skipTest("the complete hard-gate triad is intentionally absent")

    def test_trusted_gate_is_one_complete_migration_regime(self):
        current = self.workflow_bytes
        manual = manual_workflow_fixture()
        self.assertEqual(MANUAL_WORKFLOW_SHA256, workflow_digest(manual))
        self.assertNotEqual(HARD_WORKFLOW_SHA256, MANUAL_WORKFLOW_SHA256)
        self.assertEqual("absent", trusted_gate_regime(manual))
        self.assertEqual((), manual_fixture_contract_errors(manual))
        self.assertIn(trusted_gate_regime(current), ("present", "absent"))
        if trusted_gate_regime(current) == "present":
            self.assertEqual(HARD_WORKFLOW_SHA256, workflow_digest(current))
            self.assertEqual(manual, manualize_hard_workflow(current))
            for missing in TRUSTED_GATE_JOBS:
                with self.subTest(partial_hard_job=missing):
                    partial = self.workflow.replace(
                        workflow_job(self.workflow, missing), "", 1
                    ).encode("utf-8")
                    self.assertEqual("invalid", trusted_gate_regime(partial))
        else:
            self.assertEqual(manual, current)
        for name, mutation in migration_mutations(manual):
            with self.subTest(manual_mutation=name):
                self.assertEqual("invalid", trusted_gate_regime(mutation))
        self.assertEqual("invalid", trusted_gate_regime(current + b"\n"))

    def test_event_matrix_registers_authoritative_and_review_surfaces(self):
        on_block = self.workflow.partition("on:\n")[2].partition(
            "\npermissions:"
        )[0]
        pr_types = (
            "[opened, edited, reopened, synchronize, ready_for_review, "
            "review_requested, review_request_removed, assigned, unassigned, "
            "enqueued]"
        )
        self.assertIn(f"pull_request_target:\n    types: {pr_types}", on_block)
        if self.trusted_gate_regime == "present":
            self.assertNotIn("pull_request:\n", on_block)
            self.assertIn("merge_group:\n    types: [checks_requested]", on_block)
        else:
            self.assertIn("pull_request:\n", on_block)
            self.assertNotIn("merge_group:\n", on_block)
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
            "if: ${{ github.event_name == 'pull_request_target' }}",
            checkout,
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

    def test_trusted_preparer_uses_base_code_and_binds_every_candidate_identity(self):
        self.require_hard_gate()
        job = self.job("prepare-trusted-final-test-gate")
        self.assert_contains_all(job, (
            "name: Prepare trusted hard final gate candidate",
            "github.event.action == 'opened' || github.event.action == 'synchronize'",
            "github.event.pull_request.base.ref == github.event.repository.default_branch",
            "github.event.pull_request.head.repo.id == github.event.repository.id",
            "startsWith(github.event.pull_request.head.ref, 'task/')",
            "permissions:\n      contents: read",
            "bundle_sha256: ${{ steps.bundle.outputs.sha256 }}",
        ))
        checkout = self.step(
            "prepare-trusted-final-test-gate",
            "Checkout trusted pull-request base controller",
        )
        self.assert_contains_all(checkout, (
            "uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
            "fetch-depth: 0",
            "persist-credentials: false",
            "ref: ${{ github.event.pull_request.base.sha }}",
        ))
        identities = self.step(
            "prepare-trusted-final-test-gate",
            "Fetch and verify exact pull-request identities",
        )
        self.assert_contains_all(identities, (
            "GITHUB_TOKEN: ${{ github.token }}",
            "TEST_GATE_BASE: ${{ github.event.pull_request.base.sha }}",
            "TEST_GATE_HEAD: ${{ github.event.pull_request.head.sha }}",
            "TEST_GATE_CANDIDATE: ${{ github.event.pull_request.merge_commit_sha }}",
            "TEST_GATE_BRANCH: ${{ github.event.pull_request.head.ref }}",
            "TEST_GATE_ACTION: ${{ github.event.action }}",
            "TEST_GATE_BASE_BRANCH: ${{ github.event.pull_request.base.ref }}",
            "TEST_GATE_DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}",
            "TEST_GATE_HEAD_REPOSITORY_ID: ${{ github.event.pull_request.head.repo.id }}",
            "TEST_GATE_BASE_REPOSITORY_ID: ${{ github.event.repository.id }}",
            "github.event.before",
            '"+refs/pull/$TEST_GATE_PR_NUMBER/head:refs/agentfold/test-gate/head"',
            '"+refs/pull/$TEST_GATE_PR_NUMBER/merge:refs/agentfold/test-gate/merge"',
            'rev-parse --verify refs/agentfold/test-gate/head^{commit}',
            'rev-parse --verify refs/agentfold/test-gate/merge^{commit}',
            'rev-parse --verify "$TEST_GATE_CANDIDATE^1"',
            'rev-parse --verify "$TEST_GATE_CANDIDATE^2"',
            'rev-list --parents -n 1 "$TEST_GATE_CANDIDATE"',
            'test "$TEST_GATE_DISPLACED_TIP" != "$TEST_GATE_HEAD"',
            'git merge-base --is-ancestor "$TEST_GATE_DISPLACED_TIP" "$TEST_GATE_HEAD"',
            "git update-ref refs/agentfold/test-gate/base",
            "git update-ref refs/agentfold/test-gate/displaced",
            "unset AUTH_HEADER GITHUB_TOKEN",
        ))
        bundle = self.step(
            "prepare-trusted-final-test-gate",
            "Bundle trusted controller and immutable candidate",
        )
        self.assert_contains_all(bundle, (
            "refs/agentfold/test-gate/base",
            "refs/agentfold/test-gate/head",
            "refs/agentfold/test-gate/merge",
            "refs/agentfold/test-gate/displaced",
            "git bundle create",
            "git bundle verify",
            "sha256sum",
            'printf \'sha256=%s\\n\' "$TEST_GATE_BUNDLE_SHA256"',
        ))
        upload = self.step(
            "prepare-trusted-final-test-gate", "Upload trusted candidate bundle"
        )
        self.assert_contains_all(upload, (
            "uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
            "agentfold-test-gate-${{ github.run_id }}-${{ github.run_attempt }}",
            "if-no-files-found: error",
            "retention-days: 1",
        ))
        self.assertEqual(1, job.count("uses: actions/checkout@"))
        self.assertNotIn("git checkout", job)
        self.assertNotIn("python3 ", job)
        self.assertNotIn("automation/run_test_gate.py", job)
        self.assertNotIn("actions/download-artifact", job)

    def test_candidate_runner_has_no_repository_permissions_or_inherited_secrets(self):
        self.require_hard_gate()
        job = self.job("trusted-final-test-runner")
        self.assert_contains_all(job, (
            "name: AgentFold credential-free final test runner",
            "needs: prepare-trusted-final-test-gate",
            "always()",
            "permissions: {}",
        ))
        self.assertNotIn("actions/checkout", job)
        self.assertNotIn("github.token", job)
        self.assertNotIn("GITHUB_TOKEN", job)
        self.assertNotIn("checks: write", job)
        rejection = self.step(
            "trusted-final-test-runner", "Reject missing trusted preparation"
        )
        self.assert_contains_all(rejection, (
            "needs.prepare-trusted-final-test-gate.result != 'success'",
            "run: exit 1",
        ))
        download = self.step(
            "trusted-final-test-runner", "Download trusted candidate bundle"
        )
        self.assert_contains_all(download, (
            "needs.prepare-trusted-final-test-gate.result == 'success'",
            "uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
            "agentfold-test-gate-${{ github.run_id }}-${{ github.run_attempt }}",
        ))
        run = self.step(
            "trusted-final-test-runner",
            "Run trusted controller in one-shot candidate container",
        )
        self.assert_contains_all(run, (
            "needs.prepare-trusted-final-test-gate.outputs.bundle_sha256",
            "sha256sum",
            'refs/agentfold/test-gate/*:refs/agentfold/test-gate/*',
            "refs/agentfold/test-gate/base^{commit}",
            "refs/agentfold/test-gate/head^{commit}",
            "refs/agentfold/test-gate/merge^{commit}",
            "refs/agentfold/test-gate/displaced^{commit}",
            "docker.io/library/python:3.11-bookworm@sha256:",
            "timeout --signal=TERM --kill-after=15s 960s docker run",
            "--pull=never",
            "--network none",
            "--ipc private",
            "--read-only",
            "--cap-drop ALL",
            "--cap-add KILL",
            "--cap-add SETUID",
            "--cap-add SETGID",
            "--security-opt no-new-privileges",
            "--pids-limit 256",
            "--memory 2g",
            "--memory-swap 2g",
            "--cpus 2",
            "--cidfile",
            "grep -Eq '^[0-9a-f]{12,64}$'",
            "uid=0,gid=0",
            "python3 /trusted/launcher.py",
            'str(pathlib.Path(CONTROLLER) / "automation/run_test_gate.py")',
            "--provider-hard",
            '"--at-transition", "pull-request"',
            '"--base-revision", base',
            '"--head-revision", head',
            '"--candidate-revision", candidate',
            '"--branch", branch',
        ))
        self.assertEqual(3, run.count("--cap-add "))
        self.assertEqual(2, run.count("--pull=never"))
        self.assertRegex(run, r"python:3\.11-bookworm@sha256:[0-9a-f]{64}")
        self.assertNotIn("GITHUB_TOKEN", run)
        self.assertNotIn("github.token", run)
        self.assertNotIn("secrets.", run)
        self.assertNotIn("/var/run/docker.sock", run)
        self.assertNotIn("$GITHUB_WORKSPACE", run)
        self.assertNotIn("--pid=host", run)
        self.assertNotIn("--privileged", run)
        self.assertNotIn("uid=65532", run)
        self.assertIn("invalid Docker cidfile", run)

    def test_stable_required_status_is_published_by_dedicated_app(self):
        self.require_hard_gate()
        job = self.job("publish-trusted-final-test-check")
        self.assert_contains_all(job, (
            "name: Publish AgentFold App-authored hard final gate status",
            "needs: [prepare-trusted-final-test-gate, trusted-final-test-runner]",
            "always()",
            "permissions: {}",
            "environment: agentfold-trusted-publisher",
            "github.event_name == 'pull_request_target'",
        ))
        token = self.step(
            "publish-trusted-final-test-check",
            "Mint repository-scoped publisher App token",
        )
        self.assert_contains_all(token, (
            "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1",
            "client-id: ${{ vars.AGENTFOLD_PUBLISHER_CLIENT_ID }}",
            "private-key: ${{ secrets.AGENTFOLD_PUBLISHER_PRIVATE_KEY }}",
            "permission-statuses: write",
        ))
        publish = self.step(
            "publish-trusted-final-test-check",
            "Publish exact-candidate required commit status",
        )
        self.assert_contains_all(publish, (
            "TEST_GATE_APP_TOKEN: ${{ steps.publisher-token.outputs.token }}",
            "github.event.pull_request.merge_commit_sha",
            "needs.prepare-trusted-final-test-gate.outputs.candidate",
            "needs.prepare-trusted-final-test-gate.result",
            "needs.trusted-final-test-runner.result",
            "TEST_GATE_STATE=failure",
            '[ "$TEST_GATE_PREPARE_RESULT" = success ]',
            '[ "$TEST_GATE_RUNNER_RESULT" = success ]',
            'TEST_GATE_PREPARED_CANDIDATE" = "$TEST_GATE_CANDIDATE',
            "TEST_GATE_STATE=success",
            "AgentFold trusted hard final gate",
            "statuses/$TEST_GATE_CANDIDATE",
            "'{state:$state,context:$context,description:$description,target_url:$target_url}'",
            'test "$TEST_GATE_STATE" = success',
        ))
        self.assertNotIn("actions/checkout", job)
        self.assertNotIn("actions/download-artifact", job)
        self.assertNotIn("run_test_gate.py", job)
        self.assertNotIn("git checkout", job)
        self.assertNotIn("GITHUB_TOKEN", job)
        self.assertNotIn("github.token", job)
        self.assertNotIn("checks: write", job)
        self.assertNotIn("/check-runs", job)

    def test_all_hard_gate_jobs_share_the_same_restricted_event_source_condition(self):
        self.require_hard_gate()
        fragments = (
            "github.event_name == 'pull_request_target'",
            "github.event.action == 'opened' || github.event.action == 'synchronize'",
            "github.event.pull_request.base.ref == github.event.repository.default_branch",
            "github.event.pull_request.head.repo.id == github.event.repository.id",
            "startsWith(github.event.pull_request.head.ref, 'task/')",
        )
        for job_name in (
            "prepare-trusted-final-test-gate",
            "trusted-final-test-runner",
            "publish-trusted-final-test-check",
        ):
            with self.subTest(job=job_name):
                self.assert_contains_all(self.job(job_name), fragments)

    def test_hard_gate_event_history_matrix_has_no_metadata_or_rewrite_success_path(self):
        self.require_hard_gate()
        zero = "0" * 40

        def eligible(event, action, same_repository, branch, before="", head="h", ancestor=True, base_is_default=True):
            metadata_allowed = (
                event == "pull_request_target"
                and action in ("opened", "synchronize")
                and same_repository
                and base_is_default
                and branch.startswith("task/")
            )
            if not metadata_allowed:
                return False
            if action == "opened":
                return before == ""
            return bool(before) and before != zero and before != head and ancestor

        rejected = (
            ("pull_request_target", "edited", True, "task/x", "", "h", True),
            ("pull_request_target", "ready_for_review", True, "task/x", "", "h", True),
            ("pull_request_review", "submitted", True, "task/x", "", "h", True),
            ("pull_request_target", "reopened", True, "task/x", "", "h", True),
            ("pull_request_target", "opened", False, "task/x", "", "h", True),
            ("pull_request_target", "opened", True, "feature/x", "", "h", True),
            ("pull_request_target", "synchronize", True, "task/x", "before", "head", False),
            ("pull_request_target", "synchronize", True, "task/x", zero, "head", True),
            ("pull_request_target", "synchronize", True, "task/x", "head", "head", True),
            ("pull_request_target", "opened", True, "task/x", "", "h", True, False),
        )
        for case in rejected:
            with self.subTest(case=case):
                self.assertFalse(eligible(*case))
        self.assertTrue(
            eligible("pull_request_target", "opened", True, "task/x")
        )
        self.assertTrue(
            eligible(
                "pull_request_target",
                "synchronize",
                True,
                "task/x",
                "before",
                "head",
                True,
            )
        )

        identities = self.step(
            "prepare-trusted-final-test-gate",
            "Fetch and verify exact pull-request identities",
        )
        self.assert_contains_all(identities, (
            'test "$TEST_GATE_HEAD_REPOSITORY_ID" = "$TEST_GATE_BASE_REPOSITORY_ID"',
            'test "$TEST_GATE_BASE_BRANCH" = "$TEST_GATE_DEFAULT_BRANCH"',
            'test "$TEST_GATE_DISPLACED_TIP" != "$TEST_GATE_HEAD"',
            'git merge-base --is-ancestor "$TEST_GATE_DISPLACED_TIP" "$TEST_GATE_HEAD"',
        ))

    def test_stale_identity_canaries_bind_head_merge_parents_and_published_sha(self):
        self.require_hard_gate()
        identities = self.step(
            "prepare-trusted-final-test-gate",
            "Fetch and verify exact pull-request identities",
        )
        self.assert_contains_all(identities, (
            'refs/agentfold/test-gate/head^{commit}',
            'refs/agentfold/test-gate/merge^{commit}',
            '"$TEST_GATE_CANDIDATE^1"',
            '"$TEST_GATE_CANDIDATE^2"',
        ))
        publish = self.step(
            "publish-trusted-final-test-check",
            "Publish exact-candidate required commit status",
        )
        self.assert_contains_all(publish, (
            "github.event.pull_request.merge_commit_sha",
            "needs.prepare-trusted-final-test-gate.outputs.candidate",
            'TEST_GATE_PREPARED_CANDIDATE" = "$TEST_GATE_CANDIDATE',
            "statuses/$TEST_GATE_CANDIDATE",
        ))

    def test_candidate_controlled_pull_request_job_cannot_replace_hard_gate(self):
        on_block = self.workflow.partition("on:\n")[2].partition(
            "\npermissions:"
        )[0]
        push = self.job("reconcile-and-test")
        self.assertNotIn("run_test_gate.py", push)
        self.assertNotIn("Final test gate", push)
        if self.trusted_gate_regime == "present":
            self.assertNotIn("pull_request:\n", on_block)
            self.assertIn("if: ${{ github.event_name == 'push' }}", push)
            self.assertNotIn("automation/run_tests.py", push)
        else:
            self.assertIn("pull_request:\n", on_block)
            self.assertIn("github.event_name == 'pull_request'", push)
            self.assertIn("automation/run_tests.py", push)

    def test_issue_assignment_state_replays_on_issue_and_comment_events(self):
        projection = self.step(
            "authoritative-external-action-projection",
            "Action projection — issue assignment state",
        )
        self.assert_contains_all(projection, (
            "github.event_name == 'issues'",
            "github.event_name == 'issue_comment'",
            "!github.event.issue.pull_request",
            'ACTION_PROJECTION_BODY: ""',
            "github.event.issue.assignees",
            "ACTION_PROJECTION_ARTIFACT_ID: "
            "${{ github.event.issue.node_id }}",
            "steps.authoritative-default-candidate.outputs.revision",
            "--external-assignment-env ACTION_PROJECTION_ASSIGNMENTS",
            "--queue-actor any",
            "--unscoped",
            "--allow-missing-action-section-if-no-action",
        ))
        self.assertNotIn("--additional-prose-env", projection)

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
            "Action projection — issue assignment state",
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

    def test_conversation_state_replays_snapshot_and_uses_distinct_candidates(self):
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
            "Collect current event-artifact conversation state",
        )
        self.assert_contains_all(collect, (
            "github.event_name == 'issues'",
            "github.event_name == 'issue_comment'",
            "GITHUB_TOKEN: ${{ github.token }}",
            "ACTION_PROJECTION_REPOSITORY: ${{ github.repository }}",
            "ACTION_PROJECTION_ISSUE_NUMBER: "
            "${{ github.event.issue.number }}",
            "ACTION_PROJECTION_API_URL: ${{ github.api_url }}",
            "collect_conversation_actions.py",
            '--repository "$ACTION_PROJECTION_REPOSITORY"',
            '--issue-number "$ACTION_PROJECTION_ISSUE_NUMBER"',
            '--api-url "$ACTION_PROJECTION_API_URL"',
            '--event-file "$GITHUB_EVENT_PATH"',
            '--event-kind "$ACTION_PROJECTION_EVENT_KIND"',
            "agentfold-conversation-actions.json",
        ))
        issue = self.step(
            "authoritative-external-action-projection",
            "Action projection — current issue or closed-PR conversation state",
        )
        self.assert_contains_all(issue, (
            "github.event_name == 'issues'",
            "github.event_name == 'issue_comment'",
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

    def test_external_source_release_is_checked_at_controlled_admission(self):
        job = self.job("external-source-release-admission")
        self.assert_contains_all(job, (
            "name: External source release admission",
            "github.event_name == 'pull_request_target'",
            "github.event_name == 'push'",
            "github.event.repository.default_branch",
            "github.event.before !=",
        ))
        checkout = self.step(
            "external-source-release-admission",
            "Checkout trusted pre-admission source-release gate",
        )
        self.assert_contains_all(checkout, (
            "fetch-depth: 0",
            "github.event.pull_request.base.sha",
            "github.event.before",
        ))
        candidate = self.step(
            "external-source-release-admission",
            "Fetch immutable source-release candidate",
        )
        self.assert_contains_all(candidate, (
            '"refs/pull/$SOURCE_RELEASE_PR_NUMBER/merge"',
            "github.event.pull_request.merge_commit_sha",
            "github.sha",
            'test "$SOURCE_RELEASE_CANDIDATE" =',
        ))
        resolve = self.step(
            "external-source-release-admission",
            "Resolve disappearing external sources from provider state",
        )
        self.assert_contains_all(resolve, (
            "GITHUB_TOKEN: ${{ github.token }}",
            "resolve_external_source_releases.py",
            '--base-revision "$SOURCE_RELEASE_BASE"',
            '--candidate-revision "$SOURCE_RELEASE_CANDIDATE"',
            "agentfold-source-release-state.json",
        ))
        verify = self.step(
            "external-source-release-admission",
            "Verify final external-source bindings remain live",
        )
        self.assert_contains_all(verify, (
            "automation/check_action_projection.py",
            "--external-source-release-state-file",
            '--base-revision "$SOURCE_RELEASE_BASE"',
            '--candidate-revision "$SOURCE_RELEASE_CANDIDATE"',
            "--label github-external-source-release",
        ))
        self.assertNotIn("pull_request.head.sha", job)

    def test_review_surfaces_enforce_actions_with_honest_trust_ceiling(self):
        if self.trusted_gate_regime == "present":
            self.assertIn("permissions:\n  contents: read", self.workflow)
            self.assertIn("  issues: read", self.workflow)
            self.assertIn("  pull-requests: read", self.workflow)
        else:
            self.assertIn("permissions: {}", self.workflow)
        self.assertIn(
            "# GitHub has no pull_request_review_target, "
            "pull_request_review_comment_target, or",
            self.workflow,
        )
        self.assertIn(
            "# direct review events; the trusted pull_request_target job separately replays PR",
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
            "github.event_name == 'pull_request_review'",
            "github.event_name == 'pull_request_review_comment'",
        ))
        self.assertNotIn("github.event_name == 'pull_request'", job)
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
