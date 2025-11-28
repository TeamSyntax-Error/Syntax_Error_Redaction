# app.py
import streamlit as st
from redactor import RedactionEngine
from Levenshtein import distance
import time

st.set_page_config(page_title="Redaction Challenge", layout="wide")
st.title("The Redaction Challenge")
st.markdown("**All 8 entities • Redact or Mask • Entity Table • Levenshtein Score**")

@st.cache_resource
def load_engine():
    with st.spinner("Loading Microsoft Presidio + Transformer model..."):
        time.sleep(1)
    return RedactionEngine()

engine = load_engine()

mode = st.sidebar.radio("Mode", ["Redact (remove)", "Mask with [ENTITY]"])
mode_key = "redact" if "Redact" in mode else "mask"

text = st.text_area("Paste or type text here", height=200,
    value="John Smith lives at 123 Main St, New York. His email is john.doe@gmail.com and phone is +1 (555) 123-4567. "
          "Credit card: 4532-7890-1234-5678. Meeting on 2025-12-25 at https://zoom.us/j/123456789")

if st.button("Run Redaction", type="primary"):
    with st.spinner("Processing..."):
        redacted, entities = engine.process(text, mode=mode_key)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.code(text)
    with col2:
        st.subheader("Redacted / Masked")
        st.code(redacted)

    # Levenshtein similarity
    sim = 1 - distance(text, redacted) / max(len(text), len(redacted), 1)
    st.metric("Levenshtein Similarity", f"{sim:.4f}")

    # Entity table
    if entities:
        import pandas as pd
        df = pd.DataFrame(entities)
        df.index = range(1, len(df)+1)
        st.subheader("Detected Entities")
        st.dataframe(df[["type", "text", "start", "end"]], use_container_width=True)
    else:
        st.success("No PII detected!")

    st.download_button("Download Redacted Text", redacted, "redacted.txt")