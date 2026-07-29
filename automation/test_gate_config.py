#!/usr/bin/env python3
"""Load and classify AgentFold's repository-owned test-gate policy.

The public schema is deliberately closed: an unknown key is more likely to be a
misspelled safety setting than an intended extension.  Policies from both sides of a
candidate change can be combined with :func:`union_policies`; risk classification then
fails closed if either version considers a path critical or unknown.
"""
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional, Tuple

try:
    from automation._vendor import tomli
except ImportError:  # Direct execution puts automation/, not the repo root, on sys.path.
    from _vendor import tomli


SCHEMA_VERSION = 1
FINAL_MODES = frozenset(("manual", "hard"))
FINAL_TRIGGERS = frozenset(("pull-request",))
BUDGET_ACTIONS = frozenset(("file-task",))
KNOWN_CHECK_IDS = frozenset(("core-scope", "reconcile", "repository-tests/full"))
MANDATORY_CRITICAL_CATEGORIES = frozenset(
    (
        "credentials-and-secrets",
        "pii",
        "authorization",
        "destructive-operations",
        "external-publication",
        "production-deployment",
    )
)
IDENTIFIER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ConfigError(ValueError):
    """The test-gate policy is missing, malformed, or unsafe."""


@dataclass(frozen=True)
class GateBudget:
    target_seconds: float
    maximum_seconds: float


@dataclass(frozen=True)
class FinalGate:
    mode: str
    trigger: Optional[str]
    budget: GateBudget

    @property
    def target_seconds(self):
        return self.budget.target_seconds

    @property
    def maximum_seconds(self):
        return self.budget.maximum_seconds


@dataclass(frozen=True)
class CriticalBinding:
    name: str
    paths: Tuple[str, ...]
    checks: Tuple[str, ...]

    @property
    def category(self):
        return self.name

    @property
    def path_globs(self):
        return self.paths

    @property
    def required_check_ids(self):
        return self.checks


@dataclass(frozen=True)
class ReversibleBinding:
    id: str
    paths: Tuple[str, ...]

    @property
    def path_globs(self):
        return self.paths


@dataclass(frozen=True)
class TestGatePolicy:
    schema_version: int
    routine: GateBudget
    final: FinalGate
    on_budget_exceeded: str
    critical_bindings: Tuple[CriticalBinding, ...]
    reversible_bindings: Tuple[ReversibleBinding, ...]
    unmatched_is_critical: bool

    @property
    def digest(self):
        return canonical_policy_digest(self)


@dataclass(frozen=True)
class PolicyUnion:
    """Base and candidate policies retained so neither can weaken the other."""

    base: TestGatePolicy
    candidate: TestGatePolicy

    @property
    def routine(self):
        return GateBudget(
            min(self.base.routine.target_seconds, self.candidate.routine.target_seconds),
            min(self.base.routine.maximum_seconds, self.candidate.routine.maximum_seconds),
        )

    @property
    def critical_bindings(self):
        return _unique_sorted(
            self.base.critical_bindings + self.candidate.critical_bindings,
            _critical_sort_key,
        )

    @property
    def reversible_bindings(self):
        return _unique_sorted(
            self.base.reversible_bindings + self.candidate.reversible_bindings,
            _reversible_sort_key,
        )

    @property
    def hard_triggers(self):
        return tuple(
            sorted(
                {
                    gate.trigger
                    for gate in (self.base.final, self.candidate.final)
                    if gate.mode == "hard"
                }
            )
        )

    @property
    def final_target_seconds(self):
        return min(
            self.base.final.target_seconds,
            self.candidate.final.target_seconds,
        )

    @property
    def final_maximum_seconds(self):
        return min(
            self.base.final.maximum_seconds,
            self.candidate.final.maximum_seconds,
        )

    @property
    def digest(self):
        return canonical_policy_digest(self)


@dataclass(frozen=True)
class RiskClassification:
    critical_bindings: Tuple[CriticalBinding, ...]
    reversible_ids: Tuple[str, ...]
    unmatched_paths: Tuple[str, ...]
    required_check_ids: Tuple[str, ...]
    critical_paths: Tuple[str, ...]
    reversible_paths: Tuple[str, ...]

    @property
    def is_critical(self):
        return bool(self.critical_paths or self.unmatched_paths)


def _expect_table(value, location):
    if not isinstance(value, dict):
        raise ConfigError("{} must be a table".format(location))
    return value


def _closed_table(value, location, required, optional=()):
    table = _expect_table(value, location)
    required_keys = set(required)
    allowed_keys = required_keys | set(optional)
    unknown = sorted(set(table) - allowed_keys)
    missing = sorted(required_keys - set(table))
    if unknown:
        raise ConfigError(
            "{} has unknown key(s): {}".format(location, ", ".join(unknown))
        )
    if missing:
        raise ConfigError(
            "{} is missing required key(s): {}".format(location, ", ".join(missing))
        )
    return table


def _positive_number(value, location):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError("{} must be a number, not a boolean or string".format(location))
    number = float(value)
    if not math.isfinite(number):
        raise ConfigError("{} must be finite".format(location))
    if number <= 0:
        raise ConfigError("{} must be greater than zero".format(location))
    return number


def _budget(table, location):
    table = _closed_table(table, location, ("target_seconds", "maximum_seconds"))
    target = _positive_number(table["target_seconds"], location + ".target_seconds")
    maximum = _positive_number(table["maximum_seconds"], location + ".maximum_seconds")
    if maximum < 5.0:
        raise ConfigError("{}.maximum_seconds must be at least 5 seconds".format(location))
    if target > maximum:
        raise ConfigError("{}.target_seconds must not exceed maximum_seconds".format(location))
    return GateBudget(target, maximum)


def _string(value, location):
    if not isinstance(value, str) or not value:
        raise ConfigError("{} must be a non-empty string".format(location))
    return value


def _string_list(value, location):
    if not isinstance(value, list) or not value:
        raise ConfigError("{} must be a non-empty array of strings".format(location))
    strings = tuple(_string(item, "{}[{}]".format(location, index)) for index, item in enumerate(value))
    if len(set(strings)) != len(strings):
        raise ConfigError("{} must not contain duplicate values".format(location))
    return strings


def _validate_glob(pattern, location):
    pattern = _string(pattern, location)
    if "\\" in pattern:
        raise ConfigError("{} must use POSIX '/' separators".format(location))
    if pattern.startswith("/") or "\0" in pattern:
        raise ConfigError("{} must be a relative repository path glob".format(location))
    parts = pattern.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ConfigError("{} must not contain empty, '.' or '..' path segments".format(location))
    _compile_glob(pattern, location)
    return pattern


def _compile_glob(pattern, location="path glob"):
    pieces = ["^"]
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            end = index
            while end < len(pattern) and pattern[end] == "*":
                end += 1
            count = end - index
            if count == 1:
                pieces.append("[^/]*")
            elif count == 2 and (index == 0 or pattern[index - 1] == "/") and (
                end == len(pattern) or pattern[end] == "/"
            ):
                if end < len(pattern) and pattern[end] == "/":
                    pieces.append("(?:.*/)?")
                    end += 1
                else:
                    pieces.append(".*")
            else:
                raise ConfigError("{} has invalid '**' placement".format(location))
            index = end
            continue
        if character == "?":
            pieces.append("[^/]")
        elif character == "[":
            end = pattern.find("]", index + 1)
            if end < 0:
                raise ConfigError("{} has an unterminated character class".format(location))
            content = pattern[index + 1:end]
            if not content or "/" in content or "[" in content:
                raise ConfigError("{} has an invalid character class".format(location))
            negated = content.startswith("!")
            if negated:
                content = content[1:]
            if not content:
                raise ConfigError("{} has an empty character class".format(location))
            escaped = "".join("-" if item == "-" else re.escape(item) for item in content)
            pieces.append("[{}{}]".format("^" if negated else "", escaped))
            index = end
        elif character == "]":
            raise ConfigError("{} has an unmatched ']'".format(location))
        else:
            pieces.append(re.escape(character))
        index += 1
    pieces.append("$")
    try:
        return re.compile("".join(pieces))
    except re.error as error:
        raise ConfigError("{} is invalid: {}".format(location, error))


def _binding_globs(value, location):
    globs = _string_list(value, location)
    return tuple(sorted(_validate_glob(item, location) for item in globs))


def _critical_bindings(value):
    if not isinstance(value, list) or not value:
        raise ConfigError("testing.risk.critical must be a non-empty array of tables")
    bindings = []
    seen = set()
    for index, raw in enumerate(value):
        location = "testing.risk.critical[{}]".format(index)
        table = _closed_table(
            raw,
            location,
            ("category", "path_globs", "required_check_ids"),
        )
        category = _string(table["category"], location + ".category")
        if category not in MANDATORY_CRITICAL_CATEGORIES:
            raise ConfigError("{}.category is unknown: {}".format(location, category))
        if category in seen:
            raise ConfigError("testing.risk.critical repeats category '{}'".format(category))
        seen.add(category)
        checks = _string_list(table["required_check_ids"], location + ".required_check_ids")
        unknown_checks = sorted(set(checks) - KNOWN_CHECK_IDS)
        if unknown_checks:
            raise ConfigError(
                "{}.required_check_ids has unknown check id(s): {}".format(
                    location, ", ".join(unknown_checks)
                )
            )
        bindings.append(
            CriticalBinding(
                category,
                _binding_globs(table["path_globs"], location + ".path_globs"),
                tuple(sorted(checks)),
            )
        )
    missing = sorted(MANDATORY_CRITICAL_CATEGORIES - seen)
    if missing:
        raise ConfigError(
            "testing.risk.critical is missing mandatory category/categories: {}".format(
                ", ".join(missing)
            )
        )
    return tuple(sorted(bindings, key=_critical_sort_key))


def _reversible_bindings(value):
    if not isinstance(value, list) or not value:
        raise ConfigError("testing.risk.reversible must be a non-empty array of tables")
    bindings = []
    seen = set()
    for index, raw in enumerate(value):
        location = "testing.risk.reversible[{}]".format(index)
        table = _closed_table(raw, location, ("id", "path_globs"))
        binding_id = _string(table["id"], location + ".id")
        if not IDENTIFIER_RE.match(binding_id):
            raise ConfigError("{}.id must be lowercase kebab-case".format(location))
        if binding_id in seen:
            raise ConfigError("testing.risk.reversible repeats id '{}'".format(binding_id))
        seen.add(binding_id)
        bindings.append(
            ReversibleBinding(
                binding_id,
                _binding_globs(table["path_globs"], location + ".path_globs"),
            )
        )
    return tuple(sorted(bindings, key=_reversible_sort_key))


def parse_policy(document, source="<memory>"):
    """Parse and strictly validate one TOML policy document."""
    if isinstance(document, bytes):
        try:
            document = document.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ConfigError("{} is not valid UTF-8: {}".format(source, error))
    if not isinstance(document, str):
        raise TypeError("policy document must be bytes or text")
    try:
        raw = tomli.loads(document)
    except (tomli.TOMLDecodeError, ValueError) as error:
        raise ConfigError("{} is not valid TOML: {}".format(source, error))
    root = _closed_table(raw, "root", ("schema_version", "testing"))
    version = root["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != SCHEMA_VERSION:
        raise ConfigError("schema_version must be the integer {}".format(SCHEMA_VERSION))
    testing = _closed_table(
        root["testing"],
        "testing",
        ("routine", "final", "performance", "risk"),
    )
    routine = _budget(testing["routine"], "testing.routine")

    final_table = _closed_table(
        testing["final"],
        "testing.final",
        ("mode", "target_seconds", "maximum_seconds"),
        ("trigger",),
    )
    mode = _string(final_table["mode"], "testing.final.mode")
    if mode not in FINAL_MODES:
        raise ConfigError(
            "testing.final.mode must be one of: {}".format(", ".join(sorted(FINAL_MODES)))
        )
    trigger = final_table.get("trigger")
    if mode == "manual" and trigger is not None:
        raise ConfigError("testing.final.trigger must be omitted when mode is manual")
    if mode == "hard":
        if trigger is None:
            raise ConfigError("testing.final.trigger is required when mode is hard")
        trigger = _string(trigger, "testing.final.trigger")
        if trigger not in FINAL_TRIGGERS:
            raise ConfigError(
                "testing.final.trigger must be one of: {}".format(
                    ", ".join(sorted(FINAL_TRIGGERS))
                )
            )
    final_budget = _budget(
        {
            "target_seconds": final_table["target_seconds"],
            "maximum_seconds": final_table["maximum_seconds"],
        },
        "testing.final",
    )

    performance = _closed_table(
        testing["performance"],
        "testing.performance",
        ("on_budget_exceeded",),
    )
    action = _string(
        performance["on_budget_exceeded"],
        "testing.performance.on_budget_exceeded",
    )
    if action not in BUDGET_ACTIONS:
        raise ConfigError(
            "testing.performance.on_budget_exceeded must be one of: {}".format(
                ", ".join(sorted(BUDGET_ACTIONS))
            )
        )

    risk = _closed_table(
        testing["risk"],
        "testing.risk",
        ("unmatched", "critical", "reversible"),
    )
    unmatched = _string(risk["unmatched"], "testing.risk.unmatched")
    if unmatched != "critical":
        raise ConfigError("testing.risk.unmatched must be 'critical'")

    return TestGatePolicy(
        version,
        routine,
        FinalGate(mode, trigger, final_budget),
        action,
        _critical_bindings(risk["critical"]),
        _reversible_bindings(risk["reversible"]),
        True,
    )


def load_policy(path):
    """Read and validate one policy path."""
    policy_path = Path(path)
    try:
        document = policy_path.read_bytes()
    except OSError as error:
        raise ConfigError("could not read {}: {}".format(policy_path, error))
    return parse_policy(document, str(policy_path))


def union_policies(base, candidate):
    if not isinstance(base, TestGatePolicy) or not isinstance(candidate, TestGatePolicy):
        raise TypeError("policy union requires two TestGatePolicy values")
    return PolicyUnion(base, candidate)


def load_policy_union(base_path, candidate_path):
    return union_policies(load_policy(base_path), load_policy(candidate_path))


def _critical_sort_key(binding):
    return binding.name, binding.paths, binding.checks


def _reversible_sort_key(binding):
    return binding.id, binding.paths


def _unique_sorted(values, key):
    unique = {key(value): value for value in values}
    return tuple(unique[item] for item in sorted(unique))


def _normalized_path(path):
    if isinstance(path, PurePosixPath):
        path = str(path)
    if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
        raise ValueError("changed path must be a non-empty relative POSIX path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("changed path must not contain empty, '.' or '..' segments")
    return path


def _matches(pattern, path):
    return bool(_compile_glob(pattern).match(path))


def _classify_one(path, policy):
    critical = tuple(
        binding
        for binding in policy.critical_bindings
        if any(_matches(pattern, path) for pattern in binding.paths)
    )
    reversible = tuple(
        binding.id
        for binding in policy.reversible_bindings
        if any(_matches(pattern, path) for pattern in binding.paths)
    )
    if critical:
        return critical, (), False
    if reversible:
        return (), reversible, False
    return (), (), policy.unmatched_is_critical


def classify_paths(paths, policy):
    """Classify changed paths, with critical/unmatched results winning all overlap.

    A :class:`PolicyUnion` classifies each path against both versions separately.  The
    path is reversible only if neither version calls it critical or unmatched.  This
    is the downgrade-resistance boundary for a candidate policy change.
    """
    if isinstance(policy, PolicyUnion):
        policies = (policy.base, policy.candidate)
    elif isinstance(policy, TestGatePolicy):
        policies = (policy,)
    else:
        raise TypeError("classification requires TestGatePolicy or PolicyUnion")

    normalized_paths = tuple(sorted(set(_normalized_path(path) for path in paths)))
    critical_bindings = []
    reversible_ids = set()
    unmatched_paths = []
    critical_paths = []
    reversible_paths = []
    for path in normalized_paths:
        results = tuple(_classify_one(path, item) for item in policies)
        path_critical = tuple(binding for result in results for binding in result[0])
        path_unmatched = any(result[2] for result in results)
        if path_critical or path_unmatched:
            critical_bindings.extend(path_critical)
            critical_paths.append(path)
            if path_unmatched:
                unmatched_paths.append(path)
            continue
        path_reversible = {binding_id for result in results for binding_id in result[1]}
        if path_reversible:
            reversible_ids.update(path_reversible)
            reversible_paths.append(path)

    critical = _unique_sorted(critical_bindings, _critical_sort_key)
    checks = tuple(sorted({check for binding in critical for check in binding.checks}))
    if unmatched_paths:
        checks = tuple(sorted(set(checks) | KNOWN_CHECK_IDS))
    return RiskClassification(
        critical,
        tuple(sorted(reversible_ids)),
        tuple(unmatched_paths),
        checks,
        tuple(critical_paths),
        tuple(reversible_paths),
    )


def match_critical_paths(paths, policy):
    """Compatibility alias for callers interested only in critical classification."""
    return classify_paths(paths, policy)


def required_critical_checks(paths, policy):
    return classify_paths(paths, policy).required_check_ids


def _policy_payload(policy):
    return {
        "schema_version": policy.schema_version,
        "testing": {
            "final": {
                "maximum_seconds": policy.final.maximum_seconds,
                "mode": policy.final.mode,
                "target_seconds": policy.final.target_seconds,
                "trigger": policy.final.trigger,
            },
            "performance": {"on_budget_exceeded": policy.on_budget_exceeded},
            "risk": {
                "critical": [
                    {
                        "category": binding.name,
                        "path_globs": list(binding.paths),
                        "required_check_ids": list(binding.checks),
                    }
                    for binding in policy.critical_bindings
                ],
                "reversible": [
                    {"id": binding.id, "path_globs": list(binding.paths)}
                    for binding in policy.reversible_bindings
                ],
                "unmatched": "critical",
            },
            "routine": {
                "maximum_seconds": policy.routine.maximum_seconds,
                "target_seconds": policy.routine.target_seconds,
            },
        },
    }


def canonical_policy_json(policy):
    """Return normalized UTF-8 JSON bytes for receipts and policy comparison."""
    if isinstance(policy, TestGatePolicy):
        payload = _policy_payload(policy)
    elif isinstance(policy, PolicyUnion):
        payload = {
            "base": _policy_payload(policy.base),
            "candidate": _policy_payload(policy.candidate),
        }
    else:
        raise TypeError("canonical policy JSON requires TestGatePolicy or PolicyUnion")
    return json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_policy_digest(policy):
    """Return the lowercase SHA-256 of canonical normalized policy JSON."""
    return hashlib.sha256(canonical_policy_json(policy)).hexdigest()


__all__ = (
    "BUDGET_ACTIONS",
    "ConfigError",
    "CriticalBinding",
    "FINAL_MODES",
    "FINAL_TRIGGERS",
    "FinalGate",
    "GateBudget",
    "KNOWN_CHECK_IDS",
    "MANDATORY_CRITICAL_CATEGORIES",
    "PolicyUnion",
    "ReversibleBinding",
    "RiskClassification",
    "SCHEMA_VERSION",
    "TestGatePolicy",
    "canonical_policy_digest",
    "canonical_policy_json",
    "classify_paths",
    "load_policy",
    "load_policy_union",
    "match_critical_paths",
    "parse_policy",
    "required_critical_checks",
    "union_policies",
)
