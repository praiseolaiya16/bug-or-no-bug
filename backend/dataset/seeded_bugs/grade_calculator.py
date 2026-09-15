def letter_grade(score):
    """Convert a numeric score (0-100) into a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score > 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
