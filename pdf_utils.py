import fitz  # PyMuPDF
import re

# -------- EXTRACT TEXT FROM PDF --------
def extract_text(file):
    try:
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = ""

        for page in pdf:
            text += page.get_text()

        return text

    except Exception as e:
        return f"Error reading PDF: {str(e)}"


# -------- CLEAN TEXT --------
def clean_text(text):
    try:
        # remove multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text)

        # remove unwanted characters (keep legal punctuation)
        text = re.sub(r'[^a-zA-Z0-9.,;:()\- ]', '', text)

        # fix spacing issues
        text = re.sub(r'\s([?.!,](?:\s|$))', r'\1', text)

        return text.strip()

    except:
        return text


# -------- OPTIONAL: SPLIT INTO CLAUSES --------
def split_into_clauses(text):
    clauses = text.split(".")
    return [c.strip() for c in clauses if c.strip()]