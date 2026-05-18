# Weights per layer — must stay in sync with desirable.md parameter table
# and the report_generator.py max-marks column in Phase 4.
WEIGHTS = {
    "grammar":      0.15,
    "structure":    0.15,
    "methodology":  0.15,
    "logic":        0.15,
    "readability":  0.10,
    "abstract":     0.10,
    "conclusion":   0.10,
    "citations":    0.10,
}

# Grade thresholds — ordered highest-first for short-circuit matching
GRADE_MAP = [
    (85, "A — Excellent"),
    (70, "B — Good"),
    (55, "C — Needs Improvement"),
    (40, "D — Poor"),
    (0,  "F — Very Poor"),
]


def calculate_score(layer_scores: dict) -> dict:
    """
    Calculate weighted confidence score (0-100) and letter grade.

    Args:
        layer_scores: dict mapping layer name (str) to raw score 0-10 (float).
                      Expected keys: grammar, readability, abstract, structure,
                      methodology, logic, conclusion, citations.
                      Missing keys default to 0.

    Returns:
        {
            "final_score": float,   # 0-100, rounded to 1 decimal
            "grade": str            # e.g. "B — Good"
        }
    """
    # Weighted sum: each layer score (0-10) * weight → sum (0-1) → * 10 → (0-100)
    raw = sum(layer_scores.get(k, 0.0) * w for k, w in WEIGHTS.items())
    confidence_score = round(max(0.0, min(100.0, raw * 10)), 1)

    # Determine grade via threshold lookup
    grade = "F — Very Poor"
    for threshold, label in GRADE_MAP:
        if confidence_score >= threshold:
            grade = label
            break

    return {
        "final_score": confidence_score,
        "grade": grade,
    }
