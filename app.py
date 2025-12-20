import streamlit as st
import PyPDF2
import docx
import pandas as pd
import matplotlib.pyplot as plt
import io


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""
if "resumes" not in st.session_state:
    st.session_state.resumes = []

# ---------------- SIMPLE AUTH (REAL LOGIN) ----------------
USERS = {
    "admin": "admin123",
    "hr": "hr123"
}

# ---------------- FUNCTIONS ----------------
def extract_text_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join(page.extract_text() or "" for page in reader.pages)

def extract_text_docx(file):
    doc = docx.Document(file)
    return " ".join(p.text for p in doc.paragraphs)

def extract_candidate_name(text):
    lines = text.split("\n")
    return lines[0].strip() if lines else "Unknown"

def calculate_score(resume_text, jd_words):
    score = 0
    for word in jd_words:
        if word.lower() in resume_text.lower():
            score += 1
    return score

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>WELCOME TO AI RESUME SCREENER</h1>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------------- DASHBOARD ----------------
else:
    st.markdown(
        "**✔ Step 1: Login → ✔ Step 2: Job Description → ✔ Step 3: Upload Resumes → ✔ Step 4: Shortlisting & Graphs**"
    )

    # ---------- SIDEBAR ----------
    menu = st.sidebar.radio(
        "Navigate",
        ["Job Description", "Upload Resumes", "Shortlisting & Graphs"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.job_desc = ""
        st.session_state.resumes = []
        st.rerun()

    # ---------- STEP 2: JOB DESCRIPTION ----------
    if menu == "Job Description":
        st.header("📄 Step 2: Job Description")

        tech_skills = [
            "Python", "Java", "C", "C++", "JavaScript", "SQL",
            "AI", "ML", "Data Science", "Web Development"
        ]

        non_tech_skills = [
            "Communication", "Leadership", "Teamwork",
            "Problem Solving", "Time Management"
        ]

        tech = st.multiselect("Technical Skills", tech_skills)
        non_tech = st.multiselect("Non-Technical Skills", non_tech_skills)

        jd_text = " ".join(tech + non_tech)
        st.text_area("Generated Job Description", jd_text, height=120)

        if st.button("✅ Save Job Description"):
            if jd_text:
                st.session_state.job_desc = jd_text
                st.success("Job Description saved. Go to Upload Resumes.")
            else:
                st.error("Select at least one skill")

    # ---------- STEP 3: UPLOAD RESUMES ----------
    elif menu == "Upload Resumes":
        st.header("📂 Step 3: Upload Resumes")

        if not st.session_state.job_desc:
            st.warning("Please complete Job Description first.")
        else:
            files = st.file_uploader(
                "Upload PDF or DOCX resumes",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )

            if files and st.button("✅ Upload Done"):
                resumes = []
                for file in files:
                    if file.name.endswith(".pdf"):
                        text = extract_text_pdf(file)
                    else:
                        text = extract_text_docx(file)

                    resumes.append({
                        "Candidate Name": extract_candidate_name(text),
                        "Text": text
                    })

                st.session_state.resumes = resumes
                st.success(f"{len(resumes)} resumes uploaded successfully.")

    # ---------- STEP 4: SHORTLISTING + GRAPHS ----------
    elif menu == "Shortlisting & Graphs":
        st.header("📊 Step 4: Shortlisting & Analysis")

        if not st.session_state.resumes:
            st.warning("Upload resumes first.")
        else:
            jd_words = st.session_state.job_desc.split()

            results = []
            for r in st.session_state.resumes:
                score = calculate_score(r["Text"], jd_words)
                results.append({
                    "Candidate Name": r["Candidate Name"],
                    "Score": score
                })

            df = pd.DataFrame(results).sort_values("Score", ascending=False)

            shortlist_count = st.selectbox(
                "Select number of candidates to shortlist",
                [5, 10, 15, 20, 50, 100]
            )

            shortlisted = df.head(shortlist_count).copy()
            shortlisted.insert(0, "S.No", range(1, len(shortlisted) + 1))

            st.subheader("✅ Shortlisted Candidates")
            st.dataframe(shortlisted, hide_index=True)

    # -------- DOWNLOAD SHORTLISTED CSV --------
            csv_buffer = io.StringIO()
            shortlisted.to_csv(csv_buffer, index=False)

            st.download_button(
            label="⬇️ Download Shortlisted Candidates (CSV)",
            data=csv_buffer.getvalue(),
            file_name="shortlisted_candidates.csv",
            mime="text/csv"
            )


            st.subheader("📈 Shortlisted Candidate Scores")

            fig, ax = plt.subplots()
            ax.barh(shortlisted["Candidate Name"], shortlisted["Score"])
            ax.set_xlabel("Matching Score")
            ax.set_ylabel("Candidates")
            ax.invert_yaxis()

            st.pyplot(fig)












