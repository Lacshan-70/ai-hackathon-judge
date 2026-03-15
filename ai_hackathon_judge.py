import streamlit as st
import streamlit_authenticator as stauth
from pptx import Presentation
import fitz
import requests
import re

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="AI Hackathon Judge",
    layout="wide"
)

# -------------------------
# MAC STYLE UI
# -------------------------

st.markdown("""
<style>

body {
background-color: #f5f5f7;
}

.main {
background-color: white;
padding: 2rem;
border-radius: 12px;
box-shadow: 0px 5px 20px rgba(0,0,0,0.08);
}

h1 {
font-weight:600;
}

.stButton>button {
border-radius:10px;
background:#0071e3;
color:white;
}

</style>
""", unsafe_allow_html=True)


# -------------------------
# LOGIN SYSTEM
# -------------------------

names = ["Admin"]
usernames = ["admin"]

passwords = ["admin123"]

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "ai_judge_cookie",
    "abcdef",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login","main")


if authentication_status == False:
    st.error("Username or password incorrect")

if authentication_status == None:
    st.warning("Please login")


# -------------------------
# MAIN APP
# -------------------------

if authentication_status:

    authenticator.logout("Logout", "sidebar")

    st.sidebar.success(f"Welcome {name}")

    st.title("AI Hackathon PPT Judge")

    uploaded_file = st.file_uploader(
        "Upload your presentation",
        type=["pptx","pdf"]
    )


# -------------------------
# PPT EXTRACTION
# -------------------------

    def extract_ppt(file):

        prs = Presentation(file)

        text = ""

        for slide in prs.slides:

            for shape in slide.shapes:

                if hasattr(shape,"text"):
                    text += shape.text + "\n"

        return text


# -------------------------
# PDF EXTRACTION
# -------------------------

    def extract_pdf(file):

        pdf = fitz.open(stream=file.read(), filetype="pdf")

        text = ""

        for page in pdf:
            text += page.get_text()

        return text


# -------------------------
# GROQ AI EVALUATION
# -------------------------

    def evaluate(text):

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
            "Content-Type": "application/json"
        }

        payload = {
            "model":"llama3-70b-8192",
            "messages":[
            {
            "role":"user",
            "content":f"""

You are a hackathon judge.

Evaluate the presentation based on:

Problem
Innovation
Feasibility
Impact
Implementation
Presentation

Return exactly this format:

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

{text}

"""
            }]
        }

        response = requests.post(url,headers=headers,json=payload)

        return response.json()["choices"][0]["message"]["content"]


# -------------------------
# SCORE PARSER
# -------------------------

    def parse_scores(result):

        scores = {}

        scores["Problem"] = int(re.search(r"Problem:\s*(\d+)", result).group(1))
        scores["Innovation"] = int(re.search(r"Innovation:\s*(\d+)", result).group(1))
        scores["Feasibility"] = int(re.search(r"Feasibility:\s*(\d+)", result).group(1))
        scores["Impact"] = int(re.search(r"Impact:\s*(\d+)", result).group(1))
        scores["Implementation"] = int(re.search(r"Implementation:\s*(\d+)", result).group(1))
        scores["Presentation"] = int(re.search(r"Presentation:\s*(\d+)", result).group(1))

        return scores


# -------------------------
# MAIN PROCESS
# -------------------------

    if uploaded_file:

        if uploaded_file.name.endswith(".pptx"):
            text = extract_ppt(uploaded_file)
        else:
            text = extract_pdf(uploaded_file)


        with st.spinner("AI evaluating presentation..."):

            result = evaluate(text)

        scores = parse_scores(result)

        total = sum(scores.values())

        probability = int((total/60)*100)


# -------------------------
# SCORE DASHBOARD
# -------------------------

        st.subheader("Score Summary")

        col1,col2,col3 = st.columns(3)

        col1.metric("Problem",f"{scores['Problem']}/10")
        col2.metric("Innovation",f"{scores['Innovation']}/10")
        col3.metric("Feasibility",f"{scores['Feasibility']}/10")

        col1.metric("Impact",f"{scores['Impact']}/10")
        col2.metric("Implementation",f"{scores['Implementation']}/10")
        col3.metric("Presentation",f"{scores['Presentation']}/10")


# -------------------------
# SELECTION PROBABILITY
# -------------------------

        st.subheader("Selection Probability")

        st.progress(probability/100)

        st.write(f"### {probability}% Chance of Selection")


# -------------------------
# JURY SUGGESTIONS
# -------------------------

        if "Suggestions:" in result:

            tips = result.split("Suggestions:")[1].split("\n")

            st.subheader("Jury Suggestions")

            for t in tips:
                if "-" in t:
                    st.info(t.replace("-","").strip())