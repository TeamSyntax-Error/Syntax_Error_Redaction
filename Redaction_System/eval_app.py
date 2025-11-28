import streamlit as st
import pandas as pd
from redactor import RedactionEngine
from Levenshtein import distance
import json
import zipfile
import time

st.set_page_config(page_title="Redaction Accuracy Evaluator", layout="wide")
st.title("🔍 Redaction Accuracy Evaluation Dashboard")

@st.cache_resource
def load_engine():
    with st.spinner("Loading Presidio Analyzer + Custom Patterns..."):
        time.sleep(1)
        return RedactionEngine()

engine = load_engine()

st.sidebar.header("Evaluation Settings")
mode = st.sidebar.radio("Redaction Mode", ["Redact (remove)", "Mask with [ENTITY]"], index=0)
mode_key = "redact" if mode.startswith("Redact") else "mask"

tab1, tab2, tab3 = st.tabs(["Single Text Test", "Upload Test Dataset", "Batch Results & Metrics"])

with tab1:
    st.header("Test on Single Input with Preview")
    
    input_text = st.text_area(
        "Enter text to evaluate",
        height=200,
        value="Contact: Jane Doe, email: jane.doe@company.org, phone: +44 7700 900123, "
              "SSN: 123-45-6789, address: 221B Baker Street, London. "
              "Card: 6011 0009 9013 9424, IP: 192.168.1.100"
    )
    
    col_preview, col_actions = st.columns([3, 1])
    with col_actions:
        preview_button = st.button("Preview Redaction", type="secondary")
        commit_button = st.button("Commit Redaction", type="primary")
    
    if preview_button or commit_button:
        with st.spinner("Analyzing text for redaction..."):
            preview_redacted, entities = engine.process(input_text, mode=mode_key)
            lev_dist = distance(input_text, preview_redacted)
            max_len = max(len(input_text), len(preview_redacted), 1)
            similarity = 1 - lev_dist / max_len
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Text")
            st.code(input_text)
        with col2:
            st.subheader("Redaction Preview")
            st.code(preview_redacted)
        
        if preview_button and not commit_button:
            st.warning("🔍 This is a preview of the redaction. Click 'Commit Redaction' to confirm the result.")
        else:
            st.success("✅ Redaction has been committed.")
        
        st.metric("Levenshtein Distance", lev_dist)
        st.metric("Similarity Score", f"{similarity:.4f}")
        
        if entities:
            df = pd.DataFrame(entities)
            df.index = range(1, len(df) + 1)
            st.subheader("Detected Entities")
            st.dataframe(df[["type", "text", "start", "end"]], use_container_width=True)

with tab2:
    st.header("Batch Evaluation with Preview")
    
    uploaded_file = st.file_uploader("Upload test files", type=["txt", "jsonl", "zip"])
    
    if uploaded_file is not None:
        # Clear previous results when new file is uploaded
        if 'files_to_process' not in st.session_state:
            st.session_state.files_to_process = []
        
        if uploaded_file.type == "application/zip":
            with zipfile.ZipFile(uploaded_file) as z:
                files_to_process = []
                for name in z.namelist():
                    if name.endswith(('.txt', '.jsonl')):
                        content = z.read(name).decode("utf-8")
                        files_to_process.append({"name": name, "content": content})
        else:
            content = uploaded_file.read().decode("utf-8")
            name = uploaded_file.name
            files_to_process = []
            if uploaded_file.type == "text/plain":
                files_to_process.append({"name": name, "content": content})
            elif "json" in uploaded_file.type:
                for i, line in enumerate(content.splitlines()):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            files_to_process.append({"name": f"{name}_doc{i+1}", "content": data.get("text", "")})
                        except json.JSONDecodeError:
                            continue
        
        st.session_state.files_to_process = files_to_process
        st.success(f"Loaded {len(files_to_process)} document(s) for evaluation")
    
    # Only proceed if files are loaded
    if 'files_to_process' in st.session_state and st.session_state.files_to_process:
        files_to_process = st.session_state.files_to_process
        
        col_batch1, col_batch2 = st.columns(2)
        with col_batch1:
            if st.button("Generate Batch Preview", type="secondary"):
                progress_bar = st.progress(0)
                preview_results = []
                
                for i, doc in enumerate(files_to_process):
                    text = doc["content"]
                    redacted, entities = engine.process(text, mode=mode_key)
                    lev_dist = distance(text, redacted)
                    max_len = max(len(text), len(redacted), 1)
                    similarity = 1 - lev_dist / max_len
                    
                    preview_results.append({
                        "Document": doc["name"],
                        "Length": len(text),
                        "Entities Found": len(entities),
                        "Levenshtein Distance": lev_dist,
                        "Similarity Score": round(similarity, 4),
                        "Preview Redacted": redacted
                    })
                    progress_bar.progress((i + 1) / len(files_to_process))
                
                st.session_state.batch_preview_results = preview_results
                progress_bar.empty()
                st.success(f"Preview generated for {len(preview_results)} documents.")
        
        with col_batch2:
            commit_disabled = 'batch_preview_results' not in st.session_state
            if st.button("Commit Batch Redaction", type="primary", disabled=commit_disabled):
                if 'batch_preview_results' in st.session_state:
                    st.session_state.batch_results = st.session_state.batch_preview_results.copy()
                    st.success("Batch redaction has been committed.")
    
    if 'batch_preview_results' in st.session_state:
        st.info(f"Preview mode active. {len(st.session_state.batch_preview_results)} documents are ready for review.")
        df_preview = pd.DataFrame(st.session_state.batch_preview_results)
        st.subheader("Batch Preview Results")
        st.dataframe(df_preview[["Document", "Entities Found", "Similarity Score"]], use_container_width=True)
        
        selected_doc = st.selectbox("Preview individual document:", 
                                 ["Select document for detailed preview..."] + df_preview["Document"].tolist())
        if selected_doc and selected_doc != "Select document for detailed preview...":
            # Find the original text from the stored files
            original_text = None
            for doc in st.session_state.files_to_process:
                if doc["name"] == selected_doc:
                    original_text = doc["content"]
                    break
            
            if original_text is not None:
                # Get the previewed redacted text
                preview_data = next(item for item in st.session_state.batch_preview_results if item["Document"] == selected_doc)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Original Text")
                    st.text_area("Original", original_text, height=200)
                with col2:
                    st.subheader("Redaction Preview")
                    st.text_area("Preview", preview_data["Preview Redacted"], height=200)
            else:
                st.error(f"Original text for document '{selected_doc}' could not be found.")

with tab3:
    st.header("Committed Results & Metrics")
    if 'batch_results' in st.session_state and st.session_state.batch_results:
        df_results = pd.DataFrame(st.session_state.batch_results)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Documents", len(df_results))
        col2.metric("Avg Entities Found", f"{df_results['Entities Found'].mean():.2f}")
        col3.metric("Avg Similarity", f"{df_results['Similarity Score'].mean():.4f}")
        col4.metric("Best Similarity", f"{df_results['Similarity Score'].max():.4f}")
        
        st.subheader("Committed Results")
        st.dataframe(df_results, use_container_width=True)
        
        csv = df_results.to_csv(index=False)
        st.download_button(
            "📥 Download Committed Results as CSV",
            csv,
            "redaction_evaluation_results.csv",
            "text/csv"
        )
    else:
        st.info("No committed batch results available. Generate a preview and commit the batch to see results here.")

