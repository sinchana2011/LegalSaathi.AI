import os
import streamlit as st
from groq import Groq

# ---------------- SAFE CLIENT INIT ----------------
def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv("GROQ_API_KEY")

client = Groq(api_key=get_api_key())


# ---------------- MAIN FUNCTION ----------------
def analyze_contract_clean(text):

    SYSTEM_PROMPT = """
    You are a legal AI assistant.

    Analyze the contract and return JSON in this format:
    {
        "summary": "...",
        "simplified": "...",
        "red_flags": [
            {"clause": "...", "severity": "High/Medium/Low"}
        ],
        "missing_clauses": ["..."]
    }
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    )

    output = response.choices[0].message.content

    # 🔥 VERY IMPORTANT: Convert string → dict
    import json
    try:
        return json.loads(output)
    except:
        return {
            "summary": output,
            "simplified": output,
            "red_flags": [],
            "missing_clauses": []
        }
