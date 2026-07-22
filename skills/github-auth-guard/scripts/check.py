#!/usr/bin/env python3
"""Classify GitHub CLI authentication without exposing credentials.

The important distinction is between a credential GitHub rejected and an
environment that could not perform the check. Sandboxed agents commonly hit the
latter and must not turn it into a reauthentication instruction.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess]

EXIT_CODES = {
    "authenticated": 0,
    "inconclusive": 2,
    "reauth-required": 3,
    "invalid-environment-token": 4,
    "permission-or-sso": 5,
    "tool-missing": 6,
}


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        text=True,
        capture_output=True,
        check=False,
    )


def _text(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}".lower()


def _token_override(environment: Mapping[str, str], hostname: str) -> Optional[str]:
    if hostname == "github.com" or hostname.endswith(".ghe.com"):
        names = ("GH_TOKEN", "GITHUB_TOKEN")
    else:
        names = ("GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN")
    for name in names:
        if environment.get(name):
            return name
    return None


def _configured_host(
    hostname: str,
    environment: Mapping[str, str],
    home: Optional[Path] = None,
) -> Optional[bool]:
    config_root = environment.get("GH_CONFIG_DIR")
    if config_root:
        path = Path(config_root) / "hosts.yml"
    else:
        base = home or Path.home()
        path = base / ".config" / "gh" / "hosts.yml"
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    except OSError:
        return None
    pattern = rf"(?m)^{re.escape(hostname)}:\s*$"
    return re.search(pattern, content) is not None


def classify(
    hostname: str,
    status: subprocess.CompletedProcess[str],
    api_user: subprocess.CompletedProcess[str],
    environment: Mapping[str, str],
    configured_host: Optional[bool],
) -> dict[str, object]:
    override = _token_override(environment, hostname)
    api_text = _text(api_user)
    status_text = _text(status)
    combined = f"{api_text}\n{status_text}"
    login = api_user.stdout.strip() if api_user.returncode == 0 else None

    common: dict[str, object] = {
        "hostname": hostname,
        "login": login,
        "credential_source": override or ("stored-or-unknown" if configured_host else "none"),
        "configured_host": configured_host,
        "checks": {
            "auth_status_exit": status.returncode,
            "api_user_exit": api_user.returncode,
        },
    }

    if api_user.returncode == 0 and login:
        return {
            **common,
            "classification": "authenticated",
            "safe_to_recommend_login": False,
            "reason": "GitHub accepted the current credential and returned the active account.",
            "next_step": "Continue the requested GitHub operation.",
        }

    rejected = "http 401" in api_text or "bad credentials" in api_text
    if rejected and override:
        return {
            **common,
            "classification": "invalid-environment-token",
            "safe_to_recommend_login": False,
            "reason": f"GitHub rejected the token supplied by {override}.",
            "next_step": (
                f"Remove or replace {override}; it overrides stored gh credentials. "
                "Logging in again will not fix the active override."
            ),
        }

    if rejected:
        return {
            **common,
            "classification": "reauth-required",
            "safe_to_recommend_login": True,
            "reason": "GitHub was reachable and explicitly rejected the stored credential with HTTP 401.",
            "next_step": "Ask the human to reauthenticate once using the normal interactive GitHub CLI flow.",
        }

    permission_markers = (
        "http 403",
        "resource not accessible",
        "requires sso",
        "saml",
        "insufficient scope",
    )
    if any(marker in api_text for marker in permission_markers):
        return {
            **common,
            "classification": "permission-or-sso",
            "safe_to_recommend_login": False,
            "reason": "GitHub was reachable, but the request was denied for authorization or SSO reasons.",
            "next_step": "Diagnose repository permission, token scope, or SSO authorization; do not rotate login blindly.",
        }

    missing_markers = (
        "not logged into any github hosts",
        "not logged in to any github hosts",
        "to get started with github cli",
    )
    if configured_host is False and not override and any(
        marker in combined for marker in missing_markers
    ):
        return {
            **common,
            "classification": "reauth-required",
            "safe_to_recommend_login": True,
            "reason": "No credential is configured for this GitHub host.",
            "next_step": "Ask the human to authenticate once using the normal interactive GitHub CLI flow.",
        }

    return {
        **common,
        "classification": "inconclusive",
        "safe_to_recommend_login": False,
        "reason": (
            "The current environment could not prove whether the credential is valid. "
            "Network, keychain, sandbox, and process-environment failures belong here."
        ),
        "next_step": (
            "Repeat this diagnostic with scoped host access outside the agent sandbox. "
            "Do not claim expiry and do not recommend gh auth login from this result."
        ),
    }


def probe(
    hostname: str = "github.com",
    runner: Runner = run_command,
    environment: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> dict[str, object]:
    environment = environment if environment is not None else os.environ
    if shutil.which("gh") is None and runner is run_command:
        return {
            "classification": "tool-missing",
            "hostname": hostname,
            "login": None,
            "credential_source": "unknown",
            "configured_host": None,
            "checks": {"auth_status_exit": None, "api_user_exit": None},
            "safe_to_recommend_login": False,
            "reason": "GitHub CLI is not installed or is not on PATH.",
            "next_step": "Install GitHub CLI; installation and authentication are separate steps.",
        }

    configured = _configured_host(hostname, environment, home)
    status = runner(["gh", "auth", "status", "--active", "--hostname", hostname])
    api_user = runner(["gh", "api", "--hostname", hostname, "user", "--jq", ".login"])
    return classify(hostname, status, api_user, environment, configured)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify GitHub CLI authentication without reading or printing a token."
    )
    parser.add_argument("--hostname", default="github.com")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    result = probe(hostname=args.hostname)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return EXIT_CODES[str(result["classification"])]


if __name__ == "__main__":
    sys.exit(main())
