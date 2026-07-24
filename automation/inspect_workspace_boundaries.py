#!/usr/bin/env python3
"""Inspect declared layered-workspace roots without changing them.

This command verifies only storage-topology properties that can be observed from the
declared paths and their Git metadata. It does not inspect content, credentials,
process capabilities, backup coverage, or instruction provenance, and it never makes a
workspace safe to publish.
"""

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path


ZONE_ARGUMENTS = (
    ("integration-root", "integration_root"),
    ("publisher-root", "publisher_root"),
    ("restricted-root", "restricted_root"),
    ("raw-root", "raw_root"),
    ("temporary-root", "temporary_root"),
)
NON_GIT_ZONE_LABELS = ("restricted-root", "raw-root", "temporary-root")
MAX_GIT_METADATA_BYTES = 1024 * 1024
GIT_QUERY_TIMEOUT_SECONDS = 5
FIXED_EXECUTION_PATH = "/usr/bin:/bin"
DEFAULT_GIT_EXECUTABLE_CANDIDATES = (
    "/usr/bin/git",
    "/usr/local/bin/git",
    "/opt/homebrew/bin/git",
)


class InspectionError(RuntimeError):
    """A boundary condition could not be verified."""


class RedactingArgumentParser(argparse.ArgumentParser):
    """Reject malformed invocations without echoing supplied path values."""

    def error(self, _message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: invalid arguments; use --help\n")


def sanitized_git_environment():
    """Return a minimal fixed environment for trusted read-only Git queries."""
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "LC_ALL": "C",
        "PATH": FIXED_EXECUTION_PATH,
    }


def run_git(git_executable, root, *arguments):
    """Run a read-only Git query rooted at ``root`` with a clean Git environment."""
    try:
        return subprocess.run(
            [str(git_executable), "-C", str(root), *arguments],
            env=sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=sys.getfilesystemencoding(),
            errors="surrogateescape",
            timeout=GIT_QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise InspectionError("Git boundary inspection timed out") from error
    except OSError as error:
        raise InspectionError("Git is unavailable for boundary inspection") from error


def canonical_directory(raw_path, label):
    """Resolve one declared root and require an existing directory."""
    candidate = Path(raw_path)
    try:
        canonical = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise InspectionError(f"{label} is not an existing resolvable directory") from error
    if not canonical.is_dir():
        raise InspectionError(f"{label} is not a directory")
    return canonical


def canonical_roots(arguments):
    """Resolve every supplied CLI root under its stable semantic label."""
    roots = {}
    for label, attribute in ZONE_ARGUMENTS:
        raw_path = getattr(arguments, attribute)
        if raw_path is not None:
            roots[label] = canonical_directory(raw_path, label)
    return roots


def same_filesystem_entry(first, second):
    """Compare existing paths by filesystem identity, not textual spelling."""
    try:
        return os.path.samefile(str(first), str(second))
    except OSError as error:
        raise InspectionError(
            "a declared boundary changed during filesystem identity inspection"
        ) from error


def path_contains(ancestor, descendant):
    """Return whether an existing path is an identity-equal ancestor."""
    return any(
        same_filesystem_entry(ancestor, candidate)
        for candidate in (descendant, *descendant.parents)
    )


def paths_overlap(first, second):
    """Return whether two paths identify equal or nested filesystem entries."""
    return path_contains(first, second) or path_contains(second, first)


def canonical_git_executable(raw_path, roots):
    """Bind a regular executable outside declared roots without inherited PATH."""
    if raw_path is None:
        candidates = tuple(Path(path) for path in DEFAULT_GIT_EXECUTABLE_CANDIDATES)
    else:
        supplied = Path(raw_path)
        if not supplied.is_absolute():
            raise InspectionError(
                "the trusted Git executable binding must be an absolute path"
            )
        candidates = (supplied,)

    for candidate in candidates:
        try:
            canonical = candidate.resolve(strict=True)
            state = canonical.stat()
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError) as error:
            raise InspectionError(
                "could not inspect the trusted Git executable binding"
            ) from error
        if not stat.S_ISREG(state.st_mode) or not os.access(str(canonical), os.X_OK):
            raise InspectionError(
                "the trusted Git executable binding is not a regular executable"
            )
        if any(path_contains(root, canonical) for root in roots.values()):
            raise InspectionError(
                "the trusted Git executable binding is inside a declared workspace root"
            )
        return canonical

    raise InspectionError(
        "no trusted Git executable is available; bind one with --git-executable"
    )


def reject_overlaps(roots):
    """Reject every equal, nested, or symlink-resolved root pair."""
    items = tuple(roots.items())
    for index, (first_label, first_path) in enumerate(items):
        for second_label, second_path in items[index + 1 :]:
            if paths_overlap(first_path, second_path):
                raise InspectionError(
                    f"{first_label} overlaps {second_label} after canonicalization"
                )


def resolve_git_path(root, raw_path, label):
    """Resolve a path reported by Git relative to its query directory."""
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise InspectionError(
            f"could not resolve {label} Git metadata"
        ) from error


def git_output_value(result, label):
    """Remove only Git's record terminator while preserving legal path whitespace."""
    if not result.stdout.endswith("\n"):
        raise InspectionError(f"could not parse {label} Git metadata")
    return result.stdout[:-1]


def read_regular_metadata(path, label):
    """Read one bounded regular metadata file without following a symlink."""
    try:
        before = os.lstat(str(path))
    except FileNotFoundError:
        return None
    except OSError as error:
        raise InspectionError(f"could not inspect {label} Git metadata") from error
    if not stat.S_ISREG(before.st_mode):
        raise InspectionError(f"{label} Git metadata is not a regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(str(path), flags)
    except OSError as error:
        raise InspectionError(f"could not inspect {label} Git metadata") from error
    try:
        after = os.fstat(descriptor)
        if (
            not stat.S_ISREG(after.st_mode)
            or before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
        ):
            raise InspectionError(f"{label} Git metadata changed during inspection")
        chunks = []
        remaining = MAX_GIT_METADATA_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > MAX_GIT_METADATA_BYTES:
            raise InspectionError(f"{label} Git metadata exceeds the inspection limit")
        return data
    except OSError as error:
        raise InspectionError(f"could not inspect {label} Git metadata") from error
    finally:
        os.close(descriptor)


def metadata_path(base, raw_value, label):
    """Resolve one filesystem-encoded Git metadata pointer."""
    value = raw_value.decode(sys.getfilesystemencoding(), "surrogateescape")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        return candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise InspectionError(f"could not resolve {label} Git metadata") from error


def metadata_entry_exists(path, label):
    """Observe a metadata entry while treating only ENOENT as absence."""
    try:
        os.lstat(str(path))
    except FileNotFoundError:
        return False
    except OSError as error:
        raise InspectionError(f"could not inspect {label} Git metadata") from error
    return True


def local_git_config_paths(root, label):
    """Locate local/common worktree config without asking Git to parse includes."""
    marker = root / ".git"
    try:
        marker_state = os.lstat(str(marker))
    except FileNotFoundError:
        if metadata_entry_exists(root / "HEAD", label) and (
            metadata_entry_exists(root / "objects", label)
            or metadata_entry_exists(root / "config", label)
        ):
            raise InspectionError(
                f"{label} is a bare Git repository, not a worktree"
            )
        raise InspectionError(f"{label} has no direct Git worktree marker")
    except OSError as error:
        raise InspectionError(f"could not inspect {label} Git metadata") from error

    if stat.S_ISDIR(marker_state.st_mode):
        git_directory = marker
    elif stat.S_ISREG(marker_state.st_mode):
        marker_data = read_regular_metadata(marker, label)
        line = marker_data[:-1] if marker_data.endswith(b"\n") else marker_data
        pointer = line[len(b"gitdir:") :].lstrip(b" \t")
        if (
            b"\n" in line
            or b"\r" in line
            or not line.startswith(b"gitdir:")
            or not pointer
        ):
            raise InspectionError(f"could not parse {label} Git metadata")
        git_directory = metadata_path(
            root,
            pointer,
            label,
        )
    else:
        raise InspectionError(f"{label} .git metadata is not a directory or gitfile")

    common_directory = git_directory
    common_data = read_regular_metadata(git_directory / "commondir", label)
    if common_data is not None:
        line = common_data[:-1] if common_data.endswith(b"\n") else common_data
        if b"\n" in line or b"\r" in line or not line:
            raise InspectionError(f"could not parse {label} Git metadata")
        common_directory = metadata_path(git_directory, line, label)

    return tuple(
        dict.fromkeys(
            (
                common_directory / "config",
                git_directory / "config.worktree",
            )
        )
    )


def reject_external_config_dependencies(root, label):
    """Reject local Git config constructs that can read an external path."""
    for config_path in local_git_config_paths(root, label):
        data = read_regular_metadata(config_path, label)
        if data is None:
            continue
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        section = b""
        for raw_line in data.splitlines():
            line = raw_line.strip()
            if not line or line.startswith((b"#", b";")):
                continue
            lowered = line.lower()
            if lowered.startswith(b"["):
                closing = lowered.find(b"]")
                if closing < 0:
                    continue
                header = lowered[1:closing].strip()
                section = header.split(None, 1)[0].split(b'"', 1)[0]
                section = section.split(b".", 1)[0]
                if section.startswith(b"include"):
                    raise InspectionError(
                        f"{label} local Git configuration uses external includes"
                    )
                continue
            key = (
                lowered.split(b"=", 1)[0]
                .strip()
                .replace(b" ", b"")
                .replace(b"\t", b"")
            )
            if key == b"include.path" or (
                section == b"core" and key == b"worktree"
            ):
                raise InspectionError(
                    f"{label} local Git configuration selects an external path"
                )


def require_git_worktree(root, label, git_executable):
    """Return canonical common/object directories for an exact Git worktree root."""
    reject_external_config_dependencies(root, label)
    bare = run_git(git_executable, root, "rev-parse", "--is-bare-repository")
    if bare.returncode == 0 and bare.stdout.strip() == "true":
        raise InspectionError(f"{label} is a bare Git repository, not a worktree")

    inside = run_git(git_executable, root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode or inside.stdout.strip() != "true":
        raise InspectionError(f"{label} is not the root of a Git worktree")

    prefix = run_git(git_executable, root, "rev-parse", "--show-prefix")
    top_level = run_git(git_executable, root, "rev-parse", "--show-toplevel")
    common_dir = run_git(git_executable, root, "rev-parse", "--git-common-dir")
    object_dir = run_git(git_executable, root, "rev-parse", "--git-path", "objects")
    if any(
        result.returncode
        for result in (bare, prefix, top_level, common_dir, object_dir)
    ):
        raise InspectionError(f"could not inspect {label} Git metadata")

    if bare.stdout.strip() != "false":
        raise InspectionError(f"could not verify {label} worktree mode")
    if git_output_value(prefix, label) != "":
        raise InspectionError(f"{label} is not the root of its Git worktree")
    reported_top_level = resolve_git_path(
        root,
        git_output_value(top_level, label),
        label,
    )
    if not same_filesystem_entry(root, reported_top_level):
        raise InspectionError(f"{label} is not its reported Git worktree top level")
    return {
        "common": resolve_git_path(
            root,
            git_output_value(common_dir, label),
            label,
        ),
        "objects": resolve_git_path(
            root,
            git_output_value(object_dir, label),
            label,
        ),
    }


def reject_publisher_alternates(publisher_metadata):
    """Reject local or HTTP object alternates in the clean publisher."""
    info_dir = publisher_metadata["objects"] / "info"
    for filename in ("alternates", "http-alternates"):
        alternate_path = info_dir / filename
        try:
            os.lstat(str(alternate_path))
        except FileNotFoundError:
            continue
        except OSError as error:
            raise InspectionError(
                "could not verify publisher-root object alternates"
            ) from error
        else:
            raise InspectionError(
                f"publisher-root uses objects/info/{filename}"
            )


def path_entry_exists(path, label):
    """Observe one directory entry, treating only absence as absent."""
    try:
        os.lstat(str(path))
    except FileNotFoundError:
        return False
    except OSError as error:
        raise InspectionError(
            f"could not inspect repository markers for {label}"
        ) from error
    return True


def reject_repository_markers(candidate, label):
    """Reject direct worktree or bare-repository markers at one ancestor."""
    if path_entry_exists(candidate / ".git", label):
        raise InspectionError(f"{label} is inside or is a Git repository")

    head = path_entry_exists(candidate / "HEAD", label)
    objects = path_entry_exists(candidate / "objects", label)
    config = path_entry_exists(candidate / "config", label)
    if head and (objects or config):
        raise InspectionError(f"{label} is inside or is a Git repository")


def reject_git_zone(root, label):
    """Fail if a no-Git zone is itself or is beneath direct repository markers."""
    for candidate in (root, *root.parents):
        reject_repository_markers(candidate, label)


def reject_git_metadata_overlaps(roots, repositories):
    """Keep each repository's reported metadata outside every other declared zone."""
    for owner_label, metadata in repositories.items():
        for zone_label, zone_root in roots.items():
            if zone_label == owner_label:
                continue
            for metadata_kind, metadata_path in metadata.items():
                if paths_overlap(zone_root, metadata_path):
                    raise InspectionError(
                        f"{owner_label} Git {metadata_kind} metadata overlaps "
                        f"{zone_label}"
                    )
    metadata_entries = tuple(
        (owner_label, metadata_kind, metadata_path)
        for owner_label, metadata in repositories.items()
        for metadata_kind, metadata_path in metadata.items()
    )
    for index, (first_owner, first_kind, first_path) in enumerate(metadata_entries):
        for second_owner, second_kind, second_path in metadata_entries[index + 1 :]:
            if first_owner == second_owner:
                continue
            if paths_overlap(first_path, second_path):
                raise InspectionError(
                    f"{first_owner} Git {first_kind} metadata overlaps "
                    f"{second_owner} Git {second_kind} metadata"
                )


def inspect(roots, public_only, git_executable):
    """Verify the declared storage topology or raise ``InspectionError``."""
    reject_overlaps(roots)

    publisher = require_git_worktree(
        roots["publisher-root"],
        "publisher-root",
        git_executable,
    )
    integration = None
    if not public_only:
        integration = require_git_worktree(
            roots["integration-root"],
            "integration-root",
            git_executable,
        )
        if same_filesystem_entry(integration["common"], publisher["common"]):
            raise InspectionError(
                "integration-root and publisher-root share a Git common directory"
            )
        if same_filesystem_entry(integration["objects"], publisher["objects"]):
            raise InspectionError(
                "integration-root and publisher-root share a Git object directory"
            )

    repositories = {"publisher-root": publisher}
    if integration is not None:
        repositories["integration-root"] = integration
    reject_git_metadata_overlaps(roots, repositories)
    reject_publisher_alternates(publisher)
    for label in NON_GIT_ZONE_LABELS:
        if label in roots:
            reject_git_zone(roots[label], label)
    for root in roots.values():
        same_filesystem_entry(root, root)
    for metadata in repositories.values():
        for metadata_path in metadata.values():
            same_filesystem_entry(metadata_path, metadata_path)


def path_reference(label, path, show_paths):
    """Render an escaped canonical path or a role-only opaque reference."""
    if show_paths:
        return json.dumps(str(path), ensure_ascii=True)
    return f"<redacted:{label}>"


def print_report(roots, public_only, show_paths, passed, error=None):
    """Print stable claims, including explicit limits, for every inspection result."""
    print("workspace-boundary-inspection")
    print(f"mode: {'public-only' if public_only else 'private-integration'}")
    print(
        f"private-integration-role: "
        f"{'not-declared' if public_only else 'declared'}"
    )
    for label, _attribute in ZONE_ARGUMENTS:
        if label in roots:
            print(
                f"{label}: "
                f"{path_reference(label, roots[label], show_paths)}"
            )
        else:
            print(f"{label}: not-declared")
    print(f"storage-topology: {'verified' if passed else 'failed'}")
    print("storage-topology-scope: declared-roots-and-reported-git-metadata")
    print("inspection-atomicity: point-in-time-non-atomic")
    print("content-admission: not-inspected")
    print("object-file-sharing: not-inspected")
    print("detached-git-worktree-association: not-inspected")
    print("git-executable-authority: policy-bound-not-attested")
    print("git-configuration-authority: not-inspected")
    print("publisher-cleanliness: not-inspected")
    print("capability-isolation: unverified")
    print("publication-admission: not-inspected")
    print("publication-via-inspector: unavailable")
    print("scan: not-inspected")
    print("backup: not-inspected")
    print("instruction-provenance: not-inspected")
    if error is not None:
        print(f"error: {error}")


def build_parser():
    parser = RedactingArgumentParser(
        prog=Path(__file__).name,
        description=(
            "Read-only inspection of declared layered-workspace filesystem and "
            "Git boundaries."
        )
    )
    parser.add_argument(
        "--integration-root",
        help="private integration Git worktree (required unless --public-only)",
    )
    parser.add_argument(
        "--publisher-root",
        required=True,
        help="declared publisher Git worktree",
    )
    parser.add_argument("--restricted-root", help="restricted-data directory")
    parser.add_argument("--raw-root", help="raw-import directory")
    parser.add_argument("--temporary-root", help="temporary-data directory")
    parser.add_argument(
        "--git-executable",
        help=(
            "absolute installer/policy-bound Git executable; fixed platform "
            "candidates are used when omitted"
        ),
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="inspect a publisher without a private integration worktree",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="show escaped canonical paths instead of stable redacted references",
    )
    return parser


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    if arguments.public_only and arguments.integration_root is not None:
        print_report(
            {},
            arguments.public_only,
            arguments.show_paths,
            False,
            "--public-only cannot be combined with --integration-root",
        )
        return 1
    private_zone_arguments = (
        arguments.restricted_root,
        arguments.raw_root,
        arguments.temporary_root,
    )
    if arguments.public_only and any(
        value is not None for value in private_zone_arguments
    ):
        print_report(
            {},
            arguments.public_only,
            arguments.show_paths,
            False,
            "--public-only cannot inspect restricted, raw, or temporary roots",
        )
        return 1
    if not arguments.public_only and arguments.integration_root is None:
        print_report(
            {},
            arguments.public_only,
            arguments.show_paths,
            False,
            "--integration-root is required unless --public-only is explicit",
        )
        return 1

    roots = {}
    try:
        roots = canonical_roots(arguments)
        git_executable = canonical_git_executable(
            arguments.git_executable,
            roots,
        )
        inspect(roots, arguments.public_only, git_executable)
    except InspectionError as error:
        print_report(
            roots,
            arguments.public_only,
            arguments.show_paths,
            False,
            str(error),
        )
        return 1

    print_report(roots, arguments.public_only, arguments.show_paths, True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
