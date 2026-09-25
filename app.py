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
        margin-bottom: 20px;
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
        padding: 10px 14px;
        text-align: center;
    }
    
    .stat-num {
        font-size: 20px;
        font-weight: 700;
        color: #1A4199;
    }
    
    .stat-label {
        font-size: 11px;
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

    .feature-tag {
        display: inline-block;
        background: #eef2ff;
        color: #1A4199;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .upload-box {
        background: #f0fdf4;
        border: 1.5px dashed #22c55e;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 12px;
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

# Header Banner
st.markdown(
    """
    <div class="camdex-header">
        <div>
            <div class="camdex-title">CAMDEX Tutorial PDF Generator</div>
            <div class="camdex-subtitle">Upload Raw Tutor Document (.pdf / .docx), Edit in Container & Publish in Official CAMDEX </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

import shutil
import time
import uuid

# Session Isolation & Auto-Cleanup of Temp Assets
def get_session_temp_dir():
    """Returns a unique temporary directory isolated to the current user session and auto-purges old sessions."""
    base_temp = os.path.join(pdf_generator.BASE_DIR, "assets", "temp")
    os.makedirs(base_temp, exist_ok=True)
    
    # Auto-cleanup session directories older than 2 hours to prevent disk growth forever
    now = time.time()
    try:
        for item in os.listdir(base_temp):
            item_path = os.path.join(base_temp, item)
            if os.path.isdir(item_path):
                if now - os.path.getmtime(item_path) > 7200:
                    shutil.rmtree(item_path, ignore_errors=True)
    except Exception:
        pass
        
    if "user_session_id" not in st.session_state:
        st.session_state["user_session_id"] = str(uuid.uuid4())[:12]
        
    session_dir = os.path.join(base_temp, st.session_state["user_session_id"])
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

SUBJECT_LIST = [
    "Computer Science", "Mathematics", "Physics", "Chemistry",
    "Biology", "Science", "ICT", "Business", "Economics",
    "Accounting", "English"
]

# Apply any pending detected metadata BEFORE sidebar widgets instantiate
if "pending_detected_meta" in st.session_state:
    meta = st.session_state.pop("pending_detected_meta")
    if meta.get("board"):
        st.session_state["exam_board_select"] = "Edexcel (EDX)" if meta["board"] == "EDX" else "Cambridge (CMB)"
    if meta.get("subject") and meta["subject"] in SUBJECT_LIST:
        st.session_state["subject_select"] = meta["subject"]
    if meta.get("unit"):
        st.session_state["unit_title_input"] = meta["unit"]
    if meta.get("tutorial"):
        st.session_state["tut_title_input"] = meta["tutorial"]
    if meta.get("curriculum"):
        st.session_state["curr_title_input"] = meta["curriculum"]

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
        if "exam_board_select" not in st.session_state:
            st.session_state["exam_board_select"] = "Cambridge (CMB)"
        board_option = st.selectbox(
            "Exam Board",
            ["Cambridge (CMB)", "Edexcel (EDX)"],
            key="exam_board_select"
        )
        board_code = "CMB" if "CMB" in board_option else "EDX"
    
    with col_b2:
        if "subject_select" not in st.session_state:
            st.session_state["subject_select"] = "Computer Science"
        selected_subject = st.selectbox("Subject", SUBJECT_LIST, key="subject_select")

    if "unit_title_input" not in st.session_state:
        st.session_state["unit_title_input"] = "Communication & the Internet"
    unit_title = st.text_input("Unit / Topic Title", key="unit_title_input")

    if "tut_title_input" not in st.session_state:
        st.session_state["tut_title_input"] = "Tutorial 5 – August/September/October"
    tutorial_number = st.text_input("Tutorial # / Title", key="tut_title_input")
    
    curriculum_default = "Edexcel IGCSE (2026/2027)" if board_code == "EDX" else "Cambridge IGCSE O/L"
    if "curr_title_input" not in st.session_state:
        st.session_state["curr_title_input"] = curriculum_default
    curriculum_title = st.text_input("Curriculum Header", key="curr_title_input")

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

    if "pending_teacher_id" in st.session_state:
        target_id = st.session_state.pop("pending_teacher_id")
        matched_t = next((t for t in teachers_data if t["id"] == target_id), teachers_data[0])
        st.session_state["active_teacher_id"] = matched_t["id"]

    if "active_teacher_id" not in st.session_state:
        def_t = teachers_data[0]
        for t in teachers_data:
            if selected_subject in t.get("subjects_taught", []):
                def_t = t
                break
        st.session_state["active_teacher_id"] = def_t["id"]

    def on_teacher_select():
        chosen_label = st.session_state.get("teacher_dropdown_selector")
        if chosen_label in teacher_map:
            t = teacher_map[chosen_label]
            st.session_state["active_teacher_id"] = t["id"]

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

    active_teacher = next((t for t in teachers_data if t["id"] == current_active_id), teachers_data[0])
    teacher_name = active_teacher.get("name", "")
    teacher_subject = active_teacher.get("subject", "")
    teacher_qual = active_teacher.get("qualifications", "")
    teacher_msg = active_teacher.get("message", "")
    active_photo = active_teacher.get("photo", "")
    full_active_photo_path = os.path.join(pdf_generator.BASE_DIR, active_photo) if active_photo else ""

    # Non-editable Teacher Profile Preview Card
    if full_active_photo_path and os.path.exists(full_active_photo_path):
        st.image(full_active_photo_path, width=110)
    
    clean_qual_display = teacher_qual.replace("**", "").replace("\n", " • ")
    st.markdown(
        f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-top: 6px; margin-bottom: 12px;">
            <div style="font-weight: 700; font-size: 14.5px; color: #1A4199; margin-bottom: 2px;">{teacher_name}</div>
            <div style="font-size: 11.5px; font-weight: 600; color: #64748b; margin-bottom: 6px;">{teacher_subject}</div>
            <div style="font-size: 11.5px; color: #334155; margin-bottom: 6px;"><b>Qualifications:</b><br><span style="color: #475569;">{clean_qual_display}</span></div>
            <div style="font-size: 11px; color: #64748b; line-height: 1.35; border-top: 1px dashed #e2e8f0; padding-top: 6px;"><b>Bio Summary:</b><br>{teacher_msg[:160] + ('...' if len(teacher_msg) > 160 else '')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Teacher Library Manager
    with st.expander("Manage Teacher Library (Add / Edit / Delete)"):
        tab_edit, tab_add, tab_delete = st.tabs(["Edit Teacher", "Add New Teacher", "Delete"])
        
        # ----------------- EDIT TEACHER TAB -----------------
        with tab_edit:
            st.markdown("##### Edit Teacher Details")
            st.caption("Select a teacher below to update their qualifications, bio description, or photo.")
            
            edit_default_idx = dropdown_index
            edit_teacher_sel = st.selectbox(
                "Select Teacher to Edit",
                options=teacher_display_list,
                index=edit_default_idx,
                key="edit_teacher_dropdown_sel"
            )
            
            t_to_edit = teacher_map.get(edit_teacher_sel, active_teacher)
            
            st.markdown(
                f"""
                <div style="background: #f1f5f9; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 12.5px;">
                    <b style="color: #1A4199;">Teacher:</b> {t_to_edit['name']}<br/>
                    <b style="color: #64748b;">Subject Role:</b> {t_to_edit['subject']}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            edit_qual_val = st.text_input(
                "Qualifications / Subheading",
                value=t_to_edit.get("qualifications", ""),
                key=f"edit_qual_{t_to_edit['id']}"
            )
            
            edit_bio_val = st.text_area(
                "Teacher Bio / Description",
                value=t_to_edit.get("message", ""),
                height=120,
                key=f"edit_bio_{t_to_edit['id']}"
            )
            
            current_t_photo = t_to_edit.get("photo", "")
            current_t_photo_path = os.path.join(pdf_generator.BASE_DIR, current_t_photo) if current_t_photo else ""
            if current_t_photo_path and os.path.exists(current_t_photo_path):
                st.caption("Current Profile Photo:")
                st.image(current_t_photo_path, width=90)
            
            replace_photo_file = st.file_uploader(
                "Replace Profile Photo (Optional)",
                type=["png", "jpg", "jpeg"],
                key=f"replace_photo_{t_to_edit['id']}"
            )
            
            if st.button("Save Changes to Library", type="primary", key="btn_save_teacher_edit", width="stretch"):
                for t in teachers_data:
                    if t["id"] == t_to_edit["id"]:
                        t["qualifications"] = edit_qual_val.strip()
                        t["message"] = edit_bio_val.strip()
                        if replace_photo_file:
                            photo_filename = f"{t['id']}.png"
                            target_photo_path = os.path.join(pdf_generator.BASE_DIR, "assets", "teachers", photo_filename)
                            os.makedirs(os.path.dirname(target_photo_path), exist_ok=True)
                            with open(target_photo_path, "wb") as f:
                                f.write(replace_photo_file.getbuffer())
                            t["photo"] = f"assets/teachers/{photo_filename}"
                        break
                
                if save_teachers(teachers_data):
                    st.session_state["pending_teacher_id"] = t_to_edit["id"]
                    st.success(f"Successfully updated {t_to_edit['name']}!")
                    st.rerun()

        # ----------------- ADD NEW TEACHER TAB -----------------
        with tab_add:
            st.markdown("##### Add New Teacher to Permanent Library")
            new_t_name = st.text_input("Full Name", placeholder="e.g. DR. SARAH PERERA", key="new_t_name")
            new_t_role = st.text_input("Role / Title", placeholder="e.g. PHYSICS TUTOR", key="new_t_role")
            new_t_qual = st.text_input("Qualifications", placeholder="e.g. BSc. (Hons) Physics, MSc.", key="new_t_qual")
            new_t_bio = st.text_area("Teacher Bio / Description", height=90, placeholder="Teacher description...", key="new_t_bio")
            new_t_photo = st.file_uploader("Upload Profile Photo", type=["png", "jpg", "jpeg"], key="new_t_photo")
            
            if st.button("Save New Teacher to Library", type="primary", width="stretch", key="btn_add_teacher"):
                if new_t_name.strip():
                    norm_name = new_t_name.strip().upper()
                    base_slug = re.sub(r'[^a-z0-9]', '', new_t_name.lower().replace("mr.", "").replace("ms.", "").replace("dr.", "").strip()) or f"teacher_{len(teachers_data) + 1}"
                    slug_id = base_slug
                    counter = 1
                    while any(t.get("id") == slug_id for t in teachers_data):
                        counter += 1
                        slug_id = f"{base_slug}_{counter}"
                        
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
                    teachers_data.append(new_teacher_obj)
                    if save_teachers(teachers_data):
                        st.session_state["pending_teacher_id"] = slug_id
                        st.success(f"Saved {norm_name} to library!")
                        st.rerun()
                else:
                    st.error("Please enter a teacher name.")

        # ----------------- DELETE TEACHER TAB -----------------
        with tab_delete:
            st.markdown("##### Delete Teacher from Library")
            teacher_to_del_label = st.selectbox("Select Teacher to Delete", options=teacher_display_list, key="del_teacher_sel")
            confirm_del = st.checkbox("I confirm deletion", key="confirm_del_chk")
            if st.button("Delete Teacher", type="secondary", width="stretch", key="btn_del_teacher"):
                if confirm_del and len(teachers_data) > 1:
                    t_del = teacher_map.get(teacher_to_del_label)
                    if t_del:
                        remaining = [t for t in teachers_data if t["id"] != t_del["id"]]
                        if save_teachers(remaining):
                            st.session_state["pending_teacher_id"] = remaining[0]["id"]
                            st.success(f"Deleted {t_del['name']}!")
                            st.rerun()
                elif not confirm_del:
                    st.warning("Please check the confirmation box to delete.")

    st.markdown("---")
    st.markdown("### Document Layout")
    include_intro = st.checkbox("Include Institute About Page (Page 2)", value=True)
    include_teacher = st.checkbox("Include Teacher Profile Page (Page 3)", value=True)
    custom_cover_upload = st.file_uploader("Upload Custom Cover (Optional)", type=["png", "jpg", "jpeg"])

# Resolve Teacher Photo Path
final_teacher_photo_path = None
if full_active_photo_path and os.path.exists(full_active_photo_path):
    final_teacher_photo_path = full_active_photo_path

session_temp_dir = get_session_temp_dir()

temp_cover_path = None
if custom_cover_upload:
    temp_cover_path = os.path.join(session_temp_dir, f"cover_{custom_cover_upload.name}")
    with open(temp_cover_path, "wb") as f:
        f.write(custom_cover_upload.getbuffer())

# ----------------- MAIN WORKSPACE -----------------
main_col, preview_col = st.columns([1.1, 0.9])

with main_col:
    st.markdown("##### 1. Upload Raw Tutorial / Past Paper (.pdf, .docx, .txt)")
    st.info("Upload your raw tutor document here. It will convert directly into the official CAMDEX Publication.")
    
    direct_uploaded_file = st.file_uploader(
        "Upload Raw Tutor Document",
        type=["pdf", "docx", "doc", "txt"],
        key="direct_raw_tute_uploader",
        help="Transforms raw PDFs, Word documents, or worksheets into official CAMDEX format."
    )
    
    # Auto metadata extraction on upload
    if direct_uploaded_file is not None:
        f_key = f"direct_{direct_uploaded_file.name}_{direct_uploaded_file.size}"
        if st.session_state.get("last_direct_doc") != f_key:
            temp_diag_dir = os.path.join(session_temp_dir, "diagrams")
            os.makedirs(temp_diag_dir, exist_ok=True)
            with st.spinner("Analyzing document metadata and extracting structure..."):
                _, detected_meta, _ = pdf_generator.import_raw_document(
                    direct_uploaded_file.getvalue(),
                    direct_uploaded_file.name,
                    temp_diag_dir
                )
                st.session_state["last_direct_doc"] = f_key
                st.session_state["pending_detected_meta"] = detected_meta
                st.session_state["auto_generate_direct"] = True
                st.rerun()
            
        st.success(f"Loaded: **{direct_uploaded_file.name}** ({direct_uploaded_file.size / 1024:.1f} KB)")
    
    st.markdown("---")
    st.markdown("##### 2. Document Settings Summary")
    
    st.markdown(
        f"""
        <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
            <div style="font-size: 13px; font-weight: 700; color: #166534; margin-bottom: 4px;">DOCUMENT SPECIFICATIONS</div>
            <div style="font-size: 13.5px; color: #1e293b;">
                <b>Subject:</b> {selected_subject} ({board_code}) &nbsp;|&nbsp; 
                <b>Topic:</b> {unit_title} &nbsp;|&nbsp; 
                <b>Tutorial:</b> {tutorial_number}<br/>
                <b>Curriculum:</b> {curriculum_title} &nbsp;|&nbsp;
                <b>Teacher:</b> {teacher_name}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    generate_direct_btn = st.button("Convert & Publish Document", type="primary", width="stretch")

# Handle Direct Auto-Generation or Button Trigger
should_run_direct = generate_direct_btn or (st.session_state.pop("auto_generate_direct", False) and direct_uploaded_file is not None)

if should_run_direct:
    if direct_uploaded_file is None:
        st.error("Please upload a raw tutorial document (PDF, Word DOCX, or TXT) first.")
    else:
        try:
            with st.spinner("Converting raw document directly to official CAMDEX publication..."):
                pdf_bytes, page_count = pdf_generator.build_direct_raw_tutorial_pdf(
                    file_bytes=direct_uploaded_file.getvalue(),
                    filename=direct_uploaded_file.name,
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
                    image_map=st.session_state.get("active_diagram_map", {}),
                    font_color_hex="#1A4199",
                    watermark_opacity=0.20
                )
                st.session_state["generated_pdf"] = pdf_bytes
                st.session_state["pdf_q_count"] = page_count
                st.session_state["pdf_source_type"] = "DirectRawTute"
                st.session_state["preview_page_idx"] = 0
        except Exception as e:
            st.error(f"Direct conversion error: {str(e)}")

@st.cache_data(max_entries=10)
def get_pdf_total_pages(pdf_bytes):
    try:
        import pymupdf as fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 1

@st.cache_data(max_entries=20)
def render_single_pdf_page(pdf_bytes, page_idx=0, dpi=120):
    """Render only ONE specific page on demand to keep RAM usage minimal (<15 MB)."""
    try:
        import pymupdf as fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_idx < 0 or page_idx >= len(doc):
            page_idx = 0
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception:
        return None

# ----------------- PREVIEW COLUMN -----------------
with preview_col:
    st.markdown("#### PDF Output & Preview")
    
    if "generated_pdf" in st.session_state:
        pdf_bytes = st.session_state["generated_pdf"]
        q_count = st.session_state.get("pdf_q_count", 0)
        source_type = st.session_state.get("pdf_source_type", "DirectRawTute")
        
        clean_tut = re.sub(r'[^a-zA-Z0-9]', '', str(tutorial_number or "1"))
        clean_subject = re.sub(r'[^a-zA-Z0-9]', '', str(selected_subject or "Subject"))
        clean_unit = re.sub(r'[^a-zA-Z0-9]', '', str(unit_title or "Topic"))
        filename = f"tute_{clean_tut}_{clean_subject}_{clean_unit}.pdf"

        st.success(f"CAMDEX PDF Publication created successfully ({q_count} pages)")
        
        st.download_button(
            label=f"Download {filename}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width="stretch"
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        tab_page_by_page, tab_all_pages = st.tabs(["Page-by-Page View", "Continuous Booklet View"])

        total_pages = get_pdf_total_pages(pdf_bytes)

        with tab_page_by_page:
            try:
                cur_idx = int(st.session_state.get("preview_page_idx", 0))
            except (ValueError, TypeError):
                cur_idx = 0

            if cur_idx < 0 or cur_idx >= total_pages:
                cur_idx = 0
            st.session_state["preview_page_idx"] = cur_idx

            def go_prev_page():
                try:
                    v = int(st.session_state.get("preview_page_idx", 0))
                except Exception:
                    v = 0
                if v > 0:
                    st.session_state["preview_page_idx"] = v - 1

            def go_next_page():
                try:
                    v = int(st.session_state.get("preview_page_idx", 0))
                except Exception:
                    v = 0
                if v < total_pages - 1:
                    st.session_state["preview_page_idx"] = v + 1

            col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

            with col_nav1:
                st.button(
                    "Previous",
                    on_click=go_prev_page,
                    disabled=(cur_idx == 0),
                    width="stretch",
                    key="btn_prev_page"
                )

            with col_nav2:
                page_labels = [f"Page {i+1} of {total_pages}" for i in range(total_pages)]
                st.selectbox(
                    "Page Selector",
                    options=list(range(total_pages)),
                    format_func=lambda i: page_labels[i],
                    key="preview_page_idx",
                    label_visibility="collapsed"
                )

            with col_nav3:
                st.button(
                    "Next",
                    on_click=go_next_page,
                    disabled=(cur_idx >= total_pages - 1),
                    width="stretch",
                    key="btn_next_page"
                )

            current_img = render_single_pdf_page(pdf_bytes, page_idx=cur_idx, dpi=130)
            if current_img:
                st.image(
                    current_img,
                    caption=f"Showing Page {cur_idx + 1} of {total_pages} (CAMDEX Official Preview)",
                    width="stretch"
                )
            else:
                st.warning("Preview not available. Please click the Download button to view.")

        with tab_all_pages:
            for idx in range(total_pages):
                st.markdown(f"<div style='font-size: 13px; font-weight: 700; color: #1A4199; margin: 16px 0 6px 0; background: #eef2ff; padding: 4px 12px; border-radius: 6px; display: inline-block;'>Page {idx+1} of {total_pages}</div>", unsafe_allow_html=True)
                page_img = render_single_pdf_page(pdf_bytes, page_idx=idx, dpi=110)
                if page_img:
                    st.image(page_img, width="stretch")
                if idx < total_pages - 1:
                    st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px dashed #cbd5e1;'/>", unsafe_allow_html=True)
    else:
        st.info("Upload a document above or click 'Convert & Publish Document' to build your formatted tutorial PDF.")
        
        st.markdown(
            f"""
            <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; height: 520px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; text-align: center; padding: 24px;">
                <div style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">Ready to Generate</div>
                <div style="font-size: 14px; max-width: 320px; color: #64748b; margin-bottom: 12px;">
                    Selected: <b style="color: #1A4199;">{selected_subject} ({board_code})</b><br/>
                    Unit: <b>{unit_title}</b> • {tutorial_number}
                </div>
                <div>
                    <span class="feature-tag">MCQs</span>
                    <span class="feature-tag">Diagrams</span>
                    <span class="feature-tag">Tables</span>
                    <span class="feature-tag">Structured Questions</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
