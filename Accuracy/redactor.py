import re
import spacy

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

def regex_redaction(text):
    # Email
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)

    # Phone numbers
    text = re.sub(r"\b\d{10,13}\b", "[PHONE]", text)

    # Dates
    text = re.sub(r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b", "[DATE]", text)

    # Addresses (simple rule)
    text = re.sub(
        r"\b\d{1,4} [A-Za-z ]+(Road|Street|St|Avenue|Ave|Lane|Ln)\b",
        "[ADDRESS]",
        text,
    )

    # ID numbers (6–12 digits)
    text = re.sub(r"\b\d{6,12}\b", "[ID]", text)

    return text


def ner_redaction(text):
    doc = nlp(text)
    new_text = text

    # Replace entities with tags
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            new_text = new_text.replace(ent.text, "[NAME]")
        elif ent.label_ == "GPE":
            new_text = new_text.replace(ent.text, "[LOCATION]")
        elif ent.label_ == "ORG":
            new_text = new_text.replace(ent.text, "[ORG]")
        elif ent.label_ == "DATE":
            new_text = new_text.replace(ent.text, "[DATE]")

    return new_text


def redact_text(text):
    # Step 1 → ML-based NER redaction
    text = ner_redaction(text)

    # Step 2 → Regex redaction
    text = regex_redaction(text)

    return text
