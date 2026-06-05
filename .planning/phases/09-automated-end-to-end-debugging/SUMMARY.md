# Phase 9: Automated End-to-End Debugging

**Status:** Added — awaiting planning
**Created:** 2026-06-05

## Goal
Build an automated test harness that fetches real academic papers from open-access sources (arXiv, Semantic Scholar OA), runs each through the full ResearchSense pipeline, and validates that nothing is missing, broken, or inconsistent — catching bugs across diverse paper types before demo day.

## Approach
1. **Paper Fetcher** — Script that queries arXiv API and Semantic Scholar OA to download ≥5 diverse PDFs (CS, medicine, social science, review, short papers)
2. **Pipeline Runner** — Starts FastAPI server, POSTs each PDF to `/analyze`, then POSTs results to `/report`
3. **Output Validator** — Checks JSON schema, score ranges, section presence, PDF integrity
4. **Gap Analyzer** — Compares output against expected paper metadata (sections, citation count, DOIs)
5. **Summary Reporter** — Aggregates all results into a human-readable pass/fail report
