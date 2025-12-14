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

# ------------------ SETUP ------------------
nltk.download('stopwords')
from nltk.corpus import stopwords
STOP_WORDS = set(stopwords.words('english'))

st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if "page" not in st.session_state:
    st.session_state.page = "Job Description"

# ------------------ LOGIN PAGE ------------------
if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.strip():
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.warning("Please enter a username")
    st.stop()

# ------------------ SIDEBAR DASHBOARD ------------------
st.sidebar.title("📊 Dashboard")
st.sidebar.write(f"👤 Welcome, **{st.session_state.user}**")

menu = st.sidebar.radio(
    "Navigate",
    ["Job Description", "Upload & Screening", "Shortlisted Candidates"]
)

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.rerun()

# ------------------ TEXT CLEANING ------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', ' ', text)
    words = [w for w in text.split() if w not in STOP_WORDS]
    return " ".join(words)

# ------------------ TEXT EXTRACTION ------------------
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() or '' for page in reader.pages])
    else:
        doc = docx.Document(file)
        return " ".join([p.text for p in doc.paragraphs])

# ------------------ MAIN TITLE ------------------
st.title("✨ Welcome to AI Resume Screener")
st.markdown("---")

# ------------------ PAGE 1: JOB DESCRIPTION ------------------
if menu == "Job Description":
    st.subheader("📝 Enter Job Description")
    job_description = st.text_area(
        "Enter required job description here",
        height=250,
        key="job_desc"
    )

    if st.button("Save Job Description"):
        if job_description.strip():
            st.session_state.job_description = job_description
            st.success("Job description saved successfully")
        else:
            st.warning("Please enter job description")

# ------------------ PAGE 2: UPLOAD & SCREENING ------------------
elif menu == "Upload & Screening":
    if "job_description" not in st.session_state:
        st.warning("⚠ Please enter Job Description first")
    else:
        st.subheader("📂 Upload Resumes & Screen")
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

            results.index += 1
            results.insert(0, "Rank", results.index)
            st.session_state.results = results

            st.success("Screening completed successfully")

# ------------------ PAGE 3: SHORTLISTED CANDIDATES ------------------
elif menu == "Shortlisted Candidates":
    if "results" not in st.session_state:
        st.info("No results available. Please screen resumes first.")
    else:
        results = st.session_state.results.copy()

        st.subheader("🏆 Shortlisted Candidates")
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

