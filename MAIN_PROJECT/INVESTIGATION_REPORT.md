# Investigation Report: ResearchSense Issues

**Date:** 2026-06-09
**Investigator:** opencode (mimo-v2.5-free)

---

## Issue 1: Section Detection Scores Still Low

### Data Collected

| Paper | Detected | Missing | Fallback Triggered? |
|-------|----------|---------|---------------------|
| CS/ML (2606.06480) | 6/7 | Abstract | No (count=6) |
| CS Survey (2606.01015) | 3/7 | abstract, related_work, methodology, results, discussion | No (count=3) |
| Physics (2605.29839) | 2/7 | abstract, methodology, results, conclusion | No (count=2) |
| Bio/Medical (2606.02625) | 6/7 | related_work, methodology | No (count=6) |
| Econ/Social (2606.00614) | 5/7 | results, discussion, conclusion | No (count=5) |

### Root Causes Identified

#### 1. Fallback Scan Never Triggers (PRIMARY CAUSE)
**Location:** `section_detector.py:156`

```python
if detected_count <= 1:
    # fallback scan...
```

The fallback scan only triggers when 0 or 1 sections are detected. But ALL debug papers have 2+ sections detected (Introduction + References at minimum), so the fallback never runs.

**Impact:** The fallback was designed to catch papers with poor section detection, but it's too conservative.

#### 2. Missing Keywords in SECTION_KEYWORDS
**Location:** `section_detector.py:16-28`

The Bio/Medical paper has heading `## **2.Materials and methods**` which cleans to `"materials and methods"`. This doesn't match any keyword:
- "methodology" ❌
- "methods" ❌
- "method" ❌

**Missing keywords:**
- `"materials and methods"` → methodology
- `"materials & methods"` → methodology
- `"data and methods"` → methodology
- `"experimental methods"` → methodology
- `"study design"` → methodology
- `"experimental design"` → methodology

#### 3. Non-Standard Section Names
The CS Survey paper uses section names like:
- "III. FOUNDATIONAL DEFINITIONS & TAXONOMY"
- "IV. ARCHITECTURE PROPOSALS"
- "V. APPLICATION PILLARS"
- "VI. INTELLIGENCE DISTRIBUTION MODELS"

These don't match any keywords in SECTION_KEYWORDS. The detector correctly identifies them as headings (they're short, capitalized, numbered) but can't map them to standard sections.

#### 4. `_clean_heading` Doesn't Handle All Formats
**Location:** `section_detector.py:46-59`

Input: `## **2.Materials and methods**`
After cleaning: `materials and methods`

The regex `r'^\d+(\.\d+)*\.?\s*'` expects a space or dot after the number. When there's no space (e.g., `2.Materials`), the number isn't fully stripped.

#### 5. `_is_heading_line` Too Permissive
**Location:** `section_detector.py:85-86`

```python
if len(stripped) < 80 and not stripped.endswith(".") and not stripped.startswith("|"):
    return True
```

This considers ANY short line without a trailing period as a heading, including body text like:
- "Our main contributions are as follows:"
- "We model the interaction as a partially observable Markov game"

This can cause false positives that disrupt section detection.

### Proposed Fixes

1. **Lower fallback threshold** from `detected_count <= 1` to `detected_count <= 3`
2. **Add missing keywords** to SECTION_KEYWORDS
3. **Improve heading cleaning** to handle no-space formats
4. **Make `_is_heading_line` more restrictive** for body text lines

---

## Issue 2: DOI Backtick Bug

### Finding: BUG IS FIXED

The DOI extraction now correctly handles backticks and smart quotes. Testing confirms:

```
Input:  'DOI: 10.1007/s10844-017-0473-4`'
Output: '10.1007/s10844-017-0473-4'  ✅

Input:  'DOI: 10.1007/s10844-017-0473-4"'
Output: '10.1007/s10844-017-0473-4'  ✅

Input:  'DOI: 10.1007/s10844-017-0473-4\u201d'
Output: '10.1007/s10844-017-0473-4'  ✅
```

The debug results showing backticks (e.g., `"10.1007/s10844-017-0473-4`"`) were from a run BEFORE the fix was applied. The current code has:

1. `TRAILING_JUNK` regex includes backtick: `r'[.,;:)\]>\'\"\`\\\-\'\'\u2018\u2019\u201c\u201d]+$'`
2. `DOI_STANDALONE` excludes backticks from match: `[^\s,;)\]>\'\"\`\'\'\u2018\u2019\u201c\u201d]+`

Both patterns work correctly together.

### All 90 Tests Pass ✅

```
90 passed in 2.53s
```

---

## Summary

| Issue | Status | Root Cause |
|-------|--------|------------|
| Section Detection | **OPEN** | Fallback threshold too high; missing keywords; heading cleaning gaps |
| DOI Backtick Bug | **FIXED** | Already resolved in current code |

### Priority Actions for Section Detection

1. Lower fallback threshold to `detected_count <= 3`
2. Add 6+ missing methodology keywords
3. Fix `_clean_heading` for no-space number formats
4. Add stricter heuristics to `_is_heading_line`
