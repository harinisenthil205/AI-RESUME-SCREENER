import streamlit as st
import os
import re
import nltk
import pandas as pd
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ------------------ NLP SETUP ------------------
nltk.download("stopwords")
from nltk.corpus import stopwords
STOP_WORDS = set(stopwords.words("english"))

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ------------------ LOGIN PAGE ------------------
def login_page():
    st.markdown("<h1 style='text-align:center;'>🤖 Welcome to AI Resume Screener</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Smart AI-Based Resume Shortlisting System</p>", unsafe_allow_html=True)
    st.write("---")

    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.strip() and password.strip():
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Please enter both username and password")

# ------------------ LOGOUT ------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.pop("job_description", None)
    st.session_state.pop("results", None)
    st.rerun()

# ------------------ TEXT CLEANING ------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z ]", " ", text)
    words = [w for w in text.split() if w not in STOP_WORDS]
    return " ".join(words)

# ------------------ TEXT EXTRACTION ------------------
def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() or "" for page in reader.pages])
    else:
        doc = docx.Document(file)
        return " ".join([p.text for p in doc.paragraphs])

# =========================
# MAIN APP FLOW (STEP 4)
# =========================

if not st.session_state.logged_in:
    login_page()

else:
    st.sidebar.title("📊 Dashboard")
    st.sidebar.write(f"👤 Welcome, **{st.session_state.username}**")

    menu = st.sidebar.radio(
        "Navigate",
        ["Job Description", "Upload & Screening", "Shortlisted Candidates"]
    )

    if st.sidebar.button("🚪 Logout"):
        logout()

    # ---------- JOB DESCRIPTION ----------
    if menu == "Job Description":
        st.header("📝 Job Description")

        job_desc = st.text_area(
            "Enter Job Description",
            height=250,
            value=st.session_state.get("job_description", "")
        )

        if st.button("Save Job Description"):
            if job_desc.strip():
                st.session_state.job_description = job_desc
                st.success("Job description saved successfully")
            else:
                st.warning("Please enter a job description")

    # ---------- UPLOAD & SCREENING ----------
    elif menu == "Upload & Screening":
        if "job_description" not in st.session_state:
            st.warning("⚠ Please enter Job Description first")
        else:
            st.header("📂 Upload Resumes & Screen")

            uploaded_files = st.file_uploader(
                "Upload PDF or DOCX resumes",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )

            if uploaded_files and st.button("🔍 Screen Resumes"):
                resumes = []
                names = []

                for file in uploaded_files:
                    text = extract_text(file)
                    resumes.append(clean_text(text))
                    names.append(os.path.splitext(file.name)[0])

                jd_clean = clean_text(st.session_state.job_description)

                vectorizer = TfidfVectorizer()
                vectors = vectorizer.fit_transform([jd_clean] + resumes)
                scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten() * 100

                results = pd.DataFrame({
                    "Candidate Name": names,
                    "Match %": scores.round(2)
                }).sort_values(by="Match %", ascending=False).reset_index(drop=True)

                results.insert(0, "Rank", range(1, len(results) + 1))
                st.session_state.results = results

                st.success("Screening completed successfully")

    # ---------- SHORTLISTED CANDIDATES ----------
    elif menu == "Shortlisted Candidates":
        if "results" not in st.session_state:
            st.info("No results available. Please screen resumes first.")
        else:
            st.header("🏆 Shortlisted Candidates")

            results = st.session_state.results
            st.dataframe(results, hide_index=True, use_container_width=True)

            st.subheader("📈 Match Percentage Chart")
            fig = px.bar(
                results.sort_values("Match %"),
                x="Match %",
                y="Candidate Name",
                orientation="h",
                text="Match %",
                height=500
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                "⬇ Download Results (CSV)",
                data=results.to_csv(index=False),
                file_name="shortlisted_candidates.csv",
                mime="text/csv"
            )




