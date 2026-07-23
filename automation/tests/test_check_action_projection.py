import contextlib
import importlib.util
import io
import json
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
        actor="needs-human",
        leaf=None,
        external_assignment=None,
    ):
        leaf = leaf or ("reviews" if actor == "needs-human" else "requests")
        path = root / "message-queue" / actor / leaf / name
        path.parent.mkdir(parents=True, exist_ok=True)
        assignment_field = (
            f"**External assignment:** {external_assignment}\n"
            if external_assignment is not None else ""
        )
        path.write_text(
            f"# Review\n\n**Action:** {action}\n"
            f"{assignment_field}",
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
        external_actions=(),
        external_assignments=(),
        additional_prose=(),
        additional_summaries=(),
        allow_missing_action_section_if_no_action=False,
        queue_actor="needs-human",
        required_queue_actor=None,
        require_all_live=True,
    ):
        return PROJECTION.projection_findings(
            body,
            titles or ("What to review",),
            repo=root,
            allowed_url_prefixes=allowed_url_prefixes,
            task_id=task_id,
            candidate_revision=candidate_revision,
            external_actions=external_actions,
            external_assignments=external_assignments,
            additional_prose=additional_prose,
            additional_summaries=additional_summaries,
            allow_missing_action_section_if_no_action=(
                allow_missing_action_section_if_no_action
            ),
            queue_actor=queue_actor,
            required_queue_actor=required_queue_actor,
            require_all_live=require_all_live,
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

    def test_queue_actor_defaults_to_needs_human(self):
        with self.repo() as root:
            agent_item = self.queue_item(
                root,
                name="non-blocking-update-fallback.md",
                action="Update the fallback implementation.",
                actor="needs-agent",
            )
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Update the fallback implementation.]"
                f"({agent_item.relative_to(root).as_posix()})\n"
            )
            findings = self.findings(root, body)
            self.assertEqual(1, len(findings))
            self.assertIn("canonical needs-human", findings[0])

    def test_needs_agent_projection_requires_live_exact_action_link(self):
        with self.repo() as root:
            agent_item = self.queue_item(
                root,
                name="non-blocking-update-fallback.md",
                action="Update the fallback implementation.",
                actor="needs-agent",
            )
            path = agent_item.relative_to(root).as_posix()
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Update the fallback implementation.]({path})\n"
            )
            self.assertEqual(
                [],
                self.findings(root, body, queue_actor="needs-agent"),
            )
            findings = self.findings(
                root,
                f"## What to review\n\n1. [Update the fallback]({path})\n",
                queue_actor="needs-agent",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("exactly match", findings[0])

            agent_item.write_text(
                "# Request\n\n"
                "**Action:** Update the fallback implementation.\n",
                encoding="utf-8",
            )
            self.git(root, "reset")
            findings = self.findings(
                root,
                body,
                queue_actor="needs-agent",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("non-live", findings[0])

    def test_any_actor_uses_each_canonical_path_and_supports_mixed_actions(self):
        with self.repo() as root:
            human_item = self.queue_item(
                root,
                action="Review the boundary.",
            )
            agent_item = self.queue_item(
                root,
                name="non-blocking-update-fallback.md",
                action="Update the fallback implementation.",
                actor="needs-agent",
            )
            human_path = human_item.relative_to(root).as_posix()
            agent_path = agent_item.relative_to(root).as_posix()
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary.]({human_path})\n"
                f"2. [Update the fallback implementation.]({agent_path})\n"
            )
            self.assertEqual(
                [],
                self.findings(root, body, queue_actor="any"),
            )
            findings = self.findings(
                root,
                "## What to review\n\n"
                f"1. [Review the boundary.]({human_path})\n",
                queue_actor="any",
            )
            self.assertEqual(1, len(findings))
            self.assertIn(agent_path, findings[0])

        with self.repo() as root:
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo queued action requested.\n",
                    queue_actor="any",
                ),
            )
            findings = self.findings(
                root,
                "## What to review\n\nNo human action requested.\n",
                queue_actor="any",
            )
            self.assertTrue(findings)

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

    def test_declarative_reference_cue_exempts_supporting_link_title(self):
        references = (
            ("Source:", "Release notes"),
            ("Context:", "Review status"),
            ("Details:", "Merge strategy"),
            ("Reference:", "Audit logs"),
            ("For context:", "Run history"),
            ("For context:", "Update behavior"),
        )
        with self.repo() as root:
            item = self.queue_item(root, action="Review the diff.")
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            for cue, label in references:
                with self.subTest(cue=cue, label=label):
                    self.assertGreater(
                        PROJECTION.link_label_action_count(label),
                        0,
                    )
                    body = (
                        "## What to review\n\n"
                        f"1. [Review the diff]({path}). {cue} "
                        f"[{label}](https://example.invalid/reference).\n"
                    )
                    self.assertEqual([], self.findings(root, body))

    def test_imperative_or_unclosed_cue_cannot_exempt_supporting_action(self):
        fragments = (
            "See [Review code](https://example.invalid/reference).",
            "then [Review code](https://example.invalid/reference).",
            "Please see [Review code](https://example.invalid/reference).",
            "Source: [Should we merge?](https://example.invalid/reference).",
            (
                "Source: [TODO approve production]"
                "(https://example.invalid/reference)."
            ),
            (
                "Source: [approve production]"
                "(https://example.invalid/reference)."
            ),
            (
                "Ignore this source: [Review code]"
                "(https://example.invalid/reference)."
            ),
            (
                "Source: [Review code](https://example.invalid/reference), "
                "then fix it."
            ),
        )
        with self.repo() as root:
            item = self.queue_item(root, action="Review the diff.")
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            for fragment in fragments:
                with self.subTest(fragment=fragment):
                    body = (
                        "## What to review\n\n"
                        f"1. [Review the diff]({path}). {fragment}\n"
                    )
                    findings = self.findings(root, body)
                    self.assertEqual(1, len(findings))
                    self.assertTrue(
                        "action-like supporting link" in findings[0]
                        or "additional unlinked" in findings[0]
                    )

    def test_link_label_count_uses_command_grammar_and_keeps_multiplicity(self):
        for label in (
            "Release notes are attached",
            "Review status is visible",
            "Merge strategy is documented",
            "Vote totals are shown",
            "Audit logs are retained",
            "Run history remains available",
            "Update behavior is documented",
            "Published review policy",
        ):
            with self.subTest(label=label):
                self.assertEqual(
                    0,
                    PROJECTION.link_label_action_count(label),
                )
        for label in (
            "Review code",
            "Run tests",
            "Update docs that are stale",
        ):
            with self.subTest(label=label):
                self.assertEqual(
                    1,
                    PROJECTION.link_label_action_count(label),
                )
        self.assertEqual(
            2,
            PROJECTION.link_label_action_count(
                "Review code and run tests"
            ),
        )
        for label in (
            "Release notes are attached and approve production",
            "Review status is visible and merge the PR",
            "Audit logs are retained and run tests",
            "Update behavior is documented and fix the bug",
        ):
            with self.subTest(label=label):
                self.assertGreater(
                    PROJECTION.link_label_action_count(label),
                    0,
                )
        self.assertEqual(
            0,
            PROJECTION.link_label_action_count(
                "Agents review and approve"
            ),
        )

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

    def test_inline_code_subject_is_preserved_in_action_label_binding(self):
        self.assertNotEqual(
            PROJECTION.normalized_action_tokens(
                "Review `[deploy](staging)`."
            ),
            PROJECTION.normalized_action_tokens(
                "Review `[deploy](production)`."
            ),
        )
        self.assertEqual(
            PROJECTION.normalized_action_tokens(
                "Review [deploy](staging)."
            ),
            PROJECTION.normalized_action_tokens(
                "Review [deploy](production)."
            ),
        )
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Review the `staging` deployment.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            for label in (
                "Review the staging deployment",
                "Review the `staging` deployment",
            ):
                with self.subTest(label=label):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            f"## What to review\n\n1. [{label}]({path})\n",
                        ),
                    )
            findings = self.findings(
                root,
                "## What to review\n\n"
                f"1. [Review the `production` deployment]({path})\n",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("canonical `Action`", findings[0])

    def test_exact_unseen_action_verb_label_is_accepted_but_prefix_is_not(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Calibrate the boundary precisely.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\n"
                    f"1. [Calibrate the boundary precisely]({path})\n",
                ),
            )
            findings = self.findings(
                root,
                "## What to review\n\n"
                f"1. [Calibrate the boundary]({path})\n",
            )
            self.assertEqual(1, len(findings))
            self.assertIn("canonical `Action`", findings[0])

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

    def test_missing_section_can_be_optional_only_for_nonaction_prose(self):
        cases = (
            (
                "## Compatibility\n\nFixes parsing of ?foo query strings.\n",
                (),
                (),
                False,
            ),
            (
                "Routine status update.\n",
                ("Compatibility notes for this release",),
                ("[]", "{}"),
                False,
            ),
            (
                "A maintainer should select option A or B before merge.\n",
                (),
                (),
                True,
            ),
            (
                "<p>Feedback welcome.</p>\n",
                (),
                (),
                True,
            ),
            (
                "- Feedback welcome.\n",
                (),
                (),
                True,
            ),
            (
                "Routine status update.\n",
                ("Should the fallback ship?",),
                (),
                True,
            ),
            (
                "Routine status update.\n",
                (),
                ('[{"login": "reviewer"}]',),
                True,
            ),
        )
        with self.repo() as root:
            for body, additional, external, should_fail in cases:
                with self.subTest(body=body, additional=additional):
                    findings = self.findings(
                        root,
                        body,
                        additional_prose=additional,
                        external_actions=external,
                        allow_missing_action_section_if_no_action=True,
                    )
                    self.assertEqual(should_fail, bool(findings))
                    if should_fail:
                        self.assertTrue(any(
                            "missing a declared action section" in finding
                            or "additional prose input" in finding
                            for finding in findings
                        ))
        with self.repo() as root:
            self.queue_item(root)
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "Routine status update.\n",
                    allow_missing_action_section_if_no_action=True,
                ),
            )

    def test_visible_unchecked_task_list_is_an_action_without_verb_hardcoding(self):
        pending = (
            "- [ ] Migrate the database before release.\n",
            "1. [ ] Rehydrate the archive before release.\n",
            "> - [ ] Calibrate the unknown provider before release.\n",
        )
        completed_or_literal = (
            "- [x] Migrate the database before release.\n",
            "- [X] Review this change.\n",
            "`- [ ] Migrate the database before release.`\n",
            "```\n- [ ] Migrate the database before release.\n```\n",
            "    - [ ] Migrate the database before release.\n",
            "The migration guide shows `- [ ]` as its template syntax.\n",
            "Adds support for database migrations.\n",
            "The service migrates the database before release.\n",
        )
        with self.repo() as root:
            for body in pending:
                with self.subTest(kind="pending", body=body):
                    findings = self.findings(
                        root,
                        body,
                        allow_missing_action_section_if_no_action=True,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )
            for body in completed_or_literal:
                with self.subTest(kind="non-action", body=body):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            body,
                            allow_missing_action_section_if_no_action=True,
                        ),
                    )

    def test_default_ignorable_characters_cannot_obfuscate_visible_actions(self):
        asks = (
            "Rev\u200biew this change.\n",
            "Re\u2060view this change.\n",
            "Rev\ufe0fiew this change.\n",
            "Ｒｅｖｉｅｗ this change.\n",
            "[Rev\u200biew this change.](https://example.invalid/context)\n",
            "<span>Rev&#x200b;iew this change.</span>\n",
        )
        literal_or_structural = (
            "`Rev\u200biew this change.`\n",
            "```\nRev\u200biew this change.\n```\n",
            "    Rev\u200biew this change.\n",
            (
                "[Migration reference]"
                "(https://example.invalid/Rev\u200biew-this-change)\n"
            ),
        )
        with self.repo() as root:
            for body in asks:
                with self.subTest(kind="visible", body=body):
                    findings = self.findings(
                        root,
                        body,
                        allow_missing_action_section_if_no_action=True,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )
            for body in literal_or_structural:
                with self.subTest(kind="literal", body=body):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            body,
                            allow_missing_action_section_if_no_action=True,
                        ),
                    )
            findings = self.findings(
                root,
                "Routine compatibility update.\n",
                additional_prose=("Rev\u200biew this change.",),
                allow_missing_action_section_if_no_action=True,
            )
            self.assertEqual(2, len(findings))
            self.assertTrue(any(
                "additional prose input" in finding for finding in findings
            ))

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

    def test_heading_and_idiomatic_asks_outside_section_are_rejected(self):
        asks = (
            "## Please approve and merge this change",
            "Take a look when you can.",
            "Take a quick look when you can.",
            "Take one last look before merge.",
            "Have a look when you can.",
            "Have another careful look before merge.",
            "Chime in with feedback.",
            "Weigh in on the fallback.",
            "Ping me with any concerns.",
            "Assigned to Alice: squash the login race before merge.",
            "Assignee: @alice — squash the login race before merge.",
        )
        for ask in asks:
            with self.subTest(ask=ask), self.repo() as root:
                task_id = "2026-07-23-orphan-provider-ask"
                self.task_record(root, task_id, "none")
                self.git(root, "add", ".")
                findings = self.findings(
                    root,
                    f"{ask}\n\n## What to review\n\n"
                    "No queued action requested.\n",
                    task_id=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                )
                self.assertEqual(1, len(findings))
                self.assertIn(
                    "outside the declared action section",
                    findings[0],
                )

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

    def test_absent_or_historical_assignment_prose_is_not_an_action(self):
        descriptions = (
            "Assigned to nobody.",
            "The issue was assigned to Alice last week.",
            "Previously assigned to Alice.",
        )
        for description in descriptions:
            with self.subTest(description=description):
                self.assertFalse(
                    PROJECTION.action_like_prose(description)
                )

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
            "A maintainer should select option A or B before merge.",
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

    def test_agent_role_obligations_are_actions_but_capabilities_are_not(self):
        actions = (
            "A Codex agent must fix the failing test before merge.",
            "The agent must review the migration before merge.",
            "Bots should fix the failing check.",
            "The worker needs to update the generated snapshot.",
            "An automation worker is requested to retry the job.",
            "The coding assistant should review the release notes.",
            "Reviewers must assess the security impact before merge.",
            "A reviewer is requested to evaluate the migration.",
            "Reviewers must carefully assess the migration.",
            "You must never merge this branch.",
            "Reviewers must not disclose credentials.",
        )
        descriptions = (
            "The bot should not update the snapshot.",
            "The bot should generally not update the snapshot.",
            "The worker updated the snapshot yesterday.",
            "The agent must be able to review changes offline.",
            "The assistant was requested to retry the old job.",
            "The reviewer must be able to assess changes offline.",
            "The reviewer must always be able to assess changes offline.",
            "Reviewers should see failure reasons inline.",
        )
        for action in actions:
            with self.subTest(action=action):
                self.assertTrue(PROJECTION.action_like_plain_prose(action))
        for description in descriptions:
            with self.subTest(description=description):
                self.assertFalse(
                    PROJECTION.action_like_plain_prose(description)
                )

        with self.repo() as root:
            findings = self.findings(
                root,
                actions[0],
                allow_missing_action_section_if_no_action=True,
                queue_actor="any",
                require_all_live=False,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("missing a declared action section", findings[0])

    def test_indirect_recipient_solicitations_are_actions(self):
        actions = (
            "I'm curious what you think about the migration.",
            "We are curious how you would approach the fallback.",
            "I’m curious to hear your feedback on the rollout.",
            "I'm interested in your perspective on the release.",
            "I wonder whether you think the fallback should ship.",
        )
        descriptions = (
            "I'm curious what the bot reported.",
            "I was curious what you thought during the retrospective.",
            "The report explains what you think is a regression.",
            "I am not curious what you think about the archived release.",
        )
        for action in actions:
            with self.subTest(action=action):
                self.assertTrue(PROJECTION.action_like_plain_prose(action))
        for description in descriptions:
            with self.subTest(description=description):
                self.assertFalse(
                    PROJECTION.action_like_plain_prose(description)
                )

        with self.repo() as root:
            item = self.queue_item(root)
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            outside = (
                f"{actions[0]}\n\n"
                "## What to review\n\n"
                f"1. [Review the boundary.]({path})\n"
            )
            findings = self.findings(root, outside, queue_actor="any")
            self.assertEqual(1, len(findings))
            self.assertIn("outside the declared action section", findings[0])

            inside = (
                "## What to review\n\n"
                f"1. [Review the boundary.]({path}) — {actions[2]}\n"
            )
            findings = self.findings(root, inside, queue_actor="any")
            self.assertEqual(1, len(findings))
            self.assertIn("additional unlinked", findings[0])

    def test_passive_work_appreciation_is_an_action(self):
        actions = (
            "A fix would be appreciated.",
            "A fix would be greatly appreciated.",
            "A fix would be appreciated before merge.",
            "More test coverage would be helpful.",
            "More test coverage would be very helpful.",
            "This migration repair would be welcome.",
            "It would be appreciated if you fixed the race.",
        )
        descriptions = (
            "A fix would not be appreciated.",
            "A fix would have been appreciated.",
            "A fix would be appreciated by users of the old release.",
            "The archived issue said a fix would be appreciated.",
        )
        for action in actions:
            with self.subTest(action=action):
                self.assertTrue(PROJECTION.action_like_plain_prose(action))
        for description in descriptions:
            with self.subTest(description=description):
                self.assertFalse(
                    PROJECTION.action_like_plain_prose(description)
                )

        with self.repo() as root:
            findings = self.findings(
                root,
                actions[0],
                allow_missing_action_section_if_no_action=True,
                queue_actor="any",
                require_all_live=False,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("missing a declared action section", findings[0])

    def test_provider_summary_allows_change_verbs_but_not_authority_asks(self):
        summaries = (
            "Fix the login race.",
            "Update dependency metadata.",
            "Implement retry backoff.",
        )
        actions = (
            "Review this change.",
            "Rev\u200biew this change.",
            "Please fix the login race.",
            "Fix the login race and please review the security implications.",
            "Fix the login race - please review the security implications.",
            "Implement retry backoff and approve this change.",
            "Should we merge?",
            "TODO: fix the login race.",
            "A reviewer must assess the security impact.",
            "A fix would be appreciated.",
            "Reviewers must not disclose credentials.",
        )
        for summary in summaries:
            with self.subTest(summary=summary):
                self.assertFalse(
                    PROJECTION.action_like_summary_prose(summary)
                )
        for action in actions:
            with self.subTest(action=action):
                self.assertTrue(
                    PROJECTION.action_like_summary_prose(action)
                )

        with self.repo() as root:
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo queued action requested.\n",
                    queue_actor="any",
                    require_all_live=False,
                    additional_summaries=(summaries[0],),
                ),
            )
            findings = self.findings(
                root,
                "## What to review\n\nNo queued action requested.\n",
                queue_actor="any",
                require_all_live=False,
                additional_summaries=(actions[0],),
            )
            self.assertEqual(1, len(findings))
            self.assertIn("additional summary input", findings[0])

    def test_boundary_until_human_review_is_an_action_request(self):
        asks = (
            "This cannot merge until the maintainer looks over the migration.",
            "This cannot be merged until a reviewer has reviewed the migration.",
            "Merge cannot proceed until the owner approves the migration.",
            "Release is blocked until maintainer approval.",
            "This task is blocked until owner confirmation.",
            "Work cannot continue until a maintainer reviews it.",
            "Implementation stops at merge until human review.",
            "The release stays blocked until review by the owner.",
            "The merge remains blocked pending maintainer approval.",
            "The task will remain blocked until owner approval.",
            "The release will be blocked pending review by a maintainer.",
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
            "Feedback welcome.",
            "Feedback is welcome.",
            "Reviews are welcome.",
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
            "Feedback welcome.",
            "Feedback is welcome.",
            "Reviews are welcome.",
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

    def test_ordinary_courtesy_and_open_verb_requests_are_rejected(self):
        asks = (
            "Let me know whether the fallback should ship.",
            "Let us know if the Linux build is acceptable.",
            "Please benchmark the fallback before merge.",
            "Please test the Linux build before merge.",
            "Please run the release check before merge.",
            "Please fix the deployment note before merge.",
            "Please update the compatibility table before merge.",
            "Please triage the failed job before merge.",
            "Please reproduce the timeout before merge.",
            "Please investigate the timeout before merge.",
            "Would you benchmark the fallback before merge.",
            "Can the maintainer investigate the timeout before merge.",
            "I need you to benchmark the fallback before merge.",
            "Keep me posted on the release decision.",
            "Please do not merge yet.",
            "Could you not delete production yet.",
            "I need you not to merge the fallback yet.",
        )
        for ask in asks:
            with self.subTest(location="outside", ask=ask), self.repo() as root:
                findings = self.findings(
                    root,
                    f"## Goal\n\n{ask}\n\n"
                    "## What to review\n\nNo human action requested.\n",
                )
                self.assertEqual(1, len(findings))
                self.assertIn("outside the declared action section", findings[0])
            with self.subTest(location="inside", ask=ask), self.repo() as root:
                item = self.queue_item(root)
                self.git(root, "add", ".")
                findings = self.findings(
                    root,
                    "## What to review\n\n"
                    f"1. [Review the boundary]"
                    f"({item.relative_to(root).as_posix()}). {ask}\n",
                )
                self.assertEqual(1, len(findings))
                self.assertIn("additional unlinked", findings[0])

    def test_base_form_work_commands_are_actions_but_summaries_are_not(self):
        commands = (
            "Investigate the production crash now.",
            "Debug the release failure.",
            "Fix parsing before merge.",
            "Analyze the benchmark regression.",
            "Audit the migration.",
            "Review the migration.",
            "Release this build.",
            "Merge the pull request.",
            "Vote on the proposal.",
            "Review code before merge.",
            "Merge PR 42.",
            "Release v1.2.",
            "Vote yes.",
            "Audit dependencies.",
            "Check logs.",
            "Debug failures.",
            "Document behavior.",
            "Run tests.",
            "Test Linux.",
            "Update docs.",
            "Update docs that are stale.",
            "Audit logs that contain PII.",
            "Run tests that are failing.",
            "Review code that is security-sensitive.",
        )
        summaries = (
            "Adds support for release channels.",
            "Fixes parsing of query strings.",
            "Investigates production crash reports.",
            "The change fixes parsing of query strings.",
        )
        with self.repo() as root:
            for command in commands:
                with self.subTest(command=command):
                    findings = self.findings(
                        root,
                        command,
                        allow_missing_action_section_if_no_action=True,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )
            for summary in summaries:
                with self.subTest(summary=summary):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            summary,
                            allow_missing_action_section_if_no_action=True,
                        ),
                    )

    def test_summary_clause_cannot_hide_a_conjoined_command(self):
        actions = (
            "Release notes are attached and approve production.",
            "Review status is visible and merge the PR.",
            "Audit logs are retained and run tests.",
            "Update behavior is documented and fix the bug.",
        )
        summaries = (
            "Agents review and approve.",
            "Audit logs are retained and run history remains available.",
        )
        with self.repo() as root:
            for action in actions:
                with self.subTest(action=action):
                    findings = self.findings(
                        root,
                        action,
                        allow_missing_action_section_if_no_action=True,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )
            for summary in summaries:
                with self.subTest(summary=summary):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            summary,
                            allow_missing_action_section_if_no_action=True,
                        ),
                    )

    def test_benchmark_and_notification_descriptions_or_negations_are_accepted(self):
        with self.repo() as root:
            body = (
                "## Goal\n\n"
                "Benchmark results are recorded in the report.\n"
                "The test runner updates the compatibility table.\n"
                "Test coverage is 92 percent.\n"
                "Update behavior is documented.\n"
                "Audit logs are retained.\n"
                "Profile names describe assurance ceilings.\n"
                "Document metadata is immutable.\n"
                "Address fields are redacted.\n"
                "Trace output appears below.\n"
                "Run history remains available.\n"
                "The task was blocked until owner confirmation.\n"
                "The release remained blocked until review by the owner.\n"
                "The task is not blocked until owner confirmation.\n"
                "The task no longer is blocked until owner confirmation.\n"
                "The task will not be blocked until owner confirmation.\n"
                "The task will no longer remain blocked until owner confirmation.\n"
                "Release notes are attached.\n"
                "Review status is visible.\n"
                "Merge strategy is documented.\n"
                "Vote totals are shown.\n"
                "This alert lets me know whether the build completed.\n"
                "We do not need you to reproduce the archived timeout.\n\n"
                "The release alert keeps me posted on completed jobs.\n\n"
                "## What to review\n\nNo human action requested.\n"
            )
            self.assertEqual([], self.findings(root, body))

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
            "<img alt='Please approve production'>",
            "<input value='Please benchmark production'>",
            "<input placeholder='Please benchmark production'>",
            "<button aria-label='Please approve production'></button>",
            "<span title='Please approve production'></span>",
            "<textarea placeholder='Please review production'></textarea>",
            "<textarea>Please approve production</textarea>",
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
                (
                    "## What to review\n\n"
                    f"1. [Review the boundary]({path})\n"
                    "   <a href='https://example.invalid/delete'>"
                    "<img alt='Please delete production now'></a>\n"
                ),
            )
            for body in bodies:
                with self.subTest(location="inside", body=body[-48:]):
                    findings = self.findings(root, body)
                    self.assertEqual(1, len(findings))
                    self.assertIn("rendered HTML", findings[0])

    def test_rendered_action_api_detects_raw_html_outside_projection_entries(self):
        handover_prose = (
            "## Summary\n\n"
            "<p>A maintainer should select option A or B before merge.</p>\n"
        )
        self.assertTrue(
            PROJECTION.action_like_rendered_prose(handover_prose)
        )
        self.assertTrue(
            PROJECTION.action_like_rendered_prose(
                "<img alt='Feedback welcome.'>"
            )
        )
        self.assertFalse(
            PROJECTION.action_like_rendered_prose(
                "<p hidden>Feedback welcome.</p>"
            )
        )

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
            "<input type='hidden' value='Please approve production'>",
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
                "Feedback is not requested for this archived release.\n"
                "Feedback is not welcome in this archived record.\n"
                "No comments are requested for this archived release.\n"
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

    def test_task_queue_actions_value_uses_closed_projection_syntax(self):
        first = (
            "message-queue/needs-human/reviews/"
            "future-blocking-review-first.md"
        )
        second = (
            "message-queue/needs-agent/requests/"
            "non-blocking-update-second.md"
        )
        accepted = (
            ("none", ()),
            (f"`{first}`", (first,)),
            (f"`{first}`; `{second}`", (first, second)),
            (f"`{first}`, `{second}`", (first, second)),
        )
        rejected = (
            f"none; `{first}`",
            f"`{first}`; please review it",
            f"`{first}`;",
            first,
            f"`{first}`; `{first}`",
        )
        for value, expected in accepted:
            with self.subTest(accepted=value):
                self.assertEqual(
                    expected,
                    PROJECTION.parse_task_queue_action_value(value),
                )
        for value in rejected:
            with self.subTest(rejected=value):
                with self.assertRaises(ValueError):
                    PROJECTION.parse_task_queue_action_value(value)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            PROJECTION.task_queue_action_paths_from_text(
                f"**Queue actions:** `{first}`\n"
                f"**Queue actions:** `{second}`\n"
            )

    def test_task_scope_rejects_trailing_queue_actions_prose(self):
        task_id = "2026-07-23-closed-task-projection"
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            self.task_record(
                root,
                task_id,
                f"`{path}` — I’m curious what you think about deployment.",
            )
            self.git(root, "add", ".")
            with self.assertRaisesRegex(
                RuntimeError, "invalid Queue actions field"
            ):
                self.findings(
                    root,
                    "## What to review\n\n"
                    f"1. [Review the boundary.]({path})\n",
                    task_id=task_id,
                )

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

    def test_external_action_state_requires_at_least_one_queue_projection(self):
        no_action = "## What to review\n\nNo human action requested.\n"
        empty_states = ("", "[]", "{}", '[""]')
        with self.repo() as root:
            self.assertEqual(
                [],
                self.findings(
                    root,
                    no_action,
                    external_actions=empty_states,
                ),
            )
            findings = self.findings(
                root,
                no_action,
                external_actions=(
                    "[]",
                    '[{"login": "reviewer"}]',
                    "{}",
                ),
            )
            self.assertEqual(1, len(findings))
            self.assertIn("externally assigned action state", findings[0])

            item = self.queue_item(root)
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the boundary]"
                f"({item.relative_to(root).as_posix()})\n"
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    body,
                    external_actions=(
                        "[]",
                        '[{"slug": "release-team"}]',
                    ),
                ),
            )

    def test_external_action_cardinality_requires_distinct_queue_paths(self):
        with self.repo() as root:
            first = self.queue_item(
                root,
                "future-blocking-review-first-assignment.md",
                action="Review the first assignment.",
            )
            second = self.queue_item(
                root,
                "future-blocking-review-second-assignment.md",
                action="Review the second assignment.",
            )
            first_path = first.relative_to(root).as_posix()
            second_path = second.relative_to(root).as_posix()
            self.git(root, "add", ".")
            one_link = (
                "## What to review\n\n"
                f"1. [Review the first assignment.]({first_path})\n"
            )
            two_links = (
                one_link
                + f"2. [Review the second assignment.]({second_path})\n"
            )
            duplicate_link = (
                one_link
                + f"2. [Review the first assignment.]({first_path})\n"
            )

            two_reviewers = (
                '[{"login": "alice"}, {"login": "bob"}]',
            )
            findings = self.findings(
                root,
                one_link,
                external_actions=two_reviewers,
                require_all_live=False,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("contains 2 action(s)", findings[0])
            self.assertIn("only 1 distinct", findings[0])
            self.assertEqual(
                [],
                self.findings(
                    root,
                    two_links,
                    external_actions=two_reviewers,
                    require_all_live=False,
                ),
            )
            findings = self.findings(
                root,
                duplicate_link,
                external_actions=two_reviewers,
                require_all_live=False,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("only 1 distinct", findings[0])

            repeated_envs = (
                '{"login": "alice"}',
                '[{"slug": "release-team"}]',
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    two_links,
                    external_actions=repeated_envs,
                    require_all_live=False,
                ),
            )
            duplicated_records = (
                '[{"login": "alice"}, {"login": "alice"}]',
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    two_links,
                    external_actions=duplicated_records,
                    require_all_live=False,
                ),
            )

    def test_external_action_cardinality_handles_objects_scalars_and_nesting(self):
        empty_states = (
            "",
            "[]",
            "{}",
            "false",
            "0",
            '["", null, false, 0, {}, [], {"team": []}]',
            '{"reviewers": [], "teams": {"members": []}}',
        )
        for state in empty_states:
            with self.subTest(state=state):
                self.assertEqual(
                    0,
                    PROJECTION.external_action_state_count(state),
                )

        one_action_states = (
            '{"login": "alice"}',
            '{"reviewer": {"login": "alice"}}',
            '{"alice": true, "bob": true}',
            "changes_requested",
            "true",
            "1",
            '[[{"login": "alice"}, {"login": "bob"}]]',
        )
        for state in one_action_states:
            with self.subTest(state=state):
                self.assertEqual(
                    1,
                    PROJECTION.external_action_state_count(state),
                )

        self.assertEqual(
            2,
            PROJECTION.external_action_state_count(
                '[{"reviewer": {"login": "alice"}}, '
                '[{"login": "bob"}], {}, []]'
            ),
        )

        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Apply the requested review changes.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            body = (
                "## What to review\n\n"
                f"1. [Apply the requested review changes.]({path})\n"
            )
            for state in ("changes_requested", '{"login": "alice"}'):
                with self.subTest(state=state):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            body,
                            external_actions=(state,),
                            require_all_live=False,
                        ),
                    )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo human action requested.\n",
                    external_actions=empty_states,
                    require_all_live=False,
                ),
            )

    def test_external_assignments_preserve_actor_direction_and_cardinality(self):
        with self.repo() as root:
            human = self.queue_item(
                root,
                action="Review the human-facing migration.",
                external_assignment="alice",
            )
            agent = self.queue_item(
                root,
                name="non-blocking-review-automated-migration.md",
                action="Review the automated migration.",
                actor="needs-agent",
                external_assignment="copilot-pull-request-reviewer[bot]",
            )
            second_agent = self.queue_item(
                root,
                name="non-blocking-review-second-automated-migration.md",
                action="Review the second automated migration.",
                actor="needs-agent",
                external_assignment="copilot-pull-request-reviewer[bot]",
            )
            self.git(root, "add", ".")
            human_path = human.relative_to(root).as_posix()
            agent_path = agent.relative_to(root).as_posix()
            second_agent_path = second_agent.relative_to(root).as_posix()
            human_link = (
                "## What to review\n\n"
                f"1. [Review the human-facing migration.]({human_path})\n"
            )
            agent_link = (
                "## What to review\n\n"
                f"1. [Review the automated migration.]({agent_path})\n"
            )
            both_links = (
                human_link
                + f"2. [Review the automated migration.]({agent_path})\n"
            )
            bot_assignment = json.dumps([{
                "actor": "needs-agent",
                "identity": "copilot-pull-request-reviewer[bot]",
            }])
            mixed_assignments = json.dumps([
                {"actor": "needs-human", "identity": "alice"},
                {
                    "actor": "needs-agent",
                    "identity": "copilot-pull-request-reviewer[bot]",
                },
            ])

            findings = self.findings(
                root,
                human_link,
                external_assignments=(bot_assignment,),
                queue_actor="any",
                require_all_live=False,
            )
            self.assertTrue(any(
                "for needs-agent" in finding
                and "only 0 distinct" in finding
                for finding in findings
            ), findings)
            self.assertEqual(
                [],
                self.findings(
                    root,
                    agent_link,
                    external_assignments=(bot_assignment,),
                    queue_actor="any",
                    require_all_live=False,
                ),
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    both_links,
                    external_assignments=(mixed_assignments,),
                    queue_actor="any",
                    require_all_live=False,
                ),
            )

            duplicate_bots = json.dumps([
                {
                    "actor": "needs-agent",
                    "identity": "copilot-pull-request-reviewer[bot]",
                },
                {
                    "actor": "needs-agent",
                    "identity": "copilot-pull-request-reviewer[bot]",
                },
            ])
            findings = self.findings(
                root,
                agent_link,
                external_assignments=(duplicate_bots,),
                queue_actor="any",
                require_all_live=False,
            )
            self.assertTrue(any(
                "contains 2 action(s)" in finding
                for finding in findings
            ), findings)
            self.assertEqual(
                [],
                self.findings(
                    root,
                    agent_link
                    + (
                        "2. [Review the second automated migration.]"
                        f"({second_agent_path})\n"
                    ),
                    external_assignments=(duplicate_bots,),
                    queue_actor="any",
                    require_all_live=False,
                ),
            )

    def test_external_assignment_shape_and_direction_fail_closed(self):
        malformed = (
            "{}",
            '[{"actor": "needs-agent"}]',
            '[{"actor": "needs-agent", "identity": ""}]',
            '[{"actor": "any", "identity": "reviewer"}]',
            '[{"actor": "Bot", "identity": "reviewer"}]',
            '["needs-agent"]',
        )
        with self.repo() as root:
            for assignments in malformed:
                with self.subTest(assignments=assignments), self.assertRaises(
                        ValueError):
                    self.findings(
                        root,
                        "## What to review\n\nNo queued action requested.\n",
                        external_assignments=(assignments,),
                        queue_actor="any",
                        require_all_live=False,
                    )
            with self.assertRaisesRegex(
                    ValueError, "directionless external action state"):
                self.findings(
                    root,
                    "## What to review\n\nNo queued action requested.\n",
                    external_actions=('[{"login": "reviewer"}]',),
                    queue_actor="any",
                    require_all_live=False,
                )

    def test_required_actor_can_preserve_human_task_scope_on_mixed_surface(self):
        task_id = "2026-07-23-mixed-assignment-scope"
        with self.repo() as root:
            human = self.queue_item(
                root,
                action="Review the human-facing migration.",
            )
            agent = self.queue_item(
                root,
                name="non-blocking-review-automated-migration.md",
                action="Review the automated migration.",
                actor="needs-agent",
            )
            human_path = human.relative_to(root).as_posix()
            agent_path = agent.relative_to(root).as_posix()
            self.task_record(
                root,
                task_id,
                f"`{human_path}`, `{agent_path}`",
            )
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"1. [Review the human-facing migration.]({human_path})\n"
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    body,
                    task_id=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                ),
            )
            findings = self.findings(
                root,
                body,
                task_id=task_id,
                queue_actor="any",
            )
            self.assertEqual(1, len(findings))
            self.assertIn(agent_path, findings[0])

    def test_scoped_external_assignment_requires_task_owned_queue_path(self):
        task_id = "2026-07-23-scoped-bot-assignment"
        with self.repo() as root:
            unrelated = self.queue_item(
                root,
                name="non-blocking-review-unrelated-bot-work.md",
                action="Review unrelated bot work.",
                actor="needs-agent",
                external_assignment="review-bot",
            )
            wrong = self.queue_item(
                root,
                name="non-blocking-review-wrong-bot-work.md",
                action="Review wrong bot work.",
                actor="needs-agent",
            )
            matching = self.queue_item(
                root,
                name="non-blocking-review-assigned-bot-work.md",
                action="Review assigned bot work.",
                actor="needs-agent",
                external_assignment="review-bot",
            )
            unrelated_path = unrelated.relative_to(root).as_posix()
            wrong_path = wrong.relative_to(root).as_posix()
            matching_path = matching.relative_to(root).as_posix()
            self.task_record(
                root,
                task_id,
                f"`{wrong_path}`, `{matching_path}`",
            )
            self.git(root, "add", ".")
            assignment = (json.dumps([{
                "actor": "needs-agent",
                "identity": "review-bot",
            }]),)
            cases = (
                ("Review unrelated bot work.", unrelated_path),
                ("Review wrong bot work.", wrong_path),
            )
            for label, path in cases:
                with self.subTest(path=path):
                    findings = self.findings(
                        root,
                        (
                            "## What to review\n\n"
                            f"1. [{label}]({path})\n"
                        ),
                        task_id=task_id,
                        queue_actor="any",
                        required_queue_actor="needs-human",
                        external_assignments=assignment,
                    )
                    self.assertTrue(any(
                        "External assignment" in finding
                        for finding in findings
                    ), findings)
            self.assertEqual(
                [],
                self.findings(
                    root,
                    (
                        "## What to review\n\n"
                        "1. [Review assigned bot work.]"
                        f"({matching_path})\n"
                    ),
                    task_id=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                    external_assignments=assignment,
                ),
            )

    def test_mixed_pr_surface_uses_queued_no_action_marker(self):
        task_id = "2026-07-23-no-pr-actions"
        with self.repo() as root:
            self.task_record(root, task_id, "none")
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                self.findings(
                    root,
                    "## What to review\n\nNo queued action requested.\n",
                    task_id=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                ),
            )
            findings = self.findings(
                root,
                "## What to review\n\nNo human action requested.\n",
                task_id=task_id,
                queue_actor="any",
                required_queue_actor="needs-human",
            )
            self.assertTrue(findings)
            self.assertTrue(any(
                "no queue-linked action" in finding
                or "top-level action list" in finding
                for finding in findings
            ))

    def test_additional_plain_prose_cannot_hide_an_action(self):
        no_action = "## What to review\n\nNo human action requested.\n"
        with self.repo() as root:
            self.assertEqual(
                [],
                self.findings(
                    root,
                    no_action,
                    additional_prose=("Compatibility notes for this release",),
                ),
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    no_action,
                    additional_prose=(
                        "Fixes parsing of ?foo query strings",
                        "Fixes parsing of '?' and \"?\" literals",
                    ),
                ),
            )
            self.assertTrue(PROJECTION.action_like_plain_prose(
                "Should the fallback ship?"
            ))
            for title in (
                "Should the fallback ship?",
                "Please benchmark the fallback before merge",
                "`Please reproduce the timeout before merge`",
            ):
                with self.subTest(title=title):
                    findings = self.findings(
                        root,
                        no_action,
                        additional_prose=(title,),
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn("additional prose input", findings[0])

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

    def test_cli_can_allow_missing_section_only_for_nonaction_provider_prose(self):
        args = [
            "--from-env", "BODY",
            "--action-section", "What to review",
            "--allow-missing-action-section-if-no-action",
        ]
        with self.repo() as root, mock.patch.dict(
            os.environ,
            {"BODY": "Routine status update.\n"},
        ), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, PROJECTION.main(args))
            os.environ["BODY"] = "Feedback welcome.\n"
            self.assertEqual(1, PROJECTION.main(args))

    def test_cli_queue_actor_selects_inbound_agent_actions(self):
        with self.repo() as root:
            agent_item = self.queue_item(
                root,
                name="non-blocking-update-fallback.md",
                action="Update the fallback implementation.",
                actor="needs-agent",
            )
            self.git(root, "add", ".")
            path = agent_item.relative_to(root).as_posix()
            env = {
                "BODY": (
                    "## What to review\n\n"
                    f"1. [Update the fallback implementation.]({path})\n"
                ),
            }
            args = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--unscoped",
            ]
            with mock.patch.dict(os.environ, env), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, PROJECTION.main(args))
                self.assertEqual(
                    0,
                    PROJECTION.main([
                        *args,
                        "--queue-actor", "needs-agent",
                    ]),
                )

    def test_cli_reads_actor_preserving_external_assignments(self):
        with self.repo() as root:
            agent_item = self.queue_item(
                root,
                name="non-blocking-review-automated-migration.md",
                action="Review the automated migration.",
                actor="needs-agent",
                external_assignment="copilot-pull-request-reviewer[bot]",
            )
            self.git(root, "add", ".")
            path = agent_item.relative_to(root).as_posix()
            env = {
                "BODY": (
                    "## What to review\n\n"
                    f"1. [Review the automated migration.]({path})\n"
                ),
                "ASSIGNMENTS": json.dumps([{
                    "actor": "needs-agent",
                    "identity": "copilot-pull-request-reviewer[bot]",
                }]),
            }
            with mock.patch.dict(os.environ, env), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--external-assignment-env", "ASSIGNMENTS",
                        "--queue-actor", "any",
                        "--unscoped",
                    ]),
                )

    def test_cli_unscoped_inbound_agent_surface_accepts_task_action_subset(self):
        task_id = "2026-07-23-two-agent-actions"
        with self.repo() as root:
            first = self.queue_item(
                root,
                name="non-blocking-update-parser.md",
                action="Update the parser.",
                actor="needs-agent",
            )
            second = self.queue_item(
                root,
                name="non-blocking-update-renderer.md",
                action="Update the renderer.",
                actor="needs-agent",
            )
            first_path = first.relative_to(root).as_posix()
            second_path = second.relative_to(root).as_posix()
            self.task_record(
                root,
                task_id,
                f"`{first_path}`, `{second_path}`",
            )
            self.git(root, "add", ".")
            env = {
                "BODY": (
                    "## What to review\n\n"
                    f"1. [Update the parser.]({first_path})\n"
                ),
            }
            common = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--queue-actor", "needs-agent",
            ]
            with mock.patch.dict(os.environ, env), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    1,
                    PROJECTION.main([
                        *common,
                        "--branch", f"task/{task_id}",
                    ]),
                )
                self.assertEqual(
                    0,
                    PROJECTION.main([
                        *common,
                        "--unscoped",
                    ]),
                )

    def test_cli_reads_multiple_generic_external_state_and_prose_envs(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Review the first assignment.",
            )
            second = self.queue_item(
                root,
                "future-blocking-review-second-assignment.md",
                action="Review the second assignment.",
            )
            self.git(root, "add", ".")
            path = item.relative_to(root).as_posix()
            second_path = second.relative_to(root).as_posix()
            env = {
                "BODY": (
                    "## What to review\n\n"
                    f"1. [Review the first assignment.]({path})\n"
                ),
                "REVIEWERS": (
                    '[{"login": "alice"}, {"login": "bob"}]'
                ),
                "TEAMS": '[{"slug": "release-team"}]',
                "ASSIGNEES": "[]",
                "TITLE": "Compatibility notes for this release",
            }
            with mock.patch.dict(os.environ, env), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    1,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--external-action-env", "REVIEWERS",
                        "--external-action-env", "TEAMS",
                        "--external-action-env", "ASSIGNEES",
                        "--additional-prose-env", "TITLE",
                        "--unscoped",
                    ]),
                )
                os.environ["BODY"] += (
                    f"2. [Review the second assignment.]({second_path})\n"
                )
                self.assertEqual(
                    1,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--external-action-env", "REVIEWERS",
                        "--external-action-env", "TEAMS",
                        "--external-action-env", "ASSIGNEES",
                        "--additional-prose-env", "TITLE",
                        "--unscoped",
                    ]),
                )
                os.environ["TEAMS"] = "[]"
                self.assertEqual(
                    0,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--external-action-env", "REVIEWERS",
                        "--external-action-env", "TEAMS",
                        "--external-action-env", "ASSIGNEES",
                        "--additional-prose-env", "TITLE",
                        "--unscoped",
                    ]),
                )

    def test_cli_infers_task_scope_on_a_non_task_branch(self):
        task_id = "2026-07-23-conventional-branch"
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            self.task_record(root, task_id, f"`{path}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task state")
            base = self.git(root, "rev-parse", "HEAD")
            (root / "feature.md").write_text("# Feature\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(
                root,
                "commit",
                "-m", f"implement feature for task: {task_id}",
            )
            candidate = self.git(root, "rev-parse", "HEAD")
            env = {
                "BODY": (
                    "## What to review\n\n"
                    "No queued action requested.\n"
                ),
            }
            args = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--queue-actor", "any",
                "--required-queue-actor", "needs-human",
                "--branch", "feature/conventional",
                "--base-revision", base,
                "--candidate-revision", candidate,
            ]
            with mock.patch.dict(os.environ, env), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, PROJECTION.main(args))
                os.environ["BODY"] = (
                    "## What to review\n\n"
                    f"1. [Review the boundary.]({path})\n"
                )
                self.assertEqual(0, PROJECTION.main(args))

    def test_cli_task_branch_rejects_conflicting_candidate_scope(self):
        task_a = "2026-07-23-actual-task"
        task_b = "2026-07-23-misnamed-branch"
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            self.task_record(root, task_a, f"`{path}`")
            self.task_record(root, task_b, "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task state")
            base = self.git(root, "rev-parse", "HEAD")
            (root / "feature.md").write_text("# Feature\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(
                root,
                "commit",
                "-m", f"implement feature for task: {task_a}",
            )
            candidate = self.git(root, "rev-parse", "HEAD")
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        "No queued action requested.\n"
                    ),
                },
            ), contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    2,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--queue-actor", "any",
                        "--required-queue-actor", "needs-human",
                        "--branch", f"task/{task_b}",
                        "--base-revision", base,
                        "--candidate-revision", candidate,
                    ]),
                )

    def test_cli_task_branch_requires_immutable_scope_evidence(self):
        task_id = "2026-07-23-empty-task-branch"
        with self.repo() as root:
            self.task_record(root, task_id, "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task state")
            base = self.git(root, "rev-parse", "HEAD")
            (root / "feature.md").write_text("# Feature\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "unscoped feature change")
            candidate = self.git(root, "rev-parse", "HEAD")
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        "No queued action requested.\n"
                    ),
                },
            ), contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    2,
                    PROJECTION.main([
                        "--from-env", "BODY",
                        "--action-section", "What to review",
                        "--queue-actor", "any",
                        "--required-queue-actor", "needs-human",
                        "--branch", f"task/{task_id}",
                        "--base-revision", base,
                        "--candidate-revision", candidate,
                    ]),
                )

    def test_cli_non_task_branch_without_base_fails_closed(self):
        with self.repo() as root, mock.patch.dict(
            os.environ,
            {"BODY": "## What to review\n\nNo queued action requested.\n"},
        ), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                2,
                PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                    "--branch", "feature/conventional",
                ]),
            )

    def test_changed_task_record_infers_scope_without_commit_tag(self):
        task_id = "2026-07-23-changed-record-scope"
        with self.repo() as root:
            item = self.queue_item(root)
            path = item.relative_to(root).as_posix()
            task = self.task_record(root, task_id, "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task")
            base = self.git(root, "rev-parse", "HEAD")
            task.write_text(
                f"# Task\n\n**Queue actions:** `{path}`\n",
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "change task projection")
            candidate = self.git(root, "rev-parse", "HEAD")
            self.assertEqual(
                task_id,
                PROJECTION.inferred_changed_task_id(
                    base, candidate, repo=root
                ),
            )

    def test_cli_requires_explicit_unscoped_inbound_surface(self):
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
                    "--unscoped",
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
                    "--unscoped",
                ]),
            )

    def test_core_projection_source_is_provider_neutral(self):
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn("github", source)
        self.assertNotIn("codex", source)


if __name__ == "__main__":
    unittest.main()
