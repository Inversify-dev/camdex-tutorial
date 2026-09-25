import base64
import json
import os
import re
import streamlit as st
from PIL import Image

import importlib
import pdf_generator
importlib.reload(pdf_generator)

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

# ================= SAMPLE QUESTION PRESETS =================
SAMPLE_MCQ_TEXT = """Edexcel IGCSE (2026/2027)
Unit: Communication & the Internet
Tutorial 5 – August/September/October

MCQs

1. What is a computer network?
A. A single computer system in an office
B. A group of computers connected to share resources
C. A type of operating system software
D. A high-level programming language

2. Which of the following is an example of a LAN?
A. The Internet
B. Mobile phone network
C. A satellite network
D. A school computer lab

3. Which network type covers the largest geographical area?
A. LAN
B. PAN
C. WAN
D. MAN

4. What does PAN stand for?
A. Public Area Network
B. Personal Area Network
C. Private Access Network
D. Portable Area Network

5. Which device connects different networks together?
A. Router
B. Hub
C. Switch
D. Modem
"""

SAMPLE_SCIENCE_TEXT = """Cambridge IGCSE O/L
Unit: The Particulate Nature of Matter & Chemical Reactions
Tutorial 1

MCQs

1. Which gas is produced when zinc powder reacts with dilute hydrochloric acid?
A. Oxygen
B. Hydrogen
C. Carbon dioxide
D. Chlorine

Structured Questions:

2. A student investigated the reaction of zinc powder with dilute hydrochloric acid using the apparatus below.

[diagram: 1]
Fig. 2.1: Gas Syringe and Reaction Flask Apparatus

The same mass of zinc was added to different volumes of hydrochloric acid at room temperature, 20 °C. The total volume of hydrogen gas given off in each experiment was measured.

(a) Use the gas syringe readings to record the volume of hydrogen in the table below:

| Volume of acid / cm3 | Syringe reading / cm3 | Volume of hydrogen / cm3 |
| 0 | 0 | 0 |
| 5 | 14 | 14 |
| 10 | 28 | 28 |
| 15 | 42 | 42 |
| 20 | 50 | 50 |
[4]

(b) State two variables that must be kept constant during this experiment.
1. .................................................................................................................... [1]
2. .................................................................................................................... [1]

(c) Explain why the reaction rate decreases as the reaction progresses.
........................................................................................................................
........................................................................................................................ [2]

[Total: 8]
"""

SAMPLE_PASSAGE_TEXT = """Edexcel IGCSE (2026/2027)
Unit: Communication & Network Architecture
Tutorial 5

Structured Questions:

41. Zafer and Robert work for a company that makes washing machines.
a. Zafer writes user manuals for the washing machines. He stores these documents in the cloud. Zafer and the cloud storage provider share responsibility for data security. State one area of responsibility for each of them.

Zafer
........................................................................................................................
........................................................................................................................

Cloud storage provider
........................................................................................................................
........................................................................................................................

42. A network uses TCP/IP. Figure below shows the TCP/IP protocol stack.

[diagram: 1]
Fig. 42.1: TCP/IP Protocol Layers

a. One use of the application layer is to send and receive emails. State two email protocols.
1. ....................................................................................................................
2. ....................................................................................................................

43. Some employees use company laptops in public places. The management is concerned that shoulder surfing could pose a risk to security.
a. Describe what is meant by shoulder surfing.
........................................................................................................................
........................................................................................................................ [2]

b. Explain one way to prevent shoulder surfing.
........................................................................................................................
........................................................................................................................ [2]

[Total: 10]
"""

# Header Banner
st.markdown(
    """
    <div class="camdex-header">
        <div>
            <div class="camdex-title">CAMDEX Tutorial PDF Generator</div>
            <div class="camdex-subtitle">Upload Raw Tutor Document (.pdf / .docx), Edit in Container & Publish in Official CAMDEX Blue</div>
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
        board_index = 0
        if "detected_board" in st.session_state:
            board_index = 1 if st.session_state["detected_board"] == "EDX" else 0
        board_option = st.selectbox(
            "Exam Board",
            ["Cambridge (CMB)", "Edexcel (EDX)"],
            index=board_index
        )
        board_code = "CMB" if "CMB" in board_option else "EDX"
    
    with col_b2:
        subject_list = [
            "Computer Science", "Mathematics", "Physics", "Chemistry",
            "Biology", "Science", "ICT", "Business", "Economics",
            "Accounting", "English"
        ]
        subj_index = 0
        if "detected_subject" in st.session_state and st.session_state["detected_subject"] in subject_list:
            subj_index = subject_list.index(st.session_state["detected_subject"])
        selected_subject = st.selectbox("Subject", subject_list, index=subj_index)

    def_unit = st.session_state.get("detected_unit", "Communication & the Internet")
    unit_title = st.text_input("Unit / Topic Title", value=def_unit, key="unit_title_input")

    def_tut = st.session_state.get("detected_tutorial", "Tutorial 5 – August/September/October")
    tutorial_number = st.text_input("Tutorial # / Title", value=def_tut, key="tut_title_input")
    
    curriculum_default = "Edexcel IGCSE (2026/2027)" if board_code == "EDX" else "Cambridge IGCSE O/L"
    def_curr = st.session_state.get("detected_curriculum", curriculum_default)
    curriculum_title = st.text_input("Curriculum Header", value=def_curr, key="curr_title_input")

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
        st.session_state["teacher_name_input"] = matched_t["name"]
        st.session_state["teacher_subject_input"] = matched_t["subject"]
        st.session_state["teacher_qual_input"] = matched_t["qualifications"]
        st.session_state["teacher_msg_input"] = matched_t["message"]
        st.session_state["teacher_photo_path_active"] = matched_t.get("photo", "")
        st.session_state["teacher_dropdown_selector"] = f"{matched_t['name']} ({matched_t['subject']})"

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

    teacher_name = st.text_input("Teacher Name", key="teacher_name_input", placeholder="e.g. MR. YUSUF SHIHAM")
    teacher_subject = st.text_input("Subject Role / Title", key="teacher_subject_input", placeholder="e.g. COMPUTER SCIENCE TUTOR")
    teacher_qual = st.text_input("Qualifications / Subheading", key="teacher_qual_input", placeholder="e.g. BSc (Hons) Biomedical Science")
    teacher_msg = st.text_area("Teacher Bio / Description", key="teacher_msg_input", height=130, placeholder="Teacher bio description...")

    active_photo = st.session_state.get("teacher_photo_path_active", "")
    full_active_photo_path = os.path.join(pdf_generator.BASE_DIR, active_photo) if active_photo else ""

    uploaded_teacher_photo = st.file_uploader("Upload Custom Teacher Photo for this PDF", type=["png", "jpg", "jpeg"])

    if uploaded_teacher_photo:
        st.caption("Using uploaded photo for current PDF:")
        st.image(uploaded_teacher_photo, width=120)
    elif full_active_photo_path and os.path.exists(full_active_photo_path):
        st.caption(f"Preloaded photo for {teacher_name}:")
        st.image(full_active_photo_path, width=120)

    # Teacher Library Manager
    with st.expander("Manage Teacher Library (Add / Edit / Remove)"):
        tab_add, tab_update, tab_delete = st.tabs(["Add New Teacher", "Update Current", "Delete"])
        with tab_add:
            st.markdown("##### Add New Teacher to Permanent Library")
            new_t_name = st.text_input("Full Name", placeholder="e.g. DR. SARAH PERERA", key="new_t_name")
            new_t_role = st.text_input("Role / Title", placeholder="e.g. PHYSICS TUTOR", key="new_t_role")
            new_t_qual = st.text_input("Qualifications", placeholder="e.g. BSc. (Hons) Physics, MSc.", key="new_t_qual")
            new_t_bio = st.text_area("Teacher Bio / Description", height=90, placeholder="Teacher description...", key="new_t_bio")
            new_t_photo = st.file_uploader("Upload Profile Photo", type=["png", "jpg", "jpeg"], key="new_t_photo")
            
            if st.button("Save New Teacher to Library", type="primary", width="stretch"):
                if new_t_name.strip():
                    norm_name = new_t_name.strip().upper()
                    slug_id = re.sub(r'[^a-z0-9]', '', new_t_name.lower().replace("mr.", "").replace("ms.", "").replace("dr.", "").strip()) or f"teacher_{len(teachers_data) + 1}"
                    photo_rel_path = ""
                    if new_t_photo:
                        photo_filename = f"{slug_id}.png"
                        target_photo_path = os.path.join(pdf_generator.BASE_DIR, "assets", "teachers", photo_filename)
                        os.makedirs(os.path.dirname(target_photo_path), exist_ok=True)
                        with open(target_photo_path, "wb") as f:
                            f.write(new_t_photo.getbuffer())
                        photo_rel_path = f"assets/teachers/{photo_filename}"
                    
                    new_teacher_obj = {
                        "id": slug_id, "name": norm_name, "subject": new_t_role.strip().upper() if new_t_role else "TUTOR",
                        "qualifications": new_t_qual.strip(), "message": new_t_bio.strip(), "photo": photo_rel_path, "subjects_taught": []
                    }
                    teachers_data.append(new_teacher_obj)
                    if save_teachers(teachers_data):
                        st.session_state["pending_teacher_id"] = slug_id
                        st.success(f"Saved {norm_name} to library!")
                        st.rerun()

        with tab_update:
            st.markdown("##### Permanently Save Current Edits")
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
                        st.success(f"Updated {teacher_name}!")
                        st.rerun()

        with tab_delete:
            st.markdown("##### Delete Teacher from Library")
            teacher_to_del_label = st.selectbox("Select Teacher to Delete", options=teacher_display_list, key="del_teacher_sel")
            confirm_del = st.checkbox("I confirm deletion", key="confirm_del_chk")
            if st.button("Delete Teacher", type="secondary", width="stretch"):
                if confirm_del and len(teachers_data) > 1:
                    t_del = teacher_map.get(teacher_to_del_label)
                    if t_del:
                        remaining = [t for t in teachers_data if t["id"] != t_del["id"]]
                        if save_teachers(remaining):
                            st.session_state["pending_teacher_id"] = remaining[0]["id"]
                            st.success("Deleted teacher!")
                            st.rerun()

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
    mode_tab1, mode_tab2 = st.tabs([
        "Document Importer & Question Builder",
        "Past Paper PDF Publisher"
    ])
    
    # ---------------- TAB 1: DOCUMENT IMPORTER & BUILDER ----------------
    with mode_tab1:
        st.markdown("##### 1. Upload Raw Question Document (PDF / Word DOCX)")
        
        # Raw Document Uploader
        uploaded_doc = st.file_uploader(
            "Upload Tutor Question Document (.pdf, .docx, .txt)",
            type=["pdf", "docx", "doc", "txt"],
            key="raw_doc_file_uploader",
            help="Upload the raw document created by the tutor. It will automatically extract all questions, tables, and diagrams into the editor container below!"
        )
        
        temp_diagram_dir = os.path.join(pdf_generator.BASE_DIR, "assets", "temp", "diagrams")
        os.makedirs(temp_diagram_dir, exist_ok=True)
        
        # Handle automatic document extraction into the container
        if uploaded_doc is not None:
            doc_key = f"proc_{uploaded_doc.name}_{uploaded_doc.size}"
            if st.session_state.get("last_processed_doc") != doc_key:
                with st.spinner("Extracting text, questions, tables, and diagrams from document..."):
                    ext_text, ext_meta, ext_img_map = pdf_generator.import_raw_document(
                        uploaded_doc.getvalue(),
                        uploaded_doc.name,
                        temp_diagram_dir
                    )
                    st.session_state["questions_input"] = ext_text
                    st.session_state["active_diagram_map"] = ext_img_map
                    st.session_state["last_processed_doc"] = doc_key
                    
                    if ext_meta.get("board"):
                        st.session_state["detected_board"] = ext_meta["board"]
                    if ext_meta.get("subject"):
                        st.session_state["detected_subject"] = ext_meta["subject"]
                    if ext_meta.get("unit"):
                        st.session_state["detected_unit"] = ext_meta["unit"]
                    if ext_meta.get("tutorial"):
                        st.session_state["detected_tutorial"] = ext_meta["tutorial"]
                    if ext_meta.get("curriculum"):
                        st.session_state["detected_curriculum"] = ext_meta["curriculum"]
                st.success(f"Extracted all questions and {len(ext_img_map)} diagrams from **{uploaded_doc.name}** into the editor container below.")

        st.markdown("---")
        st.markdown("##### 2. Review & Edit in Container")
        
        # Preset Buttons
        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
        with btn_c1:
            if st.button("Sample MCQs", width="stretch"):
                st.session_state["questions_input"] = SAMPLE_MCQ_TEXT
        with btn_c2:
            if st.button("Science & Tables", width="stretch"):
                st.session_state["questions_input"] = SAMPLE_SCIENCE_TEXT
        with btn_c3:
            if st.button("Structured Passage", width="stretch"):
                st.session_state["questions_input"] = SAMPLE_PASSAGE_TEXT
        with btn_c4:
            if st.button("Clear Input", width="stretch"):
                st.session_state["questions_input"] = ""

        current_input_val = st.session_state.get("questions_input", SAMPLE_PASSAGE_TEXT)

        raw_text = st.text_area(
            "Questions Container",
            value=current_input_val,
            height=340,
            placeholder="Document questions and structured content will appear here...\n\nYou can edit or make any changes before generating.",
            label_visibility="collapsed"
        )

        # Diagram & Image Manager
        active_image_map = st.session_state.get("active_diagram_map", {})
        
        with st.expander(f"Attached Diagrams & Images ({len(active_image_map)} loaded)", expanded=(len(active_image_map) > 0)):
            st.caption("Diagrams extracted from your uploaded document or manually uploaded. Reference them with `[diagram: 1]`, `[diagram: 2]`, or `[diagram: filename]`.")
            
            # Additional Diagram Uploads if needed
            more_diagrams = st.file_uploader(
                "Attach Additional Diagrams",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="more_diagrams_uploader",
                label_visibility="collapsed"
            )
            
            if more_diagrams:
                for idx, df in enumerate(more_diagrams):
                    d_path = os.path.join(temp_diagram_dir, f"manual_{df.name}")
                    with open(d_path, "wb") as f:
                        f.write(df.getbuffer())
                    key_num = str(len(active_image_map) + 1)
                    active_image_map[key_num] = d_path
                    active_image_map[df.name] = d_path
                    active_image_map[os.path.splitext(df.name)[0]] = d_path
                st.session_state["active_diagram_map"] = active_image_map

            if active_image_map:
                # Show unique image files
                unique_paths = list(set(active_image_map.values()))
                d_cols = st.columns(min(len(unique_paths), 4) or 1)
                for i, p in enumerate(unique_paths):
                    if os.path.exists(p):
                        with d_cols[i % 4]:
                            st.image(p, width=100)
                            matching_keys = [k for k, v in active_image_map.items() if v == p and k.isdigit()]
                            k_label = matching_keys[0] if matching_keys else str(i+1)
                            st.caption(f"Tag: `[diagram: {k_label}]`")

        # Parsing Analysis & Stats
        parsed_info = pdf_generator.parse_input_text(raw_text)
        total_q = len(parsed_info["questions"])
        mcq_count = sum(1 for q in parsed_info["questions"] if q["q_type"] == "mcq")
        structured_count = total_q - mcq_count
        diagrams_attached = len(set(active_image_map.values())) if active_image_map else 0

        st.markdown(
            f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 14px 0;">
                <div class="stat-card">
                    <div class="stat-num">{total_q}</div>
                    <div class="stat-label">Total Questions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">{mcq_count}</div>
                    <div class="stat-label">MCQs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">{structured_count}</div>
                    <div class="stat-label">Structured</div>
                </div>
                <div class="stat-card">
                    <div class="stat-num">{diagrams_attached}</div>
                    <div class="stat-label">Diagrams</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        generate_worksheet_btn = st.button("Generate High-Resolution Tutorial PDF (CAMDEX Blue)", type="primary", width="stretch")

    # ---------------- TAB 2: PAST PAPER PDF PUBLISHER ----------------
    with mode_tab2:
        st.markdown("##### Direct Past Paper PDF Publisher")
        st.info("Have a ready-made Past Paper PDF with full diagrams and formatting? Upload it here to stamp the official CAMDEX Cover, Tutor Profile, Double Borders, Watermark, and Scalable Footer!")
        
        uploaded_past_paper_pdf = st.file_uploader(
            "Upload Existing Past Paper PDF",
            type=["pdf"],
            key="past_paper_pdf_uploader"
        )
        
        if uploaded_past_paper_pdf:
            st.success(f"Loaded Question Paper PDF: **{uploaded_past_paper_pdf.name}** ({uploaded_past_paper_pdf.size / 1024:.1f} KB)")
        
        generate_past_paper_btn = st.button("Stamp & Publish Past Paper PDF", type="primary", width="stretch")

# Handle Generation Logic
if generate_worksheet_btn:
    try:
        with st.spinner("Compiling high-resolution CAMDEX PDF..."):
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
                image_map=active_image_map,
                font_color_hex="#1A4199",
                watermark_opacity=0.22
            )
            st.session_state["generated_pdf"] = pdf_bytes
            st.session_state["pdf_q_count"] = q_count
            st.session_state["pdf_source_type"] = "Worksheet"
    except Exception as e:
        st.error(f"Generation error: {str(e)}")

elif generate_past_paper_btn:
    if not uploaded_past_paper_pdf:
        st.error("Please upload a question paper PDF first.")
    else:
        try:
            with st.spinner("Stamping and publishing branded past paper PDF..."):
                pdf_bytes, page_count = pdf_generator.build_stamped_tutorial_pdf(
                    question_pdf_bytes=uploaded_past_paper_pdf.getvalue(),
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
                    watermark_opacity=0.20
                )
                st.session_state["generated_pdf"] = pdf_bytes
                st.session_state["pdf_q_count"] = page_count
                st.session_state["pdf_source_type"] = "PastPaper"
        except Exception as e:
            st.error(f"Past paper stamping error: {str(e)}")

def render_pdf_pages_to_images(pdf_bytes, scale=1.5):
    """Render PDF pages to PIL images for universal cross-device preview."""
    try:
        import pymupdf as fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=144)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except Exception:
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_bytes)
            return [pdf[i].render(scale=scale).to_pil() for i in range(len(pdf))]
        except Exception:
            return []

# ----------------- PREVIEW COLUMN -----------------
with preview_col:
    st.markdown("#### PDF Output & Preview")
    
    if "generated_pdf" in st.session_state:
        pdf_bytes = st.session_state["generated_pdf"]
        q_count = st.session_state.get("pdf_q_count", total_q)
        source_type = st.session_state.get("pdf_source_type", "Worksheet")
        
        clean_tut = re.sub(r'[^a-zA-Z0-9]', '', str(tutorial_number or "1"))
        clean_subject = re.sub(r'[^a-zA-Z0-9]', '', str(selected_subject or "Subject"))
        clean_unit = re.sub(r'[^a-zA-Z0-9]', '', str(unit_title or "Topic"))
        filename = f"tute_{clean_tut}_{clean_subject}_{clean_unit}.pdf"

        if source_type == "Worksheet":
            st.success(f"Worksheet PDF created ({q_count} questions rendered in CAMDEX Blue)")
        else:
            st.success(f"Branded Past Paper PDF created ({q_count} content pages)")
        
        st.download_button(
            label=f"Download {filename}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width="stretch"
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        tab_page_by_page, tab_all_pages = st.tabs(["Page-by-Page View", "Continuous Booklet View"])

        page_images = render_pdf_pages_to_images(pdf_bytes, scale=1.8)
        total_pages = len(page_images)

        with tab_page_by_page:
            if page_images:
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
                        options=list(range(total_pages)),
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

                try:
                    active_idx = int(st.session_state.get("preview_page_idx", 0))
                except Exception:
                    active_idx = 0

                if active_idx < 0 or active_idx >= total_pages:
                    active_idx = 0

                current_img = page_images[active_idx]
                st.image(
                    current_img,
                    caption=f"Showing Page {active_idx + 1} of {total_pages} (CAMDEX Official Blue Preview)",
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
        st.info("Upload a document above or click **'Generate High-Resolution Tutorial PDF'** to build your formatted tutorial PDF.")
        
        st.markdown(
            f"""
            <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; height: 520px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; text-align: center; padding: 24px;">
                <div style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">Ready to Generate</div>
                <div style="font-size: 14px; max-width: 320px; color: #64748b; margin-bottom: 12px;">
                    Selected: <b style="color: #1A4199;">{selected_subject} ({board_code})</b><br/>
                    Unit: <b>{unit_title}</b> • {tutorial_number}
                </div>
                <div>
                    <span class="feature-tag">✨ MCQs</span>
                    <span class="feature-tag">📐 Diagrams</span>
                    <span class="feature-tag">📊 Tables</span>
                    <span class="feature-tag">📑 Structured</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
