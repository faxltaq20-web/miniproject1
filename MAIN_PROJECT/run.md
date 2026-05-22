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
