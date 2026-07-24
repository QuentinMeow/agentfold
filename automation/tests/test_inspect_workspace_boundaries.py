import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unicodedata
from pathlib import Path
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[1] / "inspect_workspace_boundaries.py"
)
INSPECTOR_SPEC = importlib.util.spec_from_file_location(
    "inspect_workspace_boundaries",
    str(SCRIPT),
)
INSPECTOR = importlib.util.module_from_spec(INSPECTOR_SPEC)
INSPECTOR_SPEC.loader.exec_module(INSPECTOR)


def clean_environment():
    return {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }


def run_git(*arguments):
    subprocess.run(
        ["git", *map(str, arguments)],
        check=True,
        env=clean_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding=sys.getfilesystemencoding(),
        errors="surrogateescape",
    )


class WorkspaceBoundaryInspectorTests(unittest.TestCase):
    def setUp(self):
        self.scratch_context = tempfile.TemporaryDirectory(
            prefix="agentfold-boundaries-"
        )
        self.scratch = Path(self.scratch_context.name).resolve()

    def tearDown(self):
        self.scratch_context.cleanup()

    def initialize_repository(self, name, commit=False):
        repository = self.scratch / name
        run_git("init", "-q", repository)
        if commit:
            run_git(
                "-C",
                repository,
                "-c",
                "user.name=Boundary Test",
                "-c",
                "user.email=boundary@example.invalid",
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "initial",
            )
        return repository

    def initialize_separate_workspace(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        restricted = self.scratch / "restricted-data"
        raw = self.scratch / "raw-imports"
        temporary = self.scratch / "temporary-data"
        for root in (restricted, raw, temporary):
            root.mkdir()
        return integration, publisher, restricted, raw, temporary

    def run_inspector(self, *arguments, environment=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            env=clean_environment() if environment is None else environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def full_arguments(self, roots):
        integration, publisher, restricted, raw, temporary = roots
        return (
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--restricted-root",
            restricted,
            "--raw-root",
            raw,
            "--temporary-root",
            temporary,
        )

    def assert_safety_limits(self, result, topology_status):
        self.assertEqual("", result.stderr)
        self.assertIn(f"storage-topology: {topology_status}", result.stdout)
        self.assertIn(
            "storage-topology-scope: declared-roots-and-reported-git-metadata",
            result.stdout,
        )
        self.assertIn(
            "inspection-atomicity: point-in-time-non-atomic",
            result.stdout,
        )
        self.assertIn("content-admission: not-inspected", result.stdout)
        self.assertIn("object-file-sharing: not-inspected", result.stdout)
        self.assertIn(
            "detached-git-worktree-association: not-inspected",
            result.stdout,
        )
        self.assertIn(
            "git-executable-authority: policy-bound-not-attested",
            result.stdout,
        )
        self.assertIn(
            "git-configuration-authority: not-inspected",
            result.stdout,
        )
        self.assertIn("publisher-cleanliness: not-inspected", result.stdout)
        self.assertIn("capability-isolation: unverified", result.stdout)
        self.assertIn("publication-admission: not-inspected", result.stdout)
        self.assertIn("publication-via-inspector: unavailable", result.stdout)
        self.assertIn("scan: not-inspected", result.stdout)
        self.assertIn("backup: not-inspected", result.stdout)
        self.assertIn("instruction-provenance: not-inspected", result.stdout)

    def test_separate_repositories_and_sibling_zones_pass_with_stable_redaction(self):
        roots = self.initialize_separate_workspace()

        first = self.run_inspector(*self.full_arguments(roots))
        second = self.run_inspector(*self.full_arguments(roots))

        self.assertEqual(0, first.returncode, first.stdout)
        self.assertEqual(first.stdout, second.stdout)
        self.assert_safety_limits(first, "verified")
        for root in roots:
            self.assertNotIn(str(root), first.stdout)
        self.assertIn(
            "integration-root: <redacted:integration-root>",
            first.stdout,
        )
        self.assertIn(
            "publisher-root: <redacted:publisher-root>",
            first.stdout,
        )

    def test_show_paths_displays_canonical_roots_without_broadening_claims(self):
        roots = self.initialize_separate_workspace()

        result = self.run_inspector(
            *self.full_arguments(roots),
            "--show-paths",
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        for root in roots:
            self.assertIn(str(root.resolve()), result.stdout)

    def test_linked_worktree_fails_shared_common_directory_check(self):
        integration = self.initialize_repository("private-integration", commit=True)
        publisher = self.scratch / "linked-publisher"
        run_git("-C", integration, "worktree", "add", "-q", "--detach", publisher)

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn("share a Git common directory", result.stdout)
        self.assertNotIn(str(integration), result.stdout)
        self.assertNotIn(str(publisher), result.stdout)

    def test_publisher_gitdir_inside_integration_metadata_fails(self):
        integration = self.scratch / "private-integration"
        integration_metadata = self.scratch / "integration-metadata"
        run_git(
            "init",
            "-q",
            f"--separate-git-dir={integration_metadata}",
            integration,
        )
        publisher_source = self.initialize_repository("publisher-source", commit=True)
        publisher = self.scratch / "attached-publisher"
        run_git(
            "-C",
            publisher_source,
            "worktree",
            "add",
            "-q",
            "--detach",
            publisher,
        )
        marker = publisher / ".git"
        marker_value = marker.read_text().strip()
        original_gitdir = Path(marker_value.split(":", 1)[1].strip())
        if not original_gitdir.is_absolute():
            original_gitdir = publisher / original_gitdir
        relocated_gitdir = (
            integration_metadata / "objects" / "publisher-worktree-gitdir"
        )
        shutil.move(str(original_gitdir), relocated_gitdir)
        marker.write_text(f"gitdir: {relocated_gitdir}\n")
        (relocated_gitdir / "commondir").write_text(
            f"{(publisher_source / '.git').resolve()}\n"
        )

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root Git gitdir metadata overlaps "
            "integration-root Git common metadata",
            result.stdout,
        )

    def test_publisher_with_external_effective_worktree_fails(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        run_git("-C", publisher, "config", "core.worktree", "../../private-integration")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root local Git configuration selects an external path",
            result.stdout,
        )

    def test_same_line_core_worktree_is_rejected_before_git_query(self):
        publisher = self.initialize_repository("clean-publisher")
        with (publisher / ".git" / "config").open("a") as config:
            config.write(
                f"\n[core] worktree = {self.scratch / 'external-worktree'}\n"
            )

        with mock.patch.object(INSPECTOR, "run_git") as git_query:
            with self.assertRaisesRegex(
                INSPECTOR.InspectionError,
                "local Git configuration selects an external path",
            ):
                INSPECTOR.require_git_worktree(
                    publisher,
                    "publisher-root",
                    "/usr/bin/git",
                )

        git_query.assert_not_called()

    def test_bare_publisher_fails_non_bare_worktree_requirement(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.scratch / "bare-publisher.git"
        run_git("init", "--bare", "-q", publisher)

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root is a bare Git repository, not a worktree",
            result.stdout,
        )

    def test_shared_clone_fails_publisher_alternates_check(self):
        integration = self.initialize_repository("private-integration", commit=True)
        publisher = self.scratch / "shared-clone"
        run_git("clone", "-q", "--shared", integration, publisher)

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn("publisher-root uses objects/info/alternates", result.stdout)

    def test_local_clone_reports_object_file_sharing_as_not_inspected(self):
        integration = self.initialize_repository("private-integration", commit=True)
        publisher = self.scratch / "local-clone"
        run_git("clone", "-q", "--local", integration, publisher)

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertIn("object-file-sharing: not-inspected", result.stdout)

    def test_overlapping_root_fails(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        restricted = integration / "restricted"
        restricted.mkdir()

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--restricted-root",
            restricted,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "integration-root overlaps restricted-root",
            result.stdout,
        )

    def test_symlink_alias_fails_after_canonicalization(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        restricted = self.scratch / "restricted"
        alias = self.scratch / "restricted-alias"
        restricted.mkdir()
        try:
            alias.symlink_to(restricted, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory symlinks unavailable: {error}")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--restricted-root",
            restricted,
            "--raw-root",
            alias,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "restricted-root overlaps raw-root after canonicalization",
            result.stdout,
        )

    def test_case_variant_alias_fails_by_filesystem_identity(self):
        roots = self.initialize_separate_workspace()
        integration = roots[0]
        alternate = Path(
            os.sep,
            *(
                part.swapcase() if index == 0 else part
                for index, part in enumerate(integration.parts[1:])
            ),
        )
        if (
            not alternate.exists()
            or str(alternate) == str(integration)
            or not os.path.samefile(integration, alternate)
        ):
            self.skipTest("filesystem has no case-variant alias for the scratch root")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            roots[1],
            "--raw-root",
            alternate,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "integration-root overlaps raw-root after canonicalization",
            result.stdout,
        )

    def test_unicode_normalization_alias_fails_by_filesystem_identity(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        restricted = self.scratch / unicodedata.normalize("NFC", "café")
        restricted.mkdir()
        alternate = self.scratch / unicodedata.normalize("NFD", "café")
        if (
            not alternate.exists()
            or str(alternate) == str(restricted)
            or not os.path.samefile(restricted, alternate)
        ):
            self.skipTest(
                "filesystem has no Unicode-normalization alias for the test root"
            )

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--restricted-root",
            restricted,
            "--raw-root",
            alternate,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "restricted-root overlaps raw-root after canonicalization",
            result.stdout,
        )

    def test_non_git_zone_inside_an_undeclared_repository_fails(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        undeclared_repository = self.initialize_repository("undeclared-repository")
        raw = undeclared_repository / "raw"
        raw.mkdir()

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--raw-root",
            raw,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn("raw-root is inside or is a Git repository", result.stdout)

    def test_non_git_zone_nested_in_a_bare_repository_fails(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        bare_repository = self.scratch / "undeclared-bare.git"
        run_git("init", "--bare", "-q", bare_repository)
        raw = bare_repository / "nested" / "raw"
        raw.mkdir(parents=True)

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--raw-root",
            raw,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn("raw-root is inside or is a Git repository", result.stdout)

    def test_missing_private_integration_requires_explicit_public_only_mode(self):
        publisher = self.initialize_repository("clean-publisher")

        missing = self.run_inspector("--publisher-root", publisher)
        public_only = self.run_inspector(
            "--publisher-root",
            publisher,
            "--public-only",
        )

        self.assertNotEqual(0, missing.returncode)
        self.assert_safety_limits(missing, "failed")
        self.assertIn(
            "--integration-root is required unless --public-only is explicit",
            missing.stdout,
        )
        self.assertEqual(0, public_only.returncode, public_only.stdout)
        self.assert_safety_limits(public_only, "verified")
        self.assertIn("mode: public-only", public_only.stdout)
        self.assertIn("private-integration-role: not-declared", public_only.stdout)
        self.assertIn("integration-root: not-declared", public_only.stdout)

    def test_public_only_rejects_every_private_zone_before_inspection(self):
        publisher = self.initialize_repository("clean-publisher")
        private_root = self.scratch / "private-zone"
        private_root.mkdir()
        for option in ("--restricted-root", "--raw-root", "--temporary-root"):
            with self.subTest(option=option):
                result = self.run_inspector(
                    "--publisher-root",
                    publisher,
                    "--public-only",
                    option,
                    private_root,
                )

                self.assertNotEqual(0, result.returncode)
                self.assert_safety_limits(result, "failed")
                self.assertIn(
                    "--public-only cannot inspect restricted, raw, or temporary roots",
                    result.stdout,
                )
                self.assertNotIn(str(private_root), result.stdout)

    def test_dirty_publisher_is_topology_valid_but_cleanliness_uninspected(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        (publisher / "untracked-private-content").write_text("not inspected\n")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertIn("publisher-cleanliness: not-inspected", result.stdout)

    def test_inherited_git_directory_and_work_tree_are_sanitized(self):
        roots = self.initialize_separate_workspace()
        environment = clean_environment()
        environment["GIT_DIR"] = str(roots[0] / ".git")
        environment["GIT_WORK_TREE"] = str(roots[0])
        environment["GIT_OBJECT_DIRECTORY"] = str(
            roots[0] / ".git" / "objects"
        )
        environment["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(
            roots[0] / ".git" / "objects"
        )
        global_home = self.scratch / "global-home"
        global_home.mkdir()
        (global_home / ".gitconfig").write_text(
            f"[core]\n\tworktree = {roots[0]}\n"
        )
        environment["HOME"] = str(global_home)

        result = self.run_inspector(
            *self.full_arguments(roots),
            environment=environment,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")

    def test_git_query_timeout_becomes_bounded_inspection_error(self):
        timeout = subprocess.TimeoutExpired(["git"], 5)
        with mock.patch.object(
            INSPECTOR.subprocess,
            "run",
            side_effect=timeout,
        ):
            with self.assertRaisesRegex(
                INSPECTOR.InspectionError,
                "Git boundary inspection timed out",
            ):
                INSPECTOR.run_git(
                    "/usr/bin/git",
                    self.scratch,
                    "rev-parse",
                    "--git-dir",
                )

    def test_workspace_path_cannot_replace_the_fixed_git_executable(self):
        roots = self.initialize_separate_workspace()
        fake_bin = self.scratch / "workspace-bin"
        fake_bin.mkdir()
        marker = self.scratch / "fake-git-ran"
        fake_git = fake_bin / "git"
        fake_git.write_text(
            "#!/bin/sh\n"
            ': > "$FAKE_GIT_MARKER"\n'
            "exit 99\n"
        )
        fake_git.chmod(0o755)
        environment = clean_environment()
        environment["PATH"] = f"{fake_bin}:{environment.get('PATH', '')}"
        environment["FAKE_GIT_MARKER"] = str(marker)

        result = self.run_inspector(
            *self.full_arguments(roots),
            environment=environment,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertFalse(marker.exists())

    def test_explicit_canonical_git_executable_binding_is_portable(self):
        roots = self.initialize_separate_workspace()
        discovered_git = shutil.which("git")
        self.assertIsNotNone(discovered_git)

        result = self.run_inspector(
            *self.full_arguments(roots),
            "--git-executable",
            Path(discovered_git).resolve(),
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")

    def test_missing_explicit_git_executable_binding_fails_redacted(self):
        roots = self.initialize_separate_workspace()
        missing = self.scratch / "private-toolchain" / "git"

        result = self.run_inspector(
            *self.full_arguments(roots),
            "--git-executable",
            missing,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "no trusted Git executable is available",
            result.stdout,
        )
        self.assertNotIn(str(missing), result.stdout)

    def test_git_executable_binding_inside_declared_root_is_rejected(self):
        roots = self.initialize_separate_workspace()
        workspace_git = roots[4] / "git"
        workspace_git.write_text("#!/bin/sh\nexit 99\n")
        workspace_git.chmod(0o755)

        result = self.run_inspector(
            *self.full_arguments(roots),
            "--git-executable",
            workspace_git,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "trusted Git executable binding is inside a declared workspace root",
            result.stdout,
        )
        self.assertNotIn(str(workspace_git), result.stdout)

    def test_local_git_config_include_is_rejected_without_reading_target(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        include_target = self.scratch / "private-config-fifo"
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(str(include_target))
        with (publisher / ".git" / "config").open("a") as config:
            config.write(f"\n[include]\n\tpath = {include_target}\n")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root local Git configuration uses external includes",
            result.stdout,
        )
        self.assertNotIn(str(include_target), result.stdout)

    def test_harmless_included_section_is_not_treated_as_an_include(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        with (publisher / ".git" / "config").open("a") as config:
            config.write(
                f"\n[included]\n\tpath = {self.scratch / 'external-config'}\n"
            )

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")

    def test_local_git_config_include_if_section_is_rejected(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        with (publisher / ".git" / "config").open("a") as config:
            config.write(
                '\n[includeIf "gitdir:**/declared-publisher/**"]\n'
                f"\tpath = {self.scratch / 'external-config'}\n"
            )

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root local Git configuration uses external includes",
            result.stdout,
        )

    def test_utf8_bom_cannot_hide_local_git_config_include(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        include_target = self.scratch / "bom-config-fifo"
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(str(include_target))
        config_path = publisher / ".git" / "config"
        original = config_path.read_bytes()
        config_path.write_bytes(
            b"\xef\xbb\xbf[include]\n\tpath = "
            + os.fsencode(str(include_target))
            + b"\n"
            + original
        )

        started = time.monotonic()
        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 4.0)
        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root local Git configuration uses external includes",
            result.stdout,
        )
        self.assertNotIn(str(include_target), result.stdout)

    def test_bare_publisher_config_is_not_read_before_shape_rejection(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.scratch / "bare-publisher.git"
        run_git("init", "--bare", "-q", publisher)
        include_target = self.scratch / "bare-config-fifo"
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(str(include_target))
        with (publisher / "config").open("a") as config:
            config.write(f"\n[include]\n\tpath = {include_target}\n")

        started = time.monotonic()
        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 4.0)
        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root is a bare Git repository, not a worktree",
            result.stdout,
        )

    def test_nested_publisher_ancestor_config_is_not_read(self):
        integration = self.initialize_repository("private-integration")
        publisher_parent = self.initialize_repository("publisher-parent")
        publisher = publisher_parent / "nested-declaration"
        publisher.mkdir()
        include_target = self.scratch / "nested-config-fifo"
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(str(include_target))
        with (publisher_parent / ".git" / "config").open("a") as config:
            config.write(f"\n[include]\n\tpath = {include_target}\n")

        started = time.monotonic()
        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 4.0)
        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root has no direct Git worktree marker",
            result.stdout,
        )

    def test_no_git_zone_ancestor_config_is_not_read(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("declared-publisher")
        raw_parent = self.initialize_repository("raw-parent")
        raw = raw_parent / "raw-data"
        raw.mkdir()
        include_target = self.scratch / "raw-ancestor-config-fifo"
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(str(include_target))
        with (raw_parent / ".git" / "config").open("a") as config:
            config.write(f"\n[include]\n\tpath = {include_target}\n")

        started = time.monotonic()
        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--raw-root",
            raw,
        )
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 4.0)
        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "raw-root is inside or is a Git repository",
            result.stdout,
        )

    def test_malformed_arguments_do_not_echo_sensitive_values(self):
        publisher = self.initialize_repository("declared-publisher")
        sensitive = "/private/customer-name/raw"

        result = self.run_inspector(
            "--publisher-root",
            publisher,
            "--raw-rooot",
            sensitive,
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertNotIn(sensitive, result.stderr)
        self.assertIn("invalid arguments; use --help", result.stderr)

    def test_publisher_http_alternates_file_fails(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        alternates = publisher / ".git" / "objects" / "info" / "http-alternates"
        alternates.write_text("https://example.invalid/objects\n")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root uses objects/info/http-alternates",
            result.stdout,
        )

    def test_inaccessible_publisher_alternates_directory_fails_closed(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        info = publisher / ".git" / "objects" / "info"
        (info / "alternates").write_text("../private-objects\n")
        info.chmod(0)
        try:
            result = self.run_inspector(
                "--integration-root",
                integration,
                "--publisher-root",
                publisher,
            )
        finally:
            info.chmod(0o700)

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")

    def test_inaccessible_ancestor_git_metadata_fails_closed(self):
        integration = self.initialize_repository("private-integration")
        publisher = self.initialize_repository("clean-publisher")
        outer = self.initialize_repository("outer-repository")
        raw = outer / "raw"
        raw.mkdir()
        metadata = outer / ".git"
        metadata.chmod(0)
        try:
            result = self.run_inspector(
                "--integration-root",
                integration,
                "--publisher-root",
                publisher,
                "--raw-root",
                raw,
            )
        finally:
            metadata.chmod(0o700)

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")

    def test_git_metadata_cannot_live_inside_another_declared_zone(self):
        integration = self.initialize_repository("private-integration")
        restricted = self.scratch / "restricted"
        restricted.mkdir()
        publisher = self.scratch / "publisher"
        publisher_metadata = restricted / "publisher-metadata"
        run_git(
            "init",
            "-q",
            f"--separate-git-dir={publisher_metadata}",
            publisher,
        )

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--restricted-root",
            restricted,
        )

        self.assertNotEqual(0, result.returncode)
        self.assert_safety_limits(result, "failed")
        self.assertIn(
            "publisher-root Git common metadata overlaps restricted-root",
            result.stdout,
        )

    def test_git_paths_preserve_trailing_space_and_newline(self):
        integration = self.initialize_repository("private-integration \n")
        publisher = self.initialize_repository("publisher \n")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertNotIn(str(integration), result.stdout)
        self.assertNotIn(str(publisher), result.stdout)

    def test_show_paths_escapes_control_characters(self):
        integration = self.initialize_repository("private\nintegration")
        publisher = self.initialize_repository("publisher\troot")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
            "--show-paths",
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertIn(json.dumps(str(integration), ensure_ascii=True), result.stdout)
        self.assertIn(json.dumps(str(publisher), ensure_ascii=True), result.stdout)
        self.assertNotIn(str(integration), result.stdout)
        self.assertNotIn(str(publisher), result.stdout)

    def test_non_utf8_git_metadata_path_remains_redacted(self):
        if os.name != "posix":
            self.skipTest("non-UTF-8 path-byte test requires POSIX paths")
        integration = self.initialize_repository("private-integration")
        publisher = self.scratch / "publisher"
        metadata_bytes = (
            os.fsencode(str(self.scratch))
            + os.fsencode(os.sep)
            + b"publisher-metadata-\xff"
        )
        metadata = Path(os.fsdecode(metadata_bytes))
        try:
            run_git(
                "init",
                "-q",
                f"--separate-git-dir={metadata}",
                publisher,
            )
        except (OSError, subprocess.CalledProcessError, UnicodeError):
            self.skipTest("filesystem or Git rejected a non-UTF-8 path")

        result = self.run_inspector(
            "--integration-root",
            integration,
            "--publisher-root",
            publisher,
        )

        self.assertEqual(0, result.returncode, result.stdout)
        self.assert_safety_limits(result, "verified")
        self.assertNotIn("publisher-metadata", result.stdout)


if __name__ == "__main__":
    unittest.main()
