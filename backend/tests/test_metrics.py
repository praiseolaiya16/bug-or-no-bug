"""
Tests for scoring/metrics.py — the piece the whole static-vs-LLM comparison's
validity rests on, so its matching, scoring, and significance-testing logic
need real coverage rather than trust.
"""

from scoring.metrics import match_findings, mcnemar_test, precision_recall_f1


def _bug(file="a.py", line=10, bug_type="logic"):
    return {"file": file, "line": line, "is_bug": True, "bug_type": bug_type}


def test_match_findings_exact_line_is_true_positive():
    ground_truth = [_bug(line=10)]
    predicted = [{"file": "a.py", "line": 10}]

    matches = match_findings(predicted, ground_truth)

    assert len(matches["true_positives"]) == 1
    assert matches["false_positives"] == []
    assert matches["false_negatives"] == []


def test_match_findings_within_tolerance_still_matches():
    # LINE_TOLERANCE = 2, so a finding 2 lines off the seeded bug still counts
    # — this is what let a real Gemini response (off by one on its own line
    # number) still register as "caught" during actual runs of this project.
    ground_truth = [_bug(line=10)]
    predicted = [{"file": "a.py", "line": 12}]

    matches = match_findings(predicted, ground_truth)

    assert len(matches["true_positives"]) == 1
    assert matches["false_positives"] == []


def test_match_findings_extra_finding_is_false_positive():
    ground_truth = [_bug(line=10)]
    predicted = [{"file": "a.py", "line": 10}, {"file": "a.py", "line": 50}]

    matches = match_findings(predicted, ground_truth)

    assert len(matches["true_positives"]) == 1
    assert len(matches["false_positives"]) == 1
    assert matches["false_positives"][0]["line"] == 50


def test_match_findings_missed_bug_is_false_negative():
    ground_truth = [_bug(line=10)]

    matches = match_findings([], ground_truth)

    assert matches["true_positives"] == []
    assert len(matches["false_negatives"]) == 1


def test_precision_recall_f1_perfect_score():
    ground_truth = [_bug(line=10)]
    predicted = [{"file": "a.py", "line": 10}]

    result = precision_recall_f1(predicted, ground_truth)

    assert result == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 1, "fp": 0, "fn": 0}


def test_precision_recall_f1_no_predictions_is_zero_not_error():
    ground_truth = [_bug(line=10)]

    result = precision_recall_f1([], ground_truth)

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["fn"] == 1


def test_mcnemar_no_discordant_pairs_gives_p_one():
    per_sample = [
        {"static_caught": True, "llm_caught": True},
        {"static_caught": False, "llm_caught": False},
    ]

    result = mcnemar_test(per_sample)

    assert result["n_discordant"] == 0
    assert result["p_value"] == 1.0
    assert result["significant_at_0.05"] is False


def test_mcnemar_known_exact_binomial_value():
    # 5 discordant pairs: static-only=1, llm-only=4. Exact two-sided
    # binomial p-value at p=0.5: 2 * (C(5,0) + C(5,1)) / 2**5 = 12/32 = 0.375.
    per_sample = (
        [{"static_caught": True, "llm_caught": False}] * 1
        + [{"static_caught": False, "llm_caught": True}] * 4
        + [{"static_caught": True, "llm_caught": True}] * 3
    )

    result = mcnemar_test(per_sample)

    assert result["contingency"] == {
        "both_caught": 3,
        "static_only": 1,
        "llm_only": 4,
        "neither_caught": 0,
    }
    assert result["n_discordant"] == 5
    assert abs(result["p_value"] - 0.375) < 1e-9
    assert result["significant_at_0.05"] is False


def test_mcnemar_lopsided_split_is_significant():
    # 8 discordant pairs, all favoring one tool: p = 2 * C(8,0) / 2**8 ≈ 0.0078.
    per_sample = [{"static_caught": False, "llm_caught": True}] * 8

    result = mcnemar_test(per_sample)

    assert result["n_discordant"] == 8
    assert result["p_value"] < 0.05
    assert result["significant_at_0.05"] is True
