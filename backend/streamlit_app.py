import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Code Documentation Assistant", layout="wide")
st.title("🧑‍💻 Code Documentation Assistant")

st.sidebar.header("Upload or Ingest Codebase")

with st.sidebar:
    upload_mode = st.radio("Choose upload mode", ["Upload Zip", "Ingest Directory"], index=0)
    if upload_mode == "Upload Zip":
        uploaded_file = st.file_uploader("Upload a zipped codebase", type=["zip"])
        if uploaded_file and st.button("Upload & Ingest"):
            with st.spinner("Uploading and ingesting codebase..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/zip")}
                resp = requests.post(f"{API_URL}/upload", files=files)
                if resp.ok:
                    st.success(f"Ingested {resp.json().get('files_processed', 0)} files.")
                else:
                    st.error(f"Error: {resp.text}")
    else:
        dir_path = st.text_input("Directory path on server")
        if st.button("Ingest Directory") and dir_path:
            with st.spinner("Ingesting directory..."):
                resp = requests.post(f"{API_URL}/ingest", data={"directory": dir_path})
                if resp.ok:
                    st.success(f"Ingested {resp.json().get('files_processed', 0)} files.")
                else:
                    st.error(f"Error: {resp.text}")

st.header("Ask a Question about the Codebase")
query = st.text_area("Enter your question", height=80)
if st.button("Ask") and query:
    with st.spinner("Getting answer..."):
        resp = requests.post(f"{API_URL}/ask", data={"query": query})
        if resp.ok:
            answer = resp.json().get("answer", "No answer returned.")
            st.markdown(f"**Answer:**\n{answer}")
            with st.expander("Show context chunks"):
                for i, chunk in enumerate(resp.json().get("context", [])):
                    meta = chunk.get("metadata", {})
                    st.code(chunk["content"], language=meta.get("file_type", "text"))
        else:
            st.error(f"Error: {resp.text}")

st.markdown("---")
st.caption("Code Documentation Assistant | Powered by RAG, OpenAI/Ollama, and Streamlit")
