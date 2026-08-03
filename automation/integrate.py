#!/usr/bin/env python3
"""Screen a landing set for cross-leg collisions before any of it merges.

A pull request's green light is evidence about that branch, not about the trunk it is
about to join. Five individually green branches merged on 2026-08-01 and the trunk went
red immediately, because a check added on one leg met text added on another for the first
time in the merge commit
(`memory/lessons/automation/green-branches-can-merge-to-red.md`). Three verbs close that
gap, Git and the standard library only, so they run on a bare clone with no network:

``plan``    pins the trunk and every leg to a full object id, refuses a leg the trunk has
            moved past, screens every pair for a textual collision, and writes
            ``tmp/integration/<stamp>/manifest.json``.
``build``   replays the set into a detached scratch worktree: one real ``--no-ff`` merge
            per leg, the staged test lane against the merge before it is committed, the
            merge committed, then the reconciler at the merge boundary. It stops at the
            first failing leg and names the commits that bracket the failure.
``verify``  re-pins every ref after the real merges landed, fails on drift, and asserts
            the new trunk's tree equals the tree the build produced.

Two traps are designed around rather than discovered. ``git merge-tree --write-tree``
needs Git 2.38; under an older Git the same words parse as a revision and every pair comes
back "conflicting", so the screen feature-probes the exact command it means to run and
falls back to a real merge in a scratch worktree. And the reconciler binds ``--range`` to
the committed candidate and refuses staged changes, so a merge it is asked about must be
committed first -- while the staged test lane reads ``git diff --cached``, which is empty
once it is. Hence the per-leg order: merge without committing, run the test lane, commit,
run the reconciler.

Exit codes follow the repository's gate contract: 0 clean, 1 a real finding, 2 the screen
could not run at all -- reported as one line, never a traceback.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Every Git call carries this prefix so a `refs/replace/*` entry cannot substitute one
# commit, tree, or blob for the object this screen was asked about -- the same hardening
# the reconciler, the core-scope gate, and the test runner apply.
RAW_GIT = ("git", "--no-replace-objects")
# Scrubbed from every child: they retarget Git at a repository other than the one named
# by `-C`, and this tool is routinely invoked from inside a hook or a test runner that
# sets them.
GIT_LOCATION_VARIABLES = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
)
FULL_OID_CHARACTERS = frozenset("0123456789abcdef")
FULL_OID_LENGTHS = frozenset((40, 64))
SCRATCH_PREFIX = "tmp/integration"
MANIFEST_NAME = "manifest.json"
BUILD_NAME = "build.json"
SCHEMA_VERSION = 1
RECONCILE_SCRIPT = "automation/reconcile/reconcile.py"
RUN_TESTS_SCRIPT = "automation/run_tests.py"
PROBE_CHOICES = ("auto", "merge-tree", "worktree")
# `git merge-tree --write-tree` answers with its exit status: 0 clean, 1 conflicted.
# Anything else is a failure to answer, not an answer.
MERGE_TREE_CLEAN = 0
MERGE_TREE_CONFLICT = 1


class IntegrateError(RuntimeError):
    """The screen could not run at all. Reported as one line, exit 2."""


def say(message):
    # Flushed, because the gates below write straight to this stream from their own
    # processes: a buffered report would print after the output it introduces.
    print("integrate: {0}".format(message), flush=True)


def child_environment():
    environment = dict(os.environ)
    for name in GIT_LOCATION_VARIABLES:
        environment.pop(name, None)
    return environment


def git(*arguments, **options):
    """Run one Git command and return the completed process.

    ``cwd`` names the repository or worktree; ``check`` raises IntegrateError with the
    first line of stderr instead of letting a traceback out.
    """
    cwd = options.pop("cwd", REPO)
    check = options.pop("check", True)
    if options:
        raise TypeError("unexpected options: {0}".format(sorted(options)))
    try:
        result = subprocess.run(
            [*RAW_GIT, *arguments],
            cwd=str(cwd),
            env=child_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as error:
        raise IntegrateError("git is unavailable: {0}".format(error))
    if check and result.returncode:
        raise IntegrateError(
            "git {0} failed: {1}".format(
                " ".join(arguments[:2]), first_line(result.stderr) or "no detail"
            )
        )
    return result


def first_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def is_full_oid(value):
    value = (value or "").strip()
    return (
        len(value) in FULL_OID_LENGTHS
        and not set(value) - FULL_OID_CHARACTERS
    )


def repository_root(candidate):
    """Resolve the repository this run screens, failing closed if it is not one."""
    root = Path(candidate)
    if not root.is_dir():
        raise IntegrateError("{0} is not a directory".format(root))
    result = git("rev-parse", "--show-toplevel", cwd=root, check=False)
    if result.returncode:
        raise IntegrateError(
            "{0} is not a Git repository: {1}".format(
                root, first_line(result.stderr) or "no detail"
            )
        )
    return Path(result.stdout.strip())


def resolve_commit(ref, cwd):
    """Pin one ref to a full commit object id, or None when it does not resolve."""
    result = git(
        "rev-parse", "--verify", "--quiet", "{0}^{{commit}}".format(ref),
        cwd=cwd, check=False,
    )
    oid = result.stdout.strip()
    return oid if not result.returncode and is_full_oid(oid) else None


def pin(ref, cwd):
    oid = resolve_commit(ref, cwd)
    if oid is None:
        raise IntegrateError("{0} does not resolve to a commit".format(ref))
    return oid


def merge_base(first, second, cwd):
    result = git("merge-base", first, second, cwd=cwd, check=False)
    oid = result.stdout.strip()
    return oid if not result.returncode and is_full_oid(oid) else None


def is_ancestor(candidate, descendant, cwd):
    result = git(
        "merge-base", "--is-ancestor", candidate, descendant, cwd=cwd, check=False
    )
    if result.returncode not in (0, 1):
        raise IntegrateError(
            "could not compare {0} with {1}: {2}".format(
                short(candidate), short(descendant),
                first_line(result.stderr) or "no detail",
            )
        )
    return result.returncode == 0


def short(oid):
    return (oid or "")[:12]


def git_version(cwd):
    return first_line(git("--version", cwd=cwd, check=False).stdout) or "unknown"


# --------------------------------------------------------------------------- screening


def merge_tree_available(trunk_oid, cwd):
    """Probe the exact command the screen would use, on a merge that cannot conflict.

    Version strings answer a question about spelling; this answers the question about
    behaviour. Under Git 2.23 `merge-tree` takes three tree-ish arguments, so the probe
    dies with `unknown rev --write-tree` and the screen takes the worktree path instead
    of reporting every pair as a collision.
    """
    probe = git(
        "merge-tree", "--write-tree", "--name-only", "-z", trunk_oid, trunk_oid,
        cwd=cwd, check=False,
    )
    if probe.returncode != MERGE_TREE_CLEAN:
        return False, first_line(probe.stderr) or "merge-tree rejected --write-tree"
    fields = probe.stdout.split("\0")
    if not fields or not is_full_oid(fields[0]):
        return False, "merge-tree --write-tree printed no tree object id"
    return True, "merge-tree --write-tree answered the probe"


def screen_with_merge_tree(first, second, cwd):
    """Return (conflict, paths) for one pair, without touching a working tree."""
    result = git(
        "merge-tree", "--write-tree", "--name-only", "-z", first, second,
        cwd=cwd, check=False,
    )
    if result.returncode == MERGE_TREE_CLEAN:
        return False, ()
    if result.returncode != MERGE_TREE_CONFLICT:
        raise IntegrateError(
            "merge-tree could not merge {0} with {1}: {2}".format(
                short(first), short(second),
                first_line(result.stderr) or "no detail",
            )
        )
    fields = result.stdout.split("\0")
    paths = []
    for field in fields[1:]:
        if field == "":
            break
        paths.append(field)
    return True, tuple(sorted(set(paths)))


def unmerged_paths(cwd):
    result = git("ls-files", "-u", "-z", cwd=cwd)
    paths = set()
    for record in result.stdout.split("\0"):
        if "\t" in record:
            paths.add(record.split("\t", 1)[1])
    return tuple(sorted(paths))


def reset_worktree(worktree, oid):
    """Return a scratch worktree to a known commit, whatever state it was left in."""
    git("merge", "--abort", cwd=worktree, check=False)
    git("reset", "--hard", oid, cwd=worktree)
    git("clean", "-fdq", cwd=worktree, check=False)


def screen_with_worktree(first, second, worktree):
    """Return (conflict, paths) for one pair by really merging it and rolling back."""
    reset_worktree(worktree, first)
    merge = git("merge", "--no-commit", "--no-ff", second, cwd=worktree, check=False)
    paths = unmerged_paths(worktree)
    conflict = bool(merge.returncode)
    if conflict and not paths:
        detail = first_line(merge.stderr) or first_line(merge.stdout)
        if "conflict" not in (detail or "").lower():
            reset_worktree(worktree, first)
            raise IntegrateError(
                "could not merge {0} with {1}: {2}".format(
                    short(first), short(second), detail or "no detail"
                )
            )
    reset_worktree(worktree, first)
    return conflict, paths


def conflict_matrix(nodes, probe, cwd, worktree):
    """Screen every unordered pair among trunk and legs, in a stable order."""
    matrix = []
    for index, (left_ref, left_oid) in enumerate(nodes):
        for right_ref, right_oid in nodes[index + 1:]:
            if probe == "merge-tree":
                conflict, paths = screen_with_merge_tree(left_oid, right_oid, cwd)
            else:
                conflict, paths = screen_with_worktree(left_oid, right_oid, worktree)
            matrix.append({
                "a": left_ref,
                "a_oid": left_oid,
                "b": right_ref,
                "b_oid": right_oid,
                "conflict": conflict,
                "paths": list(paths),
            })
    return matrix


# ---------------------------------------------------------------------------- manifests


def stamped_directory(root):
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    candidate = root / stamp
    suffix = 1
    while candidate.exists():
        candidate = root / "{0}-{1}".format(stamp, suffix)
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def write_record(path, record):
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_record(path, expected):
    try:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise IntegrateError("cannot read {0}: {1}".format(path, error))
    except ValueError as error:
        raise IntegrateError("{0} is not readable JSON: {1}".format(path, error))
    if not isinstance(record, dict) or record.get("version") != SCHEMA_VERSION:
        raise IntegrateError(
            "{0} is not a version {1} {2} record".format(path, SCHEMA_VERSION, expected)
        )
    if record.get("record") != expected:
        raise IntegrateError(
            "{0} is a {1} record, not a {2} one".format(
                path, record.get("record"), expected
            )
        )
    return record


def drifted_pins(pairs, cwd):
    """Return one line per ref that no longer resolves to the object id it was pinned to."""
    drift = []
    for ref, pinned in pairs:
        current = resolve_commit(ref, cwd)
        if current is None:
            drift.append("{0} pinned at {1} no longer resolves".format(ref, short(pinned)))
        elif current != pinned:
            drift.append(
                "{0} moved from {1} to {2} since it was pinned".format(
                    ref, short(pinned), short(current)
                )
            )
    return drift


def manifest_pins(manifest):
    pairs = [(manifest["trunk"]["ref"], manifest["trunk"]["oid"])]
    pairs.extend((leg["ref"], leg["oid"]) for leg in manifest["legs"])
    return pairs


# --------------------------------------------------------------------------------- plan


def command_plan(arguments):
    repository = repository_root(arguments.repo)
    if len(set(arguments.leg)) != len(arguments.leg):
        raise IntegrateError("the same leg was named twice")
    if arguments.trunk in arguments.leg:
        raise IntegrateError(
            "{0} is named as both the trunk and a leg".format(arguments.trunk)
        )

    if arguments.repin:
        previous = read_record(Path(arguments.repin), "plan")
        drift = drifted_pins(manifest_pins(previous), repository)
        for line in drift:
            say("drift: {0}".format(line))
        if drift:
            say(
                "{0} ref(s) drifted since {1}; nothing was screened".format(
                    len(drift), arguments.repin
                )
            )
            return 1
        say("re-pinned {0} ref(s) from {1}, none drifted".format(
            len(manifest_pins(previous)), arguments.repin
        ))

    trunk_oid = pin(arguments.trunk, repository)
    legs = []
    for ref in arguments.leg:
        oid = pin(ref, repository)
        base = merge_base(trunk_oid, oid, repository)
        if base is None:
            raise IntegrateError(
                "{0} and {1} have no merge base".format(arguments.trunk, ref)
            )
        legs.append({
            "ref": ref,
            "oid": oid,
            "merge_base": base,
            "behind_trunk": base != trunk_oid,
        })

    behind = [leg for leg in legs if leg["behind_trunk"]]
    for leg in behind:
        say(
            "drift: {0} branched at {1}, which {2} has moved past ({3})".format(
                leg["ref"], short(leg["merge_base"]), arguments.trunk, short(trunk_oid)
            )
        )
    if behind and not arguments.allow_behind_trunk:
        say(
            "{0} leg(s) are behind {1}; update them, or pass --allow-behind-trunk to "
            "screen them anyway".format(len(behind), arguments.trunk)
        )
        return 1

    nodes = [(arguments.trunk, trunk_oid)]
    nodes.extend((leg["ref"], leg["oid"]) for leg in legs)

    available, detail = merge_tree_available(trunk_oid, repository)
    if arguments.conflict_probe == "merge-tree" and not available:
        raise IntegrateError("--conflict-probe merge-tree was forced but {0}".format(detail))
    if arguments.conflict_probe == "worktree":
        probe = "worktree"
        reason = "forced by --conflict-probe worktree"
    elif available:
        probe = "merge-tree"
        reason = detail
    else:
        probe = "worktree"
        reason = "fell back: {0}".format(detail)
    say("git: {0}".format(git_version(repository)))
    say("conflict probe: {0} ({1})".format(probe, reason))

    directory = (
        Path(arguments.out) if arguments.out
        else stamped_directory(repository / SCRATCH_PREFIX)
    )
    directory.mkdir(parents=True, exist_ok=True)
    worktree = directory / "screen"
    try:
        if probe == "worktree":
            git("worktree", "add", "--detach", str(worktree), trunk_oid, cwd=repository)
        matrix = conflict_matrix(nodes, probe, repository, worktree)
    finally:
        if worktree.exists():
            git("worktree", "remove", "--force", str(worktree), cwd=repository,
                check=False)

    colliding = [entry for entry in matrix if entry["conflict"]]
    manifest = {
        "record": "plan",
        "version": SCHEMA_VERSION,
        "created": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_version(repository),
        "conflict_probe": probe,
        "trunk": {"ref": arguments.trunk, "oid": trunk_oid},
        "legs": legs,
        "matrix": matrix,
        "conflicts": len(colliding),
    }
    path = directory / MANIFEST_NAME
    write_record(path, manifest)

    for entry in matrix:
        state = "COLLIDES" if entry["conflict"] else "clean"
        line = "  {0:8} {1} + {2}".format(state, entry["a"], entry["b"])
        if entry["paths"]:
            line += ": " + ", ".join(entry["paths"])
        print(line, flush=True)
    say("manifest: {0}".format(path))
    say(
        "{0} pair(s) screened, {1} colliding, {2} leg(s) behind trunk".format(
            len(matrix), len(colliding), len(behind)
        )
    )
    return 1 if colliding else 0


# -------------------------------------------------------------------------------- build


def gate_command(workspace, script, *arguments):
    return [sys.executable, str(workspace / script), *arguments]


def run_gate(command, workspace, label, leg_ref):
    """Run one repository gate against the merged tree, inheriting its output."""
    say("{0}: {1}".format(label, " ".join(command[1:])))
    try:
        result = subprocess.run(
            command, cwd=str(workspace), env=child_environment()
        )
    except OSError as error:
        raise IntegrateError(
            "cannot run {0} for {1}: {2}".format(label, leg_ref, error)
        )
    if result.returncode == 2:
        raise IntegrateError(
            "{0} could not run against {1}: it exited 2".format(label, leg_ref)
        )
    return result.returncode


def report_failure(index, total, leg, stage, base, merge_oid, workspace, detail=None):
    say("leg {0} of {1} ({2}) failed at {3}".format(index, total, leg["ref"], stage))
    if detail:
        say("  {0}".format(detail))
    say("  bracket base  {0}  the integration head before this merge".format(base))
    say("  bracket leg   {0}  {1}, the tip merged in".format(leg["oid"], leg["ref"]))
    if merge_oid:
        say("  bracket merge {0}  the merge commit the gate rejected".format(merge_oid))
    else:
        say("  bracket merge (none) the merge was not committed")
    say("  workspace {0}".format(workspace))


def command_build(arguments):
    repository = repository_root(arguments.repo)
    manifest_path = Path(arguments.manifest)
    manifest = read_record(manifest_path, "plan")
    directory = manifest_path.parent

    if manifest["conflicts"]:
        say(
            "the plan found {0} colliding pair(s); resolve them before building".format(
                manifest["conflicts"]
            )
        )
        return 1
    drift = drifted_pins(manifest_pins(manifest), repository)
    for line in drift:
        say("drift: {0}".format(line))
    if drift:
        say("{0} ref(s) drifted since the plan; nothing was merged".format(len(drift)))
        return 1

    workspace = (
        Path(arguments.workspace) if arguments.workspace else directory / "workspace"
    )
    if workspace.exists():
        raise IntegrateError("{0} already exists; name an empty --workspace".format(workspace))
    trunk_oid = manifest["trunk"]["oid"]
    git("worktree", "add", "--detach", str(workspace), trunk_oid, cwd=repository)
    say("workspace: {0} at {1}".format(workspace, short(trunk_oid)))

    hooks = directory / "no-hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    record = {
        "record": "build",
        "version": SCHEMA_VERSION,
        "created": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": MANIFEST_NAME,
        "workspace": str(workspace),
        "trunk": manifest["trunk"],
        "legs": [],
        "head": trunk_oid,
        "suite": None,
    }
    total = len(manifest["legs"])
    head = trunk_oid
    for index, leg in enumerate(manifest["legs"], start=1):
        base = head
        say("leg {0} of {1}: merging {2} ({3}) into {4}".format(
            index, total, leg["ref"], short(leg["oid"]), short(base)
        ))
        merge = git(
            "merge", "--no-commit", "--no-ff", leg["oid"], cwd=workspace, check=False
        )
        entry = {
            "ref": leg["ref"], "oid": leg["oid"], "base": base,
            "merge": None, "status": "failed", "stage": None, "paths": [],
        }
        if merge.returncode:
            paths = unmerged_paths(workspace)
            entry["stage"] = "merge"
            entry["paths"] = list(paths)
            record["legs"].append(entry)
            write_record(directory / BUILD_NAME, record)
            report_failure(
                index, total, leg, "the merge itself", base, None, workspace,
                "conflicted paths: " + (", ".join(paths) or "none reported"),
            )
            return 1

        # The staged test lane reads `git diff --cached`, so it must see the merge
        # before it is committed -- exactly the bytes a pre-commit hook would gate.
        tests = ["--staged"]
        if arguments.jobs:
            tests.extend(["--jobs", str(arguments.jobs)])
        if run_gate(gate_command(workspace, RUN_TESTS_SCRIPT, *tests), workspace,
                    "staged tests", leg["ref"]):
            entry["stage"] = "the staged test lane"
            record["legs"].append(entry)
            write_record(directory / BUILD_NAME, record)
            report_failure(index, total, leg, "the staged test lane", base, None,
                           workspace)
            return 1

        # The reconciler binds --range to the committed candidate and refuses staged
        # changes, so the merge is committed before it is asked about.
        git(
            "-c", "core.hooksPath={0}".format(hooks), "commit",
            "-m", "integrate: merge {0} into the landing set".format(leg["ref"]),
            cwd=workspace,
        )
        merge_oid = pin("HEAD", workspace)
        entry["merge"] = merge_oid
        say("committed {0} (parents {1} {2})".format(
            short(merge_oid), short(base), short(leg["oid"])
        ))
        reconcile = [
            "--check", "--at-transition", "merge",
            "--branch", leg["ref"], "--range", "{0}...{1}".format(base, leg["oid"]),
        ]
        if run_gate(gate_command(workspace, RECONCILE_SCRIPT, *reconcile), workspace,
                    "reconciler", leg["ref"]):
            entry["stage"] = "the reconciler"
            record["legs"].append(entry)
            write_record(directory / BUILD_NAME, record)
            report_failure(index, total, leg, "the reconciler", base, merge_oid,
                           workspace)
            return 1

        entry["status"] = "passed"
        record["legs"].append(entry)
        record["head"] = merge_oid
        head = merge_oid
        write_record(directory / BUILD_NAME, record)

    suite = ["--jobs", str(arguments.jobs)] if arguments.jobs else []
    returncode = run_gate(
        gate_command(workspace, RUN_TESTS_SCRIPT, *suite), workspace,
        "full suite", "the integrated head",
    )
    record["suite"] = {"returncode": returncode}
    write_record(directory / BUILD_NAME, record)
    if returncode:
        say("the full suite failed on the integrated head {0}".format(short(head)))
        say("  workspace {0}".format(workspace))
        return 1
    say("build: {0} leg(s) merged, head {1}".format(total, head))
    say("record: {0}".format(directory / BUILD_NAME))
    say("keep {0} until verify has run; it is what holds the merge commits".format(
        workspace
    ))
    return 0


# ------------------------------------------------------------------------------- verify


def command_verify(arguments):
    repository = repository_root(arguments.repo)
    manifest_path = Path(arguments.manifest)
    manifest = read_record(manifest_path, "plan")
    build = read_record(manifest_path.parent / BUILD_NAME, "build")
    unfinished = [leg["ref"] for leg in build["legs"] if leg["status"] != "passed"]
    if unfinished or not build["suite"] or build["suite"]["returncode"]:
        raise IntegrateError(
            "the build recorded beside this manifest did not finish clean, so there is "
            "nothing to verify against"
        )

    if arguments.fetch:
        say("fetching {0}".format(arguments.fetch))
        git("fetch", arguments.fetch, cwd=repository)

    trunk_ref = arguments.trunk or manifest["trunk"]["ref"]
    new_trunk = resolve_commit(trunk_ref, repository)
    if new_trunk is None:
        raise IntegrateError("{0} does not resolve to a commit".format(trunk_ref))

    integrated = build["head"]
    if resolve_commit(integrated, repository) is None:
        raise IntegrateError(
            "the integrated head {0} is no longer in this repository; the build "
            "workspace holding it was removed before verify ran".format(short(integrated))
        )

    findings = []
    for leg in manifest["legs"]:
        current = resolve_commit(leg["ref"], repository)
        if current == leg["oid"]:
            continue
        if current is None:
            if is_ancestor(leg["oid"], new_trunk, repository):
                say("{0} is gone, and {1} is in {2}".format(
                    leg["ref"], short(leg["oid"]), trunk_ref
                ))
                continue
            findings.append(
                "{0} no longer resolves and {1} is not in {2}".format(
                    leg["ref"], short(leg["oid"]), trunk_ref
                )
            )
        else:
            findings.append(
                "{0} moved from {1} to {2} after it was screened".format(
                    leg["ref"], short(leg["oid"]), short(current)
                )
            )
    for line in findings:
        say("drift: {0}".format(line))
    if findings:
        say("{0} ref(s) drifted; what landed is not what was screened".format(len(findings)))
        return 1

    same = git("diff", "--quiet", new_trunk, integrated, cwd=repository, check=False)
    if same.returncode == 0:
        say("{0} at {1} has the tree the build produced at {2}".format(
            trunk_ref, short(new_trunk), short(integrated)
        ))
        return 0
    if same.returncode != 1:
        raise IntegrateError(
            "could not compare {0} with {1}: {2}".format(
                short(new_trunk), short(integrated),
                first_line(same.stderr) or "no detail",
            )
        )
    names = git("diff", "--name-only", new_trunk, integrated, cwd=repository, check=False)
    say("{0} at {1} differs from the integrated head {2}".format(
        trunk_ref, short(new_trunk), short(integrated)
    ))
    for name in names.stdout.split("\n"):
        if name.strip():
            print("  {0}".format(name.strip()))
    return 1


# ---------------------------------------------------------------------------------- CLI


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--repo", default=str(REPO), metavar="DIR",
        help="repository to screen (default: the one holding this script)",
    )
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    verbs = parser.add_subparsers(dest="verb")
    verbs.required = True

    plan = verbs.add_parser(
        "plan", parents=[common],
        help="pin the set, refuse drift, and screen every pair for a collision",
    )
    plan.add_argument("--trunk", required=True, metavar="REF",
                      help="the branch the set is landing on")
    plan.add_argument("--leg", required=True, action="append", metavar="REF",
                      help="one branch in the landing set; repeat for each")
    plan.add_argument("--repin", metavar="PATH",
                      help="re-pin every ref of an earlier manifest and refuse any drift")
    plan.add_argument("--allow-behind-trunk", action="store_true",
                      help="screen a leg the trunk has moved past instead of refusing it")
    plan.add_argument("--conflict-probe", choices=PROBE_CHOICES, default="auto",
                      help="force the screen's mechanism (default: probe for merge-tree)")
    plan.add_argument("--out", metavar="DIR",
                      help="write the manifest here instead of a stamped scratch directory")
    plan.set_defaults(handler=command_plan)

    build = verbs.add_parser(
        "build", parents=[common],
        help="replay the set into a scratch worktree, gating each merge",
    )
    build.add_argument("--manifest", required=True, metavar="PATH")
    build.add_argument("--workspace", metavar="DIR",
                       help="scratch worktree to build in (default: beside the manifest)")
    build.add_argument("--jobs", type=int, metavar="N",
                       help="passed through to the test runner")
    build.set_defaults(handler=command_build)

    verify = verbs.add_parser(
        "verify", parents=[common],
        help="after the real merges land, prove the trunk is what was screened",
    )
    verify.add_argument("--manifest", required=True, metavar="PATH")
    verify.add_argument("--trunk", metavar="REF",
                        help="re-read the trunk from this ref instead of the manifest's")
    verify.add_argument("--fetch", metavar="REMOTE",
                        help="fetch this remote first; omitted, verify never uses the network")
    verify.set_defaults(handler=command_verify)
    return parser


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    try:
        return arguments.handler(arguments)
    except IntegrateError as error:
        print("integrate: {0}".format(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("integrate: interrupted", file=sys.stderr)
        return 2
    except Exception as error:  # exit 2, never 1: a crash is not a finding
        print(
            "integrate: aborted, {0}: {1}".format(type(error).__name__, error),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
