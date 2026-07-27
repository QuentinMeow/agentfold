import contextlib
import datetime
import hashlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "reconcile" / "reconcile.py"
SPEC = importlib.util.spec_from_file_location("reconcile_queue", MODULE_PATH)
RECONCILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECONCILE)


VALID_DECISION = """# Choose the admission boundary

**Status:** waiting
**Filed:** 2026-07-23, by test
**Action:** choose one admission boundary
**Full context:** [design](docs/design.md#boundary)
**Resolution evidence:** `docs/design.md`
**Blocks now:** task:2026-07-23-example

## What you need to know

The repository must choose where unsafe content is rejected.

## Differences

Local checks are bypassable; server checks cover every accepted push.

## Options

### Option A — Local

Run before commit.
*Example consequence:* a skipped hook can still send the object.

### Option B — Server

Run at repository admission.
*Example consequence:* every accepted push passes the guard.

**Your answer:** ______
"""


class ReconcileQueueTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replacements = {
                "REPO": root,
                "QUEUE": root / "message-queue",
                "RETRIES": root / "message-queue" / "needs-agent" / "retries",
                "TASKS": root / "tasks",
                "CONVERSATIONS": root / "history" / "conversations",
                "MEMORY": root / "memory",
                "TODAY": datetime.date(2026, 7, 23),
                "ACTIVE_TASK_ID": None,
                "ACTIVE_TRANSITIONS": set(),
                "CHANGE_RANGE": None,
                "DISPLACED_TIP": None,
            }
            with mock.patch.multiple(RECONCILE, **replacements):
                yield root

    @staticmethod
    def write(root, rel, text=""):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    @staticmethod
    def messages(findings):
        return [finding.message for finding in findings]

    @staticmethod
    def git(root, *args):
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.strip()

    def init_git(self, root):
        self.git(root, "init")
        self.git(root, "config", "user.name", "Test")
        self.git(root, "config", "user.email", "test@example.invalid")

    def test_github_adapter_binds_event_merge_and_limits_push_to_reconciliation(self):
        workflow = (
            MODULE_PATH.parents[2] / ".github/workflows/harness.yml"
        ).read_text(encoding="utf-8")
        on_block = workflow.partition("on:\n")[2].partition(
            "\npermissions:"
        )[0]
        self.assertNotIn("pull_request:\n", on_block)
        self.assertIn("pull_request_target:\n", on_block)
        self.assertIn("merge_group:\n    types: [checks_requested]", on_block)

        prepare = workflow.partition(
            "  prepare-trusted-final-test-gate:\n"
        )[2].partition("  trusted-final-test-runner:\n")[0]
        self.assertTrue(prepare, "trusted final-gate preparation is missing")
        for expected in (
            "TEST_GATE_BASE: ${{ github.event.pull_request.base.sha }}",
            "TEST_GATE_HEAD: ${{ github.event.pull_request.head.sha }}",
            "TEST_GATE_CANDIDATE: ${{ github.event.pull_request.merge_commit_sha }}",
            '"+refs/pull/$TEST_GATE_PR_NUMBER/head:refs/agentfold/test-gate/head"',
            '"+refs/pull/$TEST_GATE_PR_NUMBER/merge:refs/agentfold/test-gate/merge"',
            'rev-parse --verify "$TEST_GATE_CANDIDATE^1"',
            'rev-parse --verify "$TEST_GATE_CANDIDATE^2"',
        ):
            self.assertIn(expected, prepare)

        runner = workflow.partition(
            "  trusted-final-test-runner:\n"
        )[2].partition("  publish-trusted-final-test-check:\n")[0]
        self.assertTrue(runner, "credential-free final-gate runner is missing")
        self.assertIn("permissions: {}", runner)
        self.assertIn("--provider-hard", runner)
        self.assertIn("github.event_name == 'merge_group'", runner)
        self.assertIn("run: exit 1", runner)

        publisher = workflow.partition(
            "  publish-trusted-final-test-check:\n"
        )[2].partition("  authoritative-external-action-projection:\n")[0]
        self.assertTrue(publisher, "exact-candidate check publisher is missing")
        self.assertIn("checks: write", publisher)
        self.assertIn(
            "github.event.pull_request.merge_commit_sha || github.sha",
            publisher,
        )
        self.assertIn(
            'TEST_GATE_PREPARED_CANDIDATE" = "$TEST_GATE_CANDIDATE',
            publisher,
        )
        self.assertIn("AgentFold trusted hard final gate", publisher)
        self.assertIn('head_sha "$TEST_GATE_CANDIDATE"', publisher)
        self.assertIn(
            "Schema version 1 does not support merge-group admission.",
            publisher,
        )
        self.assertIn('test "$TEST_GATE_CONCLUSION" = success', publisher)

        push = workflow.partition(
            "  reconcile-and-test:\n"
        )[2].partition("  prepare-trusted-final-test-gate:\n")[0]
        self.assertTrue(push, "push reconciliation step is missing")
        self.assertIn("if: ${{ github.event_name == 'push' }}", push)
        self.assertIn("if: github.event_name == 'push'", push)
        self.assertIn(
            '[ "$QUEUE_PUSH_BEFORE" = '
            '"0000000000000000000000000000000000000000" ]',
            push,
        )
        self.assertIn('QUEUE_CHANGE_RANGE="root:$QUEUE_PUSH_HEAD"', push)
        self.assertIn(
            'git cat-file -e "$QUEUE_PUSH_BEFORE^{commit}"', push
        )
        self.assertIn(
            'QUEUE_CHANGE_RANGE="$QUEUE_PUSH_BASE...$QUEUE_PUSH_HEAD"', push,
        )
        self.assertIn(
            'QUEUE_DISPLACED_ARGS=(--displaced-tip "$QUEUE_PUSH_BEFORE")', push,
        )
        self.assertIn("automation/reconcile/reconcile.py --check", push)
        self.assertNotIn("automation/run_tests.py", push)
        self.assertNotIn("automation/run_test_gate.py", push)
        self.assertNotIn("pull_request", push)
        self.assertNotIn("--at-transition repository-admission", workflow)

    def test_trusted_gate_migration_never_mixes_provider_regimes(self):
        workflow = (
            MODULE_PATH.parents[2] / ".github/workflows/harness.yml"
        ).read_text(encoding="utf-8")
        job_names = (
            "prepare-trusted-final-test-gate",
            "trusted-final-test-runner",
            "publish-trusted-final-test-check",
        )

        def job(name, next_name=None):
            marker = f"  {name}:\n"
            if marker not in workflow:
                return ""
            remainder = workflow.partition(marker)[2]
            if next_name is None:
                return remainder
            return remainder.partition(f"  {next_name}:\n")[0]

        blocks = (
            job(job_names[0], job_names[1]),
            job(job_names[1], job_names[2]),
            job(job_names[2], "authoritative-external-action-projection"),
        )
        present = tuple(bool(block) for block in blocks)
        if not any(present):
            regime = "legacy"
        elif not all(present):
            regime = "invalid"
        else:
            prepare, runner, publisher = blocks
            common = (
                "permissions:\n      contents: read" in prepare
                and "permissions: {}" in runner
                and "--provider-hard" in runner
                and "environment: agentfold-trusted-publisher" in publisher
                and "statuses/$TEST_GATE_CANDIDATE" in publisher
            )
            legacy = (
                "if: ${{ github.event_name == 'pull_request_target' }}" in prepare
                and "github.event_name == 'merge_group'" in runner
                and "Reject unsupported merge-queue admission" in runner
            )
            restricted_fragments = (
                "github.event.action == 'opened' || github.event.action == 'synchronize'",
                "github.event.pull_request.base.ref == github.event.repository.default_branch",
                "github.event.pull_request.head.repo.id == github.event.repository.id",
                "startsWith(github.event.pull_request.head.ref, 'task/')",
            )
            restricted = (
                all(
                    all(fragment in block for fragment in restricted_fragments)
                    for block in blocks
                )
                and "github.event_name == 'merge_group'" not in runner
                and "Reject unsupported merge-queue admission" not in runner
            )
            regime = (
                "legacy" if common and legacy and not restricted
                else "restricted" if common and restricted and not legacy
                else "invalid"
            )
        self.assertIn(regime, ("legacy", "restricted"))

    def test_queue_checks_no_op_when_queue_is_absent(self):
        with self.repo() as root:
            self.assertEqual([], list(RECONCILE.check_queue_name()))
            self.assertEqual([], list(RECONCILE.check_queue_schema()))
            self.assertEqual([], list(RECONCILE.check_stale_queue()))
            task = root / "tasks/0_backlog/2026-07-23-example"
            task.mkdir(parents=True)
            (task / "task.md").write_text(
                "# Example\n\n"
                "**Claimed-by:** unclaimed\n"
                "**Filed:** 2026-07-23\n"
                "**Repository scope:** core\n",
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_task_structure()))

    def test_valid_human_decision_passes_name_and_schema(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                VALID_DECISION,
            )
            self.assertEqual([], list(RECONCILE.check_queue_name()))
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_queue_v1_requires_concrete_human_projection_context(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            item = self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                VALID_DECISION,
            )

            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any(
                "**Why-you-might-care:**" in message for message in messages
            ), messages)
            self.assertTrue(any(
                "**If-you-do-nothing:**" in message for message in messages
            ), messages)

            item.write_text(
                VALID_DECISION.replace(
                    "**Full context:** [design](docs/design.md#boundary)\n",
                    "**Full context:** [design](docs/design.md#boundary)\n"
                    "**Why-you-might-care:** <practical consequence>\n"
                    "**If-you-do-nothing:** ______\n",
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any(
                "**Why-you-might-care:** is empty" in message
                for message in messages
            ), messages)
            self.assertTrue(any(
                "**If-you-do-nothing:** is empty" in message
                for message in messages
            ), messages)

            item.write_text(
                VALID_DECISION.replace(
                    "**Full context:** [design](docs/design.md#boundary)\n",
                    "**Full context:** [design](docs/design.md#boundary)\n"
                    "**Why-you-might-care:** This choice controls admission.\n"
                    "**If-you-do-nothing:** The task remains blocked.\n",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_commented_or_fenced_queue_evidence_is_not_schema(self):
        for wrapper in (
            "<!--\n" + VALID_DECISION + "-->\n",
            "```markdown\n" + VALID_DECISION + "```\n",
        ):
            with self.subTest(wrapper=wrapper[:4]), self.repo() as root:
                self.write(root, "docs/design.md", "# Design\n")
                self.write(
                    root,
                    "message-queue/needs-human/decisions/blocking-hidden.md",
                    wrapper,
                )
                messages = self.messages(RECONCILE.check_queue_schema())
                self.assertTrue(any("**Blocks now:**" in message
                                    for message in messages))
                self.assertTrue(any("**Status:**" in message for message in messages))
                self.assertTrue(any("## What you need to know" in message
                                    for message in messages))

    def test_angle_link_with_spaces_is_valid_full_context(self):
        with self.repo() as root:
            self.write(root, "docs/My Design.md", "# Design\n")
            text = VALID_DECISION.replace(
                "[design](docs/design.md#boundary)",
                "[design](<docs/My Design.md#boundary>)",
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                text,
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_code_escaped_indented_and_malformed_links_are_not_context(self):
        disguises = (
            "`[design](docs/design.md)`",
            r"\[design](docs/design.md)",
            "not-a-link](docs/design.md)",
            "\n    [design](docs/design.md)",
        )
        for disguise in disguises:
            with self.subTest(disguise=disguise), self.repo() as root:
                self.write(root, "docs/design.md", "# Design\n")
                self.write(
                    root,
                    "message-queue/needs-agent/requests/"
                    "non-blocking-inspect.md",
                    "# Inspect\n\n"
                    "**Status:** open\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** inspect the design\n"
                    f"**Full context:** {disguise}\n"
                    "**If unanswered:** leave the design unchanged\n",
                )
                messages = self.messages(RECONCILE.check_queue_schema())
                self.assertTrue(any("does not point to an existing" in message
                                    for message in messages))

    def test_invalid_backtick_fence_info_does_not_hide_fields(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            text = "```bad`info\n" + VALID_DECISION
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                text,
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_pathological_context_paths_report_without_crashing(self):
        for candidate in ("docs/\0escape.md", "docs/" + "a" * 10000 + ".md"):
            with self.subTest(length=len(candidate)), self.repo() as root:
                self.write(
                    root,
                    "message-queue/needs-agent/requests/"
                    "non-blocking-inspect.md",
                    "# Inspect\n\n"
                    "**Status:** open\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** inspect the source\n"
                    f"**Full context:** `{candidate}`\n"
                    "**If unanswered:** leave the source unchanged\n",
                )
                messages = self.messages(RECONCILE.check_queue_schema())
                self.assertTrue(any("does not point to an existing" in message
                                    for message in messages))

    def test_context_and_queue_state_reject_symlinks(self):
        with self.repo() as root:
            external = self.write(root, "outside.md", "# Outside\n")
            source = root / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.symlink_to(external)
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-inspect.md",
                "# Inspect\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the source\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave the source unchanged\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("does not point to an existing" in message
                                for message in messages))

            broken = (
                root / "message-queue/needs-human/reviews/"
                "blocking-broken.md"
            )
            broken.parent.mkdir(parents=True, exist_ok=True)
            broken.symlink_to(root / "does-not-exist.md")
            location_messages = self.messages(RECONCILE.check_queue_location())
            self.assertTrue(any("regular file, not a symlink" in message
                                for message in location_messages))

    def test_invalid_filed_date_is_reported_without_crashing_stale_check(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                VALID_DECISION.replace("2026-07-23", "2026-99-99", 1),
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("valid YYYY-MM-DD" in message for message in messages))
            list(RECONCILE.check_stale_queue())

    def test_duplicate_structured_field_is_rejected(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            text = VALID_DECISION.replace(
                "**Action:** choose one admission boundary",
                "**Action:** choose one admission boundary\n"
                "**Action:** choose a different boundary",
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                text,
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("**Action:** appears more than once" in message
                                for message in messages))

    def test_blocks_now_rejects_prose_even_when_it_mentions_a_task(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            queue_rel = (
                "message-queue/needs-agent/requests/blocking-misleading.md"
            )
            self.write(
                root,
                queue_rel,
                "# Misleading\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect\n"
                "**Full context:** `docs/source.md`\n"
                "**Blocks now:** operation:publish; this does not block "
                "task:2026-07-23-example\n",
            )
            self.make_task(root, "2_blocked", f"`{queue_rel}`")
            schema_messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("exactly one task:" in message
                                for message in schema_messages))
            task_messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("reciprocal live blocking-*" in message
                                for message in task_messages))

    def test_queue_filename_prefix_is_exact_and_docs_are_exempt(self):
        with self.repo() as root:
            self.write(root, "message-queue/AGENTS.md", "# Contract\n")
            self.write(root, "message-queue/CLAUDE.md", "@AGENTS.md\n")
            self.write(root, "message-queue/needs-agent/requests/README.md", "# Help\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/urgent-admission.md",
                "# Invalid\n",
            )
            self.write(
                root,
                "message-queue/needs-agent/requests/blocking-not-markdown.txt",
                "invalid\n",
            )
            findings = list(RECONCILE.check_queue_name())
            self.assertEqual(2, len(findings))
            self.assertTrue(all("dependency timing" in finding.message
                                for finding in findings))

    def test_custom_typed_endpoint_is_allowed_but_extra_nesting_is_not(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/requests/blocking-hidden.md",
                "**Blocks now:** operation:review\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_location()))
            self.write(
                root,
                "message-queue/needs-human/requests/archive/blocking-nested.md",
                "**Blocks now:** operation:review\n",
            )
            findings = list(RECONCILE.check_queue_location())
            self.assertEqual(1, len(findings))
            self.assertIn("one actor folder and one typed leaf", findings[0].message)

    def test_custom_typed_endpoint_gets_generic_human_schema(self):
        with self.repo() as root:
            self.write(root, "docs/security.md", "# Security\n")
            self.write(
                root,
                "message-queue/needs-human/security-reviews/"
                "non-blocking-check-boundary.md",
                "# Check boundary\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the boundary\n"
                "**Full context:** `docs/security.md`\n"
                "**Resolution evidence:** `docs/security.md`\n"
                "**If unanswered:** retain the current boundary\n\n"
                "## What you need to know\n\nA typed extension needs review.\n\n"
                "## Differences\n\nAccept retains it; request-change revises it.\n\n"
                "## Example\n\nAccept permits A; change permits B.\n\n"
                "**Your review:** ______\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_location()))
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_timing_fields_follow_filename_and_obsolete_blocking_is_rejected(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/retries/non-blocking-repair.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Check:** example\n"
                "**Subject:** `broken/file.md`\n"
                "**Action:** repair the file\n"
                "**Blocking:** no\n"
                "**Blocks now:** task:example\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("obsolete **Blocking:**" in message for message in messages))
            self.assertTrue(any("missing required field **If unanswered:**" in message
                                for message in messages))
            self.assertTrue(any("**Blocks now:** contradicts" in message
                                for message in messages))

    def test_human_items_require_context_differences_examples_and_response(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-thin-review.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the claim\n"
                "**Full context:** `docs/missing.md`\n"
                "**If unanswered:** keep the current wording\n\n"
                "## Differences\n\n<describe the alternatives>\n\n"
                "## Example\n\n<add a concrete example>\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("**Your review:**" in message for message in messages))
            self.assertTrue(any("Resolution evidence" in message
                                for message in messages))
            self.assertTrue(any("does not point to an existing" in message
                                for message in messages))
            self.assertTrue(any("## What you need to know" in message
                                for message in messages))
            self.assertTrue(any("## Differences" in message for message in messages))
            self.assertTrue(any("## Example" in message for message in messages))

    def test_review_artifact_state_prevents_premature_response(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.init_git(root)
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "docs/head.md", "# Head\n")
            self.git(root, "add", "docs/head.md")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-artifact.md"
            )
            awaiting = (
                "# Review artifact\n\n"
                "**Status:** awaiting-artifact\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review after publication\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks at:** transition:merge task:2026-07-23-example\n"
                "**Until then:** continue implementation\n\n"
                "## What you need to know\n\nThe diff is not published yet.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nOne merges; one returns to implementation.\n\n"
                "**Your review:** ______\n"
            )
            item = self.write(root, path, awaiting)
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

            item.write_text(
                awaiting.replace("**Your review:** ______", "**Your review:** approve"),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("cannot exist before the artifact" in message
                                for message in messages))

            item.write_text(
                awaiting.replace("awaiting-artifact", "waiting"),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("must identify exactly one" in message
                                for message in messages))

            item.write_text(
                awaiting.replace("awaiting-artifact", "waiting").replace(
                    "**Review target:** pending",
                    f"**Review target:** git:{base}...{head}",
                ).replace(
                    "**Review revision:** pending",
                    f"**Review revision:** git:{base}...{head}",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    f"git:{base}...{head}",
                    "git:" + "a" * 40 + "..." + "b" * 40,
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("not a reviewable Git artifact" in message
                                for message in messages))

    def test_review_response_is_bound_to_exact_local_bytes(self):
        with self.repo() as root:
            target = self.write(root, "docs/source.md", "# Source\n")
            digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            item = self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-exact.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review exact bytes\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the current bytes\n\n"
                "## What you need to know\n\nJudge one exact file.\n\n"
                "## Differences\n\nApprove keeps it; changes revise it.\n\n"
                "## Example\n\nApprove ships A; change produces B.\n\n"
                "**Your review:** ______\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Your review:** ______", "**Your review:** approve"
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("not bound" in message for message in messages))

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Reviewed revision:** ______",
                    f"**Reviewed revision:** {digest}",
                ).replace(
                    "**Review outcome:** pending",
                    "**Review outcome:** approved",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))
            target.write_text("# Changed\n", encoding="utf-8")
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("does not match target bytes" in message
                                for message in messages))

    def test_review_target_must_not_mix_local_and_https_artifacts(self):
        with self.repo() as root:
            target = self.write(root, "docs/source.md", "# Source\n")
            digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-ambiguous.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review one artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md` and "
                "https://example.test/pull/1\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the current bytes\n\n"
                "## What you need to know\n\nOnly one artifact may be judged.\n\n"
                "## Differences\n\nOne target is bindable; two are ambiguous.\n\n"
                "## Example\n\nA response cannot silently apply to only one target.\n\n"
                "**Your review:** ______\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("must identify exactly one" in message
                                for message in messages))

    def test_review_target_rejects_concatenated_https_artifacts(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            item = self.write(
                root,
                "message-queue/needs-human/reviews/"
                "non-blocking-concatenated.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review one artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** "
                "https://one.example/a,https://two.example/b\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the current artifact\n\n"
                "## What you need to know\n\nJudge one artifact.\n\n"
                "## Differences\n\nOne target binds; two are ambiguous.\n\n"
                "## Example\n\nApproval must bind one target.\n\n"
                "**Your review:** ______\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("must identify exactly one" in message
                                for message in messages))

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "https://one.example/a,https://two.example/b",
                    "[artifact](<https://example.test/build(foo)>)",
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertFalse(any("must identify exactly one" in message
                                 for message in messages))

    def test_review_target_accepts_exact_local_markdown_link_with_spaces(self):
        with self.repo() as root:
            target = self.write(root, "docs/My Artifact.bin", "artifact\n")
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "non-blocking-local-link.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the artifact\n"
                "**Full context:** [artifact](<docs/My Artifact.bin>)\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                "**Review target:** [artifact](<docs/My Artifact.bin>)\n"
                f"**Review revision:** sha256:{digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the artifact\n\n"
                "## What you need to know\n\nJudge one exact artifact.\n\n"
                "## Differences\n\nApprove keeps it; changes revise it.\n\n"
                "## Example\n\nOne ships; one returns to work.\n\n"
                "**Your review:** ______\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_review_target_accepts_and_binds_local_git_range(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "docs/source.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "docs/source.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            target = f"git:{base}...{head}"
            item = self.write(
                root,
                "message-queue/needs-human/reviews/"
                "non-blocking-git-range.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the exact diff\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                f"**Review target:** {target}\n"
                f"**Review revision:** {target}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the commits unmerged\n\n"
                "## What you need to know\n\nJudge one local Git diff.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nOne merges; one returns to work.\n\n"
                "**Your review:** ______\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    f"**Review revision:** {target}",
                    f"**Review revision:** git:{head}",
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("do not match" in message for message in messages))

    def test_review_binding_kind_matches_its_boundary_receipt(self):
        with self.repo() as root:
            self.init_git(root)
            target = self.write(root, "docs/source.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            target.write_text("# Head\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            common = (
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the exact artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/disposition.md`\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Until then:** continue implementation\n\n"
                "## What you need to know\n\nJudge one exact artifact.\n\n"
                "## Differences\n\nApproval crosses; changes revise.\n\n"
                "## Example\n\nOne proceeds; one remains blocked.\n\n"
                "**Your review:** ______\n"
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "future-blocking-local-merge.md",
                "# Local merge review\n\n"
                + common.replace(
                    "**Reviewed revision:** ______\n",
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    "**Reviewed revision:** ______\n",
                ).replace(
                    "**Until then:** continue implementation\n",
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** continue implementation\n",
                ),
            )
            git_target = f"git:{base}...{head}"
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "future-blocking-git-task.md",
                "# Git task review\n\n"
                + common.replace(
                    "**Reviewed revision:** ______\n",
                    f"**Review target:** {git_target}\n"
                    f"**Review revision:** {git_target}\n"
                    "**Reviewed revision:** ______\n",
                ).replace(
                    "**Until then:** continue implementation\n",
                    "**Blocks at:** transition:start "
                    "task:2026-07-23-example\n"
                    "**Until then:** continue implementation\n",
                ),
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any(
                "merge-bound review must bind" in message
                for message in messages
            ), messages)
            self.assertTrue(any(
                "task-lifecycle review must bind" in message
                for message in messages
            ), messages)

    def test_review_target_and_cancellation_evidence_must_be_distinct(self):
        with self.repo() as root:
            target = self.write(root, "docs/source.md", "# Source\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-same.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the source\n\n"
                "## What you need to know\n\nJudge one source.\n\n"
                "## Differences\n\nApproval keeps it; rejection withdraws it.\n\n"
                "## Example\n\nA distinct record can preserve cancellation.\n\n"
                "**Your review:** ______\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any(
                "same file" in message for message in messages
            ), messages)

    def test_review_target_counts_missing_declared_local_artifact(self):
        with self.repo() as root:
            target = self.write(root, "docs/source.md", "# Source\n")
            digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-ambiguous.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review one artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md` and "
                "`docs/missing.md#later`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the current bytes\n\n"
                "## What you need to know\n\nOnly one artifact may be judged.\n\n"
                "## Differences\n\nMissing files still make the target ambiguous.\n\n"
                "## Example\n\nApproval cannot silently ignore the missing target.\n\n"
                "**Your review:** ______\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("must identify exactly one" in message
                                for message in messages))

    def test_review_rejects_moving_task_path_anywhere_in_item(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Stable context\n")
            target = self.write(
                root,
                "tasks/1_in-progress/2026-07-23-example/design.md",
                "# Moving target\n",
            )
            digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-moving.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the moving artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** "
                "`tasks/1_in-progress/2026-07-23-example/design.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep the current wording\n\n"
                "## What you need to know\n\nThe task path can move.\n\n"
                "## Differences\n\nStable paths survive status changes; moving paths do not.\n\n"
                "## Example\n\nReview must remain reachable after task review starts.\n\n"
                "**Your review:** ______\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("status-dependent task path" in message
                                for message in messages))

    def test_local_review_hash_uses_index_not_unstaged_bytes(self):
        with self.repo() as root:
            self.init_git(root)
            target = self.write(root, "docs/source.md", "# Indexed\n")
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "indexed source")
            digest = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-indexed.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review indexed bytes\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**If unanswered:** keep indexed bytes\n\n"
                "## What you need to know\n\nThe index is the commit candidate.\n\n"
                "## Differences\n\nIndex bytes commit; working bytes may not.\n\n"
                "## Example\n\nAn unstaged edit cannot change the requested artifact.\n\n"
                "**Your review:** ______\n",
            )
            target.write_bytes(b"# Unstaged\r\n")
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_queue_schema_uses_staged_item_not_unstaged_repair(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "docs/source.md", "# Source\n")
            item = self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-staged.md",
                "# Request\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave the source unchanged\n",
            )
            self.git(root, "add", ".")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Filed:** 2026-07-23",
                    "**Filed:** 2026-07-23\n"
                    "**Action:** inspect the source",
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("missing required field **Action:**" in message
                                for message in messages))

    def test_git_review_requires_literal_commits_with_shared_history(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.git(root, "tag", "-a", "annotated", "-m", "tag")
            tag_object = self.git(root, "rev-parse", "annotated^{tag}")
            tree = self.git(root, "write-tree")
            unrelated = self.git(root, "commit-tree", tree, "-m", "unrelated")

            tag_problems = RECONCILE.git_review_revision_problems(
                "git:" + tag_object
            )
            self.assertTrue(any("not a commit" in problem
                                for problem in tag_problems))
            range_problems = RECONCILE.git_review_revision_problems(
                f"git:{base}...{unrelated}"
            )
            self.assertIn("base and head have no merge base", range_problems)

    def test_decision_requires_two_options_and_two_concrete_consequences(self):
        with self.repo() as root:
            self.write(root, "docs/design.md", "# Design\n")
            text = VALID_DECISION.replace(
                "### Option B — Server\n\nRun at repository admission.\n"
                "*Example consequence:* every accepted push passes the guard.\n\n",
                "",
            )
            self.write(
                root,
                "message-queue/needs-human/decisions/blocking-admission.md",
                text,
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("at least two" in message for message in messages))
            self.assertTrue(any("for each choice" in message for message in messages))

    def test_agent_request_requires_durable_context(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-investigate.md",
                "# Investigate\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the report\n"
                "**Full context:** [report](docs/missing.md)\n"
                "**If unanswered:** leave the backlog unchanged\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("does not point to an existing" in message
                                for message in messages))

    def test_future_boundary_uses_machine_readable_grammar(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "future-blocking-investigate.md",
                "# Investigate\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the report\n"
                "**Full context:** `docs/source.md`\n"
                "**Blocks at:** someday, probably\n"
                "**Until then:** continue discovery\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("exact date, event:, or transition:"
                                in message for message in messages))

    def test_task_lifecycle_boundary_requires_task_scope(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "future-blocking-review.md",
                "# Review\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the report\n"
                "**Full context:** `docs/source.md`\n"
                "**Blocks at:** transition:review\n"
                "**Until then:** keep the task in progress\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any(
                "task lifecycle transition requires" in message
                for message in messages
            ))

    def test_external_transition_may_remain_globally_scoped(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "future-blocking-merge.md",
                "# Merge\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the report\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks at:** transition:merge\n"
                "**Until then:** continue implementation\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

    def test_queue_actor_status_and_resolution_evidence_are_explicit(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-invalid-lifecycle.md",
                "# Repair\n\n"
                "**Status:** folding\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave it unchanged\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("**Status:** must be one of" in m for m in messages))
            self.assertTrue(any("**Resolution evidence:**" in m for m in messages))

    def test_manual_retry_requires_live_resolution_evidence(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Broken\n")
            manual = self.write(
                root,
                "message-queue/needs-agent/retries/blocking-manual.md",
                "# Repair manually\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23, by agent\n"
                "**Check:** manual\n"
                "**Subject:** `docs/source.md`\n"
                "**Action:** repair the source\n"
                "**Blocks now:** transition:merge\n\n"
                "## Broken invariant\n\nThe source is broken.\n\n"
                "## Fix\n\nRepair it.\n",
            )
            self.assertTrue(any(
                finding.subject == manual.relative_to(root)
                and "**Resolution evidence:**" in finding.message
                for finding in RECONCILE.check_queue_schema()
            ))

            finding = RECONCILE.Finding(
                "queue-name",
                Path("docs/source.md"),
                "generated repair",
                "repair it",
            )
            generated = (
                "message-queue/needs-agent/retries/"
                f"blocking-{RECONCILE.finding_key(finding)}.md"
            )
            self.write(root, generated, RECONCILE.retry_text(finding))
            generated_findings = [
                item for item in RECONCILE.check_queue_schema()
                if item.subject == Path(generated)
            ]
            self.assertEqual([], generated_findings)

    def test_manual_retry_can_be_claimed_and_resolved_with_evidence(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Broken\n")
            path = (
                "message-queue/needs-agent/retries/"
                "blocking-manual-repair.md"
            )
            item = self.write(
                root,
                path,
                "# Repair manually\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23, by agent\n"
                "**Check:** manual\n"
                "**Subject:** `docs/source.md`\n"
                "**Action:** repair the source\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n\n"
                "## Broken invariant\n\nThe source is broken.\n\n"
                "## Fix\n\nRepair it.\n",
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file manual retry")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim manual retry")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_open_action_cannot_be_replaced_in_place(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/old.md", "# Old context\n")
            self.write(root, "docs/new.md", "# New context\n")
            path = (
                "message-queue/needs-agent/requests/blocking-action.md"
            )
            item = self.write(
                root,
                path,
                "# Preserve the old action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the data-loss bug\n"
                "**Full context:** `docs/old.md`\n"
                "**Resolution evidence:** `docs/old.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file original action")
            item.write_text(
                "# Unrelated replacement\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** polish unrelated prose\n"
                "**Full context:** `docs/new.md`\n"
                "**Resolution evidence:** `docs/new.md`\n"
                "**Blocks now:** transition:merge\n",
                encoding="utf-8",
            )
            self.git(root, "add", path)

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("action identity changed", findings[0].message)

    def test_human_counter_question_progresses_through_successor(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/design.md", "# Unresolved\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            base = self.git(root, "rev-parse", "HEAD")
            path = (
                "message-queue/needs-human/decisions/"
                "blocking-choice.md"
            )
            item = self.write(
                root,
                path,
                VALID_DECISION.replace(
                    "task:2026-07-23-example", "transition:merge"
                ).replace(
                    "**Your answer:** ______",
                    "**Your answer:** What does option B change?",
                ),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record human counter question")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim counter question")
            source.write_text(
                "# Option B moves enforcement to CI\n", encoding="utf-8"
            )
            successor_path = (
                "message-queue/needs-human/decisions/"
                "blocking-clarified-choice.md"
            )
            self.write(
                root,
                successor_path,
                VALID_DECISION.replace(
                    "task:2026-07-23-example", "transition:merge"
                ).replace(
                    "**Full context:** [design](docs/design.md#boundary)",
                    "**Full context:** [design](docs/design.md#boundary)\n"
                    f"**Supersedes:** `{path}`",
                ),
            )
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "answer and continue clarified choice")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_waiting_human_response_cannot_be_rewritten(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/design.md", "# Unresolved\n")
            path = (
                "message-queue/needs-human/decisions/"
                "blocking-choice.md"
            )
            item = self.write(
                root,
                path,
                VALID_DECISION.replace(
                    "task:2026-07-23-example", "transition:merge"
                ).replace(
                    "**Your answer:** ______",
                    "**Your answer:** choose option B",
                ),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record final human answer")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Your answer:** choose option B",
                    "**Your answer:** choose option A",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("first concrete response", findings[0].message)

    def test_waiting_review_cannot_rebind_with_first_response_in_range(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-immutable-review.md"
            )
            item = self.write(
                root,
                path,
                "# Review exact artifact\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the published artifact\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** https://example.invalid/revision-a\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks now:** transition:merge\n\n"
                "## What you need to know\n\nReview one published artifact.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nApproval permits merge.\n\n"
                "**Your review:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "publish review revision a")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "https://example.invalid/revision-a",
                    "https://example.invalid/revision-b",
                ).replace(
                    f"**Review revision:** sha256:{'a' * 64}",
                    f"**Review revision:** sha256:{'b' * 64}",
                ).replace(
                    "**Reviewed revision:** ______",
                    f"**Reviewed revision:** sha256:{'b' * 64}",
                ).replace(
                    "**Review outcome:** pending",
                    "**Review outcome:** approved",
                ).replace(
                    "**Your review:** ______",
                    "**Your review:** approved",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "rebind and approve revision b")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("immutable review binding changed", findings[0].message)

    def test_review_binding_is_published_by_awaiting_to_waiting_transition(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-publish-review.md"
            )
            item = self.write(
                root,
                path,
                "# Review exact artifact\n\n"
                "**Status:** awaiting-artifact\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the artifact after publication\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks now:** transition:merge\n\n"
                "## What you need to know\n\nThe artifact is not published yet.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nApproval permits merge.\n\n"
                "**Your review:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file review before publication")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** awaiting-artifact",
                    "**Status:** waiting",
                ).replace(
                    "**Review target:** pending",
                    "**Review target:** https://example.invalid/revision-a",
                ).replace(
                    "**Review revision:** pending",
                    f"**Review revision:** sha256:{'a' * 64}",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "publish review revision a")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_unanswered_review_can_retract_then_republish_binding(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Revision A\n")
            digest_a = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-republish.md"
            )
            item = self.write(
                root,
                path,
                "# Review exact artifact\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the current artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                "**Why-you-might-care:** The bound revision controls acceptance.\n"
                "**If-you-do-nothing:** The merge boundary remains pending.\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest_a}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks at:** event:publication\n"
                "**Until then:** continue implementation\n\n"
                "## What you need to know\n\nReview one exact revision.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nRevision A may be replaced before response.\n\n"
                "**Your review:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "publish revision a")
            base = self.git(root, "rev-parse", "HEAD")

            target.write_text("# Revision B\n", encoding="utf-8")
            digest_b = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** awaiting-artifact"
                ).replace(
                    "**Review target:** `docs/source.md`",
                    "**Review target:** pending",
                ).replace(
                    f"**Review revision:** {digest_a}",
                    "**Review revision:** pending",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "retract obsolete revision a")

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** awaiting-artifact", "**Status:** waiting"
                ).replace(
                    "**Review target:** pending",
                    "**Review target:** `docs/source.md`",
                ).replace(
                    "**Review revision:** pending",
                    f"**Review revision:** {digest_b}",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "publish revision b")
            head = self.git(root, "rev-parse", "HEAD")

            self.assertEqual([], list(RECONCILE.check_queue_schema()))
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_review_republication_cannot_bind_and_approve_same_edge(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Revision B\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-republish.md"
            )
            item = self.write(
                root,
                path,
                "# Review exact artifact\n\n"
                "**Status:** awaiting-artifact\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review after publication\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks now:** transition:merge\n\n"
                "## What you need to know\n\nThe revision is not published yet.\n\n"
                "## Differences\n\nApprove accepts it; changes revise it.\n\n"
                "## Example\n\nPublication precedes human judgment.\n\n"
                "**Your review:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "await revision")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** awaiting-artifact", "**Status:** waiting"
                ).replace(
                    "**Review target:** pending",
                    "**Review target:** `docs/source.md`",
                ).replace(
                    "**Review revision:** pending",
                    f"**Review revision:** {digest}",
                ).replace(
                    "**Reviewed revision:** ______",
                    f"**Reviewed revision:** {digest}",
                ).replace(
                    "**Review outcome:** pending",
                    "**Review outcome:** approved",
                ).replace(
                    "**Your review:** ______",
                    "**Your review:** approved",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "publish and approve revision")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("publication transition", findings[0].message)

    def test_answered_review_cannot_retract_its_binding(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Revision A\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-answered-review.md"
            )
            item = self.write(
                root,
                path,
                "# Review exact artifact\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** rejected\n"
                "**Blocks now:** transition:merge\n"
                "## What you need to know\n\nJudge the exact revision.\n\n"
                "## Differences\n\nReject ends it; changes request revision.\n\n"
                "## Example\n\nA response freezes revision A.\n\n"
                "**Your review:** reject revision a\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record response")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** awaiting-artifact"
                ).replace(
                    "**Review target:** `docs/source.md`",
                    "**Review target:** pending",
                ).replace(
                    f"**Review revision:** {digest}",
                    "**Review revision:** pending",
                ).replace(
                    f"**Reviewed revision:** {digest}",
                    "**Reviewed revision:** ______",
                ).replace(
                    "**Review outcome:** rejected",
                    "**Review outcome:** pending",
                ).replace(
                    "**Your review:** reject revision a",
                    "**Your review:** ______",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "attempt response retraction")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("immutable review binding", findings[0].message)

    def test_review_cancellation_evidence_freezes_with_first_response(self):
        path = (
            "message-queue/needs-human/reviews/"
            "non-blocking-review-evidence.md"
        )
        unanswered = (
            "# Review\n\n"
            "**Status:** waiting\n"
            "**Action:** review the proposal\n"
            "**Review target:** pending\n"
            "**Review revision:** pending\n"
            "**Reviewed revision:** ______\n"
            "**Review outcome:** pending\n"
            "**If unanswered:** keep the proposal\n"
            "**Your review:** ______\n"
        )
        with_evidence = unanswered.replace(
            "**Review target:** pending",
            "**Resolution evidence:** `docs/cancel-a.md`\n"
            "**Review target:** pending",
        )
        self.assertIsNone(RECONCILE.queue_mutation_problem(
            path, path, unanswered, with_evidence
        ))
        answered = with_evidence.replace(
            "**Reviewed revision:** ______",
            f"**Reviewed revision:** sha256:{'a' * 64}",
        ).replace(
            "**Review revision:** pending",
            f"**Review revision:** sha256:{'a' * 64}",
        ).replace(
            "**Review outcome:** pending", "**Review outcome:** rejected"
        ).replace(
            "**Your review:** ______", "**Your review:** reject"
        )
        rebound = answered.replace(
            "`docs/cancel-a.md`", "`docs/cancel-b.md`"
        )
        problem = RECONCILE.queue_mutation_problem(
            path, path, answered, rebound
        )
        self.assertIn("after the first concrete response", problem)

    def test_timing_rename_cannot_rewrite_action_identity(self):
        for rewrites_action, rejected in ((False, False), (True, True)):
            with self.subTest(rewrites_action=rewrites_action), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                self.write(root, "docs/source.md", "# Source\n")
                source = self.write(
                    root,
                    "message-queue/needs-agent/requests/"
                    "non-blocking-repair.md",
                    "# Repair\n\n"
                    "**Status:** open\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** repair the source\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Resolution evidence:** `docs/source.md`\n"
                    "**If unanswered:** leave the source unchanged\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "file action")
                destination = source.with_name(
                    "future-blocking-repair.md"
                )
                source.rename(destination)
                text = destination.read_text(encoding="utf-8").replace(
                    "**If unanswered:** leave the source unchanged",
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** implementation may continue",
                )
                if rewrites_action:
                    text = text.replace(
                        "repair the source", "approve an unrelated release"
                    )
                destination.write_text(text, encoding="utf-8")
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))
                if rejected:
                    self.assertIn(
                        "action identity changed", findings[0].message
                    )

    def test_timing_cannot_weaken_or_move_with_a_human_response(self):
        cases = (
            (
                "future-blocking-question.md",
                "**Blocks at:** transition:merge\n"
                "**Until then:** implementation may continue\n"
                "**Your answer:** ______\n",
                "non-blocking-question.md",
                "**If unanswered:** keep the current behavior\n"
                "**Your answer:** ______\n",
                "weakened",
            ),
            (
                "non-blocking-question.md",
                "**If unanswered:** keep the current behavior\n"
                "**Your answer:** approve\n",
                "future-blocking-question.md",
                "**Blocks at:** transition:merge\n"
                "**Until then:** implementation may continue\n"
                "**Your answer:** approve\n",
                "human response",
            ),
        )
        for (
            source_name,
            source_timing,
            destination_name,
            destination_timing,
            expected,
        ) in cases:
            with self.subTest(expected=expected), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(
                    root,
                    "message-queue/needs-human/decisions/" + source_name,
                    "# Choose\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** choose the source disposition\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Resolution evidence:** `docs/source.md`\n"
                    + source_timing,
                )
                self.write(root, "docs/source.md", "# Source\n")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "file human action")

                destination = source.with_name(destination_name)
                source.rename(destination)
                destination.write_text(
                    destination.read_text(encoding="utf-8").replace(
                        source_timing, destination_timing
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(1, len(findings), self.messages(findings))
                self.assertIn(expected, findings[0].message)

    def test_claim_receipt_survives_later_timing_escalation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            source = self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-repair.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**If unanswered:** leave the source unchanged\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file action")
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim action")
            destination = source.with_name("blocking-repair.md")
            source.rename(destination)
            destination.write_text(
                destination.read_text(encoding="utf-8").replace(
                    "**If unanswered:** leave the source unchanged",
                    "**Blocks now:** operation:repair",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "reclassify action")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            destination.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_agent_claim_receipt_survives_later_slug_rename(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            source = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-original-name.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file action")
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim action")
            destination = source.with_name("blocking-clearer-name.md")
            source.rename(destination)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "clarify action name")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            destination.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_human_claim_receipt_survives_later_slug_rename(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Original\n")
            source = self.write(
                root,
                "message-queue/needs-human/decisions/"
                "blocking-original-name.md",
                "# Choose\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** choose the source disposition\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
                "**Your answer:** approve\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record answer")
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim answer")
            destination = source.with_name("blocking-clearer-name.md")
            source.rename(destination)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "clarify decision name")
            evidence.write_text("# Approved\n", encoding="utf-8")
            destination.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_slug_rename_claim_lineage_fails_closed_for_duplicate_actions(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            action = (
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
            )
            source = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-original-name.md",
                action,
            )
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-identical-action.md",
                action,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file duplicate actions")
            source.write_text(
                action.replace("**Status:** open", "**Status:** in-repair"),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim one action")
            destination = source.with_name("blocking-clearer-name.md")
            source.rename(destination)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "rename one action")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            destination.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                with self.assertRaisesRegex(
                    RECONCILE.GitSnapshotError,
                    "queue action lineage is ambiguous",
                ):
                    list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_new_identical_action_cannot_borrow_another_claim_receipt(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            open_action = (
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
            )
            claimed_action = open_action.replace(
                "**Status:** open", "**Status:** in-repair"
            )
            original = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-original-action.md",
                open_action,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file original action")
            original.write_text(claimed_action, encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim original action")
            copy = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-identical-copy.md",
                claimed_action,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add already claimed copy")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            copy.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("no committed one-line", findings[0].message)

    def test_merge_cannot_borrow_claim_from_other_parent_slug(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue")
            base = self.git(root, "rev-parse", "HEAD")
            open_action = (
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
            )
            claimed_action = open_action.replace(
                "**Status:** open", "**Status:** in-repair"
            )

            self.git(root, "checkout", "-b", "right")
            source = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-source-name.md",
                open_action,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file right action")
            source.write_text(claimed_action, encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim right action")

            self.git(root, "checkout", "-b", "left", base)
            destination = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-destination-name.md",
                claimed_action,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add preclaimed left action")
            self.git(root, "merge", "--no-ff", "--no-commit", "right")
            source = (
                root
                / "message-queue/needs-agent/requests/"
                "blocking-source-name.md"
            )
            source.unlink()
            evidence.write_text("# Folded right action\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "merge without right action")

            evidence.write_text("# Repaired destination\n", encoding="utf-8")
            destination.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("no committed one-line", findings[0].message)

    def test_merge_candidate_accepts_queue_state_from_second_parent(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Original\n")
            queue = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-repair-source.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file repair")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "resolved")
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim repair")
            evidence.write_text("# Repaired\n", encoding="utf-8")
            queue.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve repair")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            left = self.git(root, "rev-parse", "HEAD")
            self.git(root, "merge", "--no-ff", "--no-commit", "resolved")

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], staged, self.messages(staged))

            self.git(root, "commit", "-m", "merge resolved work")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{left}...{merged}"
                ):
                    committed = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], committed, self.messages(committed))

    def test_merge_candidate_rejects_dropped_second_parent_action(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "action")
            queue = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-second-parent-action.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the second-parent source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file second-parent action")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            left = self.git(root, "rev-parse", "HEAD")
            self.git(root, "merge", "--no-ff", "--no-commit", "action")
            queue.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(staged), self.messages(staged))
            self.assertIn("deleted unresolved", staged[0].message)

            self.git(root, "commit", "-m", "drop second-parent action")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{left}...{merged}"
                ):
                    committed = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(committed), self.messages(committed))
            self.assertIn("deleted unresolved", committed[0].message)

    def test_merge_candidate_rejects_dropped_first_parent_action(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "unrelated")
            self.write(root, "right.md", "# Right\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "right work")

            self.git(root, "checkout", trunk)
            queue = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-first-parent-action.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the first-parent source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file first-parent action")
            first = self.git(root, "rev-parse", "HEAD")
            self.git(root, "merge", "--no-ff", "--no-commit", "unrelated")
            queue.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(staged), self.messages(staged))
            self.assertIn("deleted unresolved", staged[0].message)

            self.git(root, "commit", "-m", "drop first-parent action")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{first}...{merged}"
                ):
                    committed = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(committed), self.messages(committed))
            self.assertIn("deleted unresolved", committed[0].message)

    def test_staged_merge_rechecks_invalid_side_queue_history(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            queue = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "blocking-unresolved-side-delete.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair before deletion\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file unresolved action")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "invalid-history")
            queue.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete without claim")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            self.git(
                root, "merge", "--no-ff", "--no-commit", "invalid-history"
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "deleted unresolved queue item" in finding.message
                or "deleted unresolved" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_staged_merge_cannot_restore_stale_parent_over_human_response(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            queue = self.write(
                root,
                "message-queue/needs-human/decisions/"
                "blocking-choice.md",
                "# Choice\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** choose the release\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
                "**Your answer:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file choice")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "stale")
            self.write(root, "right.md", "# Right\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "right work")

            self.git(root, "checkout", trunk)
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Your answer:** ______",
                    "**Your answer:** approve",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record answer")
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim answer")

            self.git(root, "merge", "--no-ff", "--no-commit", "stale")
            self.git(
                root,
                "restore",
                "--source=stale",
                "--staged",
                "--worktree",
                "--",
                str(queue.relative_to(root)),
            )
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "human response" in finding.message
                or "changed after" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_staged_merge_cannot_delete_concurrent_human_response(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Source\n")
            queue = self.write(
                root,
                "message-queue/needs-human/decisions/"
                "blocking-concurrent-choice.md",
                "# Choice\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** choose the release\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
                "**Your answer:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file concurrent choice")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "resolved-side")
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Your answer:** ______",
                    "**Your answer:** side-answer",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record side answer")
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim side answer")
            evidence.write_text("# Side resolution\n", encoding="utf-8")
            queue.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve side choice")

            self.git(root, "checkout", trunk)
            queue.write_text(
                queue.read_text(encoding="utf-8").replace(
                    "**Your answer:** ______",
                    "**Your answer:** first-answer",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record first answer")
            merge = subprocess.run(
                [
                    "git", "merge", "--no-ff", "--no-commit",
                    "resolved-side",
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertNotEqual(0, merge.returncode)
            self.git(root, "rm", str(queue.relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "human action was not committed as folding" in finding.message
                or "human response" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_staged_human_deletion_requires_folding_and_response(self):
        cases = (
            ("waiting", "______", True),
            ("folding", "approve", True),
        )
        for status, answer, rejected in cases:
            with self.subTest(status=status), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                path = (
                    "message-queue/needs-human/decisions/"
                    "blocking-choice.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Choose\n\n"
                    f"**Status:** {status}\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** choose\n"
                    "**Full context:** `message-queue/AGENTS.md`\n"
                    "**Blocks now:** transition:merge\n"
                    f"**Your answer:** {answer}\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add action")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_human_deletion_requires_claim_history_and_changed_evidence(self):
        for changes_evidence, rejected in ((False, True), (True, False)):
            with self.subTest(changes_evidence=changes_evidence), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(root, "docs/source.md", "# Original\n")
                path = (
                    "message-queue/needs-human/decisions/"
                    "blocking-choice.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Choose\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** choose\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Resolution evidence:** `docs/source.md`\n"
                    "**Blocks now:** transition:merge\n"
                    "**Your answer:** approve\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record answered action")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim answer")
                if changes_evidence:
                    source.write_text("# Folded answer\n", encoding="utf-8")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_staged_agent_deletion_requires_in_repair(self):
        for status, rejected in (("open", True), ("in-repair", True)):
            with self.subTest(status=status), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                item = self.write(
                    root,
                    "message-queue/needs-agent/requests/"
                    "blocking-repair.md",
                    "# Repair\n\n"
                    f"**Status:** {status}\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** repair\n"
                    "**Full context:** `message-queue/AGENTS.md`\n"
                    "**Blocks now:** transition:merge\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add action")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_agent_deletion_requires_claim_history_and_changed_evidence(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Broken\n")
            path = (
                "message-queue/needs-agent/requests/"
                "blocking-repair.md"
            )
            item = self.write(
                root,
                path,
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file repair")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim repair")
            source.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_deleted_review_response_must_match_requested_revision(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            item = self.write(
                root,
                "message-queue/needs-human/reviews/blocking-review.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** https://example.invalid/review\n"
                "**Review revision:** sha256:" + "a" * 64 + "\n"
                "**Reviewed revision:** sha256:" + "b" * 64 + "\n"
                "**Review outcome:** approved\n"
                "**Blocks now:** transition:merge\n"
                "**Your review:** approve\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record review")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim review")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("not bound", findings[0].message)

    def test_approved_review_revalidates_local_target_at_deletion(self):
        for changes_target, rejected in ((False, False), (True, True)):
            with self.subTest(changes_target=changes_target), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                path = (
                    "message-queue/needs-human/reviews/"
                    "non-blocking-review.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review exact bytes\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    "**Review outcome:** approved\n"
                    "**If unanswered:** leave the reviewed bytes unchanged\n"
                    "**Your review:** approve\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record approved review")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim review")
                if changes_target:
                    target.write_text("# Changed after review\n", encoding="utf-8")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_git_range_approval_satisfies_merge_only_for_queue_only_tail(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            source.write_text("# Reviewed change\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "reviewed implementation")
            reviewed_head = self.git(root, "rev-parse", "HEAD")
            binding = f"git:{base}...{reviewed_head}"
            path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review.md"
            )
            item = self.write(
                root,
                path,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the merge candidate\n"
                "**Full context:** `docs/source.md`\n"
                f"**Review target:** {binding}\n"
                f"**Review revision:** {binding}\n"
                f"**Reviewed revision:** {binding}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:merge task:2026-07-23-example\n"
                "**Until then:** implementation may continue\n"
                "**Your review:** approve\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record response")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim response")
            queue_only_head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.multiple(
                    RECONCILE,
                    ACTIVE_TRANSITIONS={"merge"},
                    ACTIVE_TASK_ID="2026-07-23-example",
                    CHANGE_RANGE=f"{base}...{queue_only_head}",
                ):
                    self.assertEqual(
                        [], list(RECONCILE.check_active_queue_boundaries())
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()

            source.write_text("# Changed after approval\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "unreviewed implementation")
            stale_head = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.multiple(
                    RECONCILE,
                    ACTIVE_TRANSITIONS={"merge"},
                    ACTIVE_TASK_ID="2026-07-23-example",
                    CHANGE_RANGE=f"{base}...{stale_head}",
                ):
                    findings = list(
                        RECONCILE.check_active_queue_boundaries()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn(
                "candidate changed outside queue lifecycle",
                findings[0].message,
            )
            self.assertIn("docs/source.md", findings[0].message)

    def test_blocking_git_range_review_cannot_delete_before_merge_receipt(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            source.write_text("# Reviewed\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "reviewed change")
            reviewed_head = self.git(root, "rev-parse", "HEAD")
            binding = f"git:{base}...{reviewed_head}"
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-review-range.md"
            )
            item = self.write(
                root,
                path,
                "# Review merge\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the exact merge range\n"
                f"**Full context:** {binding}\n"
                f"**Review target:** {binding}\n"
                f"**Review revision:** {binding}\n"
                f"**Reviewed revision:** {binding}\n"
                "**Review outcome:** approved\n"
                "**Blocks now:** transition:merge\n"
                "**Your review:** approve this range\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record blocking approval")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim blocking approval")
            source.write_text("# Unreviewed tail\n", encoding="utf-8")
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "add unreviewed tail")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "merge cleanup needs" in finding.message
                or "previously admitted target history" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_future_git_review_deletes_only_after_merge_carries_receipt(self):
        for merged, rejected in ((False, True), (True, False)):
            with self.subTest(merged=merged), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(root, "docs/source.md", "# Base\n")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "base")
                base = self.git(root, "rev-parse", "HEAD")
                source.write_text("# Reviewed change\n", encoding="utf-8")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "reviewed implementation")
                reviewed_head = self.git(root, "rev-parse", "HEAD")
                binding = f"git:{base}...{reviewed_head}"
                path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** approve the merge candidate\n"
                    "**Full context:** `docs/source.md`\n"
                    f"**Review target:** {binding}\n"
                    f"**Review revision:** {binding}\n"
                    f"**Reviewed revision:** {binding}\n"
                    "**Review outcome:** approved\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** implementation may continue\n"
                    "**Your review:** approve\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record response")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim response")
                feature = self.git(root, "rev-parse", "HEAD")
                if merged:
                    self.git(root, "checkout", "-b", "merge-receipt", base)
                    self.git(
                        root, "merge", "--no-ff", feature,
                        "-m", "carry approved receipt",
                    )
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings), self.messages(findings))
                if rejected:
                    self.assertIn(
                        "previously admitted target history",
                        findings[0].message,
                    )

    def test_historical_future_review_cannot_delete_as_blocking(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            source.write_text("# Reviewed change\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "reviewed implementation")
            reviewed_head = self.git(root, "rev-parse", "HEAD")
            binding = f"git:{base}...{reviewed_head}"
            item = self.write(
                root,
                "message-queue/needs-human/reviews/"
                "future-blocking-review.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the merge candidate\n"
                "**Full context:** `docs/source.md`\n"
                f"**Review target:** {binding}\n"
                f"**Review revision:** {binding}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks at:** transition:merge\n"
                "**Until then:** implementation may continue\n"
                "**Your review:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file future review")

            blocking = item.with_name("blocking-review.md")
            item.rename(blocking)
            blocking.write_text(
                blocking.read_text(encoding="utf-8").replace(
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** implementation may continue",
                    "**Blocks now:** transition:merge",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "escalate review")
            blocking.write_text(
                blocking.read_text(encoding="utf-8").replace(
                    "**Reviewed revision:** ______",
                    f"**Reviewed revision:** {binding}",
                ).replace(
                    "**Review outcome:** pending",
                    "**Review outcome:** approved",
                ).replace(
                    "**Your review:** ______",
                    "**Your review:** approve",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record response")
            blocking.write_text(
                blocking.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "claim response")
            blocking.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn(
                "previously admitted target history", findings[0].message
            )

    def test_merge_receipt_must_predate_the_admission_candidate(self):
        for receipt_in_base, rejected in ((False, True), (True, False)):
            with self.subTest(receipt_in_base=receipt_in_base), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(root, "docs/source.md", "# Base\n")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "base")
                base = self.git(root, "rev-parse", "HEAD")
                source.write_text("# Reviewed change\n", encoding="utf-8")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "reviewed implementation")
                reviewed_head = self.git(root, "rev-parse", "HEAD")
                binding = f"git:{base}...{reviewed_head}"
                path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** approve the merge candidate\n"
                    "**Full context:** `docs/source.md`\n"
                    f"**Review target:** {binding}\n"
                    f"**Review revision:** {binding}\n"
                    f"**Reviewed revision:** {binding}\n"
                    "**Review outcome:** approved\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** implementation may continue\n"
                    "**Your review:** approve\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record response")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim response")
                feature = self.git(root, "rev-parse", "HEAD")
                self.git(root, "checkout", "-b", "target", base)
                self.git(
                    root, "merge", "--no-ff", feature,
                    "-m", "carry approved receipt",
                )
                receipt_merge = self.git(root, "rev-parse", "HEAD")
                admitted_base = receipt_merge if receipt_in_base else base
                if not receipt_in_base:
                    self.git(root, "checkout", "-b", "candidate")
                item.unlink()
                self.git(root, "add", "-A")
                self.git(root, "commit", "-m", "clean up receipt")
                candidate = self.git(root, "rev-parse", "HEAD")

                RECONCILE.start_git_snapshot_cache()
                try:
                    with mock.patch.object(
                        RECONCILE,
                        "CHANGE_RANGE",
                        f"{admitted_base}...{candidate}",
                    ):
                        findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(
                    rejected, bool(findings), self.messages(findings)
                )
                if rejected:
                    self.assertIn(
                        "previously admitted target history",
                        findings[-1].message,
                    )

    def test_not_approved_review_requires_same_boundary_agent_successor(self):
        for creates_successor, rejected in ((False, True), (True, False)):
            with self.subTest(creates_successor=creates_successor), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                old_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                successor_path = (
                    "message-queue/needs-agent/requests/"
                    "future-blocking-repair-review.md"
                )
                followup_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review-repaired-artifact.md"
                )
                item = self.write(
                    root,
                    old_path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review exact bytes\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    "**Review outcome:** not-approved\n"
                    f"**Successor action:** `{successor_path}`\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** revise the artifact\n"
                    "**Your review:** request changes\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record requested changes")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", old_path)
                self.git(root, "commit", "-m", "claim review")
                if creates_successor:
                    self.write(
                        root,
                        successor_path,
                        "# Repair the reviewed artifact\n\n"
                        "**Status:** open\n"
                        "**Filed:** 2026-07-23\n"
                        "**Action:** repair the exact bytes requested by review\n"
                        "**Full context:** `docs/source.md`\n"
                        "**Resolution evidence:** `docs/source.md`\n"
                        f"**Supersedes:** `{old_path}`\n"
                        f"**Follow-up review:** `{followup_path}`\n"
                        "**Blocks at:** transition:merge\n"
                        "**Until then:** revise the artifact\n"
                        "\n## What you need to know\n\n"
                        "The review requested a concrete repair.\n\n"
                        "## Done when\n\nThe reviewed bytes are repaired.\n",
                    )
                    self.write(
                        root,
                        followup_path,
                        "# Review repaired artifact\n\n"
                        "**Status:** awaiting-artifact\n"
                        "**Filed:** 2026-07-23\n"
                        "**Action:** review the repaired artifact\n"
                        "**Full context:** `docs/source.md`\n"
                        "**Review target:** pending\n"
                        "**Review revision:** pending\n"
                        "**Reviewed revision:** ______\n"
                        "**Review outcome:** pending\n"
                        f"**Supersedes:** `{old_path}`\n"
                        f"**Depends on:** `{successor_path}`\n"
                        "**Blocks at:** transition:merge\n"
                        "**Until then:** revise the artifact\n"
                        "**Your review:** ______\n",
                    )
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_not_approved_review_rejects_preexisting_unrelated_successor(self):
        for preexisting, expected in (
            (True, "not introduced"),
            (False, "Full context"),
        ):
            with self.subTest(preexisting=preexisting), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(
                    root, "docs/security.md", "# Security\n"
                )
                self.write(root, "docs/logging.md", "# Logging\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                old_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-security.md"
                )
                successor_path = (
                    "message-queue/needs-agent/requests/"
                    "future-blocking-logging.md"
                )
                old = self.write(
                    root,
                    old_path,
                    "# Review security\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review the security design\n"
                    "**Full context:** `docs/security.md`\n"
                    "**Review target:** `docs/security.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    "**Review outcome:** not-approved\n"
                    f"**Successor action:** `{successor_path}`\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** continue implementation\n"
                    "**Your review:** request security changes\n",
                )

                def write_successor():
                    self.write(
                        root,
                        successor_path,
                        "# Repair unrelated logging\n\n"
                        "**Status:** open\n"
                        "**Filed:** 2026-07-23\n"
                        "**Action:** repair an unrelated logging design\n"
                        "**Full context:** `docs/logging.md`\n"
                        "**Resolution evidence:** `docs/logging.md`\n"
                        f"**Supersedes:** `{old_path}`\n"
                        "**Blocks at:** transition:merge\n"
                        "**Until then:** continue implementation\n"
                    )

                if preexisting:
                    write_successor()
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record reviews")
                old.write_text(
                    old.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", old_path)
                self.git(root, "commit", "-m", "claim rejected review")
                if not preexisting:
                    write_successor()
                old.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(1, len(findings))
                self.assertIn(expected, findings[0].message)

    def test_changes_requested_rejects_human_only_successor(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            old_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review.md"
            )
            successor_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-revision-two.md"
            )
            old = self.write(
                root,
                old_path,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review exact bytes\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** changes-requested\n"
                f"**Successor action:** `{successor_path}`\n"
                "**Blocks at:** transition:merge\n"
                "**Until then:** revise the artifact\n"
                "**Your review:** repair the boundary handling\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record requested changes")
            old.write_text(
                old.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", old_path)
            self.git(root, "commit", "-m", "claim review response")
            self.write(
                root,
                successor_path,
                "# Review revision two\n\n"
                "**Status:** awaiting-artifact\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review revised bytes\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                f"**Supersedes:** `{old_path}`\n"
                "**Blocks at:** transition:merge\n"
                "**Until then:** revise the artifact\n"
                "**Your review:** ______\n",
            )
            old.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("needs-agent", findings[0].message)

    def test_changes_requested_agent_successor_preserves_action_contract(self):
        cases = (
            ("valid", "open", "repair the reviewed bytes",
             "**Resolution evidence:** `docs/source.md`\n",
             "transition:merge", None),
            ("unclaimed", "in-repair", "repair the reviewed bytes",
             "**Resolution evidence:** `docs/source.md`\n",
             "transition:merge", "open needs-agent"),
            ("missing-action", "open", "",
             "**Resolution evidence:** `docs/source.md`\n",
             "transition:merge", "concrete **Action:**"),
            ("missing-evidence", "open", "repair the reviewed bytes", "",
             "transition:merge", "**Resolution evidence:**"),
            ("wrong-boundary", "open", "repair the reviewed bytes",
             "**Resolution evidence:** `docs/source.md`\n",
             "transition:publish", "**Blocks at:**"),
        )
        for (
            name,
            status,
            action,
            evidence,
            boundary,
            expected,
        ) in cases:
            with self.subTest(name=name), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                old_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                successor_path = (
                    "message-queue/needs-agent/requests/"
                    "future-blocking-repair-review.md"
                )
                followup_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review-repaired-artifact.md"
                )
                old = self.write(
                    root,
                    old_path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review exact bytes\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    "**Review outcome:** changes-requested\n"
                    f"**Successor action:** `{successor_path}`\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** revise the artifact\n"
                    "**Your review:** repair the reviewed bytes\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record requested changes")
                old.write_text(
                    old.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", old_path)
                self.git(root, "commit", "-m", "claim review response")
                self.write(
                    root,
                    successor_path,
                    "# Repair reviewed bytes\n\n"
                    f"**Status:** {status}\n"
                    "**Filed:** 2026-07-23\n"
                    f"**Action:** {action}\n"
                    "**Full context:** `docs/source.md`\n"
                    f"{evidence}"
                    f"**Supersedes:** `{old_path}`\n"
                    f"**Follow-up review:** `{followup_path}`\n"
                    f"**Blocks at:** {boundary}\n"
                    "**Until then:** revise the artifact\n",
                )
                self.write(
                    root,
                    followup_path,
                    "# Review repaired artifact\n\n"
                    "**Status:** awaiting-artifact\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review the repaired artifact\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** pending\n"
                    "**Review revision:** pending\n"
                    "**Reviewed revision:** ______\n"
                    "**Review outcome:** pending\n"
                    f"**Supersedes:** `{old_path}`\n"
                    f"**Depends on:** `{successor_path}`\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** revise the artifact\n"
                    "**Your review:** ______\n",
                )
                old.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                if expected is None:
                    self.assertEqual([], findings, self.messages(findings))
                else:
                    self.assertEqual(
                        1, len(findings), self.messages(findings)
                    )
                    self.assertIn(expected, findings[0].message)

    def test_changes_requested_requires_distinct_followup_review(self):
        for mode, rejected in (
            ("valid", False),
            ("missing", True),
            ("duplicate", True),
        ):
            with self.subTest(mode=mode), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                old_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                repair_path = (
                    "message-queue/needs-agent/requests/"
                    "future-blocking-repair-review.md"
                )
                followup_path = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review-repaired-artifact.md"
                )
                old = self.write(
                    root,
                    old_path,
                    "# Review\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review exact bytes\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    "**Review outcome:** changes-requested\n"
                    f"**Successor action:** `{repair_path}`\n"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** revise the artifact\n"
                    "**Your review:** repair the reviewed bytes\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record requested changes")
                old.write_text(
                    old.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", old_path)
                self.git(root, "commit", "-m", "claim review response")
                repair_action = "repair the reviewed bytes"
                followup_field = (
                    ""
                    if mode == "missing"
                    else f"**Follow-up review:** `{followup_path}`\n"
                )
                self.write(
                    root,
                    repair_path,
                    "# Repair reviewed bytes\n\n"
                    "**Status:** open\n"
                    "**Filed:** 2026-07-23\n"
                    f"**Action:** {repair_action}\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Resolution evidence:** `docs/source.md`\n"
                    f"**Supersedes:** `{old_path}`\n"
                    f"{followup_field}"
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** revise the artifact\n",
                )
                followup_action = (
                    repair_action
                    if mode == "duplicate"
                    else "review the repaired artifact"
                )
                if mode != "missing":
                    self.write(
                        root,
                        followup_path,
                        "# Review repaired artifact\n\n"
                        "**Status:** awaiting-artifact\n"
                        "**Filed:** 2026-07-23\n"
                        f"**Action:** {followup_action}\n"
                        "**Full context:** `docs/source.md`\n"
                        "**Why-you-might-care:** The repair still needs judgment.\n"
                        "**If-you-do-nothing:** The merge boundary stays closed.\n"
                        "**Review target:** pending\n"
                        "**Review revision:** pending\n"
                        "**Reviewed revision:** ______\n"
                        "**Review outcome:** pending\n"
                        f"**Supersedes:** `{old_path}`\n"
                        f"**Depends on:** `{repair_path}`\n"
                        "**Blocks at:** transition:merge\n"
                        "**Until then:** revise the artifact\n"
                        "**Your review:** ______\n",
                    )
                old.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(
                    rejected, bool(findings), self.messages(findings)
                )
                if rejected:
                    expected = (
                        "preserve the review boundary"
                        if mode == "missing"
                        else "duplicates"
                    )
                    self.assertIn(expected, findings[0].message)

    def test_negative_merge_reviews_close_only_after_candidate_withdrawal(self):
        for outcome in ("rejected", "abandoned"):
            with self.subTest(outcome=outcome), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(root, "docs/source.md", "# Base\n")
                cancellation = self.write(
                    root, "docs/cancellation.md", "# Pursuit active\n"
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "base")
                base = self.git(root, "rev-parse", "HEAD")
                source.write_text("# Candidate\n", encoding="utf-8")
                self.git(root, "add", "docs/source.md")
                self.git(root, "commit", "-m", "candidate")
                head = self.git(root, "rev-parse", "HEAD")
                target = f"git:{base}...{head}"
                path = (
                    "message-queue/needs-human/reviews/"
                    f"blocking-{outcome}.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Review proposal\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** decide whether this proposal continues\n"
                    "**Full context:** `message-queue/AGENTS.md`\n"
                    "**Resolution evidence:** `docs/cancellation.md`\n"
                    "**Why-you-might-care:** The outcome controls the proposal.\n"
                    "**If-you-do-nothing:** The merge boundary remains pending.\n"
                    f"**Review target:** {target}\n"
                    f"**Review revision:** {target}\n"
                    f"**Reviewed revision:** {target}\n"
                    f"**Review outcome:** {outcome}\n"
                    "**Blocks now:** transition:merge\n\n"
                    "## What you need to know\n\nJudge one exact proposal.\n\n"
                    "## Differences\n\nReject ends it; changes request revision.\n\n"
                    "## Example\n\nA rejected proposal creates no revision two.\n\n"
                    f"**Your review:** {outcome}\n",
                )
                self.git(root, "add", ".")
                schema_findings = list(RECONCILE.check_queue_schema())
                self.assertEqual(
                    [], schema_findings, self.messages(schema_findings)
                )
                self.git(root, "commit", "-m", f"record {outcome} outcome")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim terminal response")
                cancellation.write_text(
                    f"# Pursuit {outcome}\n", encoding="utf-8"
                )
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertTrue(any(
                    "reviewed proposal remains active" in finding.message
                    for finding in findings
                ), self.messages(findings))

                source.write_text("# Base\n", encoding="utf-8")
                self.git(root, "add", "docs/source.md")
                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual([], findings, self.messages(findings))

    def test_review_cleanup_enforces_target_kind_at_the_named_boundary(self):
        local_text = self.terminal_local_review(
            "docs/source.md",
            "sha256:" + "a" * 64,
            "approved",
            "**Blocks at:** transition:merge",
            status="folding",
        )
        problem = RECONCILE.review_cleanup_boundary_problem(
            "message-queue/needs-human/reviews/"
            "future-blocking-local-merge.md",
            local_text,
            "a" * 40,
            None,
            local_text,
            "future-blocking",
        )
        self.assertIn("candidate-range Git", problem)

        git_revision = f"git:{'a' * 40}...{'b' * 40}"
        git_text = (
            "# Review\n\n"
            "**Status:** folding\n"
            "**Review target:** " + git_revision + "\n"
            "**Review revision:** " + git_revision + "\n"
            "**Reviewed revision:** " + git_revision + "\n"
            "**Review outcome:** approved\n"
            "**Blocks at:** transition:start task:2026-07-23-example\n"
            "**Your review:** approved\n"
        )
        problem = RECONCILE.review_cleanup_boundary_problem(
            "message-queue/needs-human/reviews/"
            "future-blocking-git-task.md",
            git_text,
            "a" * 40,
            None,
            git_text,
            "future-blocking",
        )
        self.assertIn("stable local review target", problem)

    def test_event_and_custom_transition_approvals_close_with_fresh_evidence(self):
        for slug, boundary in (
            ("publication", "event:publication"),
            ("deployment", "transition:deploy"),
        ):
            with self.subTest(boundary=boundary), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                evidence = self.write(
                    root, "docs/review-disposition.md", "# Pending\n"
                )
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                path = (
                    "message-queue/needs-human/reviews/"
                    f"future-blocking-{slug}.md"
                )
                item = self.write(
                    root,
                    path,
                    self.terminal_local_review(
                        "docs/source.md",
                        digest,
                        "approved",
                        f"**Blocks at:** {boundary}",
                    ),
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record approved review")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim approved review")
                evidence.write_text("# Boundary acknowledged\n", encoding="utf-8")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual([], findings, self.messages(findings))

    def test_nonblocking_negative_local_review_requires_target_withdrawal(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            evidence = self.write(
                root, "docs/review-disposition.md", "# Pending\n"
            )
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "non-blocking-local-rejection.md"
            )
            item = self.write(
                root,
                path,
                self.terminal_local_review(
                    "docs/source.md",
                    digest,
                    "rejected",
                    "**If unanswered:** keep the reviewed pursuit unchanged",
                ),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record rejected review")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim rejected review")
            evidence.write_text("# Rejected\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "target remains unchanged and active" in finding.message
                for finding in findings
            ), self.messages(findings))

            target.write_text("# Withdrawn\n", encoding="utf-8")
            self.git(root, "add", "docs/source.md")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_historical_negative_cleanup_rejects_later_reintroduction(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            evidence = self.write(
                root, "docs/review-disposition.md", "# Pending\n"
            )
            original = target.read_text(encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "non-blocking-local-rejection.md"
            )
            item = self.write(
                root,
                path,
                self.terminal_local_review(
                    "docs/source.md",
                    digest,
                    "rejected",
                    "**If unanswered:** keep the reviewed pursuit unchanged",
                ),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record rejected review")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim rejected review")
            target.write_text("# Withdrawn\n", encoding="utf-8")
            evidence.write_text("# Rejected\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "withdraw rejected pursuit")
            target.write_text(original, encoding="utf-8")
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "reintroduce rejected pursuit")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "target remains unchanged and active" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_later_candidates_exclude_parallel_pre_deletion_snapshots(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "-b", "cleanup")
            self.write(root, "docs/cleanup.md", "# Cleanup\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "cleanup")
            deletion = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "-b", "parallel", base)
            self.write(root, "docs/parallel.md", "# Parallel\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "parallel")
            parallel = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "cleanup")
            self.git(
                root, "merge", "--no-ff", "parallel",
                "-m", "join parallel work",
            )
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                candidates = RECONCILE.deletion_and_later_candidates(
                    deletion
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(deletion, candidates[0])
            self.assertIn(head, candidates)
            self.assertNotIn(parallel, candidates)

    def test_bare_task_review_cleanup_requires_evidence_or_withdrawal(self):
        task_id = "2026-07-23-example"
        for outcome in ("approved", "rejected"):
            with self.subTest(outcome=outcome), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                evidence = self.write(
                    root, "docs/review-disposition.md", "# Pending\n"
                )
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                path = (
                    "message-queue/needs-human/reviews/"
                    f"blocking-bare-task-{outcome}.md"
                )
                item = self.write(
                    root,
                    path,
                    self.terminal_local_review(
                        "docs/source.md",
                        digest,
                        outcome,
                        f"**Blocks now:** task:{task_id}",
                    ),
                )
                task = self.make_task(root, "0_backlog", f"`{path}`")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", f"record {outcome} review")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", f"claim {outcome} review")
                evidence.write_text(f"# {outcome}\n", encoding="utf-8")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                if outcome == "approved":
                    self.assertEqual([], findings, self.messages(findings))
                else:
                    self.assertTrue(any(
                        "rejected task pursuit remains live"
                        in finding.message for finding in findings
                    ), self.messages(findings))
                    for artifact in sorted(
                        task.rglob("*"), reverse=True
                    ):
                        if artifact.is_file():
                            artifact.unlink()
                        else:
                            artifact.rmdir()
                    task.rmdir()
                    self.git(root, "add", "-A")
                    RECONCILE.start_git_snapshot_cache()
                    try:
                        findings = list(RECONCILE.check_queue_resolution())
                    finally:
                        RECONCILE.stop_git_snapshot_cache()
                    self.assertEqual([], findings, self.messages(findings))

    def test_task_receipt_survives_same_timing_slug_rename(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            self.write(root, "docs/review-disposition.md", "# Pending\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            old_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-original-start.md"
            )
            new_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-clearer-start.md"
            )
            review = self.write(
                root,
                old_path,
                self.terminal_local_review(
                    "docs/source.md",
                    digest,
                    "approved",
                    "**Blocks at:** transition:start "
                    "task:2026-07-23-example",
                ),
            )
            task = self.make_task(root, "0_backlog", f"`{old_path}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record start approval")
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", old_path)
            self.git(root, "commit", "-m", "claim start approval")

            active = root / "tasks/1_in-progress/2026-07-23-example"
            active.parent.mkdir(parents=True)
            task.rename(active)
            review.rename(root / new_path)
            task_record = active / "task.md"
            task_record.write_text(
                task_record.read_text(encoding="utf-8").replace(
                    old_path, new_path
                ),
                encoding="utf-8",
            )
            (active / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (active / "worklog.md").write_text("# Worklog\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "start task and clarify review name")

            task_record.write_text(
                task_record.read_text(encoding="utf-8").replace(
                    f"`{new_path}`", "none"
                ),
                encoding="utf-8",
            )
            (root / new_path).unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_merge_receipt_survives_same_timing_slug_rename(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Base\n")
            self.write(root, "docs/review-disposition.md", "# Pending\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            source.write_text("# Reviewed\n", encoding="utf-8")
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "reviewed change")
            reviewed_head = self.git(root, "rev-parse", "HEAD")
            binding = f"git:{base}...{reviewed_head}"
            old_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-original-merge.md"
            )
            new_path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-clearer-merge.md"
            )
            review = self.write(
                root,
                old_path,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the exact merge candidate\n"
                f"**Full context:** {binding}\n"
                "**Resolution evidence:** `docs/review-disposition.md`\n"
                f"**Review target:** {binding}\n"
                f"**Review revision:** {binding}\n"
                f"**Reviewed revision:** {binding}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:merge\n"
                "**Until then:** keep the candidate unmerged\n"
                "**Your review:** approved\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record merge approval")
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", old_path)
            self.git(root, "commit", "-m", "claim merge approval")
            review.rename(root / new_path)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "clarify merge review name")
            feature = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "target", base)
            self.git(
                root, "merge", "--no-ff", feature,
                "-m", "carry renamed merge receipt",
            )
            (root / new_path).unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_approved_date_review_closes_at_boundary_with_evidence(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            evidence = self.write(
                root, "docs/boundary.md", "# Before boundary\n"
            )
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            path = (
                "message-queue/needs-human/reviews/"
                "future-blocking-date.md"
            )
            item = self.write(
                root,
                path,
                "# Date review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the dated release\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/boundary.md`\n"
                "**Why-you-might-care:** The date controls release.\n"
                "**If-you-do-nothing:** The release remains blocked.\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** 2026-07-23\n"
                "**Until then:** wait for the release date\n\n"
                "## What you need to know\n\nJudge the dated release.\n\n"
                "## Differences\n\nApproval crosses; changes revise.\n\n"
                "## Example\n\nThe item survives until its date.\n\n"
                "**Your review:** approved\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record dated approval")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim dated approval")
            evidence.write_text("# Boundary crossed\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_blocking_review_cannot_disappear_without_boundary_evidence(self):
        for outcome in ("approved", "rejected", "abandoned"):
            with self.subTest(outcome=outcome), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                path = (
                    "message-queue/needs-human/reviews/"
                    f"blocking-{outcome}.md"
                )
                item = self.write(
                    root,
                    path,
                    "# Review proposal\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** decide whether this proposal continues\n"
                    "**Full context:** `message-queue/AGENTS.md`\n"
                    "**Why-you-might-care:** The outcome controls the proposal.\n"
                    "**If-you-do-nothing:** The merge boundary remains pending.\n"
                    "**Review target:** https://example.invalid/proposal\n"
                    f"**Review revision:** sha256:{'a' * 64}\n"
                    f"**Reviewed revision:** sha256:{'a' * 64}\n"
                    f"**Review outcome:** {outcome}\n"
                    "**Blocks now:** transition:merge\n"
                    f"**Your review:** {outcome}\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", f"record {outcome} outcome")
                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        "**Status:** waiting", "**Status:** folding"
                    ),
                    encoding="utf-8",
                )
                self.git(root, "add", path)
                self.git(root, "commit", "-m", "claim terminal response")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(1, len(findings), self.messages(findings))
                expected = (
                    "merge cleanup needs"
                    if outcome == "approved"
                    else "cancellation evidence"
                )
                self.assertIn(expected, findings[0].message)

    def test_terminal_review_outcomes_reject_successor_fields(self):
        for outcome in ("approved", "rejected", "abandoned"):
            with self.subTest(outcome=outcome), self.repo() as root:
                target = self.write(root, "docs/source.md", "# Reviewed\n")
                digest = "sha256:" + hashlib.sha256(
                    target.read_bytes()
                ).hexdigest()
                successor = (
                    "message-queue/needs-human/reviews/"
                    "blocking-unrelated-successor.md"
                )
                self.write(
                    root,
                    "message-queue/needs-human/reviews/"
                    f"blocking-{outcome}-with-successor.md",
                    "# Review proposal\n\n"
                    "**Status:** waiting\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** review the proposal\n"
                    "**Full context:** `docs/source.md`\n"
                    "**Review target:** `docs/source.md`\n"
                    f"**Review revision:** {digest}\n"
                    f"**Reviewed revision:** {digest}\n"
                    f"**Review outcome:** {outcome}\n"
                    f"**Successor action:** `{successor}`\n"
                    "**Blocks now:** operation:publish\n\n"
                    "## What you need to know\n\nReview one proposal.\n\n"
                    "## Differences\n\nA terminal result closes this action.\n\n"
                    "## Example\n\nApproval accepts these exact bytes.\n\n"
                    f"**Your review:** {outcome}\n",
                )

                messages = self.messages(RECONCILE.check_queue_schema())
                self.assertTrue(any(
                    outcome in message and "Successor action" in message
                    for message in messages
                ), messages)

    def test_range_rejects_approved_review_with_successor(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-approved-with-successor.md"
            )
            successor = (
                "message-queue/needs-human/reviews/"
                "blocking-unrelated-successor.md"
            )
            item = self.write(
                root,
                path,
                "# Review proposal\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the proposal\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** https://example.invalid/proposal\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                f"**Reviewed revision:** sha256:{'a' * 64}\n"
                "**Review outcome:** approved\n"
                f"**Successor action:** `{successor}`\n"
                "**Blocks now:** operation:publish\n"
                "**Your review:** approve\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record approved response")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim approved response")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve approved response")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("approved review is terminal", findings[0].message)

    def test_synthetic_merge_rejects_approved_review_with_successor(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-approved-merge.md"
            )
            successor = (
                "message-queue/needs-human/reviews/"
                "blocking-unrelated-successor.md"
            )
            item = self.write(
                root,
                path,
                "# Review proposal\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the proposal\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** https://example.invalid/proposal\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                f"**Reviewed revision:** sha256:{'a' * 64}\n"
                "**Review outcome:** approved\n"
                f"**Successor action:** `{successor}`\n"
                "**Blocks now:** operation:publish\n"
                "**Your review:** approve\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record approved response")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim approved response")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(root, "base.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "advance base")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", "--no-commit", trunk)
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "approved review is terminal" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_changes_requested_outcome_requires_successor(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/reviews/"
                "blocking-changes-requested.md"
            )
            item = self.write(
                root,
                path,
                "# Review proposal\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the proposal\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** https://example.invalid/proposal\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                f"**Reviewed revision:** sha256:{'a' * 64}\n"
                "**Review outcome:** changes-requested\n"
                "**Blocks now:** transition:merge\n"
                "**Your review:** revise it\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record requested changes")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim response")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("Successor action", findings[0].message)

    def test_generated_retry_gc_exception_rejects_manual_lookalike(self):
        for generated, rejected in ((True, False), (False, True)):
            with self.subTest(generated=generated), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                finding = RECONCILE.Finding(
                    "queue-name", Path("docs/source.md"), "broken", "fix"
                )
                path = (
                    "message-queue/needs-agent/retries/"
                    f"blocking-{RECONCILE.finding_key(finding)}.md"
                )
                text = (
                    RECONCILE.retry_text(finding)
                    if generated
                    else (
                        "# Manual retry\n\n"
                        "**Status:** open\n"
                        "**Filed:** 2026-07-23, by agent\n"
                        "**Check:** queue-name\n"
                        "**Subject:** `docs/source.md`\n"
                        "**Action:** fix it\n"
                        "**Blocks now:** transition:merge\n"
                    )
                )
                item = self.write(root, path, text)
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add retry")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_generated_retry_deletes_only_after_named_finding_clears(self):
        for clears_finding, rejected in ((False, True), (True, False)):
            with self.subTest(clears_finding=clears_finding), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                subject = Path(
                    "message-queue/needs-agent/requests/bad.md"
                )
                broken = self.write(root, subject.as_posix(), "# Bad name\n")
                finding = RECONCILE.Finding(
                    "queue-name", subject, "bad name", "rename it"
                )
                retry_path = (
                    "message-queue/needs-agent/retries/"
                    f"blocking-{RECONCILE.finding_key(finding)}.md"
                )
                retry = self.write(
                    root, retry_path, RECONCILE.retry_text(finding)
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "file generated retry")
                if clears_finding:
                    repaired = broken.with_name("blocking-bad.md")
                    broken.rename(repaired)
                retry.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_range_generated_retry_must_be_clear_at_deletion_commit(self):
        for fixes_at_deletion, rejected in ((False, True), (True, False)):
            with self.subTest(
                fixes_at_deletion=fixes_at_deletion
            ), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "activate resolution gate")
                base = self.git(root, "rev-parse", "HEAD")
                subject = Path(
                    "message-queue/needs-agent/requests/bad.md"
                )
                broken = self.write(
                    root, subject.as_posix(), "# Bad name\n"
                )
                finding = RECONCILE.Finding(
                    "queue-name", subject, "bad name", "rename it"
                )
                retry = self.write(
                    root,
                    "message-queue/needs-agent/retries/"
                    f"blocking-{RECONCILE.finding_key(finding)}.md",
                    RECONCILE.retry_text(finding),
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "file generated retry")
                retry.unlink()
                if fixes_at_deletion:
                    broken.rename(broken.with_name("blocking-bad.md"))
                self.git(root, "add", "-A")
                self.git(root, "commit", "-m", "delete generated retry")
                if not fixes_at_deletion:
                    broken.rename(broken.with_name("blocking-bad.md"))
                    self.git(root, "add", "-A")
                    self.git(root, "commit", "-m", "fix finding later")
                head = self.git(root, "rev-parse", "HEAD")

                RECONCILE.start_git_snapshot_cache()
                try:
                    with mock.patch.object(
                        RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                    ):
                        findings = list(
                            RECONCILE.check_queue_resolution()
                        )
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))
                if rejected:
                    self.assertIn("not cleared", findings[0].message)

    def test_open_pickup_deletion_requires_atomic_claim_and_move(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md"
            )
            item = self.write(
                root,
                queue_rel,
                "# Pick up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** claim the task\n"
                "**Full context:** "
                "`tasks/0_backlog/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n"
                "**If unanswered:** leave it in backlog\n",
            )
            task = self.make_task(root, "0_backlog", f"`{queue_rel}`")
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Claimed-by:** test", "**Claimed-by:** unclaimed"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add pickup")

            destination = root / "tasks/1_in-progress/2026-07-23-example"
            destination.parent.mkdir(parents=True)
            task.rename(destination)
            (destination / "task.md").write_text(
                (destination / "task.md").read_text(encoding="utf-8")
                .replace("**Claimed-by:** unclaimed", "**Claimed-by:** agent")
                .replace(f"**Queue actions:** `{queue_rel}`",
                         "**Queue actions:** none"),
                encoding="utf-8",
            )
            (destination / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (destination / "worklog.md").write_text(
                "# Worklog\n", encoding="utf-8"
            )
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_in_repair_pickup_cannot_bypass_atomic_claim_check(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            item = self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md",
                "# Pick up\n\n"
                "**Status:** in-repair\n"
                "**Full context:** "
                "`tasks/0_backlog/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n",
            )
            self.make_task(root, "0_backlog", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add pickup")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("not atomically claimed", findings[0].message)

    def test_posthoc_pickup_for_in_progress_task_is_not_atomic(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "task already claimed")
            path = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md"
            )
            item = self.write(
                root,
                path,
                "# Pick up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** claim the task\n"
                "**Full context:** "
                "`tasks/0_backlog/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n"
                "**If unanswered:** leave it in backlog\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add posthoc pickup")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("not atomically claimed", findings[0].message)

    def test_resolution_gate_cannot_be_disabled_with_its_marker(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-repair.md",
                "# Repair\n\n**Status:** open\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue resolution")
            contract.write_text(
                "**Queue resolution schema:** v0\n", encoding="utf-8"
            )
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            messages = self.messages(findings)
            self.assertTrue(any("removed after activation" in m for m in messages))
            self.assertTrue(any("deleted unresolved" in m for m in messages))

    def test_resolution_gate_no_ops_after_whole_queue_service_removal(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue resolution")
            base = self.git(root, "rev-parse", "HEAD")
            contract.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "remove queue service")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_whole_queue_service_removal_rejects_live_actions(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            blocking = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-live.md",
                "# Blocking action\n\n**Status:** open\n",
            )
            nonblocking = self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-live.md",
                "# Nonblocking action\n\n**Status:** open\n",
            )
            malformed = self.write(
                root,
                "message-queue/question.md",
                "# Malformed live action\n\n**Status:** waiting\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue with live actions")
            base = self.git(root, "rev-parse", "HEAD")
            contract.unlink()
            blocking.unlink()
            nonblocking.unlink()
            malformed.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(
                {
                    blocking.relative_to(root),
                    nonblocking.relative_to(root),
                    malformed.relative_to(root),
                },
                {finding.subject for finding in staged},
            )
            self.assertFalse(any(
                "removed after activation" in finding.message
                for finding in staged
            ))

            self.git(root, "commit", "-m", "remove queue with live actions")
            head = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    ranged = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(
                {
                    blocking.relative_to(root),
                    nonblocking.relative_to(root),
                    malformed.relative_to(root),
                },
                {finding.subject for finding in ranged},
            )

    def test_unreadable_historical_queue_state_fails_closed(self):
        for kind in ("invalid-utf8", "symlink"):
            with self.subTest(kind=kind), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                item = (
                    root
                    / "message-queue/needs-agent/requests/blocking-bad.md"
                )
                item.parent.mkdir(parents=True)
                if kind == "invalid-utf8":
                    item.write_bytes(b"\xff\xfe")
                else:
                    item.symlink_to("missing-target")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add unreadable action")
                item.unlink()
                self.git(root, "add", "-A")

                stderr = io.StringIO()
                with mock.patch.dict(
                    RECONCILE.CHECKS,
                    {"queue-resolution": RECONCILE.check_queue_resolution},
                    clear=True,
                ), contextlib.redirect_stderr(stderr):
                    self.assertEqual(2, RECONCILE.main(["--check"]))
                self.assertIn("Git snapshot error", stderr.getvalue())

    def test_malformed_queue_path_remains_governed_until_repaired(self):
        paths = (
            "message-queue/question.md",
            "message-queue/wrong-actor/decisions/blocking-question.md",
            "message-queue/needs-human/decisions/question.md",
            "message-queue/needs-human/decisions/archive/blocking-question.md",
        )
        for path in paths:
            with self.subTest(path=path), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                item = self.write(
                    root,
                    path,
                    "# Question\n\n**Status:** waiting\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add malformed action")
                item.unlink()
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(1, len(findings))
                self.assertIn("deleted unresolved", findings[0].message)

    def test_action_shaped_reserved_basename_is_governed(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            item = self.write(
                root,
                "message-queue/needs-human/decisions/AGENTS.md",
                "# Pending decision\n\n"
                "**Status:** waiting\n"
                "**Your answer:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file misnamed action")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("deleted unresolved", findings[0].message)

    def test_extensible_typed_leaf_readme_is_documentation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            readme = self.write(
                root,
                "message-queue/needs-human/approvals/README.md",
                "# approvals/ — extension contract\n",
            )
            self.git(root, "add", ".")

            RECONCILE.start_git_snapshot_cache()
            try:
                items = {
                    item.relative_to(root)
                    for item in RECONCILE.live_queue_items()
                }
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertNotIn(readme.relative_to(root), items)

    def test_invalid_actor_cannot_resolve_as_agent_action(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "docs/source.md", "# Broken\n")
            path = (
                "message-queue/wrong-actor/decisions/"
                "blocking-question.md"
            )
            item = self.write(
                root,
                path,
                "# Human choice\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** ask the human to choose\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
                "**Your answer:** ______\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file malformed action")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim malformed action")
            evidence.write_text("# Changed without an answer\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("malformed queue actor", findings[0].message)

    def test_queue_rename_out_is_deletion_but_timing_rename_is_move(self):
        for destination, rejected in (
            (
                "message-queue/needs-agent/requests/"
                "non-blocking-repair.md",
                True,
            ),
            (
                "message-queue/needs-human/decisions/"
                "non-blocking-repair.md",
                True,
            ),
            ("docs/blocking-repair.md", True),
        ):
            with self.subTest(destination=destination), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "message-queue/AGENTS.md",
                    "**Queue resolution schema:** v1\n",
                )
                source = self.write(
                    root,
                    "message-queue/needs-agent/requests/"
                    "blocking-repair.md",
                    "# Repair\n\n**Status:** open\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "add action")
                target = root / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
                self.git(root, "add", "-A")

                RECONCILE.start_git_snapshot_cache()
                try:
                    findings = list(RECONCILE.check_queue_resolution())
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                self.assertEqual(rejected, bool(findings))

    def test_queue_move_cannot_change_next_actor(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(
                root,
                "message-queue/needs-human/custom/"
                "blocking-shared-action.md",
                "# Shared action\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the shared artifact\n"
                "**Full context:** `README.md`\n"
                "**Resolution evidence:** `README.md`\n"
                "**Blocks now:** operation:inspect\n",
            )
            self.write(root, "README.md", "# Context\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file human action")

            target = (
                root
                / "message-queue/needs-agent/custom/"
                "blocking-shared-action.md"
            )
            target.parent.mkdir(parents=True)
            source.rename(target)
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** open"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("action identity changed", findings[0].message)

    def test_queue_move_cannot_change_typed_leaf(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(
                root,
                "message-queue/needs-agent/custom-a/"
                "blocking-shared-action.md",
                "# Shared action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the shared artifact\n"
                "**Full context:** `README.md`\n"
                "**Resolution evidence:** `README.md`\n"
                "**Blocks now:** operation:inspect\n",
            )
            self.write(root, "README.md", "# Context\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file custom-a action")

            target = (
                root
                / "message-queue/needs-agent/custom-b/"
                "blocking-shared-action.md"
            )
            target.parent.mkdir(parents=True)
            source.rename(target)
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("action identity changed", findings[0].message)

    def test_queue_slug_rename_within_same_actor_and_leaf_passes(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(
                root,
                "message-queue/needs-agent/custom/"
                "blocking-original-name.md",
                "# Shared action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the shared artifact\n"
                "**Full context:** `README.md`\n"
                "**Resolution evidence:** `README.md`\n"
                "**Blocks now:** operation:inspect\n",
            )
            self.write(root, "README.md", "# Context\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file named action")

            source.rename(source.with_name("blocking-clearer-name.md"))
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_generic_human_agent_notes_fields_are_immutable(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            path = (
                "message-queue/needs-human/custom/"
                "blocking-context-review.md"
            )
            item = self.write(
                root,
                path,
                "# Review context\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the context\n"
                "**Full context:** `README.md`\n"
                "**Resolution evidence:** `README.md`\n"
                "**Blocks now:** operation:review\n"
                "**Your answer:** ______\n\n"
                "## Agent notes\n\n"
                "**Why-you-might-care:** Original production consequence.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            self.write(root, "README.md", "# Context\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file human context")

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "Original production consequence.",
                    "Rewritten production consequence.",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("action identity changed", findings[0].message)

    def test_malformed_name_can_be_normalized_without_resolving_action(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(
                root,
                "message-queue/needs-human/decisions/question.md",
                "# Question\n\n**Status:** waiting\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add malformed action")
            destination = source.with_name("blocking-question.md")
            source.rename(destination)
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_claimed_action_identity_cannot_change_before_deletion(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Broken\n")
            path = (
                "message-queue/needs-agent/requests/blocking-repair.md"
            )
            item = self.write(
                root,
                path,
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the source\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file repair")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim repair")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "repair the source", "declare the source repaired"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "rewrite claimed action")
            source.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("identity or response changed", findings[0].message)

    def test_recreated_claimed_path_cannot_reuse_older_claim_history(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Broken\n")
            path = (
                "message-queue/needs-agent/requests/blocking-repair.md"
            )
            open_text = (
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n"
            )
            item = self.write(root, path, open_text)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file first repair")
            claimed_text = open_text.replace(
                "**Status:** open", "**Status:** in-repair"
            )
            item.write_text(claimed_text, encoding="utf-8")
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim first repair")
            source.write_text("# First repair\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve first repair")

            item = self.write(root, path, claimed_text)
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "recreate already claimed")
            source.write_text("# Second repair\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("no committed one-line", findings[0].message)

    def test_range_detects_add_then_unresolved_delete(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            base = self.git(root, "rev-parse", "HEAD")
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-repair.md",
                "# Repair\n\n**Status:** open\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add action")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete action")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))

    def test_queue_v1_activation_can_enrich_legacy_human_context_once(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v0\n",
            )
            self.write(root, "docs/design.md", "# Design\n")
            path = (
                "message-queue/needs-human/decisions/"
                "blocking-admission.md"
            )
            item = self.write(root, path, VALID_DECISION)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy human action")

            enriched = VALID_DECISION.replace(
                "**Full context:** [design](docs/design.md#boundary)\n",
                "**Full context:** [design](docs/design.md#boundary)\n"
                "**Why-you-might-care:** This choice controls admission.\n"
                "**If-you-do-nothing:** The task remains blocked.\n",
            )
            contract.write_text(
                "**Queue resolution schema:** v1\n", encoding="utf-8"
            )
            item.write_text(enriched, encoding="utf-8")
            self.git(root, "add", ".")
            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

            self.git(root, "commit", "-m", "activate queue v1")
            item.write_text(
                enriched.replace(
                    "This choice controls admission.",
                    "This rewrite changes the framing.",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("action identity changed", findings[0].message)

    def test_divergent_range_checks_discarded_old_tip_snapshot(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            common = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "old-tip")
            path = (
                "message-queue/needs-agent/requests/"
                "non-blocking-old-tip-action.md"
            )
            self.write(
                root,
                path,
                "# Preserve this action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the old tip\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Resolution evidence:** `message-queue/AGENTS.md`\n"
                "**If unanswered:** keep the action live\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file action on old tip")
            old_tip = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "rewritten", common)
            self.write(root, "rewritten.md", "# Rewritten history\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "rewrite without old action")
            new_tip = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.multiple(
                    RECONCILE,
                    CHANGE_RANGE=f"{old_tip}...{new_tip}",
                    DISPLACED_TIP=old_tip,
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertEqual(Path(path), findings[0].subject)
            self.assertIn("deleted unresolved", findings[0].message)

    def test_new_tip_activation_preserves_pre_v1_displaced_action(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Common\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common pre-v1 history")
            common = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "old-tip")
            path = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pre-v1-action.md"
            )
            self.write(
                root,
                path,
                "# Preserve this action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the old tip\n"
                "**Full context:** `README.md`\n"
                "**Resolution evidence:** `README.md`\n"
                "**If unanswered:** keep the action live\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file pre-v1 old-tip action")
            old_tip = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "rewritten", common)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue on new history")
            new_tip = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.multiple(
                    RECONCILE,
                    CHANGE_RANGE=f"{old_tip}...{new_tip}",
                    DISPLACED_TIP=old_tip,
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertEqual(Path(path), findings[0].subject)
            self.assertIn(
                "divergent update discarded", findings[0].message
            )

    def test_divergent_range_accepts_action_carried_to_new_tip(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            common = self.git(root, "rev-parse", "HEAD")
            path = (
                "message-queue/needs-agent/requests/"
                "non-blocking-carried-action.md"
            )
            action = (
                "# Preserve this action\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the update\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Resolution evidence:** `message-queue/AGENTS.md`\n"
                "**If unanswered:** keep the action live\n"
            )

            self.git(root, "checkout", "-b", "old-tip")
            self.write(root, path, action)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file action on old tip")
            old_tip = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "rewritten", common)
            self.write(root, path, action)
            self.write(root, "rewritten.md", "# Rewritten history\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "carry action through rewrite")
            new_tip = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.multiple(
                    RECONCILE,
                    CHANGE_RANGE=f"{old_tip}...{new_tip}",
                    DISPLACED_TIP=old_tip,
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_divergent_pr_range_is_not_implicitly_a_force_push(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common")
            common = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "base-branch")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-base-only.md",
                "# Base action\n\n**Status:** open\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base branch action")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "pr-head", common)
            self.write(root, "feature.md", "# Feature\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "pull request head")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings)

    def test_range_accepts_claim_then_evidence_bound_resolution(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Broken\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            base = self.git(root, "rev-parse", "HEAD")
            path = (
                "message-queue/needs-agent/requests/blocking-repair.md"
            )
            item = self.write(
                root,
                path,
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file repair")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim repair")
            source.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve repair")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    self.assertEqual(
                        [], list(RECONCILE.check_queue_resolution())
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_range_rejects_action_created_in_claimed_state(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            source = self.write(root, "docs/source.md", "# Broken\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            base = self.git(root, "rev-parse", "HEAD")
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-repair.md",
                "# Repair\n\n"
                "**Status:** in-repair\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/source.md`\n"
                "**Blocks now:** transition:merge\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add preclaimed action")
            source.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete preclaimed action")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))
            self.assertIn("no committed one-line", findings[0].message)

    def test_root_range_grandfathers_deletion_before_activation(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-legacy.md",
                "# Legacy\n\n**Status:** open\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add legacy action")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete legacy action")
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate resolution gate")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"root:{head}"
                ):
                    self.assertEqual(
                        [], list(RECONCILE.check_queue_resolution())
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_two_branch_queue_activations_govern_both_hidden_histories(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v0\n",
            )
            left_path = (
                "message-queue/needs-agent/requests/"
                "blocking-left-repair.md"
            )
            right_path = (
                "message-queue/needs-agent/requests/"
                "blocking-right-repair.md"
            )
            left = self.write(
                root, left_path, "# Left repair\n\n**Status:** open\n"
            )
            right = self.write(
                root, right_path, "# Right repair\n\n**Status:** open\n"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common ungoverned queue")
            common = self.git(root, "rev-parse", "HEAD")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "left")
            contract.write_text(
                "**Queue resolution schema:** v1\n", encoding="utf-8"
            )
            self.git(root, "add", "message-queue/AGENTS.md")
            self.git(root, "commit", "-m", "activate left queue history")
            left_activation = self.git(root, "rev-parse", "HEAD")
            left.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete left action")

            self.git(root, "checkout", "-b", "right", common)
            contract.write_text(
                "**Queue resolution schema:** v1\n", encoding="utf-8"
            )
            self.git(root, "add", "message-queue/AGENTS.md")
            self.git(root, "commit", "-m", "activate right queue history")
            right_activation = self.git(root, "rev-parse", "HEAD")
            right.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete right action")

            self.git(root, "checkout", "left")
            self.git(root, "merge", "--no-ff", "--no-commit", "right")
            self.git(root, "checkout", common, "--", left_path, right_path)
            self.git(root, "commit", "-m", "merge and preserve live actions")
            head = self.git(root, "rev-parse", "HEAD")

            simplified = set(self.git(
                root,
                "log",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "message-queue/AGENTS.md",
            ).splitlines())
            self.assertNotEqual(
                {left_activation, right_activation},
                {left_activation, right_activation}.intersection(simplified),
            )
            full = set(self.git(
                root,
                "log",
                "--full-history",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "message-queue/AGENTS.md",
            ).splitlines())
            self.assertTrue(
                {left_activation, right_activation}.issubset(full)
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"root:{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(
                {Path(left_path), Path(right_path)},
                {finding.subject for finding in findings},
            )
            self.git(root, "checkout", trunk)

    def test_treesame_queue_activation_and_removal_remain_governed(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            contract = self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v0\n",
            )
            path = (
                "message-queue/needs-agent/requests/"
                "blocking-hidden-repair.md"
            )
            item = self.write(
                root, path, "# Hidden repair\n\n**Status:** open\n"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common queue v0")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "hidden-queue-history")
            contract.write_text(
                "**Queue resolution schema:** v1\n", encoding="utf-8"
            )
            self.git(root, "add", "message-queue/AGENTS.md")
            self.git(root, "commit", "-m", "activate hidden queue history")
            activation = self.git(root, "rev-parse", "HEAD")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete hidden live action")
            contract.write_text(
                "**Queue resolution schema:** v0\n", encoding="utf-8"
            )
            self.git(root, "add", "message-queue/AGENTS.md")
            self.git(root, "commit", "-m", "restore queue v0")

            self.git(root, "checkout", trunk)
            self.write(root, "main.md", "# Main change\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "unrelated main change")
            self.git(
                root,
                "merge",
                "--no-ff",
                "hidden-queue-history",
                "-m",
                "merge hidden queue history",
            )
            head = self.git(root, "rev-parse", "HEAD")

            simplified = set(self.git(
                root,
                "log",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "message-queue/AGENTS.md",
            ).splitlines())
            self.assertNotIn(activation, simplified)
            full = set(self.git(
                root,
                "log",
                "--full-history",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "message-queue/AGENTS.md",
            ).splitlines())
            self.assertIn(activation, full)

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"root:{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                finding.subject == Path("message-queue/AGENTS.md")
                and "removed after activation" in finding.message
                for finding in findings
            ))
            self.assertTrue(any(
                finding.subject == Path(path)
                and "deleted unresolved" in finding.message
                for finding in findings
            ))

    def test_synthetic_merge_cannot_resolve_away_open_queue_item(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-merge.md",
                "# Merge action\n\n**Status:** open\n",
            )
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common queue")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            self.write(root, "feature.md", "# Feature\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "feature")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(root, "base.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", "--no-commit", trunk)
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings))

    def test_synthetic_merge_governs_parallel_history_joined_with_activation(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(root, "common.md", "# Common\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            item = self.write(
                root,
                "message-queue/needs-agent/requests/blocking-parallel.md",
                "# Parallel action\n\n**Status:** open\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "create parallel action")
            item.unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "erase parallel action")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", "--no-commit", trunk)
            self.git(root, "commit", "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                finding.subject == Path(
                    "message-queue/needs-agent/requests/"
                    "blocking-parallel.md"
                )
                and "deleted unresolved" in finding.message
                for finding in findings
            ))

    def make_task(self, root, status, queue_actions):
        task_id = "2026-07-23-example"
        task = root / "tasks" / status / task_id
        task.mkdir(parents=True)
        (task / "task.md").write_text(
            "# Example\n\n"
            "**Claimed-by:** test\n"
            "**Filed:** 2026-07-23\n"
            "**Repository scope:** core\n"
            f"**Queue actions:** {queue_actions}\n",
            encoding="utf-8",
        )
        if status in ("1_in-progress", "2_blocked", "3_in-review", "4_done"):
            (task / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (task / "worklog.md").write_text("# Worklog\n", encoding="utf-8")
        if status in ("3_in-review", "4_done"):
            (task / "verification.md").write_text("# Verification\n", encoding="utf-8")
        return task

    @staticmethod
    def terminal_local_review(
        target_path,
        digest,
        outcome,
        timing_line,
        evidence_path="docs/review-disposition.md",
        status="waiting",
    ):
        timing_followup = (
            ""
            if timing_line.startswith("**If unanswered:**")
            else "**Until then:** keep the reviewed pursuit unchanged\n"
        )
        return (
            "# Review\n\n"
            f"**Status:** {status}\n"
            "**Filed:** 2026-07-23\n"
            "**Action:** review the exact pursuit\n"
            f"**Full context:** `{target_path}`\n"
            f"**Resolution evidence:** `{evidence_path}`\n"
            f"**Review target:** `{target_path}`\n"
            f"**Review revision:** {digest}\n"
            f"**Reviewed revision:** {digest}\n"
            f"**Review outcome:** {outcome}\n"
            f"{timing_line}\n"
            f"{timing_followup}"
            f"**Your review:** {outcome}\n"
        )

    def make_handover(self, root, folder, attention, marker="v1", extra=""):
        (root / "message-queue").mkdir(parents=True, exist_ok=True)
        contract = root / "history" / "AGENTS.md"
        if not contract.is_file():
            contract.parent.mkdir(parents=True, exist_ok=True)
            contract.write_text(
                "# History contract\n\n"
                "**Queue projection schema:** v1\n",
                encoding="utf-8",
            )
        conversation = root / "history" / "conversations" / folder
        conversation.mkdir(parents=True)
        marker_line = (
            f"**Queue projection:** {marker}\n\n" if marker is not None else ""
        )
        (conversation / "handover.md").write_text(
            "# Handover\n\n"
            + marker_line
            + "## Needs your attention\n\n"
            + attention
            + "\n\n## Next steps\n\nNone.\n"
            + extra,
            encoding="utf-8",
        )
        return conversation / "handover.md"

    def activate_strict_handover_entries(self, root, version="v2"):
        contract = root / "history/AGENTS.md"
        contract.parent.mkdir(parents=True, exist_ok=True)
        text = (
            contract.read_text(encoding="utf-8")
            if contract.is_file()
            else "# History contract\n\n**Queue projection schema:** v1\n"
        )
        marker = f"**Queue action-entry schema:** {version}"
        if marker not in text:
            contract.write_text(
                text.rstrip()
                + f"\n{marker}\n",
                encoding="utf-8",
            )
        return contract

    def test_unmarked_legacy_handover_is_preserved(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-22-1200PDT-legacy",
                "Ask the owner in prose.",
                marker=None,
            )
            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

    def test_v1_handover_accepts_exact_none_and_ignores_other_sections(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-none",
                "None.",
                extra="\n## Notes\n\nAsk a non-actionable historical question.\n",
            )
            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

    def test_handover_next_steps_cannot_originate_agent_action(self):
        with self.repo() as root:
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-orphan-agent-step",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\nThe next session must deploy the release.",
                ),
                encoding="utf-8",
            )

            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any("without a canonical needs-agent link" in message
                                for message in messages))

    def test_strict_handover_rejects_second_unlinked_human_ask(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-docs.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review docs\n\n"
                "**Action:** review docs\n"
                "**Why-you-might-care:** The docs control production behavior.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-extra-human-ask",
                "- [review docs](../../../"
                f"{queue_rel}) — Also decide whether to delete production?",
            )
            self.activate_strict_handover_entries(root)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "fixed handover suffix" in message
                for message in messages
            ), messages)

    def test_strict_handover_rejects_action_like_supporting_link(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-docs.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review docs\n\n"
                "**Action:** review docs\n"
                "**Why-you-might-care:** The docs control production behavior.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-supporting-action-link",
                "- [review docs](../../../"
                f"{queue_rel}) — [Approve production](https://example.invalid) "
                "Why-you-might-care: The docs control production behavior. "
                "|| If-you-do-nothing: The review remains pending.",
            )
            self.activate_strict_handover_entries(root)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "only its exact Action-labeled needs-human queue link" in message
                for message in messages
            ), messages)

    def test_strict_handover_inline_code_subject_cannot_be_rebound(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-deployment.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review deployment\n\n"
                "**Action:** Review the `staging` deployment.\n"
                "**Why-you-might-care:** The target controls release safety.\n"
                "**If-you-do-nothing:** The deployment remains pending.\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-inline-code-rebind",
                "- [Review the `production` deployment.](../../../"
                f"{queue_rel}) — Why-you-might-care: The target controls "
                "release safety. || If-you-do-nothing: The deployment "
                "remains pending.",
            )
            self.activate_strict_handover_entries(root)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "link label must exactly project" in message
                for message in messages
            ), messages)

    def test_strict_handover_rejects_raw_html_action_attributes(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-docs.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review docs\n\n"
                "**Action:** review docs\n"
                "**Why-you-might-care:** The docs control production behavior.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-raw-html-action",
                "- [review docs](../../../"
                f"{queue_rel}) — Why-you-might-care: The docs control "
                "production behavior. || If-you-do-nothing: The review "
                "remains pending.\n"
                "  <a href='https://example.invalid/delete'>"
                "<img alt='Delete production now'></a>",
            )
            self.activate_strict_handover_entries(root)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "contains raw HTML" in message for message in messages
            ), messages)

    def test_strict_handover_rejects_raw_html_outside_entries(self):
        raw_cases = (
            "<div>Please approve production.</div>",
            "<div>The deployment context is documented.</div>",
        )
        for actor, raw_html in (
            (actor, raw_html)
            for actor in ("needs-human", "needs-agent")
            for raw_html in raw_cases
        ):
            with self.subTest(
                actor=actor,
                raw_html=raw_html,
            ), self.repo() as root:
                if actor == "needs-human":
                    queue_rel = (
                        "message-queue/needs-human/reviews/"
                        "future-blocking-review-docs.md"
                    )
                    self.write(
                        root,
                        queue_rel,
                        "# Review docs\n\n"
                        "**Action:** review docs\n"
                        "**Why-you-might-care:** The docs control behavior.\n"
                        "**If-you-do-nothing:** The review remains pending.\n",
                    )
                    entry = (
                        f"- [review docs](../../../{queue_rel})"
                        " — Why-you-might-care: The docs control behavior."
                        " || If-you-do-nothing: The review remains pending."
                    )
                    handover = self.make_handover(
                        root,
                        "2026-07-23-1200PDT-human-raw-outside",
                        entry + "\n" + raw_html,
                    )
                else:
                    queue_rel = (
                        "message-queue/needs-agent/requests/"
                        "non-blocking-repair-docs.md"
                    )
                    self.write(
                        root,
                        queue_rel,
                        "# Repair docs\n\n**Action:** repair docs\n",
                    )
                    entry = f"- [repair docs](../../../{queue_rel})"
                    handover = self.make_handover(
                        root,
                        "2026-07-23-1200PDT-agent-raw-outside",
                        "None.",
                    )
                    handover.write_text(
                        handover.read_text(encoding="utf-8").replace(
                            "## Next steps\n\nNone.",
                            "## Next steps\n\n"
                            + entry
                            + "\n"
                            + raw_html,
                        ),
                        encoding="utf-8",
                    )
                self.activate_strict_handover_entries(root)
                with mock.patch.object(
                    RECONCILE,
                    "newly_added_handovers",
                    return_value=({handover.relative_to(root)}, None),
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any(
                    "strict handover contains raw HTML" in message
                    for message in messages
                ), messages)

    def test_strict_handover_rejects_html_fake_heading_boundary(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-docs.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review docs\n\n"
                "**Action:** review docs\n"
                "**Why-you-might-care:** The docs control behavior.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            entry = (
                f"- [review docs](../../../{queue_rel})"
                " — Why-you-might-care: The docs control behavior."
                " || If-you-do-nothing: The review remains pending."
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-html-fake-heading",
                entry
                + "\n<div>\n"
                + "## fake-heading\n"
                + "Please approve production.\n"
                + "</div>",
            )
            self.activate_strict_handover_entries(root)
            raw_body = RECONCILE.raw_level_two_section_body(
                handover.read_text(encoding="utf-8"),
                "## Needs your attention",
            )
            self.assertNotIn("Please approve production.", raw_body)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "strict handover contains raw HTML" in message
                for message in messages
            ), messages)

    def test_strict_handover_rejects_agent_link_borrowing(self):
        cases = (
            (
                "- Implement billing; [repair docs](../../../{path})",
                "owning queue link first",
            ),
            (
                "- [Implement billing](../../../{path}) — "
                "The documentation is stale.",
                "link label must exactly project",
            ),
            (
                "- [repair docs](../../../{path}) — Implement billing.",
                "only its exact Action-labeled needs-agent queue link",
            ),
        )
        for next_step, expected in cases:
            with self.subTest(expected=expected), self.repo() as root:
                queue_rel = (
                    "message-queue/needs-agent/requests/"
                    "non-blocking-repair-docs.md"
                )
                self.write(
                    root,
                    queue_rel,
                    "# Repair docs\n\n**Action:** repair docs\n",
                )
                handover = self.make_handover(
                    root,
                    "2026-07-23-1200PDT-agent-link-borrowing",
                    "None.",
                )
                handover.write_text(
                    handover.read_text(encoding="utf-8").replace(
                        "## Next steps\n\nNone.",
                        "## Next steps\n\n"
                        + next_step.format(path=queue_rel),
                    ),
                    encoding="utf-8",
                )
                self.activate_strict_handover_entries(root)
                with mock.patch.object(
                    RECONCILE,
                    "newly_added_handovers",
                    return_value=({handover.relative_to(root)}, None),
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any(
                    expected in message for message in messages
                ), messages)

    def test_staged_strict_handover_accepts_fixed_context_and_agent_subset(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v2\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate strict handovers")

            human_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-boundary.md"
            )
            agent_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-repair-docs.md"
            )
            unrelated_agent_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-inspect-logs.md"
            )
            self.write(
                root,
                human_rel,
                "# Review boundary\n\n"
                "**Action:** review the boundary\n"
                "**Why-you-might-care:** The choice is hard versus soft enforcement.\n"
                "**If-you-do-nothing:** A failed scan blocks at transition:review.\n",
            )
            self.write(
                root,
                agent_rel,
                "# Repair docs\n\n"
                "**Action:** repair the docs\n",
            )
            self.write(
                root,
                unrelated_agent_rel,
                "# Inspect logs\n\n"
                "**Action:** inspect the logs\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-strict-valid",
                "- [review the boundary](../../../"
                f"{human_rel}) — Why-you-might-care: The choice is hard "
                "versus soft enforcement. || If-you-do-nothing: A failed "
                "scan blocks at transition:review.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\n"
                    "- [repair the docs](../../../"
                    f"{agent_rel})",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")

            findings = list(RECONCILE.check_handover_queue_projection())
            self.assertEqual([], findings, self.messages(findings))

    def test_strict_handover_rejects_two_queue_links_or_wrong_actor(self):
        cases = (
            (
                "attention",
                "- [review docs](../../../{human}) "
                "[repair docs](../../../{agent})",
                "exactly one canonical needs-human",
            ),
            (
                "next",
                "- [review docs](../../../{human})",
                "wrong-actor needs-agent",
            ),
        )
        for section, entry, expected in cases:
            with self.subTest(section=section), self.repo() as root:
                human_rel = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review-docs.md"
                )
                agent_rel = (
                    "message-queue/needs-agent/requests/"
                    "non-blocking-repair-docs.md"
                )
                self.write(
                    root,
                    human_rel,
                    "# Review docs\n\n"
                    "**Action:** review docs\n"
                    "**Why-you-might-care:** The docs control behavior.\n"
                    "**If-you-do-nothing:** The review remains pending.\n",
                )
                self.write(
                    root,
                    agent_rel,
                    "# Repair docs\n\n**Action:** repair docs\n",
                )
                attention = (
                    entry.format(human=human_rel, agent=agent_rel)
                    if section == "attention"
                    else "- [review docs](../../../"
                    f"{human_rel}) — Why-you-might-care: The docs control "
                    "behavior. || If-you-do-nothing: The review remains pending."
                )
                handover = self.make_handover(
                    root,
                    "2026-07-23-1200PDT-strict-link-shape",
                    attention,
                )
                if section == "next":
                    handover.write_text(
                        handover.read_text(encoding="utf-8").replace(
                            "## Next steps\n\nNone.",
                            "## Next steps\n\n"
                            + entry.format(
                                human=human_rel, agent=agent_rel
                            ),
                        ),
                        encoding="utf-8",
                    )
                self.activate_strict_handover_entries(root)
                with mock.patch.object(
                    RECONCILE,
                    "newly_added_handovers",
                    return_value=({handover.relative_to(root)}, None),
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any(
                    expected in message for message in messages
                ), messages)

    def test_new_handover_rejects_duplicate_attention_sections(self):
        with self.repo() as root:
            self.init_git(root)
            self.make_handover(
                root,
                "2026-07-23-1200PDT-duplicate-attention",
                "None.\n\n"
                "## Needs your attention\n\n"
                "Human: decide whether to merge.",
            )
            self.git(root, "add", ".")

            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any("exactly one" in message
                                for message in messages))

    def test_committed_v1_handover_cannot_be_rewritten_with_orphan_ask(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-immutable",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add handover")
            base = self.git(root, "rev-parse", "HEAD")
            handover.write_text(
                "# Handover\n\n"
                "**Queue projection:** v1\n\n"
                "## Needs your attention\n\n"
                "- [Invented](../../../message-queue/needs-human/reviews/"
                "blocking-never-existed.md) — orphan ask.\n",
                encoding="utf-8",
            )
            self.git(root, "add", str(handover.relative_to(root)))

            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any("changed after its creation" in message
                                for message in messages))
            self.git(root, "commit", "-m", "rewrite handover")
            head = self.git(root, "rev-parse", "HEAD")
            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("changed after its creation" in message
                                for message in messages))

    def test_action_entry_v2_does_not_reinterpret_v1_creation_prose(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-v1-prose",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "# Handover",
                    "# Handover — repair contract round three",
                ),
                encoding="utf-8",
            )
            self.activate_strict_handover_entries(root, version="v1")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "create v1 handover")

            contract = root / "history/AGENTS.md"
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "**Queue action-entry schema:** v1",
                    "**Queue action-entry schema:** v2",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "activate v2")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual([], findings, self.messages(findings))

    def test_action_entry_v2_rejects_new_action_like_handover_prose(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v2\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate v2")

            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-v2-prose",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "# Handover",
                    "# Handover — repair contract round three",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "create v2 handover")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "action-like question or directive" in message
                for message in messages
            ), messages)

    def test_projection_adoption_freezes_unmarked_legacy_handover(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.write(
                root,
                "history/conversations/"
                "2026-07-22-1200PDT-legacy/handover.md",
                "# Legacy\n\n"
                "## Needs your attention\n\nNone.\n\n"
                "## Next steps\n\nNone.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy")
            original = handover.read_text(encoding="utf-8")

            self.write(
                root,
                "history/AGENTS.md",
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v2\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection")
            base = self.git(root, "rev-parse", "HEAD")

            handover.write_text(
                "# Legacy\n\n"
                "## Needs your attention\n\nCan you approve this release?\n\n"
                "## Next steps\n\nDeploy this now.\n",
                encoding="utf-8",
            )
            self.git(root, "add", str(handover.relative_to(root)))
            RECONCILE.start_git_snapshot_cache()
            try:
                staged_messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "modified after queue-projection adoption" in message
                for message in staged_messages
            ), staged_messages)

            self.git(root, "commit", "-m", "originate asks")
            handover.write_text(original, encoding="utf-8")
            self.git(root, "add", str(handover.relative_to(root)))
            self.git(root, "commit", "-m", "restore legacy bytes")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                range_messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "modified after queue-projection adoption" in message
                for message in range_messages
            ), range_messages)

    def test_projection_activation_governs_parallel_handover_mutation(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.write(
                root,
                "history/conversations/"
                "2026-07-22-1200PDT-parallel-legacy/handover.md",
                "# Legacy\n\n"
                "## Needs your attention\n\nNone.\n\n"
                "## Next steps\n\nNone.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            handover.write_text(
                "# Legacy\n\n"
                "## Needs your attention\n\nCan you approve this release?\n\n"
                "## Next steps\n\nNone.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "modify parallel handover")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                "history/AGENTS.md",
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v2\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", "--no-commit", trunk)
            self.git(root, "commit", "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "modified after queue-projection adoption" in message
                for message in messages
            ), messages)

    def test_new_handover_requires_v1_marker(self):
        with self.repo() as root:
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-marker",
                "None.",
                marker=None,
            )
            rel = handover.relative_to(root)
            with mock.patch.object(
                RECONCILE, "newly_added_handovers", return_value=({rel}, None)
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("Queue projection" in message for message in messages))

    def test_handover_rejects_orphan_attention_prose(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-orphan",
                "Please ask the owner whether this is acceptable.",
            )
            messages = self.messages(RECONCILE.check_handover_queue_projection())
            self.assertTrue(any("no canonical needs-human queue link" in message
                                for message in messages))

    def test_handover_rejects_unprefixed_needs_human_link(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-unprefixed",
                "[Review](message-queue/needs-human/reviews/architecture.md)",
            )
            messages = self.messages(RECONCILE.check_handover_queue_projection())
            self.assertTrue(any("unprefixed or invalid" in message
                                for message in messages))

    def test_handover_requires_delivery_class_order(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-order",
                "- [Later](message-queue/needs-human/reviews/"
                "non-blocking-later.md)\n"
                "- [Now](message-queue/needs-human/decisions/"
                "blocking-now.md)",
            )
            messages = self.messages(RECONCILE.check_handover_queue_projection())
            self.assertTrue(any("not ordered" in message for message in messages))

    def test_handover_links_may_target_deleted_queue_items(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-deleted",
                "- [Now](/deleted/checkout/message-queue/needs-human/decisions/"
                "blocking-now.md) — context.\n"
                "- [At merge](message-queue/needs-human/clarifications/"
                "future-blocking-at-merge.md) — context.\n"
                "- [Optional](message-queue/needs-human/reviews/"
                "non-blocking-later.md) — context.",
            )
            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

    def test_handover_ignores_commented_and_fenced_fake_links(self):
        hidden = (
            "Visible orphan prose <!-- [hidden](message-queue/needs-human/reviews/"
            "blocking-hidden.md) -->\n\n"
            "```\n[also hidden](message-queue/needs-human/reviews/"
            "blocking-fenced.md)\n```\n"
            "`[inline](message-queue/needs-human/reviews/blocking-inline.md)`\n"
            "\\[escaped](message-queue/needs-human/reviews/blocking-escaped.md)\n"
            "not-a-link](message-queue/needs-human/reviews/blocking-malformed.md)\n"
            "    [indented](message-queue/needs-human/reviews/"
            "blocking-indented.md)\n"
        )
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-hidden-link",
                hidden,
            )
            messages = self.messages(RECONCILE.check_handover_queue_projection())
            self.assertTrue(any("no canonical needs-human queue link" in message
                                for message in messages))

    def test_handover_projection_no_ops_without_queue_or_local_schema(self):
        with self.repo() as root:
            conversation = root / "history/conversations/2030-01-01-1200UTC-later"
            conversation.mkdir(parents=True)
            (conversation / "handover.md").write_text(
                "# Handover\n\n## Needs your attention\n\nOrphan prose.\n",
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_handover_queue_projection()))
            (root / "message-queue").mkdir()
            self.assertEqual([], list(RECONCILE.check_handover_queue_projection()))

    def test_action_entry_schema_is_sticky_after_activation(self):
        for committed in (False, True):
            with self.subTest(committed=committed), self.repo() as root:
                self.init_git(root)
                contract = self.write(
                    root,
                    "history/AGENTS.md",
                    "# History\n\n"
                    "**Queue projection schema:** v1\n"
                    "**Queue action-entry schema:** v1\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "activate strict handovers")
                base = self.git(root, "rev-parse", "HEAD")

                contract.write_text(
                    "# History\n\n**Queue projection schema:** v1\n",
                    encoding="utf-8",
                )
                self.git(root, "add", "history/AGENTS.md")
                if committed:
                    self.git(root, "commit", "-m", "remove strict marker")
                    head = self.git(root, "rev-parse", "HEAD")
                    context = mock.patch.object(
                        RECONCILE,
                        "CHANGE_RANGE",
                        f"{base}...{head}",
                    )
                else:
                    context = contextlib.nullcontext()

                with context:
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any(
                    "action-entry schema v1 was removed" in message
                    for message in messages
                ), messages)

    def test_queue_projection_schema_is_sticky_after_activation(self):
        for committed in (False, True):
            with self.subTest(committed=committed), self.repo() as root:
                self.init_git(root)
                contract = self.write(
                    root,
                    "history/AGENTS.md",
                    "# History\n\n"
                    "**Queue projection schema:** v1\n"
                    "**Queue action-entry schema:** v1\n",
                )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "activate handovers")
                base = self.git(root, "rev-parse", "HEAD")

                contract.write_text(
                    "# History\n\n"
                    "**Queue action-entry schema:** v1\n",
                    encoding="utf-8",
                )
                self.git(root, "add", "history/AGENTS.md")
                if committed:
                    self.git(root, "commit", "-m", "remove projection marker")
                    head = self.git(root, "rev-parse", "HEAD")
                    context = mock.patch.object(
                        RECONCILE,
                        "CHANGE_RANGE",
                        f"{base}...{head}",
                    )
                else:
                    context = contextlib.nullcontext()

                with context:
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any(
                    "Queue projection schema v1 was removed" in message
                    for message in messages
                ), messages)

    def test_action_entry_schema_allows_whole_history_service_removal(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate strict handovers")

            contract.unlink()
            contract.parent.rmdir()
            self.git(root, "add", "-A")

            findings = list(RECONCILE.check_handover_queue_projection())
            self.assertEqual([], findings, self.messages(findings))

    def test_new_handover_must_project_every_live_human_action(self):
        with self.repo() as root:
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-complete",
                "None.",
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/future-blocking-review.md",
                "# Pending review\n",
            )
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("says None." in message for message in messages))

    def test_new_handover_exactly_projects_live_human_actions(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review.md"
            )
            self.write(root, queue_rel, "# Pending review\n")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-complete",
                "- [Review](../../../"
                f"{queue_rel}) — decide before the start boundary.",
            )
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_handover_queue_projection())
                )

    def test_strict_handover_requires_timing_then_path_order(self):
        with self.repo() as root:
            first_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-alpha.md"
            )
            second_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-zulu.md"
            )
            self.write(
                root,
                first_rel,
                "# Alpha\n\n"
                "**Action:** review alpha\n"
                "**Why-you-might-care:** Alpha controls the first boundary.\n"
                "**If-you-do-nothing:** Alpha remains pending.\n",
            )
            self.write(
                root,
                second_rel,
                "# Zulu\n\n"
                "**Action:** review zulu\n"
                "**Why-you-might-care:** Zulu controls the last boundary.\n"
                "**If-you-do-nothing:** Zulu remains pending.\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-strict-order",
                "- [review zulu](../../../"
                f"{second_rel}) — Why-you-might-care: Zulu controls the last "
                "boundary. || If-you-do-nothing: Zulu remains pending.\n"
                "- [review alpha](../../../"
                f"{first_rel}) — Why-you-might-care: Alpha controls the first "
                "boundary. || If-you-do-nothing: Alpha remains pending.",
            )
            self.activate_strict_handover_entries(root)
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "timing-and-filename order" in message
                for message in messages
            ), messages)

    def test_new_handover_uses_its_creation_queue_snapshot(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-created-together.md"
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-creation-snapshot",
                "- [Review](../../../"
                f"{queue_rel}) — this action was live at creation.",
            )
            creation_text = handover.read_text(encoding="utf-8")
            later_rel = (
                "message-queue/needs-human/reviews/"
                "non-blocking-created-later.md"
            )
            self.write(root, later_rel, "# Later action\n")
            with mock.patch.object(
                RECONCILE,
                "newly_added_handovers",
                return_value=({handover.relative_to(root)}, None),
            ), mock.patch.object(
                RECONCILE,
                "handover_creation_state",
                return_value=(creation_text, {queue_rel}, set(), None),
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_handover_queue_projection())
                )

    def test_range_strict_handover_binds_action_at_creation(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate strict handovers")
            base = self.git(root, "rev-parse", "HEAD")

            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-original.md"
            )
            queue_item = self.write(
                root,
                queue_rel,
                "# Review\n\n"
                "**Action:** review the original boundary\n"
                "**Why-you-might-care:** The original boundary controls release.\n"
                "**If-you-do-nothing:** The original review remains pending.\n",
            )
            self.make_handover(
                root,
                "2026-07-23-1200PDT-action-snapshot",
                "- [review the original boundary](../../../"
                f"{queue_rel}) — Why-you-might-care: The original boundary "
                "controls release. || If-you-do-nothing: The original review "
                "remains pending.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add strict handover")

            queue_item.write_text(
                "# Review\n\n"
                "**Action:** review a later boundary\n"
                "**Why-you-might-care:** A later boundary controls release.\n"
                "**If-you-do-nothing:** The later review remains pending.\n",
                encoding="utf-8",
            )
            self.git(root, "add", queue_rel)
            self.git(root, "commit", "-m", "change later queue action")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual([], findings, self.messages(findings))

    def test_range_grandfathers_handover_before_action_entry_activation(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate queue projection")
            base = self.git(root, "rev-parse", "HEAD")

            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-legacy-shape.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review\n\n**Action:** review the legacy shape\n",
            )
            self.make_handover(
                root,
                "2026-07-23-1200PDT-pre-entry-schema",
                "[Short legacy label](../../../"
                f"{queue_rel}) — paragraph-shaped context.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add pre-entry handover")

            contract = root / "history/AGENTS.md"
            contract.write_text(
                contract.read_text(encoding="utf-8").rstrip()
                + "\n**Queue action-entry schema:** v1\n",
                encoding="utf-8",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "activate strict entries")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual([], findings, self.messages(findings))

    def test_range_check_reads_queue_at_real_handover_creation_commit(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")

            original_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-created-together.md"
            )
            original = self.write(root, original_rel, "# Original action\n")
            self.make_handover(
                root,
                "2026-07-23-1200PDT-real-snapshot",
                "- [Review](../../../"
                f"{original_rel}) — live when this handover was written.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add handover and action")

            original.unlink()
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-added-later.md",
                "# Later action\n",
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "resolve old action and add another")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_handover_queue_projection())
                )

    def test_staged_handover_accepts_live_agent_action_from_same_snapshot(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")

            agent_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-follow-up.md"
            )
            self.write(root, agent_rel, "# Follow up\n")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-agent-snapshot",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\n"
                    f"- [Follow up](../../../{agent_rel}) — continue later.",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")

            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

    def test_range_handover_accepts_live_agent_action_at_creation(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            base = self.git(root, "rev-parse", "HEAD")

            agent_rel = (
                "message-queue/needs-agent/requests/"
                "future-blocking-follow-up.md"
            )
            self.write(root, agent_rel, "# Follow up\n")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-agent-range",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\n"
                    f"- [Follow up](../../../{agent_rel}) — continue later.",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add agent action and handover")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_handover_queue_projection())
                )

    def test_range_uses_merge_candidate_for_handover_added_only_on_base(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            self.write(root, "feature.md", "# Feature\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "feature change")
            feature_head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.make_handover(
                root,
                "2026-07-23-1200PDT-base-only",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add base handover")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", trunk, "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE,
                    "CHANGE_RANGE",
                    f"{base}...{feature_head}",
                ):
                    self.assertEqual(
                        [], list(RECONCILE.check_handover_queue_projection())
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_range_uses_merge_candidate_for_schema_activated_only_on_base(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(root, "README.md", "# Repository\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "initial")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            self.write(root, "feature.md", "# Feature\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "feature change")
            feature_head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", trunk, "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE,
                    "CHANGE_RANGE",
                    f"{base}...{feature_head}",
                ):
                    self.assertEqual(
                        [], list(RECONCILE.check_handover_queue_projection())
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_parallel_schema_activation_governs_merged_handover(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(root, "README.md", "# Common\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common pre-schema history")
            common = self.git(root, "rev-parse", "HEAD")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "handover", common)
            handover = self.write(
                root,
                "history/conversations/"
                "2026-07-23-1200PDT-parallel/handover.md",
                "# Handover\n\n"
                "## Needs your attention\n\n"
                "- Please review the release boundary.\n\n"
                "## Next steps\n\nNone.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add parallel handover")
            feature_head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "handover")
            self.git(root, "merge", "--no-ff", trunk, "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE,
                    "CHANGE_RANGE",
                    f"{base}...{feature_head}",
                ):
                    findings = list(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            messages = self.messages(findings)
            self.assertTrue(any(
                "missing exact **Queue projection:** v1" in message
                for message in messages
            ), messages)
            self.assertTrue(any(
                "canonical needs-human queue link" in message
                or "no canonical needs-human queue link" in message
                for message in messages
            ), messages)
            self.assertTrue(any(
                finding.subject == handover.relative_to(root)
                for finding in findings
            ), messages)

    def test_strict_handover_rejects_rendered_ask_outside_queue_sections(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v2\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate strict handovers")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-hidden-outside-ask",
                "None.",
                extra=(
                    "\n## Notes\n\n"
                    '<span aria-label="Please review the release"></span>\n'
                ),
            )
            self.git(root, "add", ".")

            findings = list(RECONCILE.check_handover_queue_projection())
            self.assertTrue(any(
                finding.subject == handover.relative_to(root)
                and "strict handover contains raw HTML" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_two_branch_handover_activations_govern_both_histories(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            contract = self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v0\n"
                "**Queue action-entry schema:** v0\n",
            )
            queue_paths = (
                "message-queue/needs-human/decisions/"
                "blocking-left-choice.md",
                "message-queue/needs-human/decisions/"
                "blocking-right-choice.md",
            )
            for label, queue_path in zip(("left", "right"), queue_paths):
                self.write(
                    root,
                    queue_path,
                    f"# {label.title()} choice\n\n"
                    f"**Action:** choose the {label} boundary\n"
                    f"**Why-you-might-care:** The {label} boundary controls release.\n"
                    f"**If-you-do-nothing:** The {label} choice remains pending.\n",
                )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common ungoverned history")
            common = self.git(root, "rev-parse", "HEAD")

            attention = "\n".join(
                f"- [{label.title()}](../../../{queue_path})"
                for label, queue_path in zip(("left", "right"), queue_paths)
            )
            activations = set()
            handovers = set()
            for branch in ("left-history", "right-history"):
                self.git(root, "checkout", "-b", branch, common)
                contract.write_text(
                    "# History\n\n"
                    "**Queue projection schema:** v1\n"
                    "**Queue action-entry schema:** v1\n",
                    encoding="utf-8",
                )
                self.git(root, "add", "history/AGENTS.md")
                self.git(root, "commit", "-m", f"activate {branch}")
                activations.add(self.git(root, "rev-parse", "HEAD"))
                handover = self.make_handover(
                    root,
                    "2026-07-23-1200PDT-" + branch,
                    attention,
                )
                handovers.add(handover.relative_to(root))
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", f"add {branch} handover")

            self.git(root, "checkout", "left-history")
            self.git(
                root,
                "merge",
                "--no-ff",
                "right-history",
                "-m",
                "merge independent history adoptions",
            )
            head = self.git(root, "rev-parse", "HEAD")

            simplified = set(self.git(
                root,
                "log",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "history/AGENTS.md",
            ).splitlines())
            self.assertNotEqual(
                activations, activations.intersection(simplified)
            )
            full = set(self.git(
                root,
                "log",
                "--full-history",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "history/AGENTS.md",
            ).splitlines())
            self.assertTrue(activations.issubset(full))

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual(
                handovers,
                {finding.subject for finding in findings},
            )

    def test_treesame_handover_activation_and_removal_remain_governed(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            contract = self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v0\n"
                "**Queue action-entry schema:** v0\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common history v0")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "hidden-handover-history")
            contract.write_text(
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v1\n",
                encoding="utf-8",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "activate hidden handover history")
            activation = self.git(root, "rev-parse", "HEAD")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-hidden-orphan",
                "None.",
                marker=None,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add hidden orphan handover")
            contract.write_text(
                "# History\n\n"
                "**Queue projection schema:** v0\n"
                "**Queue action-entry schema:** v0\n",
                encoding="utf-8",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "restore history v0")

            self.git(root, "checkout", trunk)
            self.write(root, "main.md", "# Main change\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "unrelated main change")
            self.git(
                root,
                "merge",
                "--no-ff",
                "hidden-handover-history",
                "-m",
                "merge hidden handover history",
            )
            head = self.git(root, "rev-parse", "HEAD")

            simplified = set(self.git(
                root,
                "log",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "history/AGENTS.md",
            ).splitlines())
            self.assertNotIn(activation, simplified)
            full = set(self.git(
                root,
                "log",
                "--full-history",
                "--reverse",
                "--format=%H",
                head,
                "--",
                "history/AGENTS.md",
            ).splitlines())
            self.assertIn(activation, full)

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                finding.subject == Path("history/AGENTS.md")
                and "removed after activation" in finding.message
                for finding in findings
            ))
            self.assertTrue(any(
                finding.subject == handover.relative_to(root)
                and "missing exact **Queue projection:** v1" in finding.message
                for finding in findings
            ))

    def test_handover_incarnation_follows_selected_merge_lineage(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n"
                "**Queue projection schema:** v1\n"
                "**Queue action-entry schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate history schemas")
            common = self.git(root, "rev-parse", "HEAD")
            rel = Path(
                "history/conversations/"
                "2026-07-23-1200PDT-competing-add/handover.md"
            )
            selected = (
                "# Handover A\n\n"
                "**Queue projection:** v1\n\n"
                "## Needs your attention\n\nNone.\n\n"
                "## Next steps\n\nNone.\n"
            )
            unselected = selected.replace("Handover A", "Handover B")

            self.git(root, "checkout", "-b", "selected-add")
            self.write(root, rel.as_posix(), selected)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add selected incarnation")

            self.git(root, "checkout", "-b", "unselected-add", common)
            self.write(root, rel.as_posix(), unselected)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add competing incarnation")

            self.git(root, "checkout", "selected-add")
            self.git(
                root,
                "merge",
                "--no-ff",
                "-s",
                "ours",
                "unselected-add",
                "-m",
                "select handover A",
            )
            creation_text, error = RECONCILE.handover_current_incarnation_text(
                rel
            )
            self.assertIsNone(error)
            self.assertEqual(selected, creation_text)
            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

    def test_staged_merge_preserves_second_parent_handover_incarnation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "handover")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-second-parent",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add immutable handover")
            original = handover.read_text(encoding="utf-8")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "non-blocking-review-left.md",
                "# Review left\n\n"
                "**Action:** review the left branch\n"
                "**Why-you-might-care:** The branch changes shared state.\n"
                "**If-you-do-nothing:** The review remains pending.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add left review")
            left = self.git(root, "rev-parse", "HEAD")
            self.git(root, "merge", "--no-ff", "--no-commit", "handover")

            RECONCILE.start_git_snapshot_cache()
            try:
                added, error = RECONCILE.newly_added_handovers()
                staged = list(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertIsNone(error)
            self.assertIn(handover.relative_to(root), added)
            self.assertEqual([], staged, self.messages(staged))
            creation_text, creation_error = (
                RECONCILE.handover_current_incarnation_text(
                    handover.relative_to(root)
                )
            )
            self.assertIsNone(creation_error)
            self.assertEqual(original, creation_text)

            self.git(root, "commit", "-m", "merge handover")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{left}...{merged}"
                ):
                    committed = list(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], committed, self.messages(committed))

    def test_staged_merge_rechecks_invalid_side_handover_creation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handover schema")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "invalid-handover-history")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-invalid-side",
                "Please approve the unqueued side release.",
                marker=None,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add invalid side handover")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            self.git(
                root,
                "merge",
                "--no-ff",
                "--no-commit",
                "invalid-handover-history",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                added, error = RECONCILE.newly_added_handovers()
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertIsNone(error)
            self.assertIn(handover.relative_to(root), added)
            self.assertTrue(any(
                finding.subject == handover.relative_to(root)
                and "Queue projection" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_staged_merge_rechecks_duplicate_path_side_handover_creation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handovers")
            trunk = self.git(root, "branch", "--show-current")
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review-release.md"
            )
            attention = (
                "- [review the release](../../../"
                + queue_rel
                + ") — Why-you-might-care: The release changes shared "
                "state. || If-you-do-nothing: The review remains pending."
            )

            self.git(root, "checkout", "-b", "invalid-side")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-collision",
                attention,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add unqueued side handover")

            self.git(root, "checkout", trunk)
            self.write(
                root,
                queue_rel,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review the release\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** pending\n"
                "**Why-you-might-care:** The release changes shared state.\n"
                "**If-you-do-nothing:** The review remains pending.\n"
                "**Your review:** ______\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            self.make_handover(
                root,
                "2026-07-23-1200PDT-collision",
                attention,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add valid trunk handover")
            self.git(
                root,
                "merge",
                "--no-ff",
                "--no-commit",
                "invalid-side",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                added, error = RECONCILE.newly_added_handovers()
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertIsNone(error)
            self.assertIn(handover.relative_to(root), added)
            self.assertTrue(any(
                "creation snapshot" in finding.message
                or "canonical needs-human" in finding.message
                or "reuses a path" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_staged_merge_rechecks_side_handover_reincarnation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handovers")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "reincarnated-side")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-side-reincarnation",
                "None.",
            )
            original = handover.read_text(encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add side handover")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete side handover")
            self.write(root, handover.relative_to(root), original)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "readd side handover")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            left = self.git(root, "rev-parse", "HEAD")
            self.git(
                root,
                "merge",
                "--no-ff",
                "--no-commit",
                "reincarnated-side",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "reuses a path" in finding.message for finding in staged
            ), self.messages(staged))

            self.git(root, "commit", "-m", "merge reincarnated handover")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{left}...{merged}"
                ):
                    committed = list(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "reuses a path" in finding.message for finding in committed
            ), self.messages(committed))

    def test_merge_rechecks_invalid_deleted_side_handover_creation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate handovers")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "ephemeral-invalid-side")
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-ephemeral-invalid",
                "Please approve the unqueued release.",
                marker=None,
            )
            rel = handover.relative_to(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add invalid side handover")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete invalid side handover")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            left = self.git(root, "rev-parse", "HEAD")
            self.git(
                root,
                "merge",
                "--no-ff",
                "--no-commit",
                "ephemeral-invalid-side",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                staged = list(
                    RECONCILE.check_handover_queue_projection()
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                finding.subject == rel
                and "Queue projection" in finding.message
                for finding in staged
            ), self.messages(staged))

            self.git(root, "commit", "-m", "merge ephemeral handover")
            merged = self.git(root, "rev-parse", "HEAD")
            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{left}...{merged}"
                ):
                    committed = list(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                finding.subject == rel
                and "Queue projection" in finding.message
                for finding in committed
            ), self.messages(committed))

    def test_root_range_checks_unmarked_handover_on_first_push(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.make_handover(
                root,
                "2026-07-23-1200PDT-first-push",
                "None.",
                marker=None,
            )
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "initial")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("Queue projection" in message
                                for message in messages))

    def test_root_range_preserves_handover_created_before_schema_activation(self):
        with self.repo() as root:
            self.init_git(root)
            self.make_handover(
                root,
                "2026-07-22-1200PDT-before-schema",
                "Legacy prose.",
                marker=None,
            )
            (root / "history/AGENTS.md").unlink()
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy history")

            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "activate projection schema")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                added, error = RECONCILE.newly_added_handovers()
                self.assertIsNone(error)
                self.assertEqual(set(), added)
                findings = list(RECONCILE.check_handover_queue_projection())
            self.assertEqual([], findings, self.messages(findings))

    def test_root_range_uses_latest_add_for_restored_legacy_handover(self):
        with self.repo() as root:
            self.init_git(root)
            rel = (
                "history/conversations/"
                "2026-07-22-1200PDT-restored-legacy/handover.md"
            )
            handover = self.write(
                root,
                rel,
                "# Handover\n\n"
                "## Needs your attention\n\nLegacy prose.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add legacy handover")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete legacy handover")
            self.write(
                root,
                rel,
                "# Handover\n\n"
                "## Needs your attention\n\nLegacy prose.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "restore legacy handover")
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/README.md",
                "# Reviews\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection schema")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                findings = list(RECONCILE.check_handover_queue_projection())
            self.assertEqual([], findings, self.messages(findings))

    def test_root_range_governs_handover_restored_after_schema_activation(self):
        with self.repo() as root:
            self.init_git(root)
            rel = (
                "history/conversations/"
                "2026-07-22-1200PDT-restored-after-v1/handover.md"
            )
            handover = self.write(
                root,
                rel,
                "# Handover\n\n"
                "## Needs your attention\n\nLegacy prose.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add legacy handover")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete legacy handover")
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/README.md",
                "# Reviews\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection schema")
            self.write(
                root,
                rel,
                "# Handover\n\n"
                "## Needs your attention\n\nOrphan ask.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "restore after activation")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("Queue projection" in message
                                for message in messages))

    def test_range_governs_handover_deleted_and_readded_at_same_path(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-readded-in-range",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add governed handover")
            base = self.git(root, "rev-parse", "HEAD")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete handover")
            self.write(
                root,
                handover.relative_to(root),
                "# Handover\n\n"
                "## Needs your attention\n\nUnqueued human ask.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "readd unmarked handover")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("Queue projection" in message
                                for message in messages))

    def test_range_rejects_valid_v1_handover_readded_at_same_path(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-readded-valid-v1",
                "None.",
            )
            original = handover.read_text(encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add governed v1 handover")
            base = self.git(root, "rev-parse", "HEAD")

            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete governed v1 handover")

            self.write(
                root,
                handover.relative_to(root),
                original.replace("# Handover", "# Corrected handover"),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "readd altered valid v1 handover")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any(
                "reuses a path that already has a committed governed v1 "
                "handover incarnation" in message
                for message in messages
            ), messages)

    def test_staged_rejects_valid_v1_handover_readded_at_same_path(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-readded-valid-v1-staged",
                "None.",
            )
            original = handover.read_text(encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add governed v1 handover")

            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete governed v1 handover")

            self.write(
                root,
                handover.relative_to(root),
                original.replace("# Handover", "# Corrected handover"),
            )
            self.git(root, "add", ".")

            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any(
                "reuses a path that already has a committed governed v1 "
                "handover incarnation" in message
                for message in messages
            ), messages)

    def test_range_allows_deleting_v1_handover_without_reusing_path(self):
        with self.repo() as root:
            self.init_git(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-deleted-v1",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add governed v1 handover")
            base = self.git(root, "rev-parse", "HEAD")

            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete governed v1 handover")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual([], findings, self.messages(findings))

    def test_root_range_allows_reusing_pre_activation_v1_path(self):
        with self.repo() as root:
            self.init_git(root)
            rel = (
                "history/conversations/"
                "2026-07-22-1200PDT-pre-activation-v1/handover.md"
            )
            legacy = (
                "# Legacy handover\n\n"
                "**Queue projection:** v1\n\n"
                "## Needs your attention\n\nNone.\n\n"
                "## Next steps\n\nNone.\n"
            )
            handover = self.write(root, rel, legacy)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add pre-activation v1 handover")

            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete pre-activation handover")

            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/README.md",
                "# Reviews\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection schema")

            self.write(
                root,
                rel,
                legacy.replace("# Legacy handover", "# Governed handover"),
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "reuse legacy path after activation")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"root:{head}"
            ):
                findings = list(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertEqual([], findings, self.messages(findings))

    def test_parallel_history_rejects_reusing_governed_v1_path(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.write(
                root,
                "message-queue/needs-human/reviews/README.md",
                "# Reviews\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projection schema")
            common = self.git(root, "rev-parse", "HEAD")
            trunk = self.git(root, "branch", "--show-current")

            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-parallel-reuse",
                "None.",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add trunk v1 handover")
            handover.unlink()
            handover.parent.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "delete trunk v1 handover")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "feature", common)
            feature_handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-parallel-reuse",
                "None.",
            )
            feature_handover.write_text(
                feature_handover.read_text(encoding="utf-8").replace(
                    "# Handover", "# Parallel handover"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "reuse path on parallel branch")
            feature_head = self.git(root, "rev-parse", "HEAD")
            self.git(root, "merge", "--no-ff", trunk, "-m", "synthetic merge")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE,
                    "CHANGE_RANGE",
                    f"{base}...{feature_head}",
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "reuses a path that already has a committed governed v1 "
                "handover incarnation" in message
                for message in messages
            ), messages)

    def test_multi_commit_range_preserves_handover_before_schema_activation(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")

            self.make_handover(
                root,
                "2026-07-22-1200PDT-before-schema",
                "Legacy prose.",
                marker=None,
            )
            (root / "history/AGENTS.md").unlink()
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy history")

            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", "history/AGENTS.md")
            self.git(root, "commit", "-m", "activate projection schema")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                findings = list(RECONCILE.check_handover_queue_projection())
            self.assertEqual([], findings, self.messages(findings))

    def test_staged_handover_is_checked_after_worktree_copy_is_removed(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-index-only",
                "Unqueued human ask.",
                marker=None,
            )
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            handover.unlink()

            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any("Queue projection" in message
                                for message in messages))

    def test_staged_conversation_topology_is_checked_without_worktree_copy(self):
        with self.repo() as root:
            self.init_git(root)
            bad = self.write(
                root,
                "history/conversations/bad-name/handover.md",
                "# Handover\n",
            )
            incomplete = self.write(
                root,
                "history/conversations/"
                "2026-07-23-1200PDT-incomplete/artifact.md",
                "# Artifact\n",
            )
            self.git(root, "add", ".")
            bad.unlink()
            bad.parent.rmdir()
            incomplete.unlink()
            incomplete.parent.rmdir()

            messages = self.messages(RECONCILE.check_handover_present())
            self.assertTrue(any("folder name must be" in message
                                for message in messages))
            self.assertTrue(any("without handover.md" in message
                                for message in messages))

    def test_renamed_legacy_handover_is_new_at_destination(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            original = self.make_handover(
                root,
                "2026-07-22-1200PDT-old-name",
                "Orphan human ask.",
                marker=None,
            ).parent
            self.write(root, "message-queue/needs-human/reviews/README.md", "# Reviews\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "legacy")
            base = self.git(root, "rev-parse", "HEAD")

            renamed = original.with_name("2026-07-23-1200PDT-new-name")
            original.rename(renamed)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "rename conversation")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                messages = self.messages(
                    RECONCILE.check_handover_queue_projection()
                )
            self.assertTrue(any("Queue projection" in message
                                for message in messages))

    def test_new_handover_rejects_external_or_wrongly_relative_projection(self):
        for destination in (
            "https://example.test/message-queue/needs-human/reviews/"
            "future-blocking-review.md",
            "message-queue/needs-human/reviews/future-blocking-review.md",
        ):
            with self.subTest(destination=destination), self.repo() as root:
                queue_rel = (
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review.md"
                )
                self.write(root, queue_rel, "# Pending review\n")
                handover = self.make_handover(
                    root,
                    "2026-07-23-1200PDT-bad-target",
                    f"- [Review]({destination}) — decide later.",
                )
                with mock.patch.object(
                    RECONCILE,
                    "newly_added_handovers",
                    return_value=({handover.relative_to(root)}, None),
                ):
                    messages = self.messages(
                        RECONCILE.check_handover_queue_projection()
                    )
                self.assertTrue(any("unprefixed or invalid" in message
                                    for message in messages))

    def test_staged_handover_ignores_unstaged_projection_repair(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-review.md"
            )
            self.write(root, queue_rel, "# Pending review\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "queue contract")

            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-staged-snapshot",
                "None.",
            )
            self.git(root, "add", str(handover.relative_to(root)))
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "None.",
                    "- [Review](../../../"
                    f"{queue_rel}) — only in the working tree.",
                ),
                encoding="utf-8",
            )
            messages = self.messages(
                RECONCILE.check_handover_queue_projection()
            )
            self.assertTrue(any("says None." in message for message in messages))

    def test_handover_accepts_angle_destination_with_checkout_spaces(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-angle-link",
                "[Review](</tmp/My Checkout/message-queue/needs-human/reviews/"
                "future-blocking-review.md>)",
            )
            self.assertEqual([], list(RECONCILE.check_handover_queue_projection()))

    def test_main_caches_repeated_git_snapshot_reads(self):
        with self.repo() as root:
            self.init_git(root)
            tracked = self.write(root, "docs/design.md", "# Design\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add design")

            original_run = subprocess.run
            with mock.patch.object(
                RECONCILE.subprocess,
                "run",
                wraps=original_run,
            ) as run:
                RECONCILE.start_git_snapshot_cache()
                try:
                    for _ in range(3):
                        self.assertIn(
                            "docs/design.md",
                            RECONCILE.git_index_entries("docs"),
                        )
                        self.assertIn(
                            "docs/design.md",
                            RECONCILE.git_head_paths("docs"),
                        )
                        self.assertEqual(
                            b"# Design\n",
                            RECONCILE.repo_artifact_bytes(tracked),
                        )
                finally:
                    RECONCILE.stop_git_snapshot_cache()

            commands = [entry[0][0] for entry in run.call_args_list]
            self.assertEqual(
                1,
                sum(command[:3] == ["git", "ls-files", "--stage"]
                    for command in commands),
                commands,
            )
            self.assertEqual(
                1,
                sum(command[:5] == [
                    "git", "ls-tree", "-r", "--name-only", "-z"
                ] for command in commands),
                commands,
            )
            self.assertEqual(
                0,
                sum(command[:2] == ["git", "show"] for command in commands),
                commands,
            )

    def test_git_snapshot_cache_reads_captured_oid_after_index_changes(self):
        with self.repo() as root:
            self.init_git(root)
            tracked = self.write(root, "docs/design.md", "# Original\n")
            self.git(root, "add", ".")

            RECONCILE.start_git_snapshot_cache()
            try:
                tracked.write_text("# Replaced\n", encoding="utf-8")
                self.git(root, "add", ".")
                self.assertEqual(
                    b"# Original\n",
                    RECONCILE.repo_artifact_bytes(tracked),
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

            self.assertEqual(
                b"# Replaced\n",
                RECONCILE.repo_artifact_bytes(tracked),
            )

    def test_git_snapshot_cache_excludes_unmerged_index_stages(self):
        with self.repo() as root:
            self.init_git(root)
            records = (
                b"100644 " + b"1" * 40 + b" 0\tdocs/design.md\0"
                b"100644 " + b"2" * 40 + b" 1\tdocs/conflict.md\0"
                b"100644 " + b"3" * 40 + b" 2\tdocs/conflict.md\0"
                b"100644 " + b"4" * 40 + b" 3\tdocs/conflict.md\0"
            )

            def git_snapshot(command, **_kwargs):
                if command[:3] == ["git", "ls-files", "--stage"]:
                    return subprocess.CompletedProcess(
                        command, 0, stdout=records, stderr=b""
                    )
                if command[:3] == ["git", "rev-parse", "--verify"]:
                    return subprocess.CompletedProcess(
                        command, 1, stdout="", stderr=""
                    )
                return subprocess.CompletedProcess(
                    command, 0, stdout=b"", stderr=b""
                )

            with mock.patch.object(
                RECONCILE.subprocess, "run", side_effect=git_snapshot
            ):
                RECONCILE.start_git_snapshot_cache()
                try:
                    entries = RECONCILE.git_index_entries("docs")
                    self.assertEqual(
                        {"docs/design.md": "100644"},
                        entries,
                    )
                finally:
                    RECONCILE.stop_git_snapshot_cache()

    def test_main_fails_closed_when_index_snapshot_cannot_be_read(self):
        with self.repo() as root:
            self.init_git(root)
            original_run = subprocess.run

            def fail_index(command, **kwargs):
                if command[:3] == ["git", "ls-files", "--stage"]:
                    return subprocess.CompletedProcess(
                        command, 1, stdout=b"", stderr=b"index unavailable"
                    )
                return original_run(command, **kwargs)

            stderr = io.StringIO()
            with mock.patch.object(
                RECONCILE.subprocess, "run", side_effect=fail_index
            ), contextlib.redirect_stderr(stderr):
                result = RECONCILE.main(["--check"])

            self.assertEqual(2, result)
            self.assertIn("Git snapshot error: index unavailable", stderr.getvalue())

    def test_captured_blob_failure_never_falls_back_to_worktree(self):
        with self.repo() as root:
            self.init_git(root)
            tracked = self.write(root, "docs/design.md", "# Worktree\n")
            self.git(root, "add", ".")
            RECONCILE.start_git_snapshot_cache()
            try:
                oid = RECONCILE._GIT_INDEX_OID_CACHE["docs/design.md"]
                process = mock.Mock()
                process.stdin = io.BytesIO()
                process.stdout = io.BytesIO(
                    oid.encode("ascii") + b" missing\n"
                )
                process.wait.return_value = 0
                with mock.patch.object(
                    RECONCILE.subprocess,
                    "Popen",
                    return_value=process,
                ):
                    with self.assertRaises(RECONCILE.GitSnapshotError):
                        RECONCILE.repo_text(tracked)
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_historical_candidate_isolates_and_restores_merge_caches(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            worklog = task / "worklog.md"
            worklog.write_text(
                "# Worklog\n\nHistorical candidate.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "historical candidate")
            historical = self.git(root, "rev-parse", "HEAD")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "side")
            self.write(root, "side.md", "# Side\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "side candidate")
            side = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left candidate")
            self.git(root, "merge", "--no-ff", "--no-commit", "side")
            worklog.write_text(
                "# Worklog\n\nOuter staged candidate.\n",
                encoding="utf-8",
            )
            self.git(root, "add", str(worklog.relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                outer_parents = RECONCILE.staged_parent_oids()
                outer_side_commits = RECONCILE.staged_side_commits()
                self.assertEqual(side, outer_parents[1])
                self.assertIn(side, outer_side_commits)
                self.assertEqual(
                    side,
                    RECONCILE.staged_side_creation_commit("side.md"),
                )
                RECONCILE.git_tree_path_entry(side, "side.md")
                RECONCILE.revision_parents(side, "side parent")
                RECONCILE.task_admission_activation_commits(
                    RECONCILE._GIT_HEAD_OID
                )
                outer_task = RECONCILE.task_snapshot(
                    None, "2026-07-23-example"
                )
                self.assertIn(
                    "Outer staged candidate",
                    outer_task[1]["worklog.md"][1],
                )
                saved_caches = (
                    RECONCILE._GIT_STAGED_PARENTS_CACHE,
                    RECONCILE._GIT_STAGED_SIDE_COMMITS_CACHE,
                    RECONCILE._GIT_STAGED_SIDE_CREATION_CACHE,
                    RECONCILE._GIT_TREE_PATH_ENTRY_CACHE,
                    RECONCILE._GIT_REVISION_PARENTS_CACHE,
                    RECONCILE._GIT_SCHEMA_ACTIVATION_CACHE,
                    RECONCILE._TASK_SNAPSHOT_CACHE,
                )

                with RECONCILE.git_revision_candidate(
                    historical, preserve_change_range=True
                ):
                    self.assertEqual(
                        (historical,), RECONCILE.staged_parent_oids()
                    )
                    self.assertEqual((), RECONCILE.staged_side_commits())
                    self.assertIsNone(
                        RECONCILE.staged_side_creation_commit("side.md")
                    )
                    self.assertIsNone(
                        RECONCILE.candidate_path_entry(None, "side.md")
                    )
                    historical_task = RECONCILE.task_snapshot(
                        None, "2026-07-23-example"
                    )
                    self.assertIn(
                        "Historical candidate",
                        historical_task[1]["worklog.md"][1],
                    )
                    self.assertNotIn(
                        "Outer staged candidate",
                        historical_task[1]["worklog.md"][1],
                    )

                self.assertEqual(
                    outer_parents, RECONCILE.staged_parent_oids()
                )
                self.assertEqual(
                    outer_side_commits, RECONCILE.staged_side_commits()
                )
                for saved, restored in zip(saved_caches, (
                    RECONCILE._GIT_STAGED_PARENTS_CACHE,
                    RECONCILE._GIT_STAGED_SIDE_COMMITS_CACHE,
                    RECONCILE._GIT_STAGED_SIDE_CREATION_CACHE,
                    RECONCILE._GIT_TREE_PATH_ENTRY_CACHE,
                    RECONCILE._GIT_REVISION_PARENTS_CACHE,
                    RECONCILE._GIT_SCHEMA_ACTIVATION_CACHE,
                    RECONCILE._TASK_SNAPSHOT_CACHE,
                )):
                    self.assertIs(saved, restored)
                restored_task = RECONCILE.task_snapshot(
                    None, "2026-07-23-example"
                )
                self.assertIn(
                    "Outer staged candidate",
                    restored_task[1]["worklog.md"][1],
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_staged_handover_checks_share_one_captured_index_snapshot(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "history/AGENTS.md",
                "# History\n\n**Queue projection schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate schema")

            agent_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-captured.md"
            )
            self.write(root, agent_rel, "# Captured action\n")
            first = self.make_handover(
                root,
                "2026-07-23-1200PDT-captured",
                "None.",
            )
            first.write_text(
                first.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\n"
                    f"- [Continue](../../../{agent_rel}) — follow up.",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")

            RECONCILE.start_git_snapshot_cache()
            try:
                self.git(root, "rm", "--cached", agent_rel)
                later = self.make_handover(
                    root,
                    "2026-07-23-1300PDT-added-later",
                    "None.",
                )
                self.git(root, "add", str(later.relative_to(root)))

                first_rel = first.relative_to(root)
                added, error = RECONCILE.newly_added_handovers()
                self.assertIsNone(error)
                self.assertEqual({first_rel}, added)
                _text, _human, live_agent, state_error = (
                    RECONCILE.handover_creation_state(first, first_rel)
                )
                self.assertIsNone(state_error)
                self.assertEqual({agent_rel}, live_agent)
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_blocked_task_requires_live_reciprocal_blocker(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "blocking-unblock-example.md"
            )
            self.write(root, "docs/source.md", "# Source\n")
            blocker = self.write(
                root,
                queue_rel,
                "# Unblock\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** provide the missing artifact\n"
                "**Full context:** `docs/source.md`\n"
                "**Blocks now:** task:2026-07-23-example\n",
            )
            self.make_task(root, "2_blocked", "`" + queue_rel + "`")
            self.assertEqual([], list(RECONCILE.check_task_structure()))

            blocker.write_text(
                blocker.read_text(encoding="utf-8").replace(
                    "task:2026-07-23-example",
                    "task:2026-07-23-example-other",
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("reciprocal live blocking-*" in message
                                for message in messages))

    def test_committed_agent_claim_allows_blocked_task_to_resume(self):
        with self.repo() as root:
            self.init_git(root)
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "blocking-repair-example.md"
            )
            item = self.write(
                root,
                queue_rel,
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the dependency\n"
                "**Full context:** `tasks/AGENTS.md`\n"
                "**Blocks now:** task:2026-07-23-example\n",
            )
            task = self.make_task(
                root, "2_blocked", f"`{queue_rel}`"
            )
            self.write(root, "tasks/AGENTS.md", "# Tasks\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record stopped task")

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", queue_rel)
            self.git(root, "commit", "-m", "claim dependency repair")

            resumed = (
                root / "tasks/1_in-progress/2026-07-23-example"
            )
            resumed.parent.mkdir(parents=True)
            task.rename(resumed)
            self.git(root, "add", "-A")

            findings = list(RECONCILE.check_queue_task_reciprocity())
            self.assertEqual([], findings, self.messages(findings))

    def test_committed_human_folding_claim_allows_blocked_task_to_resume(self):
        with self.repo() as root:
            self.init_git(root)
            queue_rel = (
                "message-queue/needs-human/decisions/"
                "blocking-fold-example.md"
            )
            item = self.write(
                root,
                queue_rel,
                "# Decide\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** choose the dependency boundary\n"
                "**Full context:** `tasks/AGENTS.md`\n"
                "**Blocks now:** task:2026-07-23-example\n"
                "**Your answer:** use the repository boundary\n",
            )
            task = self.make_task(
                root, "2_blocked", f"`{queue_rel}`"
            )
            self.write(root, "tasks/AGENTS.md", "# Tasks\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record answered blocker")

            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", queue_rel)
            self.git(root, "commit", "-m", "claim answer folding")

            resumed = (
                root / "tasks/1_in-progress/2026-07-23-example"
            )
            resumed.parent.mkdir(parents=True)
            task.rename(resumed)
            self.git(root, "add", "-A")

            findings = list(RECONCILE.check_queue_task_reciprocity())
            self.assertEqual([], findings, self.messages(findings))

    def test_uncommitted_or_unanswered_claim_cannot_resume_blocked_task(self):
        cases = (
            ("needs-agent/requests", "open", "in-repair", "repair"),
            ("needs-human/decisions", "waiting", "folding", "fold"),
        )
        for endpoint, initial, active, slug in cases:
            with self.subTest(endpoint=endpoint), self.repo() as root:
                self.init_git(root)
                queue_rel = (
                    f"message-queue/{endpoint}/blocking-{slug}-example.md"
                )
                response = (
                    "**Your answer:** ______\n"
                    if endpoint.startswith("needs-human")
                    else ""
                )
                item = self.write(
                    root,
                    queue_rel,
                    "# Blocking action\n\n"
                    f"**Status:** {initial}\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** repair the dependency\n"
                    "**Full context:** `tasks/AGENTS.md`\n"
                    "**Blocks now:** task:2026-07-23-example\n"
                    + response,
                )
                task = self.make_task(
                    root, "2_blocked", f"`{queue_rel}`"
                )
                self.write(root, "tasks/AGENTS.md", "# Tasks\n")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "record stopped task")

                item.write_text(
                    item.read_text(encoding="utf-8").replace(
                        f"**Status:** {initial}",
                        f"**Status:** {active}",
                    ),
                    encoding="utf-8",
                )
                resumed = (
                    root / "tasks/1_in-progress/2026-07-23-example"
                )
                resumed.parent.mkdir(parents=True)
                task.rename(resumed)
                self.git(root, "add", "-A")

                messages = self.messages(
                    RECONCILE.check_queue_task_reciprocity()
                )
                self.assertTrue(any(
                    "committed active repair/folding claim" in message
                    for message in messages
                ), messages)

    def test_waiting_or_open_blocker_requires_blocked_task_status(self):
        cases = (
            ("needs-agent/requests", "open"),
            ("needs-human/decisions", "waiting"),
        )
        for endpoint, status in cases:
            with self.subTest(endpoint=endpoint), self.repo() as root:
                queue_rel = (
                    f"message-queue/{endpoint}/blocking-stop-example.md"
                )
                self.write(
                    root,
                    queue_rel,
                    "# Stop\n\n"
                    f"**Status:** {status}\n"
                    "**Filed:** 2026-07-23\n"
                    "**Action:** resolve the dependency\n"
                    "**Full context:** `tasks/AGENTS.md`\n"
                    "**Blocks now:** task:2026-07-23-example\n",
                )
                self.write(root, "tasks/AGENTS.md", "# Tasks\n")
                self.make_task(
                    root, "1_in-progress", f"`{queue_rel}`"
                )

                messages = self.messages(
                    RECONCILE.check_queue_task_reciprocity()
                )
                self.assertTrue(any(
                    "committed active repair/folding claim" in message
                    for message in messages
                ), messages)

    def test_backlog_task_requires_a_canonical_agent_pickup_request(self):
        with self.repo() as root:
            (root / "message-queue").mkdir()
            task = self.make_task(root, "0_backlog", "none")
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Claimed-by:** test", "**Claimed-by:** unclaimed"
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("canonical needs-agent request" in message
                                for message in messages))
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Claimed-by:** unclaimed", "**Claimed-by:** bypass"
                ),
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("backlog task must remain unclaimed" in message
                                for message in messages))
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Claimed-by:** bypass", "**Claimed-by:** unclaimed"
                ),
                encoding="utf-8",
            )

            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md"
            )
            self.write(
                root,
                queue_rel,
                "# Pick up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** claim the task\n"
                "**Full context:** "
                "`tasks/0_backlog/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n"
                "**If unanswered:** leave it in backlog\n",
            )
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Queue actions:** none",
                    f"**Queue actions:** `{queue_rel}`",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], list(RECONCILE.check_task_structure()))

    def test_task_queue_actions_field_has_closed_projection_syntax(self):
        first = (
            "message-queue/needs-human/reviews/"
            "non-blocking-review-first.md"
        )
        second = (
            "message-queue/needs-agent/requests/"
            "non-blocking-update-second.md"
        )
        accepted = (
            "none",
            f"`{first}`",
            f"`{first}`; `{second}`",
            f"`{first}`, `{second}`",
        )
        rejected = (
            f"none; `{first}`",
            f"`{first}`; please review it",
            f"`{first}`;",
            first,
            f"`{first}`; `{first}`",
        )

        for value in accepted:
            with self.subTest(accepted=value), self.repo() as root:
                self.write(
                    root,
                    first,
                    "# First\n\n"
                    "**Filed:** 2026-07-23, from task "
                    "`2026-07-23-example`\n",
                )
                self.write(root, second, "# Second\n")
                self.make_task(root, "1_in-progress", value)
                messages = self.messages(RECONCILE.check_task_structure())
                self.assertFalse(any(
                    "Queue actions" in message for message in messages
                ), messages)

        for value in rejected:
            with self.subTest(rejected=value), self.repo() as root:
                self.write(root, first, "# First\n")
                self.make_task(root, "1_in-progress", value)
                messages = self.messages(RECONCILE.check_task_structure())
                self.assertTrue(any(
                    "invalid **Queue actions:** projection" in message
                    for message in messages
                ), messages)

        with self.repo() as root:
            self.write(root, first, "# First\n")
            task = self.make_task(
                root, "1_in-progress", f"`{first}`"
            )
            task_md = task / "task.md"
            task_md.write_text(
                task_md.read_text(encoding="utf-8")
                + f"**Queue actions:** `{first}`\n",
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any(
                "exactly one **Queue actions:** field" in message
                for message in messages
            ), messages)

    def test_task_cannot_cross_its_future_start_boundary(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-start.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review\n"
                "**Full context:** `docs/source.md`\n"
                "**Blocks at:** transition:start task:2026-07-23-example\n"
                "**Until then:** leave the task in backlog\n"
                "## What you need to know\n\nReview before start.\n"
                "## Differences\n\nApprove starts; change revises.\n"
                "## Example\n\nOne starts; one waits.\n"
                "**Your review:** ______\n",
            )
            self.make_task(root, "1_in-progress", f"`{queue_rel}`")
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("crossed unresolved future-blocking boundary"
                                in message
                                for message in messages))

    def test_approved_review_authorizes_task_start_and_cleanup_after_receipt(
            self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            review_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-start.md"
            )
            pickup_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md"
            )
            review = self.write(
                root,
                review_rel,
                "# Review before start\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the exact design before task start\n"
                "**Full context:** `docs/source.md`\n"
                "**Why-you-might-care:** The task must not start unreviewed.\n"
                "**If-you-do-nothing:** The task remains in backlog.\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:start task:2026-07-23-example\n"
                "**Until then:** leave the task in backlog\n"
                "**Your review:** approve these exact bytes\n",
            )
            self.write(
                root,
                pickup_rel,
                "# Pick up task\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** claim the task\n"
                "**Full context:** "
                "`tasks/0_backlog/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n"
                "**If unanswered:** leave the task in backlog\n",
            )
            task = self.make_task(
                root,
                "0_backlog",
                f"`{review_rel}`; `{pickup_rel}`",
            )
            task_md = task / "task.md"
            task_md.write_text(
                task_md.read_text(encoding="utf-8").replace(
                    "**Claimed-by:** test", "**Claimed-by:** unclaimed"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record approved start review")

            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", review_rel)
            self.git(root, "commit", "-m", "claim approved review")

            active = (
                root / "tasks/1_in-progress/2026-07-23-example"
            )
            active.parent.mkdir(parents=True)
            task.rename(active)
            task_md = active / "task.md"
            task_md.write_text(
                task_md.read_text(encoding="utf-8").replace(
                    "**Claimed-by:** unclaimed", "**Claimed-by:** test"
                ).replace(
                    f"`{review_rel}`; `{pickup_rel}`",
                    f"`{review_rel}`",
                ),
                encoding="utf-8",
            )
            (active / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (active / "worklog.md").write_text("# Worklog\n", encoding="utf-8")
            (root / pickup_rel).unlink()
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                messages = self.messages(RECONCILE.check_task_structure())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertFalse(any(
                "crossed unresolved future-blocking boundary" in message
                for message in messages
            ), messages)
            self.git(root, "commit", "-m", "start task with review receipt")

            task_md.write_text(
                task_md.read_text(encoding="utf-8").replace(
                    f"`{review_rel}`", "none"
                ),
                encoding="utf-8",
            )
            review.unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_posthoc_approval_is_not_a_task_transition_receipt(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            review_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-start.md"
            )
            review = self.write(
                root,
                review_rel,
                "# Review filed too late\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the exact design before task start\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:start task:2026-07-23-example\n"
                "**Until then:** leave the task in backlog\n"
                "**Your review:** approve these exact bytes\n",
            )
            task = self.make_task(
                root, "1_in-progress", f"`{review_rel}`"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file posthoc review")
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", review_rel)
            self.git(root, "commit", "-m", "claim posthoc review")

            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    f"`{review_rel}`", "none"
                ),
                encoding="utf-8",
            )
            review.unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "committed task transition history" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_transition_receipt_cannot_be_reused_after_rollback(self):
        with self.repo() as root:
            self.init_git(root)
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            review_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-start.md"
            )
            review = self.write(
                root,
                review_rel,
                "# Review before start\n\n"
                "**Status:** waiting\n"
                "**Action:** approve before task start\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:start task:2026-07-23-example\n"
                "**Your review:** approved\n",
            )
            task = self.make_task(
                root, "0_backlog", f"`{review_rel}`"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record approval")
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", review_rel)
            self.git(root, "commit", "-m", "claim approval")
            active = root / "tasks/1_in-progress/2026-07-23-example"
            active.parent.mkdir(parents=True)
            task.rename(active)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "start with receipt")
            task.parent.mkdir(parents=True, exist_ok=True)
            active.rename(task)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "roll task back")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                problem = RECONCILE.task_transition_receipt_problem(
                    review_rel,
                    review.read_text(encoding="utf-8"),
                    head,
                    None,
                    {
                        "transition:start",
                        "task:2026-07-23-example",
                    },
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertIn("does not remain past transition:start", problem)

    def test_approved_completion_receipt_may_survive_crossing_commit(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            target = self.write(root, "docs/source.md", "# Reviewed\n")
            digest = "sha256:" + hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            review_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-complete.md"
            )
            review = self.write(
                root,
                review_rel,
                "# Review before completion\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** approve the exact completion evidence\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                f"**Reviewed revision:** {digest}\n"
                "**Review outcome:** approved\n"
                "**Blocks at:** transition:complete task:2026-07-23-example\n"
                "**Until then:** keep the task in review\n"
                "**Your review:** approve completion\n",
            )
            task = self.make_task(
                root, "3_in-review", f"`{review_rel}`"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record completion approval")
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "**Status:** waiting", "**Status:** folding"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", review_rel)
            self.git(root, "commit", "-m", "claim completion approval")
            done = root / "tasks/4_done/2026-07-23-example"
            done.parent.mkdir(parents=True)
            task.rename(done)
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                messages = self.messages(RECONCILE.check_task_structure())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertFalse(any(
                "done task must declare" in message for message in messages
            ), messages)
            self.git(root, "commit", "-m", "complete with review receipt")

            (done / "task.md").write_text(
                (done / "task.md").read_text(encoding="utf-8").replace(
                    f"`{review_rel}`", "none"
                ),
                encoding="utf-8",
            )
            review.unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_queue_resolution())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_task_cannot_cross_linked_immediate_transition_boundary(self):
        with self.repo() as root:
            self.write(root, "tasks/AGENTS.md", "# Tasks\n")
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "blocking-before-start.md"
            )
            self.write(
                root,
                queue_rel,
                "# Repair before start\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** repair the prerequisite\n"
                "**Full context:** `tasks/AGENTS.md`\n"
                "**Blocks now:** transition:start\n",
            )
            self.make_task(root, "1_in-progress", f"`{queue_rel}`")

            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("crossed unresolved blocking boundary"
                                in message for message in messages))

    def test_queue_item_naming_task_requires_reciprocal_task_link(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "future-blocking-before-start.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                "**Blocks at:** transition:start task:2026-07-23-example\n"
                "**Until then:** leave the task in backlog\n"
                "## What you need to know\n\nReview before start.\n"
                "## Differences\n\nApprove starts; change revises.\n"
                "## Example\n\nOne starts; one waits.\n"
                "**Your review:** ______\n",
            )
            self.make_task(root, "0_backlog", "none")
            messages = self.messages(RECONCILE.check_queue_task_reciprocity())
            self.assertTrue(any("does not link this live queue action" in message
                                for message in messages))

    def test_nonblocking_task_token_requires_reciprocal_task_link(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-inspect-example.md",
                "# Inspect\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect task:2026-07-23-example\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave the task unchanged\n",
            )
            self.make_task(root, "1_in-progress", "none")
            messages = self.messages(
                RECONCILE.check_queue_task_reciprocity()
            )
            self.assertTrue(any("does not link this live queue action" in message
                                for message in messages))

    def test_pickup_request_cannot_survive_task_claim(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-pick-up-example.md"
            )
            task = self.make_task(root, "1_in-progress", f"`{queue_rel}`")
            self.write(
                root,
                queue_rel,
                "# Pick up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** claim the task\n"
                "**Full context:** "
                "`tasks/1_in-progress/2026-07-23-example/task.md`\n"
                "**Request kind:** task-pickup\n"
                "**If unanswered:** leave it unclaimed\n",
            )
            messages = self.messages(RECONCILE.check_queue_task_reciprocity())
            self.assertTrue(any("pickup request remains live" in message
                                for message in messages))
            self.assertTrue(task.is_dir())

    def test_nonpickup_request_must_not_link_status_dependent_task_path(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-follow-up-example.md"
            )
            self.make_task(root, "1_in-progress", f"`{queue_rel}`")
            self.write(
                root,
                queue_rel,
                "# Follow up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the task evidence\n"
                "**Full context:** "
                "`tasks/1_in-progress/2026-07-23-example/task.md`\n"
                "**If unanswered:** leave the current task plan unchanged\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("status-dependent task path" in message
                                for message in messages))

    def test_nonpickup_request_rejects_plain_moving_task_path_in_body(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Stable source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "non-blocking-follow-up-example.md",
                "# Follow up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the task evidence\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave the source unchanged\n\n"
                "Inspect tasks/1_in-progress/2026-07-23-example/task.md.\n",
            )
            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("status-dependent task path" in message
                                for message in messages))

    def test_generated_retry_may_quote_broken_moving_task_path(self):
        with self.repo() as root:
            finding = RECONCILE.Finding(
                "task-structure",
                "tasks/1_in-progress/2026-07-23-example/task.md",
                "missing plan.md",
                "copy templates/task/plan.md",
            )
            self.write(
                root,
                "message-queue/needs-agent/retries/"
                "blocking-reconcile-task-structure-example.md",
                RECONCILE.retry_text(finding),
            )

            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertFalse(any("status-dependent task path" in message
                                 for message in messages))

    def test_staged_queue_item_is_checked_after_worktree_copy_is_removed(self):
        with self.repo() as root:
            self.init_git(root)
            item = self.write(
                root,
                "message-queue/needs-agent/requests/non-blocking-index-only.md",
                "# Missing schema\n",
            )
            self.git(root, "add", ".")
            item.unlink()

            messages = self.messages(RECONCILE.check_queue_schema())
            self.assertTrue(any("missing required field" in message
                                for message in messages))

    def test_link_check_uses_staged_markdown_not_unstaged_repair(self):
        with self.repo() as root:
            self.init_git(root)
            source = self.write(
                root,
                "docs/source.md",
                "Broken target: `missing/target.md`\n",
            )
            self.git(root, "add", ".")
            source.write_text("# Unstaged repair\n", encoding="utf-8")

            messages = self.messages(RECONCILE.check_links())
            self.assertTrue(any("missing/target.md" in message
                                for message in messages))

    def test_link_check_allows_predeclared_future_resolution_evidence(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-human/reviews/non-blocking-review.md",
                "# Review\n\n"
                "**Status:** awaiting-artifact\n"
                "**Filed:** 2026-07-23, by test\n"
                "**Action:** Review the source.\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** "
                "`memory/decisions/future-disposition.md`\n"
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
                "**If unanswered:** The source remains unchanged.\n",
            )

            self.assertEqual([], list(RECONCILE.check_links()))

    def test_link_check_allows_queue_lifecycle_lineage_paths(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-human/reviews/"
                "future-blocking-review-revision.md",
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-24, by test\n"
                "**Action:** Review the source.\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** "
                "`memory/decisions/future-disposition.md`\n"
                "**Successor action:** "
                "`message-queue/needs-agent/requests/"
                "future-blocking-future-repair.md`\n"
                "**Follow-up review:** "
                "`message-queue/needs-human/reviews/"
                "future-blocking-future-review.md`\n"
                "**Supersedes:** "
                "`message-queue/needs-human/reviews/"
                "future-blocking-prior-review.md`\n"
                "**Depends on:** "
                "`message-queue/needs-agent/requests/"
                "future-blocking-completed-repair.md`\n",
            )

            self.assertEqual([], list(RECONCILE.check_links()))

    def test_link_check_still_rejects_unrelated_missing_queue_path(self):
        with self.repo() as root:
            self.write(root, "docs/source.md", "# Source\n")
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "future-blocking-repair.md",
                "# Repair\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-24, by test\n"
                "**Action:** Repair the source.\n"
                "**Full context:** `docs/source.md`\n"
                "**Resolution evidence:** `docs/future-result.md`\n"
                "**Supersedes:** "
                "`message-queue/needs-human/reviews/"
                "future-blocking-prior-review.md`\n\n"
                "Ordinary evidence: `docs/missing-evidence.md`\n",
            )

            messages = self.messages(RECONCILE.check_links())
            self.assertEqual(1, len(messages), messages)
            self.assertIn("docs/missing-evidence.md", messages[0])

    def test_explicit_transition_gate_scopes_task_or_checks_all(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/future-blocking-before-merge.md",
                "**Blocks at:** transition:merge task:2026-07-23-example\n",
            )
            self.write(
                root,
                "message-queue/needs-agent/requests/"
                "future-blocking-before-other-merge.md",
                "**Blocks at:** transition:merge task:2026-07-23-other\n",
            )
            with mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS={"merge"},
                ACTIVE_TASK_ID="2026-07-23-example",
            ):
                findings = list(RECONCILE.check_active_queue_boundaries())
                self.assertEqual(1, len(findings))
                self.assertIn("before-merge.md", str(findings[0].subject))
            with mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS={"merge"},
                ACTIVE_TASK_ID="2026-07-23-unrelated",
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_active_queue_boundaries())
                )
            with mock.patch.multiple(
                RECONCILE, ACTIVE_TRANSITIONS={"merge"}, ACTIVE_TASK_ID=None
            ):
                self.assertEqual(
                    2, len(list(RECONCILE.check_active_queue_boundaries()))
                )
            with mock.patch.multiple(
                RECONCILE, ACTIVE_TRANSITIONS={"merge"}, ACTIVE_TASK_ID=""
            ):
                self.assertEqual(
                    [], list(RECONCILE.check_active_queue_boundaries())
                )
            with mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS={"merge"},
                ACTIVE_TASK_ID=frozenset({"2026-07-23-example"}),
            ):
                self.assertEqual(
                    1, len(list(RECONCILE.check_active_queue_boundaries()))
                )

    def test_immediate_task_blocker_stops_scoped_external_transition(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/requests/blocking-unblock-task.md",
                "**Blocks now:** task:2026-07-23-example\n",
            )
            with mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS={"merge"},
                ACTIVE_TASK_ID="2026-07-23-example",
            ):
                findings = list(RECONCILE.check_active_queue_boundaries())
            self.assertEqual(1, len(findings))
            self.assertIn("transition:merge", findings[0].message)

    def test_immediate_blocker_stops_its_named_external_transition(self):
        with self.repo() as root:
            self.write(
                root,
                "message-queue/needs-agent/retries/"
                "blocking-repository-admission.md",
                "**Blocks now:** transition:repository-admission\n",
            )
            with mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS={"repository-admission"},
                ACTIVE_TASK_ID="",
            ):
                findings = list(RECONCILE.check_active_queue_boundaries())
            self.assertEqual(1, len(findings))
            self.assertIn("unresolved blocking action", findings[0].message)

    def test_transition_cli_accepts_task_branch_id(self):
        with self.repo(), mock.patch.dict(
            RECONCILE.CHECKS, {}, clear=True
        ), mock.patch.multiple(
            RECONCILE, ACTIVE_TRANSITIONS=set(), ACTIVE_TASK_ID=None
        ):
            self.assertEqual(
                0,
                RECONCILE.main([
                    "--check",
                    "--at-transition", "merge",
                    "--task-id", "task/2026-07-23-example",
                ]),
            )
            self.assertEqual("2026-07-23-example", RECONCILE.ACTIVE_TASK_ID)

    def test_transition_cli_marks_non_task_branch_as_unscoped(self):
        with self.repo(), mock.patch.dict(
            RECONCILE.CHECKS, {}, clear=True
        ), mock.patch.multiple(
            RECONCILE, ACTIVE_TRANSITIONS=set(), ACTIVE_TASK_ID=None
        ):
            self.assertEqual(
                0,
                RECONCILE.main([
                    "--check",
                    "--at-transition", "merge",
                    "--branch", "fix/readme-typo",
                ]),
            )
            self.assertEqual("", RECONCILE.ACTIVE_TASK_ID)

    def test_non_task_branch_infers_scope_from_range_task_evidence(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(
                root,
                "commit",
                "-m",
                "implement service change",
                "-m",
                "task: 2026-07-23-example",
            )
            head = self.git(root, "rev-parse", "HEAD")

            self.assertEqual(
                {"2026-07-23-example"},
                RECONCILE.task_ids_from_change_range(f"{base}...{head}"),
            )

            with mock.patch.dict(
                RECONCILE.CHECKS, {}, clear=True
            ), mock.patch.multiple(
                RECONCILE,
                ACTIVE_TRANSITIONS=set(),
                ACTIVE_TASK_ID=None,
                CHANGE_RANGE=None,
            ):
                self.assertEqual(
                    0,
                    RECONCILE.main([
                        "--check",
                        "--at-transition", "merge",
                        "--branch", "fix/wrong-name",
                        "--range", f"{base}...{head}",
                    ]),
                )
                self.assertEqual(
                    frozenset({"2026-07-23-example"}),
                    RECONCILE.ACTIVE_TASK_ID,
                )

    def test_range_rejects_checkout_that_is_not_head_or_synthetic_merge(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "README.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "--detach", base)

            stderr = io.StringIO()
            with mock.patch.dict(
                RECONCILE.CHECKS, {}, clear=True
            ), contextlib.redirect_stderr(stderr):
                result = RECONCILE.main([
                    "--check",
                    "--range", f"{base}...{head}",
                ])

            self.assertEqual(2, result)
            self.assertIn(
                "neither the --range head nor an exact base+head synthetic merge",
                stderr.getvalue(),
            )

    def test_range_accepts_exact_synthetic_merge_candidate(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Common\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "feature")
            self.write(root, "feature.md", "# Feature\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "feature")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", trunk)
            self.write(root, "base.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "feature")
            self.git(root, "merge", "--no-ff", trunk, "-m", "synthetic merge")

            with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                self.assertEqual(
                    0,
                    RECONCILE.main([
                        "--check",
                        "--range", f"{base}...{head}",
                    ]),
                )

    def test_range_accepts_direct_head_and_root_head_only(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "README.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")

            with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                self.assertEqual(
                    0,
                    RECONCILE.main(["--check", "--range", f"{base}...{head}"]),
                )
                self.assertEqual(
                    0,
                    RECONCILE.main(["--check", "--range", f"root:{head}"]),
                )
                self.git(root, "checkout", "--detach", base)
                self.assertEqual(
                    2,
                    RECONCILE.main(["--check", "--range", f"root:{head}"]),
                )

    def test_range_rejects_staged_intent_unstaged_and_untracked_deltas(self):
        cases = ("intent", "unstaged", "untracked")
        for case in cases:
            with self.subTest(case=case), self.repo() as root:
                self.init_git(root)
                tracked = self.write(root, "README.md", "# Base\n")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "base")
                base = self.git(root, "rev-parse", "HEAD")
                tracked.write_text("# Head\n", encoding="utf-8")
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "head")
                head = self.git(root, "rev-parse", "HEAD")

                if case == "intent":
                    self.write(root, "intent.md", "# Intent\n")
                    self.git(root, "add", "-N", "intent.md")
                elif case == "unstaged":
                    tracked.write_text("# Unstaged\n", encoding="utf-8")
                else:
                    self.write(root, "untracked.md", "# Untracked\n")

                with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                    self.assertEqual(
                        2,
                        RECONCILE.main([
                            "--check", "--range", f"{base}...{head}"
                        ]),
                    )

    def test_range_rejects_octopus_candidate(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Common\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "common")
            common = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "range-head")
            self.write(root, "head.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "-b", "side-extra", common)
            self.write(root, "extra.md", "# Extra\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "extra")

            self.git(root, "checkout", "-b", "range-base", common)
            self.write(root, "base.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.git(
                root,
                "merge", "--no-ff", "range-head", "side-extra", "-m", "octopus",
            )

            with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                self.assertEqual(
                    2,
                    RECONCILE.main([
                        "--check", "--range", f"{base}...{head}"
                    ]),
                )

    def test_range_rejects_disconnected_base(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Head history\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")

            self.git(root, "checkout", "--orphan", "other")
            self.git(root, "rm", "-rf", ".")
            self.write(root, "other.md", "# Other\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "other")
            base = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "--detach", head)

            with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                self.assertEqual(
                    2,
                    RECONCILE.main([
                        "--check", "--range", f"{base}...{head}"
                    ]),
                )

    def test_displaced_tip_validation_fails_closed(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "README.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            change_range = f"{base}...{head}"

            RECONCILE.validate_displaced_tip(base, change_range)
            with self.assertRaises(RECONCILE.GitSnapshotError):
                RECONCILE.validate_displaced_tip("a" * 40, change_range)

            tree = self.git(root, "rev-parse", "HEAD^{tree}")
            disconnected = self.git(
                root, "commit-tree", tree, "-m", "disconnected"
            )
            with self.assertRaises(RECONCILE.GitSnapshotError):
                RECONCILE.validate_displaced_tip(
                    disconnected, change_range
                )

    def test_range_allows_repository_ignored_generated_file(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, ".gitignore", "generated.md\n")
            self.write(root, "README.md", "# Base\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.write(root, "README.md", "# Head\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "head")
            head = self.git(root, "rev-parse", "HEAD")
            self.write(root, "generated.md", "# Ignored\n")

            with mock.patch.dict(RECONCILE.CHECKS, {}, clear=True):
                self.assertEqual(
                    0,
                    RECONCILE.main([
                        "--check", "--range", f"{base}...{head}"
                    ]),
                )

    def test_task_queue_paths_must_be_live_and_done_tasks_must_use_none(self):
        with self.repo() as root:
            (root / "message-queue").mkdir()
            missing = (
                "message-queue/needs-human/reviews/"
                "non-blocking-missing.md"
            )
            self.make_task(root, "4_done", "`" + missing + "`")
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("is not in the Git index" in message
                                for message in messages))
            self.assertTrue(any("done task must declare" in message for message in messages))

    def test_staged_task_cannot_link_untracked_queue_item(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", "docs/source.md")
            self.git(root, "commit", "-m", "base")
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-untracked.md"
            )
            self.write(
                root,
                queue_rel,
                "# Follow up\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** inspect the source\n"
                "**Full context:** `docs/source.md`\n"
                "**If unanswered:** leave it unchanged\n",
            )
            task = self.make_task(root, "1_in-progress", f"`{queue_rel}`")
            self.git(root, "add", str(task.relative_to(root)))

            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("is not in the Git index" in message
                                for message in messages))

    def test_staged_task_is_checked_after_worktree_directory_is_removed(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "message-queue/AGENTS.md", "# Queue\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            task = self.make_task(root, "2_blocked", "none")
            self.git(root, "add", str(task.relative_to(root)))
            for child in task.iterdir():
                child.unlink()
            task.rmdir()

            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("reciprocal live blocking-*" in message
                                for message in messages))

    def test_staged_invalid_status_and_loose_task_file_are_checked(self):
        with self.repo() as root:
            self.init_git(root)
            invalid = self.write(
                root,
                "tasks/not-a-status/2026-07-23-example/task.md",
                "# Task\n",
            )
            loose = self.write(
                root,
                "tasks/1_in-progress/loose.md",
                "# Loose\n",
            )
            self.git(root, "add", ".")
            invalid.unlink()
            invalid.parent.rmdir()
            invalid.parent.parent.rmdir()
            loose.unlink()
            loose.parent.rmdir()

            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("not a valid status folder" in message
                                for message in messages))
            self.assertTrue(any("loose file in a status folder" in message
                                for message in messages))

    def test_staged_task_move_uses_index_status_not_worktree_status(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "message-queue/AGENTS.md", "# Queue\n")
            target_digest = hashlib.sha256(b"# Queue\n").hexdigest()
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-review.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review before task review\n"
                "**Full context:** `message-queue/AGENTS.md`\n"
                "**Review target:** `message-queue/AGENTS.md`\n"
                f"**Review revision:** sha256:{target_digest}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks at:** transition:review task:2026-07-23-example\n"
                "**Until then:** keep implementing\n\n"
                "## What you need to know\n\nReview before transition.\n\n"
                "## Differences\n\nApprove advances; changes keep work active.\n\n"
                "## Example\n\nOne enters review; one does not.\n\n"
                "**Your review:** ______\n",
            )
            task = self.make_task(root, "1_in-progress", f"`{queue_rel}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")

            staged = task.parent.parent / "3_in-review" / task.name
            staged.parent.mkdir(parents=True)
            task.rename(staged)
            (staged / "verification.md").write_text(
                "# Verification\n", encoding="utf-8"
            )
            self.git(root, "add", "-A")
            task.parent.mkdir(parents=True, exist_ok=True)
            staged.rename(task)

            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("crossed unresolved future-blocking boundary"
                                in message
                                for message in messages))

    def test_task_admission_rejects_intermediate_crossing_then_revert(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.write(root, "docs/source.md", "# Source\n")
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "future-blocking-before-review.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review before task review\n\n"
                "**Status:** waiting\n"
                "**Filed:** 2026-07-23\n"
                "**Action:** review before the task enters review\n"
                "**Full context:** `docs/source.md`\n"
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** sha256:{'a' * 64}\n"
                "**Reviewed revision:** ______\n"
                "**Review outcome:** pending\n"
                "**Blocks at:** transition:review task:2026-07-23-example\n"
                "**Until then:** keep implementing\n"
                "**Your review:** ______\n",
            )
            task = self.make_task(
                root, "1_in-progress", f"`{queue_rel}`"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")

            review_task = (
                root / "tasks/3_in-review/2026-07-23-example"
            )
            review_task.parent.mkdir(parents=True)
            task.rename(review_task)
            (review_task / "verification.md").write_text(
                "# Verification\n", encoding="utf-8"
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "cross review boundary")

            task.parent.mkdir(parents=True, exist_ok=True)
            review_task.rename(task)
            (task / "verification.md").unlink()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "revert task status")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_admission_history()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "crossed unresolved future-blocking boundary" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_admission_marker_is_sticky_while_tasks_remain(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            contract.write_text("# Tasks\n", encoding="utf-8")
            self.git(root, "add", "tasks/AGENTS.md")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_admission_history())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "removed after activation" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_admission_rejects_intermediate_marker_removal(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            contract.write_text("# Tasks\n", encoding="utf-8")
            self.git(root, "add", "tasks/AGENTS.md")
            self.git(root, "commit", "-m", "remove task admission")
            contract.write_text(
                "**Task admission schema:** v1\n", encoding="utf-8"
            )
            self.git(root, "add", "tasks/AGENTS.md")
            self.git(root, "commit", "-m", "restore task admission")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_admission_history()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "removed Task admission schema v1" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_rejects_staged_owner_ask(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            design = self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\nThe current design is deterministic.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            design.write_text(
                design.read_text(encoding="utf-8")
                + "\n## Pending owner action\n\n"
                "Owner, please choose whether this task may merge.\n",
                encoding="utf-8",
            )
            self.git(root, "add", str(design.relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual(1, len(findings), self.messages(findings))
            self.assertIn("Owner, please choose", findings[0].message)

    def test_task_action_origin_uses_all_staged_merge_parents(self):
        with self.repo() as root:
            self.init_git(root)
            task = self.make_task(root, "1_in-progress", "none")
            worklog = task / "worklog.md"
            worklog.write_text(
                "# Worklog\n\nOwner, review the existing release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "record legacy task prose")
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "documented")
            self.write(root, "right.md", "# Right\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "right work")

            self.git(root, "checkout", trunk)
            worklog.write_text(
                "# Worklog\n\nNo pending action.\n", encoding="utf-8"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "remove legacy prose")
            self.git(root, "merge", "--no-ff", "--no-commit", "documented")
            self.git(
                root,
                "restore",
                "--source=documented",
                "--staged",
                "--worktree",
                "--",
                str(worklog.relative_to(root)),
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

            worklog.write_text(
                worklog.read_text(encoding="utf-8")
                + "\nOwner, approve the newly staged release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", str(worklog.relative_to(root)))
            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, approve the newly staged release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_rechecks_invalid_side_history(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "-b", "invalid-task-history")
            worklog = task / "worklog.md"
            worklog.write_text(
                "# Worklog\n\nOwner, approve the unqueued side release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add unqueued side ask")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            self.git(
                root,
                "merge",
                "--no-ff",
                "--no-commit",
                "invalid-task-history",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, approve the unqueued side release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_rechecks_imported_orphan_root(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            trunk = self.git(root, "branch", "--show-current")

            self.git(root, "checkout", "--orphan", "invalid-root")
            self.git(root, "rm", "-rf", ".")
            task = self.make_task(root, "1_in-progress", "none")
            (task / "worklog.md").write_text(
                "# Worklog\n\n"
                "Owner, approve the unqueued root release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "invalid task root")

            self.git(root, "checkout", trunk)
            self.git(
                root,
                "merge",
                "--allow-unrelated-histories",
                "--no-ff",
                "--no-commit",
                "invalid-root",
            )

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, approve the unqueued root release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_scans_extra_nested_markdown(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            question = self.write(
                root,
                task.relative_to(root) / "notes/questions.md",
                "# Questions\n\nOwner, review the release.\n",
            )
            self.git(root, "add", str(question.relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, review the release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_accepts_exact_task_owned_projection(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            design = self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\nNo pending human action.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "non-blocking-review-rollout.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review rollout\n\n"
                "**Filed:** 2026-07-23, from task "
                "`2026-07-23-example`\n"
                "**Action:** Review the rollout boundary.\n",
            )
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Queue actions:** none",
                    f"**Queue actions:** `{queue_rel}`",
                ),
                encoding="utf-8",
            )
            design.write_text(
                "# Design\n\n"
                "[Review the rollout boundary.]"
                f"(../../../{queue_rel})\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_task_action_origin_rejects_intermediate_ask_then_delete(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            design = self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\nThe current design is deterministic.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            original = design.read_text(encoding="utf-8")
            design.write_text(
                original + "\nPlease approve the release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "add orphan owner ask")
            design.write_text(original, encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "remove orphan owner ask")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Please approve the release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_survives_whole_task_service_deletion(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            design = self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\nNo pending action.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            design.write_text(
                "# Design\n\nOwner, approve the release.\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "introduce owner ask")
            tasks = root / "tasks"
            for path in sorted(
                tasks.rglob("*"),
                key=lambda candidate: len(candidate.parts),
                reverse=True,
            ):
                path.unlink() if path.is_file() else path.rmdir()
            tasks.rmdir()
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "remove task service")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_action_origin()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, approve the release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_checks_root_activation_commit(self):
        with self.repo() as root, mock.patch.object(
            RECONCILE, "CHANGE_RANGE", None
        ):
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\nPlease approve the initial release.\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "root task state")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"root:{head}"
                ):
                    findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Please approve the initial release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_removing_task_projection_ownership_reintroduces_the_ask(self):
        with self.repo() as root:
            self.init_git(root)
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "non-blocking-review-rollout.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review rollout\n\n"
                "**Filed:** 2026-07-23, from task "
                "`2026-07-23-example`\n"
                "**Action:** Review the rollout boundary.\n",
            )
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(
                root, "1_in-progress", f"`{queue_rel}`"
            )
            self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\n"
                "[Review the rollout boundary.]"
                f"(../../../{queue_rel})\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projected task action")
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    f"**Queue actions:** `{queue_rel}`",
                    "**Queue actions:** none",
                ),
                encoding="utf-8",
            )
            self.git(root, "add", str((task / "task.md").relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Review the rollout boundary" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_scans_dot_markdown_artifacts(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            question = self.write(
                root,
                task.relative_to(root) / "notes/questions.markdown",
                "# Questions\n\nOwner, review the release.\n",
            )
            self.git(root, "add", str(question.relative_to(root)))

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Owner, review the release" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_action_origin_aggregates_across_artifact_renames(self):
        with self.repo() as root:
            self.init_git(root)
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "non-blocking-review-rollout.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review rollout\n\n"
                "**Filed:** 2026-07-23, from task "
                "`2026-07-23-example`\n"
                "**Action:** Review the rollout boundary.\n",
            )
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(
                root, "1_in-progress", f"`{queue_rel}`"
            )
            design = self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\n"
                "[Review the rollout boundary.]"
                f"(../../../{queue_rel})\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate projected task action")
            renamed = design.with_name("proposal.md")
            design.rename(renamed)
            self.git(root, "add", "-A")

            RECONCILE.start_git_snapshot_cache()
            try:
                findings = list(RECONCILE.check_task_action_origin())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertEqual([], findings, self.messages(findings))

    def test_task_projection_rejects_queue_owned_by_another_task(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            queue_rel = (
                "message-queue/needs-human/reviews/"
                "non-blocking-review-rollout.md"
            )
            self.write(
                root,
                queue_rel,
                "# Review rollout\n\n"
                "**Filed:** 2026-07-23, from task "
                "`2026-07-23-somewhere-else`\n"
                "**Action:** Review the rollout boundary.\n",
            )
            (task / "task.md").write_text(
                (task / "task.md").read_text(encoding="utf-8").replace(
                    "**Queue actions:** none",
                    f"**Queue actions:** `{queue_rel}`",
                ),
                encoding="utf-8",
            )
            self.write(
                root,
                task.relative_to(root) / "design.md",
                "# Design\n\n"
                "[Review the rollout boundary.]"
                f"(../../../{queue_rel})\n",
            )
            self.git(root, "add", ".")

            RECONCILE.start_git_snapshot_cache()
            try:
                origin = list(RECONCILE.check_task_action_origin())
                structure = list(RECONCILE.check_task_structure())
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "Invalid human-action projection" in finding.message
                for finding in origin
            ), self.messages(origin))
            self.assertTrue(any(
                "is not owned by task:2026-07-23-example" in finding.message
                for finding in structure
            ), self.messages(structure))

    def test_task_admission_marker_removal_is_historical_with_only_readme(self):
        with self.repo() as root:
            self.init_git(root)
            contract = self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.write(root, "tasks/README.md", "# Tasks\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            contract.write_text("# Tasks\n", encoding="utf-8")
            self.git(root, "add", "tasks/AGENTS.md")
            self.git(root, "commit", "-m", "remove task admission")
            contract.write_text(
                "**Task admission schema:** v1\n", encoding="utf-8"
            )
            self.git(root, "add", "tasks/AGENTS.md")
            self.git(root, "commit", "-m", "restore task admission")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_admission_history()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "removed Task admission schema v1" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_admission_rejects_active_deletion_but_allows_archival(self):
        for status, rejected in (
            ("0_backlog", False),
            ("1_in-progress", True),
            ("3_in-review", True),
            ("4_done", False),
        ):
            with self.subTest(status=status), self.repo() as root:
                self.init_git(root)
                self.write(
                    root,
                    "tasks/AGENTS.md",
                    "**Task admission schema:** v1\n",
                )
                task = self.make_task(root, status, "none")
                if status == "0_backlog":
                    task_md = task / "task.md"
                    task_md.write_text(
                        task_md.read_text(encoding="utf-8").replace(
                            "**Claimed-by:** test",
                            "**Claimed-by:** unclaimed",
                        ),
                        encoding="utf-8",
                    )
                self.git(root, "add", ".")
                self.git(root, "commit", "-m", "activate task admission")
                base = self.git(root, "rev-parse", "HEAD")
                for path in sorted(
                    task.rglob("*"),
                    key=lambda candidate: len(candidate.parts),
                    reverse=True,
                ):
                    path.unlink() if path.is_file() else path.rmdir()
                task.rmdir()
                self.git(root, "add", "-A")
                self.git(root, "commit", "-m", "remove task")
                head = self.git(root, "rev-parse", "HEAD")

                RECONCILE.start_git_snapshot_cache()
                try:
                    with mock.patch.object(
                        RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                    ):
                        findings = list(
                            RECONCILE.check_task_admission_history()
                        )
                finally:
                    RECONCILE.stop_git_snapshot_cache()
                active_deletion = any(
                    "active task:2026-07-23-example was deleted"
                    in finding.message
                    for finding in findings
                )
                self.assertEqual(
                    rejected, active_deletion, self.messages(findings)
                )

    def test_task_admission_rejects_task_id_rename(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            renamed = task.with_name("2026-07-23-renamed")
            task.rename(renamed)
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "rename task id")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_admission_history()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "task id changed from 2026-07-23-example to "
                "2026-07-23-renamed" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_task_admission_rejects_illegal_lifecycle_jump(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            task = self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "activate task admission")
            base = self.git(root, "rev-parse", "HEAD")
            done = task.parent.parent / "4_done" / task.name
            done.parent.mkdir(parents=True)
            task.rename(done)
            (done / "verification.md").write_text(
                "# Verification\n", encoding="utf-8"
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "skip task review")
            head = self.git(root, "rev-parse", "HEAD")

            RECONCILE.start_git_snapshot_cache()
            try:
                with mock.patch.object(
                    RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
                ):
                    findings = list(
                        RECONCILE.check_task_admission_history()
                    )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.assertTrue(any(
                "jumped from 1_in-progress to 4_done" in finding.message
                for finding in findings
            ), self.messages(findings))

    def test_duplicate_task_id_across_status_folders_is_rejected(self):
        with self.repo() as root:
            self.make_task(root, "1_in-progress", "none")
            self.make_task(root, "2_blocked", "none")
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("exists in multiple status folders" in message
                                for message in messages))

    def test_task_id_validation_uses_the_whole_folder_name(self):
        with self.repo() as root:
            task = root / "tasks/0_backlog/2026-07-23-example.invalid"
            task.mkdir(parents=True)
            (task / "task.md").write_text(
                "# Invalid\n\n"
                "**Claimed-by:** unclaimed\n"
                "**Filed:** 2026-07-23\n"
                "**Repository scope:** records-only\n",
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("task id must be" in message for message in messages))

    def test_task_record_rejects_moving_status_path_reference(self):
        with self.repo() as root:
            task = self.make_task(root, "1_in-progress", "none")
            task_md = task / "task.md"
            task_md.write_text(
                task_md.read_text(encoding="utf-8")
                + "\nRelated: `tasks/0_backlog/2026-07-22-other/task.md`\n",
                encoding="utf-8",
            )
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("moving status path" in message
                                for message in messages))

    def test_retry_names_are_prefixed_idempotent_and_gc_legacy_names(self):
        with self.repo() as root:
            finding = RECONCILE.Finding(
                "queue-schema",
                Path("message-queue/needs-human/reviews/example.md"),
                "missing field",
                "add the field",
            )
            identity = RECONCILE.finding_key(finding)
            self.assertTrue(identity.startswith("reconcile-"))
            self.assertFalse(identity.startswith("blocking-"))

            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            expected = root / "message-queue" / "needs-agent" / "retries" / (
                "blocking-" + identity + ".md"
            )
            self.assertTrue(expected.is_file())
            body = expected.read_text(encoding="utf-8")
            self.assertIn("**Generated by:** reconcile.py/v1", body)
            self.assertIn("**Action:** add the field", body)
            self.assertIn("**Blocks now:**", body)
            claimed = body.replace("**Status:** open", "**Status:** in-repair")
            claimed += "\n## Agent notes\n\nKeep this diagnosis.\n"
            expected.write_text(claimed, encoding="utf-8")

            self.write(
                root,
                "message-queue/needs-agent/retries/" + identity + ".md",
                "# Legacy generated retry\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-22, by reconciler\n"
                "**Check:** queue-schema\n"
                "**Subject:** `legacy.md`\n\n"
                "## Broken invariant\n\nBroken.\n\n"
                "## Fix\n\nFix it.\n",
            )
            stale_finding = RECONCILE.Finding(
                "queue-schema", Path("stale.md"), "stale", "repair stale"
            )
            self.write(
                root,
                "message-queue/needs-agent/retries/"
                "blocking-reconcile-stale-subject.md",
                RECONCILE.retry_text(stale_finding),
            )
            manual = self.write(
                root,
                "message-queue/needs-agent/retries/"
                "blocking-reconcile-manual-note.md",
                "# Manual\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23, by test\n"
                "**Check:** manual\n"
                "**Subject:** `manual.md`\n"
                "**Action:** inspect it\n"
                "**Blocks now:** operation:test\n",
            )
            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            self.assertTrue(expected.is_file())
            preserved = expected.read_text(encoding="utf-8")
            self.assertIn("**Status:** in-repair", preserved)
            self.assertIn("Keep this diagnosis.", preserved)
            self.assertTrue((expected.parent / (identity + ".md")).exists())
            self.assertEqual((0, 1), RECONCILE.file_retries([]))
            self.assertFalse(expected.exists())
            self.assertTrue(manual.exists())

    def test_manual_retry_plain_agent_notes_survive_claim_and_resolution(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(
                root,
                "message-queue/AGENTS.md",
                "**Queue resolution schema:** v1\n",
            )
            evidence = self.write(root, "README.md", "# Broken\n")
            path = (
                "message-queue/needs-agent/retries/"
                "blocking-manual-diagnosis.md"
            )
            item = self.write(
                root,
                path,
                "# Diagnose manually\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23\n"
                "**Check:** manual\n"
                "**Subject:** `README.md`\n"
                "**Action:** repair the documented issue\n"
                "**Resolution evidence:** `README.md`\n"
                "**Blocks now:** operation:repair\n",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file manual retry")
            item.write_text(
                item.read_text(encoding="utf-8").replace(
                    "**Status:** open", "**Status:** in-repair"
                ),
                encoding="utf-8",
            )
            self.git(root, "add", path)
            self.git(root, "commit", "-m", "claim manual retry")

            item.write_text(
                item.read_text(encoding="utf-8")
                + "\n## Agent notes\n\n"
                + "The failure reproduces only with the documented input.\n",
                encoding="utf-8",
            )
            self.git(root, "add", path)
            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()
            self.git(root, "commit", "-m", "record diagnosis")

            evidence.write_text("# Repaired\n", encoding="utf-8")
            item.unlink()
            self.git(root, "add", "-A")
            RECONCILE.start_git_snapshot_cache()
            try:
                self.assertEqual(
                    [], list(RECONCILE.check_queue_resolution())
                )
            finally:
                RECONCILE.stop_git_snapshot_cache()

    def test_manual_retry_agent_notes_reject_structured_queue_fields(self):
        note_cases = (
            "**Why-you-might-care:** This must not be mutable metadata.\n",
            "Plain diagnosis.\n\n"
            "## Agent notes\n\n"
            "**Why-you-might-care:** Hidden in the second notes section.\n",
            "Plain diagnosis.\n\n"
            "### Details\n\n"
            "**Why-you-might-care:** Hidden below a nested heading.\n",
        )
        for notes in note_cases:
            with self.subTest(notes=notes), self.repo() as root:
                self.write(root, "README.md", "# Broken\n")
                self.write(
                    root,
                    "message-queue/needs-agent/retries/"
                    "blocking-manual-structured-note.md",
                    "# Diagnose manually\n\n"
                    "**Status:** open\n"
                    "**Filed:** 2026-07-23\n"
                    "**Check:** manual\n"
                    "**Subject:** `README.md`\n"
                    "**Action:** repair the documented issue\n"
                    "**Resolution evidence:** `README.md`\n"
                    "**Blocks now:** operation:repair\n\n"
                    "## Agent notes\n\n"
                    + notes,
                )

                messages = self.messages(RECONCILE.check_queue_schema())
                self.assertTrue(any(
                    "manual retry Agent notes contain structured queue fields"
                    in message
                    for message in messages
                ), messages)

    def test_legacy_retry_migration_preserves_claim_and_notes(self):
        with self.repo() as root:
            finding = RECONCILE.Finding(
                "queue-schema", Path("legacy.md"), "legacy failure", "repair it"
            )
            identity = RECONCILE.legacy_finding_key(finding)
            self.assertNotEqual(identity, RECONCILE.finding_key(finding))
            legacy = self.write(
                root,
                "message-queue/needs-agent/retries/" + identity + ".md",
                "# Legacy\n\n"
                "**Status:** in-repair\n"
                "**Filed:** 2026-07-22, by reconciler\n"
                "**Check:** queue-schema\n"
                "**Subject:** `legacy.md`\n\n"
                "## Broken invariant\n\nBroken.\n\n"
                "## Fix\n\nOriginal fix.\n\n"
                "## Agent notes\n\nPreserve this diagnosis.\n",
            )
            self.assertEqual((1, 1), RECONCILE.file_retries([finding]))
            migrated = legacy.parent / (
                "blocking-" + RECONCILE.finding_key(finding) + ".md"
            )
            self.assertFalse(legacy.exists())
            text = migrated.read_text(encoding="utf-8")
            self.assertIn("**Status:** in-repair", text)
            self.assertIn("**Generated by:** reconcile.py/v1", text)
            self.assertIn("**Action:** repair it", text)
            self.assertIn("**Blocks now:**", text)
            self.assertIn("Preserve this diagnosis.", text)

    def test_retry_aggregation_refresh_and_collision_safe_keys(self):
        with self.repo() as root:
            subject = Path(
                "message-queue/needs-human/reviews/"
                "future-blocking-review-assurance-profile-ceilings.md"
            )
            first = RECONCILE.Finding(
                "queue-schema", subject, "missing summary", "add summary"
            )
            second = RECONCILE.Finding(
                "queue-schema", subject, "missing example", "add example"
            )
            other = RECONCILE.Finding(
                "queue-schema",
                Path(
                    "message-queue/needs-human/reviews/"
                    "future-blocking-review-detector-failure-state.md"
                ),
                "missing summary",
                "add summary",
            )
            self.assertNotEqual(
                RECONCILE.finding_key(first), RECONCILE.finding_key(other)
            )
            self.assertLessEqual(len(RECONCILE.finding_key(first)), 80)

            self.assertEqual((1, 0), RECONCILE.file_retries([first, second]))
            retry = next(RECONCILE.RETRIES.glob("blocking-reconcile-*.md"))
            text = retry.read_text(encoding="utf-8")
            self.assertIn("missing summary", text)
            self.assertIn("missing example", text)
            retry.write_text(
                text.replace("**Status:** open", "**Status:** in-repair")
                + "\n## Agent notes\n\nKeep this.\n",
                encoding="utf-8",
            )

            self.assertEqual((1, 0), RECONCILE.file_retries([second]))
            refreshed = retry.read_text(encoding="utf-8")
            self.assertNotIn("missing summary", refreshed)
            self.assertIn("missing example", refreshed)
            self.assertIn("**Status:** in-repair", refreshed)
            self.assertIn("Keep this.", refreshed)

    def test_manual_retry_filename_collision_gets_stable_alternate(self):
        with self.repo() as root:
            finding = RECONCILE.Finding(
                "queue-schema", Path("very/long/subject.md"), "broken", "repair"
            )
            key = RECONCILE.finding_key(finding)
            manual = self.write(
                root,
                f"message-queue/needs-agent/retries/blocking-{key}.md",
                "# Manual collision\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23, by maintainer\n"
                "**Check:** manual\n"
                "**Subject:** `different.md`\n"
                "**Action:** keep this note\n"
                "**Blocks now:** operation:review\n",
            )
            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            alternate = manual.with_name(
                f"blocking-{key}-1.md"
            )
            self.assertTrue(alternate.is_file())
            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            self.assertEqual(
                [alternate],
                [
                    path for path in RECONCILE.RETRIES.glob(
                        f"blocking-{key}-*.md"
                    )
                ],
            )
            self.assertEqual("# Manual collision", manual.read_text().splitlines()[0])
            manual.unlink()
            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            self.assertTrue(alternate.is_file())
            self.assertFalse(manual.exists())

    def test_retry_gc_never_deletes_other_reconciler_action(self):
        with self.repo() as root:
            retry = self.write(
                root,
                "message-queue/needs-agent/retries/"
                "blocking-dependency-audit.md",
                "# Repair dependency audit\n\n"
                "**Status:** open\n"
                "**Filed:** 2026-07-23, by reconciler\n"
                "**Check:** dependency-audit\n"
                "**Subject:** `deps/lock`\n"
                "**Action:** refresh the lock\n"
                "**Blocks now:** transition:merge\n\n"
                "## Broken invariant\n\nThe lock is stale.\n\n"
                "## Fix\n\nRefresh it with the owning tool.\n",
            )
            self.assertFalse(RECONCILE.reconciler_owned_retry(
                retry, retry.read_text(encoding="utf-8")
            ))

            self.assertEqual((0, 0), RECONCILE.file_retries([]))
            self.assertTrue(retry.is_file())

    def test_reclassified_generated_retry_is_rediscovered_and_collected(self):
        with self.repo() as root:
            finding = RECONCILE.Finding(
                "queue-schema", Path("example.md"), "broken", "repair"
            )
            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            generated = next(RECONCILE.RETRIES.glob("blocking-*.md"))
            reclassified = generated.with_name(
                generated.name.replace("blocking-", "future-blocking-", 1)
            )
            generated.rename(reclassified)
            reclassified.write_text(
                reclassified.read_text(encoding="utf-8").replace(
                    "**Blocks now:** transition:merge",
                    "**Blocks at:** transition:merge\n"
                    "**Until then:** continue the repair",
                ),
                encoding="utf-8",
            )

            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            self.assertTrue(reclassified.is_file())
            self.assertEqual([], list(RECONCILE.RETRIES.glob("blocking-*.md")))
            self.assertNotIn(
                "**Blocks now:**",
                reclassified.read_text(encoding="utf-8"),
            )
            self.assertEqual([], list(RECONCILE.check_queue_schema()))

            self.assertEqual((0, 1), RECONCILE.file_retries([]))
            self.assertFalse(reclassified.exists())

    def test_memory_index_derives_supersession_without_rewriting_old_adr(self):
        with self.repo() as root:
            old = self.write(
                root,
                "memory/decisions/2026-07-22-old.md",
                "# Old decision\n\n"
                "**Status:** decided\n"
                "**Description:** old outcome\n"
                "**Review-by:** 2027-01-01\n"
                "**Date:** 2026-07-22\n"
                "**Decided-by:** human\n",
            )
            self.write(
                root,
                "memory/decisions/2026-07-23-new.md",
                "# New decision\n\n"
                "**Status:** decided\n"
                "**Description:** corrected outcome\n"
                "**Review-by:** 2027-01-01\n"
                "**Date:** 2026-07-23\n"
                "**Decided-by:** human\n"
                "**Supersedes:** `memory/decisions/2026-07-22-old.md`\n",
            )
            index = RECONCILE.generated_index()
            self.assertIn("[Old decision]", index)
            self.assertIn("**[superseded]**", index)
            self.assertIn("**Status:** decided", old.read_text(encoding="utf-8"))

    def test_stale_queue_respects_delivery_class(self):
        with self.repo() as root:
            folder = "message-queue/needs-agent/requests/"
            self.write(
                root,
                folder + "blocking-old.md",
                "**Filed:** 2026-06-01\n**Blocks now:** transition:commit\n",
            )
            self.write(
                root,
                folder + "non-blocking-old.md",
                "**Filed:** 2026-06-01\n**If unanswered:** keep going\n",
            )
            self.write(
                root,
                folder + "future-blocking-past.md",
                "**Filed:** 2026-07-23\n"
                "**Blocks at:** 2026-07-22\n"
                "**Until then:** continue discovery\n",
            )
            self.write(
                root,
                folder + "future-blocking-today.md",
                "**Filed:** 2026-07-23\n"
                "**Blocks at:** 2026-07-23\n"
                "**Until then:** continue discovery\n",
            )
            self.write(
                root,
                folder + "future-blocking-event.md",
                "**Filed:** 2026-06-01\n"
                "**Blocks at:** transition:start task:2026-07-22-example\n"
                "**Until then:** continue discovery\n",
            )
            self.write(
                root,
                folder + "future-blocking-future.md",
                "**Filed:** 2026-06-01\n"
                "**Blocks at:** 2026-07-24\n"
                "**Until then:** continue discovery\n",
            )
            subjects = {
                str(finding.subject) for finding in RECONCILE.check_stale_queue()
            }
            self.assertEqual(
                {
                    folder + "blocking-old.md",
                    folder + "future-blocking-past.md",
                    folder + "future-blocking-today.md",
                },
                subjects,
            )

    CODE_SPAN_QUEUE_REL = (
        "message-queue/needs-human/decisions/"
        "future-blocking-choose-freshness-mode.md"
    )

    def write_code_span_decision(self, root):
        """Write a live human item whose projected fields carry code spans."""
        self.write(
            root,
            self.CODE_SPAN_QUEUE_REL,
            "# Choose the freshness mode\n\n"
            "**Action:** keep `each-run`, or ship two modes\n"
            "**Why-you-might-care:** `each-run` costs a history pass per run.\n"
            "**If-you-do-nothing:** `Update-when:` stays prose in the "
            "`advisory` mode.\n",
        )
        return self.CODE_SPAN_QUEUE_REL

    def projection_messages(self, root, handover):
        self.activate_strict_handover_entries(root)
        with mock.patch.object(
            RECONCILE,
            "newly_added_handovers",
            return_value=({handover.relative_to(root)}, None),
        ):
            return self.messages(RECONCILE.check_handover_queue_projection())

    def test_strict_handover_projects_backticked_context_field(self):
        with self.repo() as root:
            queue_rel = self.write_code_span_decision(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-backticked-context",
                "- [keep `each-run`, or ship two modes](../../../"
                f"{queue_rel}) — Why-you-might-care: `each-run` costs a "
                "history pass per run. || If-you-do-nothing: `Update-when:` "
                "stays prose in the `advisory` mode.",
            )
            messages = self.projection_messages(root, handover)
            self.assertFalse(any(
                "fixed handover suffix" in message for message in messages
            ), messages)

    def test_strict_handover_projects_rendered_code_span_context(self):
        with self.repo() as root:
            queue_rel = self.write_code_span_decision(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-rendered-context",
                "- [keep each-run, or ship two modes](../../../"
                f"{queue_rel}) — Why-you-might-care: each-run costs a "
                "history pass per run. || If-you-do-nothing: Update-when: "
                "stays prose in the advisory mode.",
            )
            messages = self.projection_messages(root, handover)
            self.assertFalse(any(
                "fixed handover suffix" in message for message in messages
            ), messages)

    def test_strict_handover_rejects_context_copying_neither_spelling(self):
        cases = {
            "reworded": (
                "— Why-you-might-care: `each-run` costs nothing at all. "
                "|| If-you-do-nothing: `Update-when:` stays prose in the "
                "`advisory` mode."
            ),
            "swapped-span-contents": (
                "— Why-you-might-care: `review-window` costs a history pass "
                "per run. || If-you-do-nothing: `Update-when:` stays prose "
                "in the `advisory` mode."
            ),
            "dropped-span-contents": (
                "— Why-you-might-care: costs a history pass per run. "
                "|| If-you-do-nothing: stays prose in the mode."
            ),
        }
        for name, context in cases.items():
            with self.subTest(context=name), self.repo() as root:
                queue_rel = self.write_code_span_decision(root)
                handover = self.make_handover(
                    root,
                    f"2026-07-23-1200PDT-context-{name}",
                    "- [keep `each-run`, or ship two modes](../../../"
                    f"{queue_rel}) {context}",
                )
                messages = self.projection_messages(root, handover)
                self.assertTrue(any(
                    "fixed handover suffix" in message
                    for message in messages
                ), messages)

    def test_strict_handover_context_without_code_span_is_unchanged(self):
        queue_rel = (
            "message-queue/needs-human/reviews/"
            "future-blocking-review-docs.md"
        )
        for name, context, rejected in (
            (
                "faithful",
                "— Why-you-might-care: The docs control behavior. "
                "|| If-you-do-nothing: The review remains pending.",
                False,
            ),
            (
                "reworded",
                "— Why-you-might-care: The docs control nothing. "
                "|| If-you-do-nothing: The review remains pending.",
                True,
            ),
        ):
            with self.subTest(context=name), self.repo() as root:
                self.write(
                    root,
                    queue_rel,
                    "# Review docs\n\n"
                    "**Action:** review docs\n"
                    "**Why-you-might-care:** The docs control behavior.\n"
                    "**If-you-do-nothing:** The review remains pending.\n",
                )
                handover = self.make_handover(
                    root,
                    f"2026-07-23-1200PDT-plain-context-{name}",
                    f"- [review docs](../../../{queue_rel}) {context}",
                )
                messages = self.projection_messages(root, handover)
                self.assertEqual(rejected, any(
                    "fixed handover suffix" in message
                    for message in messages
                ), messages)

    def test_strict_handover_projects_code_spanned_human_item_at_all(self):
        with self.repo() as root:
            queue_rel = self.write_code_span_decision(root)
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-code-spanned-item-projects",
                "- [keep `each-run`, or ship two modes](../../../"
                f"{queue_rel}) — Why-you-might-care: `each-run` costs a "
                "history pass per run. || If-you-do-nothing: `Update-when:` "
                "stays prose in the `advisory` mode.",
            )
            self.assertEqual([], self.projection_messages(root, handover))

    def test_strict_handover_rejects_agent_entry_carrying_code_span(self):
        with self.repo() as root:
            queue_rel = (
                "message-queue/needs-agent/requests/"
                "non-blocking-repair-docs.md"
            )
            self.write(
                root,
                queue_rel,
                "# Repair docs\n\n**Action:** repair docs\n",
            )
            handover = self.make_handover(
                root,
                "2026-07-23-1200PDT-agent-entry-code-span",
                "None.",
            )
            handover.write_text(
                handover.read_text(encoding="utf-8").replace(
                    "## Next steps\n\nNone.",
                    "## Next steps\n\n"
                    f"- [repair docs](../../../{queue_rel}) "
                    "`and also drop the staging database`",
                ),
                encoding="utf-8",
            )
            messages = self.projection_messages(root, handover)
            self.assertTrue(any(
                "only its exact Action-labeled needs-agent queue link"
                in message
                for message in messages
            ), messages)

    def test_link_check_reports_dead_path_carried_behind_an_anchor(self):
        with self.repo() as root:
            self.write(
                root,
                "docs/source.md",
                "Anchored: `docs/does-not-exist.md#foo`\n",
            )

            messages = self.messages(RECONCILE.check_links())
            self.assertEqual(1, len(messages), messages)
            self.assertIn("`docs/does-not-exist.md` does not exist", messages[0])

    def test_link_check_accepts_a_live_anchor_on_a_live_path(self):
        with self.repo() as root:
            self.write(root, "docs/target.md", "# Target\n\n## Live section\n")
            self.write(root, "docs/source.md", "See `docs/target.md#live-section`.\n")

            self.assertEqual([], list(RECONCILE.check_links()))

    def test_link_check_reports_a_dead_anchor_on_a_live_path(self):
        with self.repo() as root:
            self.write(root, "docs/target.md", "# Target\n\n## Live section\n")
            self.write(
                root,
                "docs/source.md",
                "See [gone](docs/target.md#missing-section).\n",
            )

            messages = self.messages(RECONCILE.check_links())
            self.assertEqual(1, len(messages), messages)
            self.assertIn("`docs/target.md` has no `missing-section` heading anchor",
                          messages[0])

    def test_link_check_rejects_an_anchor_defined_only_inside_a_fence(self):
        with self.repo() as root:
            self.write(
                root,
                "docs/target.md",
                "# Target\n\n```markdown\n## Fenced section\n```\n",
            )
            self.write(root, "docs/source.md", "See `docs/target.md#fenced-section`.\n")

            messages = self.messages(RECONCILE.check_links())
            self.assertEqual(1, len(messages), messages)
            self.assertIn("no `fenced-section` heading anchor", messages[0])

    def test_link_check_numbers_duplicate_heading_anchors(self):
        with self.repo() as root:
            self.write(
                root,
                "docs/target.md",
                "# Target\n\n## Repeat\n\ntext\n\n## Repeat\n\ntext\n",
            )
            self.write(
                root,
                "docs/source.md",
                "First `docs/target.md#repeat`, second `docs/target.md#repeat-1`.\n",
            )

            self.assertEqual([], list(RECONCILE.check_links()))

            self.write(root, "docs/source.md", "Third `docs/target.md#repeat-2`.\n")

            messages = self.messages(RECONCILE.check_links())
            self.assertEqual(1, len(messages), messages)
            self.assertIn("no `repeat-2` heading anchor", messages[0])

    def test_link_check_slugs_punctuation_heavy_headings(self):
        with self.repo() as root:
            self.write(
                root,
                "handbook/git-workflow.md",
                "# Git workflow\n\n"
                "## Conflict avoidance (by construction, not by care)\n",
            )
            self.write(
                root,
                "docs/source.md",
                "See `handbook/git-workflow.md"
                "#conflict-avoidance-by-construction-not-by-care`.\n",
            )

            self.assertEqual([], list(RECONCILE.check_links()))

            self.write(
                root,
                "docs/source.md",
                "See `handbook/git-workflow.md"
                "#conflict-avoidance-by-construction-not-by-care-1`.\n",
            )

            self.assertEqual(1, len(list(RECONCILE.check_links())))

    def test_link_check_keeps_anchor_exemptions_for_records_and_schemas(self):
        with self.repo() as root:
            self.write(root, "docs/target.md", "# Target\n")
            for rel in (
                "history/conversations/2026-07-23-1200Z-example/handover.md",
                "templates/handover.md",
                "memory/decisions/2026-07-23-example.md",
            ):
                self.write(root, rel, "Anchored: `docs/target.md#missing-section`\n")

            self.assertEqual([], list(RECONCILE.check_links()))

    def test_link_check_ignores_a_bare_same_file_fragment(self):
        with self.repo() as root:
            self.write(
                root,
                "docs/source.md",
                "# Source\n\nSee [above](#source) and [nowhere](#absent).\n",
            )

            self.assertEqual([], list(RECONCILE.check_links()))

    @staticmethod
    def creation_topology_messages(findings):
        return [
            finding.message for finding in findings
            if "created directly in" in finding.message
        ]

    def activate_task_admission(self, root):
        self.init_git(root)
        self.write(
            root,
            "tasks/AGENTS.md",
            "**Task admission schema:** v1\n",
        )
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "activate task admission")
        return self.git(root, "branch", "--show-current")

    def file_unclaimed_backlog_task(self, root):
        task = self.make_task(root, "0_backlog", "none")
        record = task / "task.md"
        record.write_text(
            record.read_text(encoding="utf-8").replace(
                "**Claimed-by:** test", "**Claimed-by:** unclaimed"
            ),
            encoding="utf-8",
        )
        return task

    def advance_task_record(self, root, task, status):
        moved = root / "tasks" / status / task.name
        moved.parent.mkdir(parents=True, exist_ok=True)
        task.rename(moved)
        record = moved / "task.md"
        record.write_text(
            record.read_text(encoding="utf-8").replace(
                "**Claimed-by:** unclaimed", "**Claimed-by:** test"
            ),
            encoding="utf-8",
        )
        for needed, heading in (("plan.md", "Plan"), ("worklog.md", "Worklog")):
            (moved / needed).write_text(
                f"# {heading}\n", encoding="utf-8"
            )
        if status in ("3_in-review", "4_done"):
            (moved / "verification.md").write_text(
                "# Verification\n", encoding="utf-8"
            )
        return moved

    def admission_findings_over_range(self, base, head):
        RECONCILE.start_git_snapshot_cache()
        try:
            with mock.patch.object(
                RECONCILE, "CHANGE_RANGE", f"{base}...{head}"
            ):
                return list(RECONCILE.check_task_admission_history())
        finally:
            RECONCILE.stop_git_snapshot_cache()

    def test_task_admission_accepts_a_merge_parent_that_predates_a_task(self):
        with self.repo() as root:
            trunk = self.activate_task_admission(root)

            self.git(root, "checkout", "-b", "cut-before-the-task")
            self.write(root, "side.md", "# Side\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "side work")

            self.git(root, "checkout", trunk)
            backlog = self.file_unclaimed_backlog_task(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file the backlog task")
            self.advance_task_record(root, backlog, "1_in-progress")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "claim the task")
            left = self.git(root, "rev-parse", "HEAD")

            self.git(
                root, "merge", "--no-ff", "-m", "merge the earlier cut",
                "cut-before-the-task",
            )
            merged = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(left, merged)
            self.assertEqual(
                [],
                self.creation_topology_messages(findings),
                self.messages(findings),
            )

    def test_task_admission_still_rejects_a_linear_in_progress_creation(self):
        with self.repo() as root:
            self.activate_task_admission(root)
            base = self.git(root, "rev-parse", "HEAD")
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "create the task in progress")
            head = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(base, head)
            self.assertTrue(any(
                "new task:2026-07-23-example was created directly in "
                "1_in-progress" in message
                for message in self.creation_topology_messages(findings)
            ), self.messages(findings))

    def test_task_admission_still_rejects_a_merge_creation_no_parent_had(self):
        with self.repo() as root:
            trunk = self.activate_task_admission(root)

            self.git(root, "checkout", "-b", "unrelated-side")
            self.write(root, "side.md", "# Side\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "side work")

            self.git(root, "checkout", trunk)
            self.write(root, "left.md", "# Left\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "left work")
            left = self.git(root, "rev-parse", "HEAD")

            self.git(
                root, "merge", "--no-ff", "--no-commit", "unrelated-side",
            )
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "merge and create the task")
            merged = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(left, merged)
            self.assertTrue(any(
                "new task:2026-07-23-example was created directly in "
                "1_in-progress" in message
                for message in self.creation_topology_messages(findings)
            ), self.messages(findings))

    def test_task_admission_accepts_a_merge_claiming_a_backlog_task(self):
        with self.repo() as root:
            trunk = self.activate_task_admission(root)

            self.git(root, "checkout", "-b", "cut-before-the-task")
            self.write(root, "side.md", "# Side\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "side work")

            self.git(root, "checkout", trunk)
            backlog = self.file_unclaimed_backlog_task(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file the backlog task")
            left = self.git(root, "rev-parse", "HEAD")

            self.git(
                root, "merge", "--no-ff", "--no-commit", "cut-before-the-task",
            )
            self.advance_task_record(root, backlog, "1_in-progress")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "merge and claim the task")
            merged = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(left, merged)
            self.assertEqual(
                [],
                self.creation_topology_messages(findings),
                self.messages(findings),
            )
            self.assertEqual([], [
                finding.message for finding in findings
                if "jumped from" in finding.message
            ], self.messages(findings))

    def test_task_admission_still_rejects_an_illegal_merge_advance(self):
        with self.repo() as root:
            trunk = self.activate_task_admission(root)

            self.git(root, "checkout", "-b", "cut-before-the-task")
            self.write(root, "side.md", "# Side\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "side work")

            self.git(root, "checkout", trunk)
            backlog = self.file_unclaimed_backlog_task(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "file the backlog task")
            left = self.git(root, "rev-parse", "HEAD")

            self.git(
                root, "merge", "--no-ff", "--no-commit", "cut-before-the-task",
            )
            self.advance_task_record(root, backlog, "4_done")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-m", "merge and finish the task")
            merged = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(left, merged)
            self.assertTrue(any(
                "task:2026-07-23-example jumped from 0_backlog to 4_done"
                in finding.message
                for finding in findings
            ), self.messages(findings))
            self.assertEqual(
                [],
                self.creation_topology_messages(findings),
                self.messages(findings),
            )

    def test_task_admission_keeps_the_adoption_escape_for_a_first_task(self):
        with self.repo() as root:
            self.init_git(root)
            self.write(root, "docs/source.md", "# Source\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "pre-adoption history")
            base = self.git(root, "rev-parse", "HEAD")

            self.write(
                root,
                "tasks/AGENTS.md",
                "**Task admission schema:** v1\n",
            )
            self.make_task(root, "1_in-progress", "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "adopt task admission with a task")
            head = self.git(root, "rev-parse", "HEAD")

            findings = self.admission_findings_over_range(base, head)
            self.assertEqual(
                [],
                self.creation_topology_messages(findings),
                self.messages(findings),
            )


if __name__ == "__main__":
    unittest.main()
