# Phase 10: API Token Efficiency & Input Compression — PLAN.md

**Phase Goal:** Reduce the number of tokens sent to the Gemini API per paper analysis call — without losing
the semantic content needed for accurate scoring — by applying a structured text normalization and
compression pipeline on extracted paper sections before they are assembled into the LLM prompt.

**Execution scope:** Plan all 4 approaches. **Execute only Approach A** in this phase.
Approaches B, C, D are fully specified and documented here for future phases or handover.

---

## Context

### Current State (baseline)

| File | Role |
|---|---|
| `MAIN_PROJECT/gemini_analyzer.py` | Assembles paper text → sends to Gemini. Contains `_smart_truncate()` and per-section char limits. |
| `MAIN_PROJECT/section_detector.py` | Extracts raw section text from PDF parse. |
| `MAIN_PROJECT/pdf_parser.py` | PyMuPDF text extraction. |
| `MAIN_PROJECT/token_budget.py` | Token analysis script (analysis only, not runtime). |

### Current limits in `gemini_analyzer.py` (lines 234–241)

```python
SECTION_ORDER = [
    ("abstract",     "ABSTRACT",      5000),
    ("introduction", "INTRODUCTION", 30000),
    ("related_work", "RELATED WORK", 15000),
    ("methodology",  "METHODOLOGY",  40000),
    ("results",      "RESULTS",      40000),
    ("discussion",   "DISCUSSION",   30000),
    ("conclusion",   "CONCLUSION",   10000),
]
MAX_TOTAL = 150000
```

Per-section sum ≈ **18,500 chars ≈ 4,625 tokens** of real content sent.
Bottleneck: **500 RPD** (requests/day), not token count. But compression reduces latency and
enables future migration to smaller/cheaper models.

---

## Formal Problem Definition

Given extracted paper sections **S = {s₁, s₂, ..., sₙ}**, design a lossless-semantic
compression function **f(S) → S'** such that:

1. **|S'| ≪ |S|** — compressed representation is significantly shorter in token count
2. **sem(S') ≈ sem(S)** — semantic content relevant for scoring is fully preserved
3. **score(f(S)) ≈ score(S)** — Gemini's output scores when given S' match S within **±0.5 per layer**
   (measured on a 5-paper validation set)

NLP literature names: **"prompt compression"**, **"context distillation for LLM inference"**,
**"selective context compression"**

---

## All 4 Approaches — Full Specification

### ─────────────────────────────────────────────────────
### Approach A — Structured Normalization ✅ EXECUTE THIS PHASE
### ─────────────────────────────────────────────────────

> **Research keyword:** "extractive prompt compression", "text normalization for NLP"

**Philosophy:** Remove redundant, repetitive, or boilerplate text from each section using
deterministic regex and string operations — NO external ML dependencies, NO extra API calls.

**Expected reduction:** 30–50% per section. Zero latency overhead.

**What gets stripped:**

| Category | Examples | Regex / Method |
|---|---|---|
| Academic filler phrases | "In this paper, we...", "It is worth noting that...", "As mentioned above...", "In summary, we have..." | Regex match on sentence start |
| OCR artifacts | Double spaces, `\x0c` form-feeds, `\ufeff` BOM, mixed line endings | `re.sub` + `str.strip()` |
| Footnote/citation markers | `[1]`, `[12,15]`, `(Smith et al., 2020)`, `¹²` superscripts | Regex removal |
| Figure/table references | "See Figure 3.", "As shown in Table 2", "Refer to Appendix A" | Pattern matching |
| Repeated blank lines | 3+ consecutive newlines → 1 | `re.sub(r'\n{3,}', '\n\n', text)` |
| Duplicate sentences | Exact/near-duplicate sentences across paragraphs | Seen-set deduplication |
| Section header echoes | Section text that starts by re-stating the section name | Strip first sentence if it matches section label |
| URL noise | Raw URLs embedded mid-text (not in references) | `re.sub(r'https?://\S+', '[URL]', text)` |
| Equation-heavy lines | Lines that are >60% non-alphabetic (math/formula lines) | Character class ratio check |

**Files to create/modify:**

| File | Action | Description |
|---|---|---|
| `MAIN_PROJECT/text_compressor.py` | **CREATE** | New module. Public API: `compress_sections(sections: dict, mode: str = "light") -> dict` |
| `MAIN_PROJECT/gemini_analyzer.py` | **MODIFY** | Import and call `text_compressor.compress_sections(sections, mode)` before text assembly |
| `MAIN_PROJECT/.env` / `.env.example` | **MODIFY** | Add `COMPRESSION_MODE=light` (options: `off`, `light`, `aggressive`) |

**`text_compressor.py` — Full specification:**

```python
"""
text_compressor.py — Lossless-semantic text compression for ResearchSense.

Reduces assembled paper section text by 30-50% before LLM prompt assembly.
Approach A: Deterministic normalization — no external dependencies, zero latency overhead.

Public API:
    compress_sections(sections: dict, mode: str = "light") -> dict
        sections: dict of {section_key: raw_text} from section_detector.py
        mode: "off" | "light" | "aggressive"
        returns: dict with same keys, compressed text values + "_compression_stats" metadata key
"""

import re
from typing import Tuple

# ── Boilerplate phrase patterns (sentence-level removal) ──────────────────────
# These phrases add no information for scoring and are common in academic papers.
BOILERPLATE_PATTERNS = [
    # Forward references
    r"[Ii]n this (paper|work|study|section|article),?\s+we\s+\w+",
    r"[Tt]he rest of (this paper|the paper) is (organized|structured) as follows",
    r"[Tt]he remainder of this (paper|work|article) is (organized|structured)",
    r"[Tt]he (paper|article|work) is (organized|structured) as follows",
    # Filler transitions
    r"[Ii]t is worth (noting|mentioning) that",
    r"[Ii]t should be noted that",
    r"[Aa]s (mentioned|discussed|described|shown|noted) (above|below|previously|earlier|in Section \w+)",
    r"[Aa]s we (mentioned|discussed|showed|described) (above|earlier|previously|in Section \w+)",
    r"[Aa]s can be seen (from|in) (the (above|following|previous))",
    # Redundant summary phrases
    r"[Ii]n (summary|conclusion|short|brief),? (we|our|the|this)",
    r"[Tt]o (summarize|conclude|sum up),?",
    r"[Aa]s (described|shown|explained|mentioned) above",
    # Generic motivation
    r"[Ii]n recent years[,.]",
    r"[Ww]ith the (rapid|recent|growing|increasing) development of",
    r"[Ww]ith the (advent|rise|emergence) of",
    r"[Rr]ecently[,.]?\s+\w+ has (become|gained|attracted)",
    r"[Tt]here is (a|an) (growing|increasing) (interest|demand|need) in",
    # Explicit section references (figure/table callouts)
    r"[Ss]ee (Figure|Fig\.|Table|Appendix|Section) \w+",
    r"[Aa]s shown in (Figure|Fig\.|Table|Appendix) \w+",
    r"[Rr]efer to (Figure|Fig\.|Table|Appendix) \w+",
    r"[Ss]hown in (Figure|Fig\.|Table|Appendix) \w+",
    r"[Aa]s (illustrated|depicted|presented|summarized) in (Figure|Fig\.|Table) \w+",
]

# ── Citation/reference marker patterns ────────────────────────────────────────
CITATION_PATTERNS = [
    r'\[\d+(?:[,–\-]\d+)*\]',          # [1], [12], [1,2,3], [1-5]
    r'\(\w[\w\s,\.&]+,?\s+\d{4}[a-z]?\)',  # (Smith et al., 2020), (Jones, 2019a)
    r'[\u00b9\u00b2\u00b3\u2074-\u2079]+',  # Superscript numerals ¹²³
    r'(?<!\w)\^\{\d+(?:,\d+)*\}',      # LaTeX ^{1,2}
]

# ── Equation/formula line detection ───────────────────────────────────────────
def _is_formula_line(line: str) -> bool:
    """Return True if line is predominantly mathematical (>60% non-alphabetic)."""
    if len(line.strip()) < 5:
        return False
    alpha = sum(1 for c in line if c.isalpha())
    return alpha / len(line) < 0.40  # Less than 40% letters = formula-heavy

def _normalize_whitespace(text: str) -> str:
    """Collapse multiple blank lines, strip form-feeds and BOM."""
    text = text.replace('\x0c', '\n')  # form-feed
    text = text.replace('\ufeff', '')   # BOM
    text = re.sub(r'\r\n', '\n', text) # normalize line endings
    text = re.sub(r'[ \t]{2,}', ' ', text)  # collapse inline spaces
    text = re.sub(r'\n{3,}', '\n\n', text)  # max 2 consecutive newlines
    return text.strip()

def _remove_citations(text: str) -> str:
    """Strip inline citation markers."""
    for pattern in CITATION_PATTERNS:
        text = re.sub(pattern, '', text)
    return text

def _remove_boilerplate_sentences(text: str) -> str:
    """
    Remove sentences matching boilerplate patterns.
    Operates sentence-by-sentence — only strips the matched clause, not the full sentence,
    to avoid aggressive content loss.
    """
    for pattern in BOILERPLATE_PATTERNS:
        # Remove the matched clause (up to end of phrase or comma)
        text = re.sub(pattern + r'[^.!?\n]*[,]?\s*', '', text)
    return text

def _remove_url_noise(text: str) -> str:
    """Replace raw URLs with placeholder."""
    return re.sub(r'https?://\S+', '[URL]', text)

def _deduplicate_sentences(text: str) -> str:
    """
    Remove exact duplicate sentences. Near-duplicate detection (light mode):
    if two sentences share >85% character overlap, remove the second.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = set()
    result = []
    for sent in sentences:
        key = re.sub(r'\s+', ' ', sent.strip().lower())
        if key not in seen and len(key) > 10:
            seen.add(key)
            result.append(sent)
    return ' '.join(result)

def _remove_formula_lines(text: str, aggressive: bool = False) -> str:
    """
    In aggressive mode: drop lines that are predominantly mathematical.
    In light mode: only remove lines that are ENTIRELY non-alphabetic.
    """
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue
        if aggressive and _is_formula_line(stripped):
            continue
        elif not aggressive:
            # Only drop lines with NO alphabetic characters (pure math/symbols)
            if stripped and not any(c.isalpha() for c in stripped):
                continue
        result.append(line)
    return '\n'.join(result)

def _compress_section(text: str, mode: str) -> Tuple[str, int, int]:
    """
    Apply compression to a single section text.
    Returns: (compressed_text, original_len, compressed_len)
    """
    original_len = len(text)
    
    # Step 1: Always normalize whitespace (both modes)
    text = _normalize_whitespace(text)
    
    # Step 2: Remove URL noise (both modes)
    text = _remove_url_noise(text)
    
    # Step 3: Remove citation markers (both modes)
    text = _remove_citations(text)
    
    # Step 4: Remove pure-symbol lines (both modes)
    text = _remove_formula_lines(text, aggressive=False)
    
    if mode == "light":
        # Light: boilerplate phrases + deduplication
        text = _remove_boilerplate_sentences(text)
        text = _deduplicate_sentences(text)
        
    elif mode == "aggressive":
        # Aggressive: everything in light + formula lines
        text = _remove_boilerplate_sentences(text)
        text = _deduplicate_sentences(text)
        text = _remove_formula_lines(text, aggressive=True)
    
    # Final whitespace cleanup
    text = _normalize_whitespace(text)
    
    return text, original_len, len(text)


def compress_sections(sections: dict, mode: str = "light") -> dict:
    """
    Compress all paper sections using Approach A: Structured Normalization.

    Args:
        sections: dict of {section_key: raw_text} from section_detector.py
        mode: "off" | "light" | "aggressive"
            - "off": passthrough, no compression
            - "light": whitespace + citations + boilerplate + dedup
            - "aggressive": light + formula line removal

    Returns:
        dict with same section keys, compressed text values.
        Adds "_compression_stats" key with per-section stats:
        {
            "total_original_chars": int,
            "total_compressed_chars": int,
            "reduction_pct": float,
            "per_section": {section_key: {"original": int, "compressed": int, "pct": float}}
        }
    """
    if mode == "off":
        result = dict(sections)
        result["_compression_stats"] = {"mode": "off", "reduction_pct": 0.0}
        return result

    result = {}
    stats = {"mode": mode, "per_section": {}, "total_original_chars": 0, "total_compressed_chars": 0}

    for key, text in sections.items():
        if key.startswith("_") or not isinstance(text, str):
            result[key] = text
            continue
        
        compressed, orig_len, comp_len = _compress_section(text, mode)
        result[key] = compressed
        
        pct = round((1 - comp_len / orig_len) * 100, 1) if orig_len > 0 else 0.0
        stats["per_section"][key] = {"original": orig_len, "compressed": comp_len, "pct": pct}
        stats["total_original_chars"] += orig_len
        stats["total_compressed_chars"] += comp_len

    total_orig = stats["total_original_chars"]
    total_comp = stats["total_compressed_chars"]
    stats["reduction_pct"] = round((1 - total_comp / total_orig) * 100, 1) if total_orig > 0 else 0.0

    result["_compression_stats"] = stats
    return result
```

**Integration point in `gemini_analyzer.py`:**

```python
# At top of analyze_paper():
from text_compressor import compress_sections
import os

compression_mode = os.getenv("COMPRESSION_MODE", "light")
if compression_mode != "off":
    sections = compress_sections(sections, mode=compression_mode)
    stats = sections.pop("_compression_stats", {})
    print(f"   [Compress] Mode={compression_mode}, "
          f"reduction={stats.get('reduction_pct', 0)}% "
          f"({stats.get('total_original_chars',0):,} → {stats.get('total_compressed_chars',0):,} chars)",
          flush=True)
```

**.env addition:**
```
COMPRESSION_MODE=light   # Options: off | light | aggressive
```

---

### ─────────────────────────────────────────────────────
### Approach B — Semantic Chunking + Key Sentence Extraction 📋 FUTURE PHASE
### ─────────────────────────────────────────────────────

> **Research keyword:** "extractive summarization for RAG", "sentence scoring for prompt engineering",
> "BM25 sentence selection", "TF-IDF sentence ranking"

**Philosophy:** Score each sentence by its relevance to the 4 evaluation dimensions
(structure, clarity, methodology, evidence) and keep only the top-K sentences per section.

**Expected reduction:** 60–75% with very high semantic fidelity.

**Dependencies:** `sentence-transformers` OR `sklearn` (TF-IDF based, lighter)

**Architecture:**

```
section_text
     │
     ▼
sentence_tokenizer()        ← split on [.!?] + newline
     │
     ▼
score_sentences()           ← TF-IDF cosine similarity against evaluation_query_vectors
     │                         e.g., queries = ["methodology experimental design dataset",
     │                                           "grammar clarity writing quality",
     │                                           "results evidence statistical significance",
     │                                           "structure sections organization"]
     ▼
top_k_sentences()           ← select top-K by score per section
     │                         K = max(5, section_token_budget // avg_sentence_tokens)
     ▼
reassemble_text()           ← join in original order (preserve flow)
```

**Key design decision:** Use TF-IDF (scikit-learn, already likely installed) rather than
sentence-transformers to avoid a 400MB model download in the free tier environment.

**Files:**

| File | Action |
|---|---|
| `MAIN_PROJECT/text_compressor.py` | Add `compress_semantic(section_text, query_vectors, k)` function |
| `MAIN_PROJECT/requirements.txt` | Add `scikit-learn>=1.3.0` |

**Prerequisite:** Approach A must be run first (B operates on A's output as a pre-processor)

---

### ─────────────────────────────────────────────────────
### Approach C — LLM-Based Meta-Prompt Compression 📋 FUTURE PHASE
### ─────────────────────────────────────────────────────

> **Research keyword:** "LLMLingua prompt compression Microsoft", "selective context compression LLM",
> "LLM-Lingua-2 arxiv", "AutoCompressor", "RECOMP context compression"

**Philosophy:** Use a fast/cheap LLM (or LLMLingua open-source library) to produce a
"review digest" of each section, then feed that digest to the main scoring prompt.
Two-stage pipeline: **compress → score**.

**Expected reduction:** 70–80%

**Tradeoff:** Adds 1 extra API call per paper → same RPD cost as before; benefit is only
latency reduction on the scoring call + ability to use a very small scorer model.

**LLMLingua Option (fully offline, no extra API cost):**

```
pip install llmlingua
```

LLMLingua compresses a prompt using token-level perplexity from a small local model
(e.g., `llama-2-7b` or `phi-2`) to remove tokens the scoring LLM doesn't "need".
- Works without network access
- Requires ~4GB local model (feasible on dev, not on free-tier server)
- Compression ratio configurable: typically 4:1 to 10:1

**Meta-prompt Option (Gemini Flash — 1 extra RPD call):**

```python
compress_prompt = f"""
You are a research paper summarizer for peer review.
Given the following {section_name} section, produce a compact review digest
preserving ONLY information relevant for evaluating:
- Structure and section organization
- Writing clarity and grammar quality
- Methodology rigor and experimental design
- Evidence and claim support

Target length: under {target_chars} characters.
Return ONLY the digest text, no preamble.

SECTION TEXT:
{section_text}
"""
```

**Files:**

| File | Action |
|---|---|
| `MAIN_PROJECT/text_compressor.py` | Add `compress_llm_meta(section_text, target_chars)` |
| `MAIN_PROJECT/requirements.txt` | Optional: `llmlingua` if local model path configured |
| `MAIN_PROJECT/.env` | Add `COMPRESSION_LLM_ENABLED=false` flag |

**Prerequisite:** Requires Phase 10 Validation Harness (Plan 2) to measure quality tradeoff.

---

### ─────────────────────────────────────────────────────
### Approach D — Template-Driven Section Summarization 📋 FUTURE PHASE
### ─────────────────────────────────────────────────────

> **Research keyword:** "information extraction for structured summarization",
> "slot filling NLP", "template-based text summarization", "schema-guided summarization"

**Philosophy:** Instead of sending raw section prose, extract a set of structured
"review-relevant facts" per section using regex and NLP patterns, then format them as
compact structured text blocks.

**Expected reduction:** 50–65%, fully deterministic, no ML dependencies.

**Section Templates:**

```python
TEMPLATES = {
    "abstract": {
        "fields": ["objective", "method", "results", "contribution"],
        "prompts": [
            r"(aim|objective|goal|purpose)[s]?\s+(is|are|of|:)\s+([^.]+\.)",
            r"(we propose|we present|we introduce|we develop)\s+([^.]+\.)",
            r"(result[s]?|experiment[s]?|evaluation)\s+show[s]?\s+([^.]+\.)",
            r"(contribution[s]?|novelty|key|main)\s+(is|are|include[s]?)\s+([^.]+\.)",
        ]
    },
    "methodology": {
        "fields": ["dataset", "model_architecture", "baselines", "metrics", "training"],
        "prompts": [
            r"(dataset[s]?|corpus|data)\s+(used|collected|consists)\s+([^.]+\.)",
            r"(baseline[s]?|compar[e]?[d]? (with|against|to))\s+([^.]+\.)",
            r"(evaluat[e]?[d]? using|metric[s]?|measure[d]? by)\s+([^.]+\.)",
            r"(train[ed]?|fine-tun[ed]?|optimiz[ed]?)\s+(using|with|on)\s+([^.]+\.)",
        ]
    },
    "results": {
        "fields": ["primary_metric", "comparison", "key_numbers", "significance"],
        "prompts": [
            r"(achiev[e]?[d]?|obtain[e]?[d]?|reach[e]?[d]?)\s+([\d.]+%?)\s+([^.]+\.)",
            r"(outperform[s]?|surpass[e]?[s]?|exceed[s]?)\s+([^.]+)\s+by\s+([^.]+\.)",
            r"(improve[s]?|gain[s]?|increase[s]?)\s+([\d.]+%?)\s+([^.]+\.)",
        ]
    },
}
```

**Output format:**

```
[ABSTRACT DIGEST]
OBJECTIVE: To propose a transformer-based method for detecting plagiarism in academic papers.
METHOD: Fine-tuned BERT on 50,000 document pairs with contrastive learning.
RESULTS: 94.2% F1 score, outperforming baseline by 8.3%.
CONTRIBUTION: First large-scale study using contrastive learning for academic plagiarism detection.
```

This structured format is denser than prose for the reviewer task: all relevant facts,
zero redundant filler, naturally fits the scoring rubric dimensions.

**Files:**

| File | Action |
|---|---|
| `MAIN_PROJECT/text_compressor.py` | Add `compress_template(section_text, section_key)` function |
| No new dependencies | Pure regex + string formatting |

**Prerequisite:** Requires Plan 2 validation harness to measure fidelity vs. prose scoring.

---

## Execution Plan (This Phase — Approach A Only)

### Plan 1: `text_compressor.py` — Structured Normalization Module ✅ EXECUTE

**Goal:** Implement and unit-test the Approach A compression module.

**Tasks:**

- [ ] **1.1** Create `MAIN_PROJECT/text_compressor.py` with the full implementation above
  - `_normalize_whitespace(text)` — collapse blanks, strip BOM/form-feed
  - `_remove_citations(text)` — strip `[1]`, `(Author, YYYY)`, superscripts
  - `_remove_url_noise(text)` — replace raw URLs with `[URL]`
  - `_remove_boilerplate_sentences(text)` — strip 30+ academic filler patterns
  - `_deduplicate_sentences(text)` — exact sentence deduplication
  - `_remove_formula_lines(text, aggressive)` — strip math-only lines
  - `_compress_section(text, mode)` — orchestrate all steps
  - `compress_sections(sections, mode)` — public API with stats metadata

- [ ] **1.2** Add `COMPRESSION_MODE=light` to `MAIN_PROJECT/.env` and `.env.example`

- [ ] **1.3** Modify `MAIN_PROJECT/gemini_analyzer.py` — integrate compression:
  - Import `compress_sections` from `text_compressor`
  - Read `COMPRESSION_MODE` from env at top of `analyze_paper()`
  - Call compressor on `sections` dict before the `SECTION_ORDER` loop
  - Pop `_compression_stats` and print reduction summary
  - Fallback: if import fails, log warning and continue without compression

- [ ] **1.4** Write unit tests in `MAIN_PROJECT/tests/test_text_compressor.py`:
  - `test_off_mode_passthrough` — mode="off" returns identical sections
  - `test_normalize_whitespace_collapses_blanks`
  - `test_citation_bracket_removal` — `[1]`, `[1,2]`, `[1-5]` all removed
  - `test_citation_author_year_removal` — `(Smith et al., 2020)` removed
  - `test_url_replaced_with_placeholder`
  - `test_boilerplate_in_this_paper_removed`
  - `test_boilerplate_as_mentioned_above_removed`
  - `test_boilerplate_in_recent_years_removed`
  - `test_duplicate_sentences_deduplicated`
  - `test_compression_stats_returned` — stats dict present in return
  - `test_reduction_pct_within_expected_range` — 20%–60% reduction on real-ish text
  - `test_aggressive_mode_removes_formula_lines`
  - `test_light_mode_preserves_formula_lines`
  - `test_empty_section_handled_gracefully`
  - `test_section_key_starting_with_underscore_preserved`

---

### Plan 2: Validation Harness — Score Drift & Token Reduction Metrics ✅ EXECUTE

**Goal:** Measure: (a) how much text is reduced, (b) whether Gemini scores drift when using
compressed vs. uncompressed input, on the 5 validation papers from Phase 9.

**Tasks:**

- [ ] **2.1** Create `MAIN_PROJECT/validate_compression.py`:
  - Load 5 pre-cached paper section dicts (from Phase 9 output JSONs or from test PDFs)
  - For each paper, run `compress_sections(sections, mode="light")` and `mode="aggressive"`
  - Print per-section reduction table: `original_chars | compressed_chars | reduction_%`
  - Print overall stats: average reduction, min/max per section

- [ ] **2.2** Add score-drift comparison (requires live Gemini — optional/manual):
  - Run `analyze_paper(original_sections)` → record scores
  - Run `analyze_paper(compressed_sections)` → record scores
  - Print diff table: `layer | original_score | compressed_score | delta`
  - Flag if any delta > 0.5 as a WARNING
  - Write results to `MAIN_PROJECT/debug/compression_validation_report.txt`

- [ ] **2.3** Add reduction assertions to prevent regression:
  - Assert total char reduction ≥ 20% (minimum acceptable — fail with clear message if not)
  - Assert no section grows larger after compression
  - These run as pytest fixtures in `test_text_compressor.py`

---

### Plan 3: Pipeline Integration & Configurable Compression Modes ✅ EXECUTE

**Goal:** Wire the compressor into the live FastAPI pipeline with runtime configurability.

**Tasks:**

- [ ] **3.1** Verify `gemini_analyzer.py` integration from Plan 1 works end-to-end:
  - Run `python run_local.py MAIN_PROJECT/sample_paper.pdf` with `COMPRESSION_MODE=light`
  - Confirm compression stats print to console
  - Confirm scores are within ±0.5 of uncompressed baseline

- [ ] **3.2** Add `/compress-stats` diagnostic endpoint to `MAIN_PROJECT/main.py` (optional):
  - `GET /compress-stats` → returns current `COMPRESSION_MODE` and last-call stats

- [ ] **3.3** Update `MAIN_PROJECT/run.md` with compression mode documentation:
  - Explain `off`, `light`, `aggressive` modes
  - Note expected reduction % per mode
  - Note that mode `off` is the safe baseline if scores degrade unexpectedly

- [ ] **3.4** Run full pytest suite — confirm all existing + new tests pass:
  - Target: all prior 44 tests + ≥15 new compression tests = **≥59 tests passing**

---

## Verification Criteria

| # | Criterion | Pass condition |
|---|---|---|
| V1 | `text_compressor.py` importable | `from text_compressor import compress_sections` succeeds |
| V2 | `compress_sections` reduces text | ≥20% reduction on any real section text |
| V3 | Mode `off` is lossless | Output identical to input (byte-for-byte) |
| V4 | Unit tests pass | ≥15 new tests green |
| V5 | Full test suite passes | All ≥59 tests pass (prior 44 + new) |
| V6 | Live pipeline runs with compression | `run_local.py` completes without error, prints compression stats |
| V7 | Score drift acceptable | If Gemini is called: delta ≤ 0.5 per layer vs. uncompressed baseline |
| V8 | Graceful fallback | If `text_compressor.py` is missing/broken, pipeline runs with a warning |

---

## Future Phases Reference

| Approach | Phase | Trigger Condition |
|---|---|---|
| B — Semantic Chunking | Phase 11 | Approach A reduction < 30% on real papers, or model downgrade to 8B needed |
| C — LLMLingua/Meta-Prompt | Phase 12 | Paid tier migration, or latency > 30s/paper with Approach A+B |
| D — Template Summarization | Phase 12 (alt) | If score drift in B/C exceeds threshold and structured output needed |

---

## Dependencies

- **Phase 9 must be complete** for the 5-paper validation paper cache
- No new Python package dependencies for Approach A
- `COMPRESSION_MODE` env var must be set in `.env` (default: `light`)

---

*Plan created: 2026-06-07 | Phase 10 | ResearchSense*
