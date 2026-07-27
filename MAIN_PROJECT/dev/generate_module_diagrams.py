import os
from PIL import Image, ImageDraw, ImageFont

def draw_arrow_head(draw, x, y, direction="down", color="black"):
    if direction == "down":
        draw.polygon([(x - 5, y - 8), (x + 5, y - 8), (x, y)], fill=color)
    elif direction == "up":
        draw.polygon([(x - 5, y + 8), (x + 5, y + 8), (x, y)], fill=color)
    elif direction == "left":
        draw.polygon([(x + 8, y - 5), (x + 8, y + 5), (x, y)], fill=color)
    elif direction == "right":
        draw.polygon([(x - 8, y - 5), (x - 8, y + 5), (x, y)], fill=color)

def draw_box(draw, title, subtext, left, top, right, bottom, font_bold, font_regular, fill_color="#f8fafc", border_color="#1e293b"):
    draw.rectangle([left + 2, top + 2, right + 2, bottom + 2], fill="#e2e8f0", outline=None)
    draw.rectangle([left, top, right, bottom], fill=fill_color, outline=border_color, width=2)
    box_w = right - left
    box_h = bottom - top
    
    t_bbox = draw.textbbox((0, 0), title, font=font_bold)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    
    if subtext:
        s_bbox = draw.textbbox((0, 0), subtext, font=font_regular)
        s_w = s_bbox[2] - s_bbox[0]
        s_h = s_bbox[3] - s_bbox[1]
        
        t_y = top + (box_h - (t_h + s_h + 4)) / 2
        t_x = left + (box_w - t_w) / 2
        s_y = t_y + t_h + 4
        s_x = left + (box_w - s_w) / 2
        
        draw.text((t_x, t_y), title, fill="#0f172a", font=font_bold)
        draw.text((s_x, s_y), subtext, fill="#475569", font=font_regular)
    else:
        t_y = top + (box_h - t_h) / 2
        t_x = left + (box_w - t_w) / 2
        draw.text((t_x, t_y), title, fill="#0f172a", font=font_bold)

def generate_text_compressor_diagram(docs_dir, font_bold, font_regular, font_title):
    # Diagram 1: text_compressor_flow (600 x 800)
    img = Image.new("RGB", (600, 800), "white")
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.rectangle([0, 0, 600, 60], fill="#0f172a")
    t_bbox = draw.textbbox((0, 0), "text_compressor.py — Processing Pipeline", font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((300 - t_w/2, 20), "text_compressor.py — Processing Pipeline", fill="white", font=font_title)
    
    # Flow
    draw_box(draw, "Input: Raw Sections Dictionary", "Abstract, Introduction, Methodology, Results, etc.", 120, 90, 480, 150, font_bold, font_regular, fill_color="#eff6ff")
    draw.line([(300, 150), (300, 190)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 300, 190, "down", color="#0284c7")
    
    draw_box(draw, "Stage 1: Basic Normalization", "Whitespace collapse, BOM cleanup, URLs -> [URL]\nCit. stripping ([1], Smith 2020), pure symbols drop", 100, 190, 500, 260, font_bold, font_regular)
    draw.line([(300, 260), (300, 300)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 300, 300, "down", color="#0284c7")
    
    draw_box(draw, "Stage 2: Sentence Deduplication", "Checks near-identical sentences within same section\n(Prevents loss of repetition across separate sections)", 100, 300, 500, 370, font_bold, font_regular)
    draw.line([(300, 370), (300, 410)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 300, 410, "down", color="#0284c7")
    
    draw_box(draw, "Stage 3: Boilerplate Removal", "Strips filler academic openings ('In this paper, we ...')\nKeep evidence pointers (Fig. 2) in Results/Discussion", 100, 410, 500, 480, font_bold, font_regular)
    draw.line([(300, 480), (300, 520)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 300, 520, "down", color="#0284c7")
    
    draw_box(draw, "Stage 4: Formula Stripping (Aggressive)", "Aggressive mode only: drops lines with <40% alpha chars\nAlways skipped for the results section", 100, 520, 500, 590, font_bold, font_regular)
    draw.line([(300, 590), (300, 630)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 300, 630, "down", color="#0284c7")
    
    draw_box(draw, "Output: Compressed Sections & Stats", "Shields methodology section, adds _compression_stats", 120, 630, 480, 690, font_bold, font_regular, fill_color="#ecfdf5")
    
    # Save PNG
    img.save(os.path.join(docs_dir, "text_compressor_flow.png"), "PNG")
    
    # Save SVG
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800" style="background-color:#ffffff;">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#0284c7" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#cbd5e1" flood-opacity="0.8"/>
    </filter>
  </defs>
  <rect x="0" y="0" width="600" height="60" fill="#0f172a" />
  <text x="300" y="37" text-anchor="middle" font-family="sans-serif" font-size="16px" font-weight="bold" fill="#ffffff">text_compressor.py — Processing Pipeline</text>
  
  <rect x="120" y="90" width="360" height="60" rx="4" ry="4" fill="#eff6ff" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="118" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Input: Raw Sections Dictionary</text>
  <text x="300" y="135" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Abstract, Introduction, Methodology, Results, etc.</text>
  
  <line x1="300" y1="150" x2="300" y2="190" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="100" y="190" width="400" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="218" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Stage 1: Basic Normalization</text>
  <text x="300" y="235" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Whitespace collapse, BOM cleanup, URLs -> [URL]</text>
  <text x="300" y="247" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Cit. stripping ([1], Smith 2020), pure symbols drop</text>
  
  <line x1="300" y1="260" x2="300" y2="300" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="100" y="300" width="400" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="328" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Stage 2: Sentence Deduplication</text>
  <text x="300" y="345" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Checks near-identical sentences within same section</text>
  <text x="300" y="357" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">(Prevents loss of repetition across separate sections)</text>
  
  <line x1="300" y1="370" x2="300" y2="410" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="100" y="410" width="400" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="438" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Stage 3: Boilerplate Removal</text>
  <text x="300" y="455" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Strips filler academic openings ('In this paper, we ...')</text>
  <text x="300" y="467" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Keep evidence pointers (Fig. 2) in Results/Discussion</text>
  
  <line x1="300" y1="480" x2="300" y2="520" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="100" y="520" width="400" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="548" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Stage 4: Formula Stripping (Aggressive)</text>
  <text x="300" y="565" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Aggressive mode only: drops lines with <40% alpha chars</text>
  <text x="300" y="577" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Always skipped for the results section</text>
  
  <line x1="300" y1="590" x2="300" y2="630" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="120" y="630" width="360" height="60" rx="4" ry="4" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)" />
  <text x="300" y="658" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Output: Compressed Sections &amp; Stats</text>
  <text x="300" y="675" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Shields methodology section, adds _compression_stats</text>
</svg>
"""
    with open(os.path.join(docs_dir, "text_compressor_flow.svg"), "w", encoding="utf-8") as f:
        f.write(svg_content)

def generate_scoring_diagram(docs_dir, font_bold, font_regular, font_title):
    # Diagram 2: scoring_flow (700 x 500)
    img = Image.new("RGB", (700, 500), "white")
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.rectangle([0, 0, 700, 60], fill="#0f172a")
    t_bbox = draw.textbbox((0, 0), "scoring.py — Adaptive Weighted Grade Engine", font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((350 - t_w/2, 20), "scoring.py — Adaptive Weighted Grade Engine", fill="white", font=font_title)
    
    # Layout
    draw_box(draw, "1. Input Layer Scores", "5 metric dimensions: scores (0-10)\nStructure, Clarity, Method, Evidence, Citations", 30, 100, 280, 170, font_bold, font_regular, fill_color="#eff6ff")
    draw.line([(280, 135), (320, 135)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 320, 135, "right", color="#0284c7")
    
    draw_box(draw, "2. Discipline Weights Mapping", "Resolves weights based on classified discipline\n(CS, Math, Physics, Bio/Med, Chem, Humanities)", 320, 100, 670, 170, font_bold, font_regular)
    
    draw.line([(500, 170), (500, 220)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 500, 220, "down", color="#0284c7")
    
    draw_box(draw, "3. Weighted Score Formula", "Weighted Sum: raw = sum(scores[k] * weights[k])\nFinal scaled: confidence_score = round(raw * 10, 1)", 200, 220, 600, 290, font_bold, font_regular)
    
    draw.line([(400, 290), (400, 340)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 400, 340, "down", color="#0284c7")
    
    draw_box(draw, "4. Grade Lookup Thresholds", "A (>=85), B (>=70), C (>=55), D (>=40), F (<40)", 50, 340, 380, 400, font_bold, font_regular)
    draw.line([(380, 370), (420, 370)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 420, 370, "right", color="#0284c7")
    
    draw_box(draw, "5. Response Payload", "final_score, grade, weights map, resolved discipline", 420, 340, 670, 400, font_bold, font_regular, fill_color="#ecfdf5")
    
    # Save PNG
    img.save(os.path.join(docs_dir, "scoring_flow.png"), "PNG")
    
    # Save SVG
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 500" width="700" height="500" style="background-color:#ffffff;">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#0284c7" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#cbd5e1" flood-opacity="0.8"/>
    </filter>
  </defs>
  <rect x="0" y="0" width="700" height="60" fill="#0f172a" />
  <text x="350" y="37" text-anchor="middle" font-family="sans-serif" font-size="16px" font-weight="bold" fill="#ffffff">scoring.py — Adaptive Weighted Grade Engine</text>
  
  <rect x="30" y="100" width="250" height="70" rx="4" ry="4" fill="#eff6ff" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <text x="155" y="128" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">1. Input Layer Scores</text>
  <text x="155" y="145" font-family="sans-serif" font-size="9px" text-anchor="middle" fill="#475569">5 metric dimensions: scores (0-10)</text>
  <text x="155" y="157" font-family="sans-serif" font-size="9px" text-anchor="middle" fill="#475569">Structure, Clarity, Method, Evidence, Citations</text>
  
  <line x1="280" y1="135" x2="320" y2="135" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="320" y="100" width="350" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="495" y="128" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">2. Discipline Weights Mapping</text>
  <text x="495" y="145" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Resolves weights based on classified discipline</text>
  <text x="495" y="157" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">(CS, Math, Physics, Bio/Med, Chem, Humanities)</text>
  
  <line x1="500" y1="170" x2="500" y2="220" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="200" y="220" width="400" height="70" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="400" y="248" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">3. Weighted Score Formula</text>
  <text x="400" y="265" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Weighted Sum: raw = sum(scores[k] * weights[k])</text>
  <text x="400" y="277" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Final scaled: confidence_score = round(raw * 10, 1)</text>
  
  <line x1="400" y1="290" x2="400" y2="340" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="50" y="340" width="330" height="60" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="215" y="368" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">4. Grade Lookup Thresholds</text>
  <text x="215" y="385" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">A (>=85), B (>=70), C (>=55), D (>=40), F (&lt;40)</text>
  
  <line x1="380" y1="370" x2="420" y2="370" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="420" y="340" width="250" height="60" rx="4" ry="4" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)" />
  <text x="545" y="368" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">5. Response Payload</text>
  <text x="545" y="385" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">final_score, grade, weights, discipline</text>
</svg>
"""
    with open(os.path.join(docs_dir, "scoring_flow.svg"), "w", encoding="utf-8") as f:
        f.write(svg_content)

def generate_report_diagram(docs_dir, font_bold, font_regular, font_title):
    # Diagram 3: report_generator_flow (800 x 600)
    img = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.rectangle([0, 0, 800, 60], fill="#0f172a")
    t_bbox = draw.textbbox((0, 0), "report_generator.py — PLATYPUS Hybrid Layout Engine", font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((400 - t_w/2, 20), "report_generator.py — PLATYPUS Hybrid Layout Engine", fill="white", font=font_title)
    
    # Layout
    draw_box(draw, "Input: Consolidated Analysis JSON Payload", "Contains layer scores, details, citations summaries, verdict, and discipline", 100, 90, 700, 150, font_bold, font_regular, fill_color="#eff6ff")
    
    draw.line([(400, 150), (400, 200)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 400, 200, "down", color="#0284c7")
    
    # Parallel split: Canvas cover page vs Platypus story
    draw.line([(400, 200), (220, 200)], fill="#0284c7", width=2)
    draw.line([(220, 200), (220, 230)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 220, 230, "down", color="#0284c7")
    
    draw.line([(400, 200), (580, 200)], fill="#0284c7", width=2)
    draw.line([(580, 200), (580, 230)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 580, 230, "down", color="#0284c7")
    
    draw_box(draw, "1. Canvas Callbacks (Background Layout)", "draw_cover(): Full-bleed cover page layout\n(navy base, low-alpha geometry, top gradients)\ndraw_footer(): Dynamic page numbers & footer string", 30, 230, 410, 320, font_bold, font_regular)
    
    draw_box(draw, "2. PLATYPUS Flowable Story Builder", "Sequentially appends elements to document story:\n- ScoreHero overall card, Section pills grid table\n- 2-column parameter scorecards with ProgressBars\n- Citation stats, flagged references, VerdictCard", 430, 230, 770, 320, font_bold, font_regular)
    
    # Merge
    draw.line([(220, 320), (220, 360)], fill="#0284c7", width=2)
    draw.line([(220, 360), (400, 360)], fill="#0284c7", width=2)
    draw.line([(580, 320), (580, 360)], fill="#0284c7", width=2)
    draw.line([(580, 360), (400, 360)], fill="#0284c7", width=2)
    draw.line([(400, 360), (400, 390)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 400, 390, "down", color="#0284c7")
    
    draw_box(draw, "3. Build BaseDocTemplate", "Sets margins, cover & content templates, coordinates PageTemplates", 150, 390, 650, 450, font_bold, font_regular)
    
    draw.line([(400, 450), (400, 490)], fill="#0284c7", width=2)
    draw_arrow_head(draw, 400, 490, "down", color="#0284c7")
    
    draw_box(draw, "Output: In-Memory BytesIO PDF Buffer", "Streams compiled report binary directly back to FastAPI /report endpoint", 100, 490, 700, 550, font_bold, font_regular, fill_color="#ecfdf5")
    
    # Save PNG
    img.save(os.path.join(docs_dir, "report_generator_flow.png"), "PNG")
    
    # Save SVG
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600" style="background-color:#ffffff;">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#0284c7" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#cbd5e1" flood-opacity="0.8"/>
    </filter>
  </defs>
  <rect x="0" y="0" width="800" height="60" fill="#0f172a" />
  <text x="400" y="37" text-anchor="middle" font-family="sans-serif" font-size="16px" font-weight="bold" fill="#ffffff">report_generator.py — PLATYPUS Hybrid Layout Engine</text>
  
  <rect x="100" y="90" width="600" height="60" rx="4" ry="4" fill="#eff6ff" stroke="#0284c7" stroke-width="2" filter="url(#shadow)" />
  <text x="400" y="118" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Input: Consolidated Analysis JSON Payload</text>
  <text x="400" y="135" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Contains layer scores, details, citations summaries, verdict, and discipline</text>
  
  <line x1="400" y1="150" x2="400" y2="200" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <path d="M 400 200 L 220 200 L 220 230" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  <path d="M 400 200 L 580 200 L 580 230" fill="none" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="30" y="230" width="380" height="90" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="220" y="255" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">1. Canvas Callbacks (Background Layout)</text>
  <text x="220" y="275" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">draw_cover(): Full-bleed cover page layout</text>
  <text x="220" y="287" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">(navy base, low-alpha geometry, top gradients)</text>
  <text x="220" y="299" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">draw_footer(): Dynamic page numbers &amp; footer string</text>
  
  <rect x="430" y="230" width="340" height="90" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="600" y="255" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">2. PLATYPUS Flowable Story Builder</text>
  <text x="600" y="275" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Sequentially appends elements to document story:</text>
  <text x="600" y="287" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">- ScoreHero overall card, Section pills grid table</text>
  <text x="600" y="299" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">- 2-column parameter scorecards, citations tables, VerdictCard</text>
  
  <path d="M 220 320 L 220 360 L 400 360" fill="none" stroke="#0284c7" stroke-width="2" />
  <path d="M 580 320 L 580 360 L 400 360" fill="none" stroke="#0284c7" stroke-width="2" />
  <line x1="400" y1="360" x2="400" y2="390" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="150" y="390" width="500" height="60" rx="4" ry="4" fill="#f8fafc" stroke="#1e293b" stroke-width="2" filter="url(#shadow)" />
  <text x="400" y="418" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">3. Build BaseDocTemplate</text>
  <text x="400" y="435" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Sets margins, cover &amp; content templates, coordinates PageTemplates</text>
  
  <line x1="400" y1="450" x2="400" y2="490" stroke="#0284c7" stroke-width="2" marker-end="url(#arrow)" />
  
  <rect x="100" y="490" width="600" height="60" rx="4" ry="4" fill="#ecfdf5" stroke="#10b981" stroke-width="2" filter="url(#shadow)" />
  <text x="400" y="518" font-family="sans-serif" font-size="13px" font-weight="bold" text-anchor="middle" fill="#0f172a">Output: In-Memory BytesIO PDF Buffer</text>
  <text x="400" y="535" font-family="sans-serif" font-size="10px" text-anchor="middle" fill="#475569">Streams compiled report binary directly back to FastAPI /report endpoint</text>
</svg>
"""
    with open(os.path.join(docs_dir, "report_generator_flow.svg"), "w", encoding="utf-8") as f:
        f.write(svg_content)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)
    docs_dir = os.path.join(workspace_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Font setup
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 13)
        font_regular = ImageFont.truetype("arial.ttf", 10)
        font_title = ImageFont.truetype("arialbd.ttf", 16)
    except IOError:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_title = ImageFont.load_default()
        
    print("Generating text_compressor diagram...")
    generate_text_compressor_diagram(docs_dir, font_bold, font_regular, font_title)
    
    print("Generating scoring diagram...")
    generate_scoring_diagram(docs_dir, font_bold, font_regular, font_title)
    
    print("Generating report_generator diagram...")
    generate_report_diagram(docs_dir, font_bold, font_regular, font_title)
    
    print("All module diagrams successfully generated in docs/ folder!")

if __name__ == "__main__":
    main()
