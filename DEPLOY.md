# ResearchSense — Deployment Guide

Deploy ResearchSense as a public web application on **Render** (free tier) in under 10 minutes.

---

## Architecture (Single-Deployment)

```
User Browser
    │
    ▼
Render Web Service (https://researchsense.onrender.com)
    │
    ├── GET /           → serves frontend/index.html  (FastAPI StaticFiles)
    ├── GET /style.css  → serves frontend/style.css
    ├── GET /app.js     → serves frontend/app.js
    ├── POST /analyze   → FastAPI: PDF analysis pipeline
    ├── POST /report    → FastAPI: PDF report generation
    └── GET /health     → FastAPI: health check
```

The FastAPI backend serves **both** the API endpoints and the static frontend files — one URL, one service, no CORS issues.

---

## Prerequisites

- [x] A **GitHub account** with this repository pushed to it
- [x] A **Render account** — sign up free at [render.com](https://render.com)
- [x] At least one **Gemini API key** from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## Step 1: Push to GitHub

Make sure your latest code is on GitHub:

```bash
cd "c:\Users\mohdf\mini project"
git add .
git commit -m "feat(14): web app deployment — StaticFiles, Procfile, render.yaml"
git push origin main
```

> ⚠️ **Critical:** Verify `.env` is in `.gitignore` and NOT committed. Never push your API keys.

---

## Step 2: Create a Render Web Service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Select **Build and deploy from a Git repository**
4. Connect your GitHub account and choose the `mini project` repository
5. Fill in the service settings:

| Field | Value |
|---|---|
| **Name** | `researchsense` (or any name you like) |
| **Root Directory** | `MAIN_PROJECT` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free |

---

## Step 3: Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

| Key | Value | Secret? |
|---|---|---|
| `GEMINI_KEY_1` | `your-actual-gemini-api-key` | ✅ Yes — mark as secret |
| `GEMINI_KEY_2` | *(leave blank or add more keys)* | — |
| `GEMINI_MODEL` | `gemini-2.5-flash` | — |
| `COMPRESSION_MODE` | `light` | — |
| `CACHE_ENABLED` | `true` | — |
| `CONTACT_EMAIL` | `your-email@example.com` | — |

> 💡 **Tip:** You can add up to 5 Gemini API keys from different Google accounts. The system automatically rotates to the next key if one hits its rate limit. This gives you 5× the free-tier capacity.

---

## Step 4: Deploy

1. Click **Create Web Service**
2. Render will clone your repo, install dependencies, and start the server
3. First deployment takes ~2–3 minutes
4. Your app is live at: `https://researchsense.onrender.com` (or your chosen name)

---

## Step 5: Verify It Works

Visit your URL and check:
- [ ] Frontend loads — upload zone, header, health badge visible
- [ ] Health badge shows "System: Healthy" (may take 30s on first cold start)
- [ ] Upload a PDF → analysis runs → results dashboard appears
- [ ] "Download PDF Report" button works
- [ ] "Try Pre-Cached Sample" demo mode works

---

## Free-Tier Limitations & Workarounds

### Cold Starts (~30–50 seconds)

Render's free Web Service **sleeps after 15 minutes of inactivity**. The first request after sleep wakes the server, which takes 30–50 seconds.

**What users see:** The health badge shows `Server waking up... (Xs)` and counts down. Once the server is live, the badge updates and the upload form becomes usable.

**How to eliminate cold starts:**
- Upgrade to Render's **Starter plan** ($7/month) — always-on
- Or use **Railway** (free tier with no sleep, limited compute credits)

### 500MB Storage Limit

Render's free tier has limited ephemeral disk. The `cache/` directory in the project stores analysis cache files. These don't persist across deploys (ephemeral filesystem), so they reset on each deploy — this is fine for correctness.

---

## Running Locally (After This Update)

The app now works via uvicorn (not by opening `index.html` directly):

```bash
cd "c:\Users\mohdf\mini project\MAIN_PROJECT"
# Activate venv first
.\venv\Scripts\activate     # Windows
source venv/bin/activate    # Mac/Linux

# Start the server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Open in browser
# http://localhost:8000
```

> 📝 **Note:** Opening `frontend/index.html` directly as a file still works too — `app.js` detects the `file://` protocol and falls back to `http://127.0.0.1:8000` automatically.

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_KEY_1` | ✅ Yes | — | Primary Gemini API key |
| `GEMINI_KEY_2` – `GEMINI_KEY_5` | Optional | — | Rotation keys for higher throughput |
| `GEMINI_MODEL` | Optional | `gemini-2.5-flash` | Gemini model to use |
| `COMPRESSION_MODE` | Optional | `light` | Text compression: `off`, `light`, `aggressive` |
| `CACHE_ENABLED` | Optional | `true` | Cache analysis results by paper hash |
| `CONTACT_EMAIL` | Optional | — | Displayed in error messages |

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Frontend loads but API calls fail | Wrong `BACKEND_URL` | Verify `window.location.origin` matches the Render URL |
| "System: Offline" badge | Server still starting or keys missing | Wait 60s, or check Render logs → Environment tab |
| 503 on `/analyze` | All Gemini keys hit rate limit | Add more API keys, or wait for quota reset (midnight Pacific) |
| PDF download fails | Temporary file cleanup issue | Usually transient — retry the analysis |
| Build fails on Render | Dependency mismatch | Check `requirements.txt` versions, check Render build logs |
