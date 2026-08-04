import atexit
import contextlib
import importlib.util
import io
import json
import os
import shutil
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

GIT_FIXTURE_IDENTITY = (
    ("user.name", "Test"),
    ("user.email", "test@example.invalid"),
)
_GIT_FIXTURE_SKELETON = None


def build_git_fixture_skeleton(root):
    """Create the canonical fixture repository with real Git, once."""
    template = root / "empty-template"
    template.mkdir()
    origin = root / "origin"
    origin.mkdir()
    # An empty --template leaves out the sample hooks, description, and exclude
    # file: nothing here reads them, and they are most of what `git init` writes.
    commands = [["git", "init", f"--template={template}"]]
    commands.extend(
        ["git", "config", key, value] for key, value in GIT_FIXTURE_IDENTITY
    )
    for command in commands:
        subprocess.run(
            command,
            cwd=origin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    return origin / ".git"


def git_fixture_skeleton():
    """Return the shared, relocatable `.git` every repository test copies.

    Each test needs the same empty repository, and `git init` plus two
    `git config` runs cost three process spawns per test. The skeleton is built
    once and copied instead.
    """
    global _GIT_FIXTURE_SKELETON
    if _GIT_FIXTURE_SKELETON is None:
        holder = tempfile.mkdtemp(prefix="agentfold-git-fixture-")
        atexit.register(shutil.rmtree, holder, True)
        _GIT_FIXTURE_SKELETON = build_git_fixture_skeleton(Path(holder))
    return _GIT_FIXTURE_SKELETON


class ActionProjectionTests(unittest.TestCase):
    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(
                str(git_fixture_skeleton()), str(root / ".git")
            )
            (root / "message-queue").mkdir()
            with mock.patch.object(PROJECTION, "REPO", root):
                yield root

    def test_copied_fixture_skeleton_matches_a_real_git_init(self):
        """Guard the shortcut: a real `git init` must still produce this repository."""
        with tempfile.TemporaryDirectory() as tmp:
            real = build_git_fixture_skeleton(Path(tmp))
            copied = git_fixture_skeleton()
            self.assertEqual(
                sorted(item.relative_to(real).as_posix()
                       for item in real.rglob("*")),
                sorted(item.relative_to(copied).as_posix()
                       for item in copied.rglob("*")),
            )
            for item in sorted(real.rglob("*")):
                if item.is_file():
                    relative = item.relative_to(real)
                    self.assertEqual(
                        item.read_bytes(),
                        (copied / relative).read_bytes(),
                        f"`{relative}` drifted from what `git init` writes",
                    )
        with self.repo() as root:
            (root / "README.md").write_text("# Real\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "the copied skeleton commits")
            # The recorded author can come from the environment, so assert on
            # what the copy actually carries: the fixture identity config.
            self.assertEqual("Test", self.git(root, "config", "user.name"))
            self.assertEqual(
                "the copied skeleton commits",
                self.git(root, "log", "-1", "--format=%s"),
            )

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

    @classmethod
    def receipt_task(cls, root, claimant="author", duplicate=False):
        task = (
            root / "tasks" / "3_in-review" /
            "2026-07-23-example" / "task.md"
        )
        task.parent.mkdir(parents=True, exist_ok=True)
        fields = f"**Claimed-by:** {claimant}\n"
        if duplicate:
            fields += "**Claimed-by:** second author\n"
        task.write_text("# Example\n\n" + fields, encoding="utf-8")
        cls.git(root, "add", task.relative_to(root).as_posix())
        return task

    @staticmethod
    def queue_item(
        root,
        name="future-blocking-review-boundary.md",
        action="Review the boundary.",
        actor="needs-human",
        leaf=None,
        external_assignment=None,
        external_source=None,
    ):
        leaf = leaf or ("reviews" if actor == "needs-human" else "requests")
        path = root / "message-queue" / actor / leaf / name
        path.parent.mkdir(parents=True, exist_ok=True)
        assignment_field = (
            f"**External assignment:** {external_assignment}\n"
            if external_assignment is not None else ""
        )
        source_field = (
            f"**External source:** {external_source}\n"
            if external_source is not None else ""
        )
        path.write_text(
            f"# Review\n\n**Action:** {action}\n"
            f"{assignment_field}{source_field}",
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
        task_scope=None,
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
            task_scope=task_scope,
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
                    task_scope=f"task/{task_id}",
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
            findings = self.findings(root, body, task_scope=task_id)
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
                    task_scope=task_id,
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
            "We need your view on whether to ship A or B.",
            "We need your opinion on the fallback.",
            "We need your perspective on this tradeoff.",
            "We need your thoughts on the migration.",
            "We need your take on the release boundary.",
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
            "The security guild needs to sanity-check this before merge.",
            "The release circle must validate this before release.",
            "The security guild has to sanity-check this before merge.",
            "The security guild is required to sanity-check this before merge.",
            "The security guild is currently required to review this before merge.",
            "The security guild has to review this before the merge.",
            "The release circle must validate this before releasing.",
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
            "The old report says the security guild needs to sanity-check this.",
            "The security guild needed to sanity-check this yesterday.",
            "The security guild needs to be able to sanity-check this before merge.",
            "The parser should validate input offline.",
            "The security guild no longer needs to sanity-check this before merge.",
            "The memo noted security guild must review this before merge.",
            (
                "The memo noted that\n"
                "the security guild has to review this before merge."
            ),
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
            for action in (actions[0], *actions[-7:]):
                with self.subTest(end_to_end_action=action):
                    findings = self.findings(
                        root,
                        action,
                        allow_missing_action_section_if_no_action=True,
                        queue_actor="any",
                        require_all_live=False,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )
            for description in descriptions[-7:]:
                with self.subTest(end_to_end_description=description):
                    self.assertEqual(
                        [],
                        self.findings(
                            root,
                            "## Goal\n\n"
                            f"{description}\n\n"
                            "## What to review\n\n"
                            "No queued action requested.\n",
                            queue_actor="any",
                            require_all_live=False,
                        ),
                    )

    def test_self_answered_explanatory_question_is_not_a_hidden_action(self):
        explanations = (
            "Why this approach? It keeps queue ownership provider-neutral.",
            "Why this approach?\nIt keeps queue ownership provider-neutral.",
            (
                "Why this approach? We use repository-local state "
                "to avoid lock-in."
            ),
            "How is it implemented? By storing state in Git.",
            (
                "Why use queue files? They make the action survive "
                "session loss."
            ),
            "Why a queue file? So the request survives session loss.",
            (
                "What happens if nobody replies? "
                "The safe default continues."
            ),
            (
                "How does this stay portable? "
                "The repository stores all state locally."
            ),
        )
        for explanation in explanations:
            with self.subTest(explanation=explanation):
                self.assertFalse(
                    PROJECTION.action_like_plain_prose(explanation)
                )
                self.assertFalse(
                    PROJECTION.action_like_summary_prose(explanation)
                )

                with self.repo() as root:
                    body = (
                        "## Goal\n\n"
                        f"{explanation}\n\n"
                        "## What to review\n\nNo human action requested.\n"
                    )
                    self.assertEqual([], self.findings(root, body))

        with self.repo() as root:
            for ask in (
                "Why this approach?\n",
                "Does the boundary work? It should be checked before merge.\n",
                "Why did you choose this approach? It keeps ownership neutral.\n",
                (
                    "What is your recommendation? "
                    "It is useful for planning.\n"
                ),
                "Why should we merge? It appears ready.\n",
                "Why this approach? Please review the fallback.\n",
                (
                    "Why this approach? It keeps ownership neutral. "
                    "Should we merge?\n"
                ),
                (
                    "Why this approach? Maintainer approval is still "
                    "required.\n"
                ),
            ):
                with self.subTest(ask=ask):
                    findings = self.findings(
                        root,
                        "## Goal\n\n"
                        f"{ask}\n"
                        "## What to review\n\nNo human action requested.\n",
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "outside the declared action section",
                        findings[0],
                    )

    def test_passive_hard_obligations_are_actions_not_descriptions(self):
        actions = (
            "This needs to be repaired before merge.",
            "This must be reviewed before release.",
            "The migration has to be fixed before deployment.",
            "This is currently required to be validated before publication.",
            "This must be approved before merge.",
            "This needs fixing before merge.",
            "This should be fixed before merge.",
            "This requires approval before merge.",
            "This needs a fix before merge.",
            "This ought to be reviewed before release.",
            "The security guild must review this.",
            "The security guild needs to review this.",
            "Fixing the login race is required before merge.",
            "A security review remains necessary before merge.",
            "A security sign-off is mandatory before merge.",
            "This must be reviewed.",
            "The migration needs fixing.",
            "The release plan requires approval.",
            "A security review is mandatory.",
            "The patch is required to be validated.",
            "Coverage must be added.",
            "Adding a regression test is necessary.",
            "Add a regression test.",
            "Do not merge until the race is fixed.",
        )
        descriptions = (
            "This no longer needs to be repaired before merge.",
            "The memo noted this needs to be repaired before merge.",
            "This needed to be repaired before the old release.",
            "This needs to be able to be repaired before merge.",
            "This should be repairable before merge.",
            "This should be highly repairable before merge.",
            "This needs no repair before merge.",
            "A security review is not required before merge.",
            "The memo says fixing the login race is required before merge.",
            "The algorithm requires adding each element to the set.",
            (
                "This function requires checking the cache before "
                "computing a value."
            ),
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
            for action in actions:
                with self.subTest(end_to_end_action=action):
                    findings = self.findings(
                        root,
                        action,
                        allow_missing_action_section_if_no_action=True,
                        queue_actor="any",
                        require_all_live=False,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(
                        "missing a declared action section",
                        findings[0],
                    )

    def test_kindly_action_directives_are_actions_not_descriptions(self):
        actions = (
            "Kindly review the migration before merge.",
            "Kindly approve the recovery plan.",
            "Also kindly verify the credential rotation.",
        )
        descriptions = (
            "Kindly worded review comments reduce friction.",
            "The response was kindly written.",
        )
        for action in actions:
            with self.subTest(action=action):
                self.assertTrue(PROJECTION.action_like_plain_prose(action))
                self.assertTrue(PROJECTION.action_like_prose(action))
                self.assertTrue(PROJECTION.action_like_summary_prose(action))
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

    def test_modal_requests_to_named_people_and_groups_are_actions(self):
        actions = (
            "Could the security team sanity-check this.",
            "Could the platform engineers review this.",
            "Would the security guild inspect the fallback.",
            "Can the release managers verify the recovery path.",
            "Would the release committee inspect the fallback.",
            "Can someone review the migration.",
            "Could @quentin verify the recovery path.",
            "Would Alice Smith confirm the boundary.",
            "Might our specialist working group evaluate the threat model.",
        )
        descriptions = (
            "The security team sanity-checked this yesterday.",
            "The release committee can inspect the fallback automatically.",
            "Alice Smith confirmed the boundary yesterday.",
            "Could SQLite support this.",
            "Could this work better.",
            "Would the release managers have enough capacity.",
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
            "It would be great if you fixed the login race.",
            "It would be useful if a reviewer checked the migration.",
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
                task_scope=task_id,
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
                    task_scope=task_id,
                )

    def test_task_action_units_allow_ordinary_agent_plan_work(self):
        with self.repo() as root:
            plan = (
                "# Plan\n\n"
                "- [ ] Run the focused tests.\n"
                "- [ ] Review the changed files.\n"
                "- [x] Implement the queue parser.\n\n"
                "The test output records the completed review.\n"
                "The agent will verify the release.\n"
                "The agent will review the release.\n"
            )
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    plan,
                    "tasks/1_in-progress/2026-07-23-example/plan.md",
                    repo=root,
                ),
            )

    def test_task_action_units_detect_human_and_authority_asks(self):
        asks = (
            "Should we ship this release?",
            "Please review the release boundary.",
            "A maintainer should review this before merge.",
            "Feedback welcome.",
            "Approve the production release.",
            "Ask the owner to approve the production release.",
            "Assigned to Alice: review the release.",
            "Owner, review the release.",
            "Owner must not merge this release.",
            "Could platform engineers review the release?",
            "Pending owner review.",
            "The release manager must approve the change.",
            "Do not merge until security approves.",
            "| Owner | Approve the release |",
            "> [!IMPORTANT]\n> Owner, please approve the release.",
            "- [ ] Please confirm the production rollout.",
        )
        with self.repo() as root:
            for ask in asks:
                with self.subTest(ask=ask):
                    counts = PROJECTION.task_action_unit_counts(
                        ask,
                        "tasks/1_in-progress/2026-07-23-example/plan.md",
                        repo=root,
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_treat_core_fit_verdicts_as_receipts(self):
        text = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
            "- core-fit / first reviewer: approve — could not break it\n"
            "- core-fit / second reviewer: block - found a boundary leak\n"
        )
        with self.repo() as root:
            self.receipt_task(root)
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    text,
                    "tasks/3_in-review/2026-07-23-example/verification.md",
                    repo=root,
                ),
            )

    def test_task_action_units_scan_core_fit_reviewer_and_finding_text(self):
        receipts = (
            "- core-fit / Owner, please approve: block — could not break it\n",
            "- core-fit / reviewer: approve — Owner, please approve the release\n",
            "- core-fit / reviewer: block — Is the boundary acceptable?\n",
            "- core-fit / reviewer: approve — TODO ask the owner\n",
        )
        with self.repo() as root:
            self.receipt_task(root)
            for receipt in receipts:
                with self.subTest(receipt=receipt):
                    counts = PROJECTION.task_action_unit_counts(
                        "## Review verdicts\n\n"
                        f"**Reviewed revision:** {'a' * 40}\n\n"
                        + receipt,
                        "tasks/3_in-review/2026-07-23-example/verification.md",
                        repo=root,
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_do_not_normalize_receipt_near_misses(self):
        near_misses = (
            "* core-fit / reviewer: approve — could not break it\n",
            "- core-fit/reviewer: approve — could not break it\n",
            "- core-fit / reviewer: approve: could not break it\n",
            "- Core-fit / reviewer: approve — could not break it\n",
            "- core-fit / reviewer: APPROVE — could not break it\n",
            "- core-fit / reviewer: approve - could not break it\n",
            "- core-fit / reviewer:  approve — could not break it\n",
        )
        with self.repo() as root:
            self.receipt_task(root)
            for near_miss in near_misses:
                with self.subTest(near_miss=near_miss):
                    counts = PROJECTION.task_action_unit_counts(
                        "## Review verdicts\n\n"
                        f"**Reviewed revision:** {'a' * 40}\n\n"
                        + near_miss,
                        "tasks/3_in-review/2026-07-23-example/verification.md",
                        repo=root,
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

            counts = PROJECTION.task_action_unit_counts(
                "- core-fit / reviewer: approve — could not break it\n",
                "tasks/3_in-review/2026-07-23-example/design.md",
                repo=root,
            )
            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_require_the_exact_receipt_path_and_region(self):
        receipt = "- core-fit / reviewer: approve — could not break it\n"
        revision = f"**Reviewed revision:** {'a' * 40}\n\n"
        valid = "## Review verdicts\n\n" + revision + receipt
        cases = (
            (
                "tasks/3_in-review/2026-07-23-example/notes/verification.md",
                valid,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/Verification.md",
                valid,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                valid + "\n## Other\n\n" + receipt,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                "## Review verdicts\n\n" + receipt + revision,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                valid + "\n## Review verdicts\n\n" + revision + receipt,
                2,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                revision + receipt,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                "## Review verdicts\n\n" + revision + revision + receipt,
                1,
            ),
            (
                "tasks/3_in-review/2026-07-23-example/verification.md",
                "## Review verdicts\n\n" + receipt,
                1,
            ),
        )
        with self.repo() as root:
            self.receipt_task(root)
            for source_path, text, expected in cases:
                with self.subTest(source_path=source_path, text=text):
                    counts = PROJECTION.task_action_unit_counts(
                        text, source_path, repo=root
                    )
                    self.assertEqual(expected, sum(counts.values()), counts)

    def test_task_action_units_end_receipts_at_first_nonreceipt_content(self):
        receipt = "- core-fit / owner: approve — production release\n"
        prefix = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
        )
        boundaries = (
            "# Human action\n\n",
            "## Human action\n\n",
            "### Detailed findings\n\n",
            "Human action\n===\n\n",
            "Human action\n---\n\n",
            "> quoted paragraph\n"
            "lazy continuation\n"
            "---\n\n",
            "[review]: /target\n"
            "---\n\n",
            "ordinary explanation\n\n",
        )
        source_path = (
            "tasks/3_in-review/2026-07-23-example/verification.md"
        )
        with self.repo() as root:
            self.receipt_task(root)
            for boundary in boundaries:
                with self.subTest(boundary=boundary):
                    counts = PROJECTION.task_action_unit_counts(
                        prefix + boundary + receipt,
                        source_path,
                        repo=root,
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

            revision_heading = (
                "## Review verdicts\n\n"
                f"**Reviewed revision:** {'a' * 40}\n"
                "---\n\n"
                + receipt
            )
            counts = PROJECTION.task_action_unit_counts(
                revision_heading, source_path, repo=root
            )
            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_reject_container_and_decorated_headings(self):
        revision = f"**Reviewed revision:** {'a' * 40}"
        receipt = "- core-fit / reviewer: approve — could not break it"
        cases = (
            f"> ## Review verdicts\n>\n> {revision}\n>\n> {receipt}\n",
            f"- ## Review verdicts\n\n  {revision}\n\n  {receipt}\n",
            f"## Review verdicts (formal)\n\n{revision}\n\n{receipt}\n",
            f"## REVIEW VERDICTS\n\n{revision}\n\n{receipt}\n",
        )
        with self.repo() as root:
            self.receipt_task(root)
            for text in cases:
                with self.subTest(text=text):
                    counts = PROJECTION.task_action_unit_counts(
                        text,
                        "tasks/3_in-review/2026-07-23-example/verification.md",
                        repo=root,
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_allow_blank_separated_contiguous_verdicts(self):
        text = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
            "- core-fit / first: approve — could not break it\n\n"
            "- core-fit / second: block — found a boundary leak\n"
        )
        with self.repo() as root:
            self.receipt_task(root)
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    text,
                    "tasks/3_in-review/2026-07-23-example/verification.md",
                    repo=root,
                ),
            )

    def test_task_action_units_require_an_independent_real_reviewer(self):
        prefix = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
        )
        cases = (
            ("author", "- core-fit / author: approve — self review\n"),
            ("author", "- core-fit / ---: approve — punctuation identity\n"),
            ("unclaimed", "- core-fit / reviewer: approve — no claimant\n"),
        )
        source_path = "tasks/3_in-review/2026-07-23-example/verification.md"
        with self.repo() as root:
            for claimant, receipt in cases:
                with self.subTest(claimant=claimant, receipt=receipt):
                    self.receipt_task(root, claimant=claimant)
                    counts = PROJECTION.task_action_unit_counts(
                        prefix + receipt, source_path, repo=root
                    )
                    self.assertEqual(1, sum(counts.values()), counts)

            self.receipt_task(root, duplicate=True)
            counts = PROJECTION.task_action_unit_counts(
                prefix + "- core-fit / reviewer: approve — ambiguous claimant\n",
                source_path,
                repo=root,
            )
            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_compare_rendered_human_identities(self):
        prefix = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
        )
        source_path = "tasks/3_in-review/2026-07-23-example/verification.md"
        cases = (
            ("author", "au\u200bthor"),
            ("author", "<span>author</span>"),
            ("<span>author</span>", "au\u200bthor"),
            ("author", "<reviewer>"),
        )
        with self.repo() as root:
            for claimant, reviewer in cases:
                with self.subTest(claimant=claimant, reviewer=reviewer):
                    with mock.patch.object(
                        PROJECTION,
                        "candidate_text",
                        return_value=f"# Example\n\n**Claimed-by:** {claimant}\n",
                    ):
                        counts = PROJECTION.task_action_unit_counts(
                            prefix
                            + f"- core-fit / {reviewer}: approve — identity probe\n",
                            source_path,
                            repo=root,
                        )
                    self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_reject_reviewer_and_claimant_placeholders(self):
        prefix = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
        )
        source_path = "tasks/3_in-review/2026-07-23-example/verification.md"
        placeholders = (
            "unclaimed", "none yet", "TBD", "TODO", "none", "N/A", "NA",
            "unknown", "______", "<reviewer>",
        )
        with self.repo() as root:
            for placeholder in placeholders:
                with self.subTest(claimant=placeholder):
                    with mock.patch.object(
                        PROJECTION,
                        "candidate_text",
                        return_value=(
                            f"# Example\n\n**Claimed-by:** {placeholder}\n"
                        ),
                    ):
                        counts = PROJECTION.task_action_unit_counts(
                            prefix
                            + "- core-fit / independent: approve — claimant probe\n",
                            source_path,
                            repo=root,
                        )
                    self.assertEqual(1, sum(counts.values()), counts)
            placeholder_receipts = "".join(
                f"- core-fit / {placeholder}: approve — reviewer probe\n"
                for placeholder in placeholders
            )
            with mock.patch.object(
                PROJECTION,
                "candidate_text",
                return_value="# Example\n\n**Claimed-by:** author\n",
            ):
                counts = PROJECTION.task_action_unit_counts(
                    prefix + placeholder_receipts,
                    source_path,
                    repo=root,
                )
            self.assertEqual(len(placeholders), sum(counts.values()), counts)

        with self.repo() as root:
            counts = PROJECTION.task_action_unit_counts(
                prefix + "- core-fit / reviewer: approve — missing task\n",
                source_path,
                repo=root,
            )
            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_read_claimant_from_candidate_revision(self):
        text = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n\n"
            "- core-fit / reviewer: approve — independent in candidate\n"
        )
        source_path = "tasks/3_in-review/2026-07-23-example/verification.md"
        with self.repo() as root:
            task = self.receipt_task(root, claimant="author")
            self.git(root, "commit", "-m", "record candidate claimant")
            candidate = self.git(root, "rev-parse", "HEAD")
            task.write_text(
                "# Example\n\n**Claimed-by:** reviewer\n",
                encoding="utf-8",
            )
            self.git(root, "add", task.relative_to(root).as_posix())
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    text,
                    source_path,
                    repo=root,
                    candidate_revision=candidate,
                ),
            )
            counts = PROJECTION.task_action_unit_counts(
                text, source_path, repo=root
            )
            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_end_receipts_at_raw_hidden_or_code_content(self):
        prefix = (
            "## Review verdicts\n\n"
            f"**Reviewed revision:** {'a' * 40}\n"
        )
        first = "- core-fit / first: block — earlier blocker\n"
        later = "- core-fit / later: approve — must stay actionable\n"
        barriers = (
            "\n<!-- hidden comment -->\n",
            "\n<div>\nhidden HTML\n</div>\n",
            "\n```text\nhidden fence\n```\n",
            "\n    hidden indented code\n",
            "\n\u00a0\n",
            "\n\f\n",
            "\n\v\n",
            "\n\u0085\n",
            "\n\u2028\n",
            "\n\u2060\n",
            "\n\u200b\n",
        )
        source_path = "tasks/3_in-review/2026-07-23-example/verification.md"
        with self.repo() as root:
            with mock.patch.object(
                PROJECTION,
                "candidate_text",
                return_value="# Example\n\n**Claimed-by:** author\n",
            ):
                for barrier in barriers:
                    for body in (
                        prefix + barrier + later,
                        prefix + first + barrier + later,
                    ):
                        with self.subTest(barrier=barrier, body=body):
                            counts = PROJECTION.task_action_unit_counts(
                                body, source_path, repo=root
                            )
                            self.assertEqual(1, sum(counts.values()), counts)

    def test_task_action_units_accept_a_crlf_receipt(self):
        text = (
            "## Review verdicts\r\n\r\n"
            f"**Reviewed revision:** {'a' * 40}\r\n\r\n"
            "- core-fit / reviewer: approve — CRLF remained structural\r\n"
        )
        with self.repo() as root:
            self.receipt_task(root)
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    text,
                    "tasks/3_in-review/2026-07-23-example/verification.md",
                    repo=root,
                ),
            )

    def test_task_action_units_allow_syntactic_quotes_code_and_explanation(self):
        text = (
            "```\nPlease review the fenced example.\n```\n\n"
            "`Please confirm the inline example.`\n\n"
            "Why use Git? Because the commit is durable evidence.\n"
            "\n## Why Git?\n\nGit provides durable evidence.\n\n"
            "Is the parser deterministic? Yes, its grammar is closed.\n"
        )
        with self.repo() as root:
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    text,
                    "tasks/1_in-progress/2026-07-23-example/design.md",
                    repo=root,
                ),
            )

    def test_task_action_units_scan_visible_html_but_ignore_hidden_html(self):
        with self.repo() as root:
            visible = PROJECTION.task_action_unit_counts(
                "<p>Please approve the production release.</p>",
                "tasks/1_in-progress/2026-07-23-example/design.md",
                repo=root,
            )
            self.assertEqual(1, sum(visible.values()), visible)
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    "<p hidden>Please approve the production release.</p>",
                    "tasks/1_in-progress/2026-07-23-example/design.md",
                    repo=root,
                ),
            )

    def test_task_action_units_accept_only_exact_task_owned_projection(self):
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Review the rollout boundary.",
            )
            queue_path = item.relative_to(root).as_posix()
            self.git(root, "add", ".")
            source_path = (
                "tasks/1_in-progress/2026-07-23-example/design.md"
            )
            link = (
                "[Review the rollout boundary.]"
                f"(../../../{queue_path})"
            )
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    link,
                    source_path,
                    allowed_queue_paths=(queue_path,),
                    repo=root,
                ),
            )

            for body, allowed in (
                (link, ()),
                (
                    f"[Review the rollout boundary.]({queue_path})",
                    (queue_path,),
                ),
                (
                    f"[Read the design.](../../../{queue_path})",
                    (queue_path,),
                ),
                (
                    f"[Review](../../../{queue_path})",
                    (queue_path,),
                ),
                (
                    link + " Please also approve the production rollout.",
                    (queue_path,),
                ),
            ):
                with self.subTest(body=body, allowed=allowed):
                    counts = PROJECTION.task_action_unit_counts(
                        body,
                        source_path,
                        allowed_queue_paths=allowed,
                        repo=root,
                    )
                    self.assertTrue(counts)

            contextual = self.queue_item(
                root,
                name="non-blocking-review-contextual.md",
                action="Review whether this change may merge.",
            )
            contextual_path = contextual.relative_to(root).as_posix()
            self.git(root, "add", ".")
            self.assertEqual(
                {},
                PROJECTION.task_action_unit_counts(
                    "[Review whether this change may merge.]"
                    f"(../../../{contextual_path})",
                    source_path,
                    allowed_queue_paths=(contextual_path,),
                    repo=root,
                ),
            )

    def test_task_action_unit_counts_preserve_duplicate_multiplicity(self):
        with self.repo() as root:
            counts = PROJECTION.task_action_unit_counts(
                "Please approve the release.\n\n"
                "Please approve the release.\n",
                "tasks/1_in-progress/2026-07-23-example/task.md",
                repo=root,
            )
            self.assertEqual(1, len(counts))
            self.assertEqual(2, sum(counts.values()))

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
                    task_scope=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                ),
            )
            findings = self.findings(
                root,
                body,
                task_scope=task_id,
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
                        task_scope=task_id,
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
                    task_scope=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                    external_assignments=assignment,
                ),
            )

    def test_unscoped_assignment_cannot_reuse_another_artifact_binding(self):
        artifact_a = "github:issue:node:ISSUE_A:assignee:user:alice"
        artifact_b = "github:issue:node:ISSUE_B:assignee:user:alice"
        with self.repo() as root:
            item = self.queue_item(
                root,
                action="Handle Alice's issue assignment.",
                external_assignment=artifact_a,
            )
            path = item.relative_to(root).as_posix()
            self.git(root, "add", ".")
            body = (
                "## What to review\n\n"
                f"- [Handle Alice's issue assignment.]({path})\n"
            )
            def assignments(identity):
                return (json.dumps([{
                    "actor": "needs-human",
                    "identity": identity,
                }]),)

            self.assertEqual(
                [],
                self.findings(
                    root,
                    body,
                    external_assignments=assignments(artifact_a),
                    queue_actor="any",
                    require_all_live=False,
                ),
            )
            findings = self.findings(
                root,
                body,
                external_assignments=assignments(artifact_b),
                queue_actor="any",
                require_all_live=False,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("External assignment", findings[0])
            self.assertIn(artifact_b, findings[0])

    def test_external_action_source_requires_opaque_binding(self):
        identity = "provider:review-thread:opaque-42"
        with self.repo() as root:
            linked = self.queue_item(
                root,
                name="future-blocking-request-fix-login-race.md",
                action="Fix the login race.",
                actor="needs-agent",
            )
            bound = self.queue_item(
                root,
                name="future-blocking-request-address-review-thread.md",
                action="Address the external review thread.",
                actor="needs-agent",
                external_source=identity,
            )
            linked_path = linked.relative_to(root).as_posix()
            self.git(root, "add", ".")
            sources = json.dumps([{
                "actor": "needs-agent",
                "identity": identity,
                "body": "It would be great if you fixed the login race.",
                "url": "https://provider.invalid/review/42",
            }])
            self.assertEqual(
                [],
                PROJECTION.external_action_source_findings(
                    sources,
                    ("What to review",),
                    repo=root,
                ),
            )
            self.queue_item(
                root,
                name="future-blocking-request-address-second-review-ask.md",
                action="Address the second ask in the external review thread.",
                actor="needs-agent",
                external_source=identity,
            )
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                PROJECTION.external_action_source_findings(
                    sources,
                    ("What to review",),
                    repo=root,
                ),
            )
            bound.unlink()
            (
                root / "message-queue/needs-agent/requests/"
                "future-blocking-request-address-second-review-ask.md"
            ).unlink()
            self.git(root, "add", "-u")
            findings = PROJECTION.external_action_source_findings(
                sources,
                ("What to review",),
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("is not durably bound", findings[0])
            sources = json.dumps([{
                "actor": "needs-agent",
                "identity": "provider:review:linked",
                "body": (
                    "## What to review\n\n"
                    f"- [Fix the login race.]({linked_path})\n"
                ),
            }])
            findings = PROJECTION.external_action_source_findings(
                sources,
                ("What to review",),
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("is directly projected", findings[0])
            self.assertIn(
                "**External source:** provider:review:linked",
                findings[0],
            )
            self.queue_item(
                root,
                name="future-blocking-request-bind-linked-review.md",
                action="Track the directly projected external review.",
                actor="needs-agent",
                external_source="provider:review:linked",
            )
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                PROJECTION.external_action_source_findings(
                    sources,
                    ("What to review",),
                    repo=root,
                ),
            )

    def test_forced_directionless_source_cannot_use_language_or_no_action_bypass(
            self):
        identity = "provider:issue:opaque-42"
        bodies = (
            "I'd like you to review the migration plan.",
            "I'd like the next agent to run the migration test.",
            "## What to review\n\nNo queued action requested.\n",
            "",
        )
        with self.repo() as root:
            self.git(root, "add", ".")
            for body in bodies:
                with self.subTest(body=body):
                    sources = json.dumps([{
                        "actor": "any",
                        "identity": identity,
                        "body": body,
                        "force": True,
                    }])
                    findings = PROJECTION.external_action_source_findings(
                        sources,
                        ("What to review",),
                        repo=root,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(identity, findings[0])
                    self.assertIn(
                        "needs-human or needs-agent queue items",
                        findings[0],
                    )

    def test_forced_directionless_source_binding_path_supplies_actor(self):
        identity = "provider:issue:opaque-43"
        for actor in ("needs-human", "needs-agent"):
            with self.subTest(actor=actor), self.repo() as root:
                self.queue_item(
                    root,
                    name="non-blocking-handle-provider-issue.md",
                    action="Handle the provider issue.",
                    actor=actor,
                    external_source=identity,
                )
                self.git(root, "add", ".")
                sources = json.dumps([{
                    "actor": "any",
                    "identity": identity,
                    "body": "Unclassified provider prose.",
                    "force": True,
                }])
                self.assertEqual(
                    [],
                    PROJECTION.external_action_source_findings(
                        sources,
                        ("What to review",),
                        repo=root,
                    ),
                )

    def test_forced_directionless_source_requires_bound_direct_link_actor(
            self):
        for actor in ("needs-human", "needs-agent"):
            with self.subTest(actor=actor), self.repo() as root:
                identity = f"provider:issue:direct-{actor}"
                item = self.queue_item(
                    root,
                    name="non-blocking-handle-provider-issue.md",
                    action="Handle the provider issue.",
                    actor=actor,
                    external_source=identity,
                )
                path = item.relative_to(root).as_posix()
                self.git(root, "add", ".")
                sources = json.dumps([{
                    "actor": "any",
                    "identity": identity,
                    "body": (
                        "## What to review\n\n"
                        f"- [Handle the provider issue.]({path})\n"
                    ),
                    "force": True,
                }])
                self.assertEqual(
                    [],
                    PROJECTION.external_action_source_findings(
                        sources,
                        ("What to review",),
                        repo=root,
                    ),
                )

    def test_external_action_source_rejects_missing_or_wrong_actor_binding(self):
        identity = "provider:review-thread:opaque-43"
        with self.repo() as root:
            self.queue_item(
                root,
                external_source=identity,
                actor="needs-human",
            )
            self.git(root, "add", ".")
            sources = json.dumps([{
                "actor": "needs-agent",
                "identity": identity,
                "body": "Please fix the login race.",
            }])
            findings = PROJECTION.external_action_source_findings(
                sources,
                ("What to review",),
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn("must bind one or more live needs-agent", findings[0])
            self.assertIn("needs-human", findings[0])

            self.queue_item(
                root,
                name="future-blocking-request-unrelated.md",
                action="Address the external review.",
                actor="needs-agent",
            )
            self.git(root, "add", ".")
            missing = json.dumps([{
                "actor": "needs-agent",
                "identity": "provider:review:missing",
                "body": "Please fix the login race.",
            }])
            findings = PROJECTION.external_action_source_findings(
                missing,
                ("What to review",),
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn(
                "**External source:** provider:review:missing",
                findings[0],
            )

    def test_external_action_source_force_and_passive_semantics(self):
        identity = "provider:review:changes-requested"
        with self.repo() as root:
            self.git(root, "add", ".")
            passive = json.dumps([{
                "actor": "needs-agent",
                "identity": "provider:review:passive",
                "body": "The migration now has deterministic coverage.",
            }])
            self.assertEqual(
                [],
                PROJECTION.external_action_source_findings(
                    passive,
                    ("What to review",),
                    repo=root,
                ),
            )
            for index, body in enumerate((
                "This needs to be repaired before merge.",
                "This must be approved before merge.",
                "This needs fixing before merge.",
                "This should be fixed before merge.",
                "The security guild must review this.",
                "Fixing the login race is required before merge.",
                "A security review remains necessary before merge.",
                "A security sign-off is mandatory before merge.",
                "This must be reviewed.",
                "The migration needs fixing.",
                "The release plan requires approval.",
                "A security review is mandatory.",
                "The patch is required to be validated.",
                "Coverage must be added.",
                "Adding a regression test is necessary.",
                "Add a regression test.",
                "Do not merge until the race is fixed.",
            ), start=1):
                identity_value = f"provider:review:commented-action-{index}"
                commented_action = json.dumps([{
                    "actor": "needs-agent",
                    "identity": identity_value,
                    "body": body,
                    "force": False,
                }])
                with self.subTest(commented_action=body):
                    findings = PROJECTION.external_action_source_findings(
                        commented_action,
                        ("What to review",),
                        repo=root,
                    )
                    self.assertEqual(1, len(findings))
                    self.assertIn(identity_value, findings[0])
            forced = json.dumps([{
                "actor": "needs-agent",
                "identity": identity,
                "body": "",
                "force": True,
            }])
            findings = PROJECTION.external_action_source_findings(
                forced,
                ("What to review",),
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn(identity, findings[0])
            self.queue_item(
                root,
                name="future-blocking-request-handle-review.md",
                action="Handle the changes-requested review.",
                actor="needs-agent",
                external_source=identity,
            )
            self.git(root, "add", ".")
            self.assertEqual(
                [],
                PROJECTION.external_action_source_findings(
                    forced,
                    ("What to review",),
                    repo=root,
                ),
            )

    def test_external_action_source_input_is_closed_and_unique(self):
        invalid_values = (
            "{}",
            json.dumps([{"actor": "unknown", "identity": "one"}]),
            json.dumps([{
                "actor": "needs-agent",
                "identity": "one",
                "body": 42,
            }]),
            json.dumps([{
                "actor": "needs-agent",
                "identity": "one",
                "unknown": True,
            }]),
            json.dumps([{
                "actor": "needs-agent",
                "identity": "one\nforged",
            }]),
            json.dumps([{
                "actor": "needs-agent",
                "identity": "one",
                "url": "https://provider.invalid/\u001b[31m",
            }]),
            json.dumps([
                {"actor": "needs-agent", "identity": "one"},
                {"actor": "needs-agent", "identity": "one"},
            ]),
        )
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                PROJECTION.external_action_source_states(value)

    def test_cli_external_action_source_reads_immutable_candidate(self):
        identity = "provider:review-thread:candidate-44"
        with self.repo() as root:
            self.queue_item(
                root,
                name="future-blocking-request-review-thread.md",
                action="Address the external review thread.",
                actor="needs-agent",
                external_source=identity,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind external review source")
            candidate = self.git(root, "rev-parse", "HEAD")
            source_file = root / "review-sources.json"
            source_file.write_text(json.dumps([{
                "actor": "needs-agent",
                "identity": identity,
                "body": "Please address this review.",
            }]), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    PROJECTION.main([
                        "--external-action-sources-file", str(source_file),
                        "--action-section", "What to review",
                        "--candidate-revision", candidate,
                    ]),
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
                    task_scope=task_id,
                    queue_actor="any",
                    required_queue_actor="needs-human",
                ),
            )
            findings = self.findings(
                root,
                "## What to review\n\nNo human action requested.\n",
                task_scope=task_id,
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

    def test_cli_task_branch_binds_every_task_the_candidate_carries(self):
        """A second task record in the candidate widens the scope, not refuses it.

        `check_queue_task_reciprocity` requires a queue item bound to `task:<id>`
        to be listed in that task's `Queue actions`, so filing one necessarily
        edits another task's record. Refusing the resulting candidate left no
        legal commit.
        """
        branch_task = "2026-07-23-branch-task"
        linked_task = "2026-07-23-reciprocally-linked-task"
        with self.repo() as root:
            branch_item = self.queue_item(
                root,
                name="future-blocking-review-branch-work.md",
                action="Review the branch work.",
            )
            linked_item = self.queue_item(
                root,
                name="future-blocking-review-linked-task.md",
                action="Review the reciprocally linked task.",
            )
            branch_path = branch_item.relative_to(root).as_posix()
            linked_path = linked_item.relative_to(root).as_posix()
            self.task_record(root, branch_task, "none")
            self.task_record(root, linked_task, "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task state")
            base = self.git(root, "rev-parse", "HEAD")
            self.task_record(root, branch_task, f"`{branch_path}`")
            self.task_record(root, linked_task, f"`{linked_path}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "link both tasks reciprocally")
            candidate = self.git(root, "rev-parse", "HEAD")
            args = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--queue-actor", "any",
                "--required-queue-actor", "needs-human",
                "--branch", f"task/{branch_task}",
                "--base-revision", base,
                "--candidate-revision", candidate,
            ]
            self.assertEqual(
                frozenset({branch_task, linked_task}),
                PROJECTION.inferred_changed_task_ids(
                    base, candidate, repo=root
                ),
            )
            output = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        "No queued action requested.\n"
                    ),
                },
            ), contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(output):
                self.assertEqual(1, PROJECTION.main(args))
            self.assertIn(branch_path, output.getvalue())
            self.assertIn(linked_path, output.getvalue())
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        f"1. [Review the branch work.]({branch_path})\n"
                        "2. [Review the reciprocally linked task.]"
                        f"({linked_path})\n"
                    ),
                },
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, PROJECTION.main(args))

    def test_cli_non_task_branch_binds_every_task_the_candidate_carries(self):
        first_task = "2026-07-23-first-carried-task"
        second_task = "2026-07-23-second-carried-task"
        with self.repo() as root:
            first_item = self.queue_item(
                root,
                name="future-blocking-review-first-task.md",
                action="Review the first task.",
            )
            second_item = self.queue_item(
                root,
                name="future-blocking-review-second-task.md",
                action="Review the second task.",
            )
            first_path = first_item.relative_to(root).as_posix()
            second_path = second_item.relative_to(root).as_posix()
            self.task_record(root, first_task, "none")
            self.task_record(root, second_task, "none")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base task state")
            base = self.git(root, "rev-parse", "HEAD")
            self.task_record(root, first_task, f"`{first_path}`")
            self.task_record(root, second_task, f"`{second_path}`")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "carry both task records")
            candidate = self.git(root, "rev-parse", "HEAD")
            args = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--queue-actor", "any",
                "--required-queue-actor", "needs-human",
                "--branch", "harness/two-tasks-at-once",
                "--base-revision", base,
                "--candidate-revision", candidate,
            ]
            output = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        "No queued action requested.\n"
                    ),
                },
            ), contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(output):
                self.assertEqual(1, PROJECTION.main(args))
            self.assertIn(first_path, output.getvalue())
            self.assertIn(second_path, output.getvalue())
            with mock.patch.dict(
                os.environ,
                {
                    "BODY": (
                        "## What to review\n\n"
                        f"1. [Review the first task.]({first_path})\n"
                        f"2. [Review the second task.]({second_path})\n"
                    ),
                },
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, PROJECTION.main(args))

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
                frozenset({task_id}),
                PROJECTION.inferred_changed_task_ids(
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

    def test_external_source_release_blocks_current_or_unknown_final_deletion(self):
        identity = "provider:item:one:sha256:" + ("a" * 64)
        with self.repo() as root:
            item = self.queue_item(root, external_source=identity)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind source")
            base = self.git(root, "rev-parse", "HEAD")
            item.unlink()
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "delete binding")
            candidate = self.git(root, "rev-parse", "HEAD")

            current = PROJECTION.external_source_release_findings(
                json.dumps({"current": [identity], "released": []}),
                base,
                candidate,
                repo=root,
            )
            unknown = PROJECTION.external_source_release_findings(
                json.dumps({"current": [], "released": []}),
                base,
                candidate,
                repo=root,
            )
            self.assertEqual(1, len(current))
            self.assertIn("current external source", current[0])
            self.assertEqual(1, len(unknown))
            self.assertIn("without an authoritative", unknown[0])

    def test_external_source_release_allows_authoritative_release(self):
        identity = "provider:item:released:sha256:" + ("b" * 64)
        with self.repo() as root:
            item = self.queue_item(root, external_source=identity)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind source")
            base = self.git(root, "rev-parse", "HEAD")
            item.unlink()
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "delete released binding")
            candidate = self.git(root, "rev-parse", "HEAD")
            self.assertEqual(
                [],
                PROJECTION.external_source_release_findings(
                    json.dumps({"current": [], "released": [identity]}),
                    base,
                    candidate,
                    repo=root,
                ),
            )
            with self.assertRaises(ValueError):
                PROJECTION.external_source_release_findings(
                    json.dumps({
                        "current": [],
                        "released": [identity, "unrelated"],
                    }),
                    base,
                    candidate,
                    repo=root,
                )

    def test_external_source_release_allows_move_and_one_remaining_binding(self):
        identity = "provider:item:move:sha256:" + ("c" * 64)
        with self.repo() as root:
            first = self.queue_item(root, external_source=identity)
            self.queue_item(
                root,
                name="non-blocking-handle-copy.md",
                actor="needs-agent",
                external_source=identity,
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind twice")
            base = self.git(root, "rev-parse", "HEAD")
            first.unlink()
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "keep one binding")
            candidate = self.git(root, "rev-parse", "HEAD")
            self.assertEqual(
                [],
                PROJECTION.external_source_release_findings(
                    json.dumps({"current": [], "released": []}),
                    base,
                    candidate,
                    repo=root,
                ),
            )

    def test_external_source_release_rebinding_requires_old_release(self):
        old = "provider:item:old:sha256:" + ("d" * 64)
        new = "provider:item:new:sha256:" + ("e" * 64)
        with self.repo() as root:
            item = self.queue_item(root, external_source=old)
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind old source")
            base = self.git(root, "rev-parse", "HEAD")
            item.write_text(
                item.read_text(encoding="utf-8").replace(old, new),
                encoding="utf-8",
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "bind new source")
            candidate = self.git(root, "rev-parse", "HEAD")
            findings = PROJECTION.external_source_release_findings(
                json.dumps({"current": [old], "released": []}),
                base,
                candidate,
                repo=root,
            )
            self.assertEqual(1, len(findings))
            self.assertIn(old, findings[0])

    def test_external_source_release_state_is_closed_and_unambiguous(self):
        invalid = (
            "[]",
            "{}",
            '{"current":[],"released":[],"maybe":[]}',
            '{"current":"source","released":[]}',
            '{"current":["same"],"released":["same"]}',
            '{"current":["same","same"],"released":[]}',
            '{"current":["bad\\nline"],"released":[]}',
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                PROJECTION.external_source_release_states(value)

    def test_external_source_release_cli_requires_exact_two_tree_context(self):
        with self.repo() as root:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
            ) as state_file:
                state_file.write('{"current":[],"released":[]}\n')
                state_path = state_file.name
            try:
                with mock.patch.object(PROJECTION, "REPO", root), \
                        contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(
                        2,
                        PROJECTION.main([
                            "--external-source-release-state-file", state_path,
                        ]),
                    )
            finally:
                Path(state_path).unlink()

    def test_core_projection_source_is_provider_neutral(self):
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn("github", source)
        self.assertNotIn("codex", source)

    # ------------------------------------------------ pull-request body shape

    SHAPED_BODY = (
        "## TL;DR\n\n"
        "1. **A branch no longer blocks itself.** Before it could not merge. "
        "Now it can.\n"
        "2. **Three stuck branches move.** Before all three were refused. Now "
        "all three pass.\n"
        "3. **Nothing answered is skipped.** Before and after, an answered "
        "review blocks.\n\n"
        "## What to review\n\nNo queued action requested.\n\n"
        "## What changed and why\n\nThe boundary reads the range it was given.\n\n"
        "## Changes\n\nOne check, one test file.\n\n"
        "## Verification\n\nThe suite passed.\n"
    )

    def shape_repo(self, root):
        """Put the real schema where the gate reads it from."""
        schema = root / PROJECTION.PULL_REQUEST_SCHEMA_PATH
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text(
            (MODULE_PATH.parents[1] / PROJECTION.PULL_REQUEST_SCHEMA_PATH)
            .read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        return schema

    def test_body_shape_says_nothing_about_a_schema_shaped_body(self):
        with self.repo() as root:
            self.shape_repo(root)
            self.assertEqual(
                [], PROJECTION.body_shape_findings(self.SHAPED_BODY, repo=root)
            )

    def test_body_shape_names_a_missing_section(self):
        with self.repo() as root:
            self.shape_repo(root)
            body = self.SHAPED_BODY.replace(
                "## Verification\n\nThe suite passed.\n", ""
            )
            findings = PROJECTION.body_shape_findings(body, repo=root)
            self.assertEqual(1, len(findings), findings)
            self.assertIn("missing section `## Verification`", findings[0])

    def test_body_shape_treats_an_absent_notes_section_as_written(self):
        """`Notes` is deleted when it would be empty, so its absence is correct."""
        with self.repo() as root:
            self.shape_repo(root)
            self.assertNotIn("## Notes", self.SHAPED_BODY)
            self.assertEqual(
                [], PROJECTION.body_shape_findings(self.SHAPED_BODY, repo=root)
            )

    def test_body_shape_names_a_section_out_of_schema_order(self):
        with self.repo() as root:
            self.shape_repo(root)
            summary, _, rest = self.SHAPED_BODY.partition("## What to review")
            action, _, tail = rest.partition("## What changed and why")
            body = (
                "## What to review" + action + summary
                + "## What changed and why" + tail
            )
            findings = PROJECTION.body_shape_findings(body, repo=root)
            self.assertEqual(1, len(findings), findings)
            self.assertIn(
                "section `## What to review` comes before `## TL;DR`",
                findings[0],
            )

    def test_body_shape_reports_a_summary_outside_the_range(self):
        low, high = PROJECTION.PULL_REQUEST_SUMMARY_RANGE
        head, _, tail = self.SHAPED_BODY.partition("## What to review")
        with self.repo() as root:
            self.shape_repo(root)
            for count in (low - 1, high + 1):
                with self.subTest(count=count):
                    items = "".join(
                        f"{index}. **Item {index}.** Before x. Now y.\n"
                        for index in range(1, count + 1)
                    )
                    body = (
                        f"## TL;DR\n\n{items}\n## What to review" + tail
                    )
                    self.assertNotIn("## TL;DR\n\n1. **A branch", body)
                    findings = PROJECTION.body_shape_findings(body, repo=root)
                    self.assertEqual(1, len(findings), findings)
                    self.assertIn(
                        f"carries {count} numbered item(s)", findings[0]
                    )
            self.assertTrue(head)

    def test_body_shape_reads_the_requirement_from_the_schema(self):
        """Changing the schema changes the rule, because there is one copy."""
        with self.repo() as root:
            schema = self.shape_repo(root)
            self.assertEqual(
                [], PROJECTION.body_shape_findings(self.SHAPED_BODY, repo=root)
            )
            schema.write_text(
                schema.read_text(encoding="utf-8") + "\n## What it cost\n\nx\n",
                encoding="utf-8",
            )
            findings = PROJECTION.body_shape_findings(
                self.SHAPED_BODY, repo=root
            )
            self.assertEqual(1, len(findings), findings)
            self.assertIn("missing section `## What it cost`", findings[0])

    def test_body_shape_is_silent_without_the_schema(self):
        """A checkout with no schema loses an opinion, never a pull request."""
        with self.repo() as root:
            self.assertEqual(
                [],
                PROJECTION.body_shape_findings("## Nothing here\n", repo=root),
            )

    def test_cli_reports_body_shape_without_changing_its_exit_status(self):
        with self.repo() as root:
            self.shape_repo(root)
            broken = self.SHAPED_BODY.replace(
                "## Verification\n\nThe suite passed.\n", ""
            )
            args = [
                "--from-env", "BODY",
                "--action-section", "What to review",
                "--queue-actor", "any",
                "--unscoped",
                "--pull-request-body-shape",
            ]
            out = io.StringIO()
            with mock.patch.dict(os.environ, {"BODY": broken}), \
                    contextlib.redirect_stdout(out):
                code = PROJECTION.main(args)
            printed = out.getvalue()
            self.assertEqual(0, code, printed)
            self.assertIn("action-projection: 0 finding(s)", printed)
            self.assertIn(
                "[explanation-shape] external projection: missing section "
                "`## Verification`",
                printed,
            )
            self.assertIn("(advisory)", printed)
            self.assertIn(
                "explanation-shape: 1 advisory finding(s) (not blocking)",
                printed,
            )

    def test_cli_leaves_body_shape_alone_unless_it_is_asked_for(self):
        """An issue body and a comment have no section schema of their own."""
        with self.repo() as root:
            self.shape_repo(root)
            out = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {"BODY": "## What to review\n\nNo queued action requested.\n"},
            ), contextlib.redirect_stdout(out):
                code = PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                    "--queue-actor", "any",
                    "--unscoped",
                ])
            printed = out.getvalue()
            self.assertEqual(0, code, printed)
            self.assertNotIn("explanation-shape", printed)

    def test_a_blocking_projection_finding_still_fails_beside_an_advisory(self):
        """The advisory line is added beside the verdict, never instead of it."""
        with self.repo() as root:
            self.shape_repo(root)
            self.queue_item(root, name="non-blocking-review-boundary.md")
            self.git(root, "add", ".")
            broken = self.SHAPED_BODY.replace(
                "## Verification\n\nThe suite passed.\n", ""
            ).replace(
                "No queued action requested.",
                "1. [Review the boundary.](https://example.invalid/elsewhere)",
            )
            out = io.StringIO()
            with mock.patch.dict(os.environ, {"BODY": broken}), \
                    contextlib.redirect_stdout(out):
                code = PROJECTION.main([
                    "--from-env", "BODY",
                    "--action-section", "What to review",
                    "--queue-actor", "any",
                    "--unscoped",
                    "--pull-request-body-shape",
                ])
            printed = out.getvalue()
            self.assertEqual(1, code, printed)
            self.assertIn("[action-projection]", printed)
            self.assertIn(
                "explanation-shape: 1 advisory finding(s) (not blocking)",
                printed,
            )

    def test_body_shape_cannot_be_asked_of_a_source_file_input(self):
        """That input is not a body, so the flag is refused, never ignored."""
        with self.repo() as root:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False
            ) as state_file:
                state_file.write('{"current":[],"released":[]}\n')
                state_path = state_file.name
            try:
                errors = io.StringIO()
                with mock.patch.object(PROJECTION, "REPO", root), \
                        contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(errors):
                    self.assertEqual(
                        2,
                        PROJECTION.main([
                            "--external-source-release-state-file", state_path,
                            "--pull-request-body-shape",
                            "--base-revision", "0" * 40,
                            "--candidate-revision", "1" * 40,
                        ]),
                    )
                self.assertIn("cannot be combined", errors.getvalue())
            finally:
                Path(state_path).unlink()


class RepositoryViewTests(unittest.TestCase):
    """One read of a repository view must answer exactly what per-path reads did."""

    @contextlib.contextmanager
    def repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(str(git_fixture_skeleton()), str(root / ".git"))
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

    def test_a_directory_is_not_a_tracked_file_and_has_no_record(self):
        with self.repo() as root:
            (root / "queue").mkdir()
            (root / "queue" / "item.md").write_text("body\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "one file under one directory")
            revision = self.git(root, "rev-parse", "HEAD")
            for candidate_revision in (None, revision):
                # A directory holding exactly one file is the case where a
                # per-path read returns a single record that is not the path.
                self.assertIsNone(PROJECTION.candidate_record(
                    "queue", repo=root, candidate_revision=candidate_revision
                ))
                self.assertFalse(PROJECTION.tracked_regular_file(
                    "queue", repo=root, candidate_revision=candidate_revision
                ))
                self.assertTrue(PROJECTION.tracked_regular_file(
                    "queue/item.md",
                    repo=root,
                    candidate_revision=candidate_revision,
                ))
                self.assertEqual(
                    ["queue/item.md"],
                    PROJECTION.candidate_paths(
                        "queue",
                        repo=root,
                        candidate_revision=candidate_revision,
                    ),
                )

    def test_a_path_recorded_at_several_merge_stages_is_not_one_record(self):
        with self.repo() as root:
            (root / "item.md").write_text("base\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "base")
            base = self.git(root, "rev-parse", "HEAD")
            self.git(root, "checkout", "-q", "-b", "other")
            (root / "item.md").write_text("other\n", encoding="utf-8")
            self.git(root, "commit", "-qam", "other side")
            self.git(root, "checkout", "-q", base)
            self.git(root, "checkout", "-q", "-B", "mine")
            (root / "item.md").write_text("mine\n", encoding="utf-8")
            self.git(root, "commit", "-qam", "my side")
            merge = subprocess.run(
                ["git", "merge", "--no-commit", "other"],
                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, merge.returncode, "the merge must conflict")
            staged = self.git(root, "ls-files", "--stage", "item.md")
            self.assertGreater(len(staged.splitlines()), 1, staged)
            self.assertIsNone(PROJECTION.candidate_record("item.md", repo=root))
            self.assertFalse(
                PROJECTION.tracked_regular_file("item.md", repo=root)
            )

    def test_an_empty_tracked_file_is_not_a_tracked_regular_file(self):
        with self.repo() as root:
            (root / "empty.md").write_text("", encoding="utf-8")
            (root / "full.md").write_text("x\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.assertFalse(PROJECTION.tracked_regular_file("empty.md", repo=root))
            self.assertTrue(PROJECTION.tracked_regular_file("full.md", repo=root))

    def test_a_view_is_read_once_inside_one_scope(self):
        with self.repo() as root:
            (root / "queue").mkdir()
            (root / "a.md").write_text("a\n", encoding="utf-8")
            (root / "b.md").write_text("b\n", encoding="utf-8")
            (root / "queue" / "c.md").write_text("c\n", encoding="utf-8")
            self.git(root, "add", ".")
            with mock.patch.object(
                PROJECTION, "git_output", wraps=PROJECTION.git_output
            ) as reads, PROJECTION.repository_views():
                for _ in range(4):
                    PROJECTION.tracked_regular_file("a.md", repo=root)
                    PROJECTION.tracked_regular_file("b.md", repo=root)
                    PROJECTION.candidate_paths("queue", repo=root)
            self.assertEqual(
                1, reads.call_count,
                "one scope must read the index once, not once per lookup",
            )

    def test_a_later_run_never_answers_from_an_earlier_run_s_view(self):
        with self.repo() as root:
            (root / "queue").mkdir()
            (root / "queue" / "a.md").write_text("a\n", encoding="utf-8")
            self.git(root, "add", ".")
            with PROJECTION.repository_views():
                self.assertEqual(
                    ["queue/a.md"],
                    PROJECTION.candidate_paths("queue", repo=root),
                )
                self.assertFalse(
                    PROJECTION.tracked_regular_file("queue/b.md", repo=root)
                )
            (root / "queue" / "b.md").write_text("b\n", encoding="utf-8")
            self.git(root, "add", ".")
            with PROJECTION.repository_views():
                self.assertEqual(
                    ["queue/a.md", "queue/b.md"],
                    PROJECTION.candidate_paths("queue", repo=root),
                )
                self.assertTrue(
                    PROJECTION.tracked_regular_file("queue/b.md", repo=root)
                )
            self.assertIsNone(
                PROJECTION._REPOSITORY_VIEWS,
                "a closed scope must leave no view behind",
            )

    def test_a_nested_scope_joins_the_open_one_rather_than_diverging(self):
        with self.repo() as root:
            (root / "a.md").write_text("a\n", encoding="utf-8")
            self.git(root, "add", ".")
            with PROJECTION.repository_views():
                outer = PROJECTION.repository_view(root, None)
                with PROJECTION.repository_views():
                    self.assertIs(outer, PROJECTION.repository_view(root, None))
                # Leaving the inner scope must not close the outer one.
                self.assertIs(outer, PROJECTION.repository_view(root, None))
            self.assertIsNone(PROJECTION._REPOSITORY_VIEWS)

    def test_outside_every_scope_each_lookup_reads_the_repository_again(self):
        with self.repo() as root:
            (root / "queue").mkdir()
            (root / "queue" / "a.md").write_text("a\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.assertEqual(
                ["queue/a.md"], PROJECTION.candidate_paths("queue", repo=root)
            )
            (root / "queue" / "b.md").write_text("b\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.assertEqual(
                ["queue/a.md", "queue/b.md"],
                PROJECTION.candidate_paths("queue", repo=root),
            )

    def test_an_empty_prefix_is_refused_rather_than_read_as_everything(self):
        with self.repo() as root:
            (root / "a.md").write_text("a\n", encoding="utf-8")
            self.git(root, "add", ".")
            # Git refuses an empty pathspec; the snapshot must not quietly
            # start answering it with the whole repository.
            with self.assertRaises(ValueError):
                PROJECTION.candidate_paths("", repo=root)

    def test_one_blob_is_read_once_per_run_and_re_read_in_the_next(self):
        with self.repo() as root:
            (root / "item.md").write_text("first\n", encoding="utf-8")
            self.git(root, "add", ".")
            with PROJECTION.repository_views():
                self.assertEqual(
                    "first\n", PROJECTION.candidate_text("item.md", repo=root)
                )
                (root / "item.md").write_text("second\n", encoding="utf-8")
                self.git(root, "add", ".")
                self.assertEqual(
                    "first\n",
                    PROJECTION.candidate_text("item.md", repo=root),
                    "one run must see one consistent view",
                )
            with PROJECTION.repository_views():
                self.assertEqual(
                    "second\n", PROJECTION.candidate_text("item.md", repo=root)
                )

    def test_reading_a_path_the_repository_does_not_track_still_raises(self):
        with self.repo() as root:
            (root / "a.md").write_text("a\n", encoding="utf-8")
            self.git(root, "add", ".")
            with PROJECTION.repository_views():
                with self.assertRaises(RuntimeError):
                    PROJECTION.candidate_text("missing.md", repo=root)


if __name__ == "__main__":
    unittest.main()
