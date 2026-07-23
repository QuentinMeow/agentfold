#!/usr/bin/env python3
"""The reconciler: checks every mechanical harness invariant.

Modes:
  --check         report findings, exit 1 if any (default)
  --file-retries  also write one repair item per finding into
                  message-queue/needs-agent/retries/ (idempotent, keyed by
                  check+subject) and delete reconciler-filed items whose
                  finding cleared
  --fix-index     regenerate memory/index.md from the memory files

Design notes: invariants only (end states, never procedures); stdlib only;
every check no-ops if its folder is absent so adopters can pick pieces.
Registry: CHECKS at the bottom. Adding a check = one function + one entry.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TODAY = datetime.date.today()

QUEUE = REPO / "message-queue"
RETRIES = QUEUE / "needs-agent" / "retries"
TASKS = REPO / "tasks"
TASK_STATUSES = ["0_backlog", "1_in-progress", "2_blocked", "3_in-review", "4_done"]
CONVERSATIONS = REPO / "history" / "conversations"
MEMORY = REPO / "memory"
MEMORY_ZONES = ["facts", "decisions", "lessons", "known-issues"]

# Required bold-key fields per queue folder (relative to message-queue/).
QUEUE_SCHEMAS = {
    "needs-human/decisions": ["Status", "Blocking", "Filed"],
    "needs-human/clarifications": ["Status", "Blocking", "Assumption", "Matters-by", "Filed"],
    "needs-human/reviews": ["Status", "Filed", "Look-at", "Why-you-might-care", "If-you-do-nothing"],
    "needs-agent/requests": [],  # the one free-form queue
    "needs-agent/retries": ["Status", "Filed", "Check", "Subject"],
}

# Line budgets for contract files (progressive-disclosure enforcement).
ROOT_AGENTS_BUDGET = 140
LEAF_AGENTS_BUDGET = 60
SKILL_BUDGET = 70
# The root README is the human landing page — pitch + map, depth linked in handbook/
# (memory/decisions/2026-07-22-root-readme-line-budget.md).
ROOT_README_BUDGET = 140

STALE_QUEUE_DAYS = 30
STALE_TASK_DAYS = 14

TASK_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
REPOSITORY_SCOPE_RE = re.compile(r"^(core|records-only|service:[a-z0-9][a-z0-9-]*)$")
CONVERSATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}[A-Z]{2,5}-[a-z0-9][a-z0-9-]*$")
FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z -]*):\*\*\s*(.*)$", re.M)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# Link check: backticked or markdown-linked repo paths with >= 2 segments.
BACKTICK_RE = re.compile(r"`([^`\s]+/[^`\s]+)`")
MD_LINK_RE = re.compile(r"\]\(([^)#\s]+)\)")
LINK_SKIP_PREFIXES = ("http", "tmp/", "private/", ".")
LINK_SKIP_DIRS = {"templates", "history", "tmp"}  # + memory/decisions (records)


class Finding:
    def __init__(self, check, subject, message, fix):
        self.check, self.subject, self.message, self.fix = check, subject, message, fix

    def __str__(self):
        return f"[{self.check}] {self.subject}: {self.message}"


def fields(path):
    return dict(FIELD_RE.findall(path.read_text(encoding="utf-8")))


def parse_date(value):
    m = DATE_RE.search(value or "")
    return datetime.date.fromisoformat(m.group()) if m else None


def days_old(path):
    mtime = max((p.stat().st_mtime for p in path.rglob("*") if p.is_file()),
                default=path.stat().st_mtime)
    return (TODAY - datetime.date.fromtimestamp(mtime)).days


# ---------------------------------------------------------------- checks

def check_queue_schema():
    for rel, required in QUEUE_SCHEMAS.items():
        folder = QUEUE / rel
        if not folder.is_dir():
            continue
        for item in sorted(folder.glob("*.md")):
            if item.name == "README.md":
                continue
            got = fields(item)
            for key in required:
                if key not in got:
                    yield Finding("queue-schema", item.relative_to(REPO),
                                  f"missing required field **{key}:**",
                                  f"copy the schema from templates/queue/ ({rel})")
            if rel == "needs-human/decisions" and got.get("Blocking", "").startswith("no") \
                    and "Default path" not in got:
                yield Finding("queue-schema", item.relative_to(REPO),
                              "non-blocking decision without a **Default path:**",
                              "state what agents do while the human hasn't answered")
            if rel in ("needs-human/decisions", "needs-human/clarifications") \
                    and "Your answer" not in got:
                yield Finding("queue-schema", item.relative_to(REPO),
                              "missing the literal **Your answer:** line",
                              "append `**Your answer:** ______`")


def check_stale_queue():
    if not QUEUE.is_dir():
        return
    for item in QUEUE.rglob("*.md"):
        if item.name == "README.md" or item.parent == QUEUE:
            continue
        filed = parse_date(fields(item).get("Filed", ""))
        if filed and (TODAY - filed).days > STALE_QUEUE_DAYS:
            yield Finding("stale-queue", item.relative_to(REPO),
                          f"filed {filed}, older than {STALE_QUEUE_DAYS} days",
                          "resolve it, re-surface it in the next reply, or delete if moot")


def check_task_structure():
    if not TASKS.is_dir():
        return
    for entry in TASKS.iterdir():
        if entry.name in ("AGENTS.md", "README.md", "CLAUDE.md") or entry.name.startswith("."):
            continue
        if entry.name not in TASK_STATUSES:
            yield Finding("task-structure", entry.relative_to(REPO),
                          "not a valid status folder", f"one of: {', '.join(TASK_STATUSES)}")
            continue
        for task in entry.iterdir():
            if task.name == "README.md" or task.name.startswith("."):
                continue
            rel = task.relative_to(REPO)
            if not task.is_dir():
                yield Finding("task-structure", rel, "loose file in a status folder",
                              "tasks are folders; move stray files into one")
                continue
            if not TASK_ID_RE.match(task.name):
                yield Finding("task-structure", rel, "task id must be YYYY-MM-DD-kebab-slug",
                              "rename per handbook/naming-conventions.md")
            if not (task / "task.md").is_file():
                yield Finding("task-structure", rel, "missing task.md",
                              "copy templates/task/task.md")
                continue
            got = fields(task / "task.md")
            for key in ("Claimed-by", "Filed", "Repository scope"):
                if key not in got:
                    yield Finding("task-structure", rel / "task.md",
                                  f"missing required field **{key}:**",
                                  "copy the header from templates/task/task.md")
            scope = got.get("Repository scope", "")
            if scope and not REPOSITORY_SCOPE_RE.fullmatch(scope):
                yield Finding("task-structure", rel / "task.md",
                              f"invalid Repository scope {scope!r}",
                              "use core, records-only, or service:<name>")
            if entry.name in ("1_in-progress", "2_blocked", "3_in-review", "4_done"):
                for needed in ("plan.md", "worklog.md"):
                    if not (task / needed).is_file():
                        yield Finding("task-structure", rel, f"missing {needed}",
                                      f"copy templates/task/{needed}")
            if entry.name in ("3_in-review", "4_done") and not (task / "verification.md").is_file():
                yield Finding("task-structure", rel, "missing verification.md",
                              "record real command output per templates/task/verification.md")
            if entry.name == "1_in-progress" and days_old(task) > STALE_TASK_DAYS:
                yield Finding("stale-task", rel,
                              f"untouched for over {STALE_TASK_DAYS} days",
                              "continue it, or move back to 0_backlog and unclaim")


def check_handover_present():
    if not CONVERSATIONS.is_dir():
        return
    for conv in CONVERSATIONS.iterdir():
        if not conv.is_dir():
            continue
        rel = conv.relative_to(REPO)
        if not CONVERSATION_RE.match(conv.name):
            yield Finding("handover-present", rel,
                          "folder name must be YYYY-MM-DD-HHMM<TZ>-kebab-slug (local time + zone)",
                          "rename per history/AGENTS.md")
        if not (conv / "handover.md").is_file():
            yield Finding("handover-present", rel, "conversation without handover.md",
                          "write one from templates/handover.md — the session ritual skipped")


def memory_entries():
    for zone in MEMORY_ZONES:
        folder = MEMORY / zone
        if folder.is_dir():
            for f in sorted(folder.rglob("*.md")):
                if f.name != "README.md":
                    yield zone, f


def check_memory_schema():
    for zone, entry in memory_entries():
        got = fields(entry)
        required = ["Description", "Review-by"]
        if zone == "decisions":
            required += ["Status", "Date", "Decided-by"]
        if zone == "lessons":
            required += ["Area", "Last-confirmed"]
        if zone == "known-issues":
            required += ["Status", "Severity"]
        for key in required:
            if key not in got:
                yield Finding("memory-schema", entry.relative_to(REPO),
                              f"missing required field **{key}:**",
                              f"copy the header from templates/memory/ ({zone})")


def check_memory_expiry():
    for _, entry in memory_entries():
        due = parse_date(fields(entry).get("Review-by", ""))
        if due and due < TODAY:
            yield Finding("memory-expiry", entry.relative_to(REPO),
                          f"Review-by {due} is past",
                          "run the memory-gardener skill: re-verify, compact, or delete")


def generated_index():
    lines = ["<!-- GENERATED by reconcile.py --fix-index — edit the memory files, never this index -->",
             "# Memory index", ""]
    for zone in MEMORY_ZONES:
        entries = [(z, e) for z, e in memory_entries() if z == zone]
        if not entries:
            continue
        lines.append(f"## {zone}")
        for _, entry in entries:
            text = entry.read_text(encoding="utf-8")
            title = next((l[2:] for l in text.splitlines() if l.startswith("# ")), entry.stem)
            desc = fields(entry).get("Description", "").strip()
            lines.append(f"- [{title}]({entry.relative_to(MEMORY)}) — {desc}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def check_memory_index():
    index = MEMORY / "index.md"
    if not MEMORY.is_dir():
        return
    if not index.is_file() or index.read_text(encoding="utf-8") != generated_index():
        yield Finding("memory-index", index.relative_to(REPO),
                      "index does not match the memory files",
                      "run: python3 automation/reconcile/reconcile.py --fix-index")


def strip_fences(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def check_links():
    for md in REPO.rglob("*.md"):
        rel = md.relative_to(REPO)
        parts = rel.parts
        if parts[0] in LINK_SKIP_DIRS or parts[0].startswith("."):
            continue
        if parts[:2] == ("memory", "decisions"):  # immutable records may cite dead paths
            continue
        if parts[:3] == ("message-queue", "needs-agent", "retries"):
            continue  # repair items cite broken/deleted subjects by design
        text = strip_fences(md.read_text(encoding="utf-8"))
        candidates = set(BACKTICK_RE.findall(text)) | set(MD_LINK_RE.findall(text))
        for cand in sorted(candidates):
            if cand.startswith(LINK_SKIP_PREFIXES) or any(c in cand for c in "*<>{}$"):
                continue
            if cand.count("/") < 1 or (cand.count("/") == 1 and cand.endswith("/")):
                continue
            if not re.fullmatch(r"[\w./-]+", cand):
                continue
            if (REPO / cand).exists() or (md.parent / cand).resolve().exists():
                continue
            yield Finding("link-check", rel, f"`{cand}` does not exist",
                          "fix the path, create the target, or unquote if not a path")


def check_agents_budget():
    for md in REPO.rglob("*.md"):
        parts = md.relative_to(REPO).parts
        if parts[0].startswith(".") or parts[0] == "templates":  # schemas, not live contracts
            continue
        lines = len(md.read_text(encoding="utf-8").splitlines())
        budget = None
        if md.name == "AGENTS.md":
            budget = ROOT_AGENTS_BUDGET if md.parent == REPO else LEAF_AGENTS_BUDGET
        elif md.name == "SKILL.md":
            budget = SKILL_BUDGET
        elif md.name == "README.md" and md.parent == REPO:
            budget = ROOT_README_BUDGET
        if budget and lines > budget:
            yield Finding("agents-budget", md.relative_to(REPO),
                          f"{lines} lines exceeds the {budget}-line budget",
                          "move depth into a linked doc (handbook/principles/progressive-disclosure.md)")


def check_mode_valid():
    root = REPO / "AGENTS.md"
    if not root.is_file():
        return
    mode = fields(root).get("Collaboration mode", "").strip("`* ").split("`")[0].strip("` ")
    if mode not in ("autonomous", "async", "pair"):
        yield Finding("mode-valid", "AGENTS.md",
                      f"collaboration mode {mode!r} is not autonomous|async|pair",
                      "fix the **Collaboration mode:** line")


def check_roadmap_fresh():
    current = REPO / "roadmap" / "current-state.md"
    done = TASKS / "4_done"
    if not current.is_file() or not done.is_dir():
        return
    updated = parse_date(fields(current).get("Last-updated", ""))
    newest = max((parse_date(t.name) for t in done.iterdir()
                  if t.is_dir() and parse_date(t.name)), default=None)
    if updated and newest and updated < newest:
        yield Finding("roadmap-fresh", "roadmap/current-state.md",
                      f"Last-updated {updated} predates the newest done task ({newest})",
                      "re-read current-state.md against reality and bump Last-updated")


CHECKS = {
    "queue-schema": check_queue_schema,
    "stale-queue": check_stale_queue,
    "task-structure": check_task_structure,
    "handover-present": check_handover_present,
    "memory-schema": check_memory_schema,
    "memory-expiry": check_memory_expiry,
    "memory-index": check_memory_index,
    "link-check": check_links,
    "agents-budget": check_agents_budget,
    "mode-valid": check_mode_valid,
    "roadmap-fresh": check_roadmap_fresh,
}


# ---------------------------------------------------------- retry filing

def finding_key(f):
    slug = re.sub(r"[^a-z0-9]+", "-", str(f.subject).lower()).strip("-")
    return f"reconcile-{f.check}-{slug}"[:80]


def file_retries(findings):
    RETRIES.mkdir(parents=True, exist_ok=True)
    wanted = {}
    for f in findings:
        wanted[finding_key(f)] = f
    for key, f in wanted.items():
        (RETRIES / f"{key}.md").write_text(
            f"# {f.message}\n\n"
            f"**Status:** open\n"
            f"**Filed:** {TODAY}, by reconciler\n"
            f"**Check:** {f.check}\n"
            f"**Subject:** `{f.subject}`\n\n"
            f"## Broken invariant\n\n{f.message} (subject: `{f.subject}`)\n\n"
            f"## Fix\n\n{f.fix}\n", encoding="utf-8")
    removed = 0
    for item in RETRIES.glob("reconcile-*.md"):
        if item.stem not in wanted:
            item.unlink()
            removed += 1
    return len(wanted), removed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report findings (default)")
    parser.add_argument("--file-retries", action="store_true",
                        help="write repair items for findings; gc fixed ones")
    parser.add_argument("--fix-index", action="store_true",
                        help="regenerate memory/index.md")
    args = parser.parse_args(argv)

    if args.fix_index:
        (MEMORY / "index.md").write_text(generated_index(), encoding="utf-8")
        print("memory/index.md regenerated")
        if not (args.check or args.file_retries):
            return 0

    findings = [f for check in CHECKS.values() for f in check()]
    for f in findings:
        print(f)
        print(f"    fix: {f.fix}")

    if args.file_retries:
        filed, removed = file_retries(findings)
        print(f"retries: {filed} filed/refreshed, {removed} cleared")

    print(f"reconcile: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
