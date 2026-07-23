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

    def test_github_adapter_handles_root_push_and_always_runs_tests(self):
        workflow = (
            MODULE_PATH.parents[2] / ".github/workflows/harness.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '[ "$QUEUE_PUSH_BEFORE" = '
            '"0000000000000000000000000000000000000000" ]',
            workflow,
        )
        self.assertIn('QUEUE_CHANGE_RANGE="root:$QUEUE_PUSH_HEAD"', workflow)
        self.assertIn(
            'git cat-file -e "$QUEUE_PUSH_BEFORE^{commit}"', workflow
        )
        self.assertIn(
            'QUEUE_CHANGE_RANGE="$QUEUE_PUSH_BASE...$QUEUE_PUSH_HEAD"',
            workflow,
        )
        self.assertIn("if: ${{ always() }}", workflow)
        self.assertNotIn("--at-transition repository-admission", workflow)

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
                "**Review target:** pending\n"
                "**Review revision:** pending\n"
                "**Reviewed revision:** ______\n"
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
                    "**Review target:** https://example.test/pull/1",
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
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
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
                "**Review target:** [artifact](<docs/My Artifact.bin>)\n"
                f"**Review revision:** sha256:{digest}\n"
                "**Reviewed revision:** ______\n"
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
                f"**Review target:** {target}\n"
                f"**Review revision:** {target}\n"
                "**Reviewed revision:** ______\n"
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
                "**Review target:** `docs/source.md`\n"
                f"**Review revision:** {digest}\n"
                "**Reviewed revision:** ______\n"
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
            self.assertEqual((1, 2), RECONCILE.file_retries([finding]))
            self.assertTrue(expected.is_file())
            preserved = expected.read_text(encoding="utf-8")
            self.assertIn("**Status:** in-repair", preserved)
            self.assertIn("Keep this diagnosis.", preserved)
            self.assertFalse((expected.parent / (identity + ".md")).exists())
            self.assertEqual((0, 1), RECONCILE.file_retries([]))
            self.assertFalse(expected.exists())
            self.assertTrue(manual.exists())

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


if __name__ == "__main__":
    unittest.main()
