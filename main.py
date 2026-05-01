import streamlit as st
import fitz
import re

# ✅ SAFE IMPORTS (CRITICAL FIX)
try:
    from ai_engine import analyze_contract_clean, client
except:
    analyze_contract_clean = None
    client = None

try:
    from streamlit_mic_recorder import mic_recorder
    voice_enabled = True
except:
    voice_enabled = False

st.set_page_config(page_title="LegalSaathi", layout="wide")

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
    if lang == "English" or not client:
        return text
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Translate into {lang}:\n{text}"}]
        )
        return response.choices[0].message.content
    except:
        return text

# -------- PDF --------
def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

def clean_text(text):
    return re.sub(r'\s+', ' ', text)

def split_clauses(text):
    return [c.strip() for c in text.split(".") if len(c.strip()) > 20]

# -------- RISK --------
def detect_risks(clauses):
    keywords = {
        "terminate": "High",
        "penalty": "High",
        "indemnity": "High",
        "liability": "Medium",
        "arbitration": "Medium",
        "confidential": "Low"
    }
    flags = []
    for clause in clauses:
        for k, v in keywords.items():
            if k in clause.lower():
                flags.append({"clause": clause, "severity": v})
    return flags

def calculate_risk(flags):
    score = sum([3 if f["severity"]=="High" else 2 if f["severity"]=="Medium" else 1 for f in flags])
    return int((score / max(len(flags)*3,1))*100)

# -------- UI --------
uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file:
    text = clean_text(extract_text(uploaded_file))
    clauses = split_clauses(text)

    rule_flags = detect_risks(clauses)
    rule_risk = calculate_risk(rule_flags)

    # ✅ ANALYZE BUTTON FIX
    if st.button("Analyze"):
        if analyze_contract_clean:
            st.session_state.data = analyze_contract_clean(text)
        else:
            st.error("AI engine not available")

    if st.session_state.data:
        data = st.session_state.data

        # -------- SUMMARY --------
        summary = data.get("summary", "")
        simplified = data.get("simplified", "")

        st.subheader("📄 Summary")
        st.write(translate(summary))

        st.subheader("🧠 Simplified")
        st.write(translate(simplified))

        # -------- RISK --------
        st.subheader("⚠️ Risk Score")
        st.progress(rule_risk/100)
        st.write(f"{rule_risk}% Risk")

        # -------- FLAGS --------
        st.subheader("🚨 AI Red Flags")
        for f in data.get("red_flags", []):
            st.write(translate(f"{f['clause']} ({f['severity']})"))

        st.subheader("❗ Missing Clauses")
        for c in data.get("missing_clauses", []):
            st.write(translate(c))

# -------- CHAT --------
st.subheader("💬 Chat with Contract")

user_input = st.text_input("Ask something")

if voice_enabled:
    audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="⏹ Stop")
    if audio:
        user_input = "Explain risks"

if st.button("Send") and user_input:
    if client:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": user_input}]
        )
        answer = response.choices[0].message.content
    else:
        answer = "AI not available"

    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("AI", answer))

for role, msg in st.session_state.chat_history:
    st.write(f"**{role}:** {msg}")

# -------- REVIEW --------
st.subheader("⭐ Review")

rating = st.radio("Rate", ["⭐","⭐⭐","⭐⭐⭐","⭐⭐⭐⭐","⭐⭐⭐⭐⭐"])
feedback = st.text_area("Feedback")

if st.button("Submit Review"):
    st.session_state.reviews.append((rating, feedback))

for r,f in st.session_state.reviews:
    st.write(r, "-", f)
