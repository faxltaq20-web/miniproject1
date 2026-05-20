from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMPTY_RESULT = {
    "score": 0,
    "issues": ["Section not found in document."],
    "suggestions": ["Add a dedicated section for this component."]
}

FALLBACK_RESULT = {
    "score": 0,
    "issues": ["Analysis unavailable — Gemini returned unparseable response."],
    "suggestions": ["Retry the analysis."]
}


def _call_gemini(prompt: str) -> dict:
    """
    Call Gemini once. On invalid JSON, retry with strict prompt.
    On second failure, return FALLBACK_RESULT (score=0).
    Raises exceptions from network/auth failures — main.py catches these as 503.
    """
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        # Retry with strict prompt (D-03 from CONTEXT.md)
        strict_prompt = (
            prompt
            + "\n\nReturn ONLY valid JSON. No markdown code blocks. No explanatory text."
        )
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=strict_prompt,
            )
            return json.loads(response.text.strip())
        except (json.JSONDecodeError, Exception):
            return FALLBACK_RESULT


def analyze_grammar(text: str) -> dict:
    """Layer 1 — Grammar & Language analysis."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Analyse the grammar and language quality of the following academic text.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific grammar/language problems found, minimum 1>], "suggestions": [<list of specific fixes matching each issue, minimum 1>]}}

Text:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_readability(text: str) -> dict:
    """Layer 2 — Readability Score evaluation."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Analyse the readability of the following academic text.
Consider sentence length, vocabulary complexity, clarity, and flow.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific readability problems, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Text:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_abstract(text: str) -> dict:
    """Layer 3 — Abstract Quality assessment."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the quality of this academic paper abstract.
Consider whether it clearly states the problem, method, results, and contribution.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific abstract weaknesses, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Abstract:
{text[:2000]}"""
    return _call_gemini(prompt)


def analyze_structure(text: str) -> dict:
    """Layer 4 — Structural Integrity review."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the structural integrity of this academic paper.
Consider section organisation, logical flow between sections, and completeness of standard academic structure (Abstract, Introduction, Methodology, Results, Discussion, Conclusion, References).
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of structural problems, minimum 1>], "suggestions": [<list of structural improvements, minimum 1>]}}

Paper content:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_methodology(text: str) -> dict:
    """Layer 5 — Methodology Soundness evaluation."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the methodology soundness of this academic paper.
Consider experimental design, reproducibility, dataset description, evaluation metrics, and baseline comparisons.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of methodology weaknesses, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Methodology section:
{text[:3000]}"""
    return _call_gemini(prompt)


def analyze_logic(text: str) -> dict:
    """Layer 6 — Logical Consistency check."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the logical consistency of this academic paper.
Check whether claims are supported by evidence, whether conclusions follow from results, and whether there are contradictions between sections.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of logical inconsistencies or unsupported claims, minimum 1>], "suggestions": [<list of specific fixes, minimum 1>]}}

Paper content:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_conclusion(text: str) -> dict:
    """Layer 7 — Conclusion Completeness assessment."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the completeness of this academic paper conclusion.
Consider whether it summarises findings, acknowledges limitations, and suggests future work.
Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of conclusion weaknesses, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Conclusion section:
{text[:2000]}"""
    return _call_gemini(prompt)


def analyze_paper(sections: dict) -> dict:
    """
    Run all 7 analysis layers on the given sections dict (from section_detector.py).

    Args:
        sections: dict with keys: abstract, introduction, methodology,
                  results, discussion, conclusion, references
                  (empty string "" if section was not detected in Phase 1)

    Returns:
        {
            "layer_details": {
                "grammar":     {"score": int, "issues": [str], "suggestions": [str]},
                "readability": {"score": int, "issues": [str], "suggestions": [str]},
                "abstract":    {"score": int, "issues": [str], "suggestions": [str]},
                "structure":   {"score": int, "issues": [str], "suggestions": [str]},
                "methodology": {"score": int, "issues": [str], "suggestions": [str]},
                "logic":       {"score": int, "issues": [str], "suggestions": [str]},
                "conclusion":  {"score": int, "issues": [str], "suggestions": [str]},
            },
            "layer_scores": {
                "grammar": float,       # 0-10
                "readability": float,
                "abstract": float,
                "structure": float,
                "methodology": float,
                "logic": float,
                "conclusion": float,
                "citations": float      # 0.0 placeholder — Phase 3 fills this
            }
        }
    """
    # Build full text for layers that need the whole document
    full_text = " ".join([v for v in sections.values() if v.strip()])

    # Grammar checks introduction + methodology (most grammar-intensive sections)
    grammar_text = (
        sections.get("introduction", "") + " " + sections.get("methodology", "")
    ).strip()

    layer_details = {
        "grammar":      analyze_grammar(grammar_text),
        "readability":  analyze_readability(full_text),
        "abstract":     analyze_abstract(sections.get("abstract", "")),
        "structure":    analyze_structure(full_text),
        "methodology":  analyze_methodology(sections.get("methodology", "")),
        "logic":        analyze_logic(full_text),
        "conclusion":   analyze_conclusion(sections.get("conclusion", "")),
    }

    # Extract scores; default to 0 if missing
    layer_scores = {k: float(v.get("score", 0)) for k, v in layer_details.items()}
    layer_scores["citations"] = 0.0  # Phase 3 fills this

    return {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }
