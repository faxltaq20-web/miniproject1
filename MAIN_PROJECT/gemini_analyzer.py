from google import genai
from google.genai import types
from openai import OpenAI
import json
import os
import time
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── Provider Setup ──────────────────────────────────────────────────────────
# Both providers are initialized if credentials exist.
# PRIMARY_PROVIDER controls which one is tried first.
# If it fails, the other is used automatically as a fallback.
# If only one set of credentials is provided, only that provider is available.
# ─────────────────────────────────────────────────────────────────────────────

_gemini_client = None
_gemini_model = None
_openai_client = None
_openai_model = None

# Try to initialize Gemini
_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
if _gemini_key:
    try:
        _gemini_client = genai.Client(api_key=_gemini_key)
        _gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    except Exception as e:
        print(f"   [Init] Gemini client init failed: {e}", file=sys.stderr)

# Try to initialize OpenAI-compatible (OpenCode, DeepSeek, Groq, etc.)
_openai_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "").strip()
_openai_base = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "").strip()
if _openai_key and _openai_base:
    try:
        _openai_client = OpenAI(api_key=_openai_key, base_url=_openai_base)
        _openai_model = os.getenv("OPENAI_COMPATIBLE_MODEL", "minimax-2.5")
    except Exception as e:
        print(f"   [Init] OpenAI-compatible client init failed: {e}", file=sys.stderr)

# Determine primary/fallback order from env (default: openai_compatible first)
_primary_pref = os.getenv("PRIMARY_PROVIDER", "openai_compatible").lower().strip()

if _primary_pref == "gemini":
    _providers = []
    if _gemini_client:
        _providers.append(("gemini", _gemini_client, _gemini_model))
    if _openai_client:
        _providers.append(("openai_compatible", _openai_client, _openai_model))
else:
    _providers = []
    if _openai_client:
        _providers.append(("openai_compatible", _openai_client, _openai_model))
    if _gemini_client:
        _providers.append(("gemini", _gemini_client, _gemini_model))

if not _providers:
    raise RuntimeError(
        "No LLM providers configured! "
        "Set GEMINI_API_KEY and/or OPENAI_COMPATIBLE_API_KEY + OPENAI_COMPATIBLE_BASE_URL in your .env file."
    )

# Log what's available
_names = [p[0] for p in _providers]
print(f"   [LLM] Providers loaded: {' -> '.join(_names)} (primary -> fallback)", flush=True)


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
    """Extract the suggested retry delay (in seconds) from a Gemini API error message."""
    import re
    # Match patterns like: "retryDelay": "34s"  or  retry in 34.325106886s
    match = re.search(r'retry(?:Delay["\s:]+["\']?|[_ ]in\s+)([\d.]+)s', err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0


def _call_single_provider(provider_name: str, client, model: str, prompt: str,
                           max_retries: int = 5, initial_delay: float = 5.0) -> str:
    """
    Call one specific provider with retries + smart backoff.
    Parses the API's suggested retry delay and waits accordingly.
    Returns the raw text on success.
    Raises the last exception on persistent failure.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            if provider_name == "openai_compatible":
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            else:  # gemini
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text.strip()
        except Exception as e:
            err_str = str(e)
            is_transient = any(code in err_str for code in
                               ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"]) \
                           or "overloaded" in err_str.lower()

            if is_transient and attempt < max_retries - 1:
                # Use the API's suggested delay if available, otherwise use our backoff
                api_delay = _parse_retry_delay(err_str)
                wait_time = max(delay, api_delay + 2.0) if api_delay > 0 else delay

                print(f"   [Retry] {provider_name} rate-limited. "
                      f"Waiting {wait_time:.0f}s (attempt {attempt+1}/{max_retries})...",
                      flush=True)
                time.sleep(wait_time)
                delay = min(delay * 2.0, 120.0)  # Cap at 2 minutes
            else:
                raise  # Let failover handle it


def _call_llm_with_failover(prompt: str) -> str:
    """
    Try each provider in order. If the primary succeeds, return immediately.
    If it fails after retries, automatically fall back to the next provider.
    """
    last_error = None
    for provider_name, client, model in _providers:
        try:
            return _call_single_provider(provider_name, client, model, prompt)
        except Exception as e:
            last_error = e
            if len(_providers) > 1:
                print(f"   [Failover] {provider_name} failed. Switching to next provider...",
                      file=sys.stderr)
    # All providers exhausted
    raise last_error


def _call_gemini(prompt: str) -> dict:
    """
    Call the LLM with failover. On invalid JSON, retry with strict prompt.
    On persistent failure, return FALLBACK_RESULT instead of crashing.
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
        print(f"   [Error] All LLM providers failed: {e}", file=sys.stderr)
        return FALLBACK_RESULT



def analyze_structure_sections(text: str) -> dict:
    """Layer 01 — Structure & Sections (20%)."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the structural integrity and section organization of this academic paper.
Consider:
- Completeness of standard academic structure (Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion, References)
- Logical flow and transitions between sections
- Section balance (no section is disproportionately short or long)
- Proper section ordering and hierarchy

Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific structural problems found, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Paper content:
{text[:5000]}"""
    return _call_gemini(prompt)


def analyze_clarity_writing(text: str) -> dict:
    """Layer 02 — Clarity & Writing (25%)."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the clarity and writing quality of this academic text.
Consider:
- Grammar correctness and language accuracy
- Sentence structure and readability
- Vocabulary appropriateness for academic writing
- Coherence and flow within paragraphs
- Precision of technical terminology
- Absence of ambiguity and vagueness

Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific clarity/writing problems found, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Text:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_methodology_rigor(text: str) -> dict:
    """Layer 03 — Methodology Rigor (25%)."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the methodology rigor of this academic paper.
Consider:
- Experimental design and reproducibility
- Dataset description and justification
- Evaluation metrics and their appropriateness
- Baseline comparisons and statistical significance
- Threats to validity and limitations acknowledged
- Sufficient detail for replication

Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific methodology weaknesses, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Paper content:
{text[:4000]}"""
    return _call_gemini(prompt)


def analyze_evidence_claims(text: str) -> dict:
    """Layer 04 — Evidence & Claims (20%)."""
    if not text.strip():
        return EMPTY_RESULT
    prompt = f"""Evaluate the evidence and claims in this academic paper.
Consider:
- Whether claims are supported by evidence and data
- Whether conclusions logically follow from results
- Presence of unsupported or overgeneralized claims
- Consistency between abstract claims and actual findings
- Completeness of the conclusion (limitations, future work)
- Absence of contradictions between sections

Return ONLY a JSON object with exactly these three fields:
{{"score": <integer 0-10>, "issues": [<list of specific evidence/claims problems found, minimum 1>], "suggestions": [<list of specific improvements, minimum 1>]}}

Paper content:
{text[:5000]}"""
    return _call_gemini(prompt)


def analyze_paper(sections: dict) -> dict:
    """
    Run all 4 LLM analysis layers on the given sections dict.
    (The 5th layer — Citations — is handled separately by citation_checker.py)

    Args:
        sections: dict with keys: abstract, introduction, methodology,
                  results, discussion, conclusion, references, related_work
                  (empty string "" if section was not detected)

    Returns:
        {
            "layer_details": {
                "structure_sections": {"score": int, "issues": [str], "suggestions": [str]},
                "clarity_writing":    {"score": int, "issues": [str], "suggestions": [str]},
                "methodology_rigor":  {"score": int, "issues": [str], "suggestions": [str]},
                "evidence_claims":    {"score": int, "issues": [str], "suggestions": [str]},
            },
            "layer_scores": {
                "structure_sections": float,  # 0-10
                "clarity_writing": float,
                "methodology_rigor": float,
                "evidence_claims": float,
                "citations": float            # 0.0 placeholder — citation_checker fills this
            }
        }
    """
    # Build full text for layers that need the whole document
    full_text = " ".join([v for v in sections.values() if v.strip()])

    # Clarity checks introduction + methodology (most writing-intensive sections)
    clarity_text = (
        sections.get("introduction", "") + " " + sections.get("methodology", "")
    ).strip() or full_text

    # Methodology uses methodology + results sections
    methodology_text = (
        sections.get("methodology", "") + " " + sections.get("results", "")
    ).strip() or full_text

    # Evidence uses results + discussion + conclusion
    evidence_text = (
        sections.get("results", "") + " " +
        sections.get("discussion", "") + " " +
        sections.get("conclusion", "")
    ).strip() or full_text

    print("   ↳ [1/4] Analyzing structure & sections...", flush=True)
    structure_res = analyze_structure_sections(full_text)
    time.sleep(3.0)

    print("   ↳ [2/4] Analyzing clarity & writing...", flush=True)
    clarity_res = analyze_clarity_writing(clarity_text)
    time.sleep(3.0)

    print("   ↳ [3/4] Analyzing methodology rigor...", flush=True)
    methodology_res = analyze_methodology_rigor(methodology_text)
    time.sleep(3.0)

    print("   ↳ [4/4] Analyzing evidence & claims...", flush=True)
    evidence_res = analyze_evidence_claims(evidence_text)

    layer_details = {
        "structure_sections": structure_res,
        "clarity_writing":    clarity_res,
        "methodology_rigor":  methodology_res,
        "evidence_claims":    evidence_res,
    }

    # Extract scores; default to 0 if missing
    layer_scores = {k: float(v.get("score", 0)) for k, v in layer_details.items()}
    layer_scores["citations"] = 0.0  # citation_checker fills this

    return {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }

