# 🎓 CAMDEX Tutorial PDF Automation System

A high-performance, automated Python + Streamlit application designed to turn raw MCQs and structured questions into publication-ready, exam-grade PDF tutorials.

Built to match the exact visual style and branding of **`Tute_1_CMB_DataRepresentation.pdf`**.

---

## 🌟 Key Features

1. **⚡ Instant 1-Click Generation (< 0.5s)**:
   - Paste questions from Word, Google Docs, or Past Papers.
   - Click **Generate High-Resolution PDF** to build and preview immediately.

2. **📚 Full Cover Library (All 22 Cambridge & Edexcel Subjects)**:
   - Dynamic cover artwork matching selected Subject (`Computer Science`, `Maths`, `Physics`, `Chemistry`, `Biology`, `ICT`, `Commerce`, etc.) and Board (`Cambridge CMB` vs `Edexcel EDX`).
   - Dynamic unit title text overlay rendered in typography matching the original reference.

3. **🏢 Institute Introduction Page (Page 2)**:
   - High-res Camdex horizontal header logo.
   - Institute overview, key learning options, and value cards.
   - Can be toggled on/off.

4. **👤 Dynamic Teacher Profiles (Page 3)**:
   - Switch between pre-saved teacher presets or type custom teacher details.
   - Dynamic qualifications, subject specialization, instructor message, and photo upload.
   - Can be toggled on/off.

5. **📝 Smart MCQ & Structured Questions Engine (Page 4+)**:
   - Header with Camdex horizontal logo and curriculum unit title.
   - Auto-numbers questions and formats `A.`, `B.`, `C.`, `D.` MCQ options with clean indentation.
   - Handles structured sub-parts (`a.`, `b.`, `i.`, `ii.`) and dotted response lines (`........`).
   - Auto-formats subscripts & superscripts (e.g. `26(10)` -> $26_{10}$, `3F(16)` -> $3F_{16}$, `101101(2)` -> $101101_{2}$, `x^2` -> $x^2$).
   - Subtle background watermark seal centered on every question page.
   - Page numbering in footer (`Page X of Y`).
   - KeepTogether logic prevents questions from awkwardly splitting across page bottoms.

6. **👁️ In-App PDF Preview & Dynamic Download**:
   - Preview generated PDFs right inside your browser before downloading.
   - Auto-names downloads cleanly (e.g. `Tute_Tutorial1_CMB_DataRepresentation.pdf`).

---

## 🚀 How to Run Locally

### Option 1 (Double-Click):
Just double-click **`run.bat`** in the project folder!

### Option 2 (Command Line):
```bash
python -m streamlit run app.py
```

3. The app will open in your default browser at `http://localhost:8501`.

---

## 🌐 100% Free Cloud Deployment (Streamlit Community Cloud)

You can share this tool with all teachers with zero server costs:

1. Push this project folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
3. Select your repository and set Main file path to `app.py`.
4. Click **Deploy**.
5. You will receive a live URL (e.g. `https://camdex-tute-generator.streamlit.app`) accessible on any device.

---

## 📁 File Structure

```text
tutorial_automation/
├── app.py                      # Modern Streamlit Web Dashboard
├── pdf_generator.py            # High-performance ReportLab PDF Engine
├── requirements.txt            # Python Dependencies
├── sample_questions.txt        # Sample questions
├── assets/
│   ├── covers/                 # 22 High-Res Subject Covers (CMB & EDX)
│   ├── logos/                  # Official Camdex Vector/PNG Logos
│   └── defaults/               # Graphics, Badges & Default Teacher Photo
└── README.md                   # System Documentation
```
