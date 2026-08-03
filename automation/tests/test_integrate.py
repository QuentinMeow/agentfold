"""Tests for the landing-set screen in `automation/integrate.py`.

Every fixture is a real Git repository carrying stub gates in place of the reconciler
and the test runner, because what has to be proved about `build` is the *order* it
drives them in and the state each one is handed -- a committed two-parent merge for the
reconciler, an uncommitted staged one for the test lane -- not what the real gates
decide. The one thing a stub cannot fake, a real cross-leg failure caught by the real
reconciler, is recorded as command output in the task's verification.

`OLD_GIT_SHIM` stands in for the Git 2.23 that is really on this machine's PATH: it
refuses `merge-tree --write-tree` exactly the way that version does and forwards
everything else. Patching it in is what lets the fallback be exercised on any machine,
including one whose Git is new enough that the fallback would otherwise never run.
"""
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

MODULE_PATH = Path(__file__).resolve().parents[1] / "integrate.py"
SPEC = importlib.util.spec_from_file_location("integrate", MODULE_PATH)
INTEGRATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INTEGRATE)

GATE_LOG = "gate-log.jsonl"
GATE_SCRIPT = "gate-script.json"

# Both stubs answer from a tracked script file and append what they saw to an untracked
# log in the workspace, so a test can assert on the exact state the gate was handed.
GATE_STUB = '''#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys

KIND = {0!r}


def git(*arguments):
    return subprocess.run(
        ["git", *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ).stdout.strip()


log = pathlib.Path("{1}")
previous = [
    json.loads(line) for line in log.read_text().splitlines() if line.strip()
] if log.exists() else []
script = json.loads(pathlib.Path("{2}").read_text())
head = git("rev-parse", "HEAD")
parents = git("rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
staged = [name for name in git("diff", "--cached", "--name-only").splitlines() if name]
clean = subprocess.run(
    ["git", "diff-index", "--cached", "--quiet", "HEAD", "--"]
).returncode == 0
record = {{
    "kind": KIND,
    "argv": sys.argv[1:],
    "head": head,
    "parents": parents,
    "staged": staged,
    "index_clean": clean,
}}
with log.open("a") as handle:
    handle.write(json.dumps(record) + "\\n")
codes = script.get(KIND, [])
index = sum(1 for entry in previous if entry["kind"] == KIND)
sys.exit(codes[index] if index < len(codes) else 0)
'''

OLD_GIT_SHIM = '''#!/usr/bin/env python3
"""Answer `merge-tree --write-tree` the way Git 2.23 does, and forward the rest."""
import os
import sys

arguments = sys.argv[1:]
if "merge-tree" in arguments and "--write-tree" in arguments:
    sys.stderr.write("usage: git merge-tree <base-tree> <branch1> <branch2>\\n")
    sys.exit(129)
os.execvp("git", ["git", *arguments])
'''


def run_git(root, *arguments):
    result = subprocess.run(
        ["git", *arguments],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run_integrate(*arguments):
    """Run one verb in process and return (exit code, everything it printed)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = INTEGRATE.main([str(item) for item in arguments])
    return code, out.getvalue() + err.getvalue()


class IntegrateFixture(unittest.TestCase):
    """One real repository per test: stub gates on the trunk, legs branched off it."""

    def setUp(self):
        holder = tempfile.TemporaryDirectory(prefix="agentfold-integrate-")
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name) / "repository"
        self.root.mkdir()
        run_git(self.root, "init", "--quiet")
        run_git(self.root, "symbolic-ref", "HEAD", "refs/heads/main")
        run_git(self.root, "config", "user.name", "Test")
        run_git(self.root, "config", "user.email", "test@example.invalid")
        (self.root / "automation" / "reconcile").mkdir(parents=True)
        (self.root / "automation" / "run_tests.py").write_text(
            GATE_STUB.format("run_tests", GATE_LOG, GATE_SCRIPT), encoding="utf-8"
        )
        (self.root / "automation" / "reconcile" / "reconcile.py").write_text(
            GATE_STUB.format("reconcile", GATE_LOG, GATE_SCRIPT), encoding="utf-8"
        )
        (self.root / GATE_SCRIPT).write_text("{}\n", encoding="utf-8")
        (self.root / "shared.txt").write_text("one\ntwo\nthree\nfour\nfive\n", encoding="utf-8")
        (self.root / "apart.txt").write_text("apart\n", encoding="utf-8")
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "--quiet", "-m", "base")
        self.out = Path(holder.name) / "out"

    def script_gates(self, **codes):
        """Say what each gate returns, call by call, in the merged tree."""
        (self.root / GATE_SCRIPT).write_text(
            json.dumps(codes) + "\n", encoding="utf-8"
        )
        run_git(self.root, "add", GATE_SCRIPT)
        run_git(self.root, "commit", "--quiet", "-m", "script the gates")

    def leg(self, name, path, text, base="main"):
        run_git(self.root, "checkout", "--quiet", "-B", name, base)
        (self.root / path).write_text(text, encoding="utf-8")
        run_git(self.root, "commit", "--quiet", "-am", name)
        oid = run_git(self.root, "rev-parse", "HEAD")
        run_git(self.root, "checkout", "--quiet", "main")
        return oid

    def gate_log(self, directory=None):
        log = (directory or self.out) / "workspace" / GATE_LOG
        if not log.exists():
            return []
        return [
            json.loads(line) for line in log.read_text().splitlines() if line.strip()
        ]

    def manifest(self, directory=None):
        return json.loads(
            ((directory or self.out) / "manifest.json").read_text(encoding="utf-8")
        )

    def shim_git(self):
        """Return a RAW_GIT prefix that behaves like the Git 2.23 on this PATH."""
        shim = self.root.parent / "old-git.py"
        shim.write_text(OLD_GIT_SHIM, encoding="utf-8")
        os.chmod(str(shim), 0o755)
        return ("python3", str(shim), "--no-replace-objects")


class PlanTests(IntegrateFixture):
    def test_every_ref_is_pinned_to_a_full_object_id(self):
        first = self.leg("legA", "apart.txt", "changed by A\n")
        code, _output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--out", self.out,
        )
        self.assertEqual(0, code)
        manifest = self.manifest()
        trunk = run_git(self.root, "rev-parse", "main")
        self.assertEqual(trunk, manifest["trunk"]["oid"])
        self.assertEqual(first, manifest["legs"][0]["oid"])
        self.assertTrue(INTEGRATE.is_full_oid(manifest["legs"][0]["merge_base"]))

    def test_a_leg_that_moved_since_it_was_pinned_is_refused(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--out", self.out,
        )
        moved = self.leg("legA", "apart.txt", "changed again by A\n")
        code, output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--repin", self.out / "manifest.json", "--out", self.out.parent / "second",
        )
        self.assertEqual(1, code)
        self.assertIn("legA moved from", output)
        self.assertIn(moved[:12], output)
        self.assertFalse((self.out.parent / "second" / "manifest.json").exists())

    def test_a_leg_the_trunk_has_moved_past_is_refused_until_allowed(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        run_git(self.root, "commit", "--quiet", "--allow-empty", "-m", "trunk moves on")
        code, output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--out", self.out,
        )
        self.assertEqual(1, code)
        self.assertIn("main has moved past", output)
        allowed, _output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--allow-behind-trunk", "--out", self.out.parent / "allowed",
        )
        self.assertEqual(0, allowed)
        manifest = self.manifest(self.out.parent / "allowed")
        self.assertTrue(manifest["legs"][0]["behind_trunk"])

    def test_a_colliding_pair_is_reported_with_the_path_it_collides_on(self):
        self.leg("legA", "shared.txt", "one\nAAA\nthree\nfour\nfive\n")
        self.leg("legB", "shared.txt", "one\nBBB\nthree\nfour\nfive\n")
        code, output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--leg", "legB", "--out", self.out,
        )
        self.assertEqual(1, code)
        self.assertIn("COLLIDES legA + legB: shared.txt", output)
        colliding = [
            entry for entry in self.manifest()["matrix"] if entry["conflict"]
        ]
        self.assertEqual(1, len(colliding))
        self.assertEqual(["shared.txt"], colliding[0]["paths"])

    def test_the_same_matrix_comes_back_without_merge_tree(self):
        """The acceptance criterion, forced rather than hoped for.

        The shim refuses `merge-tree --write-tree` the way Git 2.23 does, so the
        second run screens by really merging in a scratch worktree. Both matrices
        must be the same object, pair for pair and path for path.
        """
        self.leg("legA", "shared.txt", "one\nAAA\nthree\nfour\nfive\n")
        self.leg("legB", "shared.txt", "one\nBBB\nthree\nfour\nfive\n")
        self.leg("legC", "apart.txt", "changed by C\n")
        legs = ["--leg", "legA", "--leg", "legB", "--leg", "legC"]
        native, _output = run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", *legs,
            "--out", self.out,
        )
        with mock.patch.object(INTEGRATE, "RAW_GIT", self.shim_git()):
            fallback, output = run_integrate(
                "plan", "--repo", self.root, "--trunk", "main", *legs,
                "--out", self.out.parent / "fallback",
            )
        self.assertEqual(native, fallback)
        self.assertIn("conflict probe: worktree (fell back", output)
        self.assertEqual("worktree", self.manifest(self.out.parent / "fallback")["conflict_probe"])
        self.assertEqual(
            self.manifest()["matrix"],
            self.manifest(self.out.parent / "fallback")["matrix"],
        )

    def test_forcing_merge_tree_without_the_capability_cannot_run(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        with mock.patch.object(INTEGRATE, "RAW_GIT", self.shim_git()):
            code, output = run_integrate(
                "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
                "--conflict-probe", "merge-tree", "--out", self.out,
            )
        self.assertEqual(2, code)
        self.assertIn("--conflict-probe merge-tree was forced but", output)
        self.assertEqual(1, len([line for line in output.splitlines() if line.strip()]))

    def test_a_directory_that_is_not_a_repository_cannot_run(self):
        code, output = run_integrate(
            "plan", "--repo", self.root.parent, "--trunk", "main", "--leg", "legA",
            "--out", self.out,
        )
        self.assertEqual(2, code)
        self.assertIn("is not a Git repository", output)


class BuildTests(IntegrateFixture):
    def plan_set(self, *legs, **options):
        arguments = ["plan", "--repo", self.root, "--trunk", "main"]
        for leg in legs:
            arguments.extend(["--leg", leg])
        arguments.extend(["--out", self.out])
        code, output = run_integrate(*arguments)
        if options.get("expect", 0) is not None:
            self.assertEqual(options.get("expect", 0), code, output)
        return self.out / "manifest.json"

    def test_each_merge_is_committed_before_the_reconciler_is_asked_about_it(self):
        """Trap one: the reconciler binds --range to the committed candidate.

        It reads the captured HEAD, which during a `--no-commit` merge is still the
        pre-merge tip, and it refuses a candidate carrying staged changes. So by the
        time it runs, HEAD must be the two-parent merge and the index must be clean.
        """
        first = self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.plan_set("legA")
        code, _output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(0, code)
        reconciles = [entry for entry in self.gate_log() if entry["kind"] == "reconcile"]
        self.assertEqual(1, len(reconciles))
        entry = reconciles[0]
        trunk = self.manifest()["trunk"]["oid"]
        self.assertEqual([trunk, first], entry["parents"])
        self.assertTrue(entry["index_clean"])
        self.assertEqual(
            ["--check", "--at-transition", "merge", "--branch", "legA",
             "--range", "{0}...{1}".format(trunk, first)],
            entry["argv"],
        )

    def test_the_staged_lane_sees_the_merge_before_it_is_committed(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.plan_set("legA")
        code, _output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(0, code)
        staged = [
            entry for entry in self.gate_log()
            if entry["kind"] == "run_tests" and entry["argv"] == ["--staged"]
        ]
        self.assertEqual(1, len(staged))
        self.assertEqual(["apart.txt"], staged[0]["staged"])
        self.assertFalse(staged[0]["index_clean"])
        self.assertEqual(self.manifest()["trunk"]["oid"], staged[0]["head"])

    def test_the_full_suite_runs_once_after_every_leg(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        self.leg("legC", "shared.txt", "one\ntwo\nthree\nfour\nFIVE\n")
        manifest = self.plan_set("legA", "legC")
        code, _output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(0, code)
        kinds = [
            (entry["kind"], tuple(entry["argv"][:1])) for entry in self.gate_log()
        ]
        self.assertEqual(
            [("run_tests", ("--staged",)), ("reconcile", ("--check",)),
             ("run_tests", ("--staged",)), ("reconcile", ("--check",)),
             ("run_tests", ())],
            kinds,
        )

    def test_the_first_failing_leg_stops_the_build_and_names_its_bracket(self):
        self.script_gates(reconcile=[0, 1])
        self.leg("legA", "apart.txt", "changed by A\n")
        second = self.leg("legB", "shared.txt", "one\ntwo\nthree\nfour\nBBB\n")
        self.leg("legC", "shared.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        manifest = self.plan_set("legA", "legB", "legC")
        code, output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(1, code)
        self.assertIn("leg 2 of 3 (legB) failed at the reconciler", output)
        record = json.loads((self.out / "build.json").read_text(encoding="utf-8"))
        failing = record["legs"][-1]
        self.assertEqual("legB", failing["ref"])
        self.assertEqual("failed", failing["status"])
        # The bracket is printed as full object ids: the integration head before
        # this merge, the leg tip merged into it, and the merge commit itself.
        self.assertIn("bracket base  " + record["legs"][0]["merge"], output)
        self.assertIn("bracket leg   " + second, output)
        self.assertIn("bracket merge " + failing["merge"], output)
        self.assertEqual(second, failing["oid"])
        self.assertEqual(
            2, len([e for e in self.gate_log() if e["kind"] == "reconcile"]),
            "the third leg must not have been merged",
        )

    def test_a_conflicting_merge_stops_the_build_before_any_gate_runs(self):
        self.leg("legA", "shared.txt", "one\nAAA\nthree\nfour\nfive\n")
        self.leg("legB", "shared.txt", "one\nBBB\nthree\nfour\nfive\n")
        # Screened separately so the manifest carries no collision of its own.
        first = self.plan_set("legA")
        manifest = json.loads(first.read_text(encoding="utf-8"))
        manifest["legs"].append({
            "ref": "legB",
            "oid": run_git(self.root, "rev-parse", "legB"),
            "merge_base": manifest["legs"][0]["merge_base"],
            "behind_trunk": False,
        })
        first.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        code, output = run_integrate("build", "--repo", self.root, "--manifest", first)
        self.assertEqual(1, code)
        self.assertIn("failed at the merge itself", output)
        self.assertIn("conflicted paths: shared.txt", output)
        self.assertIn("bracket merge (none)", output)

    def test_a_manifest_whose_plan_found_a_collision_is_refused(self):
        self.leg("legA", "shared.txt", "one\nAAA\nthree\nfour\nfive\n")
        self.leg("legB", "shared.txt", "one\nBBB\nthree\nfour\nfive\n")
        manifest = self.plan_set("legA", "legB", expect=1)
        code, output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(1, code)
        self.assertIn("resolve them before building", output)
        self.assertFalse((self.out / "workspace").exists())

    def test_a_ref_that_moved_since_the_plan_is_refused(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.plan_set("legA")
        self.leg("legA", "apart.txt", "changed again by A\n")
        code, output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(1, code)
        self.assertIn("legA moved from", output)
        self.assertFalse((self.out / "workspace").exists())

    def test_a_gate_that_cannot_run_is_not_reported_as_a_finding(self):
        self.script_gates(reconcile=[2])
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.plan_set("legA")
        code, output = run_integrate("build", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(2, code)
        self.assertIn("could not run against legA", output)

    def test_an_unreadable_manifest_cannot_run(self):
        broken = self.out
        broken.mkdir(parents=True)
        (broken / "manifest.json").write_text("{not json", encoding="utf-8")
        code, output = run_integrate(
            "build", "--repo", self.root, "--manifest", broken / "manifest.json"
        )
        self.assertEqual(2, code)
        self.assertIn("is not readable JSON", output)


class VerifyTests(IntegrateFixture):
    def landed_build(self, *legs):
        arguments = ["plan", "--repo", self.root, "--trunk", "main"]
        for leg in legs:
            arguments.extend(["--leg", leg])
        arguments.extend(["--out", self.out])
        self.assertEqual(0, run_integrate(*arguments)[0])
        manifest = self.out / "manifest.json"
        self.assertEqual(
            0, run_integrate("build", "--repo", self.root, "--manifest", manifest)[0]
        )
        return manifest

    def land(self, *legs):
        for leg in legs:
            run_git(self.root, "merge", "--quiet", "--no-ff", "-m",
                    "Merge " + leg, leg)

    def test_the_trunk_that_matches_the_build_passes(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        self.leg("legC", "shared.txt", "one\ntwo\nthree\nfour\nFIVE\n")
        manifest = self.landed_build("legA", "legC")
        self.land("legA", "legC")
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(0, code)
        self.assertIn("has the tree the build produced", output)

    def test_a_ref_that_moved_after_the_screen_fails(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.landed_build("legA")
        self.land("legA")
        self.leg("legA", "apart.txt", "changed again by A\n", base="legA")
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(1, code)
        self.assertIn("legA moved from", output)
        self.assertIn("what landed is not what was screened", output)

    def test_a_trunk_carrying_something_else_fails_and_names_the_paths(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.landed_build("legA")
        self.land("legA")
        (self.root / "shared.txt").write_text("edited on the trunk\n", encoding="utf-8")
        run_git(self.root, "commit", "--quiet", "-am", "someone else landed too")
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(1, code)
        self.assertIn("differs from the integrated head", output)
        self.assertIn("shared.txt", output)

    def test_a_deleted_leg_whose_commit_landed_still_passes(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.landed_build("legA")
        self.land("legA")
        run_git(self.root, "branch", "-D", "legA")
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(0, code)
        self.assertIn("legA is gone", output)

    def test_an_unfinished_build_cannot_be_verified(self):
        self.script_gates(reconcile=[1])
        self.leg("legA", "apart.txt", "changed by A\n")
        self.assertEqual(0, run_integrate(
            "plan", "--repo", self.root, "--trunk", "main", "--leg", "legA",
            "--out", self.out,
        )[0])
        manifest = self.out / "manifest.json"
        self.assertEqual(
            1, run_integrate("build", "--repo", self.root, "--manifest", manifest)[0]
        )
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(2, code)
        self.assertIn("did not finish clean", output)

    def test_an_integrated_head_that_is_gone_cannot_be_verified(self):
        self.leg("legA", "apart.txt", "changed by A\n")
        manifest = self.landed_build("legA")
        record_path = self.out / "build.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["head"] = "0" * 40
        record_path.write_text(json.dumps(record), encoding="utf-8")
        code, output = run_integrate("verify", "--repo", self.root, "--manifest", manifest)
        self.assertEqual(2, code)
        self.assertIn("no longer in this repository", output)


if __name__ == "__main__":
    unittest.main()
