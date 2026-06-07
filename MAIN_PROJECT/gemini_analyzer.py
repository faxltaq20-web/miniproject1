"""
gemini_analyzer.py — Multi-key Gemini LLM client with automatic key rotation.

Uses up to 5 Gemini API keys. If one key hits rate limits (429),
automatically rotates to the next key. This gives 5× the free-tier quota.
"""

from google import genai
from google.genai import types
import json
import os
import re
import time
import sys
from dotenv import load_dotenv

# Fix Windows CP1252 encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

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
    "issues": ["Analysis unavailable — Gemini API overloaded or all keys exhausted. Retry later."],
    "suggestions": ["Retry the analysis when Gemini API demand is lower."],
    "analysis_failed": True
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
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    top_p=0.95,
                ),
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
                print(f"   [Retry] {key_name} error ({e}). Waiting {wait_time:.0f}s "
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
                print(f"   [Rotate] {key_name} quota exhausted: {e} → trying next key...", flush=True)
            else:
                print(f"   [Rotate] {key_name} failed: {e} → trying next key...", flush=True)

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
    def _smart_truncate(text: str, limit: int) -> str:
        """
        Cut text at the last sentence boundary (. ! ?) within `limit` chars.
        Falls back to last whitespace if no sentence end is found.
        Appends '[...truncated]' so the LLM knows content was cut cleanly.
        """
        if len(text) <= limit:
            return text
        window = text[:limit]
        match = None
        for m in re.finditer(r'[.!?][\s\n]', window):
            match = m
        if match:
            return window[:match.end()].rstrip() + "\n[...truncated]"
        last_space = window.rfind(' ')
        if last_space > limit // 2:
            return window[:last_space].rstrip() + "\n[...truncated]"
        return window + "\n[...truncated]"

    # ── Smart per-section text assembly ───────────────────────────────
    # Gemini 2.5 Flash has 1M token context — send full section text.
    # Limits are large enough for any standard academic paper.
    SECTION_ORDER = [
        ("abstract",     "ABSTRACT",         5000),
        ("introduction", "INTRODUCTION",    30000),
        ("related_work", "RELATED WORK",    15000),
        ("methodology",  "METHODOLOGY",     40000),
        ("results",      "RESULTS",         40000),
        ("discussion",   "DISCUSSION",      30000),
        ("conclusion",   "CONCLUSION",      10000),
    ]
    MAX_TOTAL = 150000  # Full paper fits; Gemini 2.5 Flash handles it

    text_parts = []
    total_chars = 0
    for section_key, label, limit in SECTION_ORDER:
        content = sections.get(section_key, "").strip()
        if content:
            chunk = _smart_truncate(content, limit)
            text_parts.append(f"[{label}]\n{chunk}")
            total_chars += len(chunk) + len(label) + 3

    # Fallback: if named sections are sparse, use the raw concatenation
    if total_chars < 500:
        full_text = " ".join([v for v in sections.values() if v.strip()])
        assembled_text = full_text[:MAX_TOTAL]
    else:
        assembled_text = "\n\n".join(text_parts)[:MAX_TOTAL]

    if not assembled_text.strip():
        empty = {"score": 0, "issues": ["No content found."], "suggestions": ["Provide paper content."]}
        return {
            "layer_details": {k: empty for k in
                ["structure_sections", "clarity_writing", "methodology_rigor", "evidence_claims"]},
            "layer_scores": {
                "structure_sections": 0.0, "clarity_writing": 0.0,
                "methodology_rigor": 0.0, "evidence_claims": 0.0, "citations": 0.0,
            }
        }

    # ── Prompt with scoring rubric (OPT-01) ───────────────────────────
    prompt = f"""You are an experienced academic paper reviewer. Evaluate the following research paper across 4 dimensions.
For EACH dimension, provide an integer score (0-10), a list of specific issues found (minimum 2), and a list of actionable suggestions (minimum 2).

IMPORTANT: The paper content below is an excerpt — sections may be truncated for length. Evaluate based on what IS present, not what may be cut off. Do NOT penalize truncation artifacts.

SCORING RUBRIC — use this to assign consistent scores:
  9-10: Exceptional — publishable quality, no significant issues found in the content
  7-8:  Good — minor issues that don't undermine the work's contribution
  5-6:  Adequate — noticeable weaknesses but the core contribution is sound
  3-4:  Weak — significant gaps that undermine the paper's credibility
  1-2:  Poor — fundamental structural or methodological problems
  0:    Section missing or completely inadequate

DIMENSION 1 — Structure & Sections:
- Are standard academic sections present? (Abstract, Introduction, Related Work, Methodology, Results, Conclusion, References)
- Is there logical flow and transitions between sections?
- Is section ordering and balance reasonable?

DIMENSION 2 — Clarity & Writing:
- Grammar correctness and language quality
- Sentence structure and readability
- Vocabulary appropriateness for academic writing
- Coherence and flow within paragraphs

DIMENSION 3 — Methodology Rigor:
- Is the experimental design described clearly?
- Are datasets and evaluation metrics specified?
- Are there baseline comparisons?
- Is there sufficient detail for understanding the approach?

DIMENSION 4 — Evidence & Claims:
- Are claims supported by evidence and data in the text?
- Do conclusions logically follow from the results presented?
- Are there unsupported or overgeneralized claims?
- Is there consistency between abstract claims and findings?

Return ONLY a JSON object with exactly this structure (no markdown, no extra text):
{{
  "structure_sections": {{"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]}},
  "clarity_writing": {{"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]}},
  "methodology_rigor": {{"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]}},
  "evidence_claims": {{"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]}}
}}

FEW-SHOT EXAMPLE — calibration reference for scoring:

Example paper excerpt:
"This study investigates sentiment analysis using machine learning. We collected 500 tweets and applied Naive Bayes. Results show 72% accuracy. We conclude our method is effective for sentiment analysis."

Example output:
{{
  "structure_sections": {{"score": 5, "issues": ["No Related Work or Discussion section present", "Abstract is missing; paper jumps directly into introduction"], "suggestions": ["Add a Related Work section comparing to existing sentiment analysis approaches", "Include a proper abstract summarizing objectives, methods, and findings"]}},
  "clarity_writing": {{"score": 6, "issues": ["Sentences are overly simplistic and lack academic depth", "No transition phrases between sections"], "suggestions": ["Expand sentence complexity and use domain-specific terminology", "Add transition sentences to improve logical flow between paragraphs"]}},
  "methodology_rigor": {{"score": 5, "issues": ["Dataset of 500 tweets is too small without justification", "No baseline comparisons or cross-validation mentioned"], "suggestions": ["Justify dataset size or expand it; report collection methodology", "Compare against at least two baseline methods and use k-fold cross-validation"]}},
  "evidence_claims": {{"score": 5, "issues": ["Claiming method is 'effective' based solely on 72% accuracy without context", "No statistical significance testing reported"], "suggestions": ["Contextualize accuracy against baselines and state-of-the-art results", "Include confidence intervals or significance tests for reported metrics"]}}
}}

END OF EXAMPLE — now evaluate the actual paper below.

Paper content (excerpted):
{assembled_text}"""

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

    # Clamp scores to valid 0-10 range (OPT-01)
    layer_scores = {
        k: max(0.0, min(10.0, float(v.get("score", 0))))
        for k, v in layer_details.items()
    }
    layer_scores["citations"] = 0.0

    return {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }


# ─── Health Check ─────────────────────────────────────────────────────────────

def check_api_health() -> dict:
    """
    Lightweight connectivity test for all loaded Gemini API keys.
    Tests each key sequentially with a minimal prompt to avoid quota burn.
    Returns a dict with per-key status and overall availability.
    """
    keys_status = []
    any_key_working = False

    for key_name, client in _clients:
        try:
            _call_single_key(key_name, client, "ping", max_retries=1, initial_delay=1.0)
            keys_status.append({"key": key_name, "status": "ok"})
            any_key_working = True
        except Exception as e:
            err_msg = str(e)
            # Extract a short error description
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                keys_status.append({"key": key_name, "status": "error: 429"})
            elif "403" in err_msg:
                keys_status.append({"key": key_name, "status": "error: 403"})
            elif "401" in err_msg:
                keys_status.append({"key": key_name, "status": "error: 401"})
            else:
                short_err = err_msg[:80] if len(err_msg) > 80 else err_msg
                keys_status.append({"key": key_name, "status": f"error: {short_err}"})

    return {
        "gemini_keys_loaded": len(_clients),
        "keys_status": keys_status,
        "any_key_working": any_key_working,
        "model": _MODEL,
    }
