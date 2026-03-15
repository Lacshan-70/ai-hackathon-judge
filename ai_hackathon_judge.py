import streamlit as st
import streamlit_authenticator as stauth
from pptx import Presentation
import pdfplumber
import requests
import plotly.graph_objects as go

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="AI Hackathon Judge",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# LOGIN SYSTEM
# -----------------------------

names = ["Admin"]
usernames = ["admin"]

credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": "admin123"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "ai_judge_cookie",
    "abcdef",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password incorrect")

elif authentication_status == None:
    st.warning("Enter your username and password")

elif authentication_status:

    authenticator.logout("Logout", "sidebar")

    st.title("🤖 AI Hackathon PPT Judge")

    st.write("Upload your presentation and let AI evaluate it like a hackathon jury.")

# -----------------------------
# FILE UPLOADER
# -----------------------------

    uploaded_file = st.file_uploader(
        "Upload PPT or PDF",
        type=["pptx", "pdf"]
    )

# -----------------------------
# PPT TEXT EXTRACTION
# -----------------------------

    def extract_ppt_text(file):
        prs = Presentation(file)
        text = ""

        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"

        return text


# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------

    def extract_pdf_text(file):
        text = ""

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()

        return text


# -----------------------------
# GROQ AI EVALUATION
# -----------------------------

    def evaluate_presentation(text):

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        }

        prompt = f"""
You are a hackathon judge.

Evaluate this presentation.

Return results in this format only:

Problem: score/10
Innovation: score/10
Feasibility: score/10
Impact: score/10
Implementation: score/10
Presentation: score/10

Suggestions:
- point
- point
- point

Presentation text:
{text[:5000]}
"""

        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        result = response.json()

        return result["choices"][0]["message"]["content"]


# -----------------------------
# PROCESS FILE
# -----------------------------

    if uploaded_file:

        if uploaded_file.name.endswith(".pptx"):
            full_text = extract_ppt_text(uploaded_file)

        elif uploaded_file.name.endswith(".pdf"):
            full_text = extract_pdf_text(uploaded_file)

        st.subheader("Extracted Content")
        st.write(full_text[:1000])

        st.write("---")

        st.subheader("AI Evaluation")

        with st.spinner("AI is evaluating the presentation..."):

            result = evaluate_presentation(full_text)

        st.write(result)

# -----------------------------
# DEMO SCORES (UI)
# -----------------------------

        problem = 8
        innovation = 7
        feasibility = 7
        impact = 8
        implementation = 7
        presentation = 8

        total_score = (
            problem + innovation + feasibility +
            impact + implementation + presentation
        )

        probability = int((total_score / 60) * 100)

# -----------------------------
# SCORE CARDS
# -----------------------------

        st.write("---")
        st.subheader("Score Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Problem", f"{problem}/10")
            st.metric("Impact", f"{impact}/10")

        with col2:
            st.metric("Innovation", f"{innovation}/10")
            st.metric("Implementation", f"{implementation}/10")

        with col3:
            st.metric("Feasibility", f"{feasibility}/10")
            st.metric("Presentation", f"{presentation}/10")

# -----------------------------
# SELECTION PROBABILITY
# -----------------------------

        st.write("---")

        st.subheader("Selection Probability")

        st.progress(probability / 100)

        st.write(f"### {probability}% Chance of Selection")

# -----------------------------
# LINE GRAPH
# -----------------------------

        st.write("---")

        st.subheader("Evaluation Trend")

        scores = [
            problem,
            innovation,
            feasibility,
            impact,
            implementation,
            presentation
        ]

        labels = [
            "Problem",
            "Innovation",
            "Feasibility",
            "Impact",
            "Implementation",
            "Presentation"
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=labels,
            y=scores,
            mode='lines+markers',
            line=dict(width=4),
            marker=dict(size=10)
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Evaluation Criteria",
            yaxis_title="Score",
            yaxis=dict(range=[0,10])
        )

        st.plotly_chart(fig, use_container_width=True)