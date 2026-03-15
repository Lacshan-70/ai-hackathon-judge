import streamlit as st
from pptx import Presentation
import fitz
import requests
import re

st.set_page_config(page_title="Hackathon PPT AI Judge", layout="wide")

st.title("Hackathon PPT AI Judge")
st.write("Upload your hackathon presentation and AI will evaluate it.")

uploaded_file = st.file_uploader("Upload PPT or PDF", type=["pptx","pdf"])


# -------- Extract slides from PPT --------

def extract_slides_ppt(file):

    prs = Presentation(file)
    slides = []

    for i, slide in enumerate(prs.slides):

        slide_text = ""

        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text += shape.text + "\n"

        slides.append({
            "slide_number": i+1,
            "text": slide_text
        })

    return slides


# -------- Extract slides from PDF --------

def extract_slides_pdf(file):

    slides = []

    pdf = fitz.open(stream=file.read(), filetype="pdf")

    for i,page in enumerate(pdf):

        slides.append({
            "slide_number": i+1,
            "text": page.get_text()
        })

    return slides


# -------- Evaluate slide --------

def evaluate_slide(text):

    prompt = f"""
You are a hackathon judge.

Analyze this slide and identify what type of slide it is:

Problem
Solution
Architecture
Implementation
Impact
Other

Then evaluate its quality.

Return exactly:

Slide Type: TYPE
Score: X/10
Suggestion: improvement suggestion

Slide Content:
{text}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


# -------- Overall evaluation --------

def evaluate_presentation(text):

    prompt = f"""
You are a hackathon jury member.

Evaluate this presentation based on:

Problem
Innovation
Feasibility
Impact
Implementation
Presentation

Return exactly:

Problem: X/10
Innovation: X/10
Feasibility: X/10
Impact: X/10
Implementation: X/10
Presentation: X/10

Suggestions:
- suggestion
- suggestion
- suggestion

Presentation Content:
{text}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


# -------- Parse scores --------

def parse_scores(result):

    scores = {
        "Problem": int(re.search(r"Problem:\s*(\d+)", result).group(1)),
        "Innovation": int(re.search(r"Innovation:\s*(\d+)", result).group(1)),
        "Feasibility": int(re.search(r"Feasibility:\s*(\d+)", result).group(1)),
        "Impact": int(re.search(r"Impact:\s*(\d+)", result).group(1)),
        "Implementation": int(re.search(r"Implementation:\s*(\d+)", result).group(1)),
        "Presentation": int(re.search(r"Presentation:\s*(\d+)", result).group(1))
    }

    return scores


# -------- Parse suggestions --------

def parse_suggestions(result):

    suggestions = []

    if "Suggestions:" in result:

        part = result.split("Suggestions:")[1]

        lines = part.split("\n")

        for line in lines:
            if "-" in line:
                suggestions.append(line.replace("-", "").strip())

    return suggestions


# -------- Main logic --------

if uploaded_file:

    if uploaded_file.name.endswith(".pptx"):
        slides = extract_slides_ppt(uploaded_file)
    else:
        slides = extract_slides_pdf(uploaded_file)


    full_text = ""

    for slide in slides:
        full_text += slide["text"] + "\n"


    st.subheader("AI Evaluation Running...")

    result = evaluate_presentation(full_text)

    scores = parse_scores(result)

    suggestions = parse_suggestions(result)


    # -------- Score cards --------

    st.subheader("Score Summary")

    col1,col2,col3 = st.columns(3)

    with col1:
        st.metric("Problem",f"{scores['Problem']}/10")
        st.metric("Impact",f"{scores['Impact']}/10")

    with col2:
        st.metric("Innovation",f"{scores['Innovation']}/10")
        st.metric("Implementation",f"{scores['Implementation']}/10")

    with col3:
        st.metric("Feasibility",f"{scores['Feasibility']}/10")
        st.metric("Presentation",f"{scores['Presentation']}/10")


    # -------- Selection probability --------

    total_score = sum(scores.values())

    probability = int((total_score/60)*100)

    st.subheader("Selection Probability")

    st.progress(probability/100)

    st.write(f"### {probability}% Chance of Selection")


    # -------- Suggestions --------

    st.subheader("💡 Jury Suggestions")

    for tip in suggestions:
        st.info(tip)


    # -------- Slide analysis --------

    st.subheader("Slide-by-Slide Analysis")

    for slide in slides:

        st.markdown(f"### Slide {slide['slide_number']}")

        result = evaluate_slide(slide["text"])

        st.info(result)