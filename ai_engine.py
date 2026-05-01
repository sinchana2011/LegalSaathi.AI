import os
import streamlit as st
from groq import Groq
import json

# ---------------- SAFE CLIENT ----------------
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

    Analyze the contract and STRICTLY return valid JSON.

    Format:
    {
        "summary": "Detailed legal summary in 5-6 lines",
        "simplified": "Explain in very simple language for a normal person",
        "red_flags": [
            {"clause": "text", "severity": "High"},
            {"clause": "text", "severity": "Medium"}
        ],
        "missing_clauses": [
            "Termination clause",
            "Dispute resolution clause"
        ]
    }

    Rules:
    - Always return valid JSON
    - Do NOT add extra text outside JSON
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

        # 🧠 Clean JSON (important for Groq responses)
        if "```" in output:
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output.replace("json", "", 1)

        data = json.loads(output)

        # ✅ Ensure all keys exist (VERY IMPORTANT)
        return {
            "summary": data.get("summary", ""),
            "simplified": data.get("simplified", ""),
            "red_flags": data.get("red_flags", []),
            "missing_clauses": data.get("missing_clauses", [])
        }

    except Exception as e:
        # 🔥 fallback (prevents UI breaking)
        return {
            "summary": "Unable to generate summary.",
            "simplified": "Try again.",
            "red_flags": [],
            "missing_clauses": []
        }
