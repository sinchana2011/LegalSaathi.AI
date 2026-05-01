import streamlit as st
import fitz
import re
import requests
from ai_engine import analyze_contract_clean
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="LegalSaathi", layout="wide")

# -------- GROQ API WRAPPER (FIX) --------
def call_groq(messages):
    api_key = st.secrets["GROQ_API_KEY"]

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["choices"][0]["message"]["content"]


# -------- HEADER --------
st.markdown("""
<div style="text-align:center; margin-top:60px;">
    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" width="90">
    <h1>⚖️ LegalSaathi AI</h1>
    <p class="subtitle">Understand before you sign</p>
</div>
""", unsafe_allow_html=True)

# -------- SESSION --------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "reviews" not in st.session_state:
    st.session_state.reviews = []
if "data" not in st.session_state:
    st.session_state.data = None
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# -------- LANGUAGE --------
lang = st.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])

def translate(text):
    if lang == "English":
        return text
    return call_groq([
        {"role": "user", "content": f"Translate into {lang}:\n{text}"}
    ])

# -------- PDF --------
def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_clauses(text):
    return [c.strip() for c in text.split(".") if len(c.strip()) > 20]

# -------- RULE ENGINE --------
def detect_risks(clauses):
    keywords = {
        "terminate": ("High", "Agreement can be terminated"),
        "penalty": ("High", "Financial penalty involved"),
        "indemnity": ("High", "You may cover losses"),
        "liability": ("Medium", "Legal responsibility"),
        "arbitration": ("Medium", "Outside court dispute"),
        "confidential": ("Low", "Privacy requirement")
    }

    flags = []
    for clause in clauses:
        for word, (level, explanation) in keywords.items():
            if word in clause.lower():
                flags.append({
                    "clause": clause,
                    "severity": level,
                    "explanation": explanation
                })
    return flags

def calculate_risk(flags):
    score = 0
    for f in flags:
        score += 3 if f["severity"] == "High" else 2 if f["severity"] == "Medium" else 1
    return int((score / max(len(flags)*3,1)) * 100)

# -------- UI --------
uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file:
    raw_text = extract_text(uploaded_file)
    text = clean_text(raw_text)
    clauses = split_clauses(text)

    rule_flags = detect_risks(clauses)
    rule_risk = calculate_risk(rule_flags)

    if st.button("Analyze"):
        st.session_state.data = analyze_contract_clean(text)

    if st.session_state.data:
        data = st.session_state.data

        summary_prompt = f"Convert into 5-6 line summary:\n{data['summary']}"
        summary = call_groq([{"role": "user", "content": summary_prompt}])
        summary = "By signing this, you are agreeing to " + summary

        combined = f"Summary:\n{summary}\n\nSimplified:\n{data['simplified']}"
        translated = translate(combined)

        parts = translated.split("Simplified:")
        summary = parts[0].replace("Summary:", "").strip()
        simplified = parts[1].strip() if len(parts) > 1 else data["simplified"]

        st.subheader("⚠️ Risk Score")
        st.write(rule_risk)

        st.subheader("🚨 AI Red Flags")
        for flag in data["red_flags"]:
            st.write(translate(f"{flag['clause']} ({flag['severity']})"))

        st.subheader("📍 Clause-Level Risks")
        for f in rule_flags[:10]:
            st.write(translate(f["clause"]))

        st.subheader("❗ Missing Clauses")
        for clause in data["missing_clauses"]:
            st.write(translate(clause))

# -------- CHAT --------
st.subheader("💬 Chat")

user_input = st.text_input("Ask question")

if user_input:
    answer = call_groq([
        {"role": "user", "content": user_input}
    ])
    st.write(answer)
