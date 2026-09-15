"""
Static analysis wrappers for Bug-or-No-Bug.

Wraps two static analysis tools and normalizes their output into a common
finding format so it can be compared against ground truth and against
LLM-based review results:

  - Bandit: security-focused static analyzer for Python.
  - Pylint: general-purpose linter (style, errors, code smells).

Shared finding shape:
    {
        "file": str,           # filename as passed to the tool
        "line": int | None,
        "tool": "bandit" | "pylint",
        "rule_id": str | None,
        "severity": str | None,
        "message": str,
    }
"""

import json
import subprocess
from typing import Any, Dict, List

SUBPROCESS_TIMEOUT_SECONDS = 30


def run_bandit(target_path: str) -> List[Dict[str, Any]]:
    """Run Bandit against the given file or directory.

    Args:
        target_path: Path to a Python file or directory to scan.

    Returns:
        A list of normalized findings (see module docstring).
    """
    try:
        proc = subprocess.run(
            ["bandit", "-f", "json", "-q", target_path],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "bandit is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    if not proc.stdout.strip():
        return []

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []

    findings = []
    for result in data.get("results", []):
        findings.append(
            {
                "file": result.get("filename"),
                "line": result.get("line_number"),
                "tool": "bandit",
                "rule_id": result.get("test_id"),
                "severity": result.get("issue_severity"),
                "message": result.get("issue_text"),
            }
        )
    return findings


def run_pylint(target_path: str) -> List[Dict[str, Any]]:
    """Run Pylint against the given file or directory.

    Args:
        target_path: Path to a Python file or directory to lint.

    Returns:
        A list of normalized findings (see module docstring).
    """
    try:
        proc = subprocess.run(
            ["pylint", "--output-format=json", target_path],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pylint is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    if not proc.stdout.strip():
        return []

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []

    findings = []
    for item in data:
        findings.append(
            {
                "file": item.get("path"),
                "line": item.get("line"),
                "tool": "pylint",
                "rule_id": item.get("symbol") or item.get("message-id"),
                "severity": item.get("type"),
                "message": item.get("message"),
            }
        )
    return findings


def run_static_analysis(target_path: str) -> List[Dict[str, Any]]:
    """Run all static analyzers against the given path and merge results.

    Args:
        target_path: Path to a Python file or directory to analyze.

    Returns:
        Combined, normalized findings from Bandit and Pylint.
    """
    return run_bandit(target_path) + run_pylint(target_path)
