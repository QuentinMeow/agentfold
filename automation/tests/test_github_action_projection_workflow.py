#!/usr/bin/env python3
"""Static event, trust, candidate, and actor matrix for the GitHub adapter."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github/workflows/harness.yml"
JOB_HEADER_RE = re.compile(r"^  (?P<name>[a-z][a-z0-9-]*):\n", re.MULTILINE)
RUN_BLOCK_MARKER = "        run: |\n"
RUN_BLOCK_INDENT = " " * 10
# GitHub Actions runs every `run:` block as `bash -e {0}`.
STEP_SHELL = ("bash", "-e")
GIT_FIXTURE_ENVIRONMENT = {
    "GIT_AUTHOR_NAME": "harness",
    "GIT_AUTHOR_EMAIL": "harness@example.invalid",
    "GIT_COMMITTER_NAME": "harness",
    "GIT_COMMITTER_EMAIL": "harness@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}
TRUSTED_GATE_JOBS = (
    "prepare-trusted-final-test-gate",
    "trusted-final-test-runner",
    "publish-trusted-final-test-check",
)


def workflow_job(workflow, name):
    matches = list(JOB_HEADER_RE.finditer(workflow))
    for index, match in enumerate(matches):
        if match.group("name") != name:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) \
            else len(workflow)
        return workflow[match.start():end]
    return ""


def step_shell_script(step):
    """Return one step's literal `run:` block with its block indent removed."""
    _before, separator, remainder = step.partition(RUN_BLOCK_MARKER)
    if not separator:
        return ""
    lines = []
    for line in remainder.splitlines(keepends=True):
        if line.startswith(RUN_BLOCK_INDENT):
            lines.append(line[len(RUN_BLOCK_INDENT):])
        elif line.strip():
            break
        else:
            lines.append("\n")
    return "".join(lines)


def git(repository, *arguments):
    """Run one Git command in a fixture repository and return its stdout."""
    environment = dict(os.environ)
    environment.update(GIT_FIXTURE_ENVIRONMENT)
    result = subprocess.run(
        ("git", *arguments),
        cwd=str(repository),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8").strip()


class MergeRefFixture:
    """A local origin whose pull refs carry every merge-candidate shape.

    The candidate steps only inspect commit identity and parent shape, so every
    commit here shares one empty tree and differs by parents and message.
    """

    def __init__(self, root):
        self.root = Path(root)
        self.remote = self.root / "remote"
        self.remote.mkdir()
        git(self.remote, "init", "--quiet", "--bare")
        git(self.remote, "config", "uploadpack.allowAnySHA1InWant", "true")
        tree = git(self.remote, "hash-object", "-t", "tree", "-w", os.devnull)
        self.base = self.commit(tree, "base")
        self.advanced_base = self.commit(tree, "advanced base", self.base)
        self.head = self.commit(tree, "head", self.base)
        self.raced_head = self.commit(tree, "raced head", self.head)
        self.unrelated = self.commit(tree, "unrelated")
        git(self.remote, "update-ref", "refs/heads/main", self.advanced_base)
        self.publish(1, self.merge(tree, self.base, self.head))
        self.publish(2, self.merge(tree, self.advanced_base, self.head))
        self.publish(3, self.merge(tree, self.base, self.raced_head))
        self.publish(4, self.head)
        self.publish(5, self.merge(tree, self.base, self.head, self.raced_head))

    def commit(self, tree, message, *parents):
        arguments = ["commit-tree", tree, "-m", message]
        for parent in parents:
            arguments.extend(("-p", parent))
        return git(self.remote, *arguments)

    def merge(self, tree, *parents):
        return self.commit(tree, "Merge " + " ".join(parents), *parents)

    def publish(self, number, revision):
        git(self.remote, "update-ref", f"refs/pull/{number}/merge", revision)

    def workspace(self):
        workspace = Path(tempfile.mkdtemp(dir=str(self.root)))
        git(workspace, "init", "--quiet")
        git(workspace, "remote", "add", "origin", str(self.remote))
        return workspace

    def run_step(self, script, environment):
        """Run one candidate step as Actions would, and report its outcome."""
        workspace = self.workspace()
        script_path = workspace / "step.sh"
        script_path.write_text(script, encoding="utf-8")
        output_path = workspace / "step-output.txt"
        output_path.write_text("", encoding="utf-8")
        step_environment = dict(os.environ)
        step_environment.update(GIT_FIXTURE_ENVIRONMENT)
        step_environment["GITHUB_OUTPUT"] = str(output_path)
        step_environment.update(environment)
        result = subprocess.run(
            (*STEP_SHELL, str(script_path)),
            cwd=str(workspace),
            env=step_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return (
            result.returncode,
            output_path.read_text(encoding="utf-8"),
            result.stderr.decode("utf-8"),
        )


def trusted_gate_regime(workflow):
    """Recognize only a complete legacy or complete restricted gate shape."""
    jobs = {name: workflow_job(workflow, name) for name in TRUSTED_GATE_JOBS}
    present = tuple(bool(jobs[name]) for name in TRUSTED_GATE_JOBS)
    if not any(present):
        return "legacy"
    if not all(present):
        return "invalid"
    prepare = jobs["prepare-trusted-final-test-gate"]
    runner = jobs["trusted-final-test-runner"]
    publisher = jobs["publish-trusted-final-test-check"]
    common = (
        "permissions:\n      contents: read" in prepare
        and "permissions: {}" in runner
        and "--provider-hard" in runner
        and "permissions: {}" in publisher
        and "environment: agentfold-trusted-publisher" in publisher
        and "statuses/$TEST_GATE_CANDIDATE" in publisher
    )
    legacy = (
        "if: ${{ github.event_name == 'pull_request_target' }}" in prepare
        and "github.event_name == 'merge_group'" in runner
        and "Reject unsupported merge-queue admission" in runner
        and "github.event_name == 'merge_group'" not in publisher
    )
    restricted_fragments = (
        "github.event.action == 'opened' || github.event.action == 'synchronize'",
        "github.event.pull_request.base.ref == github.event.repository.default_branch",
        "github.event.pull_request.head.repo.id == github.event.repository.id",
        "startsWith(github.event.pull_request.head.ref, 'task/')",
    )
    restricted = (
        all(
            all(fragment in jobs[name] for fragment in restricted_fragments)
            for name in TRUSTED_GATE_JOBS
        )
        and 'git merge-base --is-ancestor "$TEST_GATE_DISPLACED_TIP" "$TEST_GATE_HEAD"'
        in prepare
        and "github.event_name == 'merge_group'" not in runner
        and "Reject unsupported merge-queue admission" not in runner
    )
    if common and legacy and not restricted:
        return "legacy"
    if common and restricted and not legacy:
        return "restricted"
    return "invalid"


class GitHubActionProjectionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

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

    def test_trusted_gate_is_one_complete_migration_regime(self):
        self.assertIn(trusted_gate_regime(self.workflow), ("legacy", "restricted"))

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
            "ACTION_PROJECTION_EXPECTED_HEAD: "
            "${{ github.event_name == 'pull_request_target' && "
            "github.event.pull_request.head.sha || '' }}",
            "ACTION_PROJECTION_EXPECTED_BASE: "
            "${{ github.event_name == 'pull_request_target' && "
            "github.event.pull_request.base.sha || '' }}",
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
            "SOURCE_RELEASE_EXPECTED_HEAD: "
            "${{ github.event_name == 'pull_request_target' && "
            "github.event.pull_request.head.sha || '' }}",
            "SOURCE_RELEASE_EXPECTED_BASE: "
            "${{ github.event_name == 'pull_request_target' && "
            "github.event.pull_request.base.sha || '' }}",
            "SOURCE_RELEASE_PUSH_CANDIDATE: "
            "${{ github.event_name == 'push' && github.sha || '' }}",
            '"$SOURCE_RELEASE_CANDIDATE" != \\',
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
        self.assertNotIn("ref: ${{ github.event.pull_request.head.sha }}", job)
        self.assertNotIn(
            '--candidate-revision "$SOURCE_RELEASE_EXPECTED_HEAD"', job
        )

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

    def test_merge_candidate_is_pinned_by_parent_shape_not_merge_commit_sha(self):
        """merge_commit_sha is eventually consistent, so it cannot pin anything.

        It arrives empty on `opened` and stale after `synchronize`, which made
        both admission jobs fail closed on revisions GitHub had already
        computed. The parent shape of the fetched merge commit pins the same
        immutable candidate to the same event without that race.
        """
        steps = (
            (
                "authoritative-external-action-projection",
                "Fetch immutable PR candidate without checking it out",
                "ACTION_PROJECTION_CANDIDATE_REVISION",
                "ACTION_PROJECTION_MERGED_HEAD",
                "ACTION_PROJECTION_EXPECTED_HEAD",
                "ACTION_PROJECTION_EXPECTED_BASE",
            ),
            (
                "external-source-release-admission",
                "Fetch immutable source-release candidate",
                "SOURCE_RELEASE_CANDIDATE",
                "SOURCE_RELEASE_MERGED_HEAD",
                "SOURCE_RELEASE_EXPECTED_HEAD",
                "SOURCE_RELEASE_EXPECTED_BASE",
            ),
        )
        for job, name, candidate, merged, head, base in steps:
            with self.subTest(job=job):
                step = self.step(job, name)
                self.assert_contains_all(step, (
                    f'"${candidate}^2^{{commit}}"',
                    f'"${candidate}^3^{{commit}}"',
                    f'if [ "${merged}" != \\',
                    f'"${head}" ]; then',
                    "merge-base --is-ancestor \\",
                    f'"${base}" \\',
                    f'"${candidate}^1"',
                    "exit 1",
                ))
                self.assertNotIn(
                    "github.event.pull_request.merge_commit_sha", step
                )
        self.assertNotIn(
            "github.event.pull_request.merge_commit_sha", self.workflow
        )

    def test_candidate_step_admits_the_event_merge_and_survives_a_moved_base(self):
        with tempfile.TemporaryDirectory() as root:
            fixture = MergeRefFixture(root)
            for job, name, prefix in (
                (
                    "authoritative-external-action-projection",
                    "Fetch immutable PR candidate without checking it out",
                    "ACTION_PROJECTION",
                ),
                (
                    "external-source-release-admission",
                    "Fetch immutable source-release candidate",
                    "SOURCE_RELEASE",
                ),
            ):
                script = step_shell_script(self.step(job, name))
                self.assertTrue(script, f"{job} step has no shell script")
                number_variable = f"{prefix}_PR_NUMBER"
                base_environment = {
                    f"{prefix}_EVENT": "pull_request_target",
                    f"{prefix}_EXPECTED_HEAD": fixture.head,
                    f"{prefix}_EXPECTED_BASE": fixture.base,
                }
                for label, number, expected in (
                    ("merge of this event's head", "1", fixture.head),
                    ("base branch moved since the event", "2", fixture.head),
                ):
                    with self.subTest(job=job, admitted=label):
                        code, output, stderr = fixture.run_step(
                            script,
                            {**base_environment, number_variable: number},
                        )
                        self.assertEqual(code, 0, stderr)
                        merge = git(
                            fixture.remote, "rev-parse",
                            f"refs/pull/{number}/merge",
                        )
                        self.assertEqual(output, f"revision={merge}\n")
                        self.assertEqual(
                            git(fixture.remote, "rev-parse", f"{merge}^2"),
                            expected,
                        )

    def test_candidate_step_fails_closed_on_every_unpinned_candidate(self):
        with tempfile.TemporaryDirectory() as root:
            fixture = MergeRefFixture(root)
            for job, name, prefix in (
                (
                    "authoritative-external-action-projection",
                    "Fetch immutable PR candidate without checking it out",
                    "ACTION_PROJECTION",
                ),
                (
                    "external-source-release-admission",
                    "Fetch immutable source-release candidate",
                    "SOURCE_RELEASE",
                ),
            ):
                script = step_shell_script(self.step(job, name))
                rejected = (
                    ("head raced ahead of the event", "3",
                     fixture.head, fixture.base,
                     "does not merge this event's head"),
                    ("merge ref is not a merge commit", "4",
                     fixture.head, fixture.base,
                     "is not a merge commit"),
                    ("merge ref has a third parent", "5",
                     fixture.head, fixture.base,
                     "has more than two parents"),
                    ("base is not contained in the merge", "1",
                     fixture.head, fixture.unrelated,
                     "does not contain this event's base"),
                    ("payload carries no head revision", "1",
                     "", fixture.base,
                     "carries no head or base revision"),
                    ("payload carries no base revision", "1",
                     fixture.head, "",
                     "carries no head or base revision"),
                    ("merge ref does not resolve", "9",
                     fixture.head, fixture.base, ""),
                )
                for label, number, head, base, message in rejected:
                    with self.subTest(job=job, rejected=label):
                        code, output, stderr = fixture.run_step(script, {
                            f"{prefix}_EVENT": "pull_request_target",
                            f"{prefix}_EXPECTED_HEAD": head,
                            f"{prefix}_EXPECTED_BASE": base,
                            f"{prefix}_PR_NUMBER": number,
                        })
                        self.assertNotEqual(code, 0, output)
                        self.assertEqual(output, "")
                        if message:
                            self.assertIn(message, stderr)

    def test_source_release_push_candidate_is_the_revision_the_push_names(self):
        script = step_shell_script(self.step(
            "external-source-release-admission",
            "Fetch immutable source-release candidate",
        ))
        with tempfile.TemporaryDirectory() as root:
            fixture = MergeRefFixture(root)
            code, output, stderr = fixture.run_step(script, {
                "SOURCE_RELEASE_EVENT": "push",
                "SOURCE_RELEASE_PUSH_CANDIDATE": fixture.advanced_base,
            })
            self.assertEqual(code, 0, stderr)
            self.assertEqual(output, f"revision={fixture.advanced_base}\n")
            code, output, stderr = fixture.run_step(script, {
                "SOURCE_RELEASE_EVENT": "push",
                "SOURCE_RELEASE_PUSH_CANDIDATE": "",
            })
            self.assertNotEqual(code, 0, output)
            self.assertIn("carries no candidate revision", stderr)

    def test_issue_comment_candidate_keeps_its_declared_trust_ceiling(self):
        """An issue_comment payload names no head, so its ref stays unpinned."""
        script = step_shell_script(self.step(
            "authoritative-external-action-projection",
            "Fetch immutable PR candidate without checking it out",
        ))
        with tempfile.TemporaryDirectory() as root:
            fixture = MergeRefFixture(root)
            code, output, stderr = fixture.run_step(script, {
                "ACTION_PROJECTION_EVENT": "issue_comment",
                "ACTION_PROJECTION_PR_NUMBER": "1",
                "ACTION_PROJECTION_EXPECTED_HEAD": "",
                "ACTION_PROJECTION_EXPECTED_BASE": "",
            })
            self.assertEqual(code, 0, stderr)
            merge = git(fixture.remote, "rev-parse", "refs/pull/1/merge")
            self.assertEqual(output, f"revision={merge}\n")

    def test_body_shape_is_probed_for_rather_than_assumed_of_the_gate(self):
        """The workflow and the gate it runs can arrive from different commits.

        A `pull_request_target` run resolves workflow code and checked-out gate code
        separately, and a pull request's `base.sha` lags the base branch tip, so a
        hard-coded `--pull-request-body-shape` can meet a gate that predates the
        flag. Argparse answers an unknown argument with exit 2 — a check that could
        not run — which would fail pull requests over an advisory readability line.
        """
        step = self.step(
            "authoritative-external-action-projection",
            "Action projection — pull-request description and state",
        )
        self.assert_contains_all(step, (
            "SHAPE=()",
            "grep -q -- --pull-request-body-shape",
            "SHAPE=(--pull-request-body-shape)",
            '"${SHAPE[@]}"',
        ))
        self.assertNotIn("\\\n            --pull-request-body-shape \\", step)
        # The probe is only correct while the gate really spells it that way; a
        # typo on either side would degrade to silence instead of failing.
        help_text = subprocess.run(
            [
                "python3",
                str(REPO / "automation/check_action_projection.py"),
                "--help",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
        self.assertIn("--pull-request-body-shape", help_text)

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
