# eval_app.py
import streamlit as st
import pandas as pd
from redactor import RedactionEngine
from Levenshtein import distance
import json
import zipfile
from io import StringIO
import time
from pathlib import Path

st.set_page_config(page_title="Redaction Accuracy Evaluator", layout="wide")
st.title("🔍 Redaction Accuracy Evaluation Dashboard")
st.markdown("Evaluate your PII redaction engine on single texts or batch test files.")

# Load engine
@st.cache_resource
def load_engine():
    with st.spinner("Loading Presidio Analyzer + Custom Patterns..."):
        time.sleep(1)
        return RedactionEngine()
engine = load_engine()

# Sidebar
st.sidebar.header("Evaluation Settings")
mode = st.sidebar.radio("Redaction Mode", ["Redact (remove)", "Mask with [ENTITY]"], index=0)
mode_key = "redact" if mode.startswith("Redact") else "mask"

# Main tabs
tab1, tab2, tab3 = st.tabs(["Single Text Test", "Upload Test Dataset", "Batch Results & Metrics"])

# ================================
# Tab 1: Single Text Evaluation
# ================================
with tab1:
    st.header("Test on Single Input")
    sample_text = st.text_area(
        "Enter text to evaluate",
        height=200,
        value="Contact: Jane Doe, email: jane.doe@company.org, phone: +44 7700 900123, "
              "SSN: 123-45-6789, address: 221B Baker Street, London. "
              "Card: 6011 0009 9013 9424, IP: 192.168.1.100"
    )

    if st.button("Evaluate Single Text", type="primary"):
        with st.spinner("Analyzing..."):
            redacted, entities = engine.process(sample_text, mode=mode_key)
            lev_dist = distance(sample_text, redacted)
            max_len = max(len(sample_text), len(redacted), 1)
            similarity = 1 - lev_dist / max_len

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original")
            st.code(sample_text)
        with col2:
            st.subheader(f"{mode.split('(')[0]}Output")
            st.code(redacted)

        st.metric("Levenshtein Distance", lev_dist)
        st.metric("Similarity Score (higher = less changed)", f"{similarity:.4f}")

        if entities:
            df = pd.DataFrame(entities)
            df.index = range(1, len(df) + 1)
            st.subheader("Detected Entities")
            st.dataframe(df[["type", "text", "start", "end"]], use_container_width=True)
        else:
            st.info("No entities detected.")

# ================================
# Tab 2: Upload Test Dataset
# ================================
with tab2:
    st.header("Upload Test Dataset")
    st.markdown("""
    Supported formats:
    - `.txt` – one document per file
    - `.jsonl` – JSON Lines: `{"id": 1, "text": "Hello..."}`
    - `.zip` – containing multiple `.txt` or `.jsonl` files
    """)

    uploaded_file = st.file_uploader("Upload test files", type=["txt", "jsonl", "zip"])

    if uploaded_file:
        files_to_process = []

        if uploaded_file.type == "application/zip":
            with zipfile.ZipFile(uploaded_file) as z:
                for name in z.namelist():
                    if name.endswith(('.txt', '.jsonl')):
                        content = z.read(name).decode("utf-8")
                        files_to_process.append({"name": name, "content": content})
        else:
            content = uploaded_file.read().decode("utf-8")
            name = uploaded_file.name
            if uploaded_file.type == "text/plain":
                files_to_process.append({"name": name, "content": content})
            elif "json" in uploaded_file.type:
                for line in content.splitlines():
                    if line.strip():
                        data = json.loads(line)
                        files_to_process.append({"name": f"{name}_doc{len(files_to_process)}", "content": data.get("text", "")})

        st.success(f"Loaded {len(files_to_process)} document(s) for evaluation")

        if st.button("Run Batch Evaluation", type="primary"):
            progress_bar = st.progress(0)
            results = []

            for i, doc in enumerate(files_to_process):
                text = doc["content"]
                redacted, entities = engine.process(text, mode=mode_key)

                lev_dist = distance(text, redacted)
                max_len = max(len(text), len(redacted), 1)
                similarity = 1 - lev_dist / max_len
                entity_count = len(entities)

                results.append({
                    "Document": doc["name"],
                    "Length": len(text),
                    "Entities Found": entity_count,
                    "Levenshtein Distance": lev_dist,
                    "Similarity Score": round(similarity, 4),
                    "Redacted Preview": redacted[:200] + "..." if len(redacted) > 200 else redacted
                })

                progress_bar.progress((i + 1) / len(files_to_process))

            progress_bar.empty()
            st.session_state.batch_results = results
            st.success("Batch evaluation complete!")

# ================================
# Tab 3: Results & Metrics
# ================================
with tab3:
    st.header("Batch Evaluation Results")

    if hasattr(st.session_state, "batch_results") and st.session_state.batch_results:
        df_results = pd.DataFrame(st.session_state.batch_results)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Documents", len(df_results))
        col2.metric("Avg Entities Found", f"{df_results['Entities Found'].mean():.2f}")
        col3.metric("Avg Similarity", f"{df_results['Similarity Score'].mean():.4f}")
        col4.metric("Best Similarity", f"{df_results['Similarity Score'].max():.4f}")

        st.subheader("Detailed Results")
        st.dataframe(df_results, use_container_width=True)

        # Download results
        csv = df_results.to_csv(index=False)
        st.download_button(
            "📥 Download Results as CSV",
            csv,
            "redaction_evaluation_results.csv",
            "text/csv"
        )

        # Show individual document comparison
        st.subheader("Inspect Individual Document")
        doc_options = ["Select a document..."] + df_results["Document"].tolist()
        selected = st.selectbox("Choose document to inspect", doc_options)

        if selected and selected != "Select a document...":
            idx = df_results[df_results["Document"] == selected].index[0]
            original_text = files_to_process[idx]["content"]
            redacted_text, entities = engine.process(original_text, mode=mode_key)

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Original")
                st.code(original_text)
            with c2:
                st.subheader("Redacted / Masked")
                st.code(redacted_text)

            if entities:
                ent_df = pd.DataFrame(entities)
                st.subheader("Entities Detected")
                st.dataframe(ent_df[["type", "text"]], use_container_width=True)
    else:
        st.info("Run a batch evaluation first to see results here.")