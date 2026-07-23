import contextlib
import datetime
import hashlib
import importlib.util
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
            self.assertTrue(any("unavailable Git commit object" in message
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
            + "\n"
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
                extra="\n## Next steps\n\nAsk a non-actionable historical question.\n",
            )
            self.assertEqual(
                [], list(RECONCILE.check_handover_queue_projection())
            )

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
                return_value=(creation_text, {queue_rel}, None),
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

    def test_handover_accepts_angle_destination_with_checkout_spaces(self):
        with self.repo() as root:
            self.make_handover(
                root,
                "2026-07-23-1200PDT-angle-link",
                "[Review](</tmp/My Checkout/message-queue/needs-human/reviews/"
                "future-blocking-review.md>)",
            )
            self.assertEqual([], list(RECONCILE.check_handover_queue_projection()))

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
            self.assertTrue(any("crossed unresolved future boundary" in message
                                for message in messages))

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

    def test_transition_cli_accepts_non_task_branch_as_global_only(self):
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

    def test_task_queue_paths_must_be_live_and_done_tasks_must_use_none(self):
        with self.repo() as root:
            (root / "message-queue").mkdir()
            missing = (
                "message-queue/needs-human/reviews/"
                "non-blocking-missing.md"
            )
            self.make_task(root, "4_done", "`" + missing + "`")
            messages = self.messages(RECONCILE.check_task_structure())
            self.assertTrue(any("is not a live file" in message for message in messages))
            self.assertTrue(any("done task must declare" in message for message in messages))

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
            identity = RECONCILE.finding_key(finding)
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
            migrated = legacy.parent / ("blocking-" + identity + ".md")
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

            self.assertEqual((1, 0), RECONCILE.file_retries([finding]))
            self.assertTrue(reclassified.is_file())
            self.assertEqual([], list(RECONCILE.RETRIES.glob("blocking-*.md")))

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
