import streamlit as st
import pandas as pd
import numpy as np
import PyPDF2
import docx
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------ FUNCTIONS ------------------
def extract_text_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_docx(file):
    doc = docx.Document(file)
    return " ".join([para.text for para in doc.paragraphs])

def extract_candidate_name(text):
    lines = text.split("\n")
    return lines[0][:40]  # assume name is first line

# ------------------ LOGIN PAGE ------------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>WELCOME TO AI RESUME SCREENER</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Login Name")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username and password:
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()

            else:
                st.error("Please enter login and password")

# ------------------ DASHBOARD ------------------
else:
    st.sidebar.title("Dashboard")
    menu = st.sidebar.radio(
        "Select Option",
        ["Job Description", "Upload & Screening", "Shortlisted Candidates", "Graphs"]
    )

    # ------------------ JOB DESCRIPTION ------------------
    if menu == "Job Description":
        st.header("📄 Job Description")

        tech_languages = [
            "Python", "Java", "C", "C++", "JavaScript", "SQL",
            "HTML", "CSS", "React", "NodeJS", "Machine Learning",
            "Data Science", "AI", "Cloud", "DevOps"
        ]

        non_tech_languages = [
            "Communication", "Leadership", "Teamwork",
            "Problem Solving", "Time Management",
            "Critical Thinking", "Presentation Skills"
        ]

        selected_tech = st.multiselect("Select Technical Skills", tech_languages)
        selected_non_tech = st.multiselect("Select Non-Technical Skills", non_tech_languages)

        job_desc = " ".join(selected_tech + selected_non_tech)
        st.text_area("Generated Job Description", job_desc, height=150)

        st.session_state.job_desc = job_desc

    # ------------------ UPLOAD & SCREENING ------------------
    elif menu == "Upload & Screening":
        st.header("📂 Upload Resumes & Screening")

        if "job_desc" not in st.session_state or st.session_state.job_desc.strip() == "":
            st.warning("Please complete Job Description first")
        else:
            uploaded_files = st.file_uploader(
                "Upload PDF/DOCX Resumes",
                type=["pdf", "docx"],
                accept_multiple_files=True
            )

            if uploaded_files:
                resumes = []
                names = []

                for file in uploaded_files:
                    if file.name.endswith(".pdf"):
                        text = extract_text_pdf(file)
                    else:
                        text = extract_text_docx(file)

                    resumes.append(text)
                    names.append(extract_candidate_name(text))

                vectorizer = TfidfVectorizer(stop_words="english")
                vectors = vectorizer.fit_transform([st.session_state.job_desc] + resumes)

                similarity_scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

                df = pd.DataFrame({
                    "Candidate Name": names,
                    "Score (%)": (similarity_scores * 100).round(2)
                })

                df = df.sort_values(by="Score (%)", ascending=False)

                st.subheader("📊 Screening Results")
                st.dataframe(df)

                st.session_state.results = df

    # ------------------ SHORTLISTED CANDIDATES ------------------
    elif menu == "Shortlisted Candidates":
        st.header("✅ Shortlisted Candidates")

        if "results" not in st.session_state:
            st.warning("Please perform screening first")
        else:
            threshold = st.slider("Select Cut-off Score (%)", 0, 100, 60)
            shortlisted = st.session_state.results[
                st.session_state.results["Score (%)"] >= threshold
            ]

            st.dataframe(shortlisted)
            st.session_state.shortlisted = shortlisted

    # ------------------ GRAPHS ------------------
    elif menu == "Graphs":
        st.header("📊 Candidate Comparison Graph")

        if "results" not in st.session_state:
            st.warning("No data available")
        else:
            df = st.session_state.results

            fig, ax = plt.subplots()
            ax.barh(df["Candidate Name"], df["Score (%)"])
            ax.set_xlabel("Match Score (%)")
            ax.set_ylabel("Candidate Name")
            ax.set_title("Resume Screening Results")

            st.pyplot(fig)

    # ------------------ LOGOUT ------------------
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))







