"""
Scoring metrics for Bug-or-No-Bug.

Compares findings produced by static analysis (analyzers/static_analysis.py)
or LLM review (analyzers/llm_review.py) against the labeled ground truth in
dataset/ground_truth.json, and computes standard detection metrics:

  - True positives / false positives / false negatives
  - Precision, recall, F1 score
  - Per bug-type breakdowns (logic / security / style)
  - McNemar's exact test on paired per-sample outcomes, to check whether
    an observed precision/recall gap between the two tools could plausibly
    be noise at this sample size (n=20) rather than a real difference

Matching strategy: each seeded_bugs/ file has exactly one ground-truth bug.
A predicted finding matches that bug if it's on the same file and its line
is within LINE_TOLERANCE of the bug's line. The first matching finding per
file counts as the true positive; any other findings on that file count as
false positives (this is how the project measures "false alarms" per
Assignment 1/2 — extra findings beyond the one seeded bug are noise).
"""

from math import comb
from typing import Any, Dict, List

LINE_TOLERANCE = 2


def _is_match(finding: Dict[str, Any], bug: Dict[str, Any]) -> bool:
    line = finding.get("line")
    bug_line = bug.get("line")
    if line is None or bug_line is None:
        return False
    return abs(line - bug_line) <= LINE_TOLERANCE


def match_findings(
    predicted: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]
) -> Dict[str, List[Any]]:
    """Match predicted findings against ground-truth bugs.

    Args:
        predicted: Findings from a static analyzer or the LLM reviewer.
        ground_truth: Labeled bugs loaded from dataset/ground_truth.json
            ("bugs" array entries).

    Returns:
        {
            "true_positives": [{"bug": ..., "finding": ...}, ...],
            "false_positives": [finding, ...],
            "false_negatives": [bug, ...],
        }
    """
    predicted_by_file: Dict[str, List[Dict[str, Any]]] = {}
    for finding in predicted:
        predicted_by_file.setdefault(finding.get("file"), []).append(finding)

    true_positives = []
    false_negatives = []
    matched_finding_ids = set()

    for bug in ground_truth:
        if not bug.get("is_bug"):
            continue

        candidates = predicted_by_file.get(bug.get("file"), [])
        match = None
        for finding in candidates:
            if id(finding) in matched_finding_ids:
                continue
            if _is_match(finding, bug):
                match = finding
                break

        if match is not None:
            matched_finding_ids.add(id(match))
            true_positives.append({"bug": bug, "finding": match})
        else:
            false_negatives.append(bug)

    false_positives = [f for f in predicted if id(f) not in matched_finding_ids]

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def precision_recall_f1(
    predicted: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Compute precision, recall, and F1 score for a set of predictions.

    Args:
        predicted: Findings from a static analyzer or the LLM reviewer.
        ground_truth: Labeled bugs loaded from dataset/ground_truth.json.

    Returns:
        {"precision": float, "recall": float, "f1": float,
         "tp": int, "fp": int, "fn": int}
    """
    matches = match_findings(predicted, ground_truth)
    tp = len(matches["true_positives"])
    fp = len(matches["false_positives"])
    fn = len(matches["false_negatives"])

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def _score_by_field(
    predicted: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]], field: str
) -> Dict[str, Dict[str, float]]:
    """Shared grouping logic for score_by_bug_type / score_by_source: split
    ground truth into subsets by the given field, score each subset's
    matching predictions independently.
    """
    values = sorted({bug[field] for bug in ground_truth if bug.get("is_bug")})

    scores = {}
    for value in values:
        subset_ground_truth = [b for b in ground_truth if b.get(field) == value]
        subset_files = {b["file"] for b in subset_ground_truth}
        subset_predicted = [f for f in predicted if f.get("file") in subset_files]
        scores[value] = precision_recall_f1(subset_predicted, subset_ground_truth)

    return scores


def score_by_bug_type(
    predicted: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Compute precision/recall/F1 broken down by bug type/category.

    Args:
        predicted: Findings from a static analyzer or the LLM reviewer.
        ground_truth: Labeled bugs loaded from dataset/ground_truth.json.

    Returns:
        A dict mapping bug type -> {"precision": ..., "recall": ..., "f1": ...}
    """
    return _score_by_field(predicted, ground_truth, "bug_type")


def score_by_source(
    predicted: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Compute precision/recall/F1 broken down by dataset source.

    Splits the comparison into 'synthetic' (hand-written for this project)
    vs. 'real_world' (adapted from a real CVE/issue/commit), so findings
    can be checked for whether they hold up outside of hand-constructed
    examples, not just on them.

    Args:
        predicted: Findings from a static analyzer or the LLM reviewer.
        ground_truth: Labeled bugs loaded from dataset/ground_truth.json.

    Returns:
        A dict mapping source ('synthetic' | 'real_world') ->
        {"precision": ..., "recall": ..., "f1": ...}
    """
    return _score_by_field(predicted, ground_truth, "source")


def mcnemar_test(per_sample: List[Dict[str, bool]]) -> Dict[str, Any]:
    """McNemar's exact test on paired per-sample caught/missed outcomes.

    With only 20 samples, the usual chi-square approximation to McNemar's
    test is unreliable, so this uses the exact form: an exact two-sided
    binomial test (p=0.5) on the discordant pairs — samples where the two
    tools disagreed about whether the bug was caught. Samples where they
    agree (both caught it or both missed it) carry no information about
    which tool is better and are excluded, per McNemar's test.

    Args:
        per_sample: a list of {"static_caught": bool, "llm_caught": bool}
            (or any two paired boolean outcomes) — one entry per sample.

    Returns:
        {
            "contingency": {"both_caught", "static_only", "llm_only", "neither_caught"},
            "n_discordant": int,
            "p_value": float,
            "significant_at_0.05": bool,
        }
    """
    both_caught = static_only = llm_only = neither_caught = 0

    for row in per_sample:
        static_caught = bool(row.get("static_caught"))
        llm_caught = bool(row.get("llm_caught"))
        if static_caught and llm_caught:
            both_caught += 1
        elif static_caught:
            static_only += 1
        elif llm_caught:
            llm_only += 1
        else:
            neither_caught += 1

    n_discordant = static_only + llm_only
    if n_discordant == 0:
        p_value = 1.0
    else:
        k = min(static_only, llm_only)
        tail = sum(comb(n_discordant, i) for i in range(k + 1))
        p_value = min(1.0, 2 * tail * (0.5**n_discordant))

    return {
        "contingency": {
            "both_caught": both_caught,
            "static_only": static_only,
            "llm_only": llm_only,
            "neither_caught": neither_caught,
        },
        "n_discordant": n_discordant,
        "p_value": p_value,
        "significant_at_0.05": p_value < 0.05,
    }
