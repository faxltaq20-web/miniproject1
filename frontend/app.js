/* -------------------------------------------------------------
   RESEARCHSENSE CLIENT ORCHESTRATION & API CONNECTIONS (JS)
   ------------------------------------------------------------- */

// Backend URL: always the current origin. Electron and web deploys both load
// the frontend via FastAPI, so origin resolution is unambiguous.
const BACKEND_URL = window.location.origin;

// ── Electron Custom Titlebar ────────────────────────────────
(function initTitlebar() {
    if (!window.electronAPI) return; // not in Electron — skip
    const controls = document.getElementById('titlebarControls');
    if (controls) controls.style.display = 'flex';

    const btnMin   = document.getElementById('tbMin');
    const btnMax   = document.getElementById('tbMax');
    const btnClose = document.getElementById('tbClose');

    if (btnMin)   btnMin.addEventListener('click',   () => window.electronAPI.minimize());
    if (btnMax)   btnMax.addEventListener('click',   () => window.electronAPI.maximize());
    if (btnClose) btnClose.addEventListener('click', () => window.electronAPI.close());
})();


// Discipline weights come from the /analyze response as `layer_max_marks`
// (already rounded ints in Python — no drift risk). This fallback only
// applies to the offline demo mode, which explicitly uses CS weights.
const DEFAULT_MAX_MARKS = {
    structure_sections: 20,
    clarity_writing:    22,
    methodology_rigor:  22,
    evidence_claims:    20,
    citations:          15,
};


// Flatten FastAPI/HTTPException error payloads into a single readable line.
// Handles: {error, message}, {detail: "str"}, {detail: {error, message}},
// {detail: [{msg, loc}]} (Pydantic validation errors), or unknown shapes.
function extractErrorMessage(payload) {
    if (!payload || typeof payload !== "object") return "";
    if (typeof payload.error === "string") return payload.error;
    if (typeof payload.message === "string") return payload.message;
    const d = payload.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d.length) {
        return d.map(x => x?.msg || x?.message || JSON.stringify(x)).join("; ");
    }
    if (d && typeof d === "object") {
        return d.message || d.error || JSON.stringify(d);
    }
    return "";
}

// Global storage for current paper's analysis response
let currentAnalysisData = null;

// Views Mapping
const views = {
    upload: document.getElementById("uploadView"),
    dashboard: document.getElementById("dashboardView")
};

function showView(viewName) {
    Object.entries(views).forEach(([k, el]) => {
        if (k === viewName) {
            el.classList.add("active");
        } else {
            el.classList.remove("active");
        }
    });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    checkBackendHealth();
    setupDropZone();
});

// -------------------------------------------------------------
// 1. Pre-Flight Diagnostics Check (GET /health) — with cold-start polling
// -------------------------------------------------------------
async function checkBackendHealth() {
    const badge = document.getElementById("diagnosticsBadge");
    const text = document.getElementById("diagnosticsText");
    const dot = badge.querySelector(".status-dot");

    const MAX_WAIT_MS = 60000;   // 60s max (Render free-tier cold start)
    const POLL_INTERVAL = 3000;  // retry every 3s
    const startTime = Date.now();
    let attempt = 0;

    while (Date.now() - startTime < MAX_WAIT_MS) {
        attempt++;
        try {
            const response = await fetch(`${BACKEND_URL}/health`, {
                method: "GET",
                signal: AbortSignal.timeout(5000)   // 5s per attempt
            });

            if (response.ok) {
                const health = await response.json();
                if (health.status === "healthy") {
                    dot.className = "status-dot healthy";
                    text.textContent = "System: Healthy";
                    badge.style.borderColor = "rgba(16, 185, 129, 0.3)";
                } else {
                    dot.className = "status-dot degraded";
                    text.textContent = "System: Degraded — some services unavailable";
                    badge.style.borderColor = "rgba(245, 158, 11, 0.3)";
                }
                return;   // success — stop polling
            }
        } catch (_) {
            // Network error or timeout — server still waking
        }

        // Still waking — update badge with countdown
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        const remaining = Math.max(0, 60 - elapsed);
        dot.className = "status-dot animate-pulse";
        text.textContent = `Server waking up... (${remaining}s)`;
        badge.style.borderColor = "rgba(139, 92, 246, 0.3)";

        await new Promise(r => setTimeout(r, POLL_INTERVAL));
    }

    // Timed out after 60s
    dot.className = "status-dot error";
    text.textContent = "System: Offline — server unreachable";
    badge.style.borderColor = "rgba(239, 68, 68, 0.3)";
}


// -------------------------------------------------------------
// 2. Drag & Drop Upload Zone Setup
// -------------------------------------------------------------
function setupDropZone() {
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");

    // Standard Drag events
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        }, false);
    });

    // File drop handler
    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleUploadedFile(file);
    });

    // Dropzone click triggers input click
    dropZone.addEventListener("click", () => {
        // Only trigger explorer search if stepper isn't running
        if (document.getElementById("stepperContainer").style.display !== "block") {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        handleUploadedFile(file);
    });
}

// PDF file extension validation
function handleUploadedFile(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        showToastNotification("❌ Rejection: Only PDF documents are accepted.");
        return;
    }

    // PDF is valid, trigger backend pipeline upload
    runLivePaperAnalysis(file);
}

// -------------------------------------------------------------
// 3. Custom Slide-in Toast Notifications
//    - Queued so back-to-back calls don't clobber each other
//    - Manually dismissible via the × button (or auto-dismiss after 4s)
// -------------------------------------------------------------
const _toastQueue = [];
let _toastActive = false;
let _toastTimer = null;

function _renderNextToast() {
    if (_toastActive || _toastQueue.length === 0) return;
    const { message, isSuccess } = _toastQueue.shift();
    const toast = document.getElementById("toastNotification");
    const icon = document.getElementById("toastIcon");
    const msg = document.getElementById("toastMsg");

    icon.textContent = isSuccess ? "✅" : "❌";
    toast.style.borderLeftColor = isSuccess ? "var(--accent-success)" : "var(--accent-danger)";
    msg.textContent = message;

    _toastActive = true;
    toast.classList.add("show");

    _toastTimer = setTimeout(_dismissToast, 4000);
}

function _dismissToast() {
    const toast = document.getElementById("toastNotification");
    toast.classList.remove("show");
    if (_toastTimer) { clearTimeout(_toastTimer); _toastTimer = null; }
    // Wait for slide-out transition (0.4s) before showing the next one
    setTimeout(() => {
        _toastActive = false;
        _renderNextToast();
    }, 450);
}

function showToastNotification(message, isSuccess = false) {
    _toastQueue.push({ message, isSuccess });
    _renderNextToast();
}

// Wire the close button once at load
document.addEventListener("DOMContentLoaded", () => {
    const closeBtn = document.getElementById("toastClose");
    if (closeBtn) closeBtn.addEventListener("click", _dismissToast);
});

// -------------------------------------------------------------
// 4. Stepper Progress Stage Controller
// -------------------------------------------------------------
function resetStepper() {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step${i}`);
        el.className = "step pending";
        el.querySelector(".step-icon").textContent = "○";
    }
}

function updateStepStatus(stepNum, status) {
    const el = document.getElementById(`step${stepNum}`);
    const icon = el.querySelector(".step-icon");

    if (status === "active") {
        el.className = "step active";
        icon.className = "step-icon pulse";
        icon.textContent = "●";
    } else if (status === "done") {
        el.className = "step done";
        icon.className = "step-icon";
        icon.textContent = "✓";
    } else {
        el.className = "step pending";
        icon.className = "step-icon";
        icon.textContent = "○";
    }
}

// Simulate loader timeline sequence
function runFakeStepperSequence(callback) {
    document.getElementById("stepperContainer").style.display = "block";
    document.getElementById("dropZone").style.display = "none";
    document.getElementById("demoBtn").style.pointerEvents = "none";
    document.getElementById("demoBtn").style.opacity = "0.5";
    resetStepper();

    let step = 1;
    updateStepStatus(1, "active");

    const timer = setInterval(() => {
        updateStepStatus(step, "done");
        step++;
        if (step <= 5) {
            updateStepStatus(step, "active");
        } else {
            clearInterval(timer);
            setTimeout(() => {
                document.getElementById("stepperContainer").style.display = "none";
                document.getElementById("dropZone").style.display = "block";
                document.getElementById("demoBtn").style.pointerEvents = "auto";
                document.getElementById("demoBtn").style.opacity = "1";
                callback();
            }, 500);
        }
    }, 1200);
}

// -------------------------------------------------------------
// 5. Live Paper Analysis Request (POST /analyze)
// -------------------------------------------------------------
async function runLivePaperAnalysis(file) {
    document.getElementById("stepperContainer").style.display = "block";
    document.getElementById("dropZone").style.display = "none";
    document.getElementById("demoBtn").style.pointerEvents = "none";
    document.getElementById("demoBtn").style.opacity = "0.5";
    resetStepper();

    // Stage 1 active: Document Extraction
    updateStepStatus(1, "active");

    const formData = new FormData();
    formData.append("file", file);

    // Dynamic progression estimator during API roundtrips
    let simulatedStep = 1;
    const progressTimer = setInterval(() => {
        if (simulatedStep < 4) {
            updateStepStatus(simulatedStep, "done");
            simulatedStep++;
            updateStepStatus(simulatedStep, "active");
        }
    }, 4500); // estimated inter-stage timing

    try {
        const response = await fetch(`${BACKEND_URL}/analyze`, {
            method: "POST",
            body: formData
        });

        clearInterval(progressTimer);

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(extractErrorMessage(err) || `Analysis failed (HTTP ${response.status})`);
        }

        const data = await response.json();
        
        // Complete remaining stepper quickly
        for (let i = simulatedStep; i <= 4; i++) {
            updateStepStatus(i, "done");
        }
        updateStepStatus(5, "active");

        setTimeout(() => {
            updateStepStatus(5, "done");
            setTimeout(() => {
                // Done! Clean up view and transition
                document.getElementById("stepperContainer").style.display = "none";
                document.getElementById("dropZone").style.display = "block";
                document.getElementById("demoBtn").style.pointerEvents = "auto";
                document.getElementById("demoBtn").style.opacity = "1";

                currentAnalysisData = data;
                populateDashboardView(data);
                showView("dashboard");
                showToastNotification("Analysis generated successfully!", true);
            }, 400);
        }, 800);

    } catch (e) {
        clearInterval(progressTimer);
        document.getElementById("stepperContainer").style.display = "none";
        document.getElementById("dropZone").style.display = "block";
        document.getElementById("demoBtn").style.pointerEvents = "auto";
        document.getElementById("demoBtn").style.opacity = "1";
        showToastNotification(e.message || "Uplink analysis failed. Server offline.");
    }
}

// Score counter ticker — counts from 0 to targetScore over ~1.8s
function animateScore(targetScore) {
    const el = document.getElementById("gaugeScoreText");
    if (!el) return;
    let count = 0;
    const steps = Math.max(Math.round(targetScore), 1);
    const stepDuration = 1800 / steps;
    const timer = setInterval(() => {
        count++;
        el.textContent = count;
        if (count >= steps) {
            el.textContent = Math.round(targetScore);
            clearInterval(timer);
        }
    }, stepDuration);
}

// -------------------------------------------------------------
// 6. Data Binding & Dynamic Rendering Logic
// -------------------------------------------------------------
function populateDashboardView(data) {
    // 1. Filename
    document.getElementById("analyzedFilename").textContent = data.filename;

    // 2. Score SVGs Gauge
    const targetScore = Math.round(data.final_score);
    animateScore(data.final_score);  // ticker animation: 0 → score
    
    // Animate SVG Gauge arc
    const circumference = 2 * Math.PI * 80; // ≈ 502.6
    const offset = circumference * (1 - targetScore / 100);
    const circle = document.getElementById("gaugeCircle");
    
    circle.style.transition = "stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)";
    circle.style.strokeDashoffset = offset;

    // Grade and Badge thematic colors
    const badge = document.getElementById("gradeBadge");
    const rec = document.getElementById("recBadge");
    badge.textContent = data.grade;

    // Grade-letter-based recommendation mapping. Grade badge color/gradient
    // is fully driven by the `.grade-{a..f}` CSS class — no inline overrides.
    // Recommendation pill still needs inline color since it has no dedicated CSS.
    const gradeLetter = data.grade ? data.grade.charAt(0).toUpperCase() : "F";
    const recStyles = {
        A: { color: "var(--accent-success)", bg: "rgba(16, 185, 129, 0.12)", text: "RECOMMENDED FOR JOURNAL SUBMISSION" },
        B: { color: "var(--accent-success)", bg: "rgba(16, 185, 129, 0.12)", text: "RECOMMENDED FOR JOURNAL SUBMISSION" },
        C: { color: "var(--accent-warning)", bg: "rgba(245, 158, 11, 0.12)", text: "MINOR REVISIONS REQUIRED" },
        D: { color: "var(--accent-danger)",  bg: "rgba(239, 68, 68, 0.12)",  text: "SIGNIFICANT REVISIONS REQUIRED" },
    };
    const s = recStyles[gradeLetter] || { color: "var(--accent-danger)", bg: "rgba(239, 68, 68, 0.12)", text: "NOT READY FOR SUBMISSION" };
    rec.style.color = s.color;
    rec.style.backgroundColor = s.bg;
    rec.textContent = s.text;

    // Grade badge class for CSS color-coding
    badge.classList.remove("grade-a", "grade-b", "grade-c", "grade-d", "grade-f");
    badge.classList.add(`grade-${gradeLetter.toLowerCase()}`);

    // Score-range gauge stroke color (independent of grade badge)
    let gaugeStrokeColor;
    if (targetScore >= 85) {
        gaugeStrokeColor = "#10B981";   // emerald
    } else if (targetScore >= 70) {
        gaugeStrokeColor = "#06b6d4";   // cyan
    } else if (targetScore >= 55) {
        gaugeStrokeColor = "#F59E0B";   // amber
    } else {
        gaugeStrokeColor = "#EF4444";   // red
    }
    circle.style.stroke = gaugeStrokeColor;

    // 3. Section Detection Pills
    const sectionContainer = document.getElementById("sectionPills");
    sectionContainer.innerHTML = "";
    
    const standardSections = ["Abstract", "Introduction", "Related Work", "Methods", "Results", "Discussion", "Conclusion", "References"];
    
    standardSections.forEach(sec => {
        const pill = document.createElement("div");
        const detectedVal = data.detected_sections[sec];
        const isPresent = detectedVal !== undefined && detectedVal > 0;
        
        pill.className = `section-pill ${isPresent ? "present" : "missing"}`;
        
        const nameSpan = document.createElement("span");
        nameSpan.className = "pill-name";
        nameSpan.textContent = sec;
        
        const valSpan = document.createElement("span");
        valSpan.className = "pill-val font-mono";
        valSpan.textContent = isPresent ? `${detectedVal}%` : "Missing";
        if (!isPresent) valSpan.style.color = "var(--accent-danger)";

        pill.appendChild(nameSpan);
        pill.appendChild(valSpan);
        sectionContainer.appendChild(pill);
    });

    // 4. Multi-Layer Accordion Review List
    const accordionContainer = document.getElementById("layerAccordionList");
    accordionContainer.innerHTML = "";

    const activeLayers = [
        { key: "structure_sections", label: "Structure & Sections", num: "01" },
        { key: "clarity_writing",    label: "Clarity & Writing",    num: "02" },
        { key: "methodology_rigor",  label: "Methodology Rigor",    num: "03" },
        { key: "evidence_claims",    label: "Evidence & Claims",    num: "04" },
        { key: "citations",          label: "Citations & References", num: "05" }
    ];

    activeLayers.forEach(layer => {
        const detail = data.layer_details[layer.key] || { score: 0.0, issues: [], suggestions: [] };

        const card = document.createElement("div");
        card.className = "layer-card";
        card.setAttribute("role", "button");
        card.setAttribute("tabindex", "0");
        card.setAttribute("aria-expanded", "false");
        card.setAttribute("aria-label", `${layer.label} — expand to view issues and recommendations`);

        // Expand/Collapse — click and keyboard (Enter/Space)
        const toggleCard = () => {
            const opened = card.classList.toggle("open");
            card.setAttribute("aria-expanded", String(opened));
        };
        card.addEventListener("click", toggleCard);
        card.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                toggleCard();
            }
        });

        // Authoritative max marks come from the /analyze response so JS never
        // needs to replicate Python's discipline weight math.
        const max_m = (data.layer_max_marks && data.layer_max_marks[layer.key] !== undefined)
            ? data.layer_max_marks[layer.key]
            : (DEFAULT_MAX_MARKS[layer.key] || 20);
        const rawScore = detail.score || 0.0;
        const earned = Math.round((rawScore * max_m) / 10);

        // Layer thematic color by score percentage (consistent with report_generator _bar_color)
        const pct = rawScore / 10;
        let layerColor = "var(--accent-danger)";
        if (pct >= 0.80) layerColor = "var(--accent-success)";
        else if (pct >= 0.60) layerColor = "var(--accent-warning)";

        // Card Header
        const header = document.createElement("div");
        header.className = "layer-header";
        
        const titleBlock = document.createElement("div");
        titleBlock.className = "layer-title-block";
        
        const numSpan = document.createElement("span");
        numSpan.className = "layer-num";
        numSpan.textContent = layer.num;
        
        const titleSpan = document.createElement("span");
        titleSpan.className = "layer-title";
        titleSpan.textContent = layer.label;

        titleBlock.appendChild(numSpan);
        titleBlock.appendChild(titleSpan);

        const metaBlock = document.createElement("div");
        metaBlock.className = "layer-meta-block";

        const weightSpan = document.createElement("span");
        weightSpan.className = "layer-weight";
        weightSpan.textContent = `${max_m}%`;
        
        const scoreSpan = document.createElement("span");
        scoreSpan.className = "layer-score font-mono";
        scoreSpan.style.color = layerColor;
        scoreSpan.textContent = `${earned} / ${max_m}`;
        
        const chevron = document.createElement("span");
        chevron.className = "layer-chevron";
        chevron.textContent = "›";

        metaBlock.appendChild(weightSpan);
        metaBlock.appendChild(scoreSpan);
        metaBlock.appendChild(chevron);

        header.appendChild(titleBlock);
        header.appendChild(metaBlock);

        // Card Body
        const body = document.createElement("div");
        body.className = "layer-body";
        
        // Prevent click inside body collapsing the card
        body.addEventListener("click", (e) => {
            e.stopPropagation();
        });

        const splitDiv = document.createElement("div");
        splitDiv.className = "layer-content-split";

        // Left Column (Issues)
        const leftCol = document.createElement("div");
        const issuesTitle = document.createElement("div");
        issuesTitle.className = "detail-section-title";
        issuesTitle.textContent = "Issues Detected";
        leftCol.appendChild(issuesTitle);

        const issuesList = document.createElement("ul");
        issuesList.className = "detail-list";
        
        if (detail.issues.length === 0) {
            const item = document.createElement("li");
            item.className = "detail-item";
            item.innerHTML = `<span class="detail-item-tag success">OK</span><span class="detail-text">No issues detected. Excellent quality.</span>`;
            issuesList.appendChild(item);
        } else {
            detail.issues.forEach(iss => {
                const item = document.createElement("li");
                item.className = "detail-item";
                item.innerHTML = `<span class="detail-item-tag danger">Issue</span><span class="detail-text">${iss}</span>`;
                issuesList.appendChild(item);
            });
        }
        leftCol.appendChild(issuesList);

        // Right Column (Suggestions)
        const rightCol = document.createElement("div");
        const sugTitle = document.createElement("div");
        sugTitle.className = "detail-section-title";
        sugTitle.textContent = "Actionable Recommendations";
        rightCol.appendChild(sugTitle);

        const sugList = document.createElement("ul");
        sugList.className = "detail-list";
        
        if (detail.suggestions.length === 0) {
            const item = document.createElement("li");
            item.className = "detail-item";
            item.innerHTML = `<span class="detail-item-tag success">OK</span><span class="detail-text">No recommendations required.</span>`;
            sugList.appendChild(item);
        } else {
            detail.suggestions.forEach(sug => {
                const item = document.createElement("li");
                item.className = "detail-item";
                item.innerHTML = `<span class="detail-item-tag success">Fix</span><span class="detail-text">${sug}</span>`;
                sugList.appendChild(item);
            });
        }
        rightCol.appendChild(sugList);

        splitDiv.appendChild(leftCol);
        splitDiv.appendChild(rightCol);

        // layer-body-inner required for CSS grid-rows accordion animation
        const bodyInner = document.createElement("div");
        bodyInner.className = "layer-body-inner";
        bodyInner.appendChild(splitDiv);
        body.appendChild(bodyInner);

        card.appendChild(header);
        card.appendChild(body);
        accordionContainer.appendChild(card);
    });

    // 5. Verdict Paragraph
    const verdict = data.verdict_text || data.layer_details?.verdict || "No feedback generated.";
    document.getElementById("qualitativeVerdictText").textContent = verdict;

    // 6. Citations & References Panel
    const cr = data.citation_result || { total_refs: 0, verified: 0, not_found: 0, unreachable: 0, flagged_dois: [], flagged_items: [] };
    
    document.getElementById("citeTotal").textContent = cr.total_refs;
    document.getElementById("citeVerified").textContent = cr.verified;
    document.getElementById("citeUnverified").textContent = cr.not_found + cr.unreachable;

    // Progress percentage rate math
    const rate = cr.total_refs > 0 ? Math.round((cr.verified / cr.total_refs) * 100) : 0;
    document.getElementById("verificationRatePct").textContent = `${rate}%`;
    document.getElementById("verificationProgressBar").style.width = `${rate}%`;

    // 7. Dynamic Reference Entries Table Body
    const tableBody = document.getElementById("referenceTableBody");
    tableBody.innerHTML = "";

    // Generate table entries dynamically
    if (cr.flagged_items.length === 0 && cr.total_refs === 0) {
        tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No references parsed in bibliography.</td></tr>`;
    } else {
        // To construct a comprehensive references table we iterate over the flagged items, 
        // as well as mock verified papers to fill the remaining list details
        
        // Loop over flagged duplicate reference arrays
        cr.flagged_items.forEach(item => {
            const row = document.createElement("tr");
            
            // Col 1: Name details
            const col1 = document.createElement("td");
            col1.className = "ref-citation-entry";
            col1.textContent = item.citation;
            row.appendChild(col1);

            // Col 2: Method
            const col2 = document.createElement("td");
            col2.className = "font-mono";
            col2.textContent = "Regex Index";
            row.appendChild(col2);

            // Col 3: Status badging
            const col3 = document.createElement("td");
            col3.innerHTML = `<span class="ref-badge warning">DUPLICATE</span>`;
            row.appendChild(col3);

            // Col 4: Impact details
            const col4 = document.createElement("td");
            col4.textContent = item.detail || "Duplicate bibliography item detected.";
            row.appendChild(col4);

            tableBody.appendChild(row);
        });

        // Loop over unreachable or invalid DOIs
        cr.flagged_dois.forEach(doi => {
            const row = document.createElement("tr");

            // Col 1: Name details
            const col1 = document.createElement("td");
            col1.className = "ref-citation-entry font-mono";
            col1.textContent = doi;
            row.appendChild(col1);

            // Col 2: Method
            const col2 = document.createElement("td");
            col2.className = "font-mono";
            col2.textContent = "CrossRef API";
            row.appendChild(col2);

            // Col 3: Status badging — flagged_dois only contains DOIs that
            // returned no CrossRef record after successful query
            const col3 = document.createElement("td");
            col3.innerHTML = `<span class="ref-badge danger">NOT FOUND</span>`;
            row.appendChild(col3);

            // Col 4: Impact details
            const col4 = document.createElement("td");
            col4.textContent = "CrossRef returned no record for this DOI.";
            row.appendChild(col4);

            tableBody.appendChild(row);
        });

        // Surface unreachable count so the summary number isn't unexplained.
        if (cr.unreachable > 0) {
            const row = document.createElement("tr");
            const col1 = document.createElement("td");
            col1.className = "ref-citation-entry";
            col1.textContent = `${cr.unreachable} citation${cr.unreachable > 1 ? "s" : ""} unreachable`;
            row.appendChild(col1);
            const col2 = document.createElement("td");
            col2.className = "font-mono";
            col2.textContent = "CrossRef / Semantic Scholar";
            row.appendChild(col2);
            const col3 = document.createElement("td");
            col3.innerHTML = `<span class="ref-badge warning">UNREACHABLE</span>`;
            row.appendChild(col3);
            const col4 = document.createElement("td");
            col4.textContent = "Verification service timed out or errored — status unknown.";
            row.appendChild(col4);
            tableBody.appendChild(row);
        }

        // Show verified count as summary row (real API data)
        if (cr.verified > 0) {
            const row = document.createElement("tr");
            row.className = "ref-row";

            const col1 = document.createElement("td");
            col1.className = "ref-citation-entry";
            col1.innerHTML = `<div class="tooltip">${cr.verified} citation${cr.verified > 1 ? "s" : ""} verified<span class="tooltiptext">Verified against Semantic Scholar title index and CrossRef DOI registry.</span></div>`;
            row.appendChild(col1);

            const col2 = document.createElement("td");
            col2.className = "font-mono";
            col2.textContent = "Semantic Scholar";
            row.appendChild(col2);

            const col3 = document.createElement("td");
            col3.innerHTML = `<span class="ref-badge success">VERIFIED</span>`;
            row.appendChild(col3);

            const col4 = document.createElement("td");
            col4.textContent = `${cr.verified} citation${cr.verified > 1 ? "s" : ""} successfully matched in reference libraries.`;
            row.appendChild(col4);

            tableBody.appendChild(row);
        }
    }

    // Quota-exhausted heuristic: final score is 0 AND every Gemini-driven
    // layer (i.e. non-citation) is also 0. A legitimately bad paper still
    // varies per layer, so we shouldn't cry "quota" for real zero scores.
    const geminiLayerKeys = ["structure_sections", "clarity_writing", "methodology_rigor", "evidence_claims"];
    const allGeminiZero = geminiLayerKeys.every(k => (data.layer_scores?.[k] ?? 0) === 0);
    if (data.final_score === 0.0 && allGeminiZero) {
        showToastNotification("⚠ All Gemini layers returned 0 — API quota may be exhausted. Try the sample demo.", false);
    }
}

// -------------------------------------------------------------
// 7. PDF Report Download Action (POST /report)
// -------------------------------------------------------------
async function triggerPdfDownload() {
    if (!currentAnalysisData) {
        showToastNotification("No active analysis payload located.");
        return;
    }

    const downloadBtn = document.getElementById("downloadPdfBtn");
    const originalText = downloadBtn.innerHTML;
    
    downloadBtn.innerHTML = "📥 Compiling in-memory PDF...";
    downloadBtn.disabled = true;

    try {
        const response = await fetch(`${BACKEND_URL}/report`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(currentAnalysisData)
        });

        if (!response.ok) throw new Error("PDF compilation trigger failed.");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        
        const safeName = currentAnalysisData.filename.replace(".pdf", "");
        a.download = `${safeName}_report.pdf`;
        
        document.body.appendChild(a);
        a.click();
        
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToastNotification("PDF report download completed!", true);
    } catch (e) {
        showToastNotification(e.message || "Failed generating binary PDF report.");
    } finally {
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
}

// -------------------------------------------------------------
// 8. Offline try-sample demo bindings
// -------------------------------------------------------------
function triggerDemoMode() {
    // Offline pre-cached JSON payload
    const mockPayload = {
        "filename": "attention_is_all_you_need_sample.pdf",
        "detected_sections": {
            "Abstract": 98,
            "Introduction": 95,
            "Related Work": 94,
            "Methods": 90,
            "Results": 92,
            "Discussion": 0,
            "Conclusion": 88,
            "References": 99
        },
        "section_count": 7,
        "warnings": ["discussion"],
        "layer_scores": {
            "structure_sections": 8.5,
            "clarity_writing": 8.0,
            "methodology_rigor": 7.0,
            "evidence_claims": 7.5,
            "citations": 7.0
        },
        "layer_details": {
            "structure_sections": {
                "score": 8.5,
                "issues": [
                    "Missing a dedicated Discussion section (material merged with Results).",
                    "Keyword sequence is placed below Abstract without dividers."
                ],
                "suggestions": [
                    "Decouple Results and Discussion into separate structural headers to conform to strict academic templates.",
                    "Format keyword section with explicit spacing rules."
                ]
            },
            "clarity_writing": {
                "score": 8.0,
                "issues": [
                    "Passive phrasing density is slightly elevated on page 3.",
                    "Jargon density in Section 3 makes reading difficult."
                ],
                "suggestions": [
                    "Convert passive sentences in Methods to active subject-verb sequences.",
                    "Add inline parenthetical definitions for niche vocabulary terms."
                ]
            },
            "methodology_rigor": {
                "score": 7.0,
                "issues": [
                    "Optimizer hyperparameter values are declared without theoretical justification.",
                    "No control benchmark metrics described."
                ],
                "suggestions": [
                    "Add details explaining why specific learning rates and weights decay criteria were selected.",
                    "Provide a baseline reference benchmark comparison table."
                ]
            },
            "evidence_claims": {
                "score": 7.5,
                "issues": [
                    "Generalization capabilities are claimed beyond the tested translation dataset size.",
                    "Chart axes on Figure 2 lack labeled scale units."
                ],
                "suggestions": [
                    "Qualify accuracy claims by stating bounds and scope clearly.",
                    "Re-label Figure 2 with clear coordinate scale keys."
                ]
            },
            "citations": {
                "score": 7.0,
                "issues": [
                    "No direct DOI matches located in bibliography (standard numbered bibliography formatting).",
                    "Duplicate reference parsed in citation index."
                ],
                "suggestions": [
                    "Append active DOI URL strings to the bibliography entries.",
                    "Remove duplicate record from page 8 references list."
                ]
            },
            "verdict": "The research paper presents a groundbreaking, highly structured contribution. The writing quality is robust, utilizing precise mathematical modeling. The methodology is exceptionally reproducible. The only noteworthy items include minor formatting mismatches, duplicate reference entries, and slightly overreaching generalization claims. Excellent work overall."
        },
        "final_score": 77.0,
        "grade": "B — Good",
        "discipline": "computer_science",
        "layer_max_marks": {
            "structure_sections": 20,
            "clarity_writing":    22,
            "methodology_rigor":  22,
            "evidence_claims":    20,
            "citations":          15
        },
        "citation_result": {
            "total_refs": 8,
            "verified": 6,
            "not_found": 1,
            "unreachable": 1,
            "flagged_dois": ["10.1145/fake-doi-1"],
            "flagged_items": [
                {
                    "citation": "Vaswani et al., 2017, Attention Is All You Need",
                    "category": "duplicate",
                    "detail": "Duplicate citation parsed in references list."
                }
            ]
        }
    };

    // Run the stepper checklist for 6 seconds to show the animation, then load mock results
    runFakeStepperSequence(() => {
        currentAnalysisData = mockPayload;
        populateDashboardView(mockPayload);
        showView("dashboard");
        showToastNotification("Pre-cached sample paper loaded successfully!", true);
    });
}

function resetUploadView() {
    showView("upload");
    currentAnalysisData = null;
}
