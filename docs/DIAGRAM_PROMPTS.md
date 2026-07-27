# ResearchSense — Diagram Prompts & Mermaid Schemas

This document compiles structured diagram descriptions, text-to-image prompts (for Midjourney/DALL-E), and copy-paste **Mermaid.js** code blocks for all main modules and workflow components of the ResearchSense project. You can copy these directly into other AI agents or diagram tools.

---

## Table of Contents

1. [Global System Architecture](#1-global-system-architecture)
2. [End-to-End Analysis Workflow](#2-end-to-end-analysis-workflow)
3. [main.py — FastAPI Orchestrator](#3-mainpy--fastapi-orchestrator)
4. [pdf_parser.py — Document Text Extraction](#4-pdf_parserpy--document-text-extraction)
5. [section_detector.py — Two-Tier Structural Parser](#5-section_detectorpy--two-tier-structural-parser)
6. [text_compressor.py — Text & Prompt Compression](#6-text_compressorpy--text--prompt-compression)
7. [gemini_analyzer.py — AI Evaluation & Key Rotation](#7-gemini_analyzerpy--ai-evaluation--key-rotation)
8. [scoring.py — Adaptive Scoring Matrix](#8-scoringpy--adaptive-scoring-matrix)
9. [citation_checker.py — Reference Telemetry & Validation](#9-citation_checkerpy--reference-telemetry--validation)
10. [report_generator.py — ReportLab PDF Engine](#10-report_generatorpy--reportlab-pdf-engine)
11. [app.js — Frontend SPA State Controller](#11-appjs--frontend-spa-state-controller)
12. [electron/main.js — Desktop Process Bootloader](#12-electronmainjs--desktop-process-bootloader)

---

## 1. Global System Architecture

* **Diagram Type:** High-level component flowchart
* **AI Image Gen Prompt:** 
  > A clean, modern enterprise software architecture diagram. Flat 2D vector style, minimal blue and dark slate grey color palette. Shows three distinct layers side-by-side: Client UI (Browser and Electron wrappers), Backend API Service (FastAPI), and External Services (Google Gemini API, CrossRef REST API, Semantic Scholar API, and ArXiv Atom API). Labeled boxes with connecting directional arrows showing JSON data paths. Clean typography, high contrast, professional, sans-serif, transparent background.
* **Mermaid Code:**
```mermaid
flowchart LR
    subgraph Client ["Client Side (UI)"]
        Browser[Web Browser SPA]
        Electron[Electron Desktop Shell]
        Browser --- Electron
    end

    subgraph Backend ["FastAPI Backend (main.py)"]
        Routes{API Router}
        Static[StaticFiles mount]
        Routes --- Static
    end

    subgraph Core ["Processing Modules"]
        Parser[pdf_parser.py]
        Segment[section_detector.py]
        Compress[text_compressor.py]
        Analyzer[gemini_analyzer.py]
        CitCheck[citation_checker.py]
        Scorer[scoring.py]
        Report[report_generator.py]
    end

    subgraph External ["External Services"]
        Gemini[Gemini 2.5 Flash]
        CrossRef[CrossRef REST API]
        SScholar[Semantic Scholar API]
        ArXiv[ArXiv Atom API]
    end

    Client -->|1. Upload PDF / POST /analyze| Routes
    Routes --> Parser
    Parser --> Segment
    Segment --> Compress
    Compress --> Analyzer & CitCheck
    Analyzer --> Gemini
    CitCheck --> CrossRef & SScholar & ArXiv
    Analyzer & CitCheck --> Scorer
    Scorer --> Routes
    Routes -->|2. Return Dashboard JSON| Client
    Client -->|3. POST /report| Routes
    Routes --> Report
    Report -->|4. Stream BytesIO PDF| Client
```

---

## 2. End-to-End Analysis Workflow

* **Diagram Type:** Sequence Diagram
* **AI Image Gen Prompt:**
  > A professional sequence diagram showing end-to-end message flows for a file analysis application. 2D vector illustration with a dark blue and teal theme. Vertical swimlanes representing User, Browser UI, FastAPI Backend, PDF Parser, Gemini LLM, and External Citation APIs. Labeled messages with arrows flowing down sequentially from Step 1 (Upload) to final PDF report download. Clear, crisp text, modern UI style.
* **Mermaid Code:**
```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant FE as Frontend Dashboard
    participant API as FastAPI Backend
    participant Pipe as Extraction & Segmenter
    participant LLM as Gemini Analyzer
    participant Cite as Citation Telemetry
    participant Score as Weighted Scorer

    User->>FE: Drop PDF onto dropzone
    FE->>API: POST /analyze (Multipart Upload)
    API->>API: Verify API Keys & File Size Cap
    API->>Pipe: extract_text() & detect_sections()
    Pipe-->>API: sections dict + headings confidence map
    
    par Parallel asyncio.gather()
        API->>LLM: analyze_paper(sections)
        LLM->>LLM: check cache -> call Gemini pool -> calibrate
        LLM-->>API: layer scores, issues, suggestions, discipline
    and Parallel asyncio.gather()
        API->>Cite: check_citations(references_text)
        Cite->>Cite: parallel CrossRef / Semantic Scholar / ArXiv checks
        Cite-->>API: citation score, verified/flagged list
    end

    API->>Score: calculate_score(layer_scores, discipline)
    Score-->>API: final_score, grade_letter
    API->>LLM: generate_verdict(scores) -> verdict_text
    API-->>FE: Return Enriched JSON dashboard response
    FE->>FE: Animate score gauge & render layer accordions
    User->>FE: Click "Download PDF Review"
    FE->>API: POST /report (payload JSON)
    API->>API: report_generator compiles in-memory PDF
    API-->>FE: Return application/pdf stream
    FE->>User: Browser triggers report download
```

---

## 3. main.py — FastAPI Orchestrator

* **Diagram Type:** Flowchart TD
* **AI Image Gen Prompt:**
  > A software routing and flow diagram. Labeled boxes showing FastAPI endpoint logic. Shows entry routes like /health, /analyze, /report, and static mounts. Illustrates check_api_health check guards, size checks, parallel execution paths, and error fallbacks. Teal accents, clean flow lines, transparent background.
* **Mermaid Code:**
```mermaid
flowchart TD
    Start([POST /analyze]) --> HealthCheck{check_api_health}
    HealthCheck -->|Offline| Err503[/503 - API Keys Dead/]
    HealthCheck -->|Online| FormatCheck{Is file extension .pdf?}
    FormatCheck -->|No| Err400[/400 - Reject non-PDF/]
    FormatCheck -->|Yes| Stream[Stream upload to tempfile in 1MB chunks]
    Stream --> SizeCheck{File size > 30MB?}
    SizeCheck -->|Yes| Err413[/413 - Payload Too Large/]
    SizeCheck -->|No| Parse[pdf_parser.extract_text]
    Parse -->|Failure| Err422[/422 - Unprocessable PDF/]
    Parse -->|Success| Segment[section_detector.detect_sections]
    Segment --> Parallel{{"asyncio.gather()"}}
    Parallel -->|Thread 1| LLM[gemini_analyzer.analyze_paper]
    Parallel -->|Thread 2| Cite[citation_checker.check_citations]
    LLM & Cite --> Score[scoring.calculate_score]
    Score --> Verdict[gemini_analyzer.generate_verdict]
    Verdict --> Payload[/Return 200 JSON Payload/]
    Payload --> Finally[finally: delete tempfile]
    Err422 & Err413 & Err400 & Err503 --> Finally
```

---

## 4. pdf_parser.py — Document Text Extraction

* **Diagram Type:** Fallback flowchart
* **AI Image Gen Prompt:**
  > A dual-path software logic flowchart. Clean blue and gray blocks. Left path shows primary parser utilizing pymupdf4llm to convert PDF to Markdown. Center shows check box for character length. Right path shows fallback strategy using fitz plain PyMuPDF text reader with reading-order sorting. Minimalist tech look.
* **Mermaid Code:**
```mermaid
flowchart TD
    A[PDF File Path] --> B{Try pymupdf4llm.to_markdown}
    B -->|Success & chars >= 100| C[Return Structured Markdown text]
    B -->|Throws Exception or chars < 100| D[Fallback: Open via fitz PyMuPDF]
    D --> E[page.get_text with sort=True]
    E --> F{Joined text length >= 100?}
    F -->|Yes| G[Return Plain Text]
    F -->|No| H[Raise ValueError: Scanned/Image PDF]
    
    A --> I[extract_hyperlink_dois]
    I --> J[Walk links page.get_links]
    J --> K[Regex search: 10.xxxx/uri]
    K --> L[Return deduplicated publisher DOIs list]
```

---

## 5. section_detector.py — Two-Tier Structural Parser

* **Diagram Type:** Processing flowchart
* **AI Image Gen Prompt:**
  > A flowchart displaying heading segmentation in documents. Tier 1 shows regex keyword matching scan. Decision diamond labeled "Fewer than 4 sections detected?". Yes path leads to Tier 2 LLM heading mapper querying Gemini. No path goes straight to confidence calculation. Slate grey background, professional engineering design.
* **Mermaid Code:**
```mermaid
flowchart TD
    Start[Document Raw Text] --> T1[Tier 1: heading scan line-by-line]
    T1 --> StopCheck{Is line a Stop Keyword?}
    StopCheck -->|Yes| Stop[Terminate segment accumulation]
    StopCheck -->|No| Compare{Keywords match?}
    Compare -->|Yes| Switch[Switch current section key]
    Compare -->|No| Accumulate[Append line to current section]
    
    Switch & Accumulate --> CheckCount{Total sections detected < 4?}
    CheckCount -->|Yes| T2[Tier 2 fallback: extract heading list]
    T2 --> LLM[gemini_analyzer.map_headings]
    LLM --> Map[Apply LLM mapping to sections]
    Map --> Merge[Merge Tier 1 + Tier 2 keys]
    CheckCount -->|No| Merge
    
    Merge --> Conf[Compute Section Confidence percentages]
    Conf --> End([Return sections dict + detected_sections metrics])
```

---

## 6. text_compressor.py — Text & Prompt Compression

* **Diagram Type:** Linear pipeline
* **AI Image Gen Prompt:**
  > A sequential pipeline diagram showing data compression stages. A text document shrinks as it moves through Stages: Whitespace Cleanup, Citations Stripping, Boilerplate Sentence Removal, and Mathematical Formula removal. Shows methodology section bypassed with a green shield icon. Modern flat 2D style.
* **Mermaid Code:**
```mermaid
flowchart TD
    Input[Sections Dictionary] --> ModeCheck{COMPRESSION_MODE?}
    ModeCheck -->|off| Output[Passthrough - unmodified text]
    ModeCheck -->|light / aggressive| Stage1[Stage 1: Normalize whitespace, strip URLs & Citations]
    Stage1 --> Stage2[Stage 2: Remove duplicated sentences within sections]
    Stage2 --> Stage3[Stage 3: Remove academic filler boilerplate phrases]
    Stage3 --> Shield{Is section results or discussion?}
    Shield -->|Yes| KeepPointers[Shield evidence pointers: Fig. X / Table Y]
    Shield -->|No| StripAll[Strip all boilerplate including pointers]
    KeepPointers & StripAll --> AggrCheck{Aggressive Mode?}
    AggrCheck -->|Yes| Stage4[Stage 4: Strip math notation & formula lines]
    AggrCheck -->|No| Combine
    Stage4 --> Combine[Assemble sections, shield methodology, add stats]
    Combine --> Output
```

---

## 7. gemini_analyzer.py — AI Evaluation & Key Rotation

* **Diagram Type:** Orchestration flowchart
* **AI Image Gen Prompt:**
  > A complex backend server orchestration diagram showing API key rotation and request caching. Illustrated steps: assemble prompts, SHA-256 cache verification, Gemini key validation, rotation on 429 quota exceptions, exponential backoff retries, JSON mapping, and score stretch calibration. Dark navy and cyan scheme.
* **Mermaid Code:**
```mermaid
flowchart TD
    Start[Call analyze_paper] --> Assembly[Assemble compressed text, cap at 400k chars]
    Assembly --> Hash[Generate SHA-256 key from text]
    Hash --> CacheCheck{Cache exists on disk?}
    CacheCheck -->|Yes| CacheHit[Load JSON from cache/ and return]
    CacheCheck -->|No| KeyPool[Start Multi-Key rotation loop]
    
    KeyPool --> TryKey{Try key N}
    TryKey -->|Success| JSONParse[Parse Gemini JSON response]
    TryKey -->|Rate Limit 429 / Exhausted| Rotate[Increment N -> Rotate to next key]
    TryKey -->|Transient Error 503 / overload| Retry{Attempt N count < 3?}
    
    Retry -->|Yes| Wait[Wait with exponential backoff] --> TryKey
    Retry -->|No| Rotate
    Rotate --> TryKey
    
    JSONParse --> Calibrate[Spread raw scores 6-8 by 1.5 center 7.0]
    Calibrate --> CacheSave[Save calibrated JSON to cache/]
    CacheSave --> Output([Return layer_scores and details])
    CacheHit --> Output
```

---

## 8. scoring.py — Adaptive Scoring Matrix

* **Diagram Type:** Weighted calculation flowchart
* **AI Image Gen Prompt:**
  > A data flow math diagram. Inputs of 5 layer scores are mapped to different weight percentages depending on the target academic discipline. Labeled weight values for Computer Science, Math, Medicine, and Humanities, compiling into a unified formula, rounding to a final score and assigning a letter grade pill. Crisp typography.
* **Mermaid Code:**
```mermaid
flowchart TD
    Inputs[5 Layer Scores: 0.0 - 10.0] --> DiscMap{Target Discipline?}
    
    DiscMap -->|Computer Science / other| CS[Str: 20% | Clr: 22.5% | Met: 22.5% | Evid: 20% | Cite: 15%]
    DiscMap -->|Mathematics| Math[Str: 15% | Clr: 15% | Met: 17.5% | Evid: 37.5% | Cite: 15%]
    DiscMap -->|Medicine / Biology| Med[Str: 17.5% | Clr: 15% | Met: 32.5% | Evid: 20% | Cite: 15%]
    DiscMap -->|Humanities / Social| Hum[Str: 17.5% | Clr: 32.5% | Met: 15% | Evid: 20% | Cite: 15%]
    
    CS & Math & Med & Hum --> Sum[Calculate Weighted Sum raw score]
    Sum --> Scale[Scale to 100: final_score = round raw * 10]
    Scale --> GradeCheck{final_score threshold?}
    
    GradeCheck -->|>= 85| A[Grade A - Excellent]
    GradeCheck -->|>= 70| B[Grade B - Good]
    GradeCheck -->|>= 55| C[Grade C - Needs Improvement]
    GradeCheck -->|>= 40| D[Grade D - Poor]
    GradeCheck -->|< 40| F[Grade F - Very Poor]
    
    A & B & C & D & F --> Out([Return final_score + grade_letter])
```

---

## 9. citation_checker.py — Reference Telemetry & Validation

* **Diagram Type:** Validation flowchart
* **AI Image Gen Prompt:**
  > A reference validation flow diagram. Input text split into standard DOI lookups using CrossRef REST API and fuzzy title search queries to Semantic Scholar with a 0.6 similarity limit. Includes recency score tracking and duplicate reference warning flags. Labeled paths, clear metrics, modern engineering design.
* **Mermaid Code:**
```mermaid
flowchart TD
    Start[references_text + hyperlink_dois] --> Empty{Is references empty?}
    Empty -->|Yes| Zero[Return score=0.0]
    Empty -->|No| Year[Detect paper publication year from cover]
    Year --> Extract[Extract DOIs, cap at 20]
    
    Extract --> HasDois{DOIs found?}
    HasDois -->|Yes| CrossRef[Parallel CrossRef API validates DOIs]
    CrossRef --> FallbackSS{Any DOI not found?}
    
    HasDois -->|No| SScholar[Fuzzy Semantic Scholar Title query cap at 5]
    FallbackSS -->|Yes| SScholar
    FallbackSS -->|No| Recency[_score_citation_recency]
    
    SScholar --> Check{Fuzzy match title >= 0.6 / year within 1?}
    Check -->|Yes| MarkVerified[Mark reference verified]
    Check -->|No| MarkFlagged[Mark reference flagged as not found]
    
    MarkVerified & MarkFlagged & CrossRef --> Recency
    Recency --> Dups[Scan first 60 chars for duplicates]
    Dups --> ArXiv[Extract & verify ArXiv preprint IDs]
    ArXiv --> Score[Blend verified ratio + recency + ArXiv boost - penalties]
    Score --> Output([Return citation_result dict])
```

---

## 10. report_generator.py — ReportLab PDF Engine

* **Diagram Type:** Hybrid compiler layout
* **AI Image Gen Prompt:**
  > A visual architecture layout diagram of a PDF document compiler. Displays a dark navy background cover page generated via Canvas callbacks on the left, and a multi-page flowable story builder (ScoreHero, ProgressBars, 2-column parameter scorecards, citation tables, and VerdictCards) compiled by PLATYPUS on the right, saving into an in-memory buffer. Flat vector.
* **Mermaid Code:**
```mermaid
flowchart TD
    Input[Consolidated Analysis JSON] --> Format[Prepare parameters earned / max marks]
    Format --> Buffer[Instantiate in-memory BytesIO buffer]
    Buffer --> Doc[Create BaseDocTemplate]
    
    Doc --> PageTemplate{PageTemplates}
    PageTemplate -->|cover| CoverCallback[draw_cover Canvas callback: full-bleed navy, geometry, top gradients, score circle]
    PageTemplate -->|content| ContentCallback[draw_footer Canvas callback: centered page N]
    
    Doc --> Story[PLATYPUS Flowable Story]
    Story --> S1[ScoreHero: Overall Card]
    Story --> S2[Pill Grid Table: Detected Sections]
    Story --> S3[Parameter Grid Table: _make_param_row side-by-side]
    Story --> S4[PageBreak]
    Story --> S5[Citation stats row + flagged items Table]
    Story --> S6[VerdictCard: summary prose + recommendation pill]
    
    CoverCallback & ContentCallback & S1 & S2 & S3 & S4 & S5 & S6 --> Build[doc.build story]
    Build --> Output[StreamingResponse of application/pdf]
```

---

## 11. app.js — Frontend SPA State Controller

* **Diagram Type:** State machine diagram
* **AI Image Gen Prompt:**
  > A state machine diagram of a web application UI. Transitions from DomContentLoaded starting HealthCheck, landing in UploadIdle dropzone. Analyzing trigger launches simulated progress bar, leading to populated Dashboard displaying gauge SVG arc, accordion chevrons, and downloads. Glassmorphic details, neon accents.
* **Mermaid Code:**
```mermaid
stateDiagram-v2
    [*] --> HealthCheck : DomContentLoaded
    HealthCheck --> UploadIdle : checkBackendHealth updates diagnostics badge
    
    state UploadIdle {
        [*] --> DropZoneArmed
        DropZoneArmed --> FileValidated : dragover glow, drop, check .pdf suffix
    }
    
    UploadIdle --> Analyzing : runLivePaperAnalysis(file)
    UploadIdle --> DemoMode : triggerDemoMode()
    
    state Analyzing {
        [*] --> TimerStart : setInterval updates simulated loading text
        TimerStart --> ApiCall : Fetch POST /analyze
        ApiCall --> ResponseOK : Receive response data
        ResponseOK --> TimerClear : clearInterval
    }
    
    state DemoMode {
        [*] --> SimulatedStepper : 6-second timer sequence
        SimulatedStepper --> [*]
    }
    
    Analyzing --> Dashboard : populateDashboardView(data)
    DemoMode --> Dashboard : populateDashboardView(mockPayload)
    
    state Dashboard {
        [*] --> RenderGauge : animate circular SVG gauge
        RenderGauge --> RenderPills : show section present/missing badges
        RenderPills --> RenderAccordions : build layer cards with chevron click handlers
        RenderAccordions --> RenderCitations : load metrics progress bar
        RenderCitations --> RenderTable : append duplicate/flagged references
        RenderTable --> ArmedActions : expose PDF download and reset controls
    }
    
    ArmedActions --> DownloadingReport : triggerPdfDownload() POST /report
    DownloadingReport --> ArmedActions : createObjectURL anchor triggers save
    ArmedActions --> UploadIdle : resetUploadView()
```

---

## 12. electron/main.js — Desktop Process Bootloader

* **Diagram Type:** Sequence diagram
* **AI Image Gen Prompt:**
  > A sequence diagram showing desktop application process lifecycles. Horizontal lines representing Electron App Core, Splash Window, Main App Window, Port Finder, and Python Uvicorn child process. Shows splash launch, port discovery, uvicorn background spawning, loadURL, splash close, and IPC bridge window controls. High tech theme.
* **Mermaid Code:**
```mermaid
sequenceDiagram
    autonumber
    participant Core as Electron Core
    participant Splash as Splash Window
    participant Main as Main App Window
    participant Port as Port Discovery
    participant Python as Python Child Process

    Core->>Splash: app.ready -> createSplashWindow()
    Core->>Main: createMainWindow() (frameless, preload.js, hidden)
    Core->>Port: findFreePort(8000)
    Port-->>Core: Returns available port N
    Core->>Port: killPortIfBusy(N) [Windows-only taskkill]
    Core->>Python: spawn PYTHON_EXE -m uvicorn main:app --port N
    Python-->>Core: read stdout "Application startup complete"
    Core->>Main: mainWindow.loadURL(http://127.0.0.1:N)
    Main-->>Core: webContents 'ready-to-show'
    Core->>Splash: splashWindow.close()
    Core->>Main: mainWindow.show()
    
    Note over Main, Core: Custom Titlebar IPC Handlers
    Main->>Core: ipcRenderer.send('window-minimize' / 'maximize' / 'close')
    Core->>Main: execute native window actions
```
