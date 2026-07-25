#!/usr/bin/env python3
"""Mine evolutionary coupling between Markdown contracts out of Git history.

Two files that keep changing in the same commit depend on each other whether or not
either one says so. This walks every commit, counts directed file pairs, and reports
the pairs above a support and confidence floor, with their shared commit subjects as
evidence -- already-written, never-stale rationale that costs nothing to collect.

The output is advisory, not a gate, and this is deliberately not a reconciler check:
reconciler findings carry no severity, so every finding blocks, and a mined coupling is
judgment rather than a defect. The report verb therefore always exits 0.

Verdicts append to automation/cochange-ledger.txt so a dismissal outlives the agent
that made it and a rejected pair never re-surfaces. The ledger's rejection rate is the
effective-false-positive rate -- any report the user chose not to act on -- which the
status verb judges against published governance thresholds: under 10% on target, at or
above 10% the check is on probation, above 25% it is turned off.

Every number here is provisional. This repository holds days rather than years of
history, and the published work this technique borrows from discards the first few
hundred change records as warm-up, so supports and confidences will move as history
grows in a direction nobody can predict from here. Mining is also indifferent to
quality: it learns established bad practice as readily as good, so a reported pair may
be a duplication worth removing rather than a dependency worth declaring.
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "automation" / "cochange-ledger.txt"
LEDGER_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})\t(accept|reject)\t([^\t]+)\t([^\t]+)\t([^\t]*)(?:\t(.*))?$"
)
LEDGER_HEADER = """# AgentFold co-change verdict ledger -- append-only, one verdict per line.
#
# Written by automation/mine_cochange.py (verbs accept, reject); read by its report and
# status verbs. A directed pair with a verdict never re-surfaces in the report: rejected
# means dismissed, accepted means already declared, and neither is still a candidate.
# That is what makes a decision durable once the agent that made it is gone. The share of
# verdicts that are rejections is the effective-false-positive rate the governance
# thresholds in docs/designs/markdown-edge-graph.md are measured against.
#
# Format: tab-separated fields, one line per verdict, never rewritten or reordered.
#
#   <date>  <verdict>  <a>  <b>  <reason>
#
#   date     ISO YYYY-MM-DD, the day the verdict was recorded
#   verdict  accept (the coupling is real) or reject (the report was not acted on)
#   a        the file that changed
#   b        the file the candidate said to review; the direction a -> b is recorded
#            explicitly, so a verdict on a -> b says nothing about b -> a
#   reason   one line, required for a rejection and optional for an acceptance; tabs
#            and newlines are collapsed to spaces before writing
#
# One regex parses every line:
#   ^(\\d{4}-\\d{2}-\\d{2})\\t(accept|reject)\\t([^\\t]+)\\t([^\\t]+)\\t([^\\t]*)(?:\\t(.*))?$
# A sixth and later field may be appended by a future version; this parser keeps the
# remainder as one opaque group, so lines written today keep parsing unchanged.
#
# Blank lines and lines beginning with # are comments.
"""
SUPPORT_FLOOR = 3
CONFIDENCE_FLOOR = 0.8
COMMIT_CAP = 40
REPORT_CAP = 10
EVIDENCE_CAP = 3
# Records, not live contracts: their coupling is an artifact of when they were written.
# Narrower than the reconciler's link-check exemption, which also skips templates/ --
# a template that silently restates a contract it never names is exactly what mining is
# for, so templates stay in scope here.
SCOPE_EXCLUDES = (
    "history/",
    "memory/decisions/",
    "message-queue/needs-agent/retries/",
    "tmp/",
)
# Files the repository contract requires to change every session, so their coupling is
# mandated and carries no information. Derived from the root contract: the end-of-session
# ritual updates roadmap/current-state.md and the task's worklog, and memory/index.md is
# generated rather than authored. Note that fnmatch's * crosses directory separators.
STOP_LIST = ("memory/index.md", "roadmap/current-state.md", "tasks/*/*/worklog.md")
RANKING = "confidence desc, support desc, source path asc, target path asc"


def git(*args, repo=None):
    """Resolve REPO at call time so a caller (or a test) can point this elsewhere."""
    result = subprocess.run(["git", *args], cwd=repo or REPO, capture_output=True,
                            check=False)
    if result.returncode:
        detail = result.stderr.decode("utf-8", "surrogateescape").strip()
        raise RuntimeError(detail or f"git {' '.join(args)} failed")
    return result.stdout.decode("utf-8", "surrogateescape")


def printable(text):
    """Paths and subjects may hold bytes no encoding round-trips; never crash on them."""
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


def walk_commits(log):
    """Yield (subject, changed paths) per commit from `-z --name-status` output.

    Tokens arrive NUL-separated as ('', hash, subject, status, path[, path]...). A
    rename touches both names; a copy leaves its source untouched, so only the
    destination counts.
    """
    tokens = log.split("\0")
    index = 0
    while index < len(tokens):
        if tokens[index] != "" or index + 2 >= len(tokens):
            index += 1
            continue
        subject = tokens[index + 2]
        index += 3
        paths = []
        while index < len(tokens) and tokens[index] != "":
            status = tokens[index].lstrip("\n")
            index += 1
            if not status:
                continue
            wanted = 2 if status[0] in ("R", "C") else 1
            record = tokens[index:index + wanted]
            index += len(record)
            paths.extend(record[1:] if status[0] == "C" else record)
        yield subject, paths


def in_scope(path, excludes):
    return (
        path.endswith(".md")
        and not path.startswith(".")
        and not path.startswith(tuple(excludes))
    )


def stopped(path, patterns):
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def same_directory(first, second):
    return first.rpartition("/")[0] == second.rpartition("/")[0]


def mine(support_floor=SUPPORT_FLOOR, confidence_floor=CONFIDENCE_FLOOR,
         commit_cap=COMMIT_CAP, stop_list=STOP_LIST, excludes=SCOPE_EXCLUDES,
         ledger=None, repo=None):
    """Count directed co-change pairs. Enumerated from git, never the filesystem."""
    try:
        log = git("log", "--root", "-z", "--name-status", "--format=%x00%H%x00%s",
                  repo=repo)
    except RuntimeError as error:
        reason = (str(error).splitlines() or [""])[0]
        return {"available": False, "reason": reason, "candidates": [], "commits": 0,
                "scoped": 0, "tangled": 0, "files": 0, "suppressed": 0, "stale": 0,
                "total": 0}
    touched = Counter()
    pairs = Counter()
    evidence = defaultdict(list)
    commits = scoped_commits = tangled = 0
    for subject, paths in walk_commits(log):
        commits += 1
        if len(paths) > commit_cap:
            tangled += 1
            continue
        files = sorted(
            {p for p in paths if in_scope(p, excludes) and not stopped(p, stop_list)}
        )
        if not files:
            continue
        scoped_commits += 1
        for name in files:
            touched[name] += 1
        for offset, first in enumerate(files):
            for second in files[offset + 1:]:
                pairs[(first, second)] += 1
                evidence[(first, second)].append(subject.strip())
    # A coupling to a path that is no longer tracked cannot be acted on, and this
    # repository deletes queue items and moves task folders by design, so history is
    # full of dead paths. Liveness filters what is reported, never the denominator.
    live = {name for name in git("ls-files", "-z", repo=repo).split("\0") if name}
    decided = {(a, b) for _, a, b, _, _ in (ledger or [])}
    candidates, suppressed, stale = [], 0, 0
    for pair in sorted(pairs):
        support = pairs[pair]
        first, second = pair
        if support < support_floor or same_directory(first, second):
            continue
        if first not in live or second not in live:
            stale += 1
            continue
        # Confidence is asymmetric -- P(B | A) is not P(A | B) -- and that asymmetry is
        # what gives the mined graph its direction, so each direction is its own
        # candidate. The denominator counts only commits this walk kept, and the stored
        # value is rounded to the two printed decimals so the ranking matches the report.
        for source, target in ((first, second), (second, first)):
            confidence = support / touched[source]
            if confidence < confidence_floor:
                continue
            if (source, target) in decided:
                suppressed += 1
                continue
            candidates.append({
                "source": source,
                "target": target,
                "confidence": float(f"{confidence:.2f}"),
                "support": support,
                "source_commits": touched[source],
                "subjects": evidence[pair],
            })
    candidates.sort(key=lambda c: (-c["confidence"], -c["support"], c["source"],
                                   c["target"]))
    return {"available": True, "candidates": candidates, "commits": commits,
            "scoped": scoped_commits, "tangled": tangled, "files": len(touched),
            "suppressed": suppressed, "stale": stale, "total": len(candidates)}


def load_ledger(path=None):
    """Return (verdicts, malformed lines); a missing ledger is simply empty."""
    verdicts, malformed = [], []
    try:
        text = (path or LEDGER).read_text(encoding="utf-8", errors="surrogateescape")
    except OSError:
        return verdicts, malformed
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        matched = LEDGER_RE.match(line)
        if matched:
            verdicts.append((matched.group(2), matched.group(3), matched.group(4),
                             matched.group(1), matched.group(5)))
        else:
            malformed.append(line)
    return verdicts, malformed


def append_verdict(verdict, source, target, reason, when, path=None):
    path = path or LEDGER
    field = " ".join(reason.split())
    line = f"{when}\t{verdict}\t{source}\t{target}\t{field}\n"
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="surrogateescape")
    else:
        existing = LEDGER_HEADER
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as fh:
        fh.write(existing + line)
    return line


def governance(verdicts):
    """The rejection rate is the effective-false-positive rate. Integer arithmetic."""
    total = len(verdicts)
    rejected = sum(1 for verdict, *_ in verdicts if verdict == "reject")
    if not total:
        return total, rejected, None, "unmeasured"
    if rejected * 4 > total:
        state = "off"
    elif rejected * 10 >= total:
        state = "probation"
    else:
        state = "on-target"
    return total, rejected, rejected / total, state


GOVERNANCE_TEXT = {
    "unmeasured": "no verdict recorded yet -- target under 10%, probation at or above "
                  "10%, turned off above 25%",
    "on-target": "on target -- under the 10% effective-false-positive threshold",
    "probation": "probation -- at or above 10%, the check runs on notice until the rate "
                 "falls",
    "off": "turn it off -- above 25%, the threshold at which such a check is withdrawn",
}


def report_lines(result, args, verdicts, malformed):
    total, rejected, rate, state = governance(verdicts)
    limit = args.limit if args.limit > 0 else result["total"]
    shown = result["candidates"][:limit]
    rate_text = "n/a" if rate is None else f"{rate * 100:.1f}%"
    lines = [
        "co-change candidates (advisory, provisional)",
        f"  floors      support >= {args.support} commit(s), "
        f"confidence >= {args.confidence:.2f}",
        f"  commit cap  {args.commit_cap} changed path(s); {result['tangled']} "
        f"tangled commit(s) skipped",
        f"  history     {result['commits']} commit(s) walked, {result['scoped']} in "
        f"scope, {result['files']} file(s) seen",
        f"  scope       *.md outside {', '.join(args.excludes) or '(nothing)'}",
        f"  stop-list   {', '.join(args.stop_list) or '(empty)'}",
        f"  dropped     {result['stale']} pair(s) naming a path no longer tracked, "
        f"{result['suppressed']} already in the ledger",
        f"  ledger      {LEDGER.relative_to(REPO).as_posix()} -- {total} verdict(s), "
        f"{rejected} rejected, rate {rate_text}",
        f"  ranking     {RANKING}",
        "",
    ]
    if malformed:
        # A hand-edited typo would silently stop suppressing a dismissed pair.
        lines.insert(-1, f"  warning     {len(malformed)} unparseable ledger line(s); "
                         "their verdicts suppress nothing")
    if not result["available"]:
        lines.append("no history to mine (unborn HEAD or no repository); nothing to say")
        return lines
    if not shown:
        lines.append("no pair clears both floors; that is an answer, not a clean bill "
                     "of health")
    for position, candidate in enumerate(shown, 1):
        lines.append(
            f"{position:2d}. {printable(candidate['source'])} "
            f"({candidate['source_commits']} commit(s))"
        )
        lines.append(
            f"    -> also review {printable(candidate['target'])}  "
            f"conf {candidate['confidence']:.2f}  support {candidate['support']}"
        )
        subjects = candidate["subjects"][:args.evidence]
        for offset, subject in enumerate(subjects):
            label = "because" if offset == 0 else "       "
            lines.append(f"       {label}  {printable(subject)}")
        extra = len(candidate["subjects"]) - len(subjects)
        if extra > 0:
            lines.append(f"                 +{extra} more shared commit(s)")
    dropped = result["total"] - len(shown)
    lines.append("")
    lines.append(
        f"{result['total']} candidate(s) clear the floors; {len(shown)} shown, "
        f"{dropped} dropped by the ranking above -- not \"nothing else couples\"."
    )
    if dropped:
        lines.append("  see them all: --limit 0")
    lines.append(
        f"provisional: {result['commits']} commit(s) of history, and the published work "
        "this borrows from discards the first few hundred change records as warm-up."
    )
    lines.append(
        "dismiss or keep one: mine_cochange.py accept <a> <b> | "
        "reject <a> <b> --reason \"...\""
    )
    return lines


def cmd_report(args):
    verdicts, malformed = load_ledger()
    result = mine(args.support, args.confidence, args.commit_cap, args.stop_list,
                  args.excludes, ledger=verdicts)
    if args.json:
        limit = args.limit if args.limit > 0 else result["total"]
        payload = dict(result)
        payload["shown"] = payload["candidates"][:limit]
        payload["ranking"] = RANKING
        payload["provisional"] = True
        payload["ledger_verdicts"] = len(verdicts)
        payload["ledger_malformed"] = len(malformed)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("\n".join(report_lines(result, args, verdicts, malformed)))
    return 0  # advisory: judgment, not a defect


def cmd_verdict(args):
    if not args.a or not args.b or args.a == args.b:
        print("[cochange] two distinct paths are required")
        return 2
    if any(character in field for field in (args.a, args.b) for character in "\t\n"):
        print("[cochange] a path with a tab or newline cannot be recorded")
        return 2
    reason = " ".join((args.reason or "").split())
    if args.verdict == "reject" and not reason:
        print("[cochange] --reason is required for a rejection")
        return 2
    verdicts, _ = load_ledger()
    for recorded, source, target, when, _ in verdicts:
        if (source, target) == (args.a, args.b):
            print(f"[cochange] {args.a} -> {args.b} already recorded as {recorded} "
                  f"on {when}; the ledger is append-only and never re-decided")
            return 2
    append_verdict(args.verdict, args.a, args.b, reason, args.date)
    verdicts, _ = load_ledger()
    total, rejected, rate, state = governance(verdicts)
    rate_text = "n/a" if rate is None else f"{rate * 100:.1f}%"
    print(f"recorded {args.verdict}: {printable(args.a)} -> {printable(args.b)} "
          f"({args.date})" + (f" -- {printable(reason)}" if reason else ""))
    print(f"ledger: {total} verdict(s), {rejected} rejected, rate {rate_text} ({state})")
    return 0


def cmd_status(args):
    verdicts, malformed = load_ledger()
    total, rejected, rate, state = governance(verdicts)
    rate_text = "n/a" if rate is None else f"{rate * 100:.1f}%"
    if args.json:
        print(json.dumps({
            "accepted": total - rejected,
            "effective_false_positive_rate": None if rate is None
            else float(f"{rate:.4f}"),
            "governance": state,
            "ledger": LEDGER.relative_to(REPO).as_posix(),
            "malformed_lines": len(malformed),
            "rejected": rejected,
            "verdicts": total,
        }, indent=2, sort_keys=True))
    else:
        print(f"ledger      {LEDGER.relative_to(REPO).as_posix()}")
        print(f"verdicts    {total} ({total - rejected} accepted, {rejected} rejected)")
        print(f"eff. FP     {rate_text} -- any report the user chose not to act on")
        print(f"governance  {state}: {GOVERNANCE_TEXT[state]}")
        if malformed:
            print(f"malformed   {len(malformed)} unparseable line(s); fix them by hand")
    return 0 if state in ("unmeasured", "on-target") else 1


def csv_list(value):
    return tuple(item for item in (part.strip() for part in value.split(",")) if item)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    verbs = parser.add_subparsers(dest="verb", required=True)
    report = verbs.add_parser(
        "report", help="rank mined co-change candidates (exit 0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Advisory: always exits 0. Every support and confidence is provisional --\n"
               "this repository holds days rather than years of history, and the published\n"
               "work this borrows from discards the first few hundred change records as\n"
               "warm-up. Pairs already carrying a ledger verdict, pairs naming an untracked\n"
               f"path, and pairs inside one directory are never reported.\nRanking: {RANKING}.",
    )
    report.add_argument("--support", type=int, default=SUPPORT_FLOOR,
                        help=f"minimum shared commits (default {SUPPORT_FLOOR})")
    report.add_argument("--confidence", type=float, default=CONFIDENCE_FLOOR,
                        help=f"minimum P(target|source) (default {CONFIDENCE_FLOOR})")
    report.add_argument("--commit-cap", type=int, default=COMMIT_CAP,
                        help=f"skip commits touching more paths (default {COMMIT_CAP})")
    report.add_argument("--limit", type=int, default=REPORT_CAP,
                        help=f"hard cap on suggestions, 0 for all (default {REPORT_CAP})")
    report.add_argument("--evidence", type=int, default=EVIDENCE_CAP,
                        help=f"commit subjects per pair (default {EVIDENCE_CAP})")
    report.add_argument("--stop-list", type=csv_list, default=STOP_LIST,
                        help="comma-separated fnmatch patterns whose coupling the "
                             f"contract mandates (default {', '.join(STOP_LIST)})")
    report.add_argument("--excludes", type=csv_list, default=SCOPE_EXCLUDES,
                        help="comma-separated path prefixes outside scope (default "
                             f"{', '.join(SCOPE_EXCLUDES)})")
    report.add_argument("--json", action="store_true", help="machine-readable report")
    report.set_defaults(handler=cmd_report)
    for verdict in ("accept", "reject"):
        sub = verbs.add_parser(verdict, help=f"append an {verdict} verdict to the ledger")
        sub.add_argument("a", help="the file that changed")
        sub.add_argument("b", help="the file the candidate said to review")
        sub.add_argument("--reason", default="",
                         help="one line; required for a rejection")
        sub.add_argument("--date", default=date.today().isoformat(),
                         help="ISO date to record (default today)")
        sub.set_defaults(handler=cmd_verdict, verdict=verdict)
    status = verbs.add_parser(
        "status", help="report the ledger's effective-false-positive rate (exit 1 off "
                       "target)"
    )
    status.add_argument("--json", action="store_true", help="machine-readable status")
    status.set_defaults(handler=cmd_status)
    args = parser.parse_args(argv)
    if getattr(args, "date", None) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error("--date must be YYYY-MM-DD")
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
