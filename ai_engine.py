import os
import json
import streamlit as st
from groq import Groq

# -------- SAFE API KEY --------
def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.getenv("GROQ_API_KEY")

client = None

try:
    client = Groq(api_key=get_api_key())
except Exception as e:
    print("Client init error:", e)
    client = None


# -------- MAIN FUNCTION --------
def analyze_contract_clean(text):

    # 🔒 If client fails, don't crash UI
    if client is None:
        return {
            "summary": "AI not available. Check API key.",
            "simplified": "Unable to process contract.",
            "red_flags": [],
            "missing_clauses": []
        }

    SYSTEM_PROMPT = """
    You are a legal AI assistant.

    Analyze the contract and STRICTLY return valid JSON.

    Format:
    {
        "summary": "5-6 line legal summary",
        "simplified": "Explain in simple language",
        "red_flags": [
            {"clause": "text", "severity": "High"},
            {"clause": "text", "severity": "Medium"}
        ],
        "missing_clauses": [
            "Termination clause",
            "Penalty clause",
            "Dispute resolution clause"
        ]
    }

    Rules:
    - ONLY return JSON
    - NO extra text
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]
        )

        output = response.choices[0].message.content.strip()

        # 🔥 Clean markdown JSON if present
        if "```" in output:
            parts = output.split("```")
            output = parts[1]
            if output.startswith("json"):
                output = output.replace("json", "", 1).strip()

        data = json.loads(output)

        return {
            "summary": data.get("summary", ""),
            "simplified": data.get("simplified", ""),
            "red_flags": data.get("red_flags", []),
            "missing_clauses": data.get("missing_clauses", [])
        }

    except Exception as e:
        print("AI error:", e)

        # 🔥 fallback so UI never breaks
        return {
            "summary": "Error generating summary.",
            "simplified": "Try again.",
            "red_flags": [],
            "missing_clauses": []
        }
