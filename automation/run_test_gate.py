#!/usr/bin/env python3
"""Run budgeted routine or complete final repository test gates."""

import argparse
import errno
import json
import os
import platform
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

PROCESS_STARTED = time.monotonic()
REPO = Path(__file__).resolve().parents[1]
AUTOMATION = Path(__file__).resolve().parent
sys.path.insert(0, str(AUTOMATION))

import run_tests  # noqa: E402
import test_manifest  # noqa: E402

try:
    import test_gate_config  # noqa: E402
except ImportError:  # pragma: no cover - integration supplies the policy module
    test_gate_config = None

try:
    import file_test_budget_task  # noqa: E402
except ImportError:  # pragma: no cover - the report remains complete without mutation
    file_test_budget_task = None


REPORT_SCHEMA = "agentfold.test-gate-report/v1"
RECEIPT_SCHEMA = "agentfold.test-component-receipt/v1"
CANONICAL_CONFIG = Path("agentfold.toml")
LOCAL_STATE_DIRECTORIES = frozenset(
    (Path("tmp/test-gate-receipts"), Path("tmp/test-gate-reports"))
)
OUTCOME_EXIT = {
    "pass": 0,
    "deferred": 0,
    "not-run": 0,
    "blocked-failed": 1,
    "blocked-incomplete": 1,
    "invalid": 2,
    "error": 2,
}


class GateError(RuntimeError):
    """An operational gate failure that must not be mistaken for a test failure."""


@dataclass
class ComponentResult:
    component_id: str
    outcome: str
    evidence: str
    duration_seconds: float
    command: tuple
    detail: str = ""

    def as_dict(self):
        value = asdict(self)
        value["command"] = list(self.command)
        value["duration_seconds"] = round(self.duration_seconds, 6)
        return value


def parse_arguments(arguments):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=("routine", "final"))
    parser.add_argument(
        "--staged",
        action="store_true",
        help="bind routine or explicit final prewarming to an immutable Git index copy",
    )
    final_trigger = parser.add_mutually_exclusive_group()
    final_trigger.add_argument(
        "--explicit", action="store_true", help="explicitly request the final gate"
    )
    final_trigger.add_argument(
        "--at-transition", metavar="NAME", help="run at a named final transition"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CANONICAL_CONFIG,
        help="canonical repository policy path (agentfold.toml)",
    )
    parser.add_argument("--base-revision", help="immutable final range base")
    parser.add_argument("--head-revision", help="pull-request head bound to a merge candidate")
    parser.add_argument("--candidate-revision", help="immutable final range candidate")
    parser.add_argument("--branch", help="task branch bound to final admission")
    parser.add_argument("--displaced-tip", help="prior tip for synchronize admission")
    parser.add_argument(
        "--provider-hard",
        action="store_true",
        help="mark a trusted provider pull-request hard-boundary invocation",
    )
    options = parser.parse_args(arguments)
    if options.gate == "routine" and not options.staged:
        parser.error("the routine gate requires --staged")
    if options.gate == "routine" and (
        options.explicit or options.at_transition or options.provider_hard
    ):
        parser.error("final trigger options apply only to the final gate")
    if options.gate == "routine" and any(
        (
            options.base_revision,
            options.head_revision,
            options.candidate_revision,
            options.branch,
            options.displaced_tip,
        )
    ):
        parser.error("revision range options apply only to the final gate")
    if options.gate == "final" and options.staged and not options.explicit:
        parser.error("a staged final gate requires --explicit")
    if options.gate == "final" and options.staged and any(
        (
            options.at_transition,
            options.base_revision,
            options.head_revision,
            options.candidate_revision,
            options.branch,
            options.displaced_tip,
        )
    ):
        parser.error("a staged final gate cannot name a revision range or transition")
    if options.provider_hard and (
        options.gate != "final"
        or options.explicit
        or options.staged
        or options.at_transition != "pull-request"
    ):
        parser.error(
            "--provider-hard requires final --at-transition pull-request and an exact range"
        )
    if options.at_transition and not (
        options.base_revision
        and options.head_revision
        and options.candidate_revision
        and options.branch
    ):
        parser.error(
            "named final transitions require --base-revision, --head-revision, "
            "--candidate-revision, and --branch"
        )
    if options.config != CANONICAL_CONFIG:
        parser.error("--config cannot select a non-canonical policy; use agentfold.toml")
    return options


def _policy_digest(policy):
    canonical = getattr(test_gate_config, "canonical_policy_digest", None)
    if canonical is not None:
        return canonical(policy)
    digest = getattr(policy, "digest", None)
    if not digest:
        raise GateError("loaded test policy has no canonical digest")
    return digest


def load_candidate_policy(candidate_root, relative_config, scratch_root, base_revision):
    """Load a downgrade-resistant base/candidate policy union when possible."""
    if test_gate_config is None:
        raise GateError("automation/test_gate_config.py is unavailable")
    if Path(relative_config) != CANONICAL_CONFIG:
        raise GateError("the test-gate policy must be loaded from canonical agentfold.toml")
    candidate_path = candidate_root / CANONICAL_CONFIG
    if not candidate_path.is_file() or candidate_path.is_symlink():
        raise GateError(f"candidate policy is unavailable: {relative_config}")
    base_path = scratch_root / "base-agentfold.toml"
    base = subprocess.run(
        ["git", "show", f"{base_revision}:{CANONICAL_CONFIG.as_posix()}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if base.returncode != 0:
        presence = subprocess.run(
            ["git", "ls-tree", "-z", "--name-only", base_revision, "--", CANONICAL_CONFIG.as_posix()],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if presence.returncode != 0 or presence.stdout:
            raise GateError("trusted base policy could not be read at canonical agentfold.toml")
        policy = test_gate_config.load_policy(candidate_path)
        return policy, _policy_digest(policy)
    base_path.write_bytes(base.stdout)
    union_loader = getattr(test_gate_config, "load_policy_union", None)
    if union_loader is None:
        raise GateError("downgrade-resistant policy union support is unavailable")
    policy = union_loader(base_path, candidate_path)
    return policy, _policy_digest(policy)


def _resolve_commit(revision):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    oid = result.stdout.strip()
    if result.returncode or not oid:
        raise GateError(f"final revision is unavailable: {revision}")
    return oid


def capture_revision_candidate(options, scratch_root):
    """Materialize an immutable committed range for final verification."""
    if bool(options.base_revision) != bool(options.candidate_revision):
        raise GateError("final --base-revision and --candidate-revision are required together")
    if not options.base_revision:
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if status.returncode or status.stdout:
            raise GateError(
                "explicit final without a revision range requires a clean checkout; "
                "commit the candidate or pass --base-revision and --candidate-revision"
            )
    base_revision = _resolve_commit(options.base_revision or "HEAD^")
    candidate_revision = _resolve_commit(options.candidate_revision or "HEAD")
    head_revision = (
        _resolve_commit(options.head_revision) if options.head_revision else None
    )
    if head_revision is not None:
        parents = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", candidate_revision],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        parent_oids = tuple(parents.stdout.strip().split()[1:])
        if parents.returncode or parent_oids != (base_revision, head_revision):
            raise GateError(
                "final pull-request candidate is not the declared base/head synthetic merge"
            )
    frozen_index = scratch_root / "candidate.index"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(frozen_index)
    result = subprocess.run(
        ["git", "read-tree", candidate_revision],
        cwd=REPO,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise GateError("could not create the immutable final candidate index")
    candidate = test_manifest.staged_candidate(
        REPO,
        frozen_index,
        base_revision=base_revision,
        candidate_revision=candidate_revision,
        kind="revision-range",
    )
    candidate_root = scratch_root / "candidate"
    tested_view = test_manifest.materialize_staged_candidate(
        REPO, frozen_index, candidate_root
    )

    def unchanged():
        return (
            _resolve_commit(base_revision) == base_revision
            and _resolve_commit(candidate_revision) == candidate_revision
        )

    return candidate, tested_view, candidate_root, unchanged


def capture_candidate(options, scratch_root):
    """Capture one immutable candidate and return its manifest, view, and drift check."""
    if options.gate == "final" and not options.staged:
        return capture_revision_candidate(options, scratch_root)
    candidate_root = scratch_root / "candidate"
    if options.staged:
        frozen_index = scratch_root / "candidate.index"
        test_manifest.copy_staged_index(REPO, frozen_index)
        candidate = test_manifest.staged_candidate(REPO, frozen_index)
        tested_view = test_manifest.materialize_staged_candidate(
            REPO, frozen_index, candidate_root
        )

        def unchanged():
            return test_manifest.live_index_matches(
                REPO, candidate.source_fingerprint, candidate.base_revision
            )

        return candidate, tested_view, candidate_root, unchanged

    raise GateError("routine candidate must be staged")


def classify_candidate(paths, policy):
    classifier = getattr(test_gate_config, "classify_paths", None)
    if classifier is None:
        raise GateError("test policy module does not expose classify_paths")
    return classifier(paths, policy)


def admission_commands(options, candidate, candidate_root=REPO):
    """Bind admission and reconciliation to the same captured candidate shape."""
    automation = AUTOMATION if options.provider_hard else Path(candidate_root) / "automation"
    if candidate.kind == "staged-index":
        return (
            (
                "core-scope",
                [sys.executable, str(automation / "check_core_scope.py"), "--staged"],
            ),
            (
                "reconcile",
                [sys.executable, str(automation / "reconcile/reconcile.py"), "--check"],
            ),
        )
    branch = options.branch
    if not branch:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    if not branch:
        raise GateError("final range admission requires --branch in a detached checkout")
    change_range = f"{candidate.base_revision}...{candidate.candidate_revision}"
    core = [
        sys.executable,
        str(automation / "check_core_scope.py"),
        "--range",
        change_range,
        "--branch",
        branch,
    ]
    reconcile = [
        sys.executable,
        str(automation / "reconcile/reconcile.py"),
        "--check",
        "--branch",
        branch,
        "--range",
        change_range,
    ]
    if options.at_transition:
        transition = (
            "merge" if options.at_transition == "pull-request" else options.at_transition
        )
        reconcile.extend(("--at-transition", transition))
    if options.displaced_tip:
        reconcile.extend(("--displaced-tip", _resolve_commit(options.displaced_tip)))
    return (("core-scope", core), ("reconcile", reconcile))


def candidate_git_environment(candidate_root, frozen_index):
    """Expose original history to checks while freezing all candidate-visible bytes."""
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    git_directory = result.stdout.strip()
    if result.returncode or not git_directory:
        raise GateError("could not resolve repository metadata for candidate checks")
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_DIR": git_directory,
        "GIT_WORK_TREE": str(Path(candidate_root).resolve()),
        "GIT_INDEX_FILE": str(Path(frozen_index).resolve()),
    }


def _all_relative_tests(candidate_root):
    return tuple(
        test.relative_to(candidate_root).as_posix()
        for test in run_tests.repository_test_files(candidate_root)
    )


def routine_test_manifest(changed_paths, all_tests):
    """Map explicit known ownership to a small routine set; defer the remainder."""
    all_set = set(all_tests)
    selected = set()
    service_dependencies = {
        "quote-api": ("quote-api", "quote-cli"),
        "quote-cli": ("quote-cli",),
    }
    for changed in changed_paths:
        parts = Path(changed).parts
        if len(parts) >= 2 and parts[0] == "services":
            for service in service_dependencies.get(parts[1], ()):
                prefix = f"services/{service}/tests/"
                selected.update(test for test in all_set if test.startswith(prefix))
        elif len(parts) == 2 and parts[0] == "automation" and parts[1].endswith(".py"):
            stem = Path(parts[1]).stem
            direct = f"automation/tests/test_{stem}.py"
            if direct in all_set:
                selected.add(direct)
        elif len(parts) >= 3 and parts[:2] == ("automation", "tests"):
            candidate = "/".join(parts)
            if candidate in all_set:
                selected.add(candidate)
    selected = tuple(sorted(selected))
    return selected, tuple(sorted(all_set.difference(selected)))


def _budget_for(gate, policy):
    if gate == "routine":
        return policy.routine
    final = getattr(policy, "final", None)
    if final is not None:
        return getattr(final, "budget", final)
    return test_gate_config.GateBudget(
        policy.final_target_seconds, policy.final_maximum_seconds
    )


def _final_disposition(options, policy):
    if options.gate != "final":
        return None
    final = getattr(policy, "final", None)
    if final is None:
        hard_triggers = tuple(policy.hard_triggers)
        mode = "hard" if hard_triggers else "manual"
        trigger = hard_triggers[0] if len(hard_triggers) == 1 else None
    else:
        mode = final.mode
        trigger = final.trigger
    if options.explicit:
        return None
    if options.at_transition:
        if mode == "manual":
            return (
                "not-run",
                "final mode is manual; use --explicit to run complete verification",
            )
        if mode == "hard" and options.at_transition not in (
            tuple(policy.hard_triggers) if final is None else (trigger,)
        ):
            return (
                "not-run",
                "final hard gate does not bind this transition",
            )
        return None
    return (
        "not-run",
        "final verification requires --explicit or --at-transition NAME",
    )


def _descendant_pids(root_pid, deadline):
    """Snapshot direct and indirect descendants before the root can reparent them."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return ()
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=min(0.1, remaining),
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    children = {}
    for line in result.stdout.splitlines():
        try:
            pid, parent = (int(value) for value in line.split())
        except (TypeError, ValueError):
            continue
        children.setdefault(parent, []).append(pid)
    descendants = set()
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        for child in children.get(parent, ()):
            if child not in descendants:
                descendants.add(child)
                pending.append(child)
    return tuple(sorted(descendants, reverse=True))


PROCESS_TOKEN_ENV = "AGENTFOLD_GATE_PROCESS_TOKEN"
SAFE_ENVIRONMENT_NAMES = frozenset(
    (
        "CI",
        "GITHUB_ACTIONS",
        "LANG",
        "LC_ALL",
        "PATH",
        "RUNNER_ARCH",
        "RUNNER_OS",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
    )
)
INTERNAL_COMPONENT_ENVIRONMENT_NAMES = frozenset(
    (
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
    )
)


def safe_process_environment(source=None):
    """Pass only non-secret execution context into candidate-controlled components."""
    source = os.environ if source is None else source
    return {
        name: value
        for name, value in source.items()
        if name in SAFE_ENVIRONMENT_NAMES or name.startswith("PYTHON")
    }


def _owned_process_pids(token, deadline):
    """Find same-user processes carrying the gate's unguessable ownership token."""
    if time.monotonic() >= deadline:
        return ()
    marker = f"{PROCESS_TOKEN_ENV}={token}".encode("ascii")
    proc = Path("/proc")
    owned = set()
    if proc.is_dir():
        for entry in proc.iterdir():
            if not entry.name.isdigit() or time.monotonic() >= deadline:
                continue
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                environment = (entry / "environ").read_bytes().split(b"\0")
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
                continue
            if marker in environment:
                owned.add(int(entry.name))
        return tuple(sorted(owned, reverse=True))
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return ()
    try:
        result = subprocess.run(
            ["ps", "eww", "-axo", "pid=,uid=,command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=min(0.15, remaining),
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    for line in result.stdout.splitlines():
        fields = line.split(None, 2)
        if len(fields) != 3:
            continue
        try:
            pid, uid = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        if uid == os.getuid() and marker in fields[2].split():
            owned.add(pid)
    return tuple(sorted(owned, reverse=True))


def process_identity_discovery_available():
    if Path("/proc").is_dir():
        return True
    try:
        result = subprocess.run(
            ["ps", "eww", "-p", str(os.getpid()), "-o", "command="],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=0.2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _signal_processes(process, owned, process_signal):
    try:
        os.killpg(process.pid, process_signal)
    except ProcessLookupError:
        pass
    try:
        os.kill(process.pid, process_signal)
    except ProcessLookupError:
        pass
    for pid in owned:
        if pid == os.getpid():
            continue
        try:
            os.kill(pid, process_signal)
        except ProcessLookupError:
            pass


def _kill_process_tree(process, cleanup_deadline, token):
    owned = set(_descendant_pids(process.pid, cleanup_deadline))
    owned.update(_owned_process_pids(token, cleanup_deadline))
    _signal_processes(process, owned, signal.SIGTERM)
    remaining = cleanup_deadline - time.monotonic()
    if remaining > 0:
        try:
            process.wait(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            pass
    while time.monotonic() < cleanup_deadline:
        owned.update(_owned_process_pids(token, cleanup_deadline))
        _signal_processes(process, owned, signal.SIGKILL)
        live_owned = set(_owned_process_pids(token, cleanup_deadline))
        if process.poll() is not None and not live_owned:
            break
        remaining = cleanup_deadline - time.monotonic()
        if remaining > 0:
            try:
                process.wait(timeout=min(0.02, remaining))
            except subprocess.TimeoutExpired:
                pass
    if process.poll() is None:
        _signal_processes(process, (), signal.SIGKILL)
    return tuple(sorted(owned, reverse=True))


def _read_component_output(stream):
    stream.flush()
    stream.seek(0)
    return stream.read().decode("utf-8", "replace").strip()


def run_component(
    component_id,
    command,
    remaining_seconds,
    cwd=REPO,
    cleanup_deadline=None,
    environment=None,
    internal_environment=None,
):
    if remaining_seconds <= 0:
        return ComponentResult(component_id, "incomplete", "none", 0.0, tuple(command))
    started = time.monotonic()
    run_deadline = started + remaining_seconds
    cleanup_deadline = (
        run_deadline + min(0.5, max(0.1, remaining_seconds * 0.2))
        if cleanup_deadline is None
        else cleanup_deadline
    )
    token = secrets.token_hex(32)
    component_environment = safe_process_environment(environment)
    for name, value in (internal_environment or {}).items():
        if name not in INTERNAL_COMPONENT_ENVIRONMENT_NAMES:
            raise GateError(f"unsupported internal component environment name: {name}")
        component_environment[name] = value
    component_environment[PROCESS_TOKEN_ENV] = token
    with tempfile.TemporaryFile(mode="w+b") as output_stream:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=output_stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=component_environment,
        )
        try:
            process.wait(timeout=max(0.0, run_deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            descendants = _kill_process_tree(process, cleanup_deadline, token)
            captured = _read_component_output(output_stream)
            cleanup = "terminated component process group"
            if descendants:
                cleanup += f" and {len(descendants)} gate-owned descendant(s)"
            output = "component exceeded its reserved execution interval; " + cleanup
            if captured:
                output += "\n" + captured
            return ComponentResult(
                component_id,
                "incomplete",
                "executed",
                time.monotonic() - started,
                tuple(command),
                output,
            )
        output = _read_component_output(output_stream)
        outcome = "pass" if process.returncode == 0 else "failed"
        return ComponentResult(
            component_id,
            outcome,
            "executed",
            time.monotonic() - started,
            tuple(command),
            output,
        )


def missing_required_checks(required_check_ids, components):
    passed = {
        component.component_id
        for component in components
        if component.outcome == "pass"
    }
    return tuple(sorted(set(required_check_ids).difference(passed)))


def apply_gate_outcome(
    report,
    gate_id,
    components,
    selected,
    deferred,
    critical,
    required_check_ids,
    candidate_stable,
):
    """Resolve functional, completeness, and drift evidence without weakening safety."""
    failed = next(
        (component for component in components if component.outcome == "failed"), None
    )
    incomplete = next(
        (component for component in components if component.outcome == "incomplete"),
        None,
    )
    missing_required = missing_required_checks(required_check_ids, components)
    if missing_required:
        report["incomplete"] = list(missing_required)
    if not candidate_stable:
        report["outcome"] = "blocked-incomplete"
        report["reason"] = "candidate source drifted during the gate"
        report["incomplete"] = sorted(
            set(report["incomplete"]).union(("candidate-stability",))
        )
    elif failed is not None:
        report["outcome"] = "blocked-failed"
        report["reason"] = f"{failed.component_id} failed"
    elif missing_required:
        report["outcome"] = "blocked-incomplete"
        report["reason"] = (
            "required critical checks did not complete successfully: "
            + ", ".join(missing_required)
        )
    elif incomplete is not None:
        report["incomplete"] = sorted(
            set(report["incomplete"]).union((incomplete.component_id,))
        )
        if (
            critical
            or gate_id == "final"
            or not incomplete.component_id.startswith("repository-tests/")
        ):
            report["outcome"] = "blocked-incomplete"
            report["reason"] = (
                f"{incomplete.component_id} did not complete before the maximum"
            )
        else:
            report["deferred"] = sorted(set(report["deferred"]).union(selected))
            report["outcome"] = "deferred"
            report["reason"] = (
                f"reversible remainder deferred after {incomplete.component_id}"
            )
    elif deferred:
        if critical:
            report["outcome"] = "blocked-incomplete"
            report["reason"] = "critical candidate retained deferred coverage"
        else:
            report["outcome"] = "deferred"
            report["reason"] = (
                "selected checks passed; reversible coverage remains for final"
            )
    else:
        report["outcome"] = "pass"
        report["reason"] = "every required check passed"


def runner_revision(candidate_root=REPO):
    automation = Path(candidate_root) / "automation"
    return test_manifest.canonical_digest(
        {
            path.name: test_manifest.file_digest(path)
            for path in (
                automation / "run_test_gate.py",
                automation / "run_tests.py",
                automation / "test_manifest.py",
            )
        }
    )


def environment_identity():
    git = subprocess.run(
        ["git", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "git_version": git.stdout.strip() if git.returncode == 0 else "unavailable",
    }


def receipt_binding(
    candidate,
    tested_view,
    selected_tests,
    policy_digest,
    component_id,
    candidate_root=REPO,
):
    value = {
        "candidate_digest": candidate.digest,
        "candidate_closure_digest": candidate.closure_digest,
        "tested_view_digest": tested_view["digest"],
        "test_manifest_digest": test_manifest.canonical_digest(selected_tests),
        "policy_digest": policy_digest,
        "runner_revision": runner_revision(candidate_root),
        "environment": environment_identity(),
        "component_id": component_id,
    }
    value["binding_digest"] = test_manifest.canonical_digest(value)
    return value


def _safe_local_directory(relative):
    """Return one allowed ignored local-state directory without path redirection.

    A metadata-free test projection deliberately has no Git metadata, so ``git
    check-ignore`` cannot operate there. It may still persist the report below
    its copied root only when Git confirms that there is no repository and the
    copied root has the exact ``tmp/`` ignore rule. The exception is deliberately
    narrower than the normal Git-backed path: it accepts only the two fixed
    state directories, never a caller-selected path.
    """
    relative = Path(relative)
    if relative not in LOCAL_STATE_DIRECTORIES:
        raise GateError("gate state directory is not an allowed repository-local path")
    root = REPO.resolve()
    if not root.is_dir() or root.is_symlink():
        raise GateError("repository root for gate state is unsafe")
    directory = root / relative
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(directory)],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ignore_file = root / ".gitignore"
    try:
        exact_tmp_ignore = (
            ignore_file.is_file()
            and not ignore_file.is_symlink()
            and "tmp/" in ignore_file.read_text(encoding="utf-8").splitlines()
        )
    except OSError:
        exact_tmp_ignore = False
    metadata_free_projection = (
        ignored.returncode == 128 and not (root / ".git").exists()
    )
    if ignored.returncode != 0 and not (
        metadata_free_projection and exact_tmp_ignore
    ):
        raise GateError("gate state directory must be ignored and repository-local")
    current = root
    for part in Path(relative).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            current.mkdir(mode=0o700)
            try:
                metadata = current.lstat()
            except OSError as error:
                raise GateError(
                    f"could not inspect newly created gate-state path: {current}"
                ) from error
        if stat.S_ISLNK(metadata.st_mode):
            raise GateError(f"ignored gate-state path is a symlink: {current}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise GateError(f"ignored gate-state path is unsafe: {current}")
    return directory


def _atomic_json(path, value):
    path = Path(path)
    if path.exists() and path.is_symlink():
        raise GateError(f"refusing to replace symlinked gate state: {path}")
    temporary_name = f".{path.name}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_descriptor = os.open(str(path.parent), directory_flags)
    try:
        payload = (
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        descriptor = os.open(
            temporary_name, flags, 0o600, dir_fd=directory_descriptor
        )
        try:
            remaining = memoryview(payload)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise GateError("could not finish writing gate state")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.rename(
            temporary_name,
            path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def reusable_receipt(binding):
    directory = _safe_local_directory(Path("tmp/test-gate-receipts"))
    path = directory / f"{binding['binding_digest']}.json"
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if (
        value.get("schema") != RECEIPT_SCHEMA
        or value.get("outcome") != "pass"
        or value.get("binding") != binding
    ):
        return None
    return value


def write_receipt(binding):
    directory = _safe_local_directory(Path("tmp/test-gate-receipts"))
    path = directory / f"{binding['binding_digest']}.json"
    _atomic_json(
        path,
        {"schema": RECEIPT_SCHEMA, "outcome": "pass", "binding": binding},
    )
    return path


def local_receipts_allowed(options):
    """Provider hard boundaries never trust or mutate checkout-local evidence."""
    return not options.provider_hard


def reusable_full_receipt(binding, component_id, options):
    if not component_id.endswith("/full") or not local_receipts_allowed(options):
        return None
    return reusable_receipt(binding)


def persist_full_receipt(binding, result, candidate_stable, options):
    if (
        result.outcome != "pass"
        or not candidate_stable
        or not local_receipts_allowed(options)
    ):
        return False
    write_receipt(binding)
    return True


def _write_report(report):
    directory = _safe_local_directory(Path("tmp/test-gate-reports"))
    path = directory / f"latest-{report['gate_id']}.json"
    _atomic_json(path, report)
    return path


def file_target_breach(report, target, policy_digest, options):
    """Best-effort durable performance work; its disposition never changes the gate."""
    if file_test_budget_task is None:
        return {"disposition": "unavailable", "mutated": False}
    actual = time.monotonic() - report["_started"]
    components = {
        component["component_id"]: component["duration_seconds"]
        for component in report["components"]
    }
    occurrence = {
        "schema_id": REPORT_SCHEMA,
        "gate_id": report["gate_id"],
        "config_slot": f"testing.{report['gate_id']}.target_seconds",
        "actual_seconds": actual,
        "target_seconds": target,
        "components": components,
        "candidate": report["candidate"]["digest"],
        "receipt": test_manifest.canonical_digest(
            {
                "candidate": report["candidate"]["digest"],
                "components": components,
                "policy": policy_digest,
            }
        ),
        "command": "automation/run_test_gate.py " + " ".join(sys.argv[1:]),
        "trigger": options.at_transition or ("explicit" if options.explicit else "pre-commit"),
        "environment": environment_identity(),
    }
    return file_test_budget_task.file_budget_task(REPO, occurrence).as_dict()


def _account_maximum(report, maximum):
    if maximum is None:
        return
    report["maximum_seconds"] = maximum
    report["maximum_exceeded"] = report["duration_seconds"] > maximum
    if not report["maximum_exceeded"]:
        return
    if report["outcome"] not in ("pass", "deferred"):
        return
    report["incomplete"] = sorted(
        set(report["incomplete"]).union(("gate-interval",))
    )
    if report["gate_id"] == "final" or report.get("critical", {}).get(
        "is_critical"
    ):
        report["outcome"] = "blocked-incomplete"
        report["reason"] = "whole gate interval exceeded the configured maximum"
    else:
        report["outcome"] = "deferred"
        report["reason"] = (
            "whole gate interval exceeded the maximum; reversible coverage remains deferred"
        )


def _account_elapsed(report, started, target, maximum):
    report["duration_seconds"] = round(time.monotonic() - started, 6)
    if target is not None:
        report["target_seconds"] = target
        report["target_exceeded"] = report["duration_seconds"] > target
    _account_maximum(report, maximum)
    report["exit_code"] = OUTCOME_EXIT[report["outcome"]]


def _threshold_state(report):
    return (
        report["outcome"],
        report.get("target_exceeded", False),
        report.get("maximum_exceeded", False),
        "budget_filing" in report,
    )


def _ensure_budget_filing(report, started, target, policy_digest, options):
    if (
        not report.get("target_exceeded")
        or "budget_filing" in report
        or target is None
        or options is None
    ):
        return
    report["_started"] = started
    try:
        report["budget_filing"] = file_target_breach(
            report, target, policy_digest, options
        )
    finally:
        report.pop("_started", None)


def _persist_accounted_report(
    path, report, started, target, maximum, policy_digest, options
):
    """Persist threshold transitions caused by filing or prior persistence itself."""
    directory = _safe_local_directory(Path("tmp/test-gate-reports"))
    expected_path = directory / f"latest-{report['gate_id']}.json"
    try:
        matches_report_path = path.resolve() == expected_path.resolve()
    except OSError as error:
        raise GateError("machine report path could not be verified") from error
    if not matches_report_path:
        raise GateError("machine report path escaped its allowed local-state directory")
    for _attempt in range(4):
        _account_elapsed(report, started, target, maximum)
        _ensure_budget_filing(report, started, target, policy_digest, options)
        _account_elapsed(report, started, target, maximum)
        before = _threshold_state(report)
        _atomic_json(expected_path, report)
        _account_elapsed(report, started, target, maximum)
        if _threshold_state(report) == before:
            break


def _render_summary(report, path):
    lines = [
        f"test gate: {report['gate_id']}",
        f"outcome: {report['outcome']}",
        f"evidence: {report['evidence']}",
        f"enforcement: {report['enforcement']}",
        f"reason: {report['reason']}",
    ]
    if report["candidate"] is not None:
        lines.append(f"candidate: {report['candidate']['digest']}")
    lines.append("component timings:")
    if report["components"]:
        for component in report["components"]:
            lines.append(
                "  {component_id}: {outcome} ({evidence}, {duration_seconds:.2f}s)".format(
                    **component
                )
            )
            if component["outcome"] != "pass" and component.get("detail"):
                lines.extend(f"    {line}" for line in component["detail"].splitlines())
    else:
        lines.append("  (none)")
    lines.append(
        "coverage: {selected} selected, {deferred} deferred, {incomplete} incomplete".format(
            selected=len(report["selected"]),
            deferred=len(report["deferred"]),
            incomplete=len(report["incomplete"]),
        )
    )
    lines.append(f"duration: {report['duration_seconds']:.2f}s")
    if report.get("target_exceeded"):
        filing = report.get("budget_filing", {})
        lines.append(
            "target: exceeded {target:.2f}s; budget filing {disposition}".format(
                target=report.get("target_seconds", 0.0),
                disposition=filing.get("disposition", "unavailable"),
            )
        )
    if path is None:
        disposition = report.get("report_write", {}).get("disposition", "unavailable")
        lines.append(f"machine report: {disposition}")
    else:
        lines.append(f"machine report: {path.resolve().relative_to(REPO.resolve())}")
    return "\n".join(lines) + "\n"


def _write_summary(summary):
    sys.stdout.write(summary)
    sys.stdout.flush()


def emit_report(
    report,
    target=None,
    maximum=None,
    policy_digest=None,
    options=None,
):
    started = report.pop("_started")
    _account_elapsed(report, started, target, maximum)
    _ensure_budget_filing(report, started, target, policy_digest, options)
    _account_elapsed(report, started, target, maximum)
    try:
        path = _write_report(report)
    except GateError as error:
        path = None
        report["report_write"] = {"disposition": "refused"}
        report["outcome"] = "error"
        report["reason"] = str(error)
        _account_elapsed(report, started, target, maximum)
    except OSError as error:
        read_only = isinstance(error, PermissionError) or getattr(error, "errno", None) in (
            errno.EACCES,
            errno.EPERM,
            errno.EROFS,
        )
        path = None
        report["report_write"] = {
            "disposition": "unavailable" if read_only else "failed"
        }
        if not read_only:
            report["outcome"] = "error"
            report["reason"] = "machine report persistence failed"
            _account_elapsed(report, started, target, maximum)
    if path is not None:
        _persist_accounted_report(
            path, report, started, target, maximum, policy_digest, options
        )
    reported_state = _threshold_state(report)
    _write_summary(_render_summary(report, path))
    _account_elapsed(report, started, target, maximum)
    _ensure_budget_filing(report, started, target, policy_digest, options)
    _account_elapsed(report, started, target, maximum)
    if path is not None:
        _persist_accounted_report(
            path, report, started, target, maximum, policy_digest, options
        )
    if _threshold_state(report) != reported_state:
        _write_summary(
            "test gate final outcome after output accounting: "
            f"{report['outcome']} ({report['reason']})\n"
        )
        _account_elapsed(report, started, target, maximum)
        _ensure_budget_filing(report, started, target, policy_digest, options)
        _account_elapsed(report, started, target, maximum)
        if path is not None:
            _persist_accounted_report(
                path, report, started, target, maximum, policy_digest, options
            )
    _account_elapsed(report, started, target, maximum)
    return report["exit_code"]


def _base_report(gate, started):
    return {
        "schema": REPORT_SCHEMA,
        "gate_id": gate,
        "outcome": "error",
        "evidence": "none",
        "enforcement": "unobserved",
        "reason": "gate did not complete",
        "candidate": None,
        "tested_view": None,
        "policy_digest": None,
        "critical": {},
        "selected": [],
        "deferred": [],
        "incomplete": [],
        "components": [],
        "target_exceeded": False,
        "maximum_exceeded": False,
        "invocation": None,
        "_started": started,
    }


def main(arguments=(), started=None):
    started = PROCESS_STARTED if started is None else started
    options = parse_arguments(arguments)
    report = _base_report(options.gate, started)
    try:
        with tempfile.TemporaryDirectory(prefix="agentfold-test-gate-") as scratch:
            scratch_root = Path(scratch).resolve()
            candidate, tested_view, candidate_root, unchanged = capture_candidate(
                options, scratch_root
            )
            report["candidate"] = candidate.as_dict()
            report["tested_view"] = {
                "schema": tested_view["schema"],
                "digest": tested_view["digest"],
                "paths": tested_view["paths"],
            }
            policy, policy_digest = load_candidate_policy(
                candidate_root,
                options.config,
                scratch_root,
                candidate.base_revision,
            )
            report["policy_digest"] = policy_digest
            report["invocation"] = {
                "kind": (
                    "explicit"
                    if options.explicit
                    else "transition"
                    if options.at_transition
                    else "routine"
                ),
                "transition": options.at_transition,
                "base_revision": candidate.base_revision,
                "head_revision": options.head_revision,
                "candidate_revision": candidate.candidate_revision,
                "provider_hard": options.provider_hard,
            }
            disposition = _final_disposition(options, policy)
            if disposition is not None:
                report["outcome"], report["reason"] = disposition
                return emit_report(report)

            classification = classify_candidate(candidate.changed_paths, policy)
            required_critical = tuple(classification.required_check_ids)
            critical = bool(
                classification.critical_bindings
                or classification.unmatched_paths
                or required_critical
            )
            report["critical"] = {
                "is_critical": critical,
                "bindings": [
                    getattr(binding, "name", getattr(binding, "category", str(binding)))
                    for binding in classification.critical_bindings
                ],
                "unmatched_paths": list(classification.unmatched_paths),
                "required_check_ids": list(required_critical),
            }
            all_tests = _all_relative_tests(candidate_root)
            if options.gate == "final" or "repository-tests/full" in required_critical:
                selected, deferred = all_tests, ()
            else:
                selected, deferred = routine_test_manifest(
                    candidate.changed_paths, all_tests
                )
            report["selected"] = list(selected)
            report["deferred"] = list(deferred)

            budget = _budget_for(options.gate, policy)
            maximum = float(budget.maximum_seconds)
            target = float(budget.target_seconds)
            hard_deadline = started + maximum
            reporting_reserve = min(0.5, max(0.05, maximum * 0.05))
            component_deadline = hard_deadline - reporting_reserve
            components = []
            component_environment = candidate_git_environment(
                candidate_root, scratch_root / "candidate.index"
            )
            commands = admission_commands(options, candidate, candidate_root)
            for component_id, command in commands:
                result = run_component(
                    component_id,
                    command,
                    component_deadline - time.monotonic(),
                    cwd=candidate_root,
                    cleanup_deadline=hard_deadline,
                    internal_environment=component_environment,
                )
                components.append(result)
                if result.outcome != "pass":
                    break

            if not components or all(result.outcome == "pass" for result in components):
                if selected:
                    component_id = (
                        "repository-tests/full"
                        if selected == all_tests
                        else "repository-tests/selected"
                    )
                    binding = receipt_binding(
                        candidate,
                        tested_view,
                        selected,
                        policy_digest,
                        component_id,
                        REPO if options.provider_hard else candidate_root,
                    )
                    receipt = reusable_full_receipt(binding, component_id, options)
                    if receipt is not None:
                        components.append(
                            ComponentResult(
                                component_id,
                                "pass",
                                "reused",
                                0.0,
                                (),
                                f"reused {binding['binding_digest']}",
                            )
                        )
                    else:
                        command = [
                            sys.executable,
                            str(
                                AUTOMATION / "run_tests.py"
                                if options.provider_hard
                                else candidate_root / "automation/run_tests.py"
                            ),
                            "--view-root",
                            str(candidate_root),
                        ]
                        for test in selected:
                            command.extend(("--test-file", test))
                        result = run_component(
                            component_id,
                            command,
                            component_deadline - time.monotonic(),
                            cwd=candidate_root,
                            cleanup_deadline=hard_deadline,
                            internal_environment=component_environment,
                        )
                        components.append(result)
                        persist_full_receipt(binding, result, unchanged(), options)
                elif "repository-tests/full" in required_critical:
                    components.append(
                        ComponentResult(
                            "repository-tests/full",
                            "incomplete",
                            "none",
                            0.0,
                            (),
                            "critical full-test evidence is unavailable because no tests were discovered",
                        )
                    )
                else:
                    components.append(
                        ComponentResult(
                            "repository-tests/selected",
                            "pass",
                            "none",
                            0.0,
                            (),
                            "no changed path mapped to a routine test",
                        )
                    )

            if (
                time.monotonic() >= component_deadline
                and not any(result.outcome == "incomplete" for result in components)
            ):
                components.append(
                    ComponentResult(
                        "repository-tests/reporting-reserve",
                        "incomplete",
                        "none",
                        0.0,
                        (),
                        "component work consumed the interval reserved for cleanup and reporting",
                    )
                )
            report["components"] = [result.as_dict() for result in components]
            candidate_stable = unchanged()
            apply_gate_outcome(
                report,
                options.gate,
                components,
                selected,
                deferred,
                critical,
                required_critical,
                candidate_stable,
            )
            report["evidence"] = (
                "executed"
                if any(result.evidence == "executed" for result in components)
                else "reused"
                if any(result.evidence == "reused" for result in components)
                else "none"
            )
            return emit_report(
                report, target, maximum, policy_digest, options
            )
    except getattr(test_gate_config, "ConfigError", ()) as error:
        report["outcome"] = "invalid"
        report["reason"] = str(error)
        return emit_report(report)
    except (GateError, test_manifest.ManifestError, OSError, ValueError) as error:
        report["outcome"] = "error"
        report["reason"] = str(error)
        return emit_report(report)
    except Exception as error:  # keep unexpected operational failures machine-visible
        report["outcome"] = "error"
        report["reason"] = f"unexpected gate error: {error}"
        return emit_report(report)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], PROCESS_STARTED))
