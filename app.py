import base64
import json
import os
import re
import streamlit as st
from PIL import Image

import pdf_generator

# Page Configuration & Official CAMDEX Favicon
FAVICON_PATH = os.path.join(pdf_generator.BASE_DIR, "assets", "logos", "Seal Logo Colored Version-01.png")
try:
    favicon_img = Image.open(FAVICON_PATH)
except Exception:
    favicon_img = "📘"

st.set_page_config(
    page_title="CAMDEX Tutorial PDF Generator",
    page_icon=favicon_img,
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

def deduplicate_teachers(teachers_list):
    """Ensure no duplicate teachers exist by id or normalized name."""
    seen_ids = set()
    seen_names = set()
    unique_list = []
    for t in teachers_list:
        tid = t.get("id", "").strip().lower()
        tname = t.get("name", "").strip().upper()
        if tid and tid not in seen_ids and tname not in seen_names:
            seen_ids.add(tid)
            seen_names.add(tname)
            unique_list.append(t)
    return unique_list

def load_teachers():
    if os.path.exists(TEACHERS_FILE):
        try:
            with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return deduplicate_teachers(data)
        except Exception:
            pass
    return []

def save_teachers(teachers_data):
    try:
        clean_data = deduplicate_teachers(teachers_data)
        with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=2)
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
            <div class="camdex-title">CAMDEX Tutorial PDF Generator</div>
            <div class="camdex-subtitle">High-Resolution Worksheet & Exam Tutorial Publisher</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    brand_logo_path = os.path.join(pdf_generator.BASE_DIR, "assets", "logos", "Horizontal Colored Versions -01.png")
    if os.path.exists(brand_logo_path):
        st.image(brand_logo_path, width="stretch")
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        st.markdown("---")

    st.markdown("### Syllabus & Subject")
    
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
    st.markdown("### Teacher Profile (Page 3)")
    
    teachers_data = load_teachers()
    if not teachers_data:
        teachers_data = [{
            "id": "default",
            "name": "Teacher Name",
            "subject": "TUTOR",
            "qualifications": "Qualifications",
            "message": "Teacher Bio",
            "photo": "",
            "subjects_taught": []
        }]

    teacher_display_list = [f"{t['name']} ({t['subject']})" for t in teachers_data]
    teacher_map = {f"{t['name']} ({t['subject']})": t for t in teachers_data}
    id_to_label = {t["id"]: f"{t['name']} ({t['subject']})" for t in teachers_data}

    # Handle pending teacher selection from actions (Add, Delete, etc.) BEFORE widgets instantiate
    if "pending_teacher_id" in st.session_state:
        target_id = st.session_state.pop("pending_teacher_id")
        matched_t = next((t for t in teachers_data if t["id"] == target_id), teachers_data[0])
        st.session_state["active_teacher_id"] = matched_t["id"]
        st.session_state["teacher_name_input"] = matched_t["name"]
        st.session_state["teacher_subject_input"] = matched_t["subject"]
        st.session_state["teacher_qual_input"] = matched_t["qualifications"]
        st.session_state["teacher_msg_input"] = matched_t["message"]
        st.session_state["teacher_photo_path_active"] = matched_t.get("photo", "")
        st.session_state["teacher_dropdown_selector"] = f"{matched_t['name']} ({matched_t['subject']})"

    # Auto-match teacher based on selected subject if not yet initialized
    if "active_teacher_id" not in st.session_state:
        def_t = teachers_data[0]
        for t in teachers_data:
            if selected_subject in t.get("subjects_taught", []):
                def_t = t
                break
        st.session_state["active_teacher_id"] = def_t["id"]
        st.session_state["teacher_name_input"] = def_t["name"]
        st.session_state["teacher_subject_input"] = def_t["subject"]
        st.session_state["teacher_qual_input"] = def_t["qualifications"]
        st.session_state["teacher_msg_input"] = def_t["message"]
        st.session_state["teacher_photo_path_active"] = def_t.get("photo", "")
        st.session_state["teacher_dropdown_selector"] = f"{def_t['name']} ({def_t['subject']})"

    def on_teacher_select():
        chosen_label = st.session_state.get("teacher_dropdown_selector")
        if chosen_label in teacher_map:
            t = teacher_map[chosen_label]
            st.session_state["active_teacher_id"] = t["id"]
            st.session_state["teacher_name_input"] = t["name"]
            st.session_state["teacher_subject_input"] = t["subject"]
            st.session_state["teacher_qual_input"] = t["qualifications"]
            st.session_state["teacher_msg_input"] = t["message"]
            st.session_state["teacher_photo_path_active"] = t.get("photo", "")

    # Ensure dropdown selection is valid
    current_active_id = st.session_state.get("active_teacher_id", teachers_data[0]["id"])
    default_dropdown_label = id_to_label.get(current_active_id, teacher_display_list[0])
    
    dropdown_index = 0
    if default_dropdown_label in teacher_display_list:
        dropdown_index = teacher_display_list.index(default_dropdown_label)

    st.selectbox(
        "Select Teacher Profile",
        options=teacher_display_list,
        index=dropdown_index,
        key="teacher_dropdown_selector",
        on_change=on_teacher_select
    )

    teacher_name = st.text_input(
        "Teacher Name",
        key="teacher_name_input",
        placeholder="e.g. MR. YUSUF SHIHAM"
    )
    teacher_subject = st.text_input(
        "Subject Role / Title",
        key="teacher_subject_input",
        placeholder="e.g. COMPUTER SCIENCE TUTOR"
    )
    teacher_qual = st.text_input(
        "Qualifications / Subheading",
        key="teacher_qual_input",
        placeholder="e.g. Undergraduate- BSc. Hons Information Technology"
    )
    teacher_msg = st.text_area(
        "Teacher Bio / Description",
        key="teacher_msg_input",
        height=140,
        placeholder="Teacher bio description..."
    )

    active_photo = st.session_state.get("teacher_photo_path_active", "")
    full_active_photo_path = os.path.join(pdf_generator.BASE_DIR, active_photo) if active_photo else ""

    uploaded_teacher_photo = st.file_uploader(
        "Upload Custom Teacher Photo for this PDF",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_teacher_photo:
        st.caption("Using uploaded photo for current PDF:")
        st.image(uploaded_teacher_photo, width=120)
    elif full_active_photo_path and os.path.exists(full_active_photo_path):
        st.caption(f"Preloaded photo for {teacher_name}:")
        st.image(full_active_photo_path, width=120)

    # ---------------- DYNAMIC TEACHER LIBRARY MANAGER ----------------
    with st.expander("Manage Teacher Library (Add / Edit / Remove)"):
        tab_add, tab_update, tab_delete = st.tabs(["Add New Teacher", "Update Current", "Delete"])
        
        with tab_add:
            st.markdown("##### Add New Teacher to Permanent Library")
            new_t_name = st.text_input("Full Name", placeholder="e.g. DR. SARAH PERERA", key="new_t_name")
            new_t_role = st.text_input("Role / Title", placeholder="e.g. PHYSICS TUTOR", key="new_t_role")
            new_t_qual = st.text_input("Qualifications", placeholder="e.g. BSc. (Hons) Physics, MSc.", key="new_t_qual")
            new_t_bio = st.text_area("Teacher Bio / Description", height=100, placeholder="Teacher description and achievements...", key="new_t_bio")
            new_t_photo = st.file_uploader("Upload Profile Photo", type=["png", "jpg", "jpeg"], key="new_t_photo")
            
            if st.button("Save New Teacher to Library", type="primary", width="stretch"):
                if not new_t_name.strip():
                    st.error("Please enter teacher name.")
                else:
                    norm_name = new_t_name.strip().upper()
                    slug_id = re.sub(r'[^a-z0-9]', '', new_t_name.lower().replace("mr.", "").replace("ms.", "").replace("dr.", "").strip())
                    if not slug_id:
                        slug_id = f"teacher_{len(teachers_data) + 1}"
                    
                    photo_rel_path = ""
                    if new_t_photo:
                        photo_filename = f"{slug_id}.png"
                        target_photo_path = os.path.join(pdf_generator.BASE_DIR, "assets", "teachers", photo_filename)
                        os.makedirs(os.path.dirname(target_photo_path), exist_ok=True)
                        with open(target_photo_path, "wb") as f:
                            f.write(new_t_photo.getbuffer())
                        photo_rel_path = f"assets/teachers/{photo_filename}"
                    
                    new_teacher_obj = {
                        "id": slug_id,
                        "name": norm_name,
                        "subject": new_t_role.strip().upper() if new_t_role else "TUTOR",
                        "qualifications": new_t_qual.strip(),
                        "message": new_t_bio.strip(),
                        "photo": photo_rel_path,
                        "subjects_taught": []
                    }
                    
                    # Upsert: If teacher exists with same ID or name, update them; otherwise append
                    existing_idx = -1
                    for idx, t in enumerate(teachers_data):
                        if t.get("id", "").lower() == slug_id or t.get("name", "").strip().upper() == norm_name:
                            existing_idx = idx
                            break
                    
                    if existing_idx >= 0:
                        if not photo_rel_path and teachers_data[existing_idx].get("photo"):
                            new_teacher_obj["photo"] = teachers_data[existing_idx]["photo"]
                        teachers_data[existing_idx] = new_teacher_obj
                    else:
                        teachers_data.append(new_teacher_obj)
                    
                    if save_teachers(teachers_data):
                        st.session_state["pending_teacher_id"] = slug_id
                        st.success(f"Saved {norm_name} to library!")
                        st.rerun()
                    else:
                        st.error("Failed to save teacher to teachers.json.")

        with tab_update:
            st.markdown("##### Permanently Save Current Edits")
            st.write(f"Save any modifications made above for **{teacher_name}**.")
            
            if st.button("Update This Teacher in Library", width="stretch"):
                chosen_label = st.session_state.get("teacher_dropdown_selector")
                if chosen_label in teacher_map:
                    t_to_update = teacher_map[chosen_label]
                    for t in teachers_data:
                        if t["id"] == t_to_update["id"]:
                            t["name"] = teacher_name
                            t["subject"] = teacher_subject
                            t["qualifications"] = teacher_qual
                            t["message"] = teacher_msg
                            if uploaded_teacher_photo:
                                photo_filename = f"{t['id']}.png"
                                target_photo_path = os.path.join(pdf_generator.BASE_DIR, "assets", "teachers", photo_filename)
                                os.makedirs(os.path.dirname(target_photo_path), exist_ok=True)
                                with open(target_photo_path, "wb") as f:
                                    f.write(uploaded_teacher_photo.getbuffer())
                                t["photo"] = f"assets/teachers/{photo_filename}"
                            break
                    if save_teachers(teachers_data):
                        st.session_state["pending_teacher_id"] = t_to_update["id"]
                        st.success(f"Updated {teacher_name} in library!")
                        st.rerun()
                    else:
                        st.error("Failed to update teacher in teachers.json.")

        with tab_delete:
            st.markdown("##### Delete Teacher from Library")
            teacher_to_del_label = st.selectbox(
                "Select Teacher to Delete",
                options=teacher_display_list,
                key="del_teacher_sel"
            )
            confirm_del = st.checkbox("I confirm I want to permanently delete this teacher", key="confirm_del_chk")
            if st.button("Delete Teacher", type="secondary", width="stretch"):
                if not confirm_del:
                    st.warning("Please tick the confirmation checkbox to delete.")
                elif len(teachers_data) <= 1:
                    st.error("Cannot delete the only remaining teacher.")
                else:
                    t_del = teacher_map.get(teacher_to_del_label)
                    if t_del:
                        remaining_teachers = [t for t in teachers_data if t["id"] != t_del["id"]]
                        if save_teachers(remaining_teachers):
                            st.session_state["pending_teacher_id"] = remaining_teachers[0]["id"]
                            st.success(f"Deleted teacher from library!")
                            st.rerun()
                        else:
                            st.error("Failed to update teachers.json.")

    st.markdown("---")
    st.markdown("### Document Layout")
    include_intro = st.checkbox("Include Institute About Page (Page 2)", value=True)
    include_teacher = st.checkbox("Include Teacher Profile Page (Page 3)", value=True)
    
    custom_cover_upload = st.file_uploader("Upload Custom Cover (Optional)", type=["png", "jpg", "jpeg"])

# Resolve Teacher Photo Path
final_teacher_photo_path = None
if uploaded_teacher_photo:
    temp_dir = os.path.join(pdf_generator.BASE_DIR, "assets", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    final_teacher_photo_path = os.path.join(temp_dir, f"uploaded_teacher_{uploaded_teacher_photo.name}")
    with open(final_teacher_photo_path, "wb") as f:
        f.write(uploaded_teacher_photo.getbuffer())
elif full_active_photo_path and os.path.exists(full_active_photo_path):
    final_teacher_photo_path = full_active_photo_path

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
    st.markdown("#### Paste Your Questions")
    
    # Quick Sample Buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("Load MCQs Sample", width="stretch"):
            st.session_state["questions_input"] = SAMPLE_MCQ_TEXT
    with btn_col2:
        if st.button("Load Mixed Sample", width="stretch"):
            st.session_state["questions_input"] = SAMPLE_MIXED_TEXT
    with btn_col3:
        if st.button("Clear Input", width="stretch"):
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

    generate_btn = st.button("Generate High-Resolution PDF", type="primary", width="stretch")

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
                    teacher_photo_path=final_teacher_photo_path,
                    custom_cover_path=temp_cover_path,
                    font_color_hex="#1A4199",
                    watermark_opacity=0.22
                )
                st.session_state["generated_pdf"] = pdf_bytes
                st.session_state["pdf_q_count"] = q_count
        except Exception as e:
            st.error(f"Generation error: {str(e)}")

def render_pdf_pages_to_images(pdf_bytes, scale=1.5):
    """Render PDF pages to PIL images for universal cross-device preview."""
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_bytes)
        return [pdf[i].render(scale=scale).to_pil() for i in range(len(pdf))]
    except Exception:
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=144)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            return images
        except Exception:
            return []

with preview_col:
    st.markdown("#### PDF Output & Preview")
    
    if "generated_pdf" in st.session_state:
        pdf_bytes = st.session_state["generated_pdf"]
        q_count = st.session_state.get("pdf_q_count", total_q)
        
        # Clean safe filename: tute_tutorialnumber_subjectname_Unittopic
        clean_tut = re.sub(r'[^a-zA-Z0-9]', '', str(tutorial_number or "1"))
        clean_subject = re.sub(r'[^a-zA-Z0-9]', '', str(selected_subject or "Subject"))
        clean_unit = re.sub(r'[^a-zA-Z0-9]', '', str(unit_title or "Topic"))
        filename = f"tute_{clean_tut}_{clean_subject}_{clean_unit}.pdf"

        st.success(f"PDF successfully created ({q_count} questions rendered)")
        
        st.download_button(
            label=f"Download {filename}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width="stretch"
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Universal Cross-Device Preview Tabs (100% Unblockable across all devices & browsers)
        tab_page_by_page, tab_all_pages = st.tabs(["Page-by-Page View", "Continuous Booklet View"])

        # Render high-res page images directly in memory (immune to browser plugin/iframe blocks)
        page_images = render_pdf_pages_to_images(pdf_bytes, scale=1.8)
        total_pages = len(page_images)

        with tab_page_by_page:
            if page_images:
                if "preview_page_idx" not in st.session_state or st.session_state["preview_page_idx"] >= total_pages:
                    st.session_state["preview_page_idx"] = 0

                def go_prev_page():
                    if st.session_state.get("preview_page_idx", 0) > 0:
                        st.session_state["preview_page_idx"] -= 1

                def go_next_page():
                    if st.session_state.get("preview_page_idx", 0) < total_pages - 1:
                        st.session_state["preview_page_idx"] += 1

                col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

                cur_idx = st.session_state.get("preview_page_idx", 0)

                with col_nav1:
                    st.button(
                        "◀ Previous",
                        on_click=go_prev_page,
                        disabled=(cur_idx == 0),
                        width="stretch",
                        key="btn_prev_page"
                    )

                with col_nav2:
                    page_labels = [f"Page {i+1} of {total_pages}" for i in range(total_pages)]
                    st.selectbox(
                        "Page Selector",
                        options=range(total_pages),
                        format_func=lambda i: page_labels[i],
                        key="preview_page_idx",
                        label_visibility="collapsed"
                    )

                with col_nav3:
                    st.button(
                        "Next ▶",
                        on_click=go_next_page,
                        disabled=(cur_idx >= total_pages - 1),
                        width="stretch",
                        key="btn_next_page"
                    )

                active_idx = st.session_state.get("preview_page_idx", 0)
                if active_idx >= total_pages:
                    active_idx = 0
                current_img = page_images[active_idx]
                st.image(
                    current_img,
                    caption=f"Showing Page {active_idx + 1} of {total_pages} (High Resolution Preview)",
                    width="stretch"
                )
            else:
                st.warning("Could not render page images. Please use the Download button to view.")

        with tab_all_pages:
            if page_images:
                for idx, img in enumerate(page_images):
                    st.markdown(f"<div style='font-size: 13px; font-weight: 700; color: #1A4199; margin: 16px 0 6px 0; background: #eef2ff; padding: 4px 12px; border-radius: 6px; display: inline-block;'>Page {idx+1} of {total_pages}</div>", unsafe_allow_html=True)
                    st.image(img, width="stretch")
                    if idx < total_pages - 1:
                        st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px dashed #cbd5e1;'/>", unsafe_allow_html=True)
    else:
        st.info("Click **'Generate High-Resolution PDF'** to build and preview your formatted tutorial PDF.")
        
        # Show placeholder preview
        st.markdown(
            f"""
            <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; height: 560px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; text-align: center; padding: 24px;">
                <div style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">Ready to Generate</div>
                <div style="font-size: 14px; max-width: 320px; color: #64748b;">
                    Selected: <b style="color: #1A4199;">{selected_subject} ({board_code})</b><br/>
                    Unit: <b>{unit_title}</b> • {tutorial_number}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
