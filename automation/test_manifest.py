#!/usr/bin/env python3
"""Exact candidate and tested-view manifests for the repository test gates."""

import hashlib
import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path


SCHEMA_ID = "agentfold.test-manifest/v1"
REGULAR_INDEX_MODES = frozenset(("100644", "100755"))
GIT_METADATA_SENTINEL = ".git"
GIT_NO_REPLACE_ENVIRONMENT = "GIT_NO_REPLACE_OBJECTS"


class ManifestError(RuntimeError):
    """The requested candidate cannot be represented exactly and safely."""


@dataclass(frozen=True)
class CandidateManifest:
    kind: str
    digest: str
    closure_digest: str
    paths: tuple
    changed_paths: tuple
    source_fingerprint: str
    base_revision: str = ""
    candidate_revision: str = ""

    def as_dict(self):
        return {
            "schema": SCHEMA_ID,
            "kind": self.kind,
            "digest": self.digest,
            "closure_digest": self.closure_digest,
            "paths": list(self.paths),
            "changed_paths": list(self.changed_paths),
            "source_fingerprint": self.source_fingerprint,
            "base_revision": self.base_revision,
            "candidate_revision": self.candidate_revision,
        }


def canonical_digest(value):
    """Return a stable digest for a JSON-compatible value."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repository, arguments, environment=None):
    environment = dict(os.environ if environment is None else environment)
    environment[GIT_NO_REPLACE_ENVIRONMENT] = "1"
    result = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=repository,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip()
        suffix = f": {detail}" if detail else ""
        raise ManifestError(f"Git candidate query failed{suffix}")
    return result.stdout


def selected_index_path(repository, environment=None):
    raw = _git(repository, ["rev-parse", "--git-path", "index"], environment)
    raw = raw.rstrip(b"\n")
    if not raw or b"\0" in raw or b"\n" in raw:
        raise ManifestError("selected Git index path is malformed")
    path = Path(os.fsdecode(raw))
    return path if path.is_absolute() else Path(repository) / path


def copy_staged_index(repository, destination):
    """Copy the selected index once; later reads use only this immutable candidate."""
    source = selected_index_path(repository, os.environ.copy())
    destination = Path(destination)
    try:
        if source.is_symlink() or not source.is_file():
            raise ManifestError("selected Git index is unavailable or a symlink")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        destination.chmod(0o600)
    except OSError as error:
        raise ManifestError("could not snapshot the selected Git index") from error
    return file_digest(destination)


def _parse_index(output):
    if output and not output.endswith(b"\0"):
        raise ManifestError("unterminated staged index listing")
    records = []
    for raw in output[:-1].split(b"\0") if output else ():
        try:
            header, raw_path = raw.split(b"\t", 1)
            raw_mode, raw_oid, raw_stage = header.split(b" ")
            mode = raw_mode.decode("ascii")
            oid = raw_oid.decode("ascii").lower()
            path = os.fsdecode(raw_path)
        except (UnicodeDecodeError, ValueError) as error:
            raise ManifestError("malformed staged index entry") from error
        if (
            mode not in REGULAR_INDEX_MODES
            or raw_stage != b"0"
            or not oid
            or any(character not in "0123456789abcdef" for character in oid)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or any(part.casefold() == ".git" for part in Path(path).parts)
        ):
            raise ManifestError("staged candidate contains an unsupported index entry")
        records.append({"path": path, "mode": mode, "object": oid})
    return tuple(sorted(records, key=lambda record: record["path"]))


def _parse_changed_paths(output):
    if output and not output.endswith(b"\0"):
        raise ManifestError("unterminated staged changed-path listing")
    paths = []
    fields = output[:-1].split(b"\0") if output else ()
    index = 0
    while index < len(fields):
        raw_status = fields[index]
        index += 1
        status = raw_status.decode("ascii", "strict")
        count = 2 if status[:1] in ("R", "C") else 1
        if index + count > len(fields):
            raise ManifestError("malformed staged changed-path listing")
        raw_paths = fields[index:index + count]
        index += count
        paths.extend(os.fsdecode(path) for path in raw_paths)
    return tuple(sorted(set(paths)))


def staged_candidate(
    repository,
    frozen_index,
    *,
    base_revision=None,
    candidate_revision="",
    kind="staged-index",
):
    """Describe the exact full-index candidate represented by ``frozen_index``."""
    environment = os.environ.copy()
    environment[GIT_NO_REPLACE_ENVIRONMENT] = "1"
    environment["GIT_INDEX_FILE"] = str(Path(frozen_index).resolve())
    records = _parse_index(
        _git(repository, ["ls-files", "--stage", "-z"], environment)
    )
    if base_revision is None:
        base_revision = os.fsdecode(
            _git(repository, ["rev-parse", "--verify", "HEAD"])
        ).strip()
    if not base_revision:
        raise ManifestError("staged candidate base revision is unavailable")
    changed = _parse_changed_paths(
        _git(
            repository,
            ["diff", "--cached", "--name-status", "-z", "-M", base_revision],
            environment,
        )
    )
    closure_digest = canonical_digest(records)
    source_fingerprint = file_digest(frozen_index)
    value = {
        "schema": SCHEMA_ID,
        "kind": kind,
        "closure_digest": closure_digest,
        "changed_paths": changed,
        "base_revision": base_revision,
        "candidate_revision": candidate_revision,
    }
    return CandidateManifest(
        kind,
        canonical_digest(value),
        closure_digest,
        tuple(record["path"] for record in records),
        changed,
        source_fingerprint,
        base_revision,
        candidate_revision,
    )


def materialize_staged_candidate(repository, frozen_index, destination):
    """Materialize regular-file bytes addressed by an immutable copied index.

    Tracked symlinks are rejected while parsing the index.  Following one would let
    the tested process read bytes that are neither Git objects in the candidate nor
    part of the tested-view digest.
    """
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment[GIT_NO_REPLACE_ENVIRONMENT] = "1"
    environment["GIT_INDEX_FILE"] = str(Path(frozen_index).resolve())
    _git(
        repository,
        ["checkout-index", "--all", f"--prefix={destination}{os.sep}"],
        environment,
    )
    # The reconciler intentionally uses the presence of ``.git`` to select its
    # immutable-index implementation.  checkout-index cannot project that
    # repository topology: Git rejects tracked .git entries and never records
    # directories.  Add one fixed, empty sentinel directory so candidate checks
    # use the frozen index and the separately supplied GIT_DIR, GIT_WORK_TREE,
    # and GIT_INDEX_FILE.  The name is canonical rather than candidate-derived,
    # and _parse_index rejects any candidate attempt to occupy it.
    (destination / GIT_METADATA_SENTINEL).mkdir(mode=0o700)
    return tree_manifest(destination)


def _tree_records(root):
    root = Path(root).resolve()
    records = []
    for current_root, directory_names, file_names in os.walk(
        str(root), followlinks=False
    ):
        current = Path(current_root)
        for directory_name in tuple(directory_names):
            path = current / directory_name
            if path.is_symlink():
                directory_names.remove(directory_name)
                relative = path.relative_to(root).as_posix()
                raise ManifestError(
                    f"tested-view symlinks are unsupported: {relative}"
                )
            relative = path.relative_to(root).as_posix()
            records.append({"path": relative, "kind": "directory"})
        for file_name in file_names:
            path = current / file_name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ManifestError(
                    f"tested-view symlinks are unsupported: {relative}"
                )
            elif stat.S_ISREG(info.st_mode):
                records.append(
                    {
                        "path": relative,
                        "kind": "file",
                        "mode": stat.S_IMODE(info.st_mode),
                        "sha256": file_digest(path),
                    }
                )
            else:
                raise ManifestError(f"unsupported tested-view entry: {relative}")
    return tuple(sorted(records, key=lambda record: record["path"]))


def tree_manifest(root):
    """Return the exact regular-file and directory closure below ``root``."""
    records = _tree_records(root)
    return {
        "schema": SCHEMA_ID,
        "digest": canonical_digest(records),
        "paths": [record["path"] for record in records],
        "records": records,
    }


def live_index_matches(repository, expected_fingerprint, expected_head=None):
    try:
        if file_digest(selected_index_path(repository)) != expected_fingerprint:
            return False
        if expected_head is not None:
            current_head = os.fsdecode(
                _git(repository, ["rev-parse", "--verify", "HEAD"])
            ).strip()
            if current_head != expected_head:
                return False
        return True
    except (ManifestError, OSError):
        return False
