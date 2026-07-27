import os
import sys
import re
from PIL import Image, ImageDraw, ImageFont

def draw_arrow_head(draw, x, y, direction="down", color="black"):
    if direction == "down":
        draw.polygon([(x - 6, y - 10), (x + 6, y - 10), (x, y)], fill=color)
    elif direction == "up":
        draw.polygon([(x - 6, y + 10), (x + 6, y + 10), (x, y)], fill=color)
    elif direction == "left":
        draw.polygon([(x + 10, y - 6), (x + 10, y + 6), (x, y)], fill=color)
    elif direction == "right":
        draw.polygon([(x - 10, y - 6), (x - 10, y + 6), (x, y)], fill=color)

def draw_box(draw, title, subtext, step_num, left, top, right, bottom, font_bold, font_regular, border_color="#1e293b", fill_color="#f8fafc", text_color="#0f172a"):
    # Draw shadow
    draw.rectangle([left + 3, top + 3, right + 3, bottom + 3], fill="#e2e8f0", outline=None)
    # Draw box
    draw.rectangle([left, top, right, bottom], fill=fill_color, outline=border_color, width=2)
    
    # Draw step pill
    if step_num:
        pill_left = left + 10
        pill_top = top + 10
        pill_right = left + 75
        pill_bottom = top + 30
        draw.rounded_rectangle([pill_left, pill_top, pill_right, pill_bottom], radius=4, fill="#0284c7", outline=None)
        draw.text((pill_left + 8, pill_top + 2), f"STEP {step_num}", fill="white", font=font_bold)
        
        text_offset_y = 0
    else:
        text_offset_y = -8
        
    box_w = right - left
    box_h = bottom - top
    
    # Draw Title
    t_bbox = draw.textbbox((0, 0), title, font=font_bold)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    
    title_x = left + (box_w - t_w) / 2
    title_y = top + (box_h - t_h) / 2 + text_offset_y
    if step_num:
        # Push title a bit to the right or lower to avoid overlapping step pill
        title_y = top + 35
        title_x = left + 15
        
    draw.text((title_x, title_y), title, fill=text_color, font=font_bold)
    
    # Draw Subtext
    if subtext:
        s_bbox = draw.textbbox((0, 0), subtext, font=font_regular)
        s_w = s_bbox[2] - s_bbox[0]
        s_h = s_bbox[3] - s_bbox[1]
        
        sub_x = left + 15 if step_num else left + (box_w - s_w) / 2
        sub_y = title_y + t_h + 8
        draw.text((sub_x, sub_y), subtext, fill="#475569", font=font_regular)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    docs_dir = os.path.join(workspace_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    svg_path = os.path.join(docs_dir, "workflow_details.svg")
    png_path = os.path.join(docs_dir, "workflow_details.png")
    
    # Dimensions: 900w x 1400h
    # Horizontal Center is 450
    
    # --- SVG generation ---
    print("Generating SVG workflow diagram...")
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1420" width="900" height="1420" style="background-color:#ffffff;">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#0284c7" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="3" dy="3" stdDeviation="2" flood-color="#cbd5e1" flood-opacity="0.8"/>
    </filter>
  </defs>

  <!-- Title Section -->
  <rect x="0" y="0" width="900" height="70" fill="#0f172a" />
  <text x="450" y="42" text-anchor="middle" font-family="'Segoe UI', Helvetica, sans-serif" font-size="20px" font-weight="bold" fill="#ffffff">
    ResearchSense — Detailed End-to-End Analysis Workflow
  </text>

  <!-- STEP 1: PDF Upload -->
  <rect x="250" y="100" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="112" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="126" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 1</text>
  <text x="345" y="127" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">Client PDF Upload</text>
  <text x="345" y="145" font-family="sans-serif" font-size="11px" fill="#475569">User drops paper.pdf into the UI dropzone (app.js)</text>
  <text x="345" y="161" font-family="sans-serif" font-size="11px" fill="#475569">POST request dispatched as multipart Form Data</text>

  <line x1="450" y1="180" x2="450" y2="230" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 2: Input Validation -->
  <rect x="250" y="230" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="242" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="256" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 2</text>
  <text x="345" y="257" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">FastAPI Validation &amp; Streaming</text>
  <text x="345" y="275" font-family="sans-serif" font-size="11px" fill="#475569">main.py validates PDF suffix and streams chunks</text>
  <text x="345" y="291" font-family="sans-serif" font-size="11px" fill="#475569">Aborts if file exceeds the 30MB safety limit</text>

  <line x1="450" y1="310" x2="450" y2="360" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 3: Text Extraction -->
  <rect x="250" y="360" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="372" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="386" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 3</text>
  <text x="345" y="387" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">PDF Text &amp; DOI Extraction</text>
  <text x="345" y="405" font-family="sans-serif" font-size="11px" fill="#475569">pdf_parser.py runs PyMuPDF4LLM for markdown formatting</text>
  <text x="345" y="421" font-family="sans-serif" font-size="11px" fill="#475569">Extracts embedded hyperlink DOIs from annotations</text>

  <line x1="450" y1="440" x2="450" y2="490" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 4: Section Segmentation -->
  <rect x="250" y="490" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="502" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="516" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 4</text>
  <text x="345" y="517" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">Two-Tier Section Detector</text>
  <text x="345" y="535" font-family="sans-serif" font-size="11px" fill="#475569">section_detector.py splits text into standard keys</text>
  <text x="345" y="551" font-family="sans-serif" font-size="11px" fill="#475569">Triggers Tier 2 Gemini heading mapping if headings non-standard</text>

  <line x1="450" y1="570" x2="450" y2="620" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Split into Parallel Processing -->
  <path d="M 450 620 L 450 640 L 220 640 L 220 670" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  <path d="M 450 620 L 450 640 L 680 640 L 680 670" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  <text x="450" y="635" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#475569">PARALLEL THREADS (asyncio.gather)</text>

  <!-- STEP 5A: LLM Analysis -->
  <rect x="30" y="670" width="380" height="95" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="45" y="682" width="70" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="80" y="696" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 5A</text>
  <text x="125" y="697" font-family="sans-serif" font-size="13px" font-weight="bold" fill="#0f172a">LLM Qualitative Analysis</text>
  <text x="125" y="713" font-family="sans-serif" font-size="10px" fill="#475569">- text_compressor.py shrinks tokens (light/aggr)</text>
  <text x="125" y="727" font-family="sans-serif" font-size="10px" fill="#475569">- SHA-256 cache check (cache/ key hit/miss)</text>
  <text x="125" y="741" font-family="sans-serif" font-size="10px" fill="#475569">- Gemini multi-key rotation calls (4 layers scored)</text>

  <!-- STEP 5B: Citation Validation -->
  <rect x="490" y="670" width="380" height="95" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="505" y="682" width="70" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="540" y="696" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 5B</text>
  <text x="585" y="697" font-family="sans-serif" font-size="13px" font-weight="bold" fill="#0f172a">Reference Credibility telems</text>
  <text x="585" y="713" font-family="sans-serif" font-size="10px" fill="#475569">- Concurrently check DOIs via CrossRef REST API</text>
  <text x="585" y="727" font-family="sans-serif" font-size="10px" fill="#475569">- Fallback: Semantic Scholar title fuzzy matching</text>
  <text x="585" y="741" font-family="sans-serif" font-size="10px" fill="#475569">- Parse ArXiv preprint IDs + check duplicate references</text>

  <!-- Merge Parallel Processing -->
  <path d="M 220 765 L 220 790 L 450 790 L 450 820" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  <path d="M 680 765 L 680 790 L 450 790 L 450 820" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 6: Scoring Engine -->
  <rect x="250" y="820" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="832" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="846" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 6</text>
  <text x="345" y="847" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">Discipline-Adaptive Scoring</text>
  <text x="345" y="865" font-family="sans-serif" font-size="11px" fill="#475569">scoring.py maps layer scores to discipline weights</text>
  <text x="345" y="881" font-family="sans-serif" font-size="11px" fill="#475569">Computes final 0-100 score and letter grade (A-F)</text>

  <line x1="450" y1="900" x2="450" y2="950" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 7: Verdict Generation -->
  <rect x="250" y="950" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="962" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="976" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 7</text>
  <text x="345" y="977" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">Editorial Verdict Synthesis</text>
  <text x="345" y="995" font-family="sans-serif" font-size="11px" fill="#475569">LLM parses lowest-scoring metrics to write verdict</text>
  <text x="345" y="1011" font-family="sans-serif" font-size="11px" fill="#475569">Falls back to offline templates if keys hit rate-limits</text>

  <line x1="450" y1="1030" x2="450" y2="1080" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 8: Renders Dashboard -->
  <rect x="250" y="1080" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="1092" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="1106" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 8</text>
  <text x="345" y="1107" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">Renders Dashboard UI</text>
  <text x="345" y="1125" font-family="sans-serif" font-size="11px" fill="#475569">app.js binds JSON data to dashboard page elements</text>
  <text x="345" y="1141" font-family="sans-serif" font-size="11px" fill="#475569">Animates score gauge, loads accordions and references</text>

  <line x1="450" y1="1160" x2="450" y2="1210" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />

  <!-- STEP 9: Report Generation -->
  <rect x="250" y="1210" width="400" height="80" rx="6" ry="6" fill="#f8fafc" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <rect x="265" y="1222" width="65" height="20" rx="3" ry="3" fill="#0284c7" />
  <text x="297.5" y="1236" font-family="sans-serif" font-size="10px" font-weight="bold" text-anchor="middle" fill="#ffffff">STEP 9</text>
  <text x="345" y="1237" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#0f172a">ReportLab PDF Synthesis</text>
  <text x="345" y="1255" font-family="sans-serif" font-size="11px" fill="#475569">POST /report triggers in-memory report synthesis</text>
  <text x="345" y="1271" font-family="sans-serif" font-size="11px" fill="#475569">Streams compiled BytesIO PDF directly to browser</text>

  <!-- Return Connection back to User (represented as border) -->
  <path d="M 450 1290 L 450 1330 L 150 1330 L 150 140 L 250 140" fill="none" stroke="#0f172a" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)" />
  <text x="160" y="730" font-family="sans-serif" font-size="11px" font-weight="bold" fill="#0f172a" transform="rotate(-90 160 730)">LOOP COMPLETE: Return visual reports and downloads to browser</text>
</svg>
"""

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"SVG workflow details successfully written to: {svg_path}")
    
    # --- PNG generation via PIL ---
    print("Generating PNG workflow diagram...")
    img = Image.new("RGB", (900, 1420), "white")
    draw = ImageDraw.Draw(img)
    
    # Font fallback setup
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 14)
        font_regular = ImageFont.truetype("arial.ttf", 11)
        font_title = ImageFont.truetype("arialbd.ttf", 18)
    except IOError:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_title = ImageFont.load_default()
        
    # Draw Title Bar
    draw.rectangle([0, 0, 900, 70], fill="#0f172a")
    t_bbox = draw.textbbox((0, 0), "ResearchSense — Detailed End-to-End Analysis Workflow", font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((450 - t_w/2, 25), "ResearchSense — Detailed End-to-End Analysis Workflow", fill="white", font=font_title)
    
    # Drawing boxes
    # Step 1
    draw_box(draw, "Client PDF Upload", "User drops paper.pdf into the UI dropzone (app.js)\nPOST request dispatched as multipart Form Data", "1", 250, 100, 650, 180, font_bold, font_regular)
    draw_arrow_down(draw, 180, 230, 450, color="#0284c7")
    
    # Step 2
    draw_box(draw, "FastAPI Validation & Streaming", "main.py validates PDF suffix and streams chunks\nAborts if file exceeds the 30MB safety limit", "2", 250, 230, 650, 310, font_bold, font_regular)
    draw_arrow_down(draw, 310, 360, 450, color="#0284c7")
    
    # Step 3
    draw_box(draw, "PDF Text & DOI Extraction", "pdf_parser.py runs PyMuPDF4LLM for markdown formatting\nExtracts embedded hyperlink DOIs from annotations", "3", 250, 360, 650, 440, font_bold, font_regular)
    draw_arrow_down(draw, 440, 490, 450, color="#0284c7")
    
    # Step 4
    draw_box(draw, "Two-Tier Section Detector", "section_detector.py splits text into standard keys\nTriggers Tier 2 Gemini heading mapping if headings non-standard", "4", 250, 490, 650, 570, font_bold, font_regular)
    
    # Split arrow path
    draw.line([(450, 570), (450, 640)], fill="#0284c7", width=2)
    draw.line([(450, 640), (220, 640)], fill="#0284c7", width=2)
    draw.line([(220, 640), (220, 670)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 220, 670, "down", color="#0284c7")
    
    draw.line([(450, 640), (680, 640)], fill="#0284c7", width=2)
    draw.line([(680, 640), (680, 670)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 680, 670, "down", color="#0284c7")
    
    draw.text((365, 620), "PARALLEL THREADS (asyncio.gather)", fill="#475569", font=font_regular)
    
    # Step 5A
    draw_box(draw, "LLM Qualitative Analysis", "- text_compressor.py shrinks tokens (light/aggr)\n- SHA-256 cache check (cache/ key hit/miss)\n- Gemini multi-key rotation calls (4 layers scored)", "5A", 30, 670, 410, 765, font_bold, font_regular)
    
    # Step 5B
    draw_box(draw, "Reference Credibility Telemetry", "- Concurrently check DOIs via CrossRef REST API\n- Fallback: Semantic Scholar title fuzzy matching\n- Parse ArXiv preprint IDs + check duplicate references", "5B", 490, 670, 870, 765, font_bold, font_regular)
    
    # Merge arrow path
    draw.line([(220, 765), (220, 790)], fill="#0284c7", width=2)
    draw.line([(220, 790), (450, 790)], fill="#0284c7", width=2)
    draw.line([(680, 765), (680, 790)], fill="#0284c7", width=2)
    draw.line([(680, 790), (450, 790)], fill="#0284c7", width=2)
    draw.line([(450, 790), (450, 820)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 450, 820, "down", color="#0284c7")
    
    # Step 6
    draw_box(draw, "Discipline-Adaptive Scoring", "scoring.py maps layer scores to discipline weights\nComputes final 0-100 score and letter grade (A-F)", "6", 250, 820, 650, 900, font_bold, font_regular)
    draw_arrow_down(draw, 900, 950, 450, color="#0284c7")
    
    # Step 7
    draw_box(draw, "Editorial Verdict Synthesis", "LLM parses lowest-scoring metrics to write verdict\nFalls back to offline templates if keys hit rate-limits", "7", 250, 950, 650, 1030, font_bold, font_regular)
    draw_arrow_down(draw, 1030, 1080, 450, color="#0284c7")
    
    # Step 8
    draw_box(draw, "Renders Dashboard UI", "app.js binds JSON data to dashboard page elements\nAnimates score gauge, loads accordions and references", "8", 250, 1080, 650, 1160, font_bold, font_regular)
    draw_arrow_down(draw, 1160, 1210, 450, color="#0284c7")
    
    # Step 9
    draw_box(draw, "ReportLab PDF Synthesis", "POST /report triggers in-memory report synthesis\nStreams compiled BytesIO PDF directly to browser", "9", 250, 1210, 650, 1290, font_bold, font_regular)
    
    # Loop return path
    draw.line([(450, 1290), (450, 1330)], fill="#0f172a", width=2)
    draw.line([(450, 1330), (150, 1330)], fill="#0f172a", width=2)
    draw.line([(150, 1330), (150, 140)], fill="#0f172a", width=2)
    draw.line([(150, 140), (250, 140)], fill="#0f172a", width=2)
    draw_arrow_head(draw, 250, 140, "right", color="#0f172a")
    
    # Save image
    img.save(png_path, "PNG")
    print(f"PNG workflow details successfully written to: {png_path}")
    print("Done!")

def draw_arrow_down(draw, start_y, end_y, x=450, line_width=2, color="black", label=None, label_font=None):
    draw.line([(x, start_y), (x, end_y)], fill=color, width=line_width)
    draw_arrow_head(draw, x, end_y, "down", color)
    if label and label_font:
        draw.text((x + 12, (start_y + end_y)/2 - 8), label, fill=color, font=label_font)

if __name__ == "__main__":
    main()
