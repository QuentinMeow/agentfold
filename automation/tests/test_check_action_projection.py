import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "check_action_projection.py"
)
SPEC = importlib.util.spec_from_file_location("check_action_projection", MODULE_PATH)
PROJECTION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROJECTION)


class ActionProjectionTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git(root, "init")
            self.git(root, "config", "user.name", "Test")
            self.git(root, "config", "user.email", "test@example.invalid")
            (root / "message-queue").mkdir()
            with mock.patch.object(PROJECTION, "REPO", root):
                yield root

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

    @staticmethod
    def queue_item(
        root,
        name="future-blocking-review-boundary.md",
        action="Review the boundary.",
    ):
        path = root / "message-queue/needs-human/reviews" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Review\n\n**Action:** {action}\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def task_record(root, task_id, queue_actions):
        path = root / "tasks/1_in-progress" / task_id / "task.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Task\n\n"
            f"**Queue actions:** {queue_actions}\n",
            encoding="utf-8",
        )
        return path

    def findings(
        self,
        root,
        body,
        *titles,
        allowed_url_prefixes=(),
        task_id=None,
        candidate_revision=None,
    ):
        return PROJECTION.projection_findings(
            body,
            titles or ("What to review",),
            repo=root,
            allowed_url_prefixes=allowed_url_prefixes,
            task_id=task_id,
            candidate_revision=candidate_revision,
        )

    def test_orphan_what_to_review_question_is_rejected(self):
        with self.repo() as root:
            findings = self.findings(
                root,
                "> [!IMPORTANT]\n>\n> ### What to review\n>\n"
                "> 1. Does the boundary work?\n",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("valid canonical", findings[0])

    def test_live_needs_human_link_is_accepted(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "> [!IMPORTANT]\n>\n> ### What to review\n>\n"
                "> 1. [Review the boundary]("
                + item.relative_to(root).as_posix()
                + ") before merge.\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_mixed_linked_and_orphan_entries_rejects_the_orphan(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()})\n"
                "2. Should the fallback change?\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("entry 2", findings[0])

    def test_unlisted_question_after_linked_entry_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()})\n\n"
                "Should we also ship the fallback?\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("outside the top-level action list", findings[0])

    def test_additional_ask_inside_linked_entry_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()}). "
                "Also decide whether B should ship?\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("additional unlinked", findings[0])

    def test_additional_unlinked_directive_without_question_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()}). "
                "Approve production after that.\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("additional unlinked", findings[0])

    def test_additional_declarative_ask_inside_linked_entry_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root, action="Review the copy wording.")
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the copy wording]"
                f"({item.relative_to(root).as_posix()}). "
                "Human approval is also required.\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("additional unlinked", findings[0])

    def test_each_action_entry_has_exactly_one_queue_link(self):
        with self.repo() as root:
            first = self.queue_item(root, "future-blocking-review-first.md")
            second = self.queue_item(root, "future-blocking-review-second.md")
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [First]({first.relative_to(root).as_posix()}) and "
                f"[second]({second.relative_to(root).as_posix()}).\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("exactly one", findings[0])

    def test_nonqueue_link_cannot_hide_second_action(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()}) and "
                "[approve production](https://example.invalid/approval).\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("action-like supporting link", findings[0])

    def test_nonaction_supporting_link_is_accepted(self):
        with self.repo() as root:
            item = self.queue_item(root, action="Review the diff.")
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the diff]({item.relative_to(root).as_posix()}) "
                "against the [published policy](https://example.invalid/policy).\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_queue_link_label_cannot_hide_multiple_actions(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the diff and approve production]"
                f"({item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("multiple actions", findings[0])

    def test_queue_link_label_cannot_hide_multiple_questions(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Can A ship? Can B ship?]"
                f"({item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("multiple actions", findings[0])

    def test_queue_link_label_must_summarize_canonical_action(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Review the copy wording and request changes if needed.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            unrelated = (
                "Authorize production deployment",
                "Review the copy logging",
                "Review the boundary",
                "Review the diff",
                "Review the proposal",
                "🧨",
            )
            for label in unrelated:
                with self.subTest(label=label):
                    body = (
                        "## What to review\n\n"
                        f"1. [{label}]({path})\n"
                    )
                    findings = self.findings(root, body)
                    self.assertEqual(1, len(findings))
                    self.assertIn("canonical `Action`", findings[0])

    def test_specific_and_generic_honest_action_summaries_are_accepted(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Review the copy wording and request changes if needed.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            for label in ("Review the copy wording", "Review request"):
                with self.subTest(label=label):
                    body = (
                        "## What to review\n\n"
                        f"1. [{label}]({path})\n"
                    )
                    self.assertEqual([], self.findings(root, body))

    def test_canonical_prefix_label_must_name_an_action_not_only_its_actor(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Owner must authorize production deployment.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            for label in ("Owner", "Owner?", "Owner TODO", "Owner must"):
                with self.subTest(label=label):
                    findings = self.findings(
                        root,
                        f"## What to review\n\n1. [{label}]({path})\n",
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn("canonical `Action`", findings[0])
            for label in ("Owner must authorize", "Review request"):
                with self.subTest(label=label):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            f"## What to review\n\n1. [{label}]({path})\n",
                        ),
                    )

    def test_hidden_or_duplicate_canonical_action_field_is_rejected(self):
        contents = (
            "# Review\n\n```\n**Action:** Review the boundary.\n```\n",
            (
                "# Review\n\n"
                "**Action:** Review the boundary.\n"
                "**Action:** Authorize production deployment.\n"
            ),
        )
        for content in contents:
            with self.subTest(content=content[:16]), self.repo() as root:
                item = self.queue_item(root)
                item.write_text(content, encoding="utf-8")
                self.git(root, "add", ".")
                path = item.relative_to(root).as_posix()
                findings = self.findings(
                    root,
                    f"## What to review\n\n1. [Review]({path})\n",
                )
                self.assertEqual(1, len(findings))
                self.assertIn("canonical `Action` field", findings[0])

    def test_candidate_raw_html_action_field_is_not_canonical_evidence(self):
        with self.repo() as root:
            item = self.queue_item(root)
            item.write_text(
                "<p>**Action:** Review the boundary.</p>\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "candidate hidden action")
            candidate = self.git(root, "rev-parse", "HEAD")
            path = item.relative_to(root).as_posix()
            findings = self.findings(
                root,
                f"## What to review\n\n1. [Review]({path})\n",
                candidate_revision=candidate,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("canonical `Action` field", findings[0])

    def test_nested_commonmark_bullets_are_part_of_the_linked_action(self):
        with self.repo() as root:
            item = self.queue_item(root, action="Choose the boundary.")
            self.git(root, "add", ".")
            body = (
                "> [!IMPORTANT]\n"
                "> ### What to review\n"
                ">\n"
                f"> 1. [Choose the boundary]({item.relative_to(root).as_posix()})\n"
                ">    - `hard` blocks the transition.\n"
                ">    - `soft` reports and continues.\n"
                ">    Example: a failed scan blocks only in `hard` mode.\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_missing_section_requires_explicit_acknowledgement(self):
        with self.repo() as root:
            findings = self.findings(root, "## Goal\n\nShip it.\n")
            self.assertEqual(1, len(findings))
            self.assertIn("missing a declared action section", findings[0])
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo human action requested.\n",
                ),
            )

    def test_no_action_marker_fails_closed_when_live_human_items_exist(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            findings = self.findings(
                root,
                "## What to review\n\nNo human action requested.\n",
            )
            self.assertEqual(1, len(findings))
            self.assertIn(item.relative_to(root).as_posix(), findings[0])

    def test_task_scope_allows_no_action_with_only_unrelated_human_items(self):
        task_id = "2026-07-23-no-human-review"
        with self.repo() as root:
            self.queue_item(root)
            self.task_record(root, task_id, "none")
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo human action requested.\n",
                    task_id=f"task/{task_id}",
                ),
            )

    def test_task_scope_requires_every_declared_live_human_item(self):
        task_id = "2026-07-23-needs-review"
        with self.repo() as root:
            required = self.queue_item(root, "future-blocking-review-required.md")
            unrelated = self.queue_item(
                root,
                "non-blocking-review-unrelated.md",
                action="Review the unrelated item.",
            )
            required_path = required.relative_to(root).as_posix()
            self.task_record(root, task_id, f"`{required_path}`")
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the unrelated item]"
                f"({unrelated.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body, task_id=task_id)
            self.assertEqual(1, len(findings))
            self.assertIn("omit scoped live queue item", findings[0])
            self.assertIn(required_path, findings[0])

    def test_dead_untracked_wrong_actor_and_malformed_links_are_rejected(self):
        destinations = (
            "message-queue/needs-human/reviews/blocking-dead.md",
            "message-queue/needs-agent/requests/blocking-agent.md",
            "message-queue/needs-human/reviews/question.md",
        )
        for destination in destinations:
            with self.subTest(destination=destination), self.repo() as root:
                target = root / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# Item\n", encoding="utf-8")
                findings = self.findings(
                    root,
                    f"## What to review\n\n1. [Review]({destination})\n",
                )
                self.assertEqual(1, len(findings))

    def test_tracked_symlink_does_not_satisfy_visible_queue_link(self):
        with self.repo() as root:
            item = self.queue_item(root)
            item.unlink()
            item.symlink_to(root / "outside.md")
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review]({item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("non-live", findings[0])

    def test_intent_to_add_queue_item_is_not_live(self):
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            self.git(root, "add", "-N", path)
            findings = self.findings(
                root,
                f"## What to review\n\n1. [Review]({path})\n",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("non-live", findings[0])

    def test_code_fence_comment_and_inline_code_cannot_supply_queue_link(self):
        wrappers = (
            "`[Review]({path})`",
            "<!-- [Review]({path}) -->",
            "```\n[Review]({path})\n```",
        )
        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper[:4]), self.repo() as root:
                item = self.queue_item(root)
                self.git(root, "add", ".")
                hidden = wrapper.format(
                    path=item.relative_to(root).as_posix()
                )
                body = f"## What to review\n\n1. Review this\n{hidden}\n"
                findings = self.findings(root, body)
                self.assertTrue(findings)
                self.assertTrue(any(
                    "exactly one" in finding for finding in findings
                ))

    def test_blockquoted_fence_cannot_supply_action_section_or_link(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "> ```\n"
                "> ## What to review\n"
                f"> 1. [Review]({item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("missing a declared action section", findings[0])

    def test_blockquoted_raw_html_cannot_supply_action_section_or_link(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "> <pre>\n"
                "> ## What to review\n"
                f"> 1. [Review]({item.relative_to(root).as_posix()})\n"
                "> </pre>\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("missing a declared action section", findings[0])

    def test_action_like_directive_outside_declared_section_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]({item.relative_to(root).as_posix()})\n\n"
                "## Deployment\n\n"
                "Approve production now?\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("outside the declared action section", findings[0])

    def test_ordinary_declarative_prose_outside_section_is_accepted(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## Goal\n\n"
                "This change makes review status visible and keeps deployment safe.\n\n"
                "## What to review\n\n"
                f"1. [Review the boundary]({item.relative_to(root).as_posix()})\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_appreciative_orphan_ask_outside_linked_section_is_rejected(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## Goal\n\n"
                "I'd appreciate your feedback on whether the fallback should ship.\n\n"
                "## What to review\n\n"
                f"1. [Review the boundary]({item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("outside the declared action section", findings[0])

    def test_clear_declarative_human_asks_outside_section_are_rejected(self):
        asks = (
            "Maintainer approval is requested before merge.",
            "Approval from a maintainer is required before merge.",
            "Approval from a senior maintainer is required before merge.",
            "Maintainer approval is currently required before merge.",
            "Human review is required before release.",
            "Owner confirmation is needed before deployment.",
            "We need your approval before merge.",
            "I await maintainer confirmation before release.",
            "You must review the boundary before merge.",
            "The owner is requested to confirm the choice.",
        )
        for ask in asks:
            with self.subTest(ask=ask), self.repo() as root:
                body = (
                    f"## Goal\n\n{ask}\n\n"
                    "## What to review\n\nNo human action requested.\n"
                )
                findings = self.findings(root, body)
                self.assertEqual(1, len(findings))
                self.assertIn(
                    "outside the declared action section",
                    findings[0],
                )

    def test_feedback_response_reply_and_comment_requests_are_rejected(self):
        asks = (
            "Please provide feedback on whether the fallback should ship.",
            "Please provide your feedback on the fallback.",
            "Please give feedback on whether the fallback should ship.",
            "Please give us feedback on the fallback.",
            "Please *provide feedback* on whether the fallback should ship.",
            "Please respond to the proposal.",
            "Please reply before merge.",
            "Please **reply** before merge.",
            "For this release, please reply before merge.",
            "We need you to reply before merge.",
            "Please comment on the deployment plan.",
            "Please leave a comment on the deployment plan.",
            "A reply from the owner is requested before merge.",
            "We request feedback from a maintainer.",
            "We ask a maintainer to comment on the deployment plan.",
            "I’d appreciate your feedback on the fallback.",
            "We'd value your input on the deployment plan.",
            "We’d welcome a review of the release boundary.",
            "Your feedback would be appreciated before merge.",
        )
        for ask in asks:
            with self.subTest(ask=ask), self.repo() as root:
                findings = self.findings(
                    root,
                    f"## Goal\n\n{ask}\n\n"
                    "## What to review\n\nNo human action requested.\n",
                )
                self.assertEqual(1, len(findings))
                self.assertIn("outside the declared action section", findings[0])

    def test_feedback_and_response_requests_inside_linked_entry_are_rejected(self):
        asks = (
            "Please provide feedback on whether the fallback should ship.",
            "Please give feedback on the deployment plan.",
            "Please respond before merge.",
            "Please reply before merge.",
            "Please comment on the deployment plan.",
            "Approval from a maintainer is required before merge.",
            "I'd appreciate your feedback on the fallback.",
            "We’d value your input on the deployment plan.",
            "Your review would be welcome before merge.",
        )
        for ask in asks:
            with self.subTest(ask=ask), self.repo() as root:
                item = self.queue_item(root)
                self.git(root, "add", ".")
                body = (
                    "## What to review\n\n"
                    f"1. [Review the boundary]"
                    f"({item.relative_to(root).as_posix()}). {ask}\n"
                )
                findings = self.findings(root, body)
                self.assertEqual(1, len(findings))
                self.assertIn("additional unlinked", findings[0])

    def test_rendered_html_asks_outside_and_inside_action_section_are_rejected(self):
        outside_asks = (
            "<p>Maintainer approval is requested before merge.</p>",
            (
                "<div><strong>Please provide feedback on whether the fallback "
                "should ship.</strong></div>"
            ),
            "<p>Please provide\nfeedback on whether the fallback should ship.</p>",
            "<p>Please<br>reply before merge.</p>",
            "<p>Please&nbsp;reply before merge.</p>",
            "<span>&#10;&#10;</span>\nPlease reply before merge.",
            "<p hidden>Archived request.<p>Please reply before merge.</p>",
            "<script></script>Please reply before merge.",
            "<!-- archived -->Please reply before merge.",
            "> <p>Please reply before merge.</p>",
        )
        for ask in outside_asks:
            with self.subTest(location="outside", ask=ask), self.repo() as root:
                findings = self.findings(
                    root,
                    f"## Goal\n\n{ask}\n\n"
                    "## What to review\n\nNo human action requested.\n",
                )
                self.assertEqual(1, len(findings))
                self.assertIn("outside the declared action section", findings[0])

        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            bodies = (
                (
                    "## What to review\n\n"
                    f"1. [Review the boundary]({path})\n"
                    "   <p>Approval from a maintainer is required before merge.</p>\n"
                ),
                (
                    "## What to review\n\n"
                    f"1. [Review the boundary]({path}). "
                    "<span>Please reply before merge.</span>\n"
                ),
            )
            for body in bodies:
                with self.subTest(location="inside", body=body[-48:]):
                    findings = self.findings(root, body)
                    self.assertEqual(1, len(findings))
                    self.assertIn("rendered HTML", findings[0])

    def test_hidden_html_and_code_do_not_create_human_asks(self):
        hidden = (
            "<!-- Maintainer approval is requested before merge. -->",
            "<script>Maintainer approval is requested before merge.</script>",
            "<style>p::after { content: 'Please reply before merge.'; }</style>",
            "<template>Maintainer approval is requested before merge.</template>",
            "<p hidden>Maintainer approval is requested before merge.</p>",
            (
                '<p aria-hidden="true">Maintainer approval is requested '
                "before merge.</p>"
            ),
            (
                '<p style="display: none">Maintainer approval is requested '
                "before merge.</p>"
            ),
            '<p style="display:\n none">Please reply before merge.</p>',
            '<p style="display:/**/none">Please reply before merge.</p>',
            "<code>Maintainer approval is requested before merge.</code>",
            "```\n<p>Maintainer approval is requested before merge.</p>\n```",
        )
        for content in hidden:
            with self.subTest(content=content[:20]), self.repo() as root:
                body = (
                    f"## Goal\n\n{content}\n\n"
                    "## What to review\n\nNo human action requested.\n"
                )
                self.assertEqual([], self.findings(root, body))

    def test_rendered_html_cannot_supply_a_queue_link(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            body = (
                "## What to review\n\n"
                "1. Review request:\n"
                f'   <p><a href="{path}">Review the boundary</a></p>\n'
            )
            findings = self.findings(root, body)
            self.assertTrue(findings)
            self.assertTrue(any(
                "exactly one valid canonical" in finding
                for finding in findings
            ))

    def test_descriptive_and_negated_action_prose_is_accepted(self):
        with self.repo() as root:
            body = (
                "## Goal\n\n"
                "The approval status is visible in the deployment report.\n"
                "No additional maintainer confirmation is required before merge.\n\n"
                "We do not need your approval for this documentation.\n"
                "You do not need to review the generated report.\n\n"
                "Feedback from a maintainer is not required before merge.\n"
                "No comments are requested for this archived release.\n"
                "Please do not reply to the archived notification.\n"
                "The maintainer responded to feedback on the prior release.\n"
                "Approval from a maintainer was required by the old process.\n\n"
                "Reply metadata remains in the archived audit record.\n"
                "Comment syntax is documented in the archived guide.\n\n"
                "Answer formatting changed in this release.\n\n"
                "Feedback is appreciated in the report.\n"
                "I would not appreciate your feedback on the archived release.\n"
                "We wouldn't value your input on the archived release.\n"
                "We wouldn’t welcome your review of the archived release.\n\n"
                "## What to review\n\nNo human action requested.\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_negated_and_descriptive_feedback_inside_entry_is_accepted(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()}). "
                "Feedback from a maintainer is not required for the archived "
                "release. Feedback is appreciated in the report, and we "
                "wouldn’t welcome your input on the archived release.\n"
            )
            self.assertEqual([], self.findings(root, body))

    def test_absolute_link_requires_explicit_matching_repository_prefix(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            destination = (
                f"https://example.invalid/org/repo/blob/rev/{path}"
            )
            body = (
                "### Human decisions\n\n"
                f"- [Review]({destination})\n"
            )
            self.assertEqual(1, len(self.findings(root, body, "Human decisions")))
            self.assertEqual(
                [],
                self.findings(
                    root,
                    body,
                    "Human decisions",
                    allowed_url_prefixes=(
                        "https://example.invalid/org/repo/blob/rev",
                    ),
                ),
            )
            self.assertEqual(
                1,
                len(self.findings(
                    root,
                    body,
                    "Human decisions",
                    allowed_url_prefixes=(
                        "https://example.invalid/org/repo/blob/other-rev",
                    ),
                )),
            )

    def test_relative_link_uses_explicit_candidate_with_absolute_prefix(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "candidate queue item")
            candidate = self.git(root, "rev-parse", "HEAD")
            path = item.relative_to(root).as_posix()
            body = f"## What to review\n\n1. [Review]({path})\n"
            self.assertEqual(
                [],
                self.findings(
                    root,
                    body,
                    allowed_url_prefixes=(
                        "https://example.invalid/org/repo/blob/"
                        f"{candidate}",
                    ),
                    candidate_revision=candidate,
                ),
            )

    def test_allowed_absolute_prefix_must_bind_candidate_revision(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "candidate queue item")
            candidate = self.git(root, "rev-parse", "HEAD")
            path = item.relative_to(root).as_posix()
            body = f"## What to review\n\n1. [Review]({path})\n"
            with self.assertRaisesRegex(ValueError, "exact candidate revision"):
                self.findings(
                    root,
                    body,
                    allowed_url_prefixes=(
                        "https://example.invalid/org/repo/blob/"
                        + "f" * 40,
                    ),
                    candidate_revision=candidate,
                )

    def test_candidate_revision_controls_queue_liveness(self):
        with self.repo() as root:
            (root / "message-queue/README.md").write_text(
                "# Queue\n", encoding="utf-8"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base queue")
            candidate = self.git(root, "rev-parse", "HEAD")
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            prefix = (
                f"https://example.invalid/org/repo/blob/{candidate}"
            )
            body = f"## What to review\n\n1. [Review]({prefix}/{path})\n"
            findings = self.findings(
                root,
                body,
                allowed_url_prefixes=(prefix,),
                candidate_revision=candidate,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("non-live", findings[0])

    def test_candidate_revision_controls_task_queue_actions_bytes(self):
        task_id = "2026-07-23-candidate-task"
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            task = self.task_record(root, task_id, f"`{path}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "candidate task")
            candidate = self.git(root, "rev-parse", "HEAD")
            task.write_text(
                "# Task\n\n**Queue actions:** none\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            findings = self.findings(
                root,
                "## What to review\n\nNo human action requested.\n",
                task_id=task_id,
                candidate_revision=candidate,
            )
            self.assertEqual(1, len(findings))
            self.assertIn(path, findings[0])

    def test_absolute_link_cannot_hide_queue_path_below_extra_route(self):
        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            body = (
                "## What to review\n\n"
                "1. [Review](https://example.invalid/org/repo/blob/rev/"
                f"issues/7/{path})\n"
            )
            findings = self.findings(
                root,
                body,
                allowed_url_prefixes=(
                    "https://example.invalid/org/repo/blob/rev",
                ),
            )
            self.assertEqual(1, len(findings))
            self.assertIn("exactly one", findings[0])

    def test_cli_reads_shell_metacharacters_as_environment_data(self):
        with self.repo() as root, mock.patch.dict(
            os.environ,
            {
                "BODY": (
                    "## Goal\n\n`$()` must remain data.\n\n"
                    "## What to review\n\nNo human action requested.\n"
                )
            },
        ), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                0,
                PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                ]),
            )

    def test_cli_keeps_non_task_branches_unscoped(self):
        with self.repo() as root, mock.patch.dict(
            os.environ,
            {"BODY": "## What to review\n\nNo human action requested.\n"},
        ), contextlib.redirect_stdout(io.StringIO()):
            self.queue_item(root)
            self.git(root, "add", ".")
            self.assertEqual(
                0,
                PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                    "--branch", "feature/provider-neutral",
                ]),
            )

    def test_cli_non_task_branch_rejects_declarative_orphan_ask(self):
        body = (
            "Maintainer approval is requested before merge.\n\n"
            "## What to review\n\nNo human action requested.\n"
        )
        with self.repo() as root, mock.patch.dict(
            os.environ,
            {"BODY": body},
        ), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                1,
                PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                    "--branch", "feature/provider-neutral",
                ]),
            )

    def test_workflow_passes_pr_body_to_generic_gate_and_reruns_edits(self):
        workflow = (
            MODULE_PATH.parents[1] / ".github/workflows/harness.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("edited", workflow)
        self.assertIn(
            "ACTION_PROJECTION_BODY: ${{ github.event.pull_request.body }}",
            workflow,
        )
        self.assertIn(
            "ACTION_PROJECTION_BRANCH: ${{ github.head_ref }}",
            workflow,
        )
        self.assertIn(
            "ACTION_PROJECTION_CANDIDATE_REVISION: ${{ github.sha }}",
            workflow,
        )
        self.assertIn(
            "ACTION_PROJECTION_REVISION_URL: "
            "${{ github.server_url }}/${{ github.repository }}/blob/"
            "${{ github.sha }}",
            workflow,
        )
        self.assertIn(
            "check_action_projection.py --from-env ACTION_PROJECTION_BODY",
            workflow,
        )
        self.assertIn(
            '--branch "$ACTION_PROJECTION_BRANCH"',
            workflow,
        )
        self.assertIn(
            '--candidate-revision "$ACTION_PROJECTION_CANDIDATE_REVISION"',
            workflow,
        )
        self.assertIn(
            '--allowed-url-prefix "$ACTION_PROJECTION_REVISION_URL"',
            workflow,
        )
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn("github", source)
        self.assertNotIn("codex", source)


if __name__ == "__main__":
    unittest.main()
