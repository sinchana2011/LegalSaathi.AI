from groq import Groq
import json
import os
client = Grok(api_key=os.getenv("GROQ_API_KEY"))

# 🔹 STEP 1: SYSTEM PROMPT
SYSTEM_PROMPT = """
You are a legal AI assistant.

Return ONLY JSON:

{
  "contract_type": "string",
  "summary": "string",
  "simplified": "string",
  "red_flags": [
    {
      "clause": "string",
      "reason": "string",
      "severity": "high/medium/low"
    }
  ],
  "missing_clauses": []
}

Rules:
- Identify contract type correctly
- Use very simple English
- Highlight financial and legal risks clearly
- Red flags include:
  penalty, non-compete, indemnity, liability, arbitration,
  automatic renewal, hidden charges, termination issues
- Do NOT add extra text
- Do NOT use markdown
"""
STANDARD_CLAUSES = {
    "Employment": ["salary", "termination", "leave", "confidentiality"],
    "NDA": ["confidentiality", "duration", "penalty", "jurisdiction"],
    "SaaS": ["pricing", "data privacy", "termination", "uptime"]
}


# 🔹 STEP 2: VALIDATE FUNCTION (PUT HERE 👇)
def validate(data):
    required_keys = ["summary", "simplified", "red_flags", "missing_clauses"]
    
    for key in required_keys:
        if key not in data:
            if key in ["red_flags", "missing_clauses"]:
                data[key] = []
            else:
                data[key] = ""
    
    return data
def find_missing_clauses(contract_type, text):
    expected = STANDARD_CLAUSES.get(contract_type, [])
    missing = []
    text_lower = text.lower()

    for clause in expected:
        if clause.lower() not in text_lower:
            missing.append(clause)

    return missing



# 🔹 STEP 3: MAIN FUNCTION
def analyze_contract_clean(text):

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(response.choices[0].message.content)
    except:
        data = {}

    # 🔥 STEP 4: VALIDATE CALLED HERE
    data = validate(data)

    return data

