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
    
    t_bbox = draw.textbbox((0, 0), name, font=font_bold)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    
    if subtext:
        s_bbox = draw.textbbox((0, 0), subtext, font=font_regular)
        s_w = s_bbox[2] - s_bbox[0]
        s_h = s_bbox[3] - s_bbox[1]
        
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

def draw_arrow_head(draw, x, y, direction="down", color="black"):
    if direction == "down":
        draw.polygon([(x - 5, y - 8), (x + 5, y - 8), (x, y)], fill=color)
    elif direction == "up":
        draw.polygon([(x - 5, y + 8), (x + 5, y + 8), (x, y)], fill=color)
    elif direction == "left":
        draw.polygon([(x + 8, y - 5), (x + 8, y + 5), (x, y)], fill=color)
    elif direction == "right":
        draw.polygon([(x - 8, y - 5), (x - 8, y + 5), (x, y)], fill=color)

def draw_horizontal_arrow_with_label(draw, start_x, end_x, y, label, font, color="black"):
    draw.line([(start_x, y), (end_x, y)], fill=color, width=2)
    draw_arrow_head(draw, end_x, y, "right", color)
    lbl_bbox = draw.textbbox((0, 0), label, font=font)
    lbl_w = lbl_bbox[2] - lbl_bbox[0]
    lbl_h = lbl_bbox[3] - lbl_bbox[1]
    draw.text((start_x + (end_x - start_x)/2 - lbl_w/2, y - lbl_h - 6), label, fill=color, font=font)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    
    svg_path = os.path.join(workspace_root, "system_architecture_v2.svg")
    png_path = os.path.join(workspace_root, "system_architecture_v2.png")
    
    # --- 1. GENERATE SVG ---
    print("Generating SVG diagram...")
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 750" width="1300" height="750" style="background-color:#ffffff;">
  <!-- Definitions for Markers (Arrowheads) -->
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#000000" />
    </marker>
  </defs>

  <!-- Title of the Diagram -->
  <text x="650" y="25" text-anchor="middle" font-family="'Times New Roman', Times, serif" font-size="18px" font-weight="bold" fill="#000000">
    ResearchSense — System Architecture Diagram
  </text>
  
  <!-- 1. Actor: User (Browser) -->
  <rect x="550" y="40" width="200" height="50" rx="4" ry="4" fill="#fcfcfc" stroke="#000000" stroke-width="1.5" />
  <text x="650" y="69" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">User (Browser)</text>

  <!-- Arrow User -> Client-Side Box -->
  <line x1="650" y1="90" x2="650" y2="140" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="658" y="120" font-family="'Times New Roman', Times, serif" font-size="11px" fill="#000000">Interact with Dashboard</text>

  <!-- 2. Client-Side Web Application Outer Box -->
  <rect x="370" y="140" width="560" height="90" rx="4" ry="4" fill="#fafafa" stroke="#000000" stroke-width="1.5" />
  <text x="650" y="160" font-family="'Times New Roman', Times, serif" font-size="12px" font-weight="bold" text-anchor="middle" fill="#000000">Client-Side Web Application (vanilla JS, app.js, dark-mode UI)</text>

  <!-- Nested: Upload Interface -->
  <rect x="400" y="175" width="200" height="45" rx="3" ry="3" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
  <text x="500" y="202" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Upload Interface</text>

  <!-- Nested: Report Dashboard / Viewer -->
  <rect x="680" y="175" width="220" height="45" rx="3" ry="3" fill="#ffffff" stroke="#000000" stroke-width="1.2" />
  <text x="790" y="202" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Report Dashboard / Viewer</text>

  <!-- Arrow Upload Interface -> PDF Parser (via pipeline entry) -->
  <path d="M 500 220 L 500 260 L 132.5 260 L 132.5 420" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="316" y="252" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Upload PDF</text>

  <!-- 3. Backend Processing Server Dashed Box -->
  <rect x="40" y="290" width="1230" height="300" fill="none" stroke="#555555" stroke-width="1.5" stroke-dasharray="6,4" />
  <text x="60" y="315" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" font-style="italic" fill="#555555">Backend Processing Server (main.py / run_local.py)</text>

  <!-- 3.1 PDF Parser -->
  <rect x="60" y="420" width="145" height="60" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="132.5" y="447" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">PDF Parser</text>
  <text x="132.5" y="463" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(pdf_parser.py / pymupdf4llm)</text>

  <!-- Arrow PDF Parser -> Gemini Analyzer -->
  <line x1="205" y1="450" x2="315" y2="450" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="260" y="440" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Extract Text</text>

  <!-- 3.2 Gemini Analyzer -->
  <rect x="315" y="420" width="145" height="60" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="387.5" y="447" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Gemini Analyzer</text>
  <text x="387.5" y="463" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(gemini_analyzer.py / API)</text>

  <!-- Arrow Gemini Analyzer -> Scoring Engine -->
  <line x1="460" y1="450" x2="570" y2="450" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="515" y="440" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">API Call</text>

  <!-- 3.3 Scoring Engine -->
  <rect x="570" y="420" width="145" height="60" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="642.5" y="447" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Scoring Engine</text>
  <text x="642.5" y="463" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(scoring.py)</text>

  <!-- Arrow Scoring Engine -> Citation Checker -->
  <line x1="715" y1="450" x2="825" y2="450" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="770" y="440" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Return Analysis</text>

  <!-- 3.4 Citation Checker -->
  <rect x="825" y="420" width="145" height="60" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="897.5" y="447" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Citation Checker</text>
  <text x="897.5" y="463" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(citation_checker.py)</text>

  <!-- Arrow Citation Checker -> Report Generator -->
  <line x1="970" y1="450" x2="1080" y2="450" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="1025" y="440" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Verify References</text>

  <!-- 3.5 Report Generator -->
  <rect x="1080" y="420" width="170" height="60" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="1165" y="447" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">Report Generator</text>
  <text x="1165" y="463" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(report_generator.py / PLATYPUS)</text>

  <!-- 3.6 JSON Cache Store -->
  <rect x="550" y="515" width="200" height="50" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="650" y="538" font-family="'Times New Roman', Times, serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#000000">JSON Cache Store</text>
  <text x="650" y="552" font-family="'Times New Roman', Times, serif" font-size="10px" text-anchor="middle" fill="#555555">(Local File Cache)</text>

  <!-- Bidirectional Connection PDF Parser <-> Cache Store -->
  <path d="M 132.5 480 L 132.5 540 L 550 540" fill="none" stroke="#000000" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
  <text x="341.25" y="533" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Hash-keyed cache lookup / write</text>

  <!-- Bidirectional Connection Report Generator <-> Cache Store -->
  <path d="M 1165 480 L 1165 540 L 750 540" fill="none" stroke="#000000" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
  <text x="957.5" y="533" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Hash-keyed cache lookup / write</text>

  <!-- 4. Generated PDF Report Box -->
  <rect x="530" y="640" width="240" height="50" rx="4" ry="4" fill="#ffffff" stroke="#000000" stroke-width="1.5" />
  <text x="650" y="669" font-family="'Times New Roman', Times, serif" font-size="14px" font-weight="bold" text-anchor="middle" fill="#000000">Generated PDF Report</text>

  <!-- Arrow Report Generator -> Generated PDF Report -->
  <path d="M 1165 480 L 1165 665 L 770 665" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="967.5" y="658" font-family="'Times New Roman', Times, serif" font-size="11px" text-anchor="middle" fill="#000000">Build Report</text>

  <!-- Return Path Generated PDF Report -> User (Browser) -->
  <path d="M 530 665 L 20 665 L 20 65 L 550 65" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)" />
  <text x="285" y="58" font-family="'Times New Roman', Times, serif" font-size="12px" font-weight="bold" text-anchor="middle" fill="#000000">Download Report</text>
</svg>
"""

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"SVG diagram successfully written to: {svg_path}")

    # --- 2. GENERATE PNG ---
    print("Generating PNG diagram...")
    img = Image.new("RGB", (1300, 750), "white")
    draw = ImageDraw.Draw(img)

    # Font Setup
    try:
        font_bold = ImageFont.truetype("timesbd.ttf", 13)
        font_regular = ImageFont.truetype("times.ttf", 11)
        font_italic_bold = ImageFont.truetype("timesbi.ttf", 12)
        font_title = ImageFont.truetype("timesbd.ttf", 18)
    except IOError:
        try:
            font_bold = ImageFont.truetype("arialbd.ttf", 12)
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
    draw.text((650 - t_w / 2, 17), "ResearchSense — System Architecture Diagram", fill="black", font=font_title)

    # 1. User Box
    draw_box(draw, "User (Browser)", None, 550, 40, 750, 90, font_bold, font_regular)
    
    # Arrow User -> Client-Side Web Application
    draw.line([(650, 90), (650, 140)], fill="black", width=2)
    draw_arrow_head(draw, 650, 140, "down")
    draw.text((658, 107), "Interact with Dashboard", fill="black", font=font_regular)

    # 2. Client-Side Web Application Box
    draw.rectangle([370, 140, 930, 230], fill="#fafafa", outline="black", width=2)
    outer_lbl = "Client-Side Web Application (vanilla JS, app.js, dark-mode UI)"
    lbl_bbox = draw.textbbox((0, 0), outer_lbl, font=font_regular)
    lbl_w = lbl_bbox[2] - lbl_bbox[0]
    draw.text((650 - lbl_w / 2, 148), outer_lbl, fill="black", font=font_regular)

    # Inner boxes
    draw_box(draw, "Upload Interface", None, 400, 175, 600, 220, font_bold, font_regular)
    draw_box(draw, "Report Dashboard / Viewer", None, 680, 175, 900, 220, font_bold, font_regular)

    # Arrow Upload Interface -> PDF Parser
    draw.line([(500, 220), (500, 260)], fill="black", width=2)
    draw.line([(500, 260), (132.5, 260)], fill="black", width=2)
    draw.line([(132.5, 260), (132.5, 420)], fill="black", width=2)
    draw_arrow_head(draw, 132.5, 420, "down")
    draw.text((316, 245), "Upload PDF", fill="black", font=font_regular, anchor="mm")

    # 3. Dashed boundary for Backend Processing Server
    draw_dashed_rect(draw, 40, 290, 1270, 590, dash_len=8, gap_len=6, width=2, color="gray")
    draw.text((60, 303), "Backend Processing Server (main.py / run_local.py)", fill="gray", font=font_italic_bold)

    # 3.1 PDF Parser Box
    draw_box(draw, "PDF Parser", "(pdf_parser.py / pymupdf4llm)", 60, 420, 205, 480, font_bold, font_regular)

    # Arrow PDF Parser -> Gemini Analyzer
    draw_horizontal_arrow_with_label(draw, 205, 315, 450, "Extract Text", font_regular)

    # 3.2 Gemini Analyzer Box
    draw_box(draw, "Gemini Analyzer", "(gemini_analyzer.py / API)", 315, 420, 460, 480, font_bold, font_regular)

    # Arrow Gemini Analyzer -> Scoring Engine
    draw_horizontal_arrow_with_label(draw, 460, 570, 450, "API Call", font_regular)

    # 3.3 Scoring Engine Box
    draw_box(draw, "Scoring Engine", "(scoring.py)", 570, 420, 715, 480, font_bold, font_regular)

    # Arrow Scoring Engine -> Citation Checker
    draw_horizontal_arrow_with_label(draw, 715, 825, 450, "Return Analysis", font_regular)

    # 3.4 Citation Checker Box
    draw_box(draw, "Citation Checker", "(citation_checker.py)", 825, 420, 970, 480, font_bold, font_regular)

    # Arrow Citation Checker -> Report Generator
    draw_horizontal_arrow_with_label(draw, 970, 1080, 450, "Verify References", font_regular)

    # 3.5 Report Generator Box
    draw_box(draw, "Report Generator", "(report_generator.py / PLATYPUS)", 1080, 420, 1250, 480, font_bold, font_regular)

    # 3.6 JSON Cache Store Box
    draw_box(draw, "JSON Cache Store", "(Local File Cache)", 550, 515, 750, 565, font_bold, font_regular)

    # Bidirectional PDF Parser <-> Cache Store
    draw.line([(132.5, 480), (132.5, 540)], fill="black", width=2)
    draw.line([(132.5, 540), (550, 540)], fill="black", width=2)
    draw_arrow_head(draw, 132.5, 480, "up")
    draw_arrow_head(draw, 550, 540, "right")
    draw.text((341.25, 525), "Hash-keyed cache lookup / write", fill="black", font=font_regular, anchor="mm")

    # Bidirectional Report Generator <-> Cache Store
    draw.line([(1165, 480), (1165, 540)], fill="black", width=2)
    draw.line([(1165, 540), (750, 540)], fill="black", width=2)
    draw_arrow_head(draw, 1165, 480, "up")
    draw_arrow_head(draw, 750, 540, "left")
    draw.text((957.5, 525), "Hash-keyed cache lookup / write", fill="black", font=font_regular, anchor="mm")

    # 4. Generated PDF Report Box
    draw_box(draw, "Generated PDF Report", None, 530, 640, 770, 690, font_bold, font_regular)

    # Arrow Report Generator -> Generated PDF Report
    draw.line([(1165, 480), (1165, 665)], fill="black", width=2)
    draw.line([(1165, 665), (770, 665)], fill="black", width=2)
    draw_arrow_head(draw, 770, 665, "left")
    draw.text((967.5, 650), "Build Report", fill="black", font=font_regular, anchor="mm")

    # Return Path: Generated PDF Report -> User (Browser)
    draw.line([(530, 665), (20, 665)], fill="black", width=2)
    draw.line([(20, 665), (20, 65)], fill="black", width=2)
    draw.line([(20, 65), (550, 65)], fill="black", width=2)
    draw_arrow_head(draw, 550, 65, "right")
    
    # Label on return path
    draw.text((285, 45), "Download Report", fill="black", font=font_bold, anchor="mm")

    # Save PNG
    img.save(png_path, "PNG")
    print(f"PNG diagram successfully written to: {png_path}")
    print("Done!")

if __name__ == "__main__":
    main()
