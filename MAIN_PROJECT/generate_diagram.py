import os
from PIL import Image, ImageDraw, ImageFont

def draw_dashed_line(draw, start, end, dash_length=8, gap_length=6, width=2, fill="black"):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    distance = (dx**2 + dy**2)**0.5
    if distance == 0:
        return
    cx = dx / distance
    cy = dy / distance
    
    steps = int(distance / (dash_length + gap_length))
    for i in range(steps + 1):
        s = i * (dash_length + gap_length)
        e = s + dash_length
        if e > distance:
            e = distance
        draw.line([(x1 + s*cx, y1 + s*cy), (x1 + e*cx, y1 + e*cy)], fill=fill, width=width)

def draw_dashed_rect(draw, left, top, right, bottom, dash_len=8, gap_len=6, width=2, color="black"):
    draw_dashed_line(draw, (left, top), (right, top), dash_len, gap_len, width, color)
    draw_dashed_line(draw, (left, bottom), (right, bottom), dash_len, gap_len, width, color)
    draw_dashed_line(draw, (left, top), (left, bottom), dash_len, gap_len, width, color)
    draw_dashed_line(draw, (right, top), (right, bottom), dash_len, gap_len, width, color)

def draw_box(draw, name, subtext, left, top, right, bottom, font_bold, font_regular, border_color="black", fill_color="#ffffff", text_color="black"):
    draw.rectangle([left, top, right, bottom], fill=fill_color, outline=border_color, width=2)
    box_w = right - left
    box_h = bottom - top
    
    # Calculate title size
    t_bbox = draw.textbbox((0, 0), name, font=font_bold)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    
    if subtext:
        s_bbox = draw.textbbox((0, 0), subtext, font=font_regular)
        s_w = s_bbox[2] - s_bbox[0]
        s_h = s_bbox[3] - s_bbox[1]
        
        # Center coordinates
        title_y = top + (box_h - (t_h + s_h + 6)) / 2
        title_x = left + (box_w - t_w) / 2
        sub_y = title_y + t_h + 6
        sub_x = left + (box_w - s_w) / 2
        
        draw.text((title_x, title_y), name, fill=text_color, font=font_bold)
        draw.text((sub_x, sub_y), subtext, fill="#555555", font=font_regular)
    else:
        title_y = top + (box_h - t_h) / 2
        title_x = left + (box_w - t_w) / 2
        draw.text((title_x, title_y), name, fill=text_color, font=font_bold)

def draw_arrow_down(draw, start_y, end_y, x=400, line_width=2, color="black", label=None, label_font=None):
    draw.line([(x, start_y), (x, end_y)], fill=color, width=line_width)
    draw.polygon([(x - 5, end_y - 8), (x + 5, end_y - 8), (x, end_y)], fill=color)
    if label and label_font:
        draw.text((x + 12, (start_y + end_y)/2 - 8), label, fill=color, font=label_font)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    
    svg_path = os.path.join(workspace_root, "system_architecture.svg")
    png_path = os.path.join(workspace_root, "system_architecture.png")
    
    # --- 1. GENERATE SVG ---
    print("Generating SVG diagram...")
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 960" width="800" height="960" style="background-color:#ffffff;">
  <!-- Definitions for Markers (Arrowheads) -->
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#000000" />
    </marker>
    <marker id="arrow-return" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title of the Diagram -->
  <text x="400" y="35" text-anchor="middle" font-family="'Times New Roman', Times, serif" font-size="18px" font-weight="bold" fill="#000000">
    ResearchSense — System Architecture Diagram
  </text>
  
  <!-- 1. User Browser -->
  <rect x="300" y="60" width="200" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="82" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">User (Browser)</text>
  <text x="400" y="98" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Uploads PDF &amp; Views Dashboard</text>

  <!-- Arrow User -> Web Interface -->
  <line x1="400" y1="115" x2="400" y2="155" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="140" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">1. Uploads PDF</text>

  <!-- 2. Web Interface -->
  <rect x="270" y="155" width="260" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="177" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Web Interface (app.js)</text>
  <text x="400" y="193" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Dark-mode frontend dashboard</text>

  <!-- Arrow Web Interface -> Backend Server -->
  <line x1="400" y1="210" x2="400" y2="250" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="235" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">2. Forward request</text>

  <!-- 3. Backend Server -->
  <rect x="270" y="250" width="260" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="272" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Backend Server (main.py)</text>
  <text x="400" y="288" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">FastAPI server orchestration</text>

  <!-- Arrow Backend Server -> PDF Parser -->
  <line x1="400" y1="305" x2="400" y2="375" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="340" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">3. Start analysis &amp; text extraction</text>

  <!-- Dashed boundary: Backend Processing Pipeline -->
  <rect x="150" y="355" width="500" height="495" fill="none" stroke="#555555" stroke-width="1.5" stroke-dasharray="6,4" />
  <text x="170" y="375" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" font-style="italic" fill="#555555">Backend Processing Pipeline</text>

  <!-- 4. PDF Parser -->
  <rect x="240" y="395" width="320" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="417" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">PDF Parser (pdf_parser.py)</text>
  <text x="400" y="433" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Extracts structured text via pymupdf4llm</text>

  <!-- Arrow PDF Parser -> Gemini API -->
  <line x1="400" y1="450" x2="400" y2="490" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="475" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">4. Extracted text</text>

  <!-- 5. Gemini API -->
  <rect x="240" y="490" width="320" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="512" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Gemini API (gemini_analyzer.py)</text>
  <text x="400" y="528" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Performs LLM-based analysis &amp; validation</text>

  <!-- Arrow Gemini API -> Scoring Module -->
  <line x1="400" y1="545" x2="400" y2="585" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="570" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">5. Raw analysis metadata</text>

  <!-- 6. Scoring Module -->
  <rect x="240" y="585" width="320" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="607" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Scoring Module (scoring.py)</text>
  <text x="400" y="623" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Computes research quality grades &amp; weighted scores</text>

  <!-- Arrow Scoring Module -> Citation Checker -->
  <line x1="400" y1="640" x2="400" y2="680" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="665" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">6. Quality metrics &amp; criteria</text>

  <!-- 7. Citation Checker -->
  <rect x="240" y="680" width="320" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="702" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Citation Checker (citation_checker.py)</text>
  <text x="400" y="718" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Verifies reference DOIs &amp; titles via APIs</text>

  <!-- Arrow Citation Checker -> Report Generator -->
  <line x1="400" y1="735" x2="400" y2="775" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="412" y="760" font-family="'Times New Roman', Times, serif" font-size="12px" fill="#000000">7. Validated citations &amp; references</text>

  <!-- 8. Report Generator -->
  <rect x="230" y="775" width="340" height="55" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="400" y="797" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Report Generator (report_generator.py)</text>
  <text x="400" y="813" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#555555">Assembles structured PDF report via ReportLab</text>

  <!-- Return Path flow -->
  <!-- 1. Line down from Report Generator bottom center -->
  <line x1="400" y1="830" x2="400" y2="895" stroke="#000000" stroke-width="1.5" />
  <!-- 2. Line left to X=80 -->
  <line x1="400" y1="895" x2="80" y2="895" stroke="#000000" stroke-width="1.5" />
  <!-- 3. Line up to Y=182.5 (middle of Web Interface box) -->
  <line x1="80" y1="895" x2="80" y2="182.5" stroke="#000000" stroke-width="1.5" />
  <!-- 4. Line right to Web Interface left border (X=270) -->
  <line x1="80" y1="182.5" x2="270" y2="182.5" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-return)" />

  <!-- Horizontal Label above the return path -->
  <text x="95" y="885" font-family="'Times New Roman', Times, serif" font-size="12px" font-weight="bold" fill="#000000">
    8. Return PDF Report (Delivered via Dashboard)
  </text>
</svg>
"""

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"SVG diagram successfully written to: {svg_path}")

    # --- 2. GENERATE PNG ---
    print("Generating PNG diagram...")
    img = Image.new("RGB", (800, 960), "white")
    draw = ImageDraw.Draw(img)

    # Font Setup
    try:
        font_bold = ImageFont.truetype("timesbd.ttf", 14)
        font_regular = ImageFont.truetype("times.ttf", 11)
        font_italic_bold = ImageFont.truetype("timesbi.ttf", 12)
        font_title = ImageFont.truetype("timesbd.ttf", 18)
    except IOError:
        try:
            font_bold = ImageFont.truetype("arialbd.ttf", 13)
            font_regular = ImageFont.truetype("arial.ttf", 10)
            font_italic_bold = ImageFont.truetype("arialbi.ttf", 11)
            font_title = ImageFont.truetype("arialbd.ttf", 16)
        except IOError:
            font_bold = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            font_italic_bold = ImageFont.load_default()
            font_title = ImageFont.load_default()

    # Draw Title
    t_bbox = draw.textbbox((0, 0), "ResearchSense — System Architecture Diagram", font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((400 - t_w / 2, 17), "ResearchSense — System Architecture Diagram", fill="black", font=font_title)

    # 1. User Box
    draw_box(draw, "User (Browser)", "Uploads PDF & Views Dashboard", 300, 60, 500, 115, font_bold, font_regular)
    draw_arrow_down(draw, 115, 155, label="1. Uploads PDF", label_font=font_regular)

    # 2. Web Interface Box
    draw_box(draw, "Web Interface (app.js)", "Dark-mode frontend dashboard", 270, 155, 530, 210, font_bold, font_regular)
    draw_arrow_down(draw, 210, 250, label="2. Forward request", label_font=font_regular)

    # 3. Backend Server Box
    draw_box(draw, "Backend Server (main.py)", "FastAPI server orchestration", 270, 250, 530, 305, font_bold, font_regular)
    draw_arrow_down(draw, 305, 375, label="3. Start analysis & text extraction", label_font=font_regular)

    # Dashed Boundary for Backend Processing Pipeline
    draw_dashed_rect(draw, 150, 355, 650, 850, dash_len=8, gap_len=6, width=2, color="gray")
    draw.text((170, 362), "Backend Processing Pipeline", fill="gray", font=font_italic_bold)

    # 4. PDF Parser Box
    draw_box(draw, "PDF Parser (pdf_parser.py)", "Extracts structured text via pymupdf4llm", 240, 395, 560, 450, font_bold, font_regular)
    draw_arrow_down(draw, 450, 490, label="4. Extracted text", label_font=font_regular)

    # 5. Gemini API Box
    draw_box(draw, "Gemini API (gemini_analyzer.py)", "Performs LLM-based analysis & validation", 240, 490, 560, 545, font_bold, font_regular)
    draw_arrow_down(draw, 545, 585, label="5. Raw analysis metadata", label_font=font_regular)

    # 6. Scoring Module Box
    draw_box(draw, "Scoring Module (scoring.py)", "Computes research quality grades & weighted scores", 240, 585, 560, 640, font_bold, font_regular)
    draw_arrow_down(draw, 640, 680, label="6. Quality metrics & criteria", label_font=font_regular)

    # 7. Citation Checker Box
    draw_box(draw, "Citation Checker (citation_checker.py)", "Verifies reference DOIs & titles via APIs", 240, 680, 560, 735, font_bold, font_regular)
    draw_arrow_down(draw, 735, 775, label="7. Validated citations & references", label_font=font_regular)

    # 8. Report Generator Box
    draw_box(draw, "Report Generator (report_generator.py)", "Assembles structured PDF report via ReportLab", 230, 775, 570, 830, font_bold, font_regular)

    # Draw Return Path
    # 1. Line down from Report Generator
    draw.line([(400, 830), (400, 895)], fill="black", width=2)
    # 2. Line left to X=80
    draw.line([(400, 895), (80, 895)], fill="black", width=2)
    # 3. Line up to Y=182.5 (middle of Web Interface box)
    draw.line([(80, 895), (80, 182.5)], fill="black", width=2)
    # 4. Line right to Web Interface left border (X=270)
    draw.line([(80, 182.5), (270, 182.5)], fill="black", width=2)
    
    # Draw Arrowhead pointing right at (270, 182.5)
    draw.polygon([(262, 177.5), (262, 187.5), (270, 182.5)], fill="black")

    # Add text label above the bottom return path
    draw.text((95, 878), "8. Return PDF Report (Delivered via Dashboard)", fill="black", font=font_bold)

    # Save PNG
    img.save(png_path, "PNG")
    print(f"PNG diagram successfully written to: {png_path}")
    print("Done!")

if __name__ == "__main__":
    main()
