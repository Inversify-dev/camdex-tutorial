"""
Tutorial PDF Generator Engine for Camdex Education.
Matches the exact structure, styling, colors, watermark, and branding of Camdex Education publications.
Supports MCQs, Structured Questions, Multi-paragraph Reading Passages, Tables, Diagrams, Dotted Lines,
Raw Document (.pdf / .docx) Importing with automatic diagram extraction, and Past Paper Stamping.
"""

import io
import os
import re
from PIL import Image

import pymupdf as fitz
try:
    import docx
except ImportError:
    docx = None

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether,
    Table, TableStyle, Image as PlatypusImage, HRFlowable, Flowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# Page dimensions (Letter standard matching reference 612x792 pt)
PAGE_WIDTH, PAGE_HEIGHT = 612.0, 792.0
CONTENT_WIDTH = 504.0  # 612 - 54*2


class DottedAnswerLine(Flowable):
    """
    Draws a uniform, dark CAMDEX Deep Royal Blue vector dotted answer line
    from left_indent extending fully to the right content margin (availWidth).
    Optionally draws right-aligned mark brackets (e.g. '[1]', '[2]', '[Total: 10]').
    """
    def __init__(self, left_indent=24.0, height=16.5, color=None, mark=None, mark_font="Times-Bold", mark_size=10.5):
        super().__init__()
        self.left_indent = float(left_indent)
        self.height = float(height)
        self.color = color or colors.HexColor("#1A4199")
        self.mark = mark
        self.mark_font = mark_font
        self.mark_size = float(mark_size)

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        
        y = 4.0
        x_start = self.left_indent
        x_end = self.width
        
        if self.mark:
            c.setFont(self.mark_font, self.mark_size)
            c.setFillColor(self.color)
            mark_text = str(self.mark).strip()
            mark_w = c.stringWidth(mark_text, self.mark_font, self.mark_size)
            c.drawString(self.width - mark_w, y - 2.0, mark_text)
            x_end = self.width - mark_w - 8.0
            
        if x_end > x_start:
            c.setStrokeColor(self.color)
            c.setLineWidth(0.85)
            c.setDash([1.2, 3.0])
            c.line(x_start, y, x_end, y)
            
        c.restoreState()


class NumberedDottedAnswerLine(Flowable):
    """
    Draws a number label (e.g., '1.', '2.', '(a)') followed by the dark vector dotted rule
    reaching the right margin, with optional right-aligned mark.
    """
    def __init__(self, num_str="1.", left_indent=24.0, height=16.5, color=None, mark=None, mark_font="Times-Bold", mark_size=10.5):
        super().__init__()
        self.num_str = str(num_str).strip()
        self.left_indent = float(left_indent)
        self.height = float(height)
        self.color = color or colors.HexColor("#1A4199")
        self.mark = mark
        self.mark_font = mark_font
        self.mark_size = float(mark_size)

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        
        y = 4.0
        c.setFont(self.mark_font, self.mark_size)
        c.setFillColor(self.color)
        
        c.drawString(self.left_indent, y - 2.0, self.num_str)
        num_w = c.stringWidth(self.num_str, self.mark_font, self.mark_size)
        
        x_start = self.left_indent + num_w + 6.0
        x_end = self.width
        
        if self.mark:
            mark_text = str(self.mark).strip()
            mark_w = c.stringWidth(mark_text, self.mark_font, self.mark_size)
            c.drawString(self.width - mark_w, y - 2.0, mark_text)
            x_end = self.width - mark_w - 8.0
            
        if x_end > x_start:
            c.setStrokeColor(self.color)
            c.setLineWidth(0.85)
            c.setDash([1.2, 3.0])
            c.line(x_start, y, x_end, y)
            
        c.restoreState()


# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
COVERS_DIR = os.path.join(ASSETS_DIR, "covers")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")
DEFAULTS_DIR = os.path.join(ASSETS_DIR, "defaults")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# Register custom typography: Bebas Neue and Poppins
try:
    bebas_path = os.path.join(FONTS_DIR, "BebasNeue.ttf")
    if os.path.exists(bebas_path):
        pdfmetrics.registerFont(TTFont("BebasNeue", bebas_path))

    poppins_reg = os.path.join(FONTS_DIR, "Poppins-Regular.ttf")
    poppins_bold = os.path.join(FONTS_DIR, "Poppins-Bold.ttf")
    poppins_semi = os.path.join(FONTS_DIR, "Poppins-SemiBold.ttf")

    if os.path.exists(poppins_reg):
        pdfmetrics.registerFont(TTFont("Poppins", poppins_reg))
    if os.path.exists(poppins_bold):
        pdfmetrics.registerFont(TTFont("Poppins-Bold", poppins_bold))
    if os.path.exists(poppins_semi):
        pdfmetrics.registerFont(TTFont("Poppins-SemiBold", poppins_semi))

    if os.path.exists(poppins_reg) and os.path.exists(poppins_bold):
        registerFontFamily(
            "Poppins",
            normal="Poppins",
            bold="Poppins-Bold",
            italic="Poppins",
            boldItalic="Poppins-Bold"
        )
except Exception:
    pass

# Exact Camdex Reference Brand Colors
COLOR_PRIMARY = colors.HexColor("#1A4199")     # Exact Camdex Deep Royal Blue
COLOR_SECONDARY = colors.HexColor("#3154A4")   # Header Accent Blue
COLOR_DARK = colors.HexColor("#1A4199")        # Question Text Color
COLOR_MUTED = colors.HexColor("#555555")       # Gray subtitle
COLOR_BORDER = colors.HexColor("#CBD5E1")      # Table border
COLOR_TABLE_HEADER = colors.HexColor("#EBF1FA")# Table header background
COLOR_DOTS = colors.HexColor("#6B8ECF")        # Clean exam dotted line blue

# Subject to Cover File Mapping
SUBJECT_COVER_MAP = {
    ("Accounting", "CMB"): "Accounting CMB.png",
    ("Accounting", "EDX"): "Accounting EDX.png",
    ("Biology", "CMB"): "Biology CMB.png",
    ("Biology", "EDX"): "Biology EDX.png",
    ("Business", "CMB"): "Business CMB.png",
    ("Business", "EDX"): "Business EDX.png",
    ("Chemistry", "CMB"): "Chemistry CMB.png",
    ("Chemistry", "EDX"): "Chemistry EDX.png",
    ("Computer Science", "CMB"): "Computer Science CMB.png",
    ("Computer Science", "EDX"): "Computer Science EDX.png",
    ("Economics", "CMB"): "Economics CMB.png",
    ("Economics", "EDX"): "Economics EDX.png",
    ("English", "CMB"): "English CMB cover.png",
    ("English", "EDX"): "English EDX.png",
    ("ICT", "CMB"): "ICT CMB.png",
    ("ICT", "EDX"): "ICT EDX.png",
    ("Mathematics", "CMB"): "Mathematics CMB.png",
    ("Mathematics", "EDX"): "Mathematics EDX.png",
    ("Physics", "CMB"): "Physics CMB.png",
    ("Physics", "EDX"): "Physics EDX.png",
    ("Science", "CMB"): "Science CMB.png",
    ("Science", "EDX"): "Science EDX.png",
}

def sanitize_and_escape(text):
    """
    Cleans unicode artifacts, Word/PDF smart characters, and escapes XML entities.
    Prevents black rectangle / missing glyph rendering in ReportLab.
    """
    if text is None:
        return ""
    text = str(text)
    
    # 1. Escape XML characters
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Map smart punctuation, symbols, and artifacts to safe representations
    replacements = {
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2013': '&ndash;',
        '\u2014': '&mdash;',
        '\u2026': '...',
        '\u2022': '&bull;',
        '\u25aa': '&bull;',
        '\u25cf': '&bull;',
        '\u25cb': '&bull;',
        '\u25a0': '&bull;',
        '\uf0b4': '',
        '\uf0d8': '',
        '\uf0a7': '',
        '\xa0': ' ',
        '°': '&deg;',
        '±': '&plusmn;',
        '²': '<sup>2</sup>',
        '³': '<sup>3</sup>',
        '×': '&times;',
        '÷': '&divide;',
        '→': '&rarr;',
        '←': '&larr;',
        '↔': '&harr;',
        '≤': '&le;',
        '≥': '&ge;',
        '≠': '&ne;',
        'µ': '&mu;',
        'Ω': '&#937;',
        'λ': '&#955;',
        'π': '&#960;',
        '–': '&ndash;',
        '—': '&mdash;',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    return text

def format_subscripts(text):
    """
    Format common CS/Math/Science subscripts such as CO_2, H_2O, 26_10, 3F_16, 101101_2, or explicit _sub / ^sup.
    """
    if not text:
        return ""
    text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
    text = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', text)
    text = re.sub(r'\_([0-9a-zA-Z]+)', r'<sub>\1</sub>', text)
    text = re.sub(r'\^([0-9a-zA-Z]+)', r'<sup>\1</sup>', text)
    
    # Also handle patterns like 26(10) -> 26_10
    text = re.sub(r'\(10\)', r'<sub>10</sub>', text)
    text = re.sub(r'\(16\)', r'<sub>16</sub>', text)
    text = re.sub(r'\(2\)', r'<sub>2</sub>', text)
    return text

def clean_xml_text(text):
    """Convenience helper combining sanitization, XML escaping, and subscript formatting."""
    return format_subscripts(sanitize_and_escape(text))

def format_marks_in_text(text):
    """
    Detects trailing marks like [1], [2], [Total: 10] or (2 marks).
    Returns (cleaned_text, mark_html or None).
    """
    m = re.search(r'(\[(?:\d+|Total:\s*\d+)\]|\(\d+\s*marks?\))\s*$', text, re.IGNORECASE)
    if m:
        mark_str = m.group(1)
        base_text = text[:m.start()].strip()
        return base_text, mark_str
    return text, None

def parse_markdown_table(table_lines):
    """Parses a markdown or pipe-delimited table into a list of row lists."""
    rows = []
    for line in table_lines:
        line = line.strip()
        if not line:
            continue
        # Skip separator line like |---|---|
        if re.match(r'^\|?[\s\-:|]+\|?$', line):
            continue
        cells = [c.strip() for c in line.split('|')]
        if line.startswith('|') and cells and cells[0] == '':
            cells = cells[1:]
        if line.endswith('|') and cells and cells[-1] == '':
            cells = cells[:-1]
        if cells:
            rows.append(cells)
    return rows

def parse_input_text(raw_text):
    """
    Intelligently parses pasted text into structured questions, MCQs,
    reading comprehension passages, tables, diagrams, and marks.
    Preserves all paragraphs and merges hard-wrapped lines cleanly.
    """
    lines = raw_text.splitlines()
    blocks = []
    current_q = None
    current_sec = "MCQs"
    
    table_buffer = []
    
    meta_title = None
    meta_unit = None
    meta_tutorial = None

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            if current_q is not None:
                current_q["elements"].append({"type": "table", "rows": list(table_buffer)})
            else:
                blocks.append({"type": "table", "rows": list(table_buffer)})
            table_buffer = []

    for raw_line in lines:
        line = raw_line.strip()
        
        # Check for Markdown/Pipe Table line
        if '|' in line and (line.startswith('|') or line.endswith('|') or line.count('|') >= 2):
            table_buffer.append(line)
            continue
        else:
            flush_table()

        if not line:
            continue

        low = line.lower()

        # Metadata detection
        if low.startswith("title:"):
            meta_title = line.split(":", 1)[1].strip()
            continue
        if low.startswith("unit:"):
            meta_unit = line.split(":", 1)[1].strip()
            continue
        if low.startswith("tutorial:"):
            meta_tutorial = line.split(":", 1)[1].strip()
            continue
        if low.startswith("cambridge igcse") or low.startswith("edexcel igcse") or low.startswith("cambridge o/l") or low.startswith("cambridge a/l"):
            meta_title = meta_title or line
            continue
        if (low.startswith("unit ") or low.startswith("unit:")) and not meta_unit:
            meta_unit = line.split(":", 1)[-1].strip()
            continue
        if (low.startswith("tutorial ") or low.startswith("tutorial:")) and not meta_tutorial:
            meta_tutorial = line
            continue

        # Section headers
        if low in ("mcqs", "multiple choice questions", "section a: mcqs", "section a"):
            current_sec = "MCQs"
            blocks.append({"type": "section_header", "title": "MCQs"})
            continue
        if low.startswith("structured questions") or low.startswith("section b"):
            current_sec = "Structured"
            blocks.append({"type": "section_header", "title": "Structured Questions:"})
            continue

        # Check for Diagram / Image tag
        img_match = re.match(r'^\[(?:diagram|image|fig|figure)\s*(?::\s*|\s+)?([^\]]*)\]', line, re.IGNORECASE)
        md_img_match = re.match(r'^!\[(.*?)\]\((.*?)\)', line)
        if img_match or md_img_match:
            img_ref = img_match.group(1).strip() if img_match else md_img_match.group(2).strip()
            caption = md_img_match.group(1).strip() if md_img_match else ""
            if current_q:
                current_q["elements"].append({"type": "image", "ref": img_ref, "caption": caption})
            else:
                blocks.append({"type": "image", "ref": img_ref, "caption": caption})
            continue

        # Check for Question Start (e.g. "1. What is..." or "41. Zafer and Robert...")
        # Guard against IP addresses (e.g. 192.169.0.3) and decimals (e.g. 3.14)
        is_question_start = False
        q_num = None
        q_text = ""

        if not re.match(r'^\d+\.\d+', line):
            qm = re.match(r"^(?:(?:Q|Question)\s*)?(\d+)[\.\)]\s*(.*)$", line, re.IGNORECASE)
            qm2 = None
            if not qm and re.match(r"^(\d+)\s+([A-Z].*)$", line) and len(line) > 15:
                qm2 = re.match(r"^(\d+)\s+([A-Z].*)$", line)

            if qm:
                num = int(qm.group(1))
                text = qm.group(2).strip()
                # If in structured mode and looks like a subpart answer line e.g. 1. .......... do not treat as new question
                if current_q and current_sec == "Structured" and (text.startswith("...") or "..." in text or len(text) < 4):
                    is_question_start = False
                else:
                    is_question_start = True
                    q_num = num
                    q_text = text
            elif qm2:
                is_question_start = True
                q_num = int(qm2.group(1))
                q_text = qm2.group(2).strip()

        if is_question_start:
            current_q = {
                "type": "question",
                "q_type": "mcq" if current_sec == "MCQs" else "structured",
                "section": current_sec,
                "number": q_num,
                "text": q_text,
                "options": [],
                "elements": []
            }
            blocks.append(current_q)
            continue

        # Check for MCQ Option (e.g. "A. Option" or "B) Option")
        om = re.match(r"^\(?([A-D])[\.\)]\s+(.*)$", line)
        if om and current_q and current_q["q_type"] == "mcq":
            opt_letter = om.group(1).upper()
            opt_text = om.group(2).strip()
            current_q["options"].append((opt_letter, opt_text))
            continue

        # Check for Subpart (e.g. "a. ...", "(a) ...", "b) ...", "(i) ...", "ii. ...")
        sm = re.match(r"^(?:\(([a-z]|[ivx]+)\)|([a-z]|[ivx]+)[\.\)])\s+(.*)$", line, re.IGNORECASE)

        # If we have an active question
        if current_q:
            # If line is a Subpart:
            if sm:
                lbl = sm.group(1) or sm.group(2)
                stext = sm.group(3).strip()
                current_q["elements"].append({"type": "subpart", "label": lbl, "text": stext})
                continue

            # Passage Header e.g. "Text C: Our big red bus ride"
            if re.match(r"^(?:Text|Source|Passage|Case Study)\s+[A-Z0-9]:", line, re.IGNORECASE):
                current_q["elements"].append({"type": "passage_header", "text": line})
                continue

            # Sub-item e.g. "1. ...", "2. ..." (guard against IP addresses)
            nm = re.match(r"^(\d+)[\.\)]\s*(.*)$", line) if not re.match(r'^\d+\.\d+', line) else None
            if nm and (current_q["elements"] or current_sec == "Structured"):
                current_q["elements"].append({"type": "sub_item", "num": nm.group(1), "text": nm.group(2).strip()})
                continue

            # Bullet point e.g. "• ethical hacking" or "- point"
            if line.startswith(("•", "-", "*", "▪", "–")):
                bullet_text = line.lstrip("•-*▪– ").strip()
                current_q["elements"].append({"type": "bullet", "text": bullet_text})
                continue

            # Total Marks e.g. "[Total: 10]"
            if re.match(r"^\[Total:\s*\d+\]", line, re.IGNORECASE):
                current_q["elements"].append({"type": "total_marks", "text": line})
                continue

            # Dotted answer line
            if line.startswith("...") or line.startswith("___") or "..." in line:
                current_q["elements"].append({"type": "dotted_line", "text": line})
                continue

            # Figure Caption
            if re.match(r"^(?:Fig\.|Figure)\s*\d+.*", line, re.IGNORECASE):
                current_q["elements"].append({"type": "figure_caption", "text": line})
                continue

            # Short label before dotted lines (e.g. "Zafer:", "Cloud storage provider:", "Email protocol:")
            if (line.endswith(":") and len(line) < 35) or (len(line) < 30 and not line.endswith(".") and (current_q["elements"] or current_sec == "Structured")):
                current_q["elements"].append({"type": "sub_label", "text": line})
                continue

            # General text handling (continuation vs new paragraph)
            if len(current_q["elements"]) == 0:
                if current_q["q_type"] == "mcq" and len(current_q["options"]) > 0:
                    current_q["options"][-1] = (current_q["options"][-1][0], current_q["options"][-1][1] + " " + line)
                else:
                    # Multi-line Question Prompt stem -> append cleanly so entire stem is bold!
                    current_q["text"] += " " + line
            else:
                last_elem = current_q["elements"][-1]
                if last_elem["type"] in ("subpart", "paragraph", "bullet"):
                    last_elem["text"] += " " + line
                elif last_elem["type"] == "sub_item" and not last_elem["text"].startswith("..."):
                    last_elem["text"] += " " + line
                else:
                    current_q["elements"].append({"type": "paragraph", "text": line})
        else:
            if re.match(r"^(?:Text|Source|Passage|Case Study)\s+[A-Z0-9]:", line, re.IGNORECASE):
                blocks.append({"type": "passage_header", "text": line})
            else:
                blocks.append({"type": "instruction", "text": line})

    flush_table()

    questions_list = [b for b in blocks if b.get("type") == "question"]
    for idx, q in enumerate(questions_list, 1):
        q["display_number"] = idx

    return {
        "title": meta_title,
        "unit": meta_unit,
        "tutorial": meta_tutorial,
        "blocks": blocks,
        "questions": questions_list
    }


def import_raw_document(file_bytes, filename, output_diagram_dir):
    """
    Imports a raw tutor question document (PDF, Word DOCX, or TXT).
    Extracts text, questions, tables, and images.
    Auto-detects syllabus metadata and returns (extracted_text, metadata, image_map).
    """
    os.makedirs(output_diagram_dir, exist_ok=True)
    ext = os.path.splitext(filename)[1].lower()
    
    metadata = {
        "curriculum": "",
        "unit": "",
        "tutorial": "",
        "board": "CMB",
        "subject": ""
    }
    image_map = {}
    
    if ext == ".pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        diagram_count = 0
        extracted_pages = []
        
        start_page = 0
        if len(doc) >= 4:
            p2_text = doc[1].get_text("text").lower()
            if "camdex education" in p2_text or "trusted partner" in p2_text:
                start_page = 3
                
        for p_idx in range(start_page, len(doc)):
            page = doc[p_idx]
            
            # Detect tables using PyMuPDF find_tables
            tabs = page.find_tables()
            tab_rects = [fitz.Rect(t.bbox) for t in tabs.tables] if tabs.tables else []
            
            page_items = []
            
            # 1. Add Tables
            if tabs.tables:
                for t in tabs.tables:
                    t_box = fitz.Rect(t.bbox)
                    df = t.extract()
                    tbl_lines = []
                    for row in df:
                        cells = [str(c or '').strip().replace('\n', ' ') for c in row]
                        tbl_lines.append("| " + " | ".join(cells) + " |")
                    if tbl_lines:
                        tbl_str = "\n".join(tbl_lines)
                        page_items.append((t_box.y0, "table", tbl_str))
            
            # 2. Add Text Blocks (excluding text that falls inside table bounding boxes)
            blocks = page.get_text("blocks")
            for b in blocks:
                r = fitz.Rect(b[:4])
                if any(r.intersects(tr) for tr in tab_rects):
                    continue
                text = b[4].strip()
                if not text:
                    continue
                low = text.lower()
                
                # Metadata detection on first content page
                if p_idx == start_page:
                    if "edexcel" in low:
                        metadata["board"] = "EDX"
                        metadata["curriculum"] = text
                    elif "cambridge" in low:
                        metadata["board"] = "CMB"
                        metadata["curriculum"] = text
                    if "unit:" in low or low.startswith("unit "):
                        metadata["unit"] = text.split(":", 1)[-1].strip() if ":" in text else text
                    if "tutorial" in low or "tute" in low:
                        metadata["tutorial"] = text
                    for subj in ["Computer Science", "Physics", "Chemistry", "Biology", "Mathematics", "English", "ICT", "Business", "Economics", "Accounting", "Science"]:
                        if subj.lower() in low and not metadata["subject"]:
                            metadata["subject"] = subj
                            
                # Skip header/footer repetitions on subsequent pages
                if p_idx > start_page and ("cambridge igcse" in low or "edexcel igcse" in low or (low.startswith("unit:") and len(low) < 40)):
                    continue
                    
                page_items.append((b[1], "text", text))
            
            # 3. Add Images
            page_images = page.get_images(full=True)
            for img_info in page_images:
                xref = img_info[0]
                base_img = doc.extract_image(xref)
                img_bytes = base_img["image"]
                img_ext = base_img["ext"]
                if len(img_bytes) < 2500:
                    continue
                diagram_count += 1
                diag_name = f"diagram_{diagram_count}.{img_ext}"
                diag_path = os.path.join(output_diagram_dir, diag_name)
                with open(diag_path, "wb") as f:
                    f.write(img_bytes)
                image_map[str(diagram_count)] = diag_path
                image_map[diag_name] = diag_path
                page_items.append((page.rect.height, "image", f"[diagram: {diagram_count}]"))
                
            # Sort items on this page by vertical coordinate
            page_items.sort(key=lambda x: x[0])
            page_strs = [it[2] for it in page_items]
            extracted_pages.append("\n\n".join(page_strs))
            
        full_text = "\n\n".join(extracted_pages)
        return full_text, metadata, image_map
        
    elif ext in [".docx", ".doc"] and docx is not None:
        doc = docx.Document(io.BytesIO(file_bytes))
        diagram_count = 0
        extracted_elements = []
        
        # Extract images from docx parts
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                img_part = rel.target_part
                img_bytes = img_part.blob
                if len(img_bytes) > 2500:
                    diagram_count += 1
                    ext_name = os.path.splitext(img_part.partname)[1] or ".png"
                    diag_name = f"diagram_{diagram_count}{ext_name}"
                    diag_path = os.path.join(output_diagram_dir, diag_name)
                    with open(diag_path, "wb") as f:
                        f.write(img_bytes)
                    image_map[str(diagram_count)] = diag_path
                    image_map[diag_name] = diag_path
                    
        # Extract paragraphs and tables
        for elem in doc.element.body:
            if elem.tag.endswith('p'):
                p = docx.text.paragraph.Paragraph(elem, doc)
                text = p.text.strip()
                if text:
                    extracted_elements.append(text)
            elif elem.tag.endswith('tbl'):
                tbl = docx.table.Table(elem, doc)
                tbl_rows = []
                for row in tbl.rows:
                    cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                    tbl_rows.append("| " + " | ".join(cells) + " |")
                if tbl_rows:
                    extracted_elements.append("\n".join(tbl_rows))
                    
        full_text = "\n\n".join(extracted_elements)
        
        # Detect metadata
        for l in extracted_elements[:10]:
            low = l.lower()
            if "edexcel" in low:
                metadata["board"] = "EDX"
                metadata["curriculum"] = l
            elif "cambridge" in low:
                metadata["board"] = "CMB"
                metadata["curriculum"] = l
            if "unit:" in low or low.startswith("unit "):
                metadata["unit"] = l.split(":", 1)[-1].strip() if ":" in l else l
            if "tutorial" in low or "tute" in low:
                metadata["tutorial"] = l
            for subj in ["Computer Science", "Physics", "Chemistry", "Biology", "Mathematics", "English", "ICT", "Business", "Economics", "Accounting", "Science"]:
                if subj.lower() in low and not metadata["subject"]:
                    metadata["subject"] = subj
                    
        return full_text, metadata, image_map
        
    else:
        # Plain text
        text = file_bytes.decode("utf-8", errors="ignore")
        return text, metadata, image_map


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total pages and draw exact watermark seal
    and footer contact strip matching CAMDEX Education official format.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.watermark_path = kwargs.pop("watermark_path", None)
        self.footer_path = kwargs.pop("footer_path", None)
        self.watermark_opacity = kwargs.pop("watermark_opacity", 0.22)
        self.cover_pages_count = kwargs.pop("cover_pages_count", 3)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        page_num = self._pageNumber
        
        # Don't draw border, watermark or footer on Cover (Page 1)
        if page_num == 1:
            return

        self.saveState()

        # 1. Exact Camdex Double Border (Crisp outer + inner lines with tight spacing)
        self.setStrokeColor(COLOR_PRIMARY)
        self.setLineWidth(0.7)
        self.rect(24.0, 24.0, PAGE_WIDTH - 48.0, PAGE_HEIGHT - 48.0, stroke=1, fill=0)
        self.rect(25.6, 25.6, PAGE_WIDTH - 51.2, PAGE_HEIGHT - 51.2, stroke=1, fill=0)

        # 2. Background Watermark (Only on Question pages, i.e., page_num > cover_pages_count)
        if page_num > self.cover_pages_count:
            watermark_img = self.watermark_path or os.path.join(DEFAULTS_DIR, "seal_watermark.png")
            if not os.path.exists(watermark_img):
                watermark_img = os.path.join(LOGOS_DIR, "Seal Logo Colored Version-02.png")

            if os.path.exists(watermark_img):
                try:
                    self.setFillAlpha(self.watermark_opacity)
                    self.setStrokeAlpha(self.watermark_opacity)
                    w_size = 518.0
                    h_size = 518.0
                    cx = (PAGE_WIDTH - w_size) / 2.0
                    cy = (PAGE_HEIGHT - h_size) / 2.0 - 15.0
                    self.drawImage(
                        watermark_img,
                        cx, cy,
                        width=w_size, height=h_size,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception:
                    pass

        self.setFillAlpha(1.0)
        self.setStrokeAlpha(1.0)

        # 3. Crystal Clear Scalable Vector Contact Footer Strip
        color = COLOR_PRIMARY
        self.setFillColor(color)
        self.setStrokeColor(color)
        
        font_name = "Helvetica-Bold"
        font_size = 7.5
        self.setFont(font_name, font_size)
        
        phone_text = "+94 77 519 0334"
        web_text = "camdexedu.com"
        addr_text = "5 De S Jayasinghe Mawatha, Kohuwala, Nugegoda 10250"
        
        p_w = self.stringWidth(phone_text, font_name, font_size)
        w_w = self.stringWidth(web_text, font_name, font_size)
        a_w = self.stringWidth(addr_text, font_name, font_size)
        
        # Line 1: Phone + Website
        y1 = 43.0
        gap = 20.0
        item1_w = 14.0 + p_w
        item2_w = 14.0 + w_w
        total_l1_w = item1_w + gap + item2_w
        x1 = (PAGE_WIDTH - total_l1_w) / 2.0
        
        # Phone Icon
        icon_phone = os.path.join(DEFAULTS_DIR, "icon_phone.png")
        if os.path.exists(icon_phone):
            self.drawImage(icon_phone, x1, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            self.circle(x1 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        self.drawString(x1 + 13.5, y1, phone_text)
        
        # Globe Icon
        x2 = x1 + item1_w + gap
        icon_globe = os.path.join(DEFAULTS_DIR, "icon_globe.png")
        if os.path.exists(icon_globe):
            self.drawImage(icon_globe, x2, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            self.circle(x2 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        self.drawString(x2 + 13.5, y1, web_text)
        
        # Line 2: Location Pin
        y2 = 30.0
        total_l2_w = 14.0 + a_w
        x3 = (PAGE_WIDTH - total_l2_w) / 2.0
        icon_pin = os.path.join(DEFAULTS_DIR, "icon_pin.png")
        if os.path.exists(icon_pin):
            self.drawImage(icon_pin, x3, y2 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            self.circle(x3 + 5.0, y2 + 4.0, 5.0, stroke=0, fill=1)
        self.drawString(x3 + 13.5, y2, addr_text)

        self.restoreState()


def build_tutorial_pdf(
    raw_text,
    subject="Computer Science",
    board="CMB",
    unit_title="Data Representation",
    tutorial_num="Tutorial 1",
    curriculum_title="Cambridge IGCSE O/L",
    include_intro=True,
    include_teacher=True,
    teacher_name="Mr. Yusuf Shiham",
    teacher_qualifications="BSc (Hons) in Computer Science, MSc",
    teacher_subject="Computer Science Lead Tutor",
    teacher_message="Welcome to this tutorial! Ensure all questions are carefully answered. Practice consistently for exam success.",
    teacher_photo_path=None,
    custom_cover_path=None,
    image_map=None,
    font_color_hex="#1A4199",
    watermark_opacity=0.22,
    page_size=letter
):
    """
    Compiles full high-res tutorial PDF with Cover, Intro, Teacher Profile, and Questions.
    Supports MCQs, structured questions, reading passages, tables, diagrams, and marks.
    Renders all text in the official CAMDEX theme.
    """
    parsed = parse_input_text(raw_text)
    blocks = parsed["blocks"]
    questions = parsed["questions"]
    
    if not blocks and not questions:
        raise ValueError("No questions or content detected in the input text. Please paste questions.")

    # Determine cover image
    cover_image_path = custom_cover_path
    if not cover_image_path or not os.path.exists(cover_image_path):
        cover_filename = SUBJECT_COVER_MAP.get((subject, board), "Computer Science CMB.png")
        cover_image_path = os.path.join(COVERS_DIR, cover_filename)
        if not os.path.exists(cover_image_path):
            cover_image_path = os.path.join(BASE_DIR, "Tute Cover Pages Camdex", "Tute Cover Pages Camdex", cover_filename)

    buf = io.BytesIO()
    
    # Styles Setup (Exact Reference Typography)
    styles = getSampleStyleSheet()
    text_color = colors.HexColor(font_color_hex)

    title_main_style = ParagraphStyle(
        "TutMainTitle", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=24, leading=28,
        alignment=TA_CENTER, textColor=text_color, spaceAfter=14
    )
    unit_title_style = ParagraphStyle(
        "TutUnitTitle", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=24, leading=28,
        alignment=TA_CENTER, textColor=text_color, spaceAfter=14
    )
    tutorial_sub_style = ParagraphStyle(
        "TutSubTitle", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=15, leading=19,
        alignment=TA_CENTER, textColor=text_color, spaceAfter=24
    )
    section_heading_style = ParagraphStyle(
        "TutSectionHeading", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=14.5, leading=18.5,
        textColor=text_color, spaceBefore=14, spaceAfter=10
    )
    
    # Question text: main question level 1
    q_main_style = ParagraphStyle(
        "QuestionMain", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=11.5, leading=15.5,
        textColor=text_color, leftIndent=18, firstLineIndent=-18,
        spaceBefore=4, spaceAfter=4
    )
    
    # Reading Passage Header
    passage_hdr_style = ParagraphStyle(
        "PassageHeader", parent=styles["Normal"],
        fontName="Times-BoldItalic", fontSize=11.5, leading=15.0,
        textColor=text_color, leftIndent=18, spaceBefore=6, spaceAfter=4
    )
    
    # Reading Passage / Question Body Paragraph
    passage_body_style = ParagraphStyle(
        "PassageBody", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=10.5, leading=14.5,
        textColor=text_color, alignment=TA_JUSTIFY,
        leftIndent=18, spaceAfter=5
    )
    
    # Sub-label e.g. "Zafer", "Cloud storage provider", "You should consider:"
    sub_label_style = ParagraphStyle(
        "SubLabel", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=11.0, leading=14.5,
        textColor=text_color, leftIndent=30,
        spaceBefore=6, spaceAfter=3
    )

    # Bullet point style
    bullet_style = ParagraphStyle(
        "BulletPoint", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=10.5, leading=14.5,
        textColor=text_color, leftIndent=44, firstLineIndent=-14,
        spaceAfter=2.5
    )
    
    # Subpart Level 1: (a), (b), etc.
    subpart_style = ParagraphStyle(
        "SubpartStyle", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11.0, leading=15.0,
        textColor=text_color, alignment=TA_JUSTIFY,
        leftIndent=24, firstLineIndent=-18,
        spaceBefore=4, spaceAfter=3
    )

    subpart_tbl_style = ParagraphStyle(
        "SubpartTblStyle", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11.0, leading=15.0,
        textColor=text_color, alignment=TA_JUSTIFY,
        leftIndent=24, firstLineIndent=-18,
        spaceBefore=0, spaceAfter=0
    )
    
    # Sub-item Level 2: 1., 2. or (i), (ii)
    subitem_style = ParagraphStyle(
        "SubItemStyle", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11.0, leading=14.5,
        textColor=text_color, alignment=TA_JUSTIFY,
        leftIndent=38, firstLineIndent=-16,
        spaceBefore=2, spaceAfter=3
    )

    subitem_tbl_style = ParagraphStyle(
        "SubItemTblStyle", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11.0, leading=14.5,
        textColor=text_color, alignment=TA_JUSTIFY,
        leftIndent=38, firstLineIndent=-16,
        spaceBefore=0, spaceAfter=0
    )
    
    # MCQ option style
    opt_style = ParagraphStyle(
        "OptionStyle", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11.5, leading=15.0,
        textColor=text_color, leftIndent=26, spaceAfter=2.0
    )
    
    # Right-aligned marks
    mark_style = ParagraphStyle(
        "MarksStyle", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=10.5, leading=14,
        alignment=TA_RIGHT, textColor=text_color, spaceAfter=3
    )
    
    # Figure caption
    fig_caption_style = ParagraphStyle(
        "FigCaption", parent=styles["Normal"],
        fontName="Times-Italic", fontSize=10.0, leading=13.0,
        alignment=TA_CENTER, textColor=text_color, spaceBefore=4, spaceAfter=8
    )
    
    # Table cell styles
    tbl_cell_style = ParagraphStyle(
        "TblCell", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=10.0, leading=13.0,
        alignment=TA_CENTER, textColor=text_color
    )
    tbl_hdr_style = ParagraphStyle(
        "TblHdr", parent=styles["Normal"],
        fontName="Times-Bold", fontSize=10.0, leading=13.0,
        alignment=TA_CENTER, textColor=text_color
    )

    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=54.0,
        rightMargin=54.0,
        topMargin=54.0,
        bottomMargin=54.0,
        title=f"{unit_title} - {tutorial_num}"
    )

    story = []
    cover_pages_count = 0

    # ==================== PAGE 1: COVER PAGE ====================
    cover_pages_count += 1
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== PAGE 2: ABOUT INSTITUTE PAGE ====================
    if include_intro:
        cover_pages_count += 1
        story.append(Spacer(1, 270))

        logo_img = os.path.join(DEFAULTS_DIR, "p2_logo_h02_clean.png")
        if not os.path.exists(logo_img):
            logo_img = os.path.join(LOGOS_DIR, "Horizontal Colored Versions -02.png")
        if not os.path.exists(logo_img):
            logo_img = os.path.join(DEFAULTS_DIR, "logo_horizontal.png")
        
        if os.path.exists(logo_img):
            story.append(PlatypusImage(logo_img, width=150, height=75, hAlign="LEFT"))
            story.append(Spacer(1, 24))

        about_text_style = ParagraphStyle(
            "AboutTextStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=11.0, leading=14.5,
            textColor=colors.HexColor("#4E80BC"),
            alignment=TA_JUSTIFY, spaceAfter=14
        )

        p1 = Paragraph(
            "CAMDEX Education is your trusted partner in IGCSE Edexcel and "
            "Cambridge subject preparation. We provide expert tutoring in a "
            "wide range of subjects including Biology, Chemistry, Physics, "
            "Mathematics, English, ICT, Computer Science, and Commerce "
            "(Business, Accounting &amp; Economics).",
            about_text_style
        )
        p2 = Paragraph(
            "Our flexible learning options - online and physical classes, "
            "recorded sessions, and ongoing academic support - are designed "
            "to help students excel in their IGCSE exams.",
            about_text_style
        )
        p3 = Paragraph(
            "With a focus on affordability, quality, and student success, "
            "CAMDEX Education is here to support every step of your academic "
            "journey.",
            about_text_style
        )

        about_table = Table([[ [p1, p2, p3] ]], colWidths=[328], hAlign="LEFT")
        about_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(about_table)
        story.append(PageBreak())

    # ==================== PAGE 3: TEACHER PROFILE PAGE ====================
    if include_teacher:
        cover_pages_count += 1
        story.append(Spacer(1, 160))

        name_text = str(teacher_name or "").strip().upper()
        if not name_text:
            name_text = "MR. YUSUF SHIHAM"

        subject_text = str(teacher_subject or "").strip().upper()
        if not subject_text:
            subject_text = "COMPUTER SCIENCE TUTOR"

        qual_text = str(teacher_qualifications or "").strip()
        if not qual_text:
            qual_text = "Undergraduate- BSc. Hons Information Technology<br/>specializing in Artificial Intelligence(Reading)"

        bio_raw = str(teacher_message or "").strip()
        if not bio_raw:
            bio_raw = (
                "Currently pursuing a <b>degree in Artificial Intelligence at the Sri Lanka Institute of Information Technology,</b> "
                "Mr. Yusuf brings together academic excellence and a deep enthusiasm for teaching.\n\n"
                "He is dedicated to fostering an engaging and intellectually enriching learning atmosphere, where students not only "
                "gain confidence in Computer Science but also strengthen their analytical and problem-solving abilities.\n\n"
                "At CAMDEX Education, he teaches <b>Computer Science for Edexcel and Cambridge O/Level</b> students, equipping them "
                "with the knowledge, skills, and mindset needed to excel academically and thrive in an increasingly digital future."
            )

        registered_fonts = pdfmetrics.getRegisteredFontNames()
        has_bebas = "BebasNeue" in registered_fonts
        has_poppins = "Poppins" in registered_fonts

        name_font = "BebasNeue" if has_bebas else "Helvetica-Bold"
        body_font = "Poppins" if has_poppins else "Helvetica"

        name_style = ParagraphStyle('TName', parent=styles['Normal'], fontName=name_font, fontSize=34.0, leading=32.0, textColor=colors.HexColor('#163A8B'), spaceAfter=3)
        role_style = ParagraphStyle('TRole', parent=styles['Normal'], fontName=name_font, fontSize=19.5, leading=20.5, textColor=colors.HexColor('#3577D6'), spaceAfter=10)
        qual_style = ParagraphStyle('TQual', parent=styles['Normal'], fontName=body_font, fontSize=9.0, leading=12.2, textColor=colors.HexColor('#224483'), spaceAfter=12)
        bio_style = ParagraphStyle('TBio', parent=styles['Normal'], fontName=body_font, fontSize=9.0, leading=13.4, textColor=colors.HexColor('#224483'), alignment=TA_JUSTIFY, spaceAfter=10)

        qual_formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', qual_text).replace("\n", "<br/>")
        info_flowables = [
            Paragraph(name_text, name_style),
            Paragraph(subject_text, role_style),
            Paragraph(qual_formatted, qual_style)
        ]

        for para in bio_raw.split("\n\n"):
            p_clean = para.strip().replace("\n", " ")
            if p_clean:
                p_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', p_clean)
                info_flowables.append(Paragraph(p_html, bio_style))

        target_w, target_h = 215.0, 370.0
        if teacher_photo_path and os.path.exists(teacher_photo_path):
            try:
                im = Image.open(teacher_photo_path)
                aspect = im.width / im.height
                calc_w = target_h * aspect
                if calc_w > 218.0:
                    calc_w = 218.0
                    calc_h = calc_w / aspect
                else:
                    calc_h = target_h
                photo_flowable = PlatypusImage(teacher_photo_path, width=calc_w, height=calc_h, hAlign='RIGHT')
            except Exception:
                photo_flowable = PlatypusImage(teacher_photo_path, width=target_w, height=target_h, hAlign='RIGHT')
        else:
            photo_flowable = Spacer(target_w, target_h)

        profile_table = Table([[photo_flowable, info_flowables]], colWidths=[218, 236], hAlign='CENTER')
        profile_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (1,0), (1,-1), 14),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(profile_table)
        story.append(PageBreak())

    # ==================== PAGE 4+: QUESTIONS & PASSAGES ====================
    story.append(Paragraph(f"<u><b>{clean_xml_text(curriculum_title)}</b></u>", title_main_style))
    story.append(Paragraph(f"<u><b>Unit: {clean_xml_text(unit_title)}</b></u>", unit_title_style))
    story.append(Paragraph(f"<b>{clean_xml_text(tutorial_num)}</b>", tutorial_sub_style))
    story.append(Spacer(1, 6))

    def resolve_image_path(ref_key):
        if not image_map:
            return None
        if ref_key in image_map:
            return image_map[ref_key]
        if ref_key.isdigit():
            idx = int(ref_key) - 1
            keys = list(image_map.keys())
            if 0 <= idx < len(keys):
                return image_map[keys[idx]]
        norm_ref = os.path.basename(ref_key).lower()
        for k, v in image_map.items():
            if norm_ref in k.lower() or norm_ref in os.path.basename(v).lower():
                return v
        if len(image_map) > 0:
            return list(image_map.values())[0]
        return None

    has_started_content = False

    for block in blocks:
        b_type = block.get("type")
        
        if b_type == "section_header":
            sec_title = block.get("title", "")
            # Add a PageBreak before subsequent sections (e.g., Structured Questions after MCQs) so it starts on a fresh page
            if has_started_content:
                story.append(PageBreak())
            has_started_content = True
            story.append(Paragraph(f"<u><b>{clean_xml_text(sec_title)}</b></u>", section_heading_style))
            continue

        if b_type == "instruction":
            has_started_content = True
            story.append(Paragraph(f"<b>{clean_xml_text(block['text'])}</b>", passage_body_style))
            continue

        if b_type == "passage_header":
            has_started_content = True
            story.append(Paragraph(f"<b><i>{clean_xml_text(block['text'])}</i></b>", passage_hdr_style))
            continue

        if b_type == "image":
            has_started_content = True
            img_path = resolve_image_path(block.get("ref", "1"))
            if img_path and os.path.exists(img_path):
                try:
                    im = Image.open(img_path)
                    w, h = im.size
                    max_w, max_h = 440.0, 220.0
                    scale = min(max_w / w, max_h / h, 1.0)
                    story.append(Spacer(1, 6))
                    story.append(PlatypusImage(img_path, width=w*scale, height=h*scale, hAlign='CENTER'))
                    if block.get("caption"):
                        story.append(Paragraph(clean_xml_text(block["caption"]), fig_caption_style))
                    story.append(Spacer(1, 6))
                except Exception:
                    pass
            continue

        if b_type == "table":
            has_started_content = True
            raw_rows = parse_markdown_table(block["rows"])
            if raw_rows:
                col_cnt = max(len(r) for r in raw_rows)
                col_w = min(460.0 / col_cnt, 180.0)
                col_widths = [col_w] * col_cnt
                t_data = []
                for r_idx, row in enumerate(raw_rows):
                    r_cells = []
                    row_padded = row + [''] * (col_cnt - len(row))
                    for cell in row_padded:
                        st_cell = tbl_hdr_style if r_idx == 0 else tbl_cell_style
                        r_cells.append(Paragraph(clean_xml_text(cell), st_cell))
                    t_data.append(r_cells)
                t_obj = Table(t_data, colWidths=col_widths, hAlign='CENTER')
                t_obj.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.7, COLOR_PRIMARY),
                    ('BACKGROUND', (0,0), (-1,0), COLOR_TABLE_HEADER),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(Spacer(1, 6))
                story.append(t_obj)
                story.append(Spacer(1, 6))
            continue

        if b_type == "question":
            has_started_content = True
            disp_num = block.get("display_number", block.get("number", 1))
            q_text = block.get("text", "")
            base_q_text, mark = format_marks_in_text(q_text)
            
            q_html = f"<b>{disp_num}.</b> &nbsp;{clean_xml_text(base_q_text)}"
            if mark:
                q_html += f" &nbsp; <b>{clean_xml_text(mark)}</b>"

            main_q_para = Paragraph(q_html, q_main_style)

            # MCQ Options handling
            if block.get("options"):
                opt_flowables = [main_q_para]
                for letter, opt_text in block["options"]:
                    opt_html = f"<b>{letter}.</b> &nbsp;{clean_xml_text(opt_text)}"
                    opt_flowables.append(Paragraph(opt_html, opt_style))
                opt_flowables.append(Spacer(1, 4))
                story.append(KeepTogether(opt_flowables))
                continue

            # Structured question handling
            structured_flowables = []
            if block.get("elements"):
                for elem in block["elements"]:
                    e_type = elem.get("type")
                    
                    if e_type == "passage_header":
                        structured_flowables.append(Paragraph(f"<b><i>{clean_xml_text(elem['text'])}</i></b>", passage_hdr_style))
                    
                    elif e_type == "paragraph":
                        base_p, mark = format_marks_in_text(elem["text"])
                        p_html = clean_xml_text(base_p)
                        if mark:
                            p_html += f" &nbsp; <b>{clean_xml_text(mark)}</b>"
                        structured_flowables.append(Paragraph(p_html, passage_body_style))
                    
                    elif e_type == "sub_label":
                        lbl_text = elem["text"].strip()
                        if not lbl_text.endswith(":"):
                            lbl_text += ":"
                        structured_flowables.append(Paragraph(f"<b>{clean_xml_text(lbl_text)}</b>", sub_label_style))

                    elif e_type == "bullet":
                        b_text = clean_xml_text(elem["text"])
                        structured_flowables.append(Paragraph(f"&bull; &nbsp;{b_text}", bullet_style))

                    elif e_type == "subpart":
                        lbl = elem.get("label", "")
                        stext = elem.get("text", "")
                        base_stext, mark = format_marks_in_text(stext)
                        
                        # Check if subpart text is essentially an answer dotted line e.g. "(a) ......"
                        if not base_stext or base_stext.startswith("...") or base_stext.startswith("___") or set(base_stext).issubset(set(". _-")):
                            structured_flowables.append(NumberedDottedAnswerLine(num_str=f"({lbl})", left_indent=24, color=text_color, mark=mark))
                        else:
                            sub_html = f"<b>({lbl})</b> &nbsp;{clean_xml_text(base_stext)}"
                            if mark:
                                sub_tbl = Table([
                                    [Paragraph(sub_html, subpart_tbl_style), Paragraph(f"<b>{clean_xml_text(mark)}</b>", mark_style)]
                                ], colWidths=[CONTENT_WIDTH - 44, 44], hAlign='LEFT')
                                sub_tbl.setStyle(TableStyle([
                                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                                    ('TOPPADDING', (0,0), (-1,-1), 0),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                ]))
                                structured_flowables.append(sub_tbl)
                            else:
                                structured_flowables.append(Paragraph(sub_html, subpart_style))
                    
                    elif e_type == "sub_item":
                        num = elem.get("num", "1")
                        stext = elem.get("text", "")
                        base_stext, mark = format_marks_in_text(stext)
                        
                        # Check if sub-item is essentially a numbered dotted line e.g. "1. ............. [1]"
                        if not base_stext or base_stext.startswith("...") or base_stext.startswith("___") or set(base_stext).issubset(set(". _-")):
                            structured_flowables.append(NumberedDottedAnswerLine(num_str=f"{num}.", left_indent=24, color=text_color, mark=mark))
                        else:
                            item_html = f"<b>{num}.</b> &nbsp;{clean_xml_text(base_stext)}"
                            if mark:
                                item_tbl = Table([
                                    [Paragraph(item_html, subitem_tbl_style), Paragraph(f"<b>{clean_xml_text(mark)}</b>", mark_style)]
                                ], colWidths=[CONTENT_WIDTH - 44, 44], hAlign='LEFT')
                                item_tbl.setStyle(TableStyle([
                                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                                    ('TOPPADDING', (0,0), (-1,-1), 0),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                ]))
                                structured_flowables.append(item_tbl)
                            else:
                                structured_flowables.append(Paragraph(item_html, subitem_style))
                    
                    elif e_type == "dotted_line":
                        d_text = elem["text"]
                        _, mark = format_marks_in_text(d_text)
                        structured_flowables.append(DottedAnswerLine(left_indent=24, color=text_color, mark=mark))
                    
                    elif e_type == "total_marks":
                        structured_flowables.append(Paragraph(f"<b>{clean_xml_text(elem['text'])}</b>", mark_style))
                    
                    elif e_type == "figure_caption":
                        structured_flowables.append(Paragraph(clean_xml_text(elem["text"]), fig_caption_style))
                    
                    elif e_type == "image":
                        ref = elem.get("ref", "1")
                        img_path = resolve_image_path(ref)
                        if img_path and os.path.exists(img_path):
                            try:
                                im = Image.open(img_path)
                                w, h = im.size
                                max_w, max_h = 420.0, 200.0
                                scale = min(max_w / w, max_h / h, 1.0)
                                structured_flowables.append(Spacer(1, 6))
                                structured_flowables.append(PlatypusImage(img_path, width=w*scale, height=h*scale, hAlign='CENTER'))
                                if elem.get("caption"):
                                    structured_flowables.append(Paragraph(clean_xml_text(elem["caption"]), fig_caption_style))
                                structured_flowables.append(Spacer(1, 6))
                            except Exception:
                                pass
                    
                    elif e_type == "table":
                        raw_rows = parse_markdown_table(elem["rows"])
                        if raw_rows:
                            col_cnt = max(len(r) for r in raw_rows)
                            col_w = min(460.0 / col_cnt, 180.0)
                            col_widths = [col_w] * col_cnt
                            t_data = []
                            for r_idx, row in enumerate(raw_rows):
                                r_cells = []
                                row_padded = row + [''] * (col_cnt - len(row))
                                for cell in row_padded:
                                    st_cell = tbl_hdr_style if r_idx == 0 else tbl_cell_style
                                    r_cells.append(Paragraph(clean_xml_text(cell), st_cell))
                                t_data.append(r_cells)
                            t_obj = Table(t_data, colWidths=col_widths, hAlign='CENTER')
                            t_obj.setStyle(TableStyle([
                                ('GRID', (0,0), (-1,-1), 0.7, COLOR_PRIMARY),
                                ('BACKGROUND', (0,0), (-1,0), COLOR_TABLE_HEADER),
                                ('TOPPADDING', (0,0), (-1,-1), 5),
                                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                                ('LEFTPADDING', (0,0), (-1,-1), 6),
                                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                            ]))
                            structured_flowables.append(Spacer(1, 6))
                            structured_flowables.append(t_obj)
                            structured_flowables.append(Spacer(1, 6))

            # Prevent orphan question stems: Keep main question + first 1-2 elements together
            if structured_flowables:
                lead_count = min(len(structured_flowables), 2)
                lead_group = [main_q_para] + structured_flowables[:lead_count]
                story.append(KeepTogether(lead_group))
                for rem_flowable in structured_flowables[lead_count:]:
                    story.append(rem_flowable)
            else:
                story.append(main_q_para)

            story.append(Spacer(1, 6))

    # Canvas Drawing Callbacks
    def draw_cover_canvas(c, d):
        c.saveState()
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                c.drawImage(cover_image_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            except Exception:
                pass
        
        # Only the Unit Title is rendered inside the white placeholder capsule
        unit_str = str(unit_title or "Data Representation").strip()
        if unit_str:
            font_name = "Helvetica-Bold"
            max_width = 250.0
            max_height = 84.0
            
            chosen_lines = [unit_str]
            chosen_size = 24
            chosen_leading = 28
            
            # Dynamically reduce font size from 26pt down to 10pt until it fits cleanly in 1-3 lines
            for font_size in range(26, 9, -1):
                leading = font_size * 1.18
                words = unit_str.split()
                lines = []
                curr_line = ""
                fits = True
                
                for w in words:
                    if c.stringWidth(w, font_name, font_size) > max_width:
                        fits = False
                        break
                    test_l = (curr_line + " " + w).strip()
                    if c.stringWidth(test_l, font_name, font_size) <= max_width:
                        curr_line = test_l
                    else:
                        if curr_line:
                            lines.append(curr_line)
                        curr_line = w
                if curr_line:
                    lines.append(curr_line)
                    
                if not fits:
                    continue
                    
                total_h = (len(lines) - 1) * leading + font_size
                if total_h <= max_height and len(lines) <= 4:
                    chosen_lines = lines
                    chosen_size = font_size
                    chosen_leading = leading
                    break
                    
            c.setFont(font_name, chosen_size)
            c.setFillColor(colors.HexColor("#002060"))
            
            # Vertically center inside the white capsule (center y ≈ 466.0 pt)
            capsule_center_y = 466.0
            num_lines = len(chosen_lines)
            first_y = capsule_center_y + ((num_lines - 1) * chosen_leading / 2.0) - (chosen_size * 0.15)
            
            for i, line in enumerate(chosen_lines):
                c.drawString(28.0, first_y - (i * chosen_leading), line)
        
        c.restoreState()

    def build_canvas_maker(*args, **kwargs):
        kwargs["watermark_path"] = os.path.join(DEFAULTS_DIR, "seal_watermark.png")
        kwargs["footer_path"] = os.path.join(DEFAULTS_DIR, "footer_contact.png")
        kwargs["watermark_opacity"] = watermark_opacity
        kwargs["cover_pages_count"] = cover_pages_count
        return NumberedCanvas(*args, **kwargs)

    doc.build(
        story,
        onFirstPage=draw_cover_canvas,
        canvasmaker=build_canvas_maker
    )

    return buf.getvalue(), len(questions)


def recolor_pdf_stream_to_blue(stream_bytes, blue_rgb=(0.102, 0.255, 0.600)):
    """
    Recolors black/dark gray text and vector operators in PDF content streams to official CAMDEX Blue.
    Prepends default color state and replaces 0 g, 0 G, 0 0 0 rg, 0 0 0 RG, and CMYK black.
    """
    r, g, b = blue_rgb
    blue_rg = f"{r:.3f} {g:.3f} {b:.3f} rg".encode()
    blue_RG = f"{r:.3f} {g:.3f} {b:.3f} RG".encode()
    
    prefix = b"q " + blue_rg + b" " + blue_RG + b"\n"
    suffix = b"\nQ"
    
    # Replace black/dark gray fill and stroke operators
    res = re.sub(rb'\b0(?:\.[0-2]\d*)?\s+g\b', blue_rg, stream_bytes)
    res = re.sub(rb'\b0(?:\.[0-2]\d*)?\s+G\b', blue_RG, res)
    res = re.sub(rb'\b0(?:\.[0-2]\d*)?\s+0(?:\.[0-2]\d*)?\s+0(?:\.[0-2]\d*)?\s+rg\b', blue_rg, res)
    res = re.sub(rb'\b0(?:\.[0-2]\d*)?\s+0(?:\.[0-2]\d*)?\s+0(?:\.[0-2]\d*)?\s+RG\b', blue_RG, res)
    res = re.sub(rb'\b0(?:\.0+)?\s+0(?:\.0+)?\s+0(?:\.0+)?\s+1(?:\.0+)?\s+k\b', blue_rg, res)
    res = re.sub(rb'\b0(?:\.0+)?\s+0(?:\.0+)?\s+0(?:\.0+)?\s+1(?:\.0+)?\s+K\b', blue_RG, res)
    
    return prefix + res + suffix


def build_direct_raw_tutorial_pdf(
    file_bytes,
    filename="tutorial.pdf",
    subject="Computer Science",
    board="CMB",
    unit_title="Data Representation",
    tutorial_num="Tutorial 1",
    curriculum_title="Cambridge IGCSE O/L",
    include_intro=True,
    include_teacher=True,
    teacher_name="Mr. Yusuf Shiham",
    teacher_qualifications="BSc (Hons) in Computer Science, MSc",
    teacher_subject="COMPUTER SCIENCE LEAD TUTOR",
    teacher_message="Welcome to this tutorial! Ensure all structured problems and past paper questions are carefully answered.",
    teacher_photo_path=None,
    custom_cover_path=None,
    image_map=None,
    font_color_hex="#1A4199",
    watermark_opacity=0.20
):
    """
    Direct 1-Click Converter: Takes a raw tutor question document (PDF, Word DOCX, or TXT),
    and directly produces the full, publication-ready CAMDEX document in official CAMDEX Blue (#1A4199).
    
    If given a raw PDF:
      - Automatically isolates question pages (skipping old cover/intro pages if present).
      - Converts all question text and vector lines from black to official CAMDEX Blue (#1A4199).
      - Rescales and centers question content into the safe printable bounding box [38, 70, 574, 735].
      - Stamps the official CAMDEX Header (Horizontal Logo on left, Curriculum & Unit title on right, blue dividing rule).
      - Stamps the Double Blue Border and centered Watermark Seal.
      - Stamps the official Vector Footer Strip with Phone, Website, Address, and 'Page X of Y' pagination.
      - Prepends the official 2026/2027 Cover Page (Subject + Board with typography), About Page, and Teacher Profile Page.
    
    If given Word DOCX / TXT:
      - Automatically extracts questions, tables, diagrams, and compiles via the high-resolution ReportLab engine.
    """
    ext = os.path.splitext(filename)[1].lower() if filename else ".pdf"
    
    # ------------------ CASE 1: RAW PDF DOCUMENT ------------------
    if ext == ".pdf":
        doc_src = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Determine start_page: Only skip if this is an already branded CAMDEX document with the CAMDEX About page at page 2
        start_page = 0
        if len(doc_src) >= 3:
            p2_txt = doc_src[1].get_text("text").lower()
            if "camdex education is your trusted" in p2_txt or "trusted partner in igcse" in p2_txt:
                start_page = 3
        
        # Trim accidental trailing empty blank pages at the end of the document
        end_page = len(doc_src)
        while end_page > start_page:
            last_p = doc_src[end_page - 1]
            if not last_p.get_text("text").strip() and len(last_p.get_images()) == 0 and len(last_p.get_drawings()) == 0:
                end_page -= 1
            else:
                break
                
        question_count_pages = end_page - start_page
        
        # 1. Build Cover, Intro, and Teacher Profile pages
        dummy_text = f"Title: {curriculum_title}\nUnit: {unit_title}\nTutorial: {tutorial_num}\n\n1. Sample\nA. Option"
        front_pdf_bytes, _ = build_tutorial_pdf(
            raw_text=dummy_text,
            subject=subject,
            board=board,
            unit_title=unit_title,
            tutorial_num=tutorial_num,
            curriculum_title=curriculum_title,
            include_intro=include_intro,
            include_teacher=include_teacher,
            teacher_name=teacher_name,
            teacher_qualifications=teacher_qualifications,
            teacher_subject=teacher_subject,
            teacher_message=teacher_message,
            teacher_photo_path=teacher_photo_path,
            custom_cover_path=custom_cover_path,
            font_color_hex=font_color_hex,
            watermark_opacity=watermark_opacity
        )
        
        doc_front = fitz.open(stream=front_pdf_bytes, filetype="pdf")
        cover_pages_count = 1 + (1 if include_intro else 0) + (1 if include_teacher else 0)
        
        # Check if pre-rendered final teacher page exists for this teacher
        teacher_final_dir = os.path.join(BASE_DIR, "About tutor Pages 2026-2027 Complete", "About tutor Pages 2026-2027", "Final pages")
        teacher_page_custom_img = None
        if include_teacher and os.path.exists(teacher_final_dir) and not teacher_photo_path:
            norm_name = str(teacher_name or "").lower()
            norm_subj = str(subject or "").lower()
            match_file = None
            for tf in os.listdir(teacher_final_dir):
                tf_low = tf.lower()
                if "afra" in norm_name or ("accounting" in norm_subj and "afra" in tf_low):
                    match_file = tf; break
                elif "devin" in norm_name or ("math" in norm_subj and "devin" in tf_low):
                    match_file = tf; break
                elif "dimitri" in norm_name or ("english" in norm_subj and "dimitri" in tf_low):
                    match_file = tf; break
                elif "haani" in norm_name or ("economics" in norm_subj and "haani" in tf_low):
                    match_file = tf; break
                elif "prasanna" in norm_name or ("business" in norm_subj and "prasanna" in tf_low):
                    match_file = tf; break
                elif "qaidh" in norm_name or ("ict" in norm_subj and "qaidh" in tf_low):
                    match_file = tf; break
                elif "shehan" in norm_name or (("chemistry" in norm_subj or "physics" in norm_subj or "biology" in norm_subj) and "shehan" in tf_low):
                    match_file = tf; break
                elif "yusuf" in norm_name or ("computer science" in norm_subj and "yusuf" in tf_low):
                    match_file = tf; break
            
            if match_file:
                teacher_page_custom_img = os.path.join(teacher_final_dir, match_file)

        doc_front_clean = fitz.open()
        for i in range(cover_pages_count):
            if i < len(doc_front):
                # If page 3 is teacher and we have full pre-rendered page
                if i == cover_pages_count - 1 and include_teacher and teacher_page_custom_img and os.path.exists(teacher_page_custom_img):
                    t_page = doc_front_clean.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                    t_page.insert_image(t_page.rect, filename=teacher_page_custom_img)
                else:
                    doc_front_clean.insert_pdf(doc_front, from_page=i, to_page=i)
        
        # 2. Recolor and format Question Pages
        doc_questions_clean = fitz.open()
        
        # Recolor source doc content streams to CAMDEX Blue
        for p in doc_src:
            for xref in p.get_contents():
                st = doc_src.xref_stream(xref)
                if st:
                    doc_src.update_stream(xref, recolor_pdf_stream_to_blue(st))
                    
        total_final_pages = cover_pages_count + question_count_pages
        
        logo_img_path = os.path.join(LOGOS_DIR, "Horizontal Colored Versions -01.png")
        if not os.path.exists(logo_img_path):
            logo_img_path = os.path.join(DEFAULTS_DIR, "logo_horizontal.png")
            
        watermark_img_path = os.path.join(DEFAULTS_DIR, "seal_watermark.png")
        if not os.path.exists(watermark_img_path):
            watermark_img_path = os.path.join(LOGOS_DIR, "Seal Logo Colored Version-02.png")
            
        icon_phone = os.path.join(DEFAULTS_DIR, "icon_phone.png")
        icon_globe = os.path.join(DEFAULTS_DIR, "icon_globe.png")
        icon_pin = os.path.join(DEFAULTS_DIR, "icon_pin.png")
        
        # Pre-build official CAMDEX Base Question Stamp (Double Border, Watermark, Footer Contact) ONCE
        buf_stamp = io.BytesIO()
        stamp_canv = canvas.Canvas(buf_stamp, pagesize=letter)
        
        # Double Blue Border
        stamp_canv.setStrokeColor(COLOR_PRIMARY)
        stamp_canv.setLineWidth(0.7)
        stamp_canv.rect(24.0, 24.0, PAGE_WIDTH - 48.0, PAGE_HEIGHT - 48.0, stroke=1, fill=0)
        stamp_canv.rect(25.6, 25.6, PAGE_WIDTH - 51.2, PAGE_HEIGHT - 51.2, stroke=1, fill=0)
        
        # Background Watermark Seal
        if os.path.exists(watermark_img_path):
            stamp_canv.setFillAlpha(watermark_opacity)
            w_size = 518.0
            stamp_canv.drawImage(
                watermark_img_path,
                (PAGE_WIDTH - w_size) / 2.0,
                (PAGE_HEIGHT - w_size) / 2.0 - 10.0,
                width=w_size,
                height=w_size,
                preserveAspectRatio=True,
                mask='auto'
            )
            stamp_canv.setFillAlpha(1.0)
            
        # Footer Strip (Contact details only - no page numbers)
        font_name = "Helvetica-Bold"
        font_size = 7.5
        stamp_canv.setFont(font_name, font_size)
        stamp_canv.setFillColor(COLOR_PRIMARY)
        stamp_canv.setStrokeColor(COLOR_PRIMARY)
        phone_text = "+94 77 519 0334"
        web_text = "camdexedu.com"
        addr_text = "5 De S Jayasinghe Mawatha, Kohuwala, Nugegoda 10250"
        
        p_w = stamp_canv.stringWidth(phone_text, font_name, font_size)
        w_w = stamp_canv.stringWidth(web_text, font_name, font_size)
        a_w = stamp_canv.stringWidth(addr_text, font_name, font_size)
        
        # Line 1: Phone + Web
        y1 = 43.0
        gap = 20.0
        total_l1_w = 14.0 + p_w + gap + 14.0 + w_w
        x1 = (PAGE_WIDTH - total_l1_w) / 2.0
        
        if os.path.exists(icon_phone):
            stamp_canv.drawImage(icon_phone, x1, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            stamp_canv.circle(x1 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        stamp_canv.drawString(x1 + 13.5, y1, phone_text)
        
        x2 = x1 + 14.0 + p_w + gap
        if os.path.exists(icon_globe):
            stamp_canv.drawImage(icon_globe, x2, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            stamp_canv.circle(x2 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        stamp_canv.drawString(x2 + 13.5, y1, web_text)
        
        # Line 2: Address
        y2 = 30.0
        total_l2_w = 14.0 + a_w
        x3 = (PAGE_WIDTH - total_l2_w) / 2.0
        if os.path.exists(icon_pin):
            stamp_canv.drawImage(icon_pin, x3, y2 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            stamp_canv.circle(x3 + 5.0, y2 + 4.0, 5.0, stroke=0, fill=1)
        stamp_canv.drawString(x3 + 13.5, y2, addr_text)
        
        stamp_canv.save()
        base_stamp_doc = fitz.open(stream=buf_stamp.getvalue(), filetype="pdf")
        
        for q_idx in range(start_page, len(doc_src)):
            # Create standard Letter page (612 x 792)
            target_p = doc_questions_clean.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            
            # 1. Place question content from source into clean, fully centered safe printable box
            # Top: 36pt (inside double border at 25.6pt), Bottom: 54pt (above footer), Sides: 36pt
            target_box = fitz.Rect(36.0, 36.0, PAGE_WIDTH - 36.0, PAGE_HEIGHT - 54.0)
            target_p.show_pdf_page(target_box, doc_src, q_idx)
            
            # 2. Overlay Base Stamp (Double Blue Border, Centered Watermark, Contact Footer Strip)
            target_p.show_pdf_page(target_p.rect, base_stamp_doc, 0, overlay=True)
            
        final_doc = fitz.open()
        final_doc.insert_pdf(doc_front_clean)
        final_doc.insert_pdf(doc_questions_clean)
        
        return final_doc.tobytes(), question_count_pages
        
    # ------------------ CASE 2: WORD DOCX OR TEXT ------------------
    else:
        temp_dir = os.path.join(BASE_DIR, "assets", "temp", "diagrams")
        ext_text, ext_meta, ext_img_map = import_raw_document(file_bytes, filename, temp_dir)
        combined_img_map = {**(image_map or {}), **ext_img_map}
        
        final_subject = subject or ext_meta.get("subject") or "Computer Science"
        final_board = board or ext_meta.get("board") or "CMB"
        final_unit = unit_title or ext_meta.get("unit") or "Data Representation"
        final_tut = tutorial_num or ext_meta.get("tutorial") or "Tutorial 1"
        final_curr = curriculum_title or ext_meta.get("curriculum") or "Cambridge IGCSE O/L"
        
        pdf_bytes, q_count = build_tutorial_pdf(
            raw_text=ext_text,
            subject=final_subject,
            board=final_board,
            unit_title=final_unit,
            tutorial_num=final_tut,
            curriculum_title=final_curr,
            include_intro=include_intro,
            include_teacher=include_teacher,
            teacher_name=teacher_name,
            teacher_qualifications=teacher_qualifications,
            teacher_subject=teacher_subject,
            teacher_message=teacher_message,
            teacher_photo_path=teacher_photo_path,
            custom_cover_path=custom_cover_path,
            image_map=combined_img_map,
            font_color_hex=font_color_hex,
            watermark_opacity=watermark_opacity
        )
        return pdf_bytes, q_count


def build_stamped_tutorial_pdf(
    question_pdf_bytes,
    subject="Chemistry",
    board="CMB",
    unit_title="The Particulate Nature of Matter",
    tutorial_num="Tutorial 1",
    curriculum_title="Cambridge IGCSE O/L",
    include_intro=True,
    include_teacher=True,
    teacher_name="Mr. Yusuf Shiham",
    teacher_qualifications="BSc (Hons) in Chemistry",
    teacher_subject="CHEMISTRY LEAD TUTOR",
    teacher_message="Welcome to this tutorial! Ensure all structured problems and past paper questions are carefully answered.",
    teacher_photo_path=None,
    custom_cover_path=None,
    font_color_hex="#1A4199",
    watermark_opacity=0.20
):
    """
    Backwards-compatible wrapper calling build_direct_raw_tutorial_pdf.
    """
    return build_direct_raw_tutorial_pdf(
        file_bytes=question_pdf_bytes,
        filename="past_paper.pdf",
        subject=subject,
        board=board,
        unit_title=unit_title,
        tutorial_num=tutorial_num,
        curriculum_title=curriculum_title,
        include_intro=include_intro,
        include_teacher=include_teacher,
        teacher_name=teacher_name,
        teacher_qualifications=teacher_qualifications,
        teacher_subject=teacher_subject,
        teacher_message=teacher_message,
        teacher_photo_path=teacher_photo_path,
        custom_cover_path=custom_cover_path,
        font_color_hex=font_color_hex,
        watermark_opacity=watermark_opacity
    )

