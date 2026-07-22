import importlib.util
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
            (task / "verification.md").write_text(verification, encoding="utf-8")
        return task

    def test_core_path_boundary_excludes_designs_and_services(self):
        self.assertTrue(SCOPE.is_core_path("skills/example/SKILL.md"))
        self.assertTrue(SCOPE.is_core_path("automation/check.py"))
        self.assertTrue(SCOPE.is_core_path("AGENTS.md"))
        self.assertFalse(SCOPE.is_core_path("docs/designs/provider-study.md"))
        self.assertFalse(SCOPE.is_core_path("services/example/client.py"))

    def test_task_branch_parsing_supports_full_ref(self):
        self.assertEqual("2026-07-22-example", SCOPE.task_id_from_branch(
            "refs/heads/task/2026-07-22-example"
        ))
        self.assertIsNone(SCOPE.task_id_from_branch("main"))

    def test_complete_core_fit_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp)
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_missing_design_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(tmp, design=None)
            errors = SCOPE.validate_task(task, touched_core=True)
            self.assertTrue(any("needs design.md" in error for error in errors))

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

    def test_thin_adapter_contract_is_structured(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = (
                "canonical=automation/check.py; optional=yes; policy=none; writes=repo-only"
            )
            task = self.make_task(tmp, design=COMPLETE_DESIGN.replace(
                "**Thin adapter:** none", f"**Thin adapter:** {adapter}"
            ))
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True))

    def test_independent_review_is_required_at_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / reviewer: approve — tried replacing every integration\n"
            )
            self.assertEqual([], SCOPE.validate_task(task, touched_core=True, require_review=True))

    def test_self_review_does_not_satisfy_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review", claimant="author",
                verification="- core-fit / author: approve — looks portable\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("independent reviewer" in error for error in errors))

    def test_blocking_review_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.make_task(
                tmp, status="3_in-review",
                verification="- core-fit / reviewer: block — provider policy leaked into core\n"
            )
            errors = SCOPE.validate_task(task, touched_core=True, require_review=True)
            self.assertTrue(any("blocking verdict" in error for error in errors))

    def test_home_access_in_core_executable_fails(self):
        content = "target = Path.home() / '.agent'\n"
        findings = SCOPE.global_state_findings(
            ["automation/install_personal.py"], lambda _: content
        )
        self.assertEqual(1, len(findings))

    def test_tests_and_non_core_files_are_not_static_scanned(self):
        content = "target = Path.home() / '.agent'\n"
        paths = ["automation/tests/test_home.py", "services/example/install.py"]
        self.assertEqual([], SCOPE.global_state_findings(paths, lambda _: content))


if __name__ == "__main__":
    unittest.main()
