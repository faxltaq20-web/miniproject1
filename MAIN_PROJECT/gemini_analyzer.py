"""
gemini_analyzer.py — Multi-key Gemini LLM client with automatic key rotation.

Uses up to 5 Gemini API keys. If one key hits rate limits (429),
automatically rotates to the next key. This gives 5× the free-tier quota.
"""

from google import genai
from google.genai import types
import hashlib
import json
import os
import re
import time
import sys
from dotenv import load_dotenv
from pathlib import Path

# Fix Windows CP1252 encoding for Unicode output (before any print calls)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load .env first so COMPRESSION_MODE and GEMINI_KEY_* are available immediately
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)

# ─── Optional: Text Compression (Phase 10, Approach A) ───────────────────────
# Graceful import: if text_compressor.py is absent or broken, pipeline continues
# without compression and prints a one-time warning.
try:
    from text_compressor import compress_sections as _compress_sections
    _COMPRESSOR_AVAILABLE = True
except Exception as _tc_err:
    _COMPRESSOR_AVAILABLE = False
    print(f"   [Compress] WARNING: text_compressor unavailable ({_tc_err}) — running without compression.",
          file=sys.stderr)

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

# ─── Area 2: Structured Output Schema ────────────────────────────────────────
# Gemini's native JSON mode guarantees valid JSON output matching this schema.
# Eliminates all regex-based JSON parsing and the "strict prompt" retry path.
LAYER_SCHEMA_TEMPLATE = {
    "type": "OBJECT",
    "properties": {
        "score": {"type": "INTEGER"},
        "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
        "suggestions": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["score", "issues", "suggestions"],
}

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "structure_sections": LAYER_SCHEMA_TEMPLATE,
        "clarity_writing": LAYER_SCHEMA_TEMPLATE,
        "methodology_rigor": LAYER_SCHEMA_TEMPLATE,
        "evidence_claims": LAYER_SCHEMA_TEMPLATE,
    },
    "required": ["structure_sections", "clarity_writing",
                  "methodology_rigor", "evidence_claims"],
}

# ─── Area 3: System Instruction (static prompt cached by Gemini) ─────────────
SYSTEM_PROMPT = """You are an experienced academic paper reviewer. Evaluate research papers across 4 dimensions.
For EACH dimension, provide an integer score (0-10), a list of specific issues found (minimum 2), and a list of actionable suggestions (minimum 2).
Keep issues and suggestions concise (maximum 1-2 sentences each) and focus on specific, high-impact improvements.

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

IMPORTANT: The paper content may be an excerpt — sections may be truncated for length. Evaluate based on what IS present, not what may be cut off. Do NOT penalize truncation artifacts.

Return a JSON object with exactly this structure:
{
  "structure_sections": {"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]},
  "clarity_writing": {"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]},
  "methodology_rigor": {"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]},
  "evidence_claims": {"score": <0-10>, "issues": ["issue1", "issue2"], "suggestions": ["fix1", "fix2"]}
}"""


# ─── Area 5: Result Caching ───────────────────────────────────────────────────
# Hash-based cache for Gemini analysis results. Same paper text = instant return.
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").strip().lower() == "true"
CACHE_DIR = Path(__file__).resolve().parent / "cache"


def _get_cache_key(assembled_text: str) -> str:
    """Generate a short hash key from the assembled paper text."""
    return hashlib.sha256(assembled_text.encode("utf-8")).hexdigest()[:16]


def _load_cache(key: str) -> dict | None:
    """Load cached analysis result if it exists."""
    if not CACHE_ENABLED:
        return None
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_cache(key: str, result: dict):
    """Save analysis result to cache."""
    if not CACHE_ENABLED:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"   [Cache] Warning: could not write cache: {e}", file=sys.stderr)


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
                     max_retries: int = 3, initial_delay: float = 5.0,
                     use_structured_output: bool = False,
                     system_instruction: str = None) -> str:
    """
    Call Gemini with one specific key. Retries on transient errors.
    Returns raw text on success. Raises on persistent failure.

    When use_structured_output=True, uses Gemini's native JSON mode
    with response_schema to guarantee valid JSON output (Area 2).
    When system_instruction is provided, uses Gemini's system_instruction
    parameter for cached static prompts (Area 3).
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            # Area 2 + 3 + 6: Structured output, system instruction, config tuning
            config_kwargs = {
                "temperature": 0.0,
                "top_p": 0.8,              # Area 6: tighter distribution
                "max_output_tokens": 8000,  # Area 6: raised to avoid truncation of JSON output
            }
            if use_structured_output:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = RESPONSE_SCHEMA
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
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


def _call_llm_with_failover(prompt: str, use_structured_output: bool = False,
                            system_instruction: str = None) -> str:
    """
    Try each Gemini key in order. If one key hits 429, rotate to next.
    Returns raw text on first success.
    """
    last_error = None
    for key_name, client in _clients:
        try:
            return _call_single_key(key_name, client, prompt,
                                    use_structured_output=use_structured_output,
                                    system_instruction=system_instruction)
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
    Call Gemini with key rotation and structured JSON output (Area 2).
    Uses SYSTEM_PROMPT as system_instruction (Area 3) and response_schema
    to guarantee valid JSON — no regex parsing needed.
    On persistent failure, return FALLBACK_RESULT.
    """
    try:
        raw_text = _call_llm_with_failover(
            prompt,
            use_structured_output=True,
            system_instruction=SYSTEM_PROMPT,
        )
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Structured output should prevent this, but fallback just in case
        print("   [Warning] JSON decode failed despite structured output — "
              "returning fallback.", file=sys.stderr)
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
    # ─── Phase 10: Text Compression (Approach A) ─────────────────────────────
    # Pre-compress sections before assembly to reduce prompt token count.
    # Controlled by COMPRESSION_MODE env var: off | light (default) | aggressive
    _compression_mode = os.getenv("COMPRESSION_MODE", "light").strip().lower()
    if _COMPRESSOR_AVAILABLE and _compression_mode != "off":
        try:
            _compressed = _compress_sections(sections, mode=_compression_mode)
            _stats = _compressed.pop("_compression_stats", {})
            sections = _compressed
            _orig  = _stats.get("total_original_chars", 0)
            _comp  = _stats.get("total_compressed_chars", 0)
            _pct   = _stats.get("reduction_pct", 0.0)
            print(f"   [Compress] mode={_compression_mode} | "
                  f"{_orig:,} → {_comp:,} chars | −{_pct}% reduction",
                  flush=True)
        except Exception as _ce:
            print(f"   [Compress] WARNING: compression failed ({_ce}) — continuing uncompressed.",
                  file=sys.stderr)
    # ─────────────────────────────────────────────────────────────────────────

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
    # NOTE: "references" is intentionally excluded here — it is handled
    # separately by citation_checker.py using the raw, uncompressed text
    # from the caller's sections dict (compression is a local rebind).
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

    # ── Area 3: System Instruction + Paper Content (separated) ────────────
    # System prompt is cached by Gemini across calls (warmer model).
    # User message contains only the paper text — shorter, faster.
    user_message = f"Paper content (excerpted):\n{assembled_text}"

    # ── Area 5: Cache check ─────────────────────────────────────────────
    _cache_key = _get_cache_key(assembled_text)
    _cached = _load_cache(_cache_key)
    if _cached is not None:
        print("   ↳ Cache HIT — returning cached analysis (0 API calls)", flush=True)
        return _cached

    print("   ↳ Running multi-layer analysis (single pass)...", flush=True)
    raw = _call_gemini(user_message)

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

    result = {
        "layer_details": layer_details,
        "layer_scores": layer_scores,
    }

    # ── Area 5: Save to cache ───────────────────────────────────────────
    # Only cache if the analysis actually succeeded (no keys in layer_details have analysis_failed=True)
    is_success = not any(v.get("analysis_failed", False) for v in layer_details.values() if isinstance(v, dict))
    if is_success:
        _save_cache(_cache_key, result)

    return result


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


# ─── Verdict Generation (moved from report_generator.py) ─────────────────────
# Parallelized: runs alongside citation checking in /analyze endpoint.

PARAM_LABELS = {
    "structure_sections": "Structure & Sections",
    "clarity_writing":    "Clarity & Writing",
    "methodology_rigor":  "Methodology Rigor",
    "evidence_claims":    "Evidence & Claims",
    "citations":          "Citations & References",
}


def generate_verdict(final_score: float, grade: str, layer_scores: dict,
                     layer_details: dict) -> str:
    """
    Generate a 2-3 sentence verdict paragraph using the LLM.
    Falls back to a template if all providers are unavailable.
    """
    sorted_layers = sorted(layer_scores.items(), key=lambda x: x[1])
    worst_two = sorted_layers[:2]
    top_issues = []
    for layer_key, _ in worst_two:
        details = layer_details.get(layer_key, {})
        issues = details.get("issues", [])
        if issues:
            top_issues.append(
                f"{PARAM_LABELS.get(layer_key, layer_key)}: {issues[0]}"
            )

    prompt = (
        "You are writing a short verdict for an academic paper analysis report.\n"
        "Based on the scores below, write exactly 2-3 sentences summarising the paper's "
        "overall quality. Be specific, professional, and concise.\n"
        "Do not repeat the grade or recommendation — those are shown separately.\n"
        "Do not use bullet points. Plain prose only.\n\n"
        f"Final score: {final_score}/100 ({grade})\n"
        "Key issues found:\n" + "\n".join(f"- {i}" for i in top_issues)
    )

    try:
        return _call_llm_with_failover(prompt)
    except Exception:
        grade_letter = grade.split(" — ")[0].strip() if " — " in grade else "F"
        fallbacks = {
            "A": f"This paper demonstrates strong quality across all evaluated dimensions, "
                 f"achieving a final score of {final_score}/100. "
                 "It meets the standards expected for academic submission.",
            "B": f"This paper shows good overall quality with a score of {final_score}/100, "
                 "but has areas that would benefit from revision. "
                 "Addressing the identified issues will strengthen the submission.",
            "C": f"This paper requires significant revision before it is ready for submission, "
                 f"scoring {final_score}/100. "
                 "The issues identified across multiple dimensions need to be addressed thoroughly.",
        }
        return fallbacks.get(
            grade_letter,
            f"This paper is not suitable for submission in its current state, "
            f"scoring {final_score}/100. "
            "Substantial revisions are required across multiple evaluation dimensions."
        )
