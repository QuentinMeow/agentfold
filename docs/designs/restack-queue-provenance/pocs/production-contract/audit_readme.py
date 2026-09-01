#!/usr/bin/env python3
"""Audit the production-contract README against a self-test JSONL stream.

The audit intentionally uses only the Python standard library.  It checks the
durable evidence claims rather than trusting a copied transcript.  The optional
comparison canonicalizes only the two environment strings in the summary; all
scenario OIDs, reasons, verdicts, edge lists, paths, and counters remain covered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


OID_PATTERN = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
FIXTURE_SHA_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
EXPECTED_SCENARIOS = 122
EXPECTED_CONTROLS = 15
EXPECTED_ALIASES = 4
EXPECTED_AUDIT_CHECKS = 2070


@dataclass(frozen=True)
class NamedTableSchema:
    name: str
    start: str
    end: str
    header: str
    header_index: int
    row_names: tuple[str, ...]
    oid_shape: str
    records: str = "scenarios"


P18_ROWS = tuple(
    f"P18{letter}-{suffix}"
    for letter, suffix in (
        ("h", "missing-M"),
        ("i", "noncommit-M-blob"),
        ("j", "noncommit-M-tree"),
        ("k", "noncommit-M-tag"),
        ("l", "unrelated-M"),
        ("m", "M-after-N"),
        ("n", "M-equals-C"),
        ("o", "M-equals-N"),
    )
)
R3_ROWS = (
    "R3-01-two-invalid-causal-sources",
    "R3-02-invalid-valid-causal-competition",
    "R3-03-unrelated-invalid-does-not-poison",
)
R4_ROWS = (
    "R4-01-same-root-valid-diamond",
    "R4-02-distinct-valid-root-diamond",
    "R4-03-equal-root-plus-invalid-diamond",
)
R6_ROWS = (
    "R6-01-valid-plus-invalid-all-absent",
    "R6-02-valid-plus-ambiguous-all-absent",
    "R6-03-two-invalid-all-absent",
    "R6-04-same-valid-root-all-absent-wrappers",
)
R8_ROWS = (
    "R8-direct-human-response-conflict",
    "R8-direct-human-response-identical",
    "R8-supplier-human-response-conflict",
    "R8-supplier-human-response-identical",
    "R8-review-binding-divergent",
    "R8-review-binding-identical",
    "R8-review-binding-terminal-conflict",
)
R9_ROWS = (
    "R9-direct-review-target-pending-fill",
    "R9-direct-review-revision-pending-fill",
    "R9-supplier-review-target-pending-fill",
    "R9-supplier-review-revision-pending-fill",
)
R10_ROWS = (
    "R10-direct-review-target-backtick-dotless-rejected",
    "R10-supplier-review-revision-generic-placeholder-rejected",
)
R13_BINDING_ROWS = (
    "R13-direct-review-binding-identical",
    "R13-direct-review-binding-target",
    "R13-direct-review-binding-revision",
    "R13-direct-review-binding-terminal",
    "R13-supplier-review-binding-identical",
    "R13-supplier-review-binding-target",
    "R13-supplier-review-binding-revision",
    "R13-supplier-review-binding-terminal",
)
R13_PERSISTED_ROWS = (
    "R13-persisted-same-state",
    "R13-persisted-response-removal",
    "R13-persisted-response-change",
    "R13-persisted-review-target-change",
    "R13-persisted-review-revision-change",
    "R13-persisted-review-outcome-change",
    "R13-persisted-claim-loss",
    "R13-persisted-pending-fill",
    "R13-persisted-terminal-fill",
)
R14_BINDING_ROWS = (
    "R14-direct-old-unanswered-carrier-same",
    "R14-direct-old-unanswered-carrier-target",
    "R14-supplier-old-answered-carrier-pending",
    "R14-supplier-old-answered-carrier-same",
    "R14-supplier-old-answered-carrier-target",
    "R14-supplier-old-answered-carrier-revision",
    "R14-supplier-old-unanswered-carrier-same",
    "R14-supplier-old-unanswered-carrier-target",
)
R14_PERSISTED_ROWS = (
    "R14-persisted-hidden-bytes-low-similarity",
    "R14-persisted-intermediate-claim-regression",
    "R14-persisted-intermediate-review-regression",
    "R14-persisted-delete-recreate",
    "R14-persisted-valid-review-retraction",
    "R14-persisted-valid-first-response-low-similarity",
    "R14-persisted-merge-carrier-pending",
    "R14-persisted-merge-carrier-conflict",
)
R15_ROWS = (
    "R15-old-invalid-delete-recreate",
    "R15-old-valid-delete-recreate",
    "R15-old-human-binding-restore",
    "R15-old-hidden-bytes-restore",
    "R15-old-continuous-preserved",
)
CONTROL_ROWS = (
    "missing-all-parent-direct-validation",
    "supplier-authority-borrowing",
    "identity-multiplicity-collapsed-to-set",
    "reopen-pre-C-genealogy",
    "missing-post-event-continuity",
    "sole-valid-ignores-invalid-root",
    "omit-old-tip-human-binding",
    "literal-review-pending-treated-concrete",
    "broad-review-pending-normalization",
    "omit-supplier-carrier-human-binding",
    "skip-preserved-state-validation",
    "omit-unanswered-published-review-binding",
    "skip-persisted-frozen-skeleton",
    "skip-persisted-candidate-continuity",
    "skip-old-side-continuity",
)


EXACT_NAMED_TABLES = (
    NamedTableSchema("P18 range base", "### Selected-range-base boundary regressions", "## PCX-01-PCX-20 attack coverage", "Case", 0, P18_ROWS, "C-O-M-N"),
    NamedTableSchema("R3 causal sources", "### Mixed causal-source regressions", "### Canonical-root diamond regressions", "Case", 0, R3_ROWS, "none"),
    NamedTableSchema("R4 canonical roots", "### Canonical-root diamond regressions", "### Reintroduced-occurrence history regressions", "Case", 0, R4_ROWS, "none"),
    NamedTableSchema("R6 absent frontier", "### All-absent frontier regressions", "## O-anchored human binding and adapter input", "Case", 0, R6_ROWS, "none"),
    NamedTableSchema("R8 old binding", "## O-anchored human binding and adapter input", "### Pending review target and revision", "Case", 0, R8_ROWS, "C-O-authority-M-N"),
    NamedTableSchema("R9 pending binding", "### Pending review target and revision", "### Malformed review target and revision", "Case", 0, R9_ROWS, "C-O-authority-M-N"),
    NamedTableSchema("R10 malformed binding", "### Malformed review target and revision", "### Implicated-parent and persisted-state regressions", "Case", 0, R10_ROWS, "C-O-authority-M-N"),
    NamedTableSchema("R13 implicated binding", "### Implicated-parent and persisted-state regressions", "### Unanswered review and continuous persisted-state regressions", "Case", 0, R13_BINDING_ROWS, "C-O-M-N"),
    NamedTableSchema("R13 persisted endpoint", "### Implicated-parent and persisted-state regressions", "### Unanswered review and continuous persisted-state regressions", "Case", 1, R13_PERSISTED_ROWS, "C-O-M-N"),
    NamedTableSchema("R14 unanswered binding", "### Unanswered review and continuous persisted-state regressions", "### Old-side C-rooted occurrence regressions", "Case", 0, R14_BINDING_ROWS, "C-O-M-N"),
    NamedTableSchema("R14 persisted continuity", "### Unanswered review and continuous persisted-state regressions", "### Old-side C-rooted occurrence regressions", "Case", 1, R14_PERSISTED_ROWS, "C-O-M-N"),
    NamedTableSchema("R15 old-side continuity", "### Old-side C-rooted occurrence regressions", "`R8-adapter-M-input-variants` runs three classifiers", "Case", 0, R15_ROWS, "C-O-M-N"),
    NamedTableSchema("damaged controls", "## Damaged-mode controls", "## Evidence audit", "Control", 0, CONTROL_ROWS, "C-O-M-N", "controls"),
)


@dataclass
class Checks:
    failures: list[str] = field(default_factory=list)
    total: int = 0

    def require(self, condition: bool, message: str) -> None:
        self.total += 1
        if not condition:
            self.failures.append(message)


@dataclass
class Stream:
    path: Path
    raw: bytes
    objects: list[dict[str, Any]]
    scenarios: dict[str, dict[str, Any]]
    controls: dict[str, dict[str, Any]]
    aliases: dict[str, Any]
    summary: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "Stream":
        raw = path.read_bytes()
        objects = [json.loads(line) for line in raw.decode().splitlines()]
        scenario_rows = [item for item in objects if "scenario" in item]
        control_rows = [item for item in objects if "control" in item]
        scenarios = {item["scenario"]: item for item in scenario_rows}
        controls = {item["control"]: item for item in control_rows}
        if len(scenarios) != len(scenario_rows):
            raise ValueError("duplicate scenario names in self-test stream")
        if len(controls) != len(control_rows):
            raise ValueError("duplicate control names in self-test stream")
        alias_rows = [item for item in objects if "scenario_alias_inventory" in item]
        summary_rows = [item for item in objects if "summary" in item]
        if len(alias_rows) != 1 or len(summary_rows) != 1:
            raise ValueError(
                "expected exactly one alias inventory and one summary record"
            )
        return cls(
            path=path,
            raw=raw,
            objects=objects,
            scenarios=scenarios,
            controls=controls,
            aliases=alias_rows[0],
            summary=summary_rows[0],
        )

    def raw_sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()

    def canonical_bytes(self) -> bytes:
        rows: list[str] = []
        for item in self.objects:
            canonical = dict(item)
            if "summary" in canonical:
                canonical.pop("git", None)
                canonical.pop("python", None)
            rows.append(
                json.dumps(
                    canonical,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        return ("\n".join(rows) + "\n").encode()

    def canonical_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def normalized(text: str) -> str:
    return " ".join(text.split())


def friendly_classification(value: str) -> str:
    return "no finding" if value == "no-finding" else "blocking"


def record_serialization(records: dict[str, dict[str, Any]], names: Iterable[str]) -> str:
    return "\n".join(json.dumps(records[name], sort_keys=True) for name in names)


def heading_span(readme: str, start: str, end: str | None = None) -> tuple[int, int]:
    begin = readme.index(start)
    finish = readme.index(end, begin + len(start)) if end else len(readme)
    return begin, finish


def table_row(lines: list[str], label: str) -> tuple[int, str] | None:
    matches = [
        (number, line)
        for number, line in enumerate(lines, 1)
        if line.startswith("|") and label in line
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def first_table_cell(line: str) -> str | None:
    if not line.startswith("|") or "|" not in line[1:]:
        return None
    cell = line[1:].split("|", 1)[0].strip()
    if len(cell) >= 2 and cell.startswith("`") and cell.endswith("`"):
        return cell[1:-1]
    return cell


def markdown_table_blocks(section: str, header: str) -> list[list[str]]:
    lines = section.splitlines()
    blocks: list[list[str]] = []
    for index, line in enumerate(lines):
        if first_table_cell(line) != header:
            continue
        block: list[str] = []
        cursor = index + 1
        if cursor < len(lines) and re.fullmatch(r"\|[-: |]+\|", lines[cursor]):
            cursor += 1
        while cursor < len(lines) and lines[cursor].startswith("|"):
            block.append(lines[cursor])
            cursor += 1
        blocks.append(block)
    return blocks


def expected_row_oids(item: dict[str, Any], shape: str) -> list[str]:
    if shape == "none":
        return []
    if shape == "C-O-M-N":
        return [item[key] for key in ("C", "O", "M", "N")]
    if shape == "C-O-authority-M-N":
        details = item["details"]
        return [
            item["C"],
            item["O"],
            details["authority_parent"],
            details["authority_child"],
            item["M"],
            item["N"],
        ]
    raise ValueError(f"unknown exact-table OID shape: {shape}")


def audit_exact_named_tables(
    readme: str,
    scenarios: dict[str, dict[str, Any]],
    controls: dict[str, dict[str, Any]],
    checks: Checks,
) -> tuple[int, int]:
    schemas_by_section: dict[tuple[str, str, str], list[NamedTableSchema]] = {}
    for schema in EXACT_NAMED_TABLES:
        schemas_by_section.setdefault(
            (schema.start, schema.end, schema.header), []
        ).append(schema)

    cached_blocks: dict[tuple[str, str, str], list[list[str]]] = {}
    for key, schemas in schemas_by_section.items():
        start, end, header = key
        try:
            begin, finish = heading_span(readme, start, end)
        except ValueError as error:
            checks.require(False, f"missing exact-table boundary: {error}")
            cached_blocks[key] = []
            continue
        blocks = markdown_table_blocks(readme[begin:finish], header)
        expected_blocks = max(schema.header_index for schema in schemas) + 1
        checks.require(
            len(blocks) == expected_blocks,
            f"{start}: expected {expected_blocks} {header!r} table(s), got {len(blocks)}",
        )
        cached_blocks[key] = blocks

    audited_rows = 0
    semantic_rows = 0
    for schema in EXACT_NAMED_TABLES:
        key = (schema.start, schema.end, schema.header)
        blocks = cached_blocks.get(key, [])
        if schema.header_index >= len(blocks):
            checks.require(False, f"missing exact table: {schema.name}")
            continue
        block = blocks[schema.header_index]
        actual_names = tuple(
            name
            for line in block
            if (name := first_table_cell(line)) is not None
        )
        checks.require(
            actual_names == schema.row_names,
            f"{schema.name}: row inventory differs; expected {schema.row_names}, got {actual_names}",
        )
        records = scenarios if schema.records == "scenarios" else controls
        for name in schema.row_names:
            matches = [line for line in block if first_table_cell(line) == name]
            checks.require(
                len(matches) == 1,
                f"{schema.name}: expected exactly one row named {name}, got {len(matches)}",
            )
            checks.require(name in records, f"{schema.name}: stream has no record {name}")
            if len(matches) != 1 or name not in records:
                continue
            row = matches[0]
            item = records[name]
            expected_oids = expected_row_oids(item, schema.oid_shape)
            checks.require(
                OID_PATTERN.findall(row) == expected_oids,
                f"{schema.name}: ordered endpoint OIDs differ for {name}",
            )
            if schema.records == "controls":
                checks.require(
                    item["status"] in row,
                    f"{schema.name}: control status differs for {name}",
                )
                baseline = friendly_classification(item["baseline_classification"])
                damaged = friendly_classification(item["damaged_classification"])
                checks.require(
                    f"{baseline} -> {damaged}" in row.lower(),
                    f"{schema.name}: control transition differs for {name}",
                )
            else:
                semantic = (
                    f"`{item['classification']}` / "
                    f"`{item['evidence_verdict']['status']}` / "
                    f"`{item['event_mode']}`"
                )
                checks.require(
                    semantic in row,
                    f"{schema.name}: classification/status/mode differs for {name}",
                )
            audited_rows += 1
            semantic_rows += 1
    return audited_rows, semantic_rows


P_CONTRACT_SCENARIOS: dict[str, tuple[str, ...]] = {
    "P1": ("P1-direct-linear-valid",),
    "P2": ("P2-direct-linear-invalid",),
    "P3": ("P3-genuine-old-loss",),
    "P4": ("P4-pre-C-identical-origins",),
    "P5": ("P5-duplicate-at-C",),
    "P6": ("P6a-old-delete-recreate", "P6b-candidate-delete-recreate"),
    "P7": ("P7-immutable-payload-change",),
    "P8": ("P8-path-timing-move",),
    "P9": ("P9-direct-two-parent-valid",),
    "P10": ("P10-direct-invalid-parent",),
    "P11": ("P11-direct-three-parent-valid",),
    "P12": ("P12-merge-supplier-valid",),
    "P13": ("P13-merge-supplier-invalid",),
    "P14": ("P14-supplier-reintroduced",),
    "P15": ("P15-competing-suppliers",),
    "P16": ("P16-PCX-08-invalid-supplier-claimed-carrier",),
    "P17": ("P17-post-event-reintroduction",),
    "P18": (),
    "P19": ("P19-production-identities",),
    "P20": ("P20-lifecycle-types",),
    "P21": ("P21-PCX-17c-squash-erasure",),
    "P22": ("P22-PCX-18-one-pass-many-actions",),
}


def audit_plain_table_inventories(readme: str, checks: Checks) -> int:
    schemas = (
        (
            "S alias",
            "## S1/S2/S3/S12 executable aliases",
            "## P1-P22 coverage",
            "Alias",
            ("S1", "S2", "S3", "S12"),
        ),
        (
            "P contract",
            "## P1-P22 coverage",
            "### Selected-range-base boundary regressions",
            "Contract",
            tuple(P_CONTRACT_SCENARIOS),
        ),
        (
            "PCX attack",
            "## PCX-01-PCX-20 attack coverage",
            "### Mixed causal-source regressions",
            "Attack",
            tuple(PCX_ROWS),
        ),
    )
    audited = 0
    for name, start, end, header, expected_names in schemas:
        try:
            begin, finish = heading_span(readme, start, end)
        except ValueError as error:
            checks.require(False, f"missing {name} table boundary: {error}")
            continue
        blocks = markdown_table_blocks(readme[begin:finish], header)
        checks.require(len(blocks) == 1, f"{name}: expected exactly one table")
        if len(blocks) != 1:
            continue
        rows = blocks[0]
        actual_names = tuple(
            row_name
            for line in rows
            if (row_name := first_table_cell(line)) is not None
        )
        checks.require(
            actual_names == expected_names,
            f"{name}: row inventory differs; expected {expected_names}, got {actual_names}",
        )
        if name == "P contract":
            for contract, scenario_names in P_CONTRACT_SCENARIOS.items():
                matches = [line for line in rows if first_table_cell(line) == contract]
                checks.require(len(matches) == 1, f"P contract: duplicate/missing {contract}")
                if len(matches) == 1:
                    found_names = tuple(
                        scenario
                        for scenario in scenario_names
                        if f"`{scenario}`" in matches[0]
                    )
                    checks.require(
                        found_names == scenario_names,
                        f"P contract: executable cases differ for {contract}",
                    )
        audited += len(expected_names)
    return audited


def audit_aliases(
    readme: str, stream: Stream, checks: Checks
) -> int:
    inventory = stream.aliases["scenario_alias_inventory"]
    checks.require(stream.aliases.get("status") == "PASS", "alias inventory is not PASS")
    checks.require(len(inventory) == EXPECTED_ALIASES, "alias inventory is not 4 rows")
    row_count = 0
    for item in inventory:
        alias = item["alias"]
        expected = item["expected"]
        checks.require(item.get("status") == "PASS", f"{alias} did not pass")
        checks.require(
            item.get("maps_to") == expected.get("scenario"),
            f"{alias} mapping differs from its expectation",
        )
        checks.require(
            item.get("observed") == expected,
            f"{alias} observed evidence differs from its expectation",
        )
        authority_kind = "invalid" if expected["invalid_authority_edges"] else "valid"
        authority_cell = (
            f"{expected['authority_edges']} {authority_kind}"
            if expected["authority_edges"]
            else "0"
        )
        rendered = (
            f"| {alias} | `{expected['scenario']}` | `{expected['classification']}` | "
            f"`{expected['evidence_status']}` | `{expected['event_mode']}` | "
            f"{authority_cell} / {expected['propagation_edges']} |"
        )
        checks.require(rendered in readme, f"README alias row differs for {alias}")
        row_count += 1
    return row_count


def audit_named_rows(
    lines: list[str], records: dict[str, dict[str, Any]], controls: dict[str, dict[str, Any]], checks: Checks
) -> tuple[int, int]:
    row_checks = 0
    semantic_checks = 0
    for number, line in enumerate(lines, 1):
        if not line.startswith("|"):
            continue
        names = [name for name in records if f"`{name}`" in line]
        if not names:
            continue
        row_checks += 1
        serialized = record_serialization(records, names)
        for oid in OID_PATTERN.findall(line):
            checks.require(
                oid in serialized,
                f"line {number}: row OID {oid} is absent from {names}",
            )
        if len(names) != 1:
            continue
        name = names[0]
        item = records[name]
        lower = line.lower()
        if name in controls:
            expected_oids = [item[key] for key in ("C", "O", "M", "N")]
            checks.require(
                OID_PATTERN.findall(line) == expected_oids,
                f"line {number}: control endpoints differ for {name}",
            )
            checks.require(
                item["status"] in line,
                f"line {number}: control status differs for {name}",
            )
            baseline = friendly_classification(item["baseline_classification"])
            damaged = friendly_classification(item["damaged_classification"])
            checks.require(
                f"{baseline} -> {damaged}" in lower,
                f"line {number}: control transition differs for {name}",
            )
            semantic_checks += 3
            continue
        status = item["evidence_verdict"]["status"]
        mode = item["event_mode"]
        if "no finding" in lower or "no-finding" in lower:
            semantic_checks += 1
            checks.require(
                item["classification"] == "no-finding",
                f"line {number}: no-finding claim differs for {name}",
            )
        if "blocking" in lower or " block" in lower:
            semantic_checks += 1
            checks.require(
                item["classification"] == "blocking-finding",
                f"line {number}: blocking claim differs for {name}",
            )
        for claimed_status in ("unreadable", "ambiguous", "invalid", "none"):
            if f"`{claimed_status}`" in lower or re.search(
                rf"\|\s*{claimed_status}(?:\s|;|\{{)", lower
            ):
                semantic_checks += 1
                checks.require(
                    status == claimed_status
                    or (
                        claimed_status == "invalid"
                        and "valid and one invalid" in lower
                    ),
                    f"line {number}: {claimed_status} claim differs from {status} for {name}",
                )
                break
        for claim_status, claim_mode in (
            ("valid", "direct"),
            ("valid", "supplier"),
            ("invalid", "direct"),
            ("invalid", "supplier"),
        ):
            if f"`{claim_status} {claim_mode}`" in lower:
                semantic_checks += 1
                checks.require(
                    status == claim_status and mode == claim_mode,
                    f"line {number}: {claim_status}-{claim_mode} claim differs for {name}",
                )
    return row_checks, semantic_checks


PCX_ROWS: dict[str, tuple[list[str], list[str]]] = {
    "PCX-01 neutral parent": (["PCX-01-neutral-parent"], ["valid direct", "neutral parent"]),
    "PCX-02 neutral plus invalid carrier": (["PCX-02-neutral-plus-invalid-carrier"], ["invalid direct", "neutral parent"]),
    "PCX-03 foreign exact identity": (["PCX-03-foreign-exact-identity"], ["ambiguous", "not rooted at `C`"]),
    "PCX-04 several absent parents": (["PCX-04-several-absent-one-supplier"], ["valid supplier", "two absent parents"]),
    "PCX-05 competing later supplier": (["PCX-05-competing-later-supplier"], ["ambiguous", "both independently valid authority edges"]),
    "PCX-06 nested supplier over direct": (["PCX-06-nested-supplier-over-direct"], ["two-edge authority event", "two propagation edges", "stable order"]),
    "PCX-07 overqualified propagation": (["PCX-07-overqualified-propagation"], ["valid supplier", "remains one propagation edge"]),
    "PCX-08 invalid supplier plus claimed carrier": (["P16-PCX-08-invalid-supplier-claimed-carrier"], ["invalid supplier", "blocks"]),
    "PCX-09 recreated claimed bytes": (["PCX-09-recreated-claimed-bytes"], ["ambiguous discontinuity"]),
    "PCX-10 transient multiplicity": (["PCX-10-transient-multiplicity"], ["ambiguous at multiplicity 2"]),
    "PCX-11 different payload, same path": (["PCX-11-different-payload-same-path"], ["supplier validates", "separate finding"]),
    "PCX-12 timing rename": (["PCX-12-timing-rename-supplier"], ["valid supplier"]),
    "PCX-13 conflicting human response": (["PCX-13-conflicting-human-response"], ["three-level invalid continuation", "three ordered propagation edges"]),
    "PCX-14 valid human supplier": (["PCX-14-valid-human-supplier"], ["valid supplier"]),
    "PCX-15 generated retry": (["PCX-15-generated-retry-supplier"], ["valid supplier"]),
    "PCX-16 task pickup": (["PCX-16-task-pickup-supplier"], ["valid supplier"]),
    "PCX-17 cherry-pick versus squash": (["PCX-17-complete-cherry-pick", "PCX-17-deletion-only-cherry-pick", "P21-PCX-17c-squash-erasure"], ["complete K-then-D cherry-pick validates", "D-only cherry-pick and squash block"]),
    "PCX-18 one-pass many actions": (["P22-PCX-18-one-pass-many-actions"], ["covered with P22"]),
    "PCX-19 missing claim blob": (["PCX-19-missing-claim-blob-recovery"], ["first result `unreadable`", "restored-object result `valid`"]),
    "PCX-20 budget overflow": (["PCX-20a-budget-below-limit", "PCX-20b-budget-overflow"], ["normal `valid`", "returns `ambiguous`", "zero selected events"]),
}


PCX_EXPECTATIONS: dict[str, tuple[str, str, str]] = {
    "PCX-01-neutral-parent": ("no-finding", "valid", "direct"),
    "PCX-02-neutral-plus-invalid-carrier": ("blocking-finding", "invalid", "direct"),
    "PCX-03-foreign-exact-identity": ("blocking-finding", "ambiguous", "direct"),
    "PCX-04-several-absent-one-supplier": ("no-finding", "valid", "supplier"),
    "PCX-05-competing-later-supplier": ("blocking-finding", "ambiguous", "ambiguous"),
    "PCX-06-nested-supplier-over-direct": ("no-finding", "valid", "supplier"),
    "PCX-07-overqualified-propagation": ("no-finding", "valid", "supplier"),
    "P16-PCX-08-invalid-supplier-claimed-carrier": ("blocking-finding", "invalid", "supplier"),
    "PCX-09-recreated-claimed-bytes": ("blocking-finding", "ambiguous", "ambiguous"),
    "PCX-10-transient-multiplicity": ("blocking-finding", "ambiguous", "direct"),
    "PCX-11-different-payload-same-path": ("blocking-finding", "invalid", "mixed"),
    "PCX-12-timing-rename-supplier": ("no-finding", "valid", "supplier"),
    "PCX-13-conflicting-human-response": ("blocking-finding", "invalid", "supplier"),
    "PCX-14-valid-human-supplier": ("no-finding", "valid", "supplier"),
    "PCX-15-generated-retry-supplier": ("no-finding", "valid", "supplier"),
    "PCX-16-task-pickup-supplier": ("no-finding", "valid", "supplier"),
    "PCX-17-complete-cherry-pick": ("no-finding", "valid", "direct"),
    "PCX-17-deletion-only-cherry-pick": ("blocking-finding", "invalid", "direct"),
    "P21-PCX-17c-squash-erasure": ("blocking-finding", "invalid", "direct"),
    "PCX-19-missing-claim-blob-recovery": ("no-finding", "valid", "direct"),
    "PCX-20a-budget-below-limit": ("no-finding", "valid", "direct"),
    "PCX-20b-budget-overflow": ("blocking-finding", "ambiguous", "none"),
}


def audit_pcx_rows(lines: list[str], scenarios: dict[str, dict[str, Any]], checks: Checks) -> int:
    checked = 0
    for label, (names, fragments) in PCX_ROWS.items():
        found = table_row(lines, f"| {label} |")
        checks.require(found is not None, f"missing or duplicate attack row: {label}")
        if found is None:
            continue
        number, row = found
        for fragment in fragments:
            if fragment.startswith("valid "):
                present = re.search(rf"(?<![A-Za-z]){re.escape(fragment)}", row) is not None
            else:
                present = fragment in row
            checks.require(present, f"line {number}: missing PCX claim {fragment!r}")
        for name in names:
            checks.require(name in scenarios, f"line {number}: missing scenario {name}")
            if name not in scenarios or name not in PCX_EXPECTATIONS:
                continue
            item = scenarios[name]
            classification, status, mode = PCX_EXPECTATIONS[name]
            checks.require(
                (item["classification"], item["evidence_verdict"]["status"], item["event_mode"])
                == (classification, status, mode),
                f"line {number}: {name} result differs from the attack-row contract",
            )
        checked += 1

    pcx11 = scenarios.get("PCX-11-different-payload-same-path", {})
    checks.require(
        [(action.get("status"), action.get("event_mode"), action.get("finding")) for action in pcx11.get("actions", [])]
        == [("valid", "supplier", False), ("invalid", "direct", True)],
        "PCX-11 no longer contains the claimed valid supplier plus distinct finding",
    )
    pcx19 = scenarios.get("PCX-19-missing-claim-blob-recovery", {})
    checks.require(
        pcx19.get("recovery")
        and pcx19["recovery"].get("first_status") == "unreadable"
        and pcx19["recovery"].get("second_status") == "valid"
        and pcx19["recovery"].get("same_process") is True,
        "PCX-19 recovery claim differs from the scenario record",
    )
    return checked


def audit_costs(readme: str, scenarios: dict[str, dict[str, Any]], checks: Checks) -> int:
    many = scenarios["P22-PCX-18-one-pass-many-actions"]
    expected_costs = {
        "Graph commits": many["metrics"]["graph_commits"],
        "Graph parent edges": many["metrics"]["graph_parent_edges"],
        "Graph enumerations": many["metrics"]["graph_enumerations"],
        "Per-action history walks": many["metrics"]["per_action_history_walks"],
        "Queue snapshots requested": many["metrics"]["queue_snapshots_requested"],
        "Snapshot cache hits": many["metrics"]["snapshot_cache_hits"],
        "Distinct queue subtree reads": many["metrics"]["queue_subtree_reads"],
        "Git object reads": many["metrics"]["object_reads"],
        "Object cache hits": many["metrics"]["object_cache_hits"],
        "Production identity calls": many["metrics"]["identity_calls"],
        "Production authority calls": many["metrics"]["authority_calls"],
        "Production mutation calls": many["metrics"]["mutation_calls"],
        "`cat-file --batch` processes": many["metrics"]["batch_processes"],
        "Actual Git child processes, including production validator calls": many["metrics"]["git_processes"],
    }
    count = 0
    for label, value in expected_costs.items():
        checks.require(
            f"| {label} | {value:,} |" in readme,
            f"cost counter differs: {label} expected {value:,}",
        )
        count += 1
    for field_name, expected in (
        ("history_commits", 128),
        ("disappeared_actions", 16),
        ("expected_authorized", 8),
        ("expected_findings", 8),
    ):
        checks.require(
            many["details"].get(field_name) == expected,
            f"many-action detail {field_name} changed from {expected}",
        )
        count += 1
    below = scenarios["PCX-20a-budget-below-limit"]
    over = scenarios["PCX-20b-budget-overflow"]
    budget_claims = (
        (below["metrics"]["graph_commits"] == 10, "below-limit graph count"),
        (below["evidence_verdict"]["status"] == "valid", "below-limit verdict"),
        (over["metrics"]["graph_commits"] == 11, "overflow graph count"),
        (over["details"].get("demonstration_limit") == 10, "overflow limit"),
        (not over["actions"], "overflow selected events"),
        (
            over["metrics"]["identity_calls"] == over["metrics"]["authority_calls"] == 0,
            "overflow authority/identity calls",
        ),
    )
    for condition, label in budget_claims:
        checks.require(condition, f"budget claim differs: {label}")
        count += 1
    return count


def audit_readme(readme_path: Path, stream: Stream) -> dict[str, Any]:
    readme = readme_path.read_text()
    lines = readme.splitlines()
    checks = Checks()
    scenarios = stream.scenarios
    controls = stream.controls
    records = scenarios | controls

    checks.require(len(stream.objects) == 139, "self-test stream is not 139 records")
    checks.require(len(scenarios) == EXPECTED_SCENARIOS, "scenario inventory is not 122")
    checks.require(len(controls) == EXPECTED_CONTROLS, "control inventory is not 15")
    summary_expected = {
        "aliases_passed": EXPECTED_ALIASES,
        "aliases_total": EXPECTED_ALIASES,
        "controls_passed": EXPECTED_CONTROLS,
        "controls_total": EXPECTED_CONTROLS,
        "failures": [],
        "passed": EXPECTED_SCENARIOS,
        "summary": "PASS",
        "total": EXPECTED_SCENARIOS,
    }
    for key, expected in summary_expected.items():
        checks.require(stream.summary.get(key) == expected, f"summary field {key} differs")
    for phrase in (
        "49 prescribed real-Git scenarios, 73 focused contract regressions, and all fifteen damaged-mode controls",
        "122/122 scenarios, 4/4 executable aliases, and 15/15 controls",
    ):
        checks.require(normalized(phrase) in normalized(readme), f"missing total claim: {phrase}")

    oid_occurrences = list(OID_PATTERN.finditer(readme))
    fixture_sha_occurrences = list(FIXTURE_SHA_PATTERN.finditer(readme))
    artifact = stream.raw.decode()
    for match in oid_occurrences:
        line = readme.count("\n", 0, match.start()) + 1
        checks.require(
            match.group(0) in artifact,
            f"line {line}: OID absent from self-test output: {match.group(0)}",
        )
    checks.require(len(fixture_sha_occurrences) == 7, "README does not contain 7 fixture SHA claims")
    for match in fixture_sha_occurrences:
        line = readme.count("\n", 0, match.start()) + 1
        checks.require(
            match.group(0) in artifact,
            f"line {line}: fixture SHA absent from self-test output: {match.group(0)}",
        )

    regions = [
        ("P12 starts with", "## S1/S2/S3/S12", ["P12-merge-supplier-valid"]),
        (
            "### Selected-range-base boundary regressions",
            "## PCX-01-PCX-20 attack coverage",
            [
                f"P18{letter}-{suffix}"
                for letter, suffix in (
                    ("h", "missing-M"),
                    ("i", "noncommit-M-blob"),
                    ("j", "noncommit-M-tree"),
                    ("k", "noncommit-M-tag"),
                    ("l", "unrelated-M"),
                    ("m", "M-after-N"),
                    ("n", "M-equals-C"),
                    ("o", "M-equals-N"),
                )
            ],
        ),
        (
            "## PCX-01-PCX-20 attack coverage",
            "### Mixed causal-source regressions",
            [name for name in scenarios if name.startswith("PCX-")]
            + ["P16-PCX-08-invalid-supplier-claimed-carrier", "P22-PCX-18-one-pass-many-actions"],
        ),
        (
            "### Mixed causal-source regressions",
            "### Canonical-root diamond regressions",
            ["R3-01-two-invalid-causal-sources", "R3-02-invalid-valid-causal-competition", "R3-03-unrelated-invalid-does-not-poison"],
        ),
        (
            "### Canonical-root diamond regressions",
            "### Reintroduced-occurrence history regressions",
            ["R4-01-same-root-valid-diamond", "R4-02-distinct-valid-root-diamond", "R4-03-equal-root-plus-invalid-diamond"],
        ),
        (
            "### Reintroduced-occurrence history regressions",
            "### All-absent frontier regressions",
            ["R5-01-invalid-redelete-after-supplier-reintroduction", "R5-02-valid-redelete-after-supplier-reintroduction"],
        ),
        (
            "### All-absent frontier regressions",
            "## O-anchored human binding and adapter input",
            ["R6-01-valid-plus-invalid-all-absent", "R6-02-valid-plus-ambiguous-all-absent", "R6-03-two-invalid-all-absent", "R6-04-same-valid-root-all-absent-wrappers"],
        ),
        (
            "## O-anchored human binding and adapter input",
            "### Pending review target and revision",
            [
                "R8-direct-human-response-conflict",
                "R8-direct-human-response-identical",
                "R8-supplier-human-response-conflict",
                "R8-supplier-human-response-identical",
                "R8-review-binding-divergent",
                "R8-review-binding-identical",
                "R8-review-binding-terminal-conflict",
            ],
        ),
        (
            "### Pending review target and revision",
            "### Malformed review target and revision",
            [name for name in scenarios if name.startswith("R9-")],
        ),
        (
            "### Malformed review target and revision",
            "### Implicated-parent and persisted-state regressions",
            [name for name in scenarios if name.startswith("R10-")],
        ),
        (
            "### Implicated-parent and persisted-state regressions",
            "### Unanswered review and continuous persisted-state regressions",
            [name for name in scenarios if name.startswith("R13-")],
        ),
        (
            "### Unanswered review and continuous persisted-state regressions",
            "### Old-side C-rooted occurrence regressions",
            [name for name in scenarios if name.startswith("R14-")],
        ),
        (
            "### Old-side C-rooted occurrence regressions",
            "`R8-adapter-M-input-variants` runs three classifiers",
            [name for name in scenarios if name.startswith("R15-")],
        ),
        (
            "`R8-adapter-M-input-variants` runs three classifiers",
            "## Cost and budget evidence",
            ["R8-adapter-M-input-variants", "R8-adapter-M-N-frontier-counterexample"],
        ),
        (
            "## Cost and budget evidence",
            "## Damaged-mode controls",
            ["P22-PCX-18-one-pass-many-actions", "PCX-19-missing-claim-blob-recovery", "PCX-20a-budget-below-limit", "PCX-20b-budget-overflow"],
        ),
        ("## Damaged-mode controls", "## Evidence audit", list(controls)),
    ]
    covered_positions: set[int] = set()
    region_oid_claims = 0
    for start, end, names in regions:
        missing = [name for name in names if name not in records]
        checks.require(not missing, f"missing records for README region {start}: {missing}")
        try:
            begin, finish = heading_span(readme, start, end)
        except ValueError as error:
            checks.require(False, f"missing README region boundary: {error}")
            continue
        if missing:
            continue
        allowed = record_serialization(records, names)
        for match in oid_occurrences:
            if begin <= match.start() < finish:
                region_oid_claims += 1
                covered_positions.add(match.start())
                line = readme.count("\n", 0, match.start()) + 1
                checks.require(
                    match.group(0) in allowed,
                    f"line {line}: OID is not in its named scenario/control region: {match.group(0)}",
                )
    unmapped = [
        (readme.count("\n", 0, match.start()) + 1, match.group(0))
        for match in oid_occurrences
        if match.start() not in covered_positions
    ]
    checks.require(not unmapped, f"unmapped README OID claims: {unmapped}")

    alias_rows = audit_aliases(readme, stream, checks)
    plain_inventory_rows = audit_plain_table_inventories(readme, checks)
    schema_rows, schema_semantic_rows = audit_exact_named_tables(
        readme, scenarios, controls, checks
    )
    row_checks, semantic_row_checks = audit_named_rows(lines, records, controls, checks)
    pcx_rows = audit_pcx_rows(lines, scenarios, checks)
    counter_checks = audit_costs(readme, scenarios, checks)

    canonical_digest = stream.canonical_sha256()
    raw_digest = stream.raw_sha256()
    checks.require(
        f"environment, at `{raw_digest}`." in normalized(readme),
        "README tested-environment raw digest is missing or stale",
    )
    checks.require(
        f"Canonical semantic SHA-256: `{canonical_digest}`." in normalized(readme),
        "README canonical semantic digest is missing or stale",
    )
    nonclaims = (
        "do not change production review parsing, schemas, templates, or workflow behavior.",
        "PCX-21 staged/committed parity and PCX-22 unmerged-index handling remain production-integration gates and were not run.",
        "no push-prevention claim is made.",
        "Squash remains unsupported.",
        "it must not automatically substitute either `O` or `N`.",
        "zero POC-owned per-action history walks is not a claim of zero total per-commit history queries.",
        "production integration must reuse the enumerated parent cache, eliminate those queries, and set a measured process budget.",
        "No production code, schema, task record, contract, dependency, adapter, or neighboring POC changed",
        "no branch was pushed or pull request opened.",
    )
    normalized_readme = normalized(readme)
    for phrase in nonclaims:
        checks.require(normalized(phrase) in normalized_readme, f"missing nonclaim: {phrase}")
    checks.require(
        checks.total + 2 == EXPECTED_AUDIT_CHECKS,
        "auditor coverage-check topology changed without updating its pinned schema",
    )
    checks.require(
        f'"audit": "PASS", "checks_passed": {EXPECTED_AUDIT_CHECKS}, '
        f'"checks_total": {EXPECTED_AUDIT_CHECKS}'
        in readme,
        "README audit PASS/check-count transcript is missing or stale",
    )

    return {
        "audit": "PASS" if not checks.failures else "FAIL",
        "alias_rows": alias_rows,
        "canonical_sha256": canonical_digest,
        "checks_passed": checks.total - len(checks.failures),
        "checks_total": checks.total,
        "control_rows": len(controls),
        "counter_checks": counter_checks,
        "failures": checks.failures,
        "fixture_sha256_claims": len(fixture_sha_occurrences),
        "oid_occurrences": len(oid_occurrences),
        "pcx_rows": pcx_rows,
        "pinned_controls": len(controls),
        "pinned_scenarios": len(scenarios),
        "plain_inventory_rows": plain_inventory_rows,
        "raw_sha256": stream.raw_sha256(),
        "record_rows": row_checks,
        "region_oid_claims": region_oid_claims,
        "schema_rows": schema_rows,
        "schema_semantic_rows": schema_semantic_rows,
        "semantic_row_checks": semantic_row_checks,
        "unique_oids": len({match.group(0) for match in oid_occurrences}),
    }


def recursive_field_differences(left: Any, right: Any) -> int:
    if type(left) is not type(right):
        return 1
    if isinstance(left, dict):
        keys = set(left) | set(right)
        return sum(
            1
            if key not in left or key not in right
            else recursive_field_differences(left[key], right[key])
            for key in keys
        )
    if isinstance(left, list):
        common = min(len(left), len(right))
        return abs(len(left) - len(right)) + sum(
            recursive_field_differences(left[index], right[index])
            for index in range(common)
        )
    return int(left != right)


def compare_streams(left: Stream, right: Stream) -> dict[str, Any]:
    common = min(len(left.objects), len(right.objects))
    record_differences = sum(
        left.objects[index] != right.objects[index] for index in range(common)
    ) + abs(len(left.objects) - len(right.objects))
    field_differences = abs(len(left.objects) - len(right.objects))
    field_differences += sum(
        recursive_field_differences(left.objects[index], right.objects[index])
        for index in range(common)
    )
    result = {
        "canonical_equal": left.canonical_bytes() == right.canonical_bytes(),
        "canonical_sha256_left": left.canonical_sha256(),
        "canonical_sha256_right": right.canonical_sha256(),
        "differing_fields": field_differences,
        "differing_records": record_differences,
        "raw_equal": left.raw == right.raw,
        "raw_sha256_left": left.raw_sha256(),
        "raw_sha256_right": right.raw_sha256(),
    }
    result["comparison"] = (
        "PASS"
        if result["canonical_equal"]
        and result["raw_equal"]
        and result["differing_records"] == 0
        and result["differing_fields"] == 0
        else "FAIL"
    )
    return result


def damage_control(readme_path: Path, stream: Stream) -> dict[str, Any]:
    original = readme_path.read_text()
    literal_mutations = {
        "readme-oid": (
            "3a01d100e676a9a20f8dc545fed19be3419fb759",
            "0000000000000000000000000000000000000000",
        ),
        "readme-result": (
            "| PCX-01 neutral parent | valid direct;",
            "| PCX-01 neutral parent | invalid direct;",
        ),
        "readme-counter": ("| Graph commits | 133 |", "| Graph commits | 134 |"),
    }
    mutations: list[tuple[str, str, int]] = []
    for name, (old, new) in literal_mutations.items():
        mutations.append((name, original.replace(old, new, 1), original.count(old)))

    r14_row = next(
        line
        for line in original.splitlines()
        if first_table_cell(line) == "R14-direct-old-unanswered-carrier-target"
    )
    forged_real_oids = r14_row.replace(
        "`R14-direct-old-unanswered-carrier-target`",
        "`R14-invented-real-oids`",
        1,
    ).replace(
        "`blocking-finding` / `invalid` / `direct`",
        "`no-finding` / `valid` / `direct`",
        1,
    )
    mutations.extend(
        (
            (
                "invented-row-real-oids-false-verdict",
                original.replace(r14_row, r14_row + "\n" + forged_real_oids, 1),
                1,
            ),
            (
                "invented-row-no-oids",
                original.replace(
                    r14_row,
                    r14_row
                    + "\n| `R14-invented-no-oids` | none | "
                    + "`no-finding` / `valid` / `direct` |",
                    1,
                ),
                1,
            ),
            (
                "duplicate-real-row",
                original.replace(r14_row, r14_row + "\n" + r14_row, 1),
                1,
            ),
            (
                "missing-real-row",
                original.replace(r14_row + "\n", "", 1),
                1,
            ),
        )
    )
    row_oids = OID_PATTERN.findall(r14_row)
    swapped_row = r14_row.replace(row_oids[0], "OID_SWAP_SENTINEL", 1)
    swapped_row = swapped_row.replace(row_oids[1], row_oids[0], 1)
    swapped_row = swapped_row.replace("OID_SWAP_SENTINEL", row_oids[1], 1)
    mutations.append(
        (
            "swapped-same-region-oids",
            original.replace(r14_row, swapped_row, 1),
            1,
        )
    )
    transcript_match = re.search(
        r'"checks_passed": (\d+), "checks_total": (\d+)', original
    )
    if transcript_match:
        changed_transcript = (
            f'"checks_passed": {int(transcript_match.group(1)) + 1}, '
            f'"checks_total": {int(transcript_match.group(2)) + 1}'
        )
        mutations.append(
            (
                "changed-transcript-counts",
                original[: transcript_match.start()]
                + changed_transcript
                + original[transcript_match.end() :],
                1,
            )
        )
    else:
        mutations.append(("changed-transcript-counts", original, 0))

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="production-contract-readme-audit-") as root:
        for name, damaged, occurrences in mutations:
            path = Path(root) / f"{name}.md"
            path.write_text(damaged)
            result = audit_readme(path, stream)
            observed = occurrences >= 1 and result["audit"] == "FAIL"
            results.append(
                {
                    "control": name,
                    "failure_count": len(result["failures"]),
                    "status": "OBSERVED_RED" if observed else "FAILED_TO_RED",
                }
            )
        damaged_objects = json.loads(json.dumps(stream.objects))
        damaged_objects[0]["classification"] = "blocking-finding"
        damaged_stream_path = Path(root) / "semantic-stream.jsonl"
        damaged_stream_path.write_text(
            "\n".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True)
                for item in damaged_objects
            )
            + "\n"
        )
        comparison = compare_streams(stream, Stream.load(damaged_stream_path))
        comparison_control = {
            "control": "comparison-semantic-field",
            "differing_fields": comparison["differing_fields"],
            "differing_records": comparison["differing_records"],
            "status": (
                "OBSERVED_RED"
                if comparison["comparison"] == "FAIL"
                else "FAILED_TO_RED"
            ),
        }
    passed = all(item["status"] == "OBSERVED_RED" for item in results)
    passed = passed and comparison_control["status"] == "OBSERVED_RED"
    return {
        "audit_damage_control": "PASS" if passed else "FAIL",
        "comparison_control": comparison_control,
        "controls": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jsonl", required=True, type=Path, help="self-test JSONL to audit"
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path(__file__).with_name("README.md"),
        help="README to audit (defaults to the sibling README.md)",
    )
    parser.add_argument("--compare", type=Path, help="second self-test stream")
    parser.add_argument(
        "--damage-control",
        action="store_true",
        help="prove README schema and evidence mutations fail the audit",
    )
    arguments = parser.parse_args()
    try:
        stream = Stream.load(arguments.jsonl)
        result = audit_readme(arguments.readme, stream)
        if arguments.compare:
            comparison = compare_streams(
                stream, Stream.load(arguments.compare)
            )
            result["comparison"] = comparison
            if comparison["comparison"] != "PASS":
                result["audit"] = "FAIL"
                result["failures"].append(
                    "comparison stream differs from the primary stream"
                )
        if arguments.damage_control:
            result["observed_red"] = damage_control(arguments.readme, stream)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"audit": "FAIL", "failures": [str(error)]}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    passed = result["audit"] == "PASS"
    if arguments.damage_control:
        passed = passed and result["observed_red"]["audit_damage_control"] == "PASS"
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
