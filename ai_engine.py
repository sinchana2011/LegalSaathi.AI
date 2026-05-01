import os
import streamlit as st
from groq import Groq

def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv("GROQ_API_KEY")

# ✅ THIS MUST EXIST
client = Groq(api_key=get_api_key())


def analyze_contract_clean(text):
    SYSTEM_PROMPT = """
    You are a legal AI assistant.

    Return JSON:
    {
        "summary": "...",
        "simplified": "...",
        "red_flags": [{"clause": "...", "severity": "High"}],
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

    import json
    output = response.choices[0].message.content

    try:
        return json.loads(output)
    except:
        return {
            "summary": output,
            "simplified": output,
            "red_flags": [],
            "missing_clauses": []
        }
