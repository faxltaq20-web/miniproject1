# Phase 13 Research: Refine Citation Verification Logic

This document details the research findings regarding the Citations score degradation in Report-4 and outlines the refined scoring pipeline solution.

---

## 1. Analysis of the Score Drop

In Report-4, the Citations & References score fell to **2/10** (down from 7/10 in Report-3) with 0 verified DOIs and 8 unreachable DOIs. This was caused by:

### A. Bibliography Sampling Bias
Capping the check to the first 15 references is too restrictive for papers with large bibliographies (e.g. Llama 3 has 282 references). The first 15 references of the Llama 3 paper are preprint-heavy (ArXiv papers), which do not have standard DOIs indexed in CrossRef. This resulted in 0 verified DOIs in the checked sample.

### B. Semantic Scholar API Rate Limiting (HTTP 429)
Failing back to Semantic Scholar title searches for all of the 15 references exhausted our rate limit, returning `429 Too Many Requests`. This caused 8 title lookups to fail as `"unreachable"`, preventing fallback verification from succeeding.

---

## 2. Refined Solution Architecture

We will implement a hybrid verification loop inside `check_citations()` in `citation_checker.py`:

1. **Extract and Validate DOIs Globally (Entire Bibliography):**
   - Extract all DOIs from the entire `references_text` using the merged labeled and standalone extractor (capped at `MAX_DOIS = 20`).
   - Validate these DOIs in parallel using `ThreadPoolExecutor` (5 workers). Since CrossRef allows 50 req/sec, this will not trigger rate limits.

2. **Capped Title Search Fallback:**
   - Identify references in the bibliography that do not have a DOI or had a DOI that failed validation (`not_found`).
   - From this set, select a small sample (up to **max 5 references**) and verify their titles via Semantic Scholar in parallel.
   - This keeps Semantic Scholar API calls bounded (max 5), avoiding HTTP 429 errors.

3. **Blended Scoring:**
   - Sum verified DOIs and verified titles: `verified = verified_dois + verified_titles`.
   - The score is calculated based on the combined checked set: checked DOIs + checked titles.
   - Maintain existing ArXiv boost and recency scoring logic.
