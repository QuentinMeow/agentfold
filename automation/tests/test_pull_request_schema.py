"""The pull-request body schema must satisfy the boundary check it is written for.

`templates/pull-request.md` prescribes a section order, folded `<details>` sections, and a
`What to review` section. `automation/check_action_projection.py` decides at the provider
boundary whether a body is acceptable. A schema that a filled body cannot satisfy would
be discovered one failing pull request at a time, so it is proven here instead.

These tests build bodies in the schema's exact shape and assert the check's verdict. They
do not read the template file for its prose: an unfilled template is not a body, and
asserting on wording would break on every edit. What they hold fixed is the structure —
which is what the check actually reads.
"""

import contextlib
import importlib.util
import re
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


AUTOMATION = Path(__file__).resolve().parents[1]
REPO = AUTOMATION.parent
SPEC = importlib.util.spec_from_file_location(
    "check_action_projection", AUTOMATION / "check_action_projection.py"
)
PROJECTION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROJECTION)

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TEMPLATE = REPO / "templates/pull-request.md"
GITHUB_ADAPTER = REPO / ".github/pull_request_template.md"

QUEUE_DIR = "message-queue/needs-human/reviews"
QUEUE_NAME = "non-blocking-review-the-explanation-skill.md"
QUEUE_PATH = f"{QUEUE_DIR}/{QUEUE_NAME}"
TASK_ID = "2026-08-01-write-the-explanation-skill"
ACTION = "Say whether this is the standard every human-facing message is held to."

FOLDED_SECTIONS = """
## What changed and why

<details>
<summary>The whole picture — no other reading required</summary>

### What this is

The reconciler is the script that checks every repository invariant before a commit.

</details>

## Changes

<details>
<summary>What a reader would notice, then the files</summary>

- A branch is no longer blocked by a review it filed itself.

| Area | Files | Why |
|---|---|---|
| Merge boundary | `automation/reconcile/reconcile.py` | Skips an action the range itself filed. |

</details>

## Verification

<details>
<summary>Commands actually run, and their real output</summary>

```
$ python3 automation/reconcile/reconcile.py --check
reconcile: 0 blocking finding(s)
```

</details>
"""

TLDR = """## TL;DR

1. **A branch no longer blocks itself.** Before, a pull request that filed its own review
   could never merge. Now the check skips it and reports it at the next boundary.
2. **Three stuck branches can merge.** Before, all three were permanently refused.
"""

STACK_NOTE = """> [!NOTE]
> **Layer 2 of 4.** Stacked on #61 (`task/2026-08-01-write-the-explanation-skill`); its
> base is that branch, not `main`. The stack lands bottom-up.
"""


def run_git(root, *args):
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class PullRequestSchemaTest(unittest.TestCase):
    """Every assertion here is about structure the boundary check reads."""

    @contextlib.contextmanager
    def repo(self, with_item=True):
        """A throwaway Git repository holding one live queue item.

        The check resolves every projected link against tracked repository content, so
        the item has to exist and be tracked; an untracked file reads as a dead link.
        """
        root = Path(tempfile.mkdtemp(prefix="agentfold-pr-schema-"))
        try:
            env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
            subprocess.run(
                ["git", "init", "-q"], cwd=root, check=True, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            run_git(root, "config", "user.name", "Test")
            run_git(root, "config", "user.email", "test@example.invalid")
            if not with_item:
                (root / "README.md").write_text("# fixture\n", encoding="utf-8")
                run_git(root, "add", ".")
                yield root
                return
            item = root / QUEUE_PATH
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_text(
                "# Is this the standard?\n\n"
                f"**Action:** {ACTION}\n"
                "**Why this matters:** Every later message is written to it.\n"
                "**If you do nothing:** The standard stands and nothing stops.\n",
                encoding="utf-8",
            )
            task = root / f"tasks/1_in-progress/{TASK_ID}/task.md"
            task.parent.mkdir(parents=True, exist_ok=True)
            task.write_text(
                "# Task\n\n"
                f"**Queue actions:** `{QUEUE_PATH}`\n",
                encoding="utf-8",
            )
            run_git(root, "add", ".")
            yield root
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def findings(self, root, body, **kwargs):
        return PROJECTION.projection_findings(
            body,
            ("What to review",),
            repo=root,
            **kwargs,
        )

    def body(self, action_section, stack_note=""):
        parts = [part for part in (stack_note, TLDR, action_section, FOLDED_SECTIONS) if part]
        return "\n".join(parts)

    def test_schema_shaped_body_with_a_ranked_action_list_passes(self):
        """The shape the schema prescribes is accepted, indented context included."""
        with self.repo() as root:
            action_section = (
                "## What to review\n\n"
                f"1. [{ACTION}]({QUEUE_PATH})\n"
                "   - Why this matters: Every later message is written to it.\n"
                "   - If you do nothing: The standard stands and nothing stops.\n"
            )
            self.assertEqual([], self.findings(root, self.body(action_section)))

    def test_the_stack_note_alert_does_not_look_like_an_unqueued_ask(self):
        """A top-level `> [!NOTE]` stack banner is declarative, so it must not fail."""
        with self.repo() as root:
            action_section = (
                "## What to review\n\n"
                f"1. [{ACTION}]({QUEUE_PATH})\n"
                "   - Why this matters: Every later message is written to it.\n"
            )
            self.assertEqual(
                [],
                self.findings(root, self.body(action_section, STACK_NOTE)),
            )

    def test_absolute_commit_pinned_links_are_accepted(self):
        """The form GitHub actually renders is the form the check accepts."""
        with self.repo() as root:
            revision = "0" * 40
            prefix = f"https://github.com/OWNER/REPO/blob/{revision}"
            action_section = (
                "## What to review\n\n"
                f"1. [{ACTION}]({prefix}/{QUEUE_PATH})\n"
                "   - If you do nothing: The standard stands and nothing stops.\n"
            )
            self.assertEqual(
                [],
                self.findings(
                    root,
                    self.body(action_section),
                    allowed_url_prefixes=(prefix,),
                ),
            )

    def test_no_action_acknowledgement_is_accepted_when_nothing_is_live(self):
        """With no live item in scope, the schema's empty case passes as written."""
        with self.repo(with_item=False) as root:
            body = self.body("## What to review\n\nNo queued action requested.\n")
            self.assertEqual([], self.findings(root, body, queue_actor="any"))

    def test_claiming_no_action_while_one_is_live_is_refused(self):
        """The empty case is a fact about the queue, not a choice the author makes."""
        with self.repo() as root:
            body = self.body("## What to review\n\nNo queued action requested.\n")
            findings = self.findings(
                root, body, queue_actor="any", task_scope=(TASK_ID,)
            )
            self.assertTrue(findings)
            self.assertIn("claims no queued action", findings[0])

    def test_omitting_a_live_action_is_refused(self):
        """A body cannot quietly drop an item the task in scope still owes."""
        with self.repo() as root:
            body = self.body(
                "## What to review\n\n"
                "1. [Something else](https://example.invalid/other)\n"
            )
            findings = self.findings(root, body, task_scope=(TASK_ID,))
            self.assertTrue(findings)

    def test_an_unfilled_template_fails_closed(self):
        """Submitting the skeleton unchanged must be refused, not silently accepted."""
        with self.repo() as root:
            unfilled = (
                "## What to review\n\n"
                "1. [<the queue item's Action, summarised>]"
                "(https://github.com/<owner>/<repo>/blob/<full-sha>/"
                "message-queue/needs-human/<kind>/<prefixed-name>.md)\n"
            )
            findings = self.findings(root, self.body(unfilled))
            self.assertTrue(findings)
            self.assertIn("valid canonical", findings[0])

    def test_permission_phrasing_outside_the_action_section_is_refused(self):
        """"can now merge" reads as permission to act, so it fails outside the list.

        This is the trap the schema warns about: prose that describes a capability can
        be indistinguishable from prose that grants one. The repair is the indicative
        with a named subject, which the passing half of this test shows.
        """
        with self.repo() as root:
            action_section = (
                "## What to review\n\n"
                f"1. [{ACTION}]({QUEUE_PATH})\n"
            )
            permissive = self.body(action_section) + (
                "\n## Notes\n\nA branch that filed its own review can now merge.\n"
            )
            findings = self.findings(root, permissive)
            self.assertTrue(findings)
            self.assertIn("outside the declared action section", findings[0])

            indicative = self.body(action_section) + (
                "\n## Notes\n\nA branch is no longer blocked by a review it filed "
                "itself.\n"
            )
            self.assertEqual([], self.findings(root, indicative))

    def test_an_ask_outside_the_action_section_is_refused(self):
        """Folded prose stays declarative; the ask lives in one place only."""
        with self.repo() as root:
            action_section = (
                "## What to review\n\n"
                f"1. [{ACTION}]({QUEUE_PATH})\n"
            )
            leaking = self.body(action_section) + (
                "\n## Notes\n\n<details>\n<summary>Anything optional</summary>\n\n"
                "Could you also decide whether the gate should be hard?\n\n"
                "</details>\n"
            )
            self.assertTrue(self.findings(root, leaking))

    def test_the_schema_and_its_github_adapter_both_exist_and_agree(self):
        """The adapter is a projection: same sections, same order, no extra ask."""
        self.assertTrue(TEMPLATE.is_file())
        self.assertTrue(GITHUB_ADAPTER.is_file())
        for path in (TEMPLATE, GITHUB_ADAPTER):
            text = COMMENT_RE.sub("", path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertIn("## TL;DR", text)
                self.assertIn("## What to review", text)
                self.assertIn("## What changed and why", text)
                self.assertIn("## Changes", text)
                self.assertIn("## Verification", text)
                # The alert must stay outside every folded section, because GitHub
                # renders it as literal text inside one.
                head, _, folded = text.partition("<details>")
                self.assertIn("> [!NOTE]", head)
                self.assertNotIn("[!NOTE]", folded)
                # Order is part of the schema: the reader's to-do list precedes depth.
                self.assertLess(text.index("## TL;DR"), text.index("## What to review"))
                self.assertLess(
                    text.index("## What to review"), text.index("<details>")
                )


if __name__ == "__main__":
    unittest.main()
