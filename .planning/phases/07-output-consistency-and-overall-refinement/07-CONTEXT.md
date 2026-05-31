# Phase 7: Output Consistency and Overall Refinement - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement Phase 7 optimization across the entire ResearchSense backend pipeline. This phase enhances LLM scoring consistency, implements highly advanced parallel citation title checking, polishes the PDF report layout, and introduces robust API pre-flight diagnostic protections.

**What this phase includes:**
- **LLM Scoring Consistency:** Strict temperature parameters, quota-rotated client settings, and few-shot anchored prompt engineering.
- **Concurrent Title Verification:** Concurrently querying the Semantic Scholar Search API to verify non-DOI citations without delaying overall execution.
- **Report Polishing:** Custom flowable KeepTogether safeguards, dynamic spacers, and string truncation length protections.
- **Diagnostic Protection:** A robust `/health` endpoint and pre-flight API credentials guards to fail fast when quotas or keys are invalid.

**What this phase does NOT include:**
- HTML/CSS/JS frontend Web UI (explicitly deferred by user request).
- Any modifications to the core 5-layer pipeline architecture weights.

</domain>

<decisions>
## Implementation Decisions

### 1. Scoring Consistency & LLM Settings
- **D-01 (Deterministic Generation):** Set `temperature = 0.0` and `top_p = 0.95` inside all `Client.models.generate_content(...)` API calls to make scoring near-deterministic.
- **D-02 (Few-Shot Prompts):** Update the combined analysis prompt in `gemini_analyzer.py` to include anchored few-shot input-output examples representing exact grade boundaries.
- **D-03 (Primary Provider Default):** Standardize Gemini as the default primary provider across all analysis layers, fully utilizing the 5-key rotation system (`GEMINI_KEY_1` through `GEMINI_KEY_5`).

### 2. Advanced Citation Title Checking
- **D-04 (Semantic Scholar Fallback):** For references lacking DOIs, parse raw titles and query **Semantic Scholar's free public Search API** (`https://api.semanticscholar.org/graph/v1/paper/search?query={title}`) to verify existence.
- **D-05 (Parallel Processing):** Execute title queries concurrently using Python's `concurrent.futures.ThreadPoolExecutor` to restrict overall latency to under 1.5 seconds.
- **D-06 (Selective Sampling Cap):** Cap the number of checked references to a representative subset of up to 10 entries to conserve free-tier API quotas and protect from rate limits. Non-DOI papers can earn up to a perfect **10/10** score if all sampled refs verify successfully.

### 3. Spacing, Formatting & PDF Polish
- **D-07 (Orphan Prevention):** Wrap key PDF segments (such as section headers and their matching custom cards) in ReportLab `KeepTogether` blocks to prevent ugly orphaned text at page breaks.
- **D-08 (Text Overflow Budget):** Apply a strict 135-character budget truncation (using a safe `_sanitize_and_truncate()` function) on dynamic issue and suggestion paragraphs in `report_generator.py` to maintain card grids alignment.

### 4. API Pre-Flight & Diagnostics
- **D-09 (Pre-Flight Guard):** Run a fast, lightweight 1-second credential connectivity test at the start of the `/analyze` route. Fail fast if all keys are missing or invalid before starting PDF parsing.
- **D-10 (Health Endpoint):** Add a FastAPI `/health` GET endpoint to diagnose the status of loaded API keys, CrossRef, and Semantic Scholar connectivity.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Primary user, report tone, budget constraints
- `.planning/REQUIREMENTS.md` — Target requirements for overall optimization
- `.planning/ROADMAP.md` — Phase 7 roadmap entry
- `.planning/STATE.md` — Project milestone tracking state

### Codebase Integration
- `MAIN_PROJECT/gemini_analyzer.py` — Combined multi-layer analysis prompts
- `MAIN_PROJECT/citation_checker.py` — CrossRef DOI checking and reference validation
- `MAIN_PROJECT/report_generator.py` — ReportLab PLATYPUS styling and custom Flowables
- `MAIN_PROJECT/main.py` — FastAPI routes and Orchestrator endpoint

</canonical_refs>

<code_context>
## Existing Code Insights

### Semantic Scholar Query Pattern
```python
# Semantic Scholar search syntax:
# GET https://api.semanticscholar.org/graph/v1/paper/search?query=Title+Name+Here&limit=1
# Returns: {"total": 1, "data": [{"paperId": "...", "title": "..."}]}
```

### KeepTogether Flowable Wrapping
```python
from reportlab.platypus import KeepTogether
# Group SectionHeader and VerdictCard together:
story.append(KeepTogether([
    SectionHeader('=', 'Verdict', 'Final assessment...'),
    Spacer(1, 4 * mm),
    VerdictCard(verdict_text, recommendation)
]))
```

</code_context>

<deferred>
## Deferred Ideas
- **HTML Web UI Frontend (REP-03):** Deferred to focus 100% on backend robustness and verification accuracy.
- **User Accounts and History Caching:** Deferred (remains out of scope).

</deferred>

***

*Phase: 07-output-consistency-and-overall-refinement*
*Context gathered: 2026-05-30*
