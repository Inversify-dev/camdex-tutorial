"""
Tutorial PDF Generator Engine for Camdex Education.
Matches the exact structure, styling, colors, watermark, and branding of Tute_1_CMB_DataRepresentation.pdf.
"""

import io
import os
import re
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether,
    Table, TableStyle, Image as PlatypusImage, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# Page dimensions (Letter standard matching reference 612x792 pt)
PAGE_WIDTH, PAGE_HEIGHT = 612.0, 792.0

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
except Exception as _fe:
    pass

# Exact Camdex Reference Brand Colors
COLOR_PRIMARY = colors.HexColor("#1A4199")     # Exact Camdex Deep Royal Blue
COLOR_SECONDARY = colors.HexColor("#3154A4")   # Header Accent Blue
COLOR_DARK = colors.HexColor("#1A4199")        # Question Text Color
COLOR_MUTED = colors.HexColor("#555555")       # Gray subtitle
COLOR_BORDER = colors.HexColor("#E0E4F0")      # Table border

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

def escape_xml(text):
    """Escapes XML entities and unicode dashes for ReportLab Paragraphs."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("—", "&mdash;").replace("–", "&ndash;")
    return text

def format_subscripts(text):
    """
    Format common CS/Math subscripts such as 26_10, 3F_16, 101101_2, 26(10), or explicit _sub / ^sup.
    """
    # Convert explicit _2, _10, _16 or _{sub}
    text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
    text = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', text)
    text = re.sub(r'\_([0-9a-zA-Z]+)', r'<sub>\1</sub>', text)
    text = re.sub(r'\^([0-9a-zA-Z]+)', r'<sup>\1</sup>', text)
    
    # Also handle patterns like 26(10) -> 26_10
    text = re.sub(r'\(10\)', r'<sub>10</sub>', text)
    text = re.sub(r'\(16\)', r'<sub>16</sub>', text)
    text = re.sub(r'\(2\)', r'<sub>2</sub>', text)
    return text

QUESTION_START_RE = re.compile(r"^(?:(?:Q|Question)\s*)?(\d+)[\.\)]\s*(.*)$", re.IGNORECASE)
SUBPART_START_RE = re.compile(r"^\(?([a-z]|[ivx]+)\)[\.\)]\s*(.*)$", re.IGNORECASE)

def parse_input_text(raw_text):
    """
    Intelligently parses pasted text into structured questions (MCQs and Structured Questions).
    """
    lines = raw_text.splitlines()
    questions = []
    current_q = None
    current_section = "MCQs"
    
    meta_title = None
    meta_unit = None
    meta_tutorial = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current_q and current_q["type"] == "structured":
                current_q["lines"].append("")
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
            current_section = "MCQs"
            continue
        if low.startswith("structured questions") or low.startswith("section b"):
            current_section = "Structured"
            continue

        # Check for Question Start (e.g., "1. What is...")
        qm = QUESTION_START_RE.match(line)
        is_sub_numbered = (current_section == "Structured" and current_q and line.startswith(("1.", "2.", "3.", "1)", "2)")) and (line.endswith("...") or len(line) < 40 or "..." in line))
        
        if qm and not is_sub_numbered:
            if current_q:
                questions.append(current_q)
            q_num = int(qm.group(1))
            q_text = qm.group(2).strip()
            current_q = {
                "number": q_num,
                "text": q_text,
                "type": "mcq" if current_section == "MCQs" else "structured",
                "section": current_section,
                "options": [],
                "lines": []
            }
            continue

        # Check for MCQ Option (e.g., "A. 11010") - only in MCQ mode
        if current_section == "MCQs" and current_q and current_q["type"] == "mcq":
            om = re.match(r"^\(?([A-D])[\.\)]\s*(.*)$", line)
            if om:
                opt_letter = om.group(1).upper()
                opt_text = om.group(2).strip()
                current_q["options"].append((opt_letter, opt_text))
                continue

        # If we have an active question, append as structured / extra line
        if current_q:
            if current_q["type"] == "mcq" and len(current_q["options"]) == 0:
                current_q["text"] += " " + line
            else:
                if current_section == "Structured":
                    current_q["type"] = "structured"
                current_q["lines"].append(line)
        else:
            # Skip loose leading blank or header-like lines before question 1
            if len(line) < 30 and ("exam" in low or "paper" in low or "cambridge" in low or "grade" in low):
                continue
            # First item without explicit number
            current_q = {
                "number": 1,
                "text": line,
                "type": "mcq" if current_section == "MCQs" else "structured",
                "section": current_section,
                "options": [],
                "lines": []
            }

    if current_q:
        questions.append(current_q)

    # Renumber sequentially
    for idx, q in enumerate(questions, 1):
        q["display_number"] = idx

    return {
        "title": meta_title,
        "unit": meta_unit,
        "tutorial": meta_tutorial,
        "questions": questions
    }


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total pages and draw exact watermark seal
    and footer contact strip matching Tute_1_CMB_DataRepresentation.pdf.
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

        # 1. Outer Page Border (Exact Camdex Navy Border on ALL interior pages: Page 2, 3, 4...)
        self.setStrokeColor(COLOR_PRIMARY)
        self.setLineWidth(1.2)
        self.rect(24.0, 24.0, PAGE_WIDTH - 48.0, PAGE_HEIGHT - 48.0, stroke=1, fill=0)

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
        
        r = 5.0
        
        # ---------------- LINE 1: Phone + Website ----------------
        y1 = 43.0
        gap = 20.0
        item1_w = 14.0 + p_w
        item2_w = 14.0 + w_w
        total_l1_w = item1_w + gap + item2_w
        x1 = (PAGE_WIDTH - total_l1_w) / 2.0
        
        # 1. Phone Icon
        icon_phone = os.path.join(DEFAULTS_DIR, "icon_phone.png")
        if os.path.exists(icon_phone):
            self.drawImage(icon_phone, x1, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            self.circle(x1 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        self.drawString(x1 + 13.5, y1, phone_text)
        
        # 2. Globe Icon
        x2 = x1 + item1_w + gap
        icon_globe = os.path.join(DEFAULTS_DIR, "icon_globe.png")
        if os.path.exists(icon_globe):
            self.drawImage(icon_globe, x2, y1 - 1.0, width=10.0, height=10.0, preserveAspectRatio=True, mask='auto')
        else:
            self.circle(x2 + 5.0, y1 + 4.0, 5.0, stroke=0, fill=1)
        self.drawString(x2 + 13.5, y1, web_text)
        
        # ---------------- LINE 2: Location Pin ----------------
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


def create_teacher_card_image(photo_path=None, output_path=None):
    """
    If photo_path is provided, uses the uploaded image directly without drawing
    an artificial background arch that creates double-lines/artifacts.
    If no photo is provided, renders the clean solid blue arch (#163A8B).
    """
    if photo_path and os.path.exists(photo_path):
        return photo_path
        
    arch_path = os.path.join(DEFAULTS_DIR, "blue_arch.png")
    if not os.path.exists(arch_path):
        from PIL import ImageDraw
        arch_w, arch_h = 500, 840
        arch_im = Image.new('RGBA', (arch_w, arch_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(arch_im)
        arch_color = (22, 58, 139, 255)
        draw.pieslice([0, 0, arch_w, arch_w], 180, 360, fill=arch_color)
        draw.rectangle([0, arch_w//2, arch_w, arch_h], fill=arch_color)
        os.makedirs(DEFAULTS_DIR, exist_ok=True)
        arch_im.save(arch_path)
    return arch_path


def build_tutorial_pdf(
    raw_text,
    subject="Computer Science",
    board="CMB",
    unit_title="Data Representation",
    tutorial_num="Tutorial 1",
    curriculum_title="Cambridge IGCSE O/L",
    include_intro=True,
    include_teacher=True,
    teacher_name="Mr. Raaid",
    teacher_qualifications="BSc (Hons) in Computer Science, MSc",
    teacher_subject="Computer Science & ICT Lead",
    teacher_message="Welcome to this tutorial! Ensure all MCQs and structured questions are carefully answered. Practice consistently for exam success.",
    teacher_photo_path=None,
    custom_cover_path=None,
    font_color_hex="#1A4199",
    watermark_opacity=0.22,
    page_size=letter
):
    """
    Compiles full high-res tutorial PDF with Cover, Intro, Teacher Profile, and Questions.
    Matches exact reference PDF layout, typography, underlines, and spacing.
    """
    parsed = parse_input_text(raw_text)
    questions = parsed["questions"]
    if not questions:
        raise ValueError("No questions detected in the input text. Please paste questions.")

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
    
    # Exact Camdex Deep Royal Blue
    text_color = colors.HexColor(font_color_hex)

    title_main_style = ParagraphStyle(
        "TutMainTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceAfter=14
    )

    unit_title_style = ParagraphStyle(
        "TutUnitTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceAfter=14
    )

    tutorial_sub_style = ParagraphStyle(
        "TutSubTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceAfter=24
    )

    section_heading_style = ParagraphStyle(
        "TutSectionHeading",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=15,
        leading=19,
        textColor=text_color,
        spaceBefore=10,
        spaceAfter=12
    )

    # Question Prompt: starts at x=72pt, number + text with clean line height
    q_text_style = ParagraphStyle(
        "QuestionText",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12.0,
        leading=15.0,
        textColor=text_color,
        leftIndent=18,
        firstLineIndent=-18,
        spaceAfter=3
    )

    # MCQ Options: indented at x=90pt (leftIndent=18)
    opt_style = ParagraphStyle(
        "OptionStyle",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12.0,
        leading=14.5,
        textColor=text_color,
        leftIndent=18,
        spaceAfter=1.0
    )

    structured_line_style = ParagraphStyle(
        "StructuredLine",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11.5,
        leading=15.0,
        textColor=text_color,
        leftIndent=18,
        spaceAfter=2.5
    )

    dotted_line_style = ParagraphStyle(
        "DottedLine",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#666666"),
        leftIndent=18,
        spaceAfter=3
    )

    intro_heading_style = ParagraphStyle(
        "IntroHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=COLOR_PRIMARY,
        spaceAfter=10
    )

    intro_body_style = ParagraphStyle(
        "IntroBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15.5,
        textColor=colors.HexColor("#333333"),
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )

    # Document Template with exact reference side margins (54pt matching reference)
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
    # Drawn completely via canvas callback
    cover_pages_count += 1
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ==================== PAGE 2: ABOUT INSTITUTE PAGE ====================
    if include_intro:
        cover_pages_count += 1
        
        # Position logo at upper lower half matching reference
        story.append(Spacer(1, 270))

        # Camdex Brand Logo on the left using Horizontal Colored Versions -02.png (trimmed)
        logo_img = os.path.join(DEFAULTS_DIR, "p2_logo_h02_clean.png")
        if not os.path.exists(logo_img):
            logo_img = os.path.join(LOGOS_DIR, "Horizontal Colored Versions -02.png")
        if not os.path.exists(logo_img):
            logo_img = os.path.join(DEFAULTS_DIR, "logo_horizontal.png")
        
        if os.path.exists(logo_img):
            story.append(PlatypusImage(logo_img, width=150, height=75, hAlign="LEFT"))
            story.append(Spacer(1, 24))

        # 3 Paragraphs matching exact reference layout, font, size, line breaks, and color (Fully Justified)
        about_text_style = ParagraphStyle(
            "AboutTextStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11.0,
            leading=14.5,
            textColor=colors.HexColor("#4E80BC"),
            alignment=TA_JUSTIFY,
            spaceAfter=14
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

    # ==================== PAGE 3: TEACHER / TUTOR PROFILE PAGE ====================
    if include_teacher:
        cover_pages_count += 1
        
        # Position profile in lower half matching reference layout
        story.append(Spacer(1, 215))

        # Teacher Name (uppercase, bold navy)
        name_text = str(teacher_name or "").strip().upper()
        if not name_text:
            name_text = "MR. YUSUF SHIHAM"

        # Teacher Subject Role (uppercase, vibrant light blue)
        subject_text = str(teacher_subject or "").strip().upper()
        if not subject_text:
            subject_text = "COMPUTER SCIENCE TUTOR"

        # Qualifications / Subheading
        qual_text = str(teacher_qualifications or "").strip()
        if not qual_text:
            qual_text = "Undergraduate- BSc. Hons Information Technology<br/>specializing in Artificial Intelligence(Reading)"

        # Bio / Description paragraphs
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

        # Typography: Bebas Neue for titles, Poppins for body/quals
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        has_bebas = "BebasNeue" in registered_fonts
        has_poppins = "Poppins" in registered_fonts

        name_font = "BebasNeue" if has_bebas else "Helvetica-Bold"
        body_font = "Poppins" if has_poppins else "Helvetica"

        name_style = ParagraphStyle(
            'TName',
            parent=styles['Normal'],
            fontName=name_font,
            fontSize=34.0,
            leading=33.0,
            textColor=colors.HexColor('#163A8B'),
            spaceAfter=2
        )

        role_style = ParagraphStyle(
            'TRole',
            parent=styles['Normal'],
            fontName=name_font,
            fontSize=19.5,
            leading=20.0,
            textColor=colors.HexColor('#3577D6'),
            spaceAfter=8
        )

        qual_style = ParagraphStyle(
            'TQual',
            parent=styles['Normal'],
            fontName=body_font,
            fontSize=8.4,
            leading=11.6,
            textColor=colors.HexColor('#224483'),
            spaceAfter=11
        )

        bio_style = ParagraphStyle(
            'TBio',
            parent=styles['Normal'],
            fontName=body_font,
            fontSize=8.4,
            leading=12.5,
            textColor=colors.HexColor('#224483'),
            alignment=TA_JUSTIFY,
            spaceAfter=9
        )

        info_flowables = [
            Paragraph(name_text, name_style),
            Paragraph(subject_text, role_style),
            Paragraph(qual_text.replace("\n", "<br/>"), qual_style)
        ]

        # Parse bio paragraphs
        for para in bio_raw.split("\n\n"):
            p_clean = para.strip().replace("\n", " ")
            if p_clean:
                p_html = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', p_clean)
                info_flowables.append(Paragraph(p_html, bio_style))

        # Teacher Photo Column: renders uploaded image if provided, else clean blank space
        if teacher_photo_path and os.path.exists(teacher_photo_path):
            try:
                im = Image.open(teacher_photo_path)
                aspect = im.width / im.height
                target_h = 276.0
                target_w = target_h * aspect
                if target_w > 195.0:
                    target_w = 195.0
                    target_h = target_w / aspect
                photo_flowable = PlatypusImage(teacher_photo_path, width=target_w, height=target_h, hAlign='CENTER')
            except Exception:
                photo_flowable = PlatypusImage(teacher_photo_path, width=195, height=276, hAlign='CENTER')
        else:
            # Clean blank placeholder matching exact dimensions
            photo_flowable = Spacer(195, 276)

        profile_table = Table([[photo_flowable, info_flowables]], colWidths=[195, 238], hAlign='CENTER')
        profile_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (0,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (1,0), (1,-1), 28),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(profile_table)
        story.append(PageBreak())

    # ==================== PAGE 4+: QUESTIONS CONTENT ====================
    # Exact Underlined Headers matching Reference
    story.append(Paragraph(f"<u><b>{escape_xml(curriculum_title)}</b></u>", title_main_style))
    story.append(Paragraph(f"<u><b>Unit: {escape_xml(unit_title)}</b></u>", unit_title_style))
    story.append(Paragraph(f"<b>{escape_xml(tutorial_num)}</b>", tutorial_sub_style))
    story.append(Spacer(1, 6))

    current_sec = None
    for q in questions:
        q_sec = q.get("section", "MCQs")
        if q_sec != current_sec:
            current_sec = q_sec
            sec_title = "MCQs" if current_sec == "MCQs" else "Structured Questions:"
            story.append(Paragraph(f"<u><b>{sec_title}</b></u>", section_heading_style))

        q_block = []
        
        # Format Question Title & Number (e.g. "1. What is...")
        q_num = q["display_number"]
        q_text_escaped = format_subscripts(escape_xml(q["text"]))
        full_q_paragraph = Paragraph(f"{q_num}. &nbsp;{q_text_escaped}", q_text_style)
        q_block.append(full_q_paragraph)

        # Format MCQ Options (e.g. "A. 11010")
        if q["options"]:
            for letter, opt_text in q["options"]:
                opt_escaped = format_subscripts(escape_xml(opt_text))
                q_block.append(Paragraph(f"{letter}. &nbsp;{opt_escaped}", opt_style))

        # Format Structured lines / sub-questions
        if q.get("lines"):
            for l in q["lines"]:
                if not l.strip():
                    q_block.append(Spacer(1, 4))
                    continue
                if l.strip().startswith("...") or "..." in l:
                    q_block.append(Paragraph(escape_xml(l), dotted_line_style))
                else:
                    line_escaped = format_subscripts(escape_xml(l))
                    q_block.append(Paragraph(line_escaped, structured_line_style))

        # Space between questions matching reference (~10pt)
        q_block.append(Spacer(1, 10))
        story.append(KeepTogether(q_block))

    # Canvas Drawing Callbacks
    def draw_cover_canvas(c, d):
        c.saveState()
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                c.drawImage(cover_image_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            except Exception:
                pass
        
        # Overlay Unit Title on cover (matching exact position from reference)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(25.0, 458.0, str(unit_title))
        
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
