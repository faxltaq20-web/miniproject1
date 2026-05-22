"""
gemini_analyzer.py — Multi-key Gemini LLM client with automatic key rotation.

Uses up to 5 Gemini API keys. If one key hits rate limits (429),
automatically rotates to the next key. This gives 5× the free-tier quota.
"""

from google import genai
import json
import os
import re
import time
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── Multi-Key Setup ─────────────────────────────────────────────────────────
# Load up to 5 Gemini API keys from .env
# Keys are tried in order: GEMINI_KEY_1 → GEMINI_KEY_2 → ... → GEMINI_KEY_5
# ─────────────────────────────────────────────────────────────────────────────

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_clients = []
for i in range(1, 6):
    key = os.getenv(f"GEMINI_KEY_{i}", "").strip()
    if key:
        try:
            client = genai.Client(api_key=key)
            _clients.append((f"Key_{i}", client))
        except Exception as e:
            print(f"   [Init] GEMINI_KEY_{i} failed: {e}", file=sys.stderr)

if not _clients:
    raise RuntimeError(
        "No Gemini API keys configured!\n"
        "Add at least one key to your .env file:\n"
        "  GEMINI_KEY_1=AIza...\n"
        "  GEMINI_KEY_2=AIza...  (optional)\n"
        "  ...up to GEMINI_KEY_5"
    )

print(f"   [LLM] {len(_clients)} Gemini key(s) loaded — model: {_MODEL}", flush=True)


# ─── Constants ────────────────────────────────────────────────────────────────

EMPTY_RESULT = {
    "score": 0,
    "issues": ["Section not found in document."],
    "suggestions": ["Add a dedicated section for this component."]
}

FALLBACK_RESULT = {
    "score": 0,
    "issues": ["Analysis unavailable — LLM returned unparseable response."],
    "suggestions": ["Retry the analysis."]
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def clean_json_text(text: str) -> str:
    """Strip markdown code block formatting if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _parse_retry_delay(err_str: str) -> float:
    """Extract suggested retry delay (seconds) from a Gemini API error."""
    match = re.search(r'retry(?:Delay["\s:]+["\'"]?|[_ ]in\s+)([\d.]+)s', err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0


# ─── Core LLM Call (key rotation) ────────────────────────────────────────────

def _call_single_key(key_name: str, client, prompt: str,
                     max_retries: int = 3, initial_delay: float = 5.0) -> str:
    """
    Call Gemini with one specific key. Retries on transient errors.
    Returns raw text on success. Raises on persistent failure.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            is_rate_limit = any(code in err_str for code in
                                ["429", "RESOURCE_EXHAUSTED"])
            is_transient = is_rate_limit or any(code in err_str for code in
                                ["503", "UNAVAILABLE"]) or "overloaded" in err_str.lower()

            if is_rate_limit:
                # Don't retry on rate limit — rotate to next key instead
                raise

            if is_transient and attempt < max_retries - 1:
                api_delay = _parse_retry_delay(err_str)
                wait_time = max(delay, api_delay + 2.0) if api_delay > 0 else delay
                print(f"   [Retry] {key_name} error. Waiting {wait_time:.0f}s "
                      f"(attempt {attempt+1}/{max_retries})...", flush=True)
                time.sleep(wait_time)
                delay = min(delay * 2.0, 60.0)
            else:
                raise


def _call_llm_with_failover(prompt: str) -> str:
    """
    Try each Gemini key in order. If one key hits 429, rotate to next.
    Returns raw text on first success.
    """
    last_error = None
    for key_name, client in _clients:
        try:
            return _call_single_key(key_name, client, prompt)
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"   [Rotate] {key_name} quota exhausted → trying next key...", flush=True)
            else:
                print(f"   [Rotate] {key_name} failed → trying next key...", flush=True)

    raise RuntimeError(f"All {len(_clients)} Gemini keys exhausted: {last_error}")


def _call_gemini(prompt: str) -> dict:
    """
    Call Gemini with key rotation. Parse JSON response.
    On invalid JSON, retry with strict prompt.
    On persistent failure, return FALLBACK_RESULT.
    """
    try:
        raw_text = _call_llm_with_failover(prompt)
        cleaned_text = clean_json_text(raw_text)
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # Retry with strict prompt
        strict_prompt = (
            prompt
            + "\n\nReturn ONLY valid JSON. No markdown code blocks. No explanatory text."
        )
        try:
            raw_text = _call_llm_with_failover(strict_prompt)
            cleaned_text = clean_json_text(raw_text)
            return json.loads(cleaned_text)
        except (json.JSONDecodeError, Exception):
            return FALLBACK_RESULT
    except Exception as e:
        print(f"   [Error] All Gemini keys failed: {e}", file=sys.stderr)
        return FALLBACK_RESULT


# ─── Paper Analysis (single-prompt, all 4 layers) ────────────────────────────

def analyze_paper(sections: dict) -> dict:
    """
    Run all 4 analysis layers in a SINGLE LLM call.
    (The 5th layer — Citations — is handled separately by citation_checker.py)

    Uses 1 API call instead of 4, preserving quota.

    Returns:
        {
            "layer_details": {
                "structure_sections": {"score": int, "issues": [str], "suggestions": [str]},
                "clarity_writing":    {"score": int, "issues": [str], "suggestions": [str]},
                "methodology_rigor":  {"score": int, "issues": [str], "suggestions": [str]},
                "evidence_claims":    {"score": int, "issues": [str], "suggestions": [str]},
            },
            "layer_scores": {
                "structure_sections": float,
                "clarity_writing": float,
                "methodology_rigor": float,
                "evidence_claims": float,
                "citations": float   # 0.0 placeholder — citation_checker fills this
            }
        }
    """
    full_text = " ".join([v for v in sections.values() if v.strip()])

    if not full_text.strip():
        empty = {"score": 0, "issues": ["No content found."], "suggestions": ["Provide paper content."]}
        return {
            "layer_details": {k: empty for k in
                ["structure_sections", "clarity_writing", "methodology_rigor", "evidence_claims"]},
            "layer_scores": {
                "structure_sections": 0.0, "clarity_writing": 0.0,
                "methodology_rigor": 0.0, "evidence_claims": 0.0, "citations": 0.0,
            }
        }

    prompt = f"""You are an academic paper reviewer. Evaluate the following research paper across 4 dimensions.
For EACH dimension, provide a score (0-10), a list of specific issues found (minimum 1), and a list of specific suggestions (minimum 1).

DIMENSION 1 — Structure & Sections (evaluate):
- Completeness of standard academic structure (Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion, References)
- Logical flow and transitions between sections
- Section balance and proper ordering

DIMENSION 2 — Clarity & Writing (evaluate):
- Grammar correctness and language accuracy
- Sentence structure and readability
- Vocabulary appropriateness for academic writing
- Coherence and flow within paragraphs

DIMENSION 3 — Methodology Rigor (evaluate):
- Experimental design and reproducibility
- Dataset description and justification
- Evaluation metrics and baseline comparisons
- Sufficient detail for replication

DIMENSION 4 — Evidence & Claims (evaluate):
- Whether claims are supported by evidence and data
- Whether conclusions logically follow from results
- Presence of unsupported or overgeneralized claims
- Consistency between abstract claims and actual findings

Return ONLY a JSON object with exactly this structure (no markdown, no extra text):
{{
  "structure_sections": {{"score": <0-10>, "issues": ["..."], "suggestions": ["..."]}},
  "clarity_writing": {{"score": <0-10>, "issues": ["..."], "suggestions": ["..."]}},
  "methodology_rigor": {{"score": <0-10>, "issues": ["..."], "suggestions": ["..."]}},
  "evidence_claims": {{"score": <0-10>, "issues": ["..."], "suggestions": ["..."]}}
}}

Paper content:
{full_text[:8000]}"""

    print("   ↳ Running multi-layer analysis (single pass)...", flush=True)
    raw = _call_gemini(prompt)

    layer_keys = ["structure_sections", "clarity_writing", "methodology_rigor", "evidence_claims"]

    if all(k in raw for k in layer_keys):
        layer_details = {k: raw[k] for k in layer_keys}
    else:
        layer_details = {k: raw for k in layer_keys}

    # Ensure each layer has required fields
    for key in layer_keys:
        layer = layer_details[key]
        if not isinstance(layer, dict):
            layer_details[key] = EMPTY_RESULT
        else:
            layer.setdefault("score", 0)
            layer.setdefault("issues", ["No issues recorded."])
            layer.setdefault("suggestions", ["No suggestions recorded."])

    layer_scores = {k: float(v.get("score", 0)) for k, v in layer_details.items()}
    layer_scores["citations"] = 0.0

    return {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }
