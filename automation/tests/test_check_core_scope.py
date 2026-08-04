import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "check_core_scope.py"
SPEC = importlib.util.spec_from_file_location("check_core_scope", MODULE_PATH)
SCOPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCOPE)


COMPLETE_DESIGN = """# Design

## Core fit

**Agent substitution:** pass — another agent reads the same repository files
**Provider substitution:** pass — provider adapters invoke the same local command
**Repository substitution:** pass — unrelated repositories need the same boundary
**User-global writes:** none
**Why AgentFold core:** this protects AgentFold extension boundaries in every adopted repository
**Thin adapter:** none
"""
REVIEWED_REVISION = "a" * 40


class CoreScopeTests(unittest.TestCase):
    def make_task(self, root, scope="core", design=COMPLETE_DESIGN, status="1_in-progress",
                  verification=None, claimant="author"):
        task = Path(root) / "tasks" / status / "2026-07-22-example"
        task.mkdir(parents=True)
        (task / "task.md").write_text(
            f"# Example\n\n**Claimed-by:** {claimant}\n**Filed:** 2026-07-22\n"
            f"**Repository scope:** {scope}\n", encoding="utf-8"
        )
        if design is not None:
            (task / "design.md").write_text(design, encoding="utf-8")
        if verification is not None:
            (task / "verification.md").write_text(
                "# Verification\n\n## Review verdicts\n\n"
                f"**Reviewed revision:** {REVIEWED_REVISION}\n\n" + verification,
                encoding="utf-8",
            )
        return task

    def test_core_path_boundary_excludes_designs_and_services(self):
        self.assertTrue(SCOPE.is_core_path("skills/example/SKILL.md"))
        self.assertTrue(SCOPE.is_core_path("automation/check.py"))
        self.assertTrue(SCOPE.is_core_path("AGENTS.md"))
        self.assertFalse(SCOPE.is_core_path("docs/designs/provider-study.md"))
        self.assertFalse(SCOPE.is_core_path("services/example/client.py"))
        self.assertTrue(SCOPE.is_core_path("tasks/AGENTS.md"))
        self.assertTrue(SCOPE.is_core_path("handbook/git-workflow.md"))
        self.assertFalse(SCOPE.is_core_path("CLAUDE.md"))
        self.assertTrue(SCOPE.is_core_path("CLAUDE.md", {"CLAUDE.md"}))
        self.assertFalse(SCOPE.is_core_path(".gitignore"))
        self.assertTrue(SCOPE.is_core_path("AGENT_GUIDE.md"))
        self.assertFalse(SCOPE.is_core_path("ARCHITECTURE.md"))
        self.assertFalse(SCOPE.is_core_path("DEVELOPMENT.md"))
        self.assertFalse(SCOPE.is_core_path("API.md"))
        self.assertFalse(SCOPE.is_core_path("BUSINESS_RULES.md"))
        self.assertFalse(SCOPE.is_core_path("GEMINI.md"))
        self.assertTrue(SCOPE.is_core_path("GEMINI.md", {"GEMINI.md"}))
        self.assertTrue(SCOPE.is_core_path(".github/copilot-instructions.md"))
        self.assertTrue(SCOPE.is_core_path(".windsurf/rules/policy.md"))
        self.assertFalse(SCOPE.is_core_path(".clinerules/policy.md"))
        self.assertTrue(SCOPE.is_core_path(
            ".clinerules/policy.md", {".clinerules/policy.md"}
        ))
        self.assertFalse(SCOPE.is_core_path("README.md"))
        self.assertFalse(SCOPE.is_core_path(".github/ISSUE_TEMPLATE/bug_report.md"))
        self.assertFalse(SCOPE.is_core_path(".github/ISSUE_TEMPLATE/agent_bug.md"))

    def test_only_registered_provider_adapter_is_core(self):
        registered = {
            ".github/scripts/collect_review_actions.py",
            ".github/workflows/harness.yml",
            ".gitlab-ci.yml",
            "CLAUDE.md",
        }
        self.assertTrue(SCOPE.is_core_path(
            ".github/scripts/collect_review_actions.py", registered
        ))
        self.assertTrue(SCOPE.is_core_path(".github/workflows/harness.yml", registered))
        self.assertTrue(SCOPE.is_core_path(".gitlab-ci.yml", registered))
        self.assertTrue(SCOPE.is_core_path("CLAUDE.md", registered))
        self.assertFalse(SCOPE.is_core_path(".github/workflows/deploy-payments.yml", registered))

    def test_task_branch_parsing_supports_full_ref(self):
        self.assertEqual("2026-07-22-example", SCOPE.task_id_from_branch(
            "refs/heads/task/2026-07-22-example"
        ))
        self.assertIsNone(SCOPE.task_id_from_branch("main"))

    def test_complete_core_fit_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp)
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_annotated_core_fit_heading_does_not_consume_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            annotated = COMPLETE_DESIGN.replace(
                "## Core fit", "## Core fit (required when changing AgentFold core)"
            )
            task = self.make_task(tmp, design=annotated)
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_bare_level_two_heading_terminates_core_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            fields_only = COMPLETE_DESIGN.split("## Core fit\n\n", 1)[1]
            design = (
                "# Design\n\n## Core fit\n\nThe receipt stops here.\n\n"
                "##\n\n" + fields_only
            )
            task = self.make_task(tmp, design=design)
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("Agent substitution" in error for error in errors))

    def test_complete_core_fit_passes_with_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace("\n", "\r\n"))
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_missing_design_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, design=None)
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("needs design.md" in error for error in errors))

    def test_fenced_receipt_example_is_not_evidence(self):
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, design=f"# Design\n\n{fence}markdown\n{COMPLETE_DESIGN}\n{fence}\n"
                )
                errors = SCOPE.validate_task(task, touched_core=True)
                self.assertTrue(any("exactly one real" in error for error in errors))

    def test_html_commented_receipt_is_not_evidence(self):
        for close in ("-->\n", ""):
            with self.subTest(close=close), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, design=f"# Design\n\n<!--\n{COMPLETE_DESIGN}\n{close}"
                )
                errors = SCOPE.validate_task(task, touched_core=True)
                self.assertTrue(any("exactly one real" in error for error in errors))

    def test_raw_html_block_receipt_is_not_evidence(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        for tag in ("pre", "details", "table", "h1", "menuitem", "custom-element"):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, design=f"# Design\n\n<{tag}>\n{compact_receipt}\n</{tag}>\n"
                )
                errors = SCOPE.validate_task(task, touched_core=True)
                self.assertTrue(any("exactly one real" in error for error in errors))

    def test_complete_custom_tag_keeps_following_compact_receipt_in_html_block(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design="# Design\n\n<custom-element></custom-element>\n" + compact_receipt
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_partial_commonmark_html_start_keeps_compact_receipt_in_block(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        for opening in ("<div", "<div class", "<pre"):
            with self.subTest(opening=opening), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, design="# Design\n\n" + opening + "\n" + compact_receipt
                )
                errors = SCOPE.validate_task(task, touched_core=True)
                self.assertTrue(any("exactly one real" in error for error in errors))

    def test_type1_html_block_can_end_with_another_type1_end_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design="# Design\n\n<pre>\nliteral\n</script>\n" + COMPLETE_DESIGN
            )
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_type1_html_end_tag_must_be_exact(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design="# Design\n\n<pre\n</script >\n" + compact_receipt
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_fence_markers_inside_html_do_not_change_block_state(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp,
                design=(
                    "# Design\n\n<div>\n```\nliteral\n```\n" + compact_receipt
                ),
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_non_ascii_space_does_not_end_html_block(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design="# Design\n\n<div>\n\N{NO-BREAK SPACE}\n" + compact_receipt
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_form_feed_is_not_a_commonmark_line_boundary(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design="# Design\n\n<div>\n\f\n" + compact_receipt
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_blank_terminated_and_special_html_receipts_are_not_evidence(self):
        compact_receipt = "\n".join(
            line for line in COMPLETE_DESIGN.splitlines() if line.strip()
        )
        wrappers = (
            "<hr>\n{compact}\n",
            "<?processing\n{receipt}\n?>\n",
            "<![CDATA[\n{receipt}\n]]>\n",
            "<!DECLARATION\n{receipt}\n>\n",
            "<!declaration\n{receipt}\n>\n",
        )
        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, design="# Design\n\n" + wrapper.format(
                        receipt=COMPLETE_DESIGN, compact=compact_receipt
                    )
                )
                errors = SCOPE.validate_task(task, touched_core=True)
                self.assertTrue(any("exactly one real" in error for error in errors))

    def test_three_space_indented_fence_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, design=f"# Design\n\n   ~~~markdown\n{COMPLETE_DESIGN}\n   ~~~\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exactly one real" in error for error in errors))

    def test_service_scope_cannot_change_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, scope="service:example")
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("Repository scope" in error for error in errors))

    def test_placeholder_rationale_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace(
                "this protects AgentFold extension boundaries in every adopted repository", "<why>"
            ))
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("Why AgentFold core" in error for error in errors))

    def test_user_global_write_declaration_must_be_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace(
                "**User-global writes:** none", "**User-global writes:** installs a hook"
            ))
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("User-global writes" in error for error in errors))

    def test_duplicate_core_fit_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            duplicate = COMPLETE_DESIGN.replace(
                "**User-global writes:** none",
                "**User-global writes:** installs in home\n**User-global writes:** none",
            )
            task = self.make_task(tmp, design=duplicate)
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("duplicate field" in error for error in errors))

    def test_thin_adapter_contract_is_structured(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = (
                "canonical=automation/check.py; optional=yes; policy=none; writes=repo-only"
            )
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace(
                "**Thin adapter:** none", f"**Thin adapter:** {adapter}"
            ))
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_thin_adapter_values_are_exact_and_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            malformed = "canonical=; optional=yes-but-no; policy=none-until-runtime; writes=repo-only-and-home"
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace(
                "**Thin adapter:** none", f"**Thin adapter:** {malformed}"
            ))
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("exact nonempty" in error for error in errors))

    def test_independent_review_is_manual_by_default_at_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, status="3_in-review")
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_manual_independent_review_accepts_valid_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / reviewer: approve — tried replacing every integration\n"
            )
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True, require_review=True))
            self.assertEqual([], SCOPE.validate_task(task, touched_core=False, require_review=True))

    def test_review_parser_closes_when_a_verdict_precedes_the_revision_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification=(
                    "- core-fit / early: block — appears before the binding\n"
                    f"**Reviewed revision:** {'b' * 40}\n\n"
                    "- core-fit / reviewer: approve — bound review\n"
                ),
            )
            verification = task / "verification.md"
            text = verification.read_text(encoding="utf-8")
            verification.write_text(
                text.replace(
                    f"**Reviewed revision:** {REVIEWED_REVISION}\n\n",
                    "",
                    1,
                ),
                encoding="utf-8",
            )
            errors = SCOPE.validate_task(
                task, touched_core=True, require_review=True
            )
            self.assertTrue(any("independent reviewer" in error for error in errors), errors)

    def test_review_parser_ends_at_first_nonreceipt_content(self):
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
        for boundary in boundaries:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp,
                    status="3_in-review",
                    verification=(
                        boundary
                        + "- core-fit / owner: approve — production release\n"
                    ),
                )
                errors = SCOPE.validate_task(
                    task, touched_core=True, require_review=True
                )
                self.assertTrue(any(
                    "independent reviewer" in error for error in errors
                ), errors)

    def test_review_parser_rejects_a_revision_like_setext_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp,
                status="3_in-review",
                verification="- core-fit / reviewer: approve — outside section\n",
            )
            (task / "verification.md").write_text(
                "# Verification\n\n## Review verdicts\n\n"
                f"**Reviewed revision:** {'a' * 40}\n"
                "---\n\n"
                "- core-fit / reviewer: approve — outside section\n",
                encoding="utf-8",
            )
            errors = SCOPE.validate_task(
                task, touched_core=True, require_review=True
            )
            self.assertTrue(any("independent reviewer" in error for error in errors), errors)

    def test_review_parser_rejects_container_and_decorated_headings(self):
        revision = f"**Reviewed revision:** {'a' * 40}"
        receipt = "- core-fit / reviewer: approve — bound review"
        cases = (
            f"> ## Review verdicts\n>\n> {revision}\n>\n> {receipt}\n",
            f"- ## Review verdicts\n\n  {revision}\n\n  {receipt}\n",
            f"## Review verdicts (formal)\n\n{revision}\n\n{receipt}\n",
            f"## REVIEW VERDICTS\n\n{revision}\n\n{receipt}\n",
        )
        for text in cases:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(tmp, status="3_in-review")
                (task / "verification.md").write_text(text, encoding="utf-8")
                errors = SCOPE.validate_task(
                    task, touched_core=True, require_review=True
                )
                self.assertTrue(any("Review verdicts" in error for error in errors), errors)
                self.assertTrue(any("independent reviewer" in error for error in errors), errors)

    def test_review_parser_accepts_blank_separated_contiguous_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp,
                status="3_in-review",
                verification=(
                    "- core-fit / first: approve — could not break it\n\n"
                    "- core-fit / second: approve — boundary remained closed\n"
                ),
            )
            self.assertEqual([], SCOPE.validate_task(
                task, touched_core=True, require_review=True
            ))

    def test_anonymous_review_does_not_satisfy_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit /  : approve — no reviewer identity\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_review_identity_cannot_cross_a_line_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / \nreviewer: approve — split identity\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_shared_identity_tokens_do_not_merge_distinct_reviewers(self):
        for claimant, reviewer in (
            ("codex agent", "claude agent"),
            ("author@example.com", "reviewer@example.com"),
            ("Alice Smith", "Bob Smith"),
        ):
            with self.subTest(claimant=claimant), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, status="3_in-review", claimant=claimant,
                    verification=(
                        f"- core-fit / {reviewer}: approve — independent review\n"
                    ),
                )
                self.assertEqual([], SCOPE.validate_task(
                    task, touched_core=True, require_review=True
                ))

    def test_unicode_review_identity_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / 李雷: approve — independent review\n",
            )
            self.assertEqual([], SCOPE.validate_task(
                task, touched_core=True, require_review=True
            ))

    def test_self_review_does_not_satisfy_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / author: approve — looks portable\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_identity_word_order_does_not_create_a_second_reviewer(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="Smith Alice",
                verification="- core-fit / Alice Smith: approve — self review\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_reviewed_revision_field_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification="- core-fit / reviewer: approve — unbound review\n",
            )
            (task / "verification.md").write_text(
                "# Verification\n\n## Review verdicts\n\n"
                "- core-fit / reviewer: approve — unbound review\n",
                encoding="utf-8",
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("Reviewed revision" in error for error in errors))

    def test_reviewed_revision_accepts_full_sha1_or_sha256_ids(self):
        for length in (40, 64):
            with self.subTest(length=length), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, status="3_in-review",
                    verification="- core-fit / reviewer: approve — bound review\n",
                )
                revision = "b" * length
                (task / "verification.md").write_text(
                    "# Verification\n\n## Review verdicts\n\n"
                    f"**Reviewed revision:** {revision}\n\n"
                    "- core-fit / reviewer: approve — bound review\n",
                    encoding="utf-8",
                )
                checked = []
                errors = SCOPE.validate_task(
                    task,
                    touched_core=True,
                    require_review=True,
                    review_revision_check=lambda value: checked.append(value) or [],
                )
                self.assertEqual([], errors)
                self.assertEqual([revision], checked)

    def test_historical_revision_fields_outside_formal_block_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, status="3_in-review")
            (task / "verification.md").write_text(
                "# Verification\n\n"
                "## Historical panel\n\n"
                f"**Reviewed revision:** {'b' * 40}\n\n"
                "- adversarial panel / reviewer: block — prior candidate failed\n\n"
                "## Review verdicts\n\n"
                f"**Reviewed revision:** {'a' * 40}\n\n"
                "- core-fit / reviewer: approve — repaired candidate held\n",
                encoding="utf-8",
            )
            self.assertEqual([], SCOPE.validate_task(
                task, touched_core=True, require_review=True
            ))

    def test_duplicate_revision_inside_formal_block_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, status="3_in-review")
            (task / "verification.md").write_text(
                "# Verification\n\n## Review verdicts\n\n"
                f"**Reviewed revision:** {'a' * 40}\n\n"
                f"**Reviewed revision:** {'b' * 40}\n\n"
                "- core-fit / reviewer: approve — must not count\n",
                encoding="utf-8",
            )
            errors = SCOPE.validate_task(
                task, touched_core=True, require_review=True
            )
            self.assertTrue(any("Reviewed revision" in error for error in errors), errors)
            self.assertTrue(any("independent reviewer" in error for error in errors), errors)

    def test_abbreviated_reviewed_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification="- core-fit / reviewer: approve — weak binding\n",
            )
            (task / "verification.md").write_text(
                "# Verification\n\n## Review verdicts\n\n"
                "**Reviewed revision:** abc1234\n\n"
                "- core-fit / reviewer: approve — weak binding\n",
                encoding="utf-8",
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("Reviewed revision" in error for error in errors))

    def test_review_parser_rejects_noncanonical_verdict_lines(self):
        near_misses = (
            "* core-fit / reviewer: approve — could not break it\n",
            "- Core-fit / reviewer: approve — could not break it\n",
            "- core-fit / reviewer: APPROVE — could not break it\n",
            "- core-fit / reviewer: approve - could not break it\n",
            "- core-fit / reviewer:  approve — could not break it\n",
        )
        for verdict in near_misses:
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(
                    tmp, status="3_in-review", verification=verdict
                )
                errors = SCOPE.validate_task(
                    task, touched_core=True, require_review=True
                )
                self.assertTrue(any(
                    "independent reviewer" in error for error in errors
                ), errors)

    def test_fenced_review_example_is_not_a_verdict(self):
        for wrapper in (
            "~~~text\n- core-fit / reviewer: approve — example only\n~~~\n",
            "<!-- - core-fit / reviewer: approve — example only -->\n",
        ):
            with self.subTest(wrapper=wrapper), tempfile.TemporaryDirectory() as tmp:
                task = self.make_task(tmp, status="3_in-review", verification=wrapper)
                errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
                self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_raw_html_block_review_is_not_a_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification=(
                    "<pre>\n- core-fit / reviewer: approve — example only\n</pre>\n"
                ),
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_blocking_review_without_approve_majority_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification="- core-fit / reviewer: block — provider policy leaked into core\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("approve majority" in error for error in errors))

    def test_approve_majority_preserves_historical_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification=(
                    "- core-fit / first: block — found a concrete bypass\n"
                    "- core-fit / second: approve — bypass is fixed\n"
                    "- core-fit / third: approve — could not reproduce the bypass\n"
                ),
            )
            self.assertEqual([], SCOPE.validate_task(
                task, touched_core=True, require_review=True
            ))

    def test_home_access_in_core_executable_fails(self):
        content = "target = Path.home() / '.agent'\n"
        findings = SCOPE.global_state_findings(
            ["automation/install_personal.py"], lambda _: content
        )
        self.assertEqual(1, len(findings))

    def test_shell_and_powershell_home_forms_fail(self):
        cases = {
            "automation/install-personal": "#!/bin/sh\ntarget=${HOME}/.agent\n",
            "automation/install.ps1": "$target = $env:USERPROFILE + '/.agent'\n",
            "automation/install.sh": "mkdir ~/.agent\ncp file $CODEX_HOME/plugins/\n",
            "automation/install.py": "target = os.getenv('XDG_CONFIG_HOME')\n",
        }
        for path, content in cases.items():
            with self.subTest(path=path):
                findings = SCOPE.global_state_findings(
                    [path], lambda _: content, lambda _: "100755"
                )
                self.assertGreaterEqual(len(findings), 1)

    def test_skill_audit_examples_are_left_to_core_fit_review(self):
        findings = SCOPE.global_state_findings(
            ["skills/example/SKILL.md"],
            lambda _: "Reject scripts that run `mkdir -p ~/.agent`.\n",
        )
        self.assertEqual([], findings)

    def test_forced_generated_adapter_file_is_rejected_but_deletion_is_allowed(self):
        path = ".agents/skills/personal/SKILL.md"
        self.assertEqual(1, len(SCOPE.generated_adapter_findings(
            [path], lambda _: "personal policy\n"
        )))

        def deleted(_):
            raise RuntimeError("missing from tree")

        self.assertEqual([], SCOPE.generated_adapter_findings([path], deleted))

    def test_product_gitignore_edits_outside_adapter_block_are_allowed(self):
        content = "\n".join((
            "dist/", SCOPE.ADAPTER_IGNORE_START, *SCOPE.ADAPTER_IGNORE_LINES,
            SCOPE.ADAPTER_IGNORE_END, ".env.local", "",
        ))
        self.assertEqual([], SCOPE.adapter_ignore_findings(
            [".gitignore"], lambda _: content
        ))

    def test_adapter_ignore_block_cannot_be_removed_or_unignored(self):
        missing = "dist/\n"
        self.assertTrue(SCOPE.adapter_ignore_findings(
            [".gitignore"], lambda _: missing
        ))
        unignored = "\n".join((
            SCOPE.ADAPTER_IGNORE_START, *SCOPE.ADAPTER_IGNORE_LINES,
            SCOPE.ADAPTER_IGNORE_END, "!.agents/**", "",
        ))
        self.assertTrue(SCOPE.adapter_ignore_findings(
            [".gitignore"], lambda _: unignored
        ))

    def test_tests_and_non_core_files_are_not_static_scanned(self):
        content = "target = Path.home() / '.agent'\n"
        paths = ["automation/tests/test_home.py", "services/example/install.py"]
        self.assertEqual([], SCOPE.global_state_findings(paths, lambda _: content))

    def test_evidence_loader_cannot_use_untracked_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp)
            task_text = (task / "task.md").read_text(encoding="utf-8")

            def index_only(path):
                if path.endswith("task.md"):
                    return task_text
                raise RuntimeError("not in index")

            errors = SCOPE.validate_task(task, touched_core=True, load_text=index_only)
            self.assertTrue(any("needs design.md" in error for error in errors))

    def test_task_discovery_uses_selected_tree_not_working_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wanted = "tasks/3_in-review/2026-07-22-example/task.md"

            def head_tree(path):
                if path == wanted:
                    return "**Repository scope:** core\n"
                raise RuntimeError("missing")

            task = SCOPE.find_task(
                "task/2026-07-22-example", repo=root, load_text=head_tree
            )
            self.assertEqual(root / "tasks/3_in-review/2026-07-22-example", task)

    def test_staged_paths_include_deleted_and_both_renamed_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "automation").mkdir()
            (root / "docs").mkdir()
            tool = root / "automation" / "tool.py"
            tool.write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)

            subprocess.run(["git", "mv", "automation/tool.py", "docs/tool.py"], cwd=root, check=True)
            paths = SCOPE.staged_paths(root)
            self.assertIn("automation/tool.py", paths)
            self.assertIn("docs/tool.py", paths)

            subprocess.run(["git", "reset", "--hard", "-q", "HEAD"], cwd=root, check=True)
            tool.unlink()
            subprocess.run(["git", "add", "-u"], cwd=root, check=True)
            self.assertIn("automation/tool.py", SCOPE.staged_paths(root))

    def test_reviewed_revision_rejects_later_or_pending_core_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "automation").mkdir()
            tool = root / "automation" / "tool.py"
            tool.write_text("print('reviewed')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "reviewed"], cwd=root, check=True)
            reviewed = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            (root / "notes.txt").write_text("review record\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "records"], cwd=root, check=True)
            records_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertEqual([], SCOPE.review_revision_findings(
                reviewed, records_head, repo=root
            ))
            self.assertTrue(SCOPE.review_revision_findings(
                reviewed, records_head, pending_paths=["automation/pending.py"], repo=root
            ))

            tool.write_text("print('changed after review')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "later core change"], cwd=root, check=True)
            current = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            findings = SCOPE.review_revision_findings(reviewed, current, repo=root)
            self.assertTrue(any("stale" in finding for finding in findings))

    def test_reviewed_revision_binds_task_decision_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            task_id = "2026-07-22-example"
            task = root / "tasks" / "3_in-review" / task_id
            task.mkdir(parents=True)
            (task / "task.md").write_text("**Claimed-by:** author\n", encoding="utf-8")
            (task / "design.md").write_text(COMPLETE_DESIGN, encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "reviewed"], cwd=root, check=True)
            reviewed = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            done_task = root / "tasks" / "4_done" / task_id
            done_task.parent.mkdir(parents=True)
            subprocess.run(["git", "mv", str(task), str(done_task)], cwd=root, check=True)
            self.assertEqual([], SCOPE.review_revision_findings(
                reviewed,
                reviewed,
                pending_paths=SCOPE.staged_paths(root),
                task_id=task_id,
                selected_task_blobs=SCOPE.staged_task_input_blobs(task_id, root),
                repo=root,
            ))
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "move to done"], cwd=root, check=True)
            moved = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertEqual([], SCOPE.review_revision_findings(
                reviewed, moved, task_id=task_id, repo=root
            ))

            (done_task / "task.md").write_text(
                "**Claimed-by:** reviewer\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            self.assertTrue(SCOPE.review_revision_findings(
                reviewed,
                moved,
                pending_paths=SCOPE.staged_paths(root),
                task_id=task_id,
                selected_task_blobs=SCOPE.staged_task_input_blobs(task_id, root),
                repo=root,
            ))
            subprocess.run(["git", "commit", "-qm", "change claimant"], cwd=root, check=True)
            current = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            findings = SCOPE.review_revision_findings(
                reviewed, current, task_id=task_id, repo=root
            )
            self.assertTrue(any("task.md" in finding for finding in findings))

    def test_sha256_receipt_rejects_a_40_character_abbreviation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialized = subprocess.run(
                ["git", "init", "-q", "--object-format=sha256"],
                cwd=root, text=True, capture_output=True, check=False,
            )
            if initialized.returncode:
                self.skipTest("installed Git does not support SHA-256 repositories")
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "notes.txt").write_text("head\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=root, check=True)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertEqual(64, len(head))
            self.assertEqual([], SCOPE.review_revision_findings(head, head, repo=root))
            findings = SCOPE.review_revision_findings(head[:40], head, repo=root)
            self.assertTrue(any("full commit ID" in finding for finding in findings))

    def test_reviewed_revision_must_be_a_known_ancestor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "notes.txt").write_text("head\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=root, check=True)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            self.assertTrue(SCOPE.review_revision_findings("deadbee", head, repo=root))

    def test_replace_ref_cannot_pass_a_blob_as_the_reviewed_core_commit(self):
        """A `refs/replace/*` entry must not turn a blob into a reviewed commit.

        Bare, `git rev-parse --verify $BLOB^{commit}` answers from the
        replacement and prints the blob's own object id, so the blob clears both
        the "is this a commit" test and the full-object-id equality test that
        follows it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "notes.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            (root / "notes.txt").write_text("head\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=root, check=True)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            payload = root / "payload.txt"
            payload.write_text("not a commit\n", encoding="utf-8")
            blob = subprocess.check_output(
                ["git", "hash-object", "-w", str(payload)], cwd=root, text=True
            ).strip()

            def verdict():
                return SCOPE.review_revision_findings(blob, head, repo=root)

            without_replace = verdict()
            subprocess.run(
                ["git", "replace", "-f", blob, base], cwd=root, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                with_replace = verdict()
            finally:
                subprocess.run(["git", "replace", "-d", blob], cwd=root, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual(
                [f"reviewed revision {blob!r} is not a commit in this repository"],
                without_replace,
            )
            self.assertEqual(without_replace, with_replace)

    def test_replace_ref_cannot_hide_a_stale_core_fit_review(self):
        """The whole gate, not one check: a stale review must stay stale.

        Replacing the reviewed commit with the current one empties the later
        bound diff and makes the reviewed task inputs equal the current ones, so
        every bare read agrees the review is fresh when it is not.
        """
        task_id = "2026-07-22-example"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            task = root / "tasks" / "1_in-progress" / task_id
            task.mkdir(parents=True)
            (task / "task.md").write_text("# reviewed input\n", encoding="utf-8")
            (root / "automation").mkdir()
            tool = root / "automation" / "tool.py"
            tool.write_text("print('reviewed')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "reviewed"], cwd=root, check=True)
            reviewed = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            tool.write_text("print('changed after the review')\n", encoding="utf-8")
            (task / "task.md").write_text("# rewritten input\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "later core change"], cwd=root, check=True)
            current = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            def verdict():
                return SCOPE.review_revision_findings(
                    reviewed, current, task_id=task_id, repo=root
                )

            without_replace = verdict()
            subprocess.run(
                ["git", "replace", "-f", reviewed, current], cwd=root, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                with_replace = verdict()
            finally:
                subprocess.run(["git", "replace", "-d", reviewed], cwd=root, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual(1, len(without_replace), without_replace)
            self.assertIn("is stale", without_replace[0])
            self.assertIn("automation/tool.py", without_replace[0])
            self.assertIn("task input task.md", without_replace[0])
            self.assertEqual(without_replace, with_replace)


if __name__ == "__main__":
    unittest.main()
