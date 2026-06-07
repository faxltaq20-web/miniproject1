# ResearchSense — How to Run

## Quick Start

```powershell
cd "c:\Users\mohdf\mini project\MAIN_PROJECT"
python run_local.py sample_paper.pdf
```

## Analyze Any PDF

```powershell
python run_local.py "path\to\your\paper.pdf"
```

## Run Tests

```powershell
python -m pytest tests/ -v
```

## Generate Test PDF (no API needed)

```powershell
python generate_test_pdf.py
```

## Start API Server

```powershell
python main.py
```

Then visit: `http://localhost:8000/docs`

## Environment Setup (first time only)

```powershell
pip install -r requirements.txt
```

Create a `.env` file with your Gemini API keys (up to 5 for auto-rotation):

```
GEMINI_KEY_1=AIza...
GEMINI_KEY_2=AIza...
GEMINI_KEY_3=AIza...
GEMINI_KEY_4=AIza...
GEMINI_KEY_5=AIza...
GEMINI_MODEL=gemini-2.5-flash
```

Each key gives 20 free requests/day. 5 keys = ~50 papers/day.

## Text Compression (Phase 10)

ResearchSense pre-compresses extracted paper sections before sending to Gemini,
reducing prompt size by **30–60%** with no loss of scoring quality.

Set `COMPRESSION_MODE` in your `.env`:

```
COMPRESSION_MODE=light       # default — recommended
COMPRESSION_MODE=aggressive  # more reduction, removes math lines too
COMPRESSION_MODE=off         # disable (use as fallback if scores degrade)
```

| Mode | What it does | Expected reduction |
|---|---|---|
| `off` | No compression — raw text sent | 0% |
| `light` | Whitespace + citations + boilerplate + dedup | ~30–55% |
| `aggressive` | light + formula/math line removal | ~40–65% |

### What gets removed (light mode)
- OCR artifacts: form-feeds, BOM, double spaces, CRLF
- Inline citation markers: `[1]`, `[1,2]`, `(Smith et al., 2020)`
- Raw URLs → replaced with `[URL]`
- Academic boilerplate: "In this paper, we...", "It is worth noting that...", 
  "As mentioned above...", "In recent years...", "See Figure X...", etc.
- Exact duplicate sentences

### Validate compression
```powershell
python validate_compression.py               # offline reduction table
python validate_compression.py --mode aggressive
python validate_compression.py --score-drift # run Gemini comparison (uses API quota)
```

### API endpoint
```
GET /compress-stats
```
Returns the current `COMPRESSION_MODE` setting and last-run compression statistics.
