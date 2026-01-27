# Code Documentation Assistant – Backend Flow & Responsibility Document

This document explains the flow of the backend system and the responsibility of each main file and function.

---

## 1. `main.py` (FastAPI Application Entrypoint)
- **Purpose:** Exposes API endpoints for code ingestion, upload, and Q&A.
- **Key Functions:**
  - `ingest_codebase`: Ingests a local directory.
  - `upload_codebase`: Accepts a zipped codebase and ingests it.
  - `ask_question`: Answers user questions using RAG, including cross-file context expansion.
- **Flow:**
  - Receives user requests.
  - Calls `CodebaseIngestor` for ingestion.
  - Uses `vector_store` for semantic search.
  - Expands context with related chunks (cross-file reasoning).
  - Builds prompt and calls LLM for answer.

---

## 2. `ingestor.py` (Code Ingestion & Chunking)
- **Purpose:** Reads code files, chunks them, and extracts relationships for cross-file reasoning.
- **Key Classes/Functions:**
  - `CodeDocument`: Represents a code file; responsible for chunking (by AST for Python, by lines for others).
    - `chunk()`: Main chunking method, configurable by strategy.
    - `_chunk_python()`: Uses AST to extract functions, classes, docstrings, and relationships (calls, imports).
    - `_chunk_by_lines()`: Fallback for non-Python files.
  - `CodebaseIngestor`: Manages ingestion of entire codebases.
    - `ingest_directory()`: Recursively ingests all supported files in a directory.
    - `ingest_file()`: Ingests a single file.
    - `get_related_chunks()`: Finds related chunks (called functions/classes, imported modules) for cross-file reasoning.
    - `function_index`/`class_index`: Maps function/class names to their locations for fast lookup.

---

## 3. `vector_store.py` (Vector Database Abstraction)
- **Purpose:** Stores and retrieves code/document chunks for semantic search.
- **Key Classes/Functions:**
  - `VectorStore`: Abstract base class.
  - `ChromaVectorStore`: Local, file-based vector DB for development.
  - `PineconeVectorStore`: Cloud, scalable vector DB for production.
  - `get_vector_store()`: Factory to select the appropriate backend.

---

## 4. `llm_utils.py` (LLM & Embedding Utilities)
- **Purpose:** Handles prompt construction, context management, and LLM API calls.
- **Key Functions:**
  - `get_embedding`: Gets embeddings for text chunks using OpenAI or local Sentence-BERT/BERT (configurable).
  - `build_prompt`: Constructs the prompt for the LLM, including all relevant context.
  - `call_llm`: Calls the configured LLM backend (OpenAI, Ollama, or local quantized) and returns the answer.

---

## 5. `config.py` (Configuration)
- **Purpose:** Centralizes all configuration using Pydantic settings.
- **Key Class:**
  - `Settings`: Loads API keys, chunking parameters, logging, embedding/LLM backend, local quantized model path, and other settings from environment or `.env` file.

---

## 6. `logger.py` (Logging & Observability)
- **Purpose:** Provides structured logging for debugging and observability.
- **Key Class/Function:**
  - `StructuredLogger`: Custom logger for structured, context-rich logs.
  - `get_logger`: Factory for logger instances.

---

## 7. `streamlit_app.py` (UI)
- **Purpose:** Provides a simple, interactive UI for uploading codebases, ingesting directories, and asking questions.
- **Key Features:**
  - Upload zipped codebase or ingest directory.
  - Ask questions and view answers/context chunks interactively.

---

## 8. `tests/` (Testing)
- **Purpose:** Contains unit tests for ingestion and vector store logic.
- **Key Files:**
  - `test_ingestor.py`: Tests code ingestion and chunking.
  - `test_vector_store.py`: Tests vector store operations.

---

## Flow Summary
1. **User** sends a codebase or question via API or Streamlit UI.
2. **main.py** routes the request.
3. **ingestor.py** reads and chunks code, extracting relationships (calls, imports) for cross-file reasoning.
4. **vector_store.py** stores/retrieves chunks for semantic search, using flexible embedding backend.
5. **main.py** expands context with related chunks (cross-file reasoning).
6. **llm_utils.py** builds prompt and calls the configured LLM backend (OpenAI, Ollama, or local quantized).
7. **main.py** returns the answer to the user or UI.

---

This modular design makes it easy to extend, test, and maintain the system, with flexibility for local/cloud embeddings, LLMs, and UI.
