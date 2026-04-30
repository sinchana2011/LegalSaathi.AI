import streamlit as st
import fitz
import re
from ai_engine import analyze_contract_clean, client
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="LegalSaathi", layout="wide")

# -------- HEADER (FIXED STRUCTURE) --------

st.markdown("""
<div style="text-align:center; margin-top:60px;">
    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" width="90" style="margin-bottom:10px;">
    <h1>⚖️ LegalSaathi AI</h1>
    <p class="subtitle">Understand before you sign</p>
</div>
""", unsafe_allow_html=True)

# -------- CSS (CLEAN + STABLE) --------
st.markdown("""
<style>

/* MAIN BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0f172a, #0a2472);
    color: #e2e8f0;
}

/* DO NOT OVERRIDE LAYOUT HEAVILY */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* TITLE */
h1 {
    font-size: 42px;
    font-weight: 800;
    margin: 5px 0;
    background: linear-gradient(to right, #00f5d4, #4cc9f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* SUBTITLE */
.subtitle {
    font-size: 18px;
    color: #94a3b8;
    margin-bottom: 20px;
}

/* CARD UI */
.card {
    background: rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 15px;
    border: 1px solid rgba(255,255,255,0.15);
}

/* RED FLAG */
.risk-card {
    background: rgba(255, 80, 80, 0.18);
    border-left: 5px solid #ff4d4d;
    padding: 12px;
    border-radius: 12px;
    color: #ffe4e4;
    margin-bottom: 10px;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(to right, #00f5d4, #4cc9f0);
    color: black;
    border-radius: 12px;
    font-weight: 600;
    border: none;
}

/* INPUT */
input, textarea {
    background-color: rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
}

/* SECTION SPACING */
h2, h3 {
    margin-top: 25px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "reviews" not in st.session_state:
    st.session_state.reviews = []
if "data" not in st.session_state:
    st.session_state.data = None
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# ---------------- LANGUAGE ----------------
lang = st.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])

def translate(text):
    if lang == "English":
        return text
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"Translate into {lang}:\n{text}"}]
    )
    return response.choices[0].message.content

def translate_severity(sev):
    mapping = {
        "High": "High",
        "Medium": "Medium",
        "Low": "Low"
    }
    return mapping.get(sev, sev)

# ---------------- PDF ----------------
def extract_text(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9.,;:()\- ]', '', text)
    return text.strip()

def split_clauses(text):
    return [c.strip() for c in text.split(".") if len(c.strip()) > 20]

# ---------------- RULE-BASED RISK ----------------
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
        if f["severity"] == "High":
            score += 3
        elif f["severity"] == "Medium":
            score += 2
        else:
            score += 1

    max_score = max(len(flags) * 3, 1)
    return int((score / max_score) * 100)

# ---------------- UI ----------------


uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file:
    raw_text = extract_text(uploaded_file)
    text = clean_text(raw_text)
    clauses = split_clauses(text)

    # -------- RULE ENGINE --------
    rule_flags = detect_risks(clauses)
    rule_risk = calculate_risk(rule_flags)

    # -------- ANALYZE --------
    if st.button("Analyze"):
        st.session_state.data = analyze_contract_clean(text)

    if st.session_state.data:
        data = st.session_state.data

        # -------- AI SUMMARY --------
        summary_prompt = f"""
        Convert this into a clear 5-6 line paragraph summary:

        {data['summary']}
        """

        summary = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": summary_prompt}]
        ).choices[0].message.content

        summary = "By signing this, you are agreeing to " + summary

        # 🔥 batch translation (avoid rate limit + consistency)
        combined = f"Summary:\n{summary}\n\nSimplified:\n{data['simplified']}"
        translated = translate(combined)

        parts = translated.split("Simplified:")

        summary = parts[0].replace("Summary:", "").strip()
        simplified = parts[1].strip() if len(parts) > 1 else data["simplified"]
                # -------- RISK SCORE --------
        st.subheader("⚠️ Risk Score")

        st.markdown(f"""
        <div style="
            width: 300px;
            height: 25px;
            background-color: rgba(255,255,255,0.1);
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 10px;
        ">
            <div style="
                width: {rule_risk}%;
                height: 100%;
                background: linear-gradient(to right, #00f5d4, #4cc9f0);
                border-radius: 20px;
                text-align: center;
                color: black;
                font-weight: bold;
                line-height: 25px;
            ">
                {rule_risk}%
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # -------- AI RED FLAGS --------
        st.subheader("🚨 AI Red Flags")
        for flag in data["red_flags"]:
            st.write(translate(f"{flag['clause']} ({flag['severity']})"))
        
        # -------- RULE RED FLAGS --------
        st.subheader("📍 Clause-Level Risks")
        for f in rule_flags[:10]:
            st.markdown(f"""
            <div class="risk-card">
            ⚠️ {translate(f['clause'])} <br>
            <small>{translate(f['explanation'])}</small>
            </div>
            """, unsafe_allow_html=True)

        # -------- MISSING CLAUSES --------
        st.subheader("❗ Missing Clauses")
        for clause in data["missing_clauses"]:
            st.write(translate(clause))

    # ---------------- CHATBOT ----------------
# ---------------- CHATBOT ----------------
st.subheader("💬 Chat with your Contract")

suggestions = [
    "",
    "Is there any penalty?",
    "What are the risks?",
    "Can I terminate early?",
    "Is there a non-compete clause?",
    "What should I be careful about?"
]

selected = st.selectbox("💡 Suggested Questions", suggestions, key="suggest_box")

if selected:
    st.session_state.user_input = selected

# ---------------- INPUT STATE SAFETY ----------------
if "last_processed" not in st.session_state:
    st.session_state.last_processed = ""

col1, col2 = st.columns([8, 2])

with col1:
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask your question",
            value=st.session_state.user_input,
            key="chat_input_box"
        )

        submitted = st.form_submit_button("Send")

with col2:
    audio = mic_recorder(
        start_prompt="🎤 Speak",
        stop_prompt="⏹ Stop",
        key="voice_input_1"
    )

    if audio:
        user_input = "Explain important risks"
        submitted = True  # 🔥 IMPORTANT FIX

# ---------------- CHAT LOGIC ----------------
if submitted and user_input and user_input != st.session_state.last_processed:

    st.session_state.last_processed = user_input

    # safety check
    contract_text = text if "text" in globals() else ""

    context = ""
    if st.session_state.data:
        d = st.session_state.data
        context = f"""
Summary: {d['summary']}
Simplified: {d['simplified']}
"""

    lang_instruction = "" if lang == "English" else f"Answer in {lang}."

    messages = [
        {"role": "system", "content": f"You are a smart legal assistant. {lang_instruction}"}
    ]

    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            messages.append({"role": "user", "content": chat["content"]})
        else:
            messages.append({"role": "assistant", "content": chat["content"]})

    messages.append({
        "role": "user",
        "content": f"Contract:\n{contract_text}\nContext:\n{context}\nQuestion: {user_input}"
    })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    answer = response.choices[0].message.content

    # store properly as dict (IMPORTANT FIX)
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.user_input = ""

# ---------------- CHAT DISPLAY (ONLY ONCE) ----------------
st.markdown("### 🧾 Chat History")

for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"🧑 **You:** {chat['content']}")
    else:
        st.markdown(f"🤖 **AI:** {chat['content']}")

# ---------------- REVIEW SECTION (ONLY ONCE, OUTSIDE CHAT) ----------------
st.markdown("---")
st.subheader("⭐ Rate LegalSaathi AI")

rating = st.radio(
    "Rating",
    ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
    key="rating_input"
)

feedback = st.text_area("Write feedback", key="feedback_input")

if st.button("Submit Review", key="submit_review_btn"):

    if feedback.strip():
        st.session_state.reviews.append({
            "rating": rating,
            "feedback": feedback
        })
        st.success("Thanks for your feedback!")
    else:
        st.warning("Please write feedback before submitting.")


if st.session_state.reviews:
    st.markdown("### 📊 Reviews")

    for r in reversed(st.session_state.reviews):
        st.markdown(f"""
        <div class="card">
             {r['rating']} <br>
            💬 {r['feedback']}
        </div>
        """, unsafe_allow_html=True)