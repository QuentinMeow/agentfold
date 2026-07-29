"""Exact snapshot and semantic contract for the manual GitHub diagnostics."""
import hashlib
import re
from pathlib import Path


HARD_WORKFLOW_SHA256 = "d3d2882bbe3a701071de68ffeb58b9c2d8d59371e75c660b7255fc6f0b55d4c3"
MANUAL_WORKFLOW_SHA256 = "d7f5dfdb98eb3d34ef46c577eb1e99ba04a42c58ccff52b718fa63d2e3f69ab0"
PINNED_CHECKOUT = "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
FIXTURE = Path(__file__).resolve().with_name("fixtures") / "manual-harness.yml"
JOB_HEADER_RE = re.compile(r"^  (?P<name>[a-z][a-z0-9-]*):\n", re.MULTILINE)
TRUSTED_GATE_JOBS = (
    "prepare-trusted-final-test-gate",
    "trusted-final-test-runner",
    "publish-trusted-final-test-check",
)
MANUAL_JOBS = (
    "push-repository-diagnostics",
    "trusted-pr-merge-diagnostics",
    "cooperative-pr-complete-test-diagnostics",
    "authoritative-external-action-projection",
    "external-source-release-admission",
    "review-state-action-projection",
)
MANUAL_CHECKOUT_COUNTS = {
    "push-repository-diagnostics": 1,
    "trusted-pr-merge-diagnostics": 1,
    "cooperative-pr-complete-test-diagnostics": 1,
    "authoritative-external-action-projection": 2,
    "external-source-release-admission": 1,
    "review-state-action-projection": 1,
}
MANUAL_PERMISSION_BLOCKS = {
    "push-repository-diagnostics": "    permissions:\n      contents: read\n",
    "trusted-pr-merge-diagnostics": "    permissions:\n      contents: read\n",
    "cooperative-pr-complete-test-diagnostics": (
        "    permissions:\n      contents: read\n"
    ),
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
    """Return the byte-exact admitted workflow, pinned by the digest above."""
    workflow = FIXTURE.read_bytes()
    if workflow_digest(workflow) != MANUAL_WORKFLOW_SHA256:
        raise AssertionError("base-pinned manual workflow fixture digest changed")
    return workflow


def workflow_job(workflow, name):
    """Return one exact job block by its real workflow identity."""
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
    """Admit only the exact manual diagnostic workflow snapshot."""
    digest = workflow_digest(workflow)
    if digest == MANUAL_WORKFLOW_SHA256:
        try:
            if workflow == manual_workflow_fixture():
                return "absent"
        except AssertionError:
            pass
    return "invalid"


def manualize_hard_workflow(workflow):
    """The retired hard workflow has no automatic transformation anymore."""
    if workflow_digest(workflow) != HARD_WORKFLOW_SHA256:
        raise AssertionError("manual transformation requires the retired hard snapshot")
    raise AssertionError("the retired hard snapshot must not be transformed automatically")


def _job_display_names(workflow):
    names = []
    for job_name in workflow_job_names(workflow):
        job = workflow_job(workflow, job_name)
        matches = re.findall(r"^    name: (.+)$", job, re.MULTILINE)
        if len(matches) != 1:
            return (), "job {!r} must have exactly one explicit name".format(job_name)
        names.append(matches[0])
    return tuple(names), ""


def manual_fixture_contract_errors(workflow):
    """Explain authority, topology, or trust-boundary drift in a candidate fixture."""
    try:
        workflow = decode_workflow(workflow)
    except (AssertionError, TypeError, UnicodeDecodeError) as error:
        return ("manual workflow bytes are invalid: {}".format(error),)

    errors = []
    if workflow_job_names(workflow) != MANUAL_JOBS:
        errors.append("manual workflow job set or order changed")
    if "\npermissions: {}\n\njobs:\n" not in workflow:
        errors.append("manual workflow lacks exact empty top-level permissions")
    on_block = workflow.partition("on:\n")[2].partition("\npermissions:")[0]
    for event in ("push:\n", "pull_request:\n", "pull_request_target:\n"):
        if event not in on_block:
            errors.append("manual workflow lacks event {}".format(event.rstrip()))
    if "merge_group" in on_block:
        errors.append("manual workflow retains merge_group admission")
    if "reconcile" + "-and-test" in workflow:
        errors.append("manual workflow retains the retired combined identity")

    display_names, display_error = _job_display_names(workflow)
    if display_error:
        errors.append(display_error)
    elif len(set(display_names)) != len(display_names):
        errors.append("manual workflow has duplicate explicit job names")

    uses_lines = tuple(
        line.strip().partition("uses: ")[2]
        for line in workflow.splitlines()
        if line.strip().startswith(("uses: ", "- uses: "))
    )
    expected_checkout_count = sum(MANUAL_CHECKOUT_COUNTS.values())
    if uses_lines != (PINNED_CHECKOUT,) * expected_checkout_count:
        errors.append("manual workflow action set changed")
    for name in MANUAL_JOBS:
        job = workflow_job(workflow, name)
        if job.count(MANUAL_PERMISSION_BLOCKS[name]) != 1:
            errors.append("manual permissions changed for {}".format(name))
        if re.search(r"^      [a-z-]+: (?:write|write-all)\s*$", job, re.MULTILINE):
            errors.append("manual workflow grants write permission for {}".format(name))
        checkout_count = job.count("uses: {}".format(PINNED_CHECKOUT))
        if checkout_count != MANUAL_CHECKOUT_COUNTS[name]:
            errors.append("manual checkout count changed for {}".format(name))
        if job.count("persist-credentials: false") != checkout_count:
            errors.append("checkout credentials persist for {}".format(name))
        if job.count("runs-on: ubuntu-latest") != 1:
            errors.append("manual runner changed for {}".format(name))

    lowered = workflow.lower()
    forbidden_fragments = (
        "environment:",
        "secrets.",
        "vars.",
        "id-token:",
        "authorization: bearer",
        "gh_token",
        "actions/create-github-app-token",
        "statuses: write",
        "checks: write",
        "/statuses/",
        "/check-runs",
        "createcommitstatus",
        "createcheckrun",
        "actions_id_token_request_url",
        "actions_id_token_request_token",
        "--provider-hard",
    )
    for fragment in forbidden_fragments:
        if fragment in lowered:
            errors.append("manual workflow contains forbidden surface {}".format(fragment))
    if re.search(r"(?im)^\s*[a-z0-9_]*pat[a-z0-9_]*\s*:", workflow):
        errors.append("manual workflow contains a PAT binding")
    if re.search(r"(?i)/commits/[^\s]+/status(?:\s|$)", workflow):
        errors.append("manual workflow contains a status publisher endpoint")

    push = workflow_job(workflow, "push-repository-diagnostics")
    for expected in (
        "    name: Push repository diagnostics (not a merge gate)\n",
        "    if: ${{ github.event_name == 'push' }}\n",
        "automation/reconcile/reconcile.py --check",
        'QUEUE_DISPLACED_ARGS=(--displaced-tip "$QUEUE_PUSH_BEFORE")',
    ):
        if expected not in push:
            errors.append("push diagnostics contract changed: missing {}".format(expected))
    if "automation/run_tests.py" in push or "automation/run_test_gate.py" in push:
        errors.append("push diagnostics execute repository tests")

    trusted = workflow_job(workflow, "trusted-pr-merge-diagnostics")
    trusted_expected = (
        "    name: PR core and merge diagnostics (non-enforcing)\n",
        "    if: ${{ github.event_name == 'pull_request_target' }}\n",
        "ref: ${{ github.event.pull_request.base.sha }}",
        '"+refs/pull/$MERGE_DIAGNOSTIC_PR_NUMBER/merge:refs/agentfold/diagnostics/pr-merge"',
        "MERGE_DIAGNOSTIC_CANDIDATE: ${{ github.event.pull_request.merge_commit_sha }}",
        'test "$MERGE_DIAGNOSTIC_FETCHED" = "$MERGE_DIAGNOSTIC_CANDIDATE"',
        '"$MERGE_DIAGNOSTIC_CANDIDATE^1"',
        '"$MERGE_DIAGNOSTIC_CANDIDATE^2"',
        'MERGE_DIAGNOSTIC_DISPLACED_TIP: ${{ github.event.action == \'synchronize\' && github.event.before || \'\' }}',
        "python3 automation/check_core_scope.py \\",
        (
            '--range "$MERGE_DIAGNOSTIC_BASE...$MERGE_DIAGNOSTIC_CANDIDATE" '
            '\\\n            --branch "$MERGE_DIAGNOSTIC_BRANCH"'
        ),
        "python3 automation/reconcile/reconcile.py --check \\",
        "--at-transition merge \\",
        '--displaced-tip "$MERGE_DIAGNOSTIC_DISPLACED_TIP"',
    )
    for expected in trusted_expected:
        if expected not in trusted:
            errors.append("trusted PR diagnostics contract changed: missing {}".format(expected))
    exact_range = '--range "$MERGE_DIAGNOSTIC_BASE...$MERGE_DIAGNOSTIC_CANDIDATE"'
    if trusted.count(exact_range) != 2:
        errors.append("trusted PR diagnostics exact base-to-candidate ranges changed")
    if trusted.count("if [ \"$MERGE_DIAGNOSTIC_ACTION\" = synchronize ]; then") != 2:
        errors.append("trusted PR diagnostics displaced-tip action guard changed")
    trusted_python = tuple(
        line.strip() for line in trusted.splitlines() if line.strip().startswith("python3 ")
    )
    if trusted_python != (
        "python3 automation/check_core_scope.py \\",
        "python3 automation/reconcile/reconcile.py --check \\",
    ):
        errors.append("trusted PR diagnostics execute code outside the two base scripts")
    for forbidden in (
        "git checkout",
        "git switch",
        "git worktree",
        "automation/run_tests.py",
        "automation/run_test_gate.py",
        "pytest",
        "unittest",
    ):
        if forbidden in trusted:
            errors.append("trusted PR diagnostics contain candidate execution surface {}".format(forbidden))

    cooperative = workflow_job(
        workflow, "cooperative-pr-complete-test-diagnostics"
    )
    for expected in (
        "    name: Cooperative PR complete tests (not a merge gate)\n",
        "    if: ${{ github.event_name == 'pull_request' }}\n",
        "persist-credentials: false",
    ):
        if expected not in cooperative:
            errors.append("cooperative PR diagnostics contract changed: missing {}".format(expected))
    run_lines = tuple(
        line.strip() for line in cooperative.splitlines() if line.startswith("        run:")
    )
    if run_lines != ("run: python3 automation/run_tests.py",):
        errors.append("cooperative PR diagnostics run more than the complete test command")
    candidate_executors = tuple(
        name
        for name in MANUAL_JOBS
        if "automation/run_tests.py" in workflow_job(workflow, name)
        or "automation/run_test_gate.py" in workflow_job(workflow, name)
    )
    if candidate_executors != ("cooperative-pr-complete-test-diagnostics",):
        errors.append("cooperative PR diagnostics are not the sole candidate executor")
    return tuple(errors)


def _text_migration_mutations(manual):
    """Return representative authority and trust-boundary mutation canaries."""
    trusted = workflow_job(manual, "trusted-pr-merge-diagnostics")
    return (
        ("renamed-job", manual.replace(
            "  push-repository-diagnostics:\n", "  renamed-diagnostics:\n", 1
        )),
        ("quoted-job", manual.replace(
            "  push-repository-diagnostics:\n", '  "push-repository-diagnostics":\n', 1
        )),
        ("duplicate-job", manual + "\n" + trusted),
        ("retired-identity", manual.replace(
            "push-repository-diagnostics", "reconcile" + "-and-test", 1
        )),
        ("duplicate-display-name", manual.replace(
            "PR core and merge diagnostics (non-enforcing)",
            "Push repository diagnostics (not a merge gate)",
            1,
        )),
        ("status-writer", manual.replace(
            "      contents: read\n", "      contents: read\n      statuses: write\n", 1
        )),
        ("check-writer", manual.replace(
            "      contents: read\n", "      contents: read\n      checks: write\n", 1
        )),
        ("secret-pat", manual.replace(
            "        run: python3 automation/run_tests.py\n",
            "        env:\n          RELEASE_PAT: ${{ secrets.RELEASE_PAT }}\n"
            "        run: python3 automation/run_tests.py\n",
            1,
        )),
        ("app-token-action", manual +
            "\n  app-token-broker:\n    name: App token broker\n"
            "    permissions: {}\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/create-github-app-token@"
            "bcd2ba49218906704ab6c1aa796996da409d3eb1\n"),
        ("oidc-broker", manual +
            "\n  oidc-broker:\n    name: OIDC broker\n    permissions:\n"
            "      id-token: write\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: curl \"$ACTIONS_ID_TOKEN_REQUEST_URL\"\n"),
        ("status-endpoint", manual +
            "\n  status-publisher:\n    name: Status publisher\n"
            "    permissions: {}\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: gh api repos/x/y/commits/deadbeef/status\n"),
        ("check-endpoint", manual +
            "\n  check-publisher:\n    name: Check publisher\n"
            "    permissions: {}\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: curl -X POST https://api.github.invalid/repos/x/y/check-runs\n"),
        ("provider-hard", manual.replace(
            "        run: python3 automation/run_tests.py\n",
            "        run: python3 automation/run_tests.py --provider-hard\n",
            1,
        )),
        ("candidate-checkout", manual.replace(
            "          ref: ${{ github.event.pull_request.base.sha }}\n",
            "          ref: ${{ github.event.pull_request.merge_commit_sha }}\n",
            1,
        )),
        ("candidate-execution-in-trusted-job", manual.replace(
            "          python3 automation/check_core_scope.py \\\n",
            "          python3 automation/run_tests.py\n"
            "          python3 automation/check_core_scope.py \\\n",
            1,
        )),
        ("missing-head-parent-check", manual.replace(
            '              "$MERGE_DIAGNOSTIC_CANDIDATE^2"\n',
            '              "$MERGE_DIAGNOSTIC_CANDIDATE^3"\n',
            1,
        )),
        ("wrong-core-range", manual.replace(
            '--range "$MERGE_DIAGNOSTIC_BASE...$MERGE_DIAGNOSTIC_CANDIDATE"',
            '--range "$MERGE_DIAGNOSTIC_BASE..$MERGE_DIAGNOSTIC_CANDIDATE"',
            1,
        )),
        ("candidate-execution-in-push", manual.replace(
            "      - name: Reconciler — every harness invariant holds\n",
            "      - name: Candidate tests leaked into push\n"
            "        run: python3 automation/run_tests.py\n"
            "      - name: Reconciler — every harness invariant holds\n",
            1,
        )),
    )


def migration_mutations(manual):
    """Return raw-byte authority, topology, trust, and line-ending mutations."""
    text = decode_workflow(manual)
    mutations = tuple(
        (name, mutation.encode("utf-8"))
        for name, mutation in _text_migration_mutations(text)
    )
    return mutations + (("crlf-raw-bytes", manual.replace(b"\n", b"\r\n")),)
