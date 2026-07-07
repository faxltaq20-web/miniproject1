"""
Unit tests for scoring.py — Phase 14 discipline-adaptive weighting.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scoring


class TestDisciplineWeightingSelection:

    def test_default_uses_computer_science_weights(self):
        result = scoring.calculate_score(
            {"structure_sections": 7, "clarity_writing": 7,
             "methodology_rigor": 7, "evidence_claims": 7, "citations": 7}
        )
        assert result["discipline"] == "computer_science"
        assert result["weights"] == scoring.DISCIPLINE_WEIGHTS["computer_science"]

    def test_unknown_discipline_falls_back_to_cs(self):
        result = scoring.calculate_score(
            {"structure_sections": 5, "clarity_writing": 5,
             "methodology_rigor": 5, "evidence_claims": 5, "citations": 5},
            discipline="not_a_real_field"
        )
        # Resolved discipline is CS; weights map is the CS map (default WEIGHTS).
        assert result["discipline"] == "computer_science"
        assert result["weights"] == scoring.WEIGHTS

    def test_math_weights_emphasize_evidence(self):
        # Same scores; math should reward a high evidence layer more than humanities.
        scores_evidence_strong = {
            "structure_sections": 5, "clarity_writing": 5,
            "methodology_rigor": 5, "evidence_claims": 10, "citations": 5,
        }
        math = scoring.calculate_score(scores_evidence_strong, discipline="mathematics")
        hum = scoring.calculate_score(scores_evidence_strong, discipline="humanities_social")
        assert math["final_score"] > hum["final_score"]

    def test_humanities_weights_emphasize_clarity(self):
        scores_clarity_strong = {
            "structure_sections": 5, "clarity_writing": 10,
            "methodology_rigor": 5, "evidence_claims": 5, "citations": 5,
        }
        hum = scoring.calculate_score(scores_clarity_strong, discipline="humanities_social")
        math = scoring.calculate_score(scores_clarity_strong, discipline="mathematics")
        assert hum["final_score"] > math["final_score"]

    def test_medicine_weights_emphasize_methodology(self):
        scores_method_strong = {
            "structure_sections": 5, "clarity_writing": 5,
            "methodology_rigor": 10, "evidence_claims": 5, "citations": 5,
        }
        med = scoring.calculate_score(scores_method_strong, discipline="medicine_biology")
        hum = scoring.calculate_score(scores_method_strong, discipline="humanities_social")
        assert med["final_score"] > hum["final_score"]

    def test_all_discipline_weight_maps_sum_to_one(self):
        for disc, weights in scoring.DISCIPLINE_WEIGHTS.items():
            assert abs(sum(weights.values()) - 1.0) < 1e-9, f"{disc} weights don't sum to 1"

    def test_grade_threshold_unchanged(self):
        # Perfect 10s on default discipline → final_score 100 → grade A.
        result = scoring.calculate_score(
            {"structure_sections": 10, "clarity_writing": 10,
             "methodology_rigor": 10, "evidence_claims": 10, "citations": 10}
        )
        assert result["final_score"] == 100.0
        assert result["grade"].startswith("A")
