import streamlit as st
import PyPDF2
import docx
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ---------------- SESSION STATE ----------------
for key in ["logged_in", "job_desc", "resumes", "results"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- FUNCTIONS ----------------
def extract_text_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join(page.extract_text() for page in reader.pages)

def extract_text_docx(file):
    doc = docx.Document(file)
    return " ".join(p.text for p in doc.paragraphs)

def extract_candidate_name(text):
    return text.split("\n")[0][:40]

def shortlist(resume_text, jd_words):
    score = sum(1 for w in jd_words if w.lower() in resume_text.lower())
    return score

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>WELCOME TO AI RESUME SCREENER</h1>", unsafe_allow_html=True)

    u = st.text_input("Login Name")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u and p:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Enter login details")

# ---------------- DASHBOARD ----------------
else:
    # -------- STEP INDICATOR --------
    st.markdown("""
    **✔ Step 1: Login → ✔ Step 2: Job Description → ✔ Step 3: Upload Resumes → ✔ Step 4: Shortlisting**
    """)

    menu = st.sidebar.radio(
        "Navigate",
        ["Job Description", "Upload Resumes", "Shortlisting & Graphs"]
    )

    # ---------- STEP 2: JOB DESCRIPTION ----------
    if menu == "Job Description":
        st.header("📄 Step 2: Job Description")

        tech = ["Python", "Java", "SQL", "AI", "ML", "Web Development", "Javascript", "C", "C++", "Rust"]
        non_tech = ["Communication", "Leadership", "Teamwork"]

        t = st.multiselect("Technical Skills", tech)
        nt = st.multiselect("Non-Technical Skills", non_tech)

        jd = " ".join(t + nt)
        st.text_area("Generated Job Description", jd, height=120)

        if st.button("✅ Save Job Description"):
            if jd:
                st.session_state.job_desc = jd
                st.success("Job Description Saved. Go to Upload Resumes.")
            else:
                st.error("Select at least one skill")

    # ---------- STEP 3: UPLOAD ----------
    elif menu == "Upload Resumes":
        st.header("📂 Step 3: Upload Resumes")

        if not st.session_state.job_desc:
            st.warning("Complete Job Description first")
        else:
            files = st.file_uploader(
                "Upload resumes",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )

            if files:
                resumes = []

                for f in files:
                    text = extract_text_pdf(f) if f.name.endswith(".pdf") else extract_text_docx(f)
                    resumes.append({
                        "name": extract_candidate_name(text),
                        "text": text
                    })

                if st.button("✅ Upload Done"):
                    st.session_state.resumes = resumes
                    st.success("Resumes Uploaded. Go to Shortlisting.")

    # ---------- STEP 4: SHORTLISTING + GRAPHS ----------
    elif menu == "Shortlisting & Graphs":
    st.header("📊 Step 4: Shortlisting & Analysis")

    if not st.session_state.resumes:
        st.warning("Upload resumes first")
    else:
        jd_words = st.session_state.job_desc.split()
        data = []

        for r in st.session_state.resumes:
            score = shortlist(r["text"], jd_words)
            data.append({
                "Candidate Name": r["name"],
                "Score": score
            })

        df = pd.DataFrame(data)
        df = df.sort_values(by="Score", ascending=False)

        # ---------- USER SHORTLIST OPTION ----------
        shortlist_count = st.selectbox(
            "Select number of candidates to shortlist",
            [5, 10, 15, 20, 50, 100]
        )

        shortlisted_df = df.head(shortlist_count).copy()

        # ---------- SERIAL NUMBER STARTS FROM 1 ----------
        shortlisted_df.insert(0, "S.No", range(1, len(shortlisted_df) + 1))

        st.subheader("✅ Shortlisted Candidates")
        st.dataframe(shortlisted_df, hide_index=True)

        # ---------- GRAPH (HORIZONTAL BAR LIKE IMAGE) ----------
        st.subheader("📈 Shortlisted Candidate Scores")

        fig, ax = plt.subplots()
        ax.barh(
            shortlisted_df["Candidate Name"],
            shortlisted_df["Score"]
        )
        ax.set_xlabel("Matching Score")
        ax.set_ylabel("Candidates")
        ax.invert_yaxis()  # highest score on top

        st.pyplot(fig)

    # ---------- LOGOUT ----------
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()











