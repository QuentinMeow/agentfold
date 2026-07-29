#!/usr/bin/env python3
"""Static authority and execution-boundary tests for the harness workflow."""
import re
import unittest
from pathlib import Path

if __package__:
    from .trusted_gate_snapshots import (
        MANUAL_JOBS,
        MANUAL_WORKFLOW_SHA256,
        PINNED_CHECKOUT,
        decode_workflow,
        manual_fixture_contract_errors,
        manual_workflow_fixture,
        migration_mutations,
        trusted_gate_regime,
        workflow_digest,
        workflow_job,
        workflow_job_names,
    )
else:
    from trusted_gate_snapshots import (
        MANUAL_JOBS,
        MANUAL_WORKFLOW_SHA256,
        PINNED_CHECKOUT,
        decode_workflow,
        manual_fixture_contract_errors,
        manual_workflow_fixture,
        migration_mutations,
        trusted_gate_regime,
        workflow_digest,
        workflow_job,
        workflow_job_names,
    )


REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github/workflows/harness.yml"


class HarnessWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow_bytes = WORKFLOW.read_bytes()
        cls.workflow = decode_workflow(cls.workflow_bytes)

    def job(self, name):
        job = workflow_job(self.workflow, name)
        self.assertTrue(job, "missing workflow job {!r}".format(name))
        return job

    def test_current_workflow_is_the_exact_manual_fixture(self):
        fixture = manual_workflow_fixture()
        self.assertEqual(fixture, self.workflow_bytes)
        self.assertEqual(MANUAL_WORKFLOW_SHA256, workflow_digest(fixture))
        self.assertEqual("absent", trusted_gate_regime(fixture))
        self.assertEqual((), manual_fixture_contract_errors(fixture))

    def test_all_workflow_files_reject_retired_or_publishing_authority(self):
        forbidden = (
            "reconcile" + "-and-test",
            "merge_group",
            "--provider-hard",
            "statuses: write",
            "checks: write",
            "id-token: write",
            "secrets.",
            "actions/create-github-app-token",
            "/statuses/",
            "/check-runs",
        )
        workflow_files = sorted((REPO / ".github/workflows").glob("*.y*ml"))
        workflow_files.append(
            REPO / "automation/tests/fixtures/manual-harness.yml"
        )
        self.assertTrue(workflow_files)
        for path in workflow_files:
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden:
                with self.subTest(path=path.name, fragment=fragment):
                    self.assertNotIn(fragment.lower(), text)

    def test_jobs_have_unique_explicit_names_and_explicit_permissions(self):
        self.assertEqual(MANUAL_JOBS, workflow_job_names(self.workflow))
        names = []
        for job_name in MANUAL_JOBS:
            job = self.job(job_name)
            explicit = re.findall(r"^    name: (.+)$", job, re.MULTILINE)
            self.assertEqual(1, len(explicit), job_name)
            names.extend(explicit)
            self.assertRegex(job, r"(?m)^    permissions:(?: \{\}|\n)")
            self.assertNotRegex(
                job, r"(?m)^      [a-z-]+: (?:write|write-all)\s*$"
            )
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("\npermissions: {}\n\njobs:\n", self.workflow)

    def test_every_action_is_pinned_checkout_without_persisted_credentials(self):
        uses = tuple(
            line.strip().partition("uses: ")[2]
            for line in self.workflow.splitlines()
            if line.strip().startswith(("uses: ", "- uses: "))
        )
        self.assertTrue(uses)
        self.assertEqual((PINNED_CHECKOUT,) * len(uses), uses)
        self.assertEqual(len(uses), self.workflow.count("persist-credentials: false"))

    def test_push_job_is_diagnostic_only(self):
        push = self.job("push-repository-diagnostics")
        self.assertIn("name: Push repository diagnostics (not a merge gate)", push)
        self.assertIn("github.event_name == 'push'", push)
        self.assertIn("contents: read", push)
        self.assertIn("automation/reconcile/reconcile.py --check", push)
        self.assertNotIn("automation/run_tests.py", push)
        self.assertNotIn("automation/run_test_gate.py", push)

    def test_target_job_binds_merge_identity_and_runs_base_scripts_only(self):
        trusted = self.job("trusted-pr-merge-diagnostics")
        expected = (
            "name: PR core and merge diagnostics (non-enforcing)",
            "github.event_name == 'pull_request_target'",
            "ref: ${{ github.event.pull_request.base.sha }}",
            '"+refs/pull/$MERGE_DIAGNOSTIC_PR_NUMBER/merge:'
            'refs/agentfold/diagnostics/pr-merge"',
            "github.event.pull_request.merge_commit_sha",
            'test "$MERGE_DIAGNOSTIC_FETCHED" = "$MERGE_DIAGNOSTIC_CANDIDATE"',
            '"$MERGE_DIAGNOSTIC_CANDIDATE^1"',
            '"$MERGE_DIAGNOSTIC_CANDIDATE^2"',
            "python3 automation/check_core_scope.py \\",
            '--range "$MERGE_DIAGNOSTIC_BASE...$MERGE_DIAGNOSTIC_CANDIDATE"',
            '--branch "$MERGE_DIAGNOSTIC_BRANCH"',
            "python3 automation/reconcile/reconcile.py --check \\",
            "--at-transition merge \\",
        )
        for fragment in expected:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, trusted)
        self.assertEqual(
            2,
            trusted.count(
                'if [ "$MERGE_DIAGNOSTIC_ACTION" = synchronize ]; then'
            ),
        )
        self.assertIn(
            '--displaced-tip "$MERGE_DIAGNOSTIC_DISPLACED_TIP"', trusted
        )
        python_commands = tuple(
            line.strip()
            for line in trusted.splitlines()
            if line.strip().startswith("python3 ")
        )
        self.assertEqual(
            (
                "python3 automation/check_core_scope.py \\",
                "python3 automation/reconcile/reconcile.py --check \\",
            ),
            python_commands,
        )
        for forbidden in (
            "git checkout",
            "git switch",
            "git worktree",
            "automation/run_tests.py",
            "automation/run_test_gate.py",
        ):
            self.assertNotIn(forbidden, trusted)

    def test_cooperative_job_is_the_only_candidate_executor(self):
        cooperative = self.job("cooperative-pr-complete-test-diagnostics")
        self.assertIn(
            "name: Cooperative PR complete tests (not a merge gate)", cooperative
        )
        self.assertIn("github.event_name == 'pull_request'", cooperative)
        self.assertIn("contents: read", cooperative)
        self.assertIn("persist-credentials: false", cooperative)
        run_lines = tuple(
            line.strip()
            for line in cooperative.splitlines()
            if line.startswith("        run:")
        )
        self.assertEqual(("run: python3 automation/run_tests.py",), run_lines)
        executors = tuple(
            name
            for name in MANUAL_JOBS
            if "automation/run_tests.py" in self.job(name)
            or "automation/run_test_gate.py" in self.job(name)
        )
        self.assertEqual(("cooperative-pr-complete-test-diagnostics",), executors)

    def test_mutation_canaries_are_rejected_semantically_and_by_snapshot(self):
        fixture = manual_workflow_fixture()
        mutations = migration_mutations(fixture)
        self.assertGreaterEqual(len(mutations), 15)
        for name, mutation in mutations:
            with self.subTest(mutation=name):
                self.assertEqual("invalid", trusted_gate_regime(mutation))
                self.assertTrue(manual_fixture_contract_errors(mutation))


if __name__ == "__main__":
    unittest.main()
