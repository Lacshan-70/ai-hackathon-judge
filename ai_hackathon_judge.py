import streamlit as st
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
# SIMPLE LOGIN SYSTEM
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():

    st.title("🤖 AI Hackathon Judge Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.rerun()

        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# -----------------------------
# APP HEADER
# -----------------------------

st.title("🤖 AI Hackathon PPT Judge")

st.write(
    "Upload your hackathon presentation and AI will evaluate it like a jury."
)

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
            page_text = page.extract_text()

            if page_text:
                text += page_text

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

Return bullet point feedback.

Presentation:
{text[:4000]}
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

    with st.spinner("AI is evaluating your presentation..."):

        result = evaluate_presentation(full_text)

    st.subheader("AI Jury Feedback")

    st.write(result)

# -----------------------------
# DEMO SCORES
# -----------------------------

    problem = 8
    innovation = 7
    feasibility = 7
    impact = 8
    implementation = 7
    presentation = 8

    total = (
        problem +
        innovation +
        feasibility +
        impact +
        implementation +
        presentation
    )

    probability = int((total / 60) * 100)

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
# GRAPH
# -----------------------------

    st.write("---")

    st.subheader("Evaluation Trend")

    labels = [
        "Problem",
        "Innovation",
        "Feasibility",
        "Impact",
        "Implementation",
        "Presentation"
    ]

    scores = [
        problem,
        innovation,
        feasibility,
        impact,
        implementation,
        presentation
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=scores,
            mode="lines+markers"
        )
    )

    fig.update_layout(
        yaxis=dict(range=[0,10])
    )

    st.plotly_chart(fig, use_container_width=True)