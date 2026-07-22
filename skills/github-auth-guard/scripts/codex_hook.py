#!/usr/bin/env python3
"""Codex hook that prevents unsupported GitHub reauthentication advice."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, Optional


sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as auth_check  # noqa: E402


Probe = Callable[[str], Dict[str, object]]

LOGIN_COMMAND = re.compile(r"(?:^|[/\s])gh\s+auth\s+login(?:\s|$)", re.IGNORECASE)
STATUS_COMMAND = re.compile(r"(?:^|[/\s])gh\s+auth\s+status(?:\s|$)", re.IGNORECASE)
NEGATIONS = (
    "do not",
    "don't",
    "never",
    "no need",
    "should not",
    "shouldn't",
    "without running",
    "blocked",
)


def _command(payload: dict[str, object]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def _hostname(command: str) -> str:
    match = re.search(r"(?:--hostname|-h)\s+([^\s]+)", command)
    return match.group(1) if match else "github.com"


def recommends_login(message: str) -> bool:
    lowered = message.lower()
    for match in re.finditer(r"gh\s+auth\s+login", lowered):
        context = lowered[max(0, match.start() - 100) : match.end() + 100]
        if not any(negative in context for negative in NEGATIONS):
            return True

    phrase_patterns = (
        r"(?:need|must|please|try|should)\s+(?:to\s+)?(?:re-?authenticate|log\s+(?:back\s+)?in).{0,60}github",
        r"(?:re-?authenticate|log\s+(?:back\s+)?in).{0,60}github.{0,30}(?:again|now|first)",
    )
    for pattern in phrase_patterns:
        match = re.search(pattern, lowered)
        if match:
            context = lowered[max(0, match.start() - 60) : match.end() + 20]
            if not any(negative in context for negative in NEGATIONS):
                return True
    return False


def _probe(hostname: str) -> dict[str, object]:
    return auth_check.probe(hostname=hostname)


def _deny_login(result: dict[str, object]) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "GitHub reauthentication blocked by the auth-evidence guard. "
                f"Diagnostic classification: {result['classification']}. "
                f"{result['next_step']}"
            ),
        }
    }


def handle(payload: dict[str, object], probe: Probe = _probe) -> Optional[dict[str, object]]:
    event = payload.get("hook_event_name")
    command = _command(payload)

    if event == "PreToolUse" and LOGIN_COMMAND.search(command):
        result = probe(_hostname(command))
        if not result.get("safe_to_recommend_login"):
            return _deny_login(result)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    "The independent diagnostic confirmed that reauthentication is "
                    "appropriate. Keep the interactive flow human-visible and never "
                    "print or capture the token."
                ),
            }
        }

    if event in ("PreToolUse", "PostToolUse") and STATUS_COMMAND.search(command):
        return {
            "hookSpecificOutput": {
                "hookEventName": str(event),
                "additionalContext": (
                    "A nonzero gh auth status result inside Codex is not proof of an "
                    "expired credential. Run the github-auth-guard diagnostic with "
                    "scoped host access; do not recommend login from sandbox output."
                ),
            }
        }

    if event == "Stop":
        message = payload.get("last_assistant_message")
        if isinstance(message, str) and recommends_login(message):
            result = probe("github.com")
            if not result.get("safe_to_recommend_login"):
                return {
                    "decision": "block",
                    "reason": (
                        "Remove the unsupported GitHub login recommendation and continue "
                        "the task. The auth-evidence guard classified the current state as "
                        f"{result['classification']}: {result['next_step']}"
                    ),
                }

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as error:
        print(f"github-auth-guard received invalid hook input: {error}", file=sys.stderr)
        return 1
    result = handle(payload)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
