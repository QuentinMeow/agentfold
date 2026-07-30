"""Build test fixture Git history in process instead of spawning add and commit.

The suite is bound by process creation, not computation, and fixture setup is the
largest remaining source of spawns: the repository tests build history with `git add`
and `git commit` purely so they can read it back. This module writes the same loose
objects and the same index entries from Python, so a fixture commit costs no spawn.

Real Git reads everything written here, because everything written here is what real
Git writes: `automation/tests/test_reconcile_queue.py` byte-compares both sides for
identical content, and keeps the boundary of what stays on real Git.

Scope, deliberately narrow so anything unsupported fails loudly rather than silently
producing different history than real Git would:

- SHA-1 repositories only. A `--object-format=sha256` repository uses a different
  object identifier algorithm and must keep using real Git.
- Index versions 2 and 3 are read; version 2 is written. Version 4 raises.
- Ignore rules are not interpreted: `stage` refuses a worktree carrying `.gitignore`
  so the caller falls back to real `git add`.
- Only resolved (stage 0) index entries can be committed, as in real Git.
"""

import hashlib
import os
import stat
import struct
import zlib

# A pinned identity and a pinned clock make fixture object identifiers reproducible
# run to run. The identity matches the one the fixture skeleton configures.
FIXTURE_NAME = "Test"
FIXTURE_EMAIL = "test@example.invalid"
FIXTURE_TIMEZONE = "+0000"
# 2026-03-04T05:46:40Z: a fixed point, far from any real clock reading.
FIXTURE_EPOCH = 1772603200
FIXTURE_INTERVAL = 60

INDEX_SIGNATURE = b"DIRC"
INDEX_WRITE_VERSION = 2
# ctime, mtime, dev, ino, mode, uid, gid, size, then the object id and the flags.
INDEX_ENTRY_HEAD = struct.Struct(">10I20sH")
INDEX_ENTRY_STAGE = 0x3000
INDEX_ENTRY_EXTENDED = 0x4000
INDEX_NAME_LENGTH_MASK = 0x0FFF
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
# Git compresses loose objects at Z_BEST_SPEED unless core.compression says otherwise.
LOOSE_OBJECT_COMPRESSION = 1

REGULAR_MODE = 0o100644
EXECUTABLE_MODE = 0o100755
SYMLINK_MODE = 0o120000
TREE_MODE = b"40000"


class FixtureGitError(Exception):
    """Raised when the fixture writer will not speak for real Git."""


def object_payload(kind, content):
    """Return the exact bytes Git hashes: type, size, NUL, then the content."""
    return b"%s %d\0%s" % (kind, len(content), content)


def object_id(kind, content):
    """Return the object identifier Git would give this content."""
    return hashlib.sha1(object_payload(kind, content)).hexdigest()


def write_object(git_dir, kind, content):
    """Write one zlib-compressed loose object and return its identifier."""
    payload = object_payload(kind, content)
    oid = hashlib.sha1(payload).hexdigest()
    path = git_dir / "objects" / oid[:2] / oid[2:]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.parent / (oid[2:] + ".tmp")
        pending.write_bytes(zlib.compress(payload, LOOSE_OBJECT_COMPRESSION))
        # Git leaves loose objects read-only; matching it keeps the two
        # repositories the conformance test compares indistinguishable.
        os.chmod(str(pending), 0o444)
        os.replace(str(pending), str(path))
    return oid


def read_object(git_dir, oid):
    """Return the (type, content) of one loose object."""
    path = git_dir / "objects" / oid[:2] / oid[2:]
    if not path.exists():
        raise FixtureGitError(
            "{0} is not a loose object; the fixture writer only reads loose "
            "objects".format(oid)
        )
    payload = zlib.decompress(path.read_bytes())
    header, _, content = payload.partition(b"\0")
    kind, _, size = header.partition(b" ")
    if int(size) != len(content):
        raise FixtureGitError("{0} declares a size it does not carry".format(oid))
    return kind, content


def write_tree(git_dir, entries):
    """Write the tree objects for staged entries and return the root identifier."""
    root = {}
    for name, mode, oid in entries:
        parts = name.split(b"/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise FixtureGitError(
                    "{0} is both a file and a directory".format(name.decode())
                )
        node[parts[-1]] = (mode, oid)
    return _write_tree_node(git_dir, root)


def _write_tree_node(git_dir, node):
    items = []
    for name, value in node.items():
        if isinstance(value, dict):
            # Git sorts a directory as if its name ended in a slash.
            items.append((name + b"/", TREE_MODE, name, _write_tree_node(git_dir, value)))
        else:
            mode, oid = value
            items.append((name, b"%o" % mode, name, oid))
    items.sort(key=lambda item: item[0])
    content = b"".join(
        b"%s %s\0%s" % (mode, name, bytes.fromhex(oid))
        for _sort_key, mode, name, oid in items
    )
    return write_object(git_dir, b"tree", content)


def clean_message(parts):
    """Apply the whitespace cleanup `git commit -m` applies to its message."""
    text = "\n\n".join(parts)
    lines = [line.rstrip() for line in text.split("\n")]
    collapsed = []
    for line in lines:
        if not line and (not collapsed or not collapsed[-1]):
            continue
        collapsed.append(line)
    while collapsed and not collapsed[-1]:
        collapsed.pop()
    if not collapsed:
        return b""
    return ("\n".join(collapsed) + "\n").encode("utf-8")


def write_commit(git_dir, tree, parents, message, timestamp):
    """Write one commit object with the pinned identity and the given clock."""
    stamp = "{0} <{1}> {2} {3}".format(
        FIXTURE_NAME, FIXTURE_EMAIL, timestamp, FIXTURE_TIMEZONE
    )
    lines = ["tree " + tree]
    lines.extend("parent " + parent for parent in parents)
    lines.append("author " + stamp)
    lines.append("committer " + stamp)
    header = ("\n".join(lines) + "\n\n").encode("utf-8")
    return write_object(git_dir, b"commit", header + message)


def commit_time(git_dir, oid):
    """Return the committer timestamp recorded in one commit object."""
    kind, content = read_object(git_dir, oid)
    if kind != b"commit":
        raise FixtureGitError("{0} is not a commit".format(oid))
    for line in content.split(b"\n"):
        if line.startswith(b"committer "):
            return int(line.rsplit(b" ", 2)[-2])
        if not line:
            break
    raise FixtureGitError("{0} records no committer".format(oid))


def read_head(git_dir):
    """Return the branch reference HEAD points at, or None when it is detached."""
    text = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if text.startswith("ref: "):
        return text[len("ref: "):]
    return None


def read_ref(git_dir, reference):
    """Resolve one reference through the loose file and then packed-refs."""
    loose = git_dir / reference
    if loose.exists():
        return loose.read_text(encoding="utf-8").strip()
    packed = git_dir / "packed-refs"
    if packed.exists():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or line.startswith("^"):
                continue
            oid, _, name = line.partition(" ")
            if name.strip() == reference:
                return oid
    return None


def head_commit(git_dir):
    """Return the commit HEAD resolves to, or None on an unborn branch."""
    reference = read_head(git_dir)
    if reference is None:
        return (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    return read_ref(git_dir, reference)


def update_head(git_dir, oid):
    """Point HEAD, or the branch it names, at one commit."""
    reference = read_head(git_dir)
    target = git_dir / "HEAD" if reference is None else git_dir / reference
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(oid + "\n", encoding="utf-8")


def merge_parents(git_dir):
    """Return the extra parents an uncommitted merge has recorded."""
    merge_head = git_dir / "MERGE_HEAD"
    if not merge_head.exists():
        return []
    return merge_head.read_text(encoding="utf-8").split()


def clear_merge_state(git_dir):
    """Remove the state `git commit` clears once a merge is recorded."""
    for name in ("MERGE_HEAD", "MERGE_MSG", "MERGE_MODE"):
        path = git_dir / name
        if path.exists():
            path.unlink()


def read_index(git_dir):
    """Return the index as a list of (name, mode, oid, stat tuple, stage)."""
    path = git_dir / "index"
    if not path.exists():
        return []
    data = path.read_bytes()
    if data[:4] != INDEX_SIGNATURE:
        raise FixtureGitError("the index does not start with DIRC")
    version, count = struct.unpack(">II", data[4:12])
    if version not in (2, 3):
        raise FixtureGitError(
            "index version {0} is not one the fixture writer reads".format(version)
        )
    entries = []
    offset = 12
    for _position in range(count):
        fields = INDEX_ENTRY_HEAD.unpack_from(data, offset)
        flags = fields[11]
        name_start = offset + INDEX_ENTRY_HEAD.size
        if flags & INDEX_ENTRY_EXTENDED:
            name_start += 2
        end = data.index(b"\0", name_start)
        name = data[name_start:end]
        entries.append((
            name,
            fields[6],
            fields[10].hex(),
            fields[:6] + fields[7:10],
            (flags & INDEX_ENTRY_STAGE) >> 12,
        ))
        # Entries are padded with one to eight NUL bytes onto an eight-byte edge.
        offset += ((name_start - offset) + len(name) + 8) & ~7
    return entries


def write_index(git_dir, entries):
    """Write a version 2 index holding exactly these entries."""
    body = struct.pack(">4sII", INDEX_SIGNATURE, INDEX_WRITE_VERSION, len(entries))
    chunks = [body]
    for name, mode, oid, stat_data, stage in sorted(entries, key=lambda e: (e[0], e[4])):
        flags = min(len(name), INDEX_NAME_LENGTH_MASK) | (stage << 12)
        head = INDEX_ENTRY_HEAD.pack(
            stat_data[0], stat_data[1], stat_data[2], stat_data[3],
            stat_data[4], stat_data[5], mode,
            stat_data[6], stat_data[7], stat_data[8],
            bytes.fromhex(oid), flags,
        )
        padding = ((INDEX_ENTRY_HEAD.size + len(name) + 8) & ~7) - (
            INDEX_ENTRY_HEAD.size + len(name)
        )
        chunks.append(head + name + b"\0" * padding)
    payload = b"".join(chunks)
    path = git_dir / "index"
    pending = git_dir / "index.fixture-tmp"
    pending.write_bytes(payload + hashlib.sha1(payload).digest())
    os.replace(str(pending), str(path))


def stat_fields(path):
    """Return the truncated stat data Git records for one worktree path."""
    info = os.lstat(str(path))
    ctime_s, ctime_ns = divmod(info.st_ctime_ns, 1000000000)
    mtime_s, mtime_ns = divmod(info.st_mtime_ns, 1000000000)
    values = (
        ctime_s, ctime_ns, mtime_s, mtime_ns,
        info.st_dev, info.st_ino,
        info.st_uid, info.st_gid, info.st_size,
    )
    return tuple(value & 0xFFFFFFFF for value in values), info


def worktree_entry(git_dir, path):
    """Write the blob for one worktree path and return its index entry parts."""
    stat_data, info = stat_fields(path)
    if stat.S_ISLNK(info.st_mode):
        content = os.readlink(str(path)).encode("utf-8")
        mode = SYMLINK_MODE
    else:
        content = path.read_bytes()
        mode = EXECUTABLE_MODE if info.st_mode & 0o111 else REGULAR_MODE
    return mode, write_object(git_dir, b"blob", content), stat_data


def worktree_paths(root):
    """List every worktree path, or raise when ignore rules would apply."""
    found = []
    _scan(root, root, b"", found)
    return sorted(found)


def _scan(root, directory, prefix, found):
    with os.scandir(str(directory)) as listing:
        children = sorted(listing, key=lambda item: item.name)
    for entry in children:
        if not prefix and entry.name == ".git":
            continue
        if entry.name == ".gitignore":
            raise FixtureGitError("the worktree carries ignore rules")
        name = prefix + os.fsencode(entry.name)
        if entry.is_symlink() or not entry.is_dir():
            found.append(name)
        else:
            _scan(root, directory / entry.name, name + b"/", found)


def _selected(name, pathspec):
    if pathspec is None:
        return True
    return name == pathspec or name.startswith(pathspec + b"/")


def stage(root, pathspecs):
    """Stage the worktree the way `git add` does, without spawning it."""
    git_dir = root / ".git"
    present = worktree_paths(root)
    entries = {entry[0]: entry for entry in read_index(git_dir)}
    specs = [None if spec in (".", "-A") else os.fsencode(str(spec).rstrip("/"))
             for spec in pathspecs]
    for pathspec in specs:
        kept = {name for name in present if _selected(name, pathspec)}
        stale = [name for name in entries if _selected(name, pathspec)]
        if pathspec is not None and not kept and not stale:
            # Real Git refuses a pathspec that matches nothing; so does this.
            raise FixtureGitError(
                "{0} matched no worktree path and no index entry".format(
                    os.fsdecode(pathspec)
                )
            )
        for name in stale:
            if name not in kept:
                del entries[name]
        for name in sorted(kept):
            mode, oid, stat_data = worktree_entry(git_dir, root / os.fsdecode(name))
            entries[name] = (name, mode, oid, stat_data, 0)
    write_index(git_dir, list(entries.values()))


def commit(root, messages):
    """Record the index as a commit the way `git commit -m` does."""
    git_dir = root / ".git"
    entries = read_index(git_dir)
    for entry in entries:
        if entry[4]:
            raise FixtureGitError("the index still holds an unresolved path")
    tree = write_tree(git_dir, [(name, mode, oid) for name, mode, oid, _s, _t in entries])
    parents = []
    head = head_commit(git_dir)
    if head:
        parents.append(head)
    extra = merge_parents(git_dir)
    parents.extend(extra)
    if not extra and tree == _parent_tree(git_dir, parents):
        raise FixtureGitError("nothing to commit, as real Git would also report")
    timestamp = FIXTURE_EPOCH
    if parents:
        timestamp = max(commit_time(git_dir, parent) for parent in parents)
        timestamp += FIXTURE_INTERVAL
    oid = write_commit(git_dir, tree, parents, clean_message(messages), timestamp)
    update_head(git_dir, oid)
    clear_merge_state(git_dir)
    return oid


def _parent_tree(git_dir, parents):
    if not parents:
        return EMPTY_TREE
    _kind, content = read_object(git_dir, parents[0])
    return content.split(b"\n", 1)[0].split(b" ", 1)[1].decode("ascii")


def run(root, arguments):
    """Serve `git add` and `git commit` in process, or decline the invocation.

    Returning None means the caller must spawn real Git: the invocation used a
    flag or a repository shape this writer deliberately does not speak for.
    """
    if not arguments:
        return None
    command, rest = arguments[0], [str(item) for item in arguments[1:]]
    if not (root / ".git").is_dir():
        return None
    try:
        if command == "add":
            if not rest or any(
                item.startswith("-") and item != "-A" for item in rest
            ):
                return None
            stage(root, rest)
            return ""
        if command == "commit":
            if len(rest) < 2 or len(rest) % 2 or set(rest[::2]) != {"-m"}:
                return None
            commit(root, rest[1::2])
            return ""
    except FixtureGitError:
        return None
    return None
