"""Closed two-snapshot admission floor for the hard-to-manual gate boundary."""
import hashlib
import re
from pathlib import Path


HARD_WORKFLOW_SHA256 = "d3d2882bbe3a701071de68ffeb58b9c2d8d59371e75c660b7255fc6f0b55d4c3"
MANUAL_WORKFLOW_SHA256 = "a07b4751a93e11534586ffebe33e5a34af47f4900568493eea57bcd350a66cf1"
PINNED_CHECKOUT = "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
FIXTURE = Path(__file__).resolve().with_name("fixtures") / "manual-harness.yml"
JOB_HEADER_RE = re.compile(r"^  (?P<name>[a-z][a-z0-9-]*):\n", re.MULTILINE)
TRUSTED_GATE_JOBS = (
    "prepare-trusted-final-test-gate",
    "trusted-final-test-runner",
    "publish-trusted-final-test-check",
)
MANUAL_JOBS = (
    "reconcile-and-test",
    "authoritative-external-action-projection",
    "external-source-release-admission",
    "review-state-action-projection",
)
MANUAL_CHECKOUT_COUNTS = {
    "reconcile-and-test": 1,
    "authoritative-external-action-projection": 2,
    "external-source-release-admission": 1,
    "review-state-action-projection": 1,
}
MANUAL_READ_TOKEN_COUNTS = {
    "reconcile-and-test": 0,
    "authoritative-external-action-projection": 3,
    "external-source-release-admission": 1,
    "review-state-action-projection": 2,
}
MANUAL_PERMISSION_BLOCKS = {
    "reconcile-and-test": "    permissions:\n      contents: read\n",
    "authoritative-external-action-projection": (
        "    permissions:\n"
        "      contents: read\n"
        "      issues: read\n"
        "      pull-requests: read\n"
    ),
    "external-source-release-admission": (
        "    permissions:\n"
        "      contents: read\n"
        "      issues: read\n"
        "      pull-requests: read\n"
    ),
    "review-state-action-projection": (
        "    permissions:\n"
        "      contents: read\n"
        "      issues: read\n"
        "      pull-requests: read\n"
    ),
}


def workflow_digest(workflow):
    if not isinstance(workflow, bytes):
        raise TypeError("workflow snapshot identity requires raw bytes")
    return hashlib.sha256(workflow).hexdigest()


def decode_workflow(workflow):
    """Decode an LF-only UTF-8 snapshot only after byte-level classification."""
    if not isinstance(workflow, bytes):
        raise TypeError("workflow snapshot must be raw bytes")
    if b"\r" in workflow or not workflow.endswith(b"\n"):
        raise AssertionError("workflow snapshot must be LF-only and newline-terminated")
    text = workflow.decode("utf-8", errors="strict")
    if text.encode("utf-8") != workflow:
        raise AssertionError("workflow snapshot does not round-trip through UTF-8")
    return text


def manual_workflow_fixture():
    workflow = FIXTURE.read_bytes()
    if workflow_digest(workflow) != MANUAL_WORKFLOW_SHA256:
        raise AssertionError("base-pinned manual workflow fixture digest changed")
    return workflow


def workflow_job(workflow, name):
    jobs = workflow.partition("\njobs:\n")[2]
    matches = list(JOB_HEADER_RE.finditer(jobs))
    for index, match in enumerate(matches):
        if match.group("name") != name:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(jobs)
        return jobs[match.start():end]
    return ""


def workflow_job_names(workflow):
    jobs = workflow.partition("\njobs:\n")[2]
    return tuple(match.group("name") for match in JOB_HEADER_RE.finditer(jobs))


def trusted_gate_regime(workflow):
    """Admit only the exact hard snapshot or the exact base-pinned manual fixture."""
    digest = workflow_digest(workflow)
    if digest == HARD_WORKFLOW_SHA256:
        return "present"
    if digest == MANUAL_WORKFLOW_SHA256 and workflow == manual_workflow_fixture():
        return "absent"
    return "invalid"


def _replace_exact(workflow, old, new, expected_count):
    actual_count = workflow.count(old)
    if actual_count != expected_count:
        raise AssertionError(
            "hard workflow transformation source changed: expected {} occurrence(s), got {}"
            .format(expected_count, actual_count)
        )
    return workflow.replace(old, new)


def manualize_hard_workflow(workflow):
    """Apply the one approved deterministic hard-to-manual snapshot transformation."""
    if workflow_digest(workflow) != HARD_WORKFLOW_SHA256:
        raise AssertionError("manual transformation requires the exact hard snapshot")
    transformed = decode_workflow(workflow)
    for name in TRUSTED_GATE_JOBS:
        job = workflow_job(transformed, name)
        if not job:
            raise AssertionError("hard workflow is missing gate job {!r}".format(name))
        transformed = _replace_exact(transformed, job, "", 1)
    transformed = _replace_exact(
        transformed,
        "  merge_group:\n    types: [checks_requested]\n",
        "",
        1,
    )
    transformed = _replace_exact(
        transformed,
        "  push:\n  pull_request_target:\n",
        "  push:\n  pull_request:\n  pull_request_target:\n",
        1,
    )
    transformed = _replace_exact(
        transformed,
        "permissions:\n  contents: read\n  issues: read\n  pull-requests: read",
        "permissions: {}",
        1,
    )
    transformed = _replace_exact(
        transformed,
        "    if: ${{ github.event_name == 'push' }}",
        "    if: ${{ github.event_name == 'push' || "
        "github.event_name == 'pull_request' }}",
        1,
    )
    for name in MANUAL_JOBS:
        job = workflow_job(transformed, name)
        if not job:
            raise AssertionError("manual workflow is missing job {!r}".format(name))
        changed = _replace_exact(
            job,
            "    runs-on: ubuntu-latest\n",
            MANUAL_PERMISSION_BLOCKS[name] + "    runs-on: ubuntu-latest\n",
            1,
        )
        transformed = _replace_exact(transformed, job, changed, 1)
    transformed = _replace_exact(
        transformed, "actions/checkout@v4", PINNED_CHECKOUT, 5
    )
    transformed = _replace_exact(
        transformed,
        "uses: {}\n        with:\n          fetch-depth: 0".format(
            PINNED_CHECKOUT
        ),
        "uses: {}\n        with:\n          fetch-depth: 0\n"
        "          persist-credentials: false".format(PINNED_CHECKOUT),
        5,
    )
    transformed = _replace_exact(
        transformed,
        '            "${QUEUE_DISPLACED_ARGS[@]}"\n\n'
        "  authoritative-external-action-projection:",
        '            "${QUEUE_DISPLACED_ARGS[@]}"\n'
        "      - name: Complete test diagnostics — pull requests\n"
        "        if: github.event_name == 'pull_request'\n"
        "        run: python3 automation/run_tests.py\n\n"
        "  authoritative-external-action-projection:",
        1,
    )
    return transformed.encode("utf-8")


def manual_fixture_contract_errors(workflow):
    """Explain accidental weakening of the intended manual snapshot."""
    workflow = decode_workflow(workflow)
    errors = []
    if workflow_job_names(workflow) != MANUAL_JOBS:
        errors.append("manual workflow job set or order changed")
    if "\npermissions: {}\n\njobs:\n" not in workflow:
        errors.append("manual workflow lacks exact empty top-level permissions")
    if "  pull_request:\n" not in workflow or "  pull_request_target:\n" not in workflow:
        errors.append("manual workflow event split changed")
    if "merge_group" in workflow:
        errors.append("manual workflow retains merge_group admission")
    for name in TRUSTED_GATE_JOBS:
        if workflow_job(workflow, name):
            errors.append("manual workflow retains hard-gate job {}".format(name))
    uses_lines = tuple(
        line.strip().partition("uses: ")[2]
        for line in workflow.splitlines()
        if line.strip().startswith(("uses: ", "- uses: "))
    )
    if uses_lines != (PINNED_CHECKOUT,) * 5:
        errors.append("manual workflow action set changed")
    for name in MANUAL_JOBS:
        job = workflow_job(workflow, name)
        if job.count(MANUAL_PERMISSION_BLOCKS[name]) != 1:
            errors.append("manual permissions changed for {}".format(name))
        if re.search(r"^      .*: (?:write|write-all)\s*$", job, re.MULTILINE):
            errors.append("manual workflow grants write permission for {}".format(name))
        checkout_count = job.count("uses: {}".format(PINNED_CHECKOUT))
        if checkout_count != MANUAL_CHECKOUT_COUNTS[name]:
            errors.append("manual checkout count changed for {}".format(name))
        if job.count("persist-credentials: false") != checkout_count:
            errors.append("checkout credentials persist for {}".format(name))
        if job.count("runs-on: ubuntu-latest") != 1:
            errors.append("manual runner changed for {}".format(name))
        token_count = job.count("GITHUB_TOKEN: ${{ github.token }}")
        if token_count != MANUAL_READ_TOKEN_COUNTS[name]:
            errors.append("manual read-token binding changed for {}".format(name))
    forbidden = (
        "environment:",
        "secrets.",
        "vars.",
        "id-token",
        "authorization: bearer",
        "gh_token",
        "actions/create-github-app-token",
        "statuses: write",
        "checks: write",
        "/statuses/",
        "/check-runs",
        "createcommitstatus",
        "createcheckrun",
    )
    lowered = workflow.lower()
    for fragment in forbidden:
        if fragment in lowered:
            errors.append("manual workflow contains forbidden surface {}".format(fragment))
    reconcile = workflow_job(workflow, "reconcile-and-test")
    if (
        "github.event_name == 'pull_request'" not in reconcile
        or "python3 automation/run_tests.py" not in reconcile
    ):
        errors.append("manual pull-request diagnostics are missing")
    return tuple(errors)


def _text_migration_mutations(manual):
    """Return representative authority and topology mutations for both suites."""
    reconcile = workflow_job(manual, "reconcile-and-test")
    return (
        (
            "renamed-job",
            manual.replace("  reconcile-and-test:\n", "  renamed-diagnostics:\n", 1),
        ),
        (
            "quoted-job",
            manual.replace("  reconcile-and-test:\n", '  "reconcile-and-test":\n', 1),
        ),
        ("duplicate-job", manual + "\n" + reconcile),
        (
            "generic-status-writer-context-split",
            manual
            + "\n  generic-result-writer:\n"
            "    permissions:\n"
            "      statuses: write\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - env:\n"
            "          GH_TOKEN: ${{ github.token }}\n"
            "        run: >-\n"
            "          gh api repos/${{ github.repository }}/\n"
            "          statuses/${{ github.sha }}\n",
        ),
        (
            "check-run-writer",
            manual
            + "\n  generic-check-writer:\n"
            "    permissions:\n"
            "      checks: write\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: gh api repos/x/y/check-runs\n",
        ),
        (
            "secret-pat",
            manual.replace(
                "        run: python3 automation/run_tests.py\n",
                "        env:\n"
                "          RELEASE_PAT: ${{ secrets.RELEASE_PAT }}\n"
                "        run: python3 automation/run_tests.py\n",
                1,
            ),
        ),
        (
            "app-token-action",
            manual
            + "\n  app-token-broker:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/create-github-app-token@"
            "bcd2ba49218906704ab6c1aa796996da409d3eb1\n",
        ),
        (
            "oidc-broker",
            manual
            + "\n  oidc-broker:\n"
            "    permissions:\n"
            "      id-token: write\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: curl \"$ACTIONS_ID_TOKEN_REQUEST_URL\"\n",
        ),
        (
            "alternate-status-endpoint",
            manual
            + "\n  alternate-status-writer:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: gh api repos/x/y/commits/deadbeef/status\n",
        ),
        (
            "alternate-check-endpoint",
            manual
            + "\n  alternate-check-writer:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: curl -X POST https://api.github.invalid/repos/x/y/check-runs\n",
        ),
        (
            "duplicate-authority-inside",
            manual.replace(
                "        run: python3 automation/run_tests.py\n",
                "        run: python3 automation/run_tests.py # --provider-hard\n",
                1,
            ),
        ),
        (
            "duplicate-authority-outside",
            manual
            + "\n  renamed-hard-authority:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: --provider-hard\n",
        ),
    )


def migration_mutations(manual):
    """Return raw-byte authority, topology, and line-ending mutations."""
    text = decode_workflow(manual)
    mutations = tuple(
        (name, mutation.encode("utf-8"))
        for name, mutation in _text_migration_mutations(text)
    )
    return mutations + (("crlf-raw-bytes", manual.replace(b"\n", b"\r\n")),)
