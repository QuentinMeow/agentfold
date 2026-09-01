#!/usr/bin/env python3
"""Executable replay diagnostics for displaced-tip queue continuity.

This is deliberately a design prototype, not queue-resolution authority. It builds
real Git DAGs and reports what tree ownership, patch-id, range-diff, and replay can
observe. The authoritative expected verdicts come from the shared POC scenario
matrix; none is derived from the replay heuristics.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable


QUEUE_PATH = "message-queue/needs-agent/requests/non-blocking-action.md"
OID_RE = re.compile(r"^[0-9a-f]{40,64}$")


class GitError(RuntimeError):
    """A Git command failed while constructing or inspecting a fixture."""


class GitRepo:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.clock = 0
        path.mkdir(parents=True)
        self.run("init", "-q")
        self.run("config", "user.name", "Replay Oracle")
        self.run("config", "user.email", "replay-oracle@example.invalid")
        self.run("config", "commit.gpgSign", "false")
        self.run("config", "core.autocrlf", "false")
        # A disposable fixture must not inherit hooks from the host repository.
        self.run("config", "core.hooksPath", ".git/no-hooks")

    def _env(self, *, commit: bool = False) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_NAME": "Replay Oracle",
                "GIT_AUTHOR_EMAIL": "replay-oracle@example.invalid",
                "GIT_COMMITTER_NAME": "Replay Oracle",
                "GIT_COMMITTER_EMAIL": "replay-oracle@example.invalid",
                "GIT_EDITOR": "true",
                "GIT_SEQUENCE_EDITOR": "true",
            }
        )
        if commit:
            self.clock += 1
            timestamp = str(978307200 + self.clock) + " +0000"
            env["GIT_AUTHOR_DATE"] = timestamp
            env["GIT_COMMITTER_DATE"] = timestamp
        return env

    def run(
        self,
        *args: str,
        check: bool = True,
        commit: bool = False,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *args],
            cwd=self.path,
            env=self._env(commit=commit),
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and result.returncode:
            rendered = " ".join(("git", *args))
            raise GitError(
                f"{rendered} exited {result.returncode}: {result.stderr.strip()}"
            )
        return result

    def inspect(
        self,
        *args: str,
        check: bool = True,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return self.run(
            "--no-replace-objects", *args, check=check, input_text=input_text
        )

    def write(self, relative: str, content: str) -> None:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def delete(self, relative: str) -> None:
        target = self.path / relative
        if target.exists():
            target.unlink()

    def commit(self, subject: str) -> str:
        self.run("add", "-A")
        self.run("commit", "-q", "-m", subject, commit=True)
        return self.oid("HEAD")

    def checkout(self, name: str, start: str) -> None:
        self.run("checkout", "-q", "-B", name, start)

    def cherry_pick(
        self, oid: str, *, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return self.run("cherry-pick", oid, check=check, commit=True)

    def oid(self, revision: str) -> str:
        return self.inspect("rev-parse", revision).stdout.strip()

    def tree_oid(self, revision: str) -> str:
        return self.oid(f"{revision}^{{tree}}")

    def path_exists(self, revision: str, relative: str) -> bool:
        return (
            self.inspect(
                "cat-file", "-e", f"{revision}:{relative}", check=False
            ).returncode
            == 0
        )

    def path_equal(self, left: str, right: str, relative: str) -> bool:
        return (
            self.inspect(
                "diff", "--quiet", left, right, "--", relative, check=False
            ).returncode
            == 0
        )

    def commits(self, base: str, tip: str, *, no_merges: bool = True) -> list[str]:
        args = ["rev-list", "--reverse", "--topo-order"]
        if no_merges:
            args.append("--no-merges")
        args.append(f"{base}..{tip}")
        return [line for line in self.inspect(*args).stdout.splitlines() if line]

    def patch_id(self, commit_oid: str) -> str:
        patch = self.inspect(
            "show", "--format=", "--no-ext-diff", "--binary", commit_oid
        ).stdout
        result = self.inspect("patch-id", "--stable", input_text=patch)
        fields = result.stdout.split()
        return fields[0] if fields else ""

    def patch_ids(self, base: str, tip: str) -> list[str]:
        return [self.patch_id(commit) for commit in self.commits(base, tip)]

    def range_diff(
        self, old_base: str, old_tip: str, new_base: str, new_tip: str
    ) -> tuple[int, list[str]]:
        result = self.inspect(
            "range-diff",
            "--no-color",
            f"{old_base}..{old_tip}",
            f"{new_base}..{new_tip}",
            check=False,
        )
        lines = [line.rstrip() for line in result.stdout.splitlines() if line.strip()]
        return result.returncode, lines

    def replay(
        self,
        old_base: str,
        old_tip: str,
        new_base: str,
        candidate: str,
    ) -> dict[str, Any]:
        commits = self.commits(old_base, old_tip)
        self.run("checkout", "-q", "--detach", new_base)
        for commit_oid in commits:
            result = self.cherry_pick(commit_oid, check=False)
            if result.returncode:
                unmerged = self.inspect(
                    "diff", "--name-only", "--diff-filter=U", check=False
                ).stdout.splitlines()
                status = "conflict" if unmerged else "empty"
                self.run("cherry-pick", "--abort", check=False)
                self.run("checkout", "-q", "--detach", candidate)
                return {
                    "status": status,
                    "commit_count": len(commits),
                    "tree_matches_candidate": False,
                    "unmerged_paths": sorted(unmerged),
                }
        matches = self.tree_oid("HEAD") == self.tree_oid(candidate)
        replay_tree = self.tree_oid("HEAD")
        self.run("checkout", "-q", "--detach", candidate)
        return {
            "status": "clean",
            "commit_count": len(commits),
            "tree_matches_candidate": matches,
            "replay_tree": replay_tree,
        }


def create_common(repo: GitRepo, *, queue_present: bool) -> str:
    repo.write("app.txt", "base\n")
    if queue_present:
        repo.write(QUEUE_PATH, "**Status:** open\n\nLive action.\n")
    return repo.commit("create common history")


def base_record(
    *,
    scenario: str,
    repo: GitRepo,
    c_oid: str,
    o_oid: str,
    m_oid: str,
    n_oid: str,
    classification: str,
    evidence_verdict: str,
    expected_verdict: str,
    explanation: str,
    extra_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    old_patch_ids = repo.patch_ids(c_oid, o_oid)
    new_patch_ids = repo.patch_ids(m_oid, n_oid)
    range_code, range_lines = repo.range_diff(c_oid, o_oid, m_oid, n_oid)
    replay = repo.replay(c_oid, o_oid, m_oid, n_oid)
    old_exists = repo.path_exists(o_oid, QUEUE_PATH)
    new_exists = repo.path_exists(n_oid, QUEUE_PATH)
    signals: dict[str, Any] = {
        "old_path_matches_common": repo.path_equal(c_oid, o_oid, QUEUE_PATH),
        "old_tip_has_action": old_exists,
        "candidate_has_action": new_exists,
        "candidate_deletes_old_action": old_exists and not new_exists,
        "old_non_merge_patch_ids": old_patch_ids,
        "candidate_non_merge_patch_ids": new_patch_ids,
        "shared_patch_ids": sorted(set(old_patch_ids) & set(new_patch_ids)),
        "range_diff_exit": range_code,
        "range_diff_lines": range_lines,
        "replay": replay,
    }
    if extra_signals:
        signals.update(extra_signals)
    return {
        "scenario": scenario,
        "oids": {"C": c_oid, "O": o_oid, "M": m_oid, "N": n_oid},
        "classification": classification,
        "authoring_lineage": (
            "old-tip path equals common history"
            if signals["old_path_matches_common"]
            else "old lineage changed the path"
        ),
        "evidence_verdict": evidence_verdict,
        "authoritative_expected_verdict": expected_verdict,
        "authority": "diagnostic-only; never authorizes suppression",
        "heuristics": signals,
        "explanation": explanation,
    }


def build_s1(root: Path) -> dict[str, Any]:
    repo = GitRepo(root / "s1-valid-base-resolution")
    c_oid = create_common(repo, queue_present=True)
    repo.checkout("s1-old", c_oid)
    repo.write("feature.txt", "task feature\n")
    o_oid = repo.commit("add task feature")
    repo.checkout("s1-base", c_oid)
    repo.write(QUEUE_PATH, "**Status:** in-repair\n\nClaimed action.\n")
    repo.commit("claim base action")
    repo.write("docs/evidence.txt", "resolution evidence\n")
    repo.delete(QUEUE_PATH)
    m_oid = repo.commit("resolve base action with evidence")
    repo.checkout("s1-candidate", m_oid)
    repo.cherry_pick(o_oid)
    n_oid = repo.oid("HEAD")
    return base_record(
        scenario="S1-valid-base-resolution",
        repo=repo,
        c_oid=c_oid,
        o_oid=o_oid,
        m_oid=m_oid,
        n_oid=n_oid,
        classification="inherited candidate-side absence",
        evidence_verdict="valid real-edge claim and changed evidence",
        expected_verdict="no-finding",
        explanation=(
            "Replay shows the task delta survived and tree ownership locates the absence "
            "on the selected base; only the separately supplied real-edge evidence verdict "
            "makes the disappearance legitimate."
        ),
    )


def build_s2(root: Path) -> dict[str, Any]:
    repo = GitRepo(root / "s2-invalid-base-deletion")
    c_oid = create_common(repo, queue_present=True)
    repo.checkout("s2-old", c_oid)
    repo.write("feature.txt", "task feature\n")
    o_oid = repo.commit("add task feature")
    repo.checkout("s2-base", c_oid)
    repo.delete(QUEUE_PATH)
    m_oid = repo.commit("delete base action without evidence")
    repo.checkout("s2-candidate", m_oid)
    repo.cherry_pick(o_oid)
    n_oid = repo.oid("HEAD")
    return base_record(
        scenario="S2-invalid-base-deletion",
        repo=repo,
        c_oid=c_oid,
        o_oid=o_oid,
        m_oid=m_oid,
        n_oid=n_oid,
        classification="inherited candidate-side absence",
        evidence_verdict="invalid: no committed claim or changed evidence",
        expected_verdict="finding",
        explanation=(
            "Every replay and final-tree signal looks as healthy as S1, but the base "
            "deletion has no lifecycle evidence. Replay therefore cannot authorize "
            "suppression."
        ),
    )


def build_s3(root: Path) -> dict[str, Any]:
    repo = GitRepo(root / "s3-branch-owned-action-loss")
    c_oid = create_common(repo, queue_present=False)
    repo.checkout("s3-old", c_oid)
    repo.write(QUEUE_PATH, "**Status:** open\n\nBranch-owned action.\n")
    repo.commit("file branch-owned action")
    repo.write("feature.txt", "task feature\n")
    feature_oid = repo.commit("add task feature")
    o_oid = repo.oid("HEAD")
    repo.checkout("s3-base", c_oid)
    repo.write("base.txt", "new base\n")
    m_oid = repo.commit("advance selected base")
    repo.checkout("s3-candidate", m_oid)
    repo.cherry_pick(feature_oid)
    n_oid = repo.oid("HEAD")
    return base_record(
        scenario="S3-branch-owned-action-loss",
        repo=repo,
        c_oid=c_oid,
        o_oid=o_oid,
        m_oid=m_oid,
        n_oid=n_oid,
        classification="old-lineage action omitted",
        evidence_verdict="no candidate-side resolution witness",
        expected_verdict="finding",
        explanation=(
            "Patch correspondence shows the feature survived, while full replay retains "
            "the branch-authored action and therefore does not match the candidate tree. "
            "That is useful diagnostic evidence of a genuine discard."
        ),
    )


def build_s7(root: Path) -> dict[str, Any]:
    repo = GitRepo(root / "s7-unrelated-restack")
    c_oid = create_common(repo, queue_present=True)
    repo.checkout("s7-old", c_oid)
    repo.write("feature.txt", "task feature\n")
    o_oid = repo.commit("add unrelated task feature")
    repo.checkout("s7-base", c_oid)
    repo.write("base.txt", "new base\n")
    m_oid = repo.commit("advance unrelated base")
    repo.checkout("s7-candidate", m_oid)
    repo.cherry_pick(o_oid)
    n_oid = repo.oid("HEAD")
    return base_record(
        scenario="S7-unrelated-restack",
        repo=repo,
        c_oid=c_oid,
        o_oid=o_oid,
        m_oid=m_oid,
        n_oid=n_oid,
        classification="queue tree unchanged",
        evidence_verdict="not needed",
        expected_verdict="no-finding",
        explanation=(
            "The candidate preserves the same queue action and cleanly replays the task "
            "delta, so the diagnostic reports no queue continuity change."
        ),
    )


def validate_simple(records: list[dict[str, Any]]) -> None:
    by_id = {record["scenario"]: record for record in records}
    for record in records:
        assert all(OID_RE.fullmatch(value) for value in record["oids"].values())
        assert record["authority"].startswith("diagnostic-only")

    s1 = by_id["S1-valid-base-resolution"]
    s2 = by_id["S2-invalid-base-deletion"]
    s3 = by_id["S3-branch-owned-action-loss"]
    s7 = by_id["S7-unrelated-restack"]
    assert s1["authoritative_expected_verdict"] == "no-finding"
    assert s1["heuristics"]["candidate_deletes_old_action"] is True
    assert s1["heuristics"]["old_path_matches_common"] is True
    assert s1["heuristics"]["replay"]["tree_matches_candidate"] is True
    assert s2["authoritative_expected_verdict"] == "finding"
    assert s2["heuristics"]["candidate_deletes_old_action"] is True
    assert s2["heuristics"]["old_path_matches_common"] is True
    assert s2["heuristics"]["replay"]["tree_matches_candidate"] is True
    assert bool(s1["heuristics"]["shared_patch_ids"])
    assert bool(s2["heuristics"]["shared_patch_ids"])
    assert s3["authoritative_expected_verdict"] == "finding"
    assert s3["heuristics"]["old_path_matches_common"] is False
    assert s3["heuristics"]["replay"]["tree_matches_candidate"] is False
    assert s7["authoritative_expected_verdict"] == "no-finding"
    assert s7["heuristics"]["candidate_deletes_old_action"] is False
    assert s7["heuristics"]["replay"]["tree_matches_candidate"] is True


def run_self_test(root: Path) -> list[dict[str, Any]]:
    records = [build_s1(root), build_s2(root), build_s3(root), build_s7(root)]
    validate_simple(records)
    return records


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="build and verify all DAGs")
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="preserve fixtures in a new or empty directory instead of a temporary one",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = ()) -> int:
    args = parse_args(argv)
    if not args.self_test:
        print("prototype.py requires --self-test", file=sys.stderr)
        return 2

    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="agentfold-replay-oracle-")
        root = Path(temporary.name)
    else:
        root = args.work_dir.resolve()
        if root.exists() and any(root.iterdir()):
            print(f"refusing non-empty --work-dir: {root}", file=sys.stderr)
            return 2
        root.mkdir(parents=True, exist_ok=True)

    try:
        records = run_self_test(root)
    except (AssertionError, GitError, OSError) as exc:
        print(f"replay-oracle self-test failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()

    for record in records:
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    print(
        f"replay-oracle self-test: {len(records)}/{len(records)} scenarios passed",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
