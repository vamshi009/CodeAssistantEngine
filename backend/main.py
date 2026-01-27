"""
Main FastAPI app for Code Documentation Assistant
Handles endpoints for code ingestion and Q&A
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.ingestor import CodebaseIngestor, add_chunks_to_chroma
from backend.vector_store import get_vector_store
from backend.llm_utils import build_prompt, call_llm
from backend.logger import get_logger
import os
import shutil

logger = get_logger(__name__)

app = FastAPI(title=settings.api_title, version=settings.api_version)

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploaded_code"

vector_store = get_vector_store()


@app.post("/ingest")
def ingest_codebase(directory: str = Form(...)):
    """
    Ingest a codebase from a local directory
    """
    try:
        ingestor = CodebaseIngestor()
        file_count = ingestor.ingest_directory(directory)
        chunks = ingestor.get_chunks()
        #vector_store = get_vector_store()
        add_chunks_to_chroma(chunks, vector_store=vector_store)
        return {"status": "success", "files_processed": file_count, "chunks": len(chunks)}
    except Exception as e:
        logger.error("Ingestion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
def upload_codebase(file: UploadFile = File(...)):
    """
    Upload a zipped codebase and ingest it
    """
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        # Unzip and ingest
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_DIR)
        ingestor = CodebaseIngestor()
        file_count = ingestor.ingest_directory(UPLOAD_DIR)
        chunks = ingestor.get_chunks()
        add_chunks_to_chroma(chunks, vector_store=vector_store) 
        return {"status": "success", "files_processed": file_count, "chunks": len(chunks)}
    except Exception as e:
        logger.error("Upload/ingest failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_question(query: str = Form(...)):
    """
    Answer a question about the ingested codebase, including cross-file context
    """
    try:
        ingestor = CodebaseIngestor()  # Should be persistent/shared in production
        #print the metadata of the vector store / collection being used here
        print("Vector Store Metadata:", vector_store.metadata)
        print("Chroma Collection Metadata at ask:", vector_store.get())
        n_results = settings.top_k_documents
        # ChromaDB returns a dict with keys: "ids", "documents", "metadatas", etc.
        result = vector_store.query(query_texts=[query], n_results=n_results)
        expanded_context = []
        for i in range(len(result["ids"][0])):
            chunk = {
                "content": result["documents"][0][i],
                "metadata": result["metadatas"][0][i]
            }
            expanded_context.append(chunk)
        print("Retrieved context chunks:")
        for c in expanded_context:
            print(f"File: {c['metadata'].get('file_path')}, Chunk: {c['metadata'].get('chunk_index')}, Content: {c['content'][:200]}")
        # Expand context with related chunks for cross-file reasoning
        for chunk in expanded_context.copy():
            related = ingestor.get_related_chunks(chunk)
            expanded_context.extend(related)
        # Remove duplicates
        seen = set()
        unique_context = []
        for c in expanded_context:
            key = (c['metadata'].get('file_path'), c['metadata'].get('chunk_index'))
            if key not in seen:
                unique_context.append(c)
                seen.add(key)
        # Limit the number of context tokens to avoid exceeding LLM context window
        max_tokens = 128  # or set to your LLM's context window limit
        current_tokens = 0
        limited_context = []
        for c in unique_context:
            # Estimate tokens (roughly 4 chars per token for English)
            chunk_tokens = max(1, len(c['content']) // 4)
            if current_tokens + chunk_tokens > max_tokens:
                break
            limited_context.append(c)
            current_tokens += chunk_tokens
        prompt = build_prompt(query, limited_context)
        print("Constructed Prompt:", prompt)  # Debug print
        print("Retrieved context chunks:", limited_context)
        print("results from vector store:", result)
        answer = call_llm(prompt)
        print("LLM Answer:", answer)  # Debug print
        return {"answer": answer, "context": limited_context}
    except Exception as e:
        logger.error("Q&A failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Code Documentation Assistant API is running."}

