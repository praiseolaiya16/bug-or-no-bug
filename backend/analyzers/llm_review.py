"""
LLM-based code review client for Bug-or-No-Bug.

Wraps the Gemini API to perform an LLM-based "does this code have a bug?"
review, so its findings can be compared against static analysis
(analyzers/static_analysis.py) and scored against ground truth
(scoring/metrics.py).

Normalized finding shape (deliberately close to static_analysis.py's, minus
fields an LLM can't produce like a rule id):
    {
        "line": int | None,
        "message": str,
        "confidence": float | None,
        "is_bug": bool,
    }
"""

import json
import os
from typing import Any, Dict, List, Optional

from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

_client = None


def get_client():
    """Construct and cache a configured Gemini client.

    Raises:
        RuntimeError: if GEMINI_API_KEY is not set.
    """
    global _client
    if _client is not None:
        return _client

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def build_review_prompt(code: str, context: Optional[str] = None) -> str:
    """Build the prompt sent to the LLM for a single code sample.

    Args:
        code: The source code snippet to review.
        context: Optional extra context (e.g. filename).

    Returns:
        A prompt instructing the model to identify bugs and return a
        strict JSON array of findings.
    """
    context_line = f"Filename: {context}\n" if context else ""
    return (
        "You are a meticulous code reviewer looking for a single seeded bug "
        "in a short Python function. It may be a logic error, a security "
        "vulnerability, or a style/convention issue with real consequences.\n\n"
        f"{context_line}"
        "Respond with ONLY a JSON array (no markdown fences, no commentary) "
        "of finding objects, one per issue you find, in this exact shape:\n"
        '[{"line": <int>, "is_bug": true, "description": "<one sentence>", '
        '"confidence": <float 0-1>}]\n\n'
        "If you find no issues, respond with exactly: []\n\n"
        "Code:\n"
        "```python\n"
        f"{code}\n"
        "```"
    )


def review_code(code: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
    """Send a code sample to the LLM and return normalized findings.

    Args:
        code: The source code snippet to review.
        context: Optional extra context (e.g. filename).

    Returns:
        A list of normalized findings (see module docstring). Returns an
        empty list if the model's response can't be parsed as JSON.

    Raises:
        RuntimeError: if GEMINI_API_KEY is not set (propagated from
        get_client()), or if the Gemini API call itself fails.
    """
    client = get_client()
    prompt = build_review_prompt(code, context)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    try:
        raw_findings = json.loads(response.text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []

    if not isinstance(raw_findings, list):
        return []

    findings = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        findings.append(
            {
                "line": item.get("line"),
                "message": item.get("description", ""),
                "confidence": item.get("confidence"),
                "is_bug": item.get("is_bug", True),
            }
        )
    return findings
