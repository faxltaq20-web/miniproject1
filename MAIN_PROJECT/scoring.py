# Phase 14 (P2): Discipline-adaptive weighting. Each map sums to 1.0 and adjusts
# emphasis to match what reviewers in that field weigh most heavily.
# The "computer_science" entry doubles as the default fallback (exposed below
# as `WEIGHTS`) — keeping one source of truth so the two never drift apart.
DISCIPLINE_WEIGHTS = {
    "computer_science": {
        "structure_sections": 0.20,
        "clarity_writing":    0.225,
        "methodology_rigor":  0.225,
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
    "mathematics": {
        "structure_sections": 0.15,
        "clarity_writing":    0.15,
        "methodology_rigor":  0.175,
        "evidence_claims":    0.375,  # proofs are the core evidence
        "citations":          0.15,
    },
    "physics": {
        "structure_sections": 0.175,
        "clarity_writing":    0.20,
        "methodology_rigor":  0.275,  # reproducibility of setup
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
    "chemistry": {
        "structure_sections": 0.175,
        "clarity_writing":    0.20,
        "methodology_rigor":  0.275,
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
    "medicine_biology": {
        "structure_sections": 0.175,
        "clarity_writing":    0.15,
        "methodology_rigor":  0.325,  # clinical trial rigor
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
    "humanities_social": {
        "structure_sections": 0.175,
        "clarity_writing":    0.325,  # writing quality is the work
        "methodology_rigor":  0.15,
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
    "other": {
        "structure_sections": 0.20,
        "clarity_writing":    0.225,
        "methodology_rigor":  0.225,
        "evidence_claims":    0.20,
        "citations":          0.15,
    },
}

# Default weights — alias of the CS map. Reference UI layout:
#   01 Structure & Sections  20%
#   02 Clarity & Writing      22.5%
#   03 Methodology Rigor      22.5%
#   04 Evidence & Claims      20%
#   05 Citations & References 15%
WEIGHTS = DISCIPLINE_WEIGHTS["computer_science"]

# Grade thresholds — ordered highest-first for short-circuit matching
GRADE_MAP = [
    (85, "A — Excellent"),
    (70, "B — Good"),
    (55, "C — Needs Improvement"),
    (40, "D — Poor"),
    (0,  "F — Very Poor"),
]


def calculate_score(layer_scores: dict, discipline: str = "computer_science") -> dict:
    """
    Calculate weighted confidence score (0-100) and letter grade using
    discipline-adaptive weights when available.

    Args:
        layer_scores: dict mapping layer name (str) to raw score 0-10 (float).
                      Expected keys: structure_sections, clarity_writing,
                      methodology_rigor, evidence_claims, citations.
                      Missing keys default to 0.
        discipline:   one of the keys in DISCIPLINE_WEIGHTS. Unknown values
                      fall back to the default CS weights.

    Returns:
        {
            "final_score": float,    # 0-100, rounded to 1 decimal
            "grade": str,            # e.g. "B — Good"
            "weights": dict,         # the weight map actually used
            "discipline": str        # the resolved discipline
        }
    """
    weights = DISCIPLINE_WEIGHTS.get(discipline, WEIGHTS)

    # Weighted sum: each layer score (0-10) * weight → sum (0-1) → * 10 → (0-100)
    raw = sum(layer_scores.get(k, 0.0) * w for k, w in weights.items())
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
        "weights": weights,
        "discipline": discipline if discipline in DISCIPLINE_WEIGHTS else "computer_science",
    }
