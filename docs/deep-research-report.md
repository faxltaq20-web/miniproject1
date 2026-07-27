# Executive Summary  

Academic PDFs present unique extraction challenges: two-column layouts, equations, tables, and figures often break traditional parsers. Our proposed **layered pipeline** augments the existing PyMuPDF4LLM extractor with specialized modules for the hardest elements (equations, tables, figures, references) rather than replacing it wholesale. We first classify PDFs as **native (text-based)**, **hybrid** (mix of text and images), or **scanned (image-only)**, since each class has different failure modes.  We then outline a modular architecture that starts with PyMuPDF4LLM to get text + layout JSON, followed by targeted passes for tables (e.g. Camelot/Tabula or ML-based), equations (glyph recovery or math OCR), figures (image OCR and caption linking), and citations (GROBID or rule-based). This design maintains provenance (page, bbox, confidence) and maximizes reuse of the existing pipeline. Key components include equation region detectors (e.g. YOLO/LayoutLM/Surya), Mathpix or open-source math OCR (Pix2Text, MinerU), and table parsers. We detail orchestration (selective OCR, parallelism, caching), deployment (CPU vs GPU, costing for ~20K pages/day), and monitoring (extraction accuracy metrics, A/B testing). A migration path shows minimal changes to add a Mathpix equation layer and table extractor to the current PyMuPDF4LLM flow. Finally, we present decision criteria (accuracy vs cost), a comparison table of tools (accuracy, cost, equation support), and a phased rollout plan. 

This comprehensive design aims for maximal content recovery (≥90%) with minimal disruption, balancing immediate ROI (patching PyMuPDF4LLM) against longer-term upgrades (Docling/Marker/MinerU) as needed.  

# 1. PDF Types and Failure Modes 

We classify academic PDFs into three types (with illustrative examples) and map extraction failures to each:

- **Type A: Native PDFs (born-digital).**  These (e.g. arXiv, IEEE, Springer papers) have embedded text/glyphs generated from Word/LaTeX. Equations may be stored as text (glyphs) but often with special math fonts. Two-column text may be interleaved. Figures are embedded but their text is not machine-extracted unless OCR is applied.  
- **Type B: Hybrid PDFs.**  These contain a mix: ordinary text layers plus pages or parts (especially figures/equations) rendered as images. Many older publisher PDFs or scanned sections fit here.  
- **Type C: Scanned PDFs.**  These (e.g. digitized archives) have no text layer – every page is an image. All content requires OCR first, compounding errors.

Common failure modes by element (adapted from [2],[11]):

- **Reading Order (Multi-Column):** Native/hybrid multi-column text often becomes interleaved (left-right-left-right) if columns aren’t detected. The PDF internal stream does *not* preserve column order, so naive extraction jumbles paragraphs. This is a critical issue: a small column mis-order can corrupt large sections of content.  

- **Equations:**  In native PDFs, equations are usually glyphs from math fonts, lacking semantic markup. Parsers see them as separate characters. In hybrid/scanned, equations are images. In both cases, extraction typically yields gibberish or blanks (e.g. subscripts/superscripts lost, “∂²u/∂x²” becomes “@2u@x2” or nothing).  
- **Tables:**  PDF stores tables as positioned text and drawn lines, with no table structure. Parsers either output borderless text (losing cell boundaries) or incorrectly interleave columns. Complex tables (multi-row headers, spans) almost always break.  
- **Figures & Captions:**  Figures (charts, diagrams) are images. Parsers ignore image content, so any text inside (labels, legends) is missed. Captions (text blocks) may be placed below or above figures; flattening text by reading order often inserts caption text mid-paragraph, breaking context.  
- **Headers & Footers:**  Repeated page headers/footers (conference name, page numbers) appear on every page. Parsers treat them as normal text, inserting e.g. “Page 3” in the middle of a sentence spanning pages. These must be filtered out or suppressed.  
- **References & Citations:**  Reference sections involve irregular formatting. Citations (e.g. “[12]” or “Smith et al. 2023”) are extracted, but linking them to bibliography entries usually fails. Reference parsing typically requires a separate tool (e.g. GROBID).  
- **Appendices/Supplementary:**  Layout often shifts (from two-column to one-column, or landscape pages). Without re-detection, column detection may fail mid-doc, causing truncated text or mis-ordered reading. Many workflows truncate after “References” or max tokens, losing appendices entirely.  
- **Abstract/Section Headers:**  First-page abstracts often span columns, causing misplaced slicing. While less damaging if column detection works, simple extractors may merge title/authors/abstract with first column of intro, hiding section breaks.  

A summary (ordered by severity for typical research corpora):  

| Element                    | Difficulty        | Common Failure Mode                                                                         |
|----------------------------|-------------------|---------------------------------------------------------------------------------------------|
| Tables (complex)           | Extreme           | Cells interleaved, merged-header lost; requires dedicated extraction                       |
| Reading Order (multi-col)  | Extreme           | Column text mixed; paragraphs fragmented                                                   |
| Figure Text / Charts       | Very High         | Graphic text omitted; captions mis-placed/injected                                         |
| Equations (native/glyph)   | Very High         | Superscripts/subscripts lost; math fonts unreadable (gibberish)             |
| Equations (rendered image) | Extreme           | Treated as image; OCR required                                                             |
| References/Citations       | High              | Bibliography extracted poorly; in-text links lost                             |
| Footnotes                  | Medium            | Positioned at bottom; often merged with body text                                          |
| Headers/Footers            | Low-Med           | Page numbers, titles repeated mid-sentences (removable by layout filtering)                |
| Layout Switches (Appendix)| Medium            | Column detector fails on format change                                                    |
| Abstract/Section Headers   | Low-Med           | Lost or run together if columns not segmented correctly                                    |

*Sources:* Academic PDF structure issues have long been documented. Tabula/Camelot struggle with layout-based tables, and GROBID is often used for titles, sections, references. The table above synthesizes observed failure modes from these sources.

# 2. Layered Extraction Architecture  

The core idea is to **retain PyMuPDF4LLM as the workhorse** for broad extraction (since it already handles text blocks, basic tables, images, and selective OCR) and **layer on specialized modules** for the hardest elements. This modular design allows incremental improvement. Below is a high-level flowchart (Mermaid) of the proposed pipeline:

```mermaid
flowchart TD
  A[Input: PDF] --> B[PyMuPDF4LLM Extraction]
  B --> C{Element Classification}
  C --> D[Text Blocks (Markdown/JSON)]
  C --> E[Table Blocks]
  C --> F[Equation Regions]
  C --> G[Figures/Images]
  C --> H[Reference Section]
  D --> I[Heading & List Detection]
  E --> J[Table Extraction]
  F --> K[Glyph-based LaTeX Recovery]
  F --> L[Math OCR (image formulas)]
  G --> M[Image OCR & ALT-text]
  G --> N[Caption Association]
  H --> O[Citation/Reference Parser]
  I & J & K & L & M & N & O --> P[Merge & Assemble]
  P --> Q[Structured Markdown/JSON]
  Q --> R[LLM (Gemini) Analysis]
```

1. **PyMuPDF4LLM Extraction (Stage 1):** We feed each PDF to PyMuPDF4LLM (`to_json()` mode) to get a page-by-page JSON of text elements, bounding boxes, and image references. PyMuPDF4LLM handles:
   - Two-column reflow (its layout module attempts correct reading order).
   - Header/footer detection (marking or omitting repeated elements).
   - OCR on-scanned content (its hybrid OCR only on needed pages or regions).
   - Initial table detection (`table_strategy`) which will catch simple lined tables.  
   This stage outputs a base JSON/Markdown with block segmentation and bounding boxes.

2. **Layout and Reading Order Correction (Stage 2):** We post-process the JSON to ensure correct reading order and hierarchy. This may involve:
   - **Column reordering:** Using the bounding boxes, reflow text by column rather than row-order if needed.
   - **Header/Footer filtering:** Drop any header/footer text flagged (if not already removed in Markdown) based on repeating content or PyMuPDF flags.
   - **Paragraph merging:** Combine lines mis-split by PDF artifacts (often needed if PyMuPDF splits too aggressively).  

3. **Table Extraction (Stage 3):** For each page (or detected `table` block):
   - If PyMuPDF4LLM already identified a table and it looks correct, we keep it. Otherwise:
   - Use a table-dedicated extractor on pages with tabular layouts:
     - **Camelot/Tabula:** If the table has clear borders/lines or simple structure. These parse PDFs directly and output CSV/Markdown.
     - **ML-based/Table detection:** If Camelot fails or for more complex tables, use an AI parser (MinerU, Docling) or cloud API (Azure/AWS) to get cell structure.  
   - The extracted table is formatted as Markdown (or HTML for complex cells) and inserted into the output. We keep original cell/column headers and row order.  
   - *Rationale:* Tables are the single hardest element, so a focused tool is warranted. We may run both: first PyMuPDF’s own method, then Camelot, then fall back to MinerU if needed.

4. **Equation/Formula Extraction (Stage 4):**  We detect likely formula regions and extract them:
   - **Region Detection:** Use a layout model (e.g. YOLO, LayoutLM classifier, or Surya) to find bounding boxes of equations (display and inline). For example, a small CNN-based detector or rules (if font is math font).  
   - For each equation region:
     - If the content is textual (glyphs), try **native glyph recovery**: parse the PDF text in that bbox. Algorithms may cluster characters by baseline shifts to infer superscripts/subscripts. In practice this is very hard, so at best a heuristic is used to produce LaTeX-like text. (See Shah et al. 2021 for a complex graph-based approach, but such pipelines are research prototypes.)
     - Otherwise, treat it as an image and send to **Math OCR**:
       - **Mathpix API:** Cloud service returning high-quality LaTeX. Very accurate (SOTA) but paid. Ideal for production when budget allows.
       - **Open-source OCR:** Tools like Pix2Text, MinerU’s OCR, or Im2LaTeX models. Pix2Text is free/MIT and can run on GPU locally; it gives about “90–95%” accuracy (per developer claims) but may lag Mathpix on very complex formulas. MinerU also supports formula output as LaTeX.
     - **Inline Math:** Often equations appear in the middle of text (“$L(\theta) = -\sum...$”). These are tricky to detect. We can apply heuristics: any tiny superscript/subscript in the text flow (PyMuPDF can report font size offsets), or regex patterns (numbers after letters). If found, run math OCR on the inline segment or try to merge superscripts manually.
   - We then replace the original equation (image or garbled text) in the Markdown with the recovered LaTeX string, preserving its location. We also attach a confidence/provenance tag (page, bbox).  

5. **Figure/Image Processing (Stage 5):**  For each embedded figure:
   - **OCR on Figures:** Extract the image (PyMuPDF4LLM already outputs images). Run an image OCR (Tesseract or Google/Vision OCR) to get any embedded labels/legends as text. This recovers content that would otherwise be lost.
   - **Caption Association:** Identify caption text in the JSON by proximity and keywords (“Figure”, “Fig.”). If a text block is found below an image bbox, treat it as that figure’s caption. Extract it separately (so LLM knows “Figure 1: Description”).
   - *Optional:* Use an image captioning VLM (e.g. GPT-4o Vision) to auto-generate a descriptive caption if the figure is central to the paper's contribution (useful for RAG indexing).
   - We then ensure figures are referenced properly in the Markdown (e.g. using `![Fig1](fig1.png)` with alt-text from OCR/caption).

6. **Reference/Citation Parsing (Stage 6):**  
   - Detect the References section (usually by heading “References” near end). Extract each reference entry, possibly using GROBID or a regex/ML model.  
   - Build a simple map from citation keys (e.g. “[12]” or “(Smith 2020)”) to reference details. We may not need to fully resolve them, but at least present the reference list in the output. GROBID can do title/authors/venue extraction, but integration adds complexity.  
   - In the Markdown, keep reference lists as a block at the end, and note in-line markers (e.g. `[12]`).

7. **Merging and Output (Stage 7):**  Finally, we combine all processed elements into a single structured document. We maintain the original section hierarchy (headings, paragraphs), but enrich it:
   - Insert the cleaned text (Stage 2) as paragraphs.
   - Replace table placeholders with the Markdown tables from Stage 3.
   - Insert each equation as a LaTeX code block or inline math at the right position.
   - Place figures with captions.
   - List references at the end.
   - The result is a Markdown (or JSON) with rich structure and the needed provenance (we keep a mapping of page/bbox to each chunk, to allow citation of sources in analysis).  
   This Markdown/JSON is then ingested by the LLM (Gemini) for analysis.

**Pipeline Flowchart:**  

```mermaid
flowchart LR
    PDF[PDF] -->|page-by-page| PyMuPDF[PyMuPDF4LLM extraction (JSON/MD)]
    PyMuPDF --> Layout[Layout Analysis & Reflow]
    Layout --> Text[Text Blocks]
    Layout --> Tables[Detected Table Blocks]
    Layout --> Equations[Detected Formula Blocks]
    Layout --> Figures[Detected Figures]
    Layout --> References[Reference Section]
    Text --> Final[Merge to Markdown]
    Tables --> TableParse[Table Extraction (Camelot/MinerU/...)] --> Final
    Equations -->|native glyph| GlyphParse[Glyph Parsing→LaTeX] --> Final
    Equations -->|image OCR| MathOCR[Math OCR (Mathpix/Pix2Text)] --> Final
    Figures --> ImgOCR[Figure OCR] --> Final
    Figures --> CaptionAssoc[Caption Linker] --> Final
    References --> RefParser[Parse Bibliography] --> Final
    Final --> Gemini[Gemini Analysis]
```

*Key Notes:* This design keeps PyMuPDF4LLM at the center (handling ~80–90% of text). Specialized modules kick in only where needed. All intermediate data remain linked to the original pages and bboxes, ensuring the final LLM prompts can refer to page-level evidence. 

# 3. Equation Extraction Strategies 

Extracting math formulas is the *singular toughest* extraction challenge. We employ a two-pronged approach: (a) try to recover from the PDF’s native text layer if possible, (b) otherwise use Math OCR on image data.  We also handle inline math specially.

### (a) Native Glyph Recovery (Text-layer equations)  
In **native PDFs**, some formulas exist as text glyphs (especially from LaTeX generation). Here, each symbol (like “x”, “^”, “2”) is a separate text object. The strategy is: use the PDF text coordinates to reconstruct the expression. Methods include: 
- **Character clustering:** Identify groups of characters with overlapping vertical/horizontal positions to form symbols (e.g. “x” with a superscript “2” above it).  
- **Baseline analysis:** If a character is drawn significantly above or below the current text line, treat it as superscript/subscript.  
- **Math fonts detection:** Many LaTeX PDFs use fonts like Computer Modern. If a text chunk uses a known “math font”, flag it as likely formula.  
- **Graph-based parsing:** In advanced research, algorithms like QD-GGA (graph attention networks) parse symbol layouts into expression trees. Implementing such is beyond scope, but references exist.  

**Tools/Libraries:** There is no widely-used open tool that reliably converts PDF glyphs to LaTeX. Research prototypes (e.g. MathSeer [ICDAR2021]) exist. In practice, our pipeline would do a heuristic scan: any garbled text from PyMuPDF4LLM that looks mathematical (many symbols, foreign characters) triggers this. If confident, we assemble a LaTeX string; if not, skip to OCR. 

**Caveat:** Native glyph recovery is error-prone. In many production settings, teams rely almost entirely on OCR for formulas. We will attempt it for small inline cases (e.g. x_i^2) or clear display equations, but otherwise fall back.

### (b) Math OCR for Rendered Equations  
When formulas are images (scanned or rasterized), we use a specialized OCR:

- **Mathpix API:** Industry-leading accuracy for math OCR (biomedical, academic use cases). It returns LaTeX. Pricing (as of 2026) is ~$4.99+ per 1000 equations (numbers from user research), and offers bulk conversion via PDF/Image APIs. We would call it only on detected equation images. The output is high-quality (often near-perfect, including matrices and multi-line). Integration: use Mathpix SDK or HTTP API, respecting rate limits. We batch equations per page or document to amortize latency, and cache results for reused content.  
- **Open-source alternatives:**  
  - **Pix2Text (P2T):** MIT-licensed tool that does math OCR among other tasks. It includes models (TrOCR-based) fine-tuned on formulas. It can run on local GPU or CPU (slower). According to the developers, Pix2Text achieves ~90–95% of Mathpix’s accuracy at no cost. It also does layout analysis and tables. We can integrate Pix2Text in our pipeline (via its Python API) to process formula images and get LaTeX.  
  - **MinerU:** Aside from being a full parser, MinerU’s OCR component can output LaTeX for equations (it advertises “high formula recognition”). However, MinerU is heavyweight (requires GPU, PyTorch), so perhaps use only if GPU is available and volume justifies it.  
  - **Im2LaTeX models:** There are research ML models (e.g. by Deng et al.) on HuggingFace that convert images to LaTeX. Performance varies; could be a backup.  

**Trade-offs:** Mathpix provides the best quality out-of-box but is a recurring cost. Pix2Text (free, local) is less accurate on very complex formulas (G2 reviews note slight deficiencies) but removes API dependency. For 1k papers/day (~20k equations?), costs for Mathpix could become significant (potentially thousands of USD/month), whereas Pix2Text scales with local GPU usage. We may adopt a hybrid: e.g. use Pix2Text by default, fall back to Mathpix when Pix2Text’s confidence is low (both provide confidence scores).  

**Batching & Parallelism:** We should parallelize math OCR (e.g. send many formula images concurrently). Mathpix API supports bulk PDF conversion (though costs more, but yields full document text including formulas). For open-source, we can run multiple Pix2Text instances on GPU. 

### (c) Inline Math Detection and Heuristics  
Inline math (e.g. `$x_i^2$` in the text flow) can be overlooked. Strategies:
- **Font/size analysis:** If a small superscript or subscript is detected (PyMuPDF can report vertical offsets in the `to_json()` output), treat that span as inline math.  
- **Pattern detection:** After extraction, search for isolated single symbols that follow a letter (e.g. “x 2” where “2” is lower).
- **Regex on raw text:** Look for patterns like `=−Σ` or Greek letters (π,λ) next to English text.  
If an inline math candidate is found, we isolate that run of characters and send it through the same pipeline (glyph or OCR). We then merge the returned LaTeX back into the word (with proper `$...$` or `\(...\)` markers).  

Inline equations are smaller, so even moderate OCR (like Pix2Text) usually handles them fine. We must ensure not to confuse hyphenated words or abbreviations for math. Confirming with a simple small threshold (most inline math has special symbols like `^,_,=,≥, ...`) can help.

*Sources:* The need to detect and preserve math in research documents is well-known. Commercial Mathpix emphasizes this capability. Pix2Text’s documentation likewise highlights formula OCR.  

# 4. Table Extraction Strategy 

Tables require dedicated handling. Our pipeline will use a **hybrid approach**:

- **Default Pass (PyMuPDF4LLM):** PyMuPDF4LLM’s `to_markdown()` can output detected tables, but only simple ones (especially if `table_strategy="lines_strict"` is used). These often suffice for plain bordered tables. If the output looks reasonable, we accept it.  

- **Camelot/Tabula (if needed):** If PyMuPDF’s table looks wrong or is missing:
  - **Camelot** (with lattice/stream modes) can parse tables in PDFs. Use `lattice=True` for clearly-lined tables, else `stream=True` for whitespace tables. It outputs Pandas DataFrames or HTML/CSV. We convert to Markdown/HTML and insert.  
  - **Tabula** is an alternative (Java-based). It often requires more tuning.  
  These are CPU-bound and can be run in parallel per page. They fail on very complex tables (merged headers, nested columns).  

- **ML-based Table Extraction:** For stubborn cases (merged cells, irregular layouts), use a more powerful parser:
  - **MinerU/Docling:** Both use deep models to detect table cells. MinerU’s marketing claims “near-perfect table extraction”. Docling similarly outputs structured tables. The downside is heavy compute (GPU) and integration complexity. We might reserve these for high-value documents or phases of migration.
  - **Surya Layout:** Surya’s layout analysis can detect table blocks. It outputs row+column grids. We could feed Surya’s results into a converter (or let Surya itself output table text).
  - **Cloud APIs:** AWS Textract and Azure Form Recognizer excel at tables. They return JSON with cell coordinates. As a fallback, we could send pages flagged as “failed table” to Textract. This has latency and cost ($0.0025 per page roughly for Textract).
  
- **Integration:** We plan to do this per page: if PyMuPDF4LLM’s JSON flagged a table block (`"type":"table"`), run Camelot; if Camelot fails (no data) run MinerU; if still bad, try cloud API. Each output is merged into the Markdown. We keep original headers as table headings.  

**Choice Heuristics:**  
- **Simple table (borders, 2–5 cols):** Camelot lattice.  
- **Borderless but well-aligned:** Camelot stream or PyMuPDF’s lines-based detection.  
- **Nested/Complex:** Skip to MinerU/Docling or Azure/AWS.  
- **Fallback:** If everything fails, as last resort, output the table page as image (so LLM can at least see it) and log for manual review.  

*Sources:* The difficulty of tables is widely noted. Marker and MinerU explicitly advertise strong table handling. Commerical docs (Microsoft/AWS) emphasize it too. PyMuPDF’s own docs advise “lines_strict” or disabling layout for tables.  

# 5. Figure and Citation Extraction 

**Figures & Diagrams:** Figures (plots, photos, diagrams) are extracted as image files by PyMuPDF4LLM. We should:
- **OCR inside Figures:** Use Tesseract or Google/Vision OCR on the image to capture any textual elements (axis labels, legends). This text is not part of the main flow but should be noted. We can append “(text in image: …)” after figure reference or embed as alt-text.  
- **Figure Captions:** Identify text blocks that appear immediately above/below each image. Typically, caption lines begin with “Figure 1.” or “Fig. 2”. We use spatial proximity: any text at the bottom of the figure’s bbox or top if layout is unusual. Extract that as the caption. In Markdown, format as: `![Fig1: Caption...](fig1.png)`. This preserves it for LLM context.  
- **Image Captioning (Optional):** If desired, run a vision model (like GPT-4o with image input) to auto-caption the image based on content. This can help when figures have no helpful text. Use as a *supplemental* annotation (flagged as “auto-caption”) since it may hallucinate or oversimplify.  
- **Flow:** In the merged Markdown, figures are placed at their mention points or grouped at end of section, with references like “Figure 3 (see appendix)”. We ensure references to them (e.g. “as shown in Fig. 3”) remain linked by numbering.

**Citations & References:**  
- **Detect Reference Section:** Use a simple regex or look for the heading “References” or “Bibliography” in extracted text. Once found, mark all subsequent lines as references.  
- **Parse Entries:** Optionally run GROBID (external service) or a regex parser on each reference line to separate authors/title/year. For our RAG use-case, even the raw reference text is often enough; GROBID could improve structured linking (but adds complexity).  
- **In-text Citations:** Leave them as-is (e.g. “[5]” or “(Smith et al., 2021)”). We could attempt to hyperlink them to the reference list (if output allows HTML), but at minimum we preserve their context.  
- **Citation Graph:** As a longer-term feature, one could index references in a DB to interlink authors. Not needed for initial pipeline.

*Sources:* GROBID is indeed used in pipelines like Semantic Scholar for parsing refs. Cloud OCRs also identify tables and forms (including references). We assume basic regex or model is sufficient for now. 

# 6. Equation/Formula Region Detection 

A crucial sub-step is identifying **where** equations reside on a page. Approaches:
- **LayoutParser/Detector Models:** Use an ML model to label regions. For example, LayoutParser has pre-trained models or can be fine-tuned to classify blocks (Table, Figure, Formula, etc).  
- **YOLO/SSD:** A dedicated object detector (e.g. based on YOLO) can be trained on a set of PDF images to find “formula” boxes. The MathSeer pipeline used an SSD for this. Surya’s layout detection might also flag formula regions (it lists “table, image, header, etc.”).  
- **Heuristics:** If ML is infeasible, use text clues from PyMuPDF’s JSON: look for text segments with tiny fonts or lots of symbols. If a line has a high density of non-alphanumeric characters, mark it. Or detect where the text width is extremely small relative to page (typical of equations).  
- **Fallback:** Also treat any isolated image with aspect ratio like formula (wide and short) as equation, subject to manual review.  

Once we have equation bboxes, those are fed to native vs image OCR as described. We keep a confidence score (from the detector) and can skip low-confidence (to avoid OCRing math in plain text).  

*Provenance:* For each recovered formula (as LaTeX), record the page number and bounding box from which it came. In the merged Markdown, we annotate it, for example:  
```latex
\begin{equation} 
E=mc^2 
\end{equation} 
<!-- [Page 5, bbox=(100,200,150,220), source: PDF] -->
```  
so Gemini can trace where this formula was found.

# 7. Pipeline Orchestration & Deployment 

To run this at scale (1000–10000 papers/day), we must manage resources and costs:

- **Selective OCR:** PyMuPDF4LLM’s hybrid OCR already reduces unnecessary Tesseract runs. We similarly apply OCR only where needed (problematic pages, equation/figure regions).  
- **Parallel Processing:** All stages can be parallelized by page or by module. For example, run PyMuPDF4LLM on multiple CPUs, dispatch table and equation tasks asynchronously, and possibly batch math OCR calls. If using GPUs (for Pix2Text or MinerU), process in batches to maximize throughput (e.g. Pix2Text example [8] shows 5 pages/sec on an H100).  
- **Caching and Rate Limiting:** 
  - *Mathpix:* It has API rate limits and costs per call. We should cache LaTeX results per unique image (though duplicates are rare), and throttle requests. Possibly pool equations from multiple papers in a day to one Mathpix call. 
  - *OpenAI API (if used for any VLM tasks)* would similarly need batching and pooling of tokens.  
- **Infrastructure:** 
  - CPU-bound tasks (PyMuPDF4LLM, Tesseract) can run on standard nodes. 
  - GPU tasks (MinerU, Pix2Text, Surya) require GPUs (A100/H100 or even mid-tier cards). Estimate: to process 20k pages/day, if Pix2Text does ~2 images/sec on an A100, one GPU can do ~172k images/day, which is sufficient. Layout analysis (Surya) at 5 pages/sec on RTX 5090 as [13] suggests ~432k pages/day per GPU, so also okay. MinerU might need more.  
  - We should size: maybe start with 2 GPUs (for math OCR and layout/ML tasks) and a few dozen CPU cores. Adjust after benchmarking.

- **Cost Estimates (Assumptions):**  
  - *Mathpix:* $0.0005 per equation? If 20k pages with ~2 eq each = 40k eq = ~$20/day (just guess). Could be more for complex usage. 
  - *GPUs:* Cloud GPU ~ $3/hour * 24*30 = $2160/mo per card. If 2 GPUs, ~$4320/mo. On-prem could be cheaper long-term. 
  - *Compute:* 20k pages on PyMuPDF4LLM (text extraction) maybe 0.1s/page = ~2k seconds on one core; so ~0.6 CPU-min/page ~ 200 CPU-hrs. With parallel machines, manageable. 
  - *Storage:* Output markdown/JSON + images, maybe 0.5MB/page, so 10GB/day, easy. 

- **Monitoring & Benchmarking:** 
  - **Metrics:** Design metrics for extraction quality: e.g. text recall, table recall, equation recall. We can use a test corpus of ~50 varied papers (native/hybrid/scanned) with ground-truth (manually labeled or from LaTeX) to compute error rates. 
  - For downstream impact, do an A/B test: process a set of papers with and without the new pipeline, feed both to Gemini, and evaluate the generated reports for factual accuracy or completeness (via human raters or automated QA).  
  - Monitor system logs for failure cases (pages with no text extracted, parsing exceptions) and maintain a feedback loop: if certain journals or layouts fail often, tune rules.  
  - Log usage: number of OCR calls, Mathpix spend, GPU utilization.

- **Progressive Rollout:** Start with the easiest cases (PDFs already parsed well) to ensure stability. Then enable one feature at a time (e.g. first inline equations, then tables, then figures) and validate outputs.  

# 8. Migration Path (PyMuPDF4LLM to Enhanced Pipeline) 

To minimize disruption, we propose **extending** the current PyMuPDF4LLM codebase rather than a wholesale rewrite. Key steps (with pseudocode) might be:

1. **Keep existing PyMuPDF4LLM usage** for the main extraction (Markdown/JSON).  
2. **Add equation detection:** After calling `to_json(doc)`, inspect the JSON. For each page:
   ```python
   from pymupdf4llm import to_json
   data = to_json(doc)
   for page in data['pages']:
       # Example heuristic: find glyph blocks with small baselines
       eq_regions = detect_equations(page)
       for bbox in eq_regions:
           img = get_page_image(page_num)  # render area to image
           latex = mathpix_api.convert(img)  # or use Pix2Text locally
           insert_into_md(page, bbox, latex)
   ```
   This hooks in before finalizing the Markdown.  

3. **Table extraction layer:** Also inspect page elements:
   ```python
   for table_block in page['tables']:
       try:
           df = camelot.read_pdf(pdf_path, pages=page_num, flavor='lattice')
       except:
           df = camelot.read_pdf(..., flavor='stream')
       markdown_table = df_to_markdown(df)
       replace_in_md(page, table_block['text_range'], markdown_table)
   ```
   Or even simpler: after PyMuPDF4LLM output, call Camelot on flagged pages and splice in.  

4. **Figure OCR:** 
   ```python
   for img_ref in page['images']:
       img = extract_image(img_ref) 
       text = ocr_engine.recognize(img)
       append_to_output(f"[Fig image text: {text}]")
   ```
   And similarly associate captions via positional logic.  

5. **References parsing:** After all pages, find “References” heading in `data['text']` and process that segment with GROBID or simple splitting.  

These additions require minimal change to the extraction loop: essentially intercept the JSON and Markdown output and post-process. We ensure to respect any user-config (`header=False`, etc).  

# 9. Risk Analysis & Decision Criteria 

**Mathpix vs Open Source:** Mathpix yields the highest accuracy, especially on complex equations, but is costly and an external dependency. Use criteria:
- If a client *requires* near-perfect math (e.g. math-intensive domain, knowledge graph), Mathpix or a service (Mathpix or new entrants) is justified.
- If budget is tight or equations are secondary, a local alternative (Pix2Text/MinerU) may suffice. Our plan: start with Pix2Text (free) in dev, and selectively use Mathpix for a sample to measure error.  
- If GPU resource is *very* limited, Mathpix offloads compute at a price. But at 20k pages/day, if ~5,000 equations, Mathpix at ~$0.001 each is ~$5/day, which could be fine.

**Tool Migration (PyMuPDF4LLM → New Parser):** We mostly avoid this unless needed. Reasons to replace:
- If PyMuPDF4LLM consistently misses >X% of content even after augmentation.
- If a tool like Marker/Docling dramatically cuts manual curation (recommenders say Marker/MinerU excel at tables/formulas).
- Risks of switching: code changes, licensing (Marker’s GPL-research license may preclude commercial use), infrastructure changes.
- Approach: Run both in parallel on a test set. If new parser’s extra yield justifies development effort, plan phased migration.

**Surya/Other Layout Models:** Using Surya or LayoutLM for detection adds complexity (serving those models). The risk is model hallucination (Firecrawl warns VLMs may hallucinate text). We should keep human-readable content as ground truth. If Surya is used, validate outputs thoroughly.

**Fallbacks:** Always keep ability to mark “unknown” rather than hallucinate. For example, if equation OCR is low-confidence, output the original image (or a placeholder “(see figure for equation)”) to avoid wrong LaTeX.

**Milestones & Metrics:** We will track metrics like:
- Text extraction recall (against ground truth PDF text).
- Table structure accuracy (matched cells).
- Equation OCR accuracy (compare extracted LaTeX to ground truth).
- Impact: e.g. improvement in LLM answer correctness (via manual annotation).

*Decision Table of Tools:* Below is a simplified comparison for key components:  

| Tool/Service          | Cost (USD)         | Accuracy (Equation/Table)     | Deployment | License   | Notes                                 |
|-----------------------|--------------------|-------------------------------|------------|-----------|---------------------------------------|
| **PyMuPDF4LLM**       | Free               | Moderate (text), poor (eq)    | Local (CPU) | MIT       | Good base extractor, misses eq/table |
| **Mathpix Snip API**  | ~$0.001/eq (~$4.99/month up) | Excellent (SOTA eqs, decent tables) | Cloud (API) | Proprietary| Best formula OCR; paid; rate limits |
| **Pix2Text (P2T)**    | Free/Open-Source   | High (~90-95% formula) | Local (CPU/GPU) | MIT       | OCR + layout, can run local. Requires GPU for speed |
| **MinerU**            | Free/Open-Source   | Very High (eq + tables) | Local (GPU req) | Apache   | Top accuracy; heavy, GPU needed |
| **Marker-PDF**        | Free (GPL-research) | High (table, images), formulas weak | Local (GPU req) | GPL/research | Great image/table; formula support limited |
| **Docling**           | Free/Open (IBM)    | High (good structure)         | Local       | Apache   | Strong reading order, formula moderate |
| **Surya OCR**         | Free/Open         | High (OCR + layout)           | Local (GPU) | Apache 2.0 | 90+ langs, includes table detection |
| **AWS Textract**      | $0.0015/page      | Good (tables, forms)          | Cloud       | Proprietary| Paid, OCR+table, but equation=garbage |
| **Azure Doc Int.**    | ~$0.0008/page     | Good (tables, forms)          | Cloud       | Proprietary| Similar to AWS; no equation support |
| **OpenAI GPT-4o Vision** | $0.3–$1/image (est) | Good captioning,  moderate text| Cloud  | Proprietary| Use for fig captioning (hallucination risk) |
| **GROBID**            | Free/Open         | Good (refs, sections)         | Local/Java  | Apache 2.0 | Parse refs/structure of papers |

*(Costs are illustrative and subject to change. GPU = NVIDIA GPU recommended.)*

# 10. Phased Rollout Plan and Success Metrics 

**Phase 1 – Baseline & Monitoring (Weeks 1–2):** Use current PyMuPDF4LLM pipeline on a diverse set of papers (genomics, physics, CS, etc). Collect metrics: % of text extracted, table completeness, number of equations found (empty vs image). This establishes a baseline.

**Phase 2 – Add Table & Caption Fixes (Weeks 3–4):** Integrate Camelot for tables on flagged pages. Add caption association logic. Measure improvement in table and figure extraction accuracy (via sample ground truth). Success: at least 50% drop in table parsing errors on test set. Also ensure no regressions in text extraction.

**Phase 3 – Inline and Native Math (Weeks 5–6):** Add small heuristics for inline superscripts. Try a simple glyph grouping for very small cases. Likely minimal improvement, but implement for completeness. Validate that parser doesn’t break non-math text. 

**Phase 4 – Math OCR Integration (Weeks 7–10):** Integrate Pix2Text (or Mathpix trial). Run on sample of pages with equations. Compare accuracy (e.g. Levenshtein distance on LaTeX) vs baseline (garbage). Tune use of local GPU (if available). Metric: ≥90% of equations correctly recognized in sample. If not, consider Mathpix for missed cases.

**Phase 5 – Layout Detection (Weeks 11–12):** If still many multi-col issues, experiment with Surya or LayoutParser to re-segment columns. Also test parsing References with GROBID. Metric: reduction in reading-order errors (by manual check).  

**Phase 6 – Scaling & Cost Tests (Weeks 13–14):** Run the pipeline on a larger batch (100–500 papers). Monitor throughput, GPU/CPU usage, API costs. Optimize batch sizes (e.g. 50 eq at a time to Mathpix). Ensure stable operation under expected load.  

**Phase 7 – A/B User Testing (Weeks 15–16):** Take the final enhanced pipeline vs baseline, generate LLM reports (Gemini) for a set of papers. Have domain experts rate completeness/accuracy of summaries. Success if the enhanced pipeline yields significantly better scores (e.g. 20% more correct answers about methods/results).  

**Ongoing Monitoring:** Maintain dashboards for key metrics (extraction rate, error counts, cost per paper). Use logging to catch new failure modes as new sources arrive.

**Assumptions:** We assume a variable budget (able to pay for some cloud OCR), and availability of modest GPU resources. We also assume typical academic paper sizes (~10–20 pages, ~5 equations/page, ~1 table/page).

**Conclusion:** By incrementally augmenting PyMuPDF4LLM with targeted modules for tables, formulas, and images, this layered pipeline addresses the major content gaps. Citations from PDF analysis research and tool comparisons confirm that no single tool solves everything. Our architecture leverages the strengths of each: PyMuPDF4LLM for text/layout, Camelot for simple tables, Pix2Text/Mathpix for equations, etc. This strikes a balance of **accuracy vs cost** and allows a gradual migration path. The result is a production-ready extraction system geared for academic PDFs in 2026, maximizing the usable content for downstream LLM analysis.  

