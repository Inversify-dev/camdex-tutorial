import base64
import json
import os
import re
import streamlit as st
from PIL import Image

import pdf_generator

# Page Configuration
st.set_page_config(
    page_title="CAMDEX Tutorial PDF Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design & Modern Look
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
    }
    
    .camdex-header {
        background: linear-gradient(135deg, #0f2b6b 0%, #1A4199 50%, #295bcc 100%);
        padding: 22px 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px -5px rgba(26, 65, 153, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .camdex-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    
    .camdex-subtitle {
        font-size: 13.5px;
        color: #d1dcff;
        margin-top: 4px;
        font-weight: 400;
    }
    
    .badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: #ffffff;
        backdrop-filter: blur(10px);
    }
    
    .stat-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    
    .stat-num {
        font-size: 22px;
        font-weight: 700;
        color: #1A4199;
    }
    
    .stat-label {
        font-size: 11.5px;
        color: #64748b;
        font-weight: 500;
    }
    
    .stButton>button {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton>button {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3);
    }
    
    .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Teacher Library Management
TEACHERS_FILE = os.path.join(pdf_generator.BASE_DIR, "teachers.json")

def load_teachers():
    if os.path.exists(TEACHERS_FILE):
        try:
            with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {
            "id": "raaid",
            "name": "Mr. Raaid",
            "subject": "Computer Science & ICT Lead",
            "qualifications": "BSc (Hons) in Computer Science, MSc",
            "message": "Welcome to this tutorial! Ensure all MCQs and structured questions are carefully answered. Practice consistently for exam success.",
            "photo": "assets/defaults/default_teacher.jpeg",
            "subjects_taught": ["Computer Science", "ICT"]
        }
    ]

def save_teachers(teachers_data):
    try:
        with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(teachers_data, f, indent=2)
        return True
    except Exception:
        return False

# Sample Questions for Quick Testing
SAMPLE_MCQ_TEXT = """Cambridge IGCSE O/L
Unit: Data Representation
Tutorial 1

MCQs

1. What is the binary equivalent of 26(10)?
A. 11010
B. 10101
C. 11100
D. 10011

2. Convert 3F(16) to denary.
A. 31
B. 63
C. 45
D. 72

3. Why do computers prefer binary representation?
A. Faster arithmetic
B. Simple representation of On/Off states
C. Easier for humans to read
D. Saves memory

4. Convert 101101(2) to denary.
A. 42
B. 45
C. 37
D. 49

5. Convert 255(10) to hexadecimal.
A. FE
B. FF
C. 1F
D. F1

6. Which hexadecimal digit equals 1111(2)?
A. F
B. E
C. D
D. C

7. Convert 7A(16) to binary.
A. 01111011
B. 01111010
C. 01111110
D. 01110110

8. What is the result of 1010(2) + 0110(2)?
A. 10000
B. 1110
C. 10100
D. 1100

9. Which operation does a logical left shift correspond to?
A. Multiply by 4
B. Multiply by 2
C. Divide by 2
D. Subtract by 2

10. Shifting 00010101(2) one place left gives:
A. 00101010
B. 00001010
C. 01010100
D. 00010110
"""

SAMPLE_MIXED_TEXT = SAMPLE_MCQ_TEXT + """

Structured Questions:

11. Binary numbers can be converted to hexadecimal.
a. Convert the two binary numbers to hexadecimal:
i. 10010011
........................................................................................................................
ii. 00001101
........................................................................................................................

b. State two reasons why programmers use hexadecimal notation instead of binary.
1. ....................................................................................................................
2. ....................................................................................................................

c. Explain the effect of a logical right shift of 2 places on an unsigned binary integer.
........................................................................................................................
........................................................................................................................
"""

# Header Banner
st.markdown(
    """
    <div class="camdex-header">
        <div>
            <div class="camdex-title">🎓 CAMDEX Tutorial PDF Generator</div>
            <div class="camdex-subtitle">Automated, High-Resolution Worksheet & Exam Tutorial Publisher</div>
        </div>
        <div class="badge">⚡ Zero Cost • 100% Automated</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### 📚 Syllabus & Subject")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        board_option = st.selectbox(
            "Exam Board",
            ["Cambridge (CMB)", "Edexcel (EDX)"],
            index=0
        )
        board_code = "CMB" if "CMB" in board_option else "EDX"
    
    with col_b2:
        subject_list = [
            "Computer Science", "Mathematics", "Physics", "Chemistry",
            "Biology", "ICT", "Business", "Economics", "Accounting",
            "English", "Science"
        ]
        selected_subject = st.selectbox("Subject", subject_list, index=0)

    unit_title = st.text_input("Unit / Topic Title", value="Data Representation")
    tutorial_number = st.text_input("Tutorial # / Title", value="Tutorial 1")
    
    curriculum_default = "Cambridge IGCSE O/L" if board_code == "CMB" else "Edexcel International GCSE"
    curriculum_title = st.text_input("Curriculum Header", value=curriculum_default)

    st.markdown("---")
    st.markdown("### 👤 Teacher Profile (Page 3)")
    
    teacher_name = st.text_input(
        "Teacher Name",
        value="",
        placeholder="e.g. MR. YUSUF SHIHAM"
    )
    teacher_subject = st.text_input(
        "Subject Role / Title",
        value="",
        placeholder="e.g. COMPUTER SCIENCE TUTOR"
    )
    teacher_qual = st.text_input(
        "Qualifications / Subheading",
        value="",
        placeholder="e.g. Undergraduate- BSc. Hons Information Technology specializing in Artificial Intelligence(Reading)"
    )
    teacher_msg = st.text_area(
        "Teacher Bio / Description",
        value="",
        height=140,
        placeholder="Currently pursuing a degree in Artificial Intelligence at the Sri Lanka Institute of Information Technology, Mr. Yusuf brings together academic excellence and a deep enthusiasm for teaching.\n\nHe is dedicated to fostering an engaging and intellectually enriching learning atmosphere, where students not only gain confidence in Computer Science but also strengthen their analytical and problem-solving abilities.\n\nAt CAMDEX Education, he teaches Computer Science for Edexcel and Cambridge O/Level students..."
    )
    uploaded_teacher_photo = st.file_uploader(
        "Upload Teacher Photo (Optional - Cutout/Portrait)",
        type=["png", "jpg", "jpeg"]
    )

    st.markdown("---")
    st.markdown("### ⚙️ Document Layout")
    include_cover = st.checkbox("Include Subject Cover Page (Page 1)", value=True)
    include_intro = st.checkbox("Include Institute About Page (Page 2)", value=True)
    include_teacher = st.checkbox("Include Teacher Profile Page (Page 3)", value=True)
    
    custom_cover_upload = st.file_uploader("Upload Custom Cover (Optional)", type=["png", "jpg", "jpeg"])

# Resolve Teacher Photo Path (blank if none uploaded)
temp_teacher_photo_path = None
if uploaded_teacher_photo:
    temp_dir = os.path.join(pdf_generator.BASE_DIR, "assets", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_teacher_photo_path = os.path.join(temp_dir, f"uploaded_teacher_{uploaded_teacher_photo.name}")
    with open(temp_teacher_photo_path, "wb") as f:
        f.write(uploaded_teacher_photo.getbuffer())

temp_cover_path = None
if custom_cover_upload:
    temp_dir = os.path.join(pdf_generator.BASE_DIR, "assets", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_cover_path = os.path.join(temp_dir, f"uploaded_cover_{custom_cover_upload.name}")
    with open(temp_cover_path, "wb") as f:
        f.write(custom_cover_upload.getbuffer())

# ----------------- MAIN WORKSPACE -----------------
main_col, preview_col = st.columns([1.1, 0.9])

with main_col:
    st.markdown("#### 📝 Paste Your Questions")
    
    # Quick Sample Buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("📋 Load MCQs Sample", use_container_width=True):
            st.session_state["questions_input"] = SAMPLE_MCQ_TEXT
    with btn_col2:
        if st.button("📑 Load Mixed Sample", use_container_width=True):
            st.session_state["questions_input"] = SAMPLE_MIXED_TEXT
    with btn_col3:
        if st.button("🗑️ Clear Input", use_container_width=True):
            st.session_state["questions_input"] = ""

    current_input_val = st.session_state.get("questions_input", SAMPLE_MCQ_TEXT)

    raw_text = st.text_area(
        "Questions Editor",
        value=current_input_val,
        height=420,
        placeholder="Paste your questions here...\n1. Question text\nA. Option 1\nB. Option 2\nC. Option 3\nD. Option 4",
        label_visibility="collapsed"
    )

    # Parsing Analysis
    parsed_info = pdf_generator.parse_input_text(raw_text)
    total_q = len(parsed_info["questions"])
    mcq_count = sum(1 for q in parsed_info["questions"] if q["type"] == "mcq")
    structured_count = total_q - mcq_count

    # Statistics Bar
    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0;">
            <div class="stat-card">
                <div class="stat-num">{total_q}</div>
                <div class="stat-label">Total Questions</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{mcq_count}</div>
                <div class="stat-label">MCQs Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{structured_count}</div>
                <div class="stat-label">Structured Questions</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    generate_btn = st.button("🚀 Generate High-Resolution PDF", type="primary", use_container_width=True)

# Generate PDF State
if generate_btn or "generated_pdf" in st.session_state:
    if generate_btn:
        try:
            with st.spinner("Compiling high-resolution PDF..."):
                pdf_bytes, q_count = pdf_generator.build_tutorial_pdf(
                    raw_text=raw_text,
                    subject=selected_subject,
                    board=board_code,
                    unit_title=unit_title,
                    tutorial_num=tutorial_number,
                    curriculum_title=curriculum_title,
                    include_intro=include_intro,
                    include_teacher=include_teacher,
                    teacher_name=teacher_name,
                    teacher_qualifications=teacher_qual,
                    teacher_subject=teacher_subject,
                    teacher_message=teacher_msg,
                    teacher_photo_path=temp_teacher_photo_path,
                    custom_cover_path=temp_cover_path,
                    font_color_hex="#1A4199",
                    watermark_opacity=0.22
                )
                st.session_state["generated_pdf"] = pdf_bytes
                st.session_state["pdf_q_count"] = q_count
        except Exception as e:
            st.error(f"Generation error: {str(e)}")

with preview_col:
    st.markdown("#### 📄 PDF Output & Download")
    
    if "generated_pdf" in st.session_state:
        pdf_bytes = st.session_state["generated_pdf"]
        q_count = st.session_state.get("pdf_q_count", total_q)
        
        # Clean safe filename: tute_tutorialnumber_subjectname_Unittopic
        clean_tut = re.sub(r'[^a-zA-Z0-9]', '', str(tutorial_number or "1"))
        clean_subject = re.sub(r'[^a-zA-Z0-9]', '', str(selected_subject or "Subject"))
        clean_unit = re.sub(r'[^a-zA-Z0-9]', '', str(unit_title or "Topic"))
        filename = f"tute_{clean_tut}_{clean_subject}_{clean_unit}.pdf"

        st.success(f"✓ PDF successfully created ({q_count} questions rendered)")
        
        st.download_button(
            label=f"⬇️ Download {filename}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Embedded PDF Viewer
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=1&navpanes=0&scrollbar=1" width="100%" height="600" style="border: 1px solid #cbd5e1; border-radius: 8px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("👈 Click **'Generate High-Resolution PDF'** to build and preview your formatted tutorial PDF.")
        
        # Show placeholder preview
        st.markdown(
            f"""
            <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; height: 560px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; text-align: center; padding: 24px;">
                <div style="font-size: 48px; margin-bottom: 12px;">📑</div>
                <div style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 6px;">Ready to Generate</div>
                <div style="font-size: 14px; max-width: 320px;">
                    Selected: <b>{selected_subject} ({board_code})</b><br/>
                    Unit: <b>{unit_title}</b> • {tutorial_number}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
