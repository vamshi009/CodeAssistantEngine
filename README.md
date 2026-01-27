# Quick setup instructions for Code Documentation Assistant

## Prerequisites
- Python 3.9+
- (Optional) Pinecone API key for production vector DB
- OpenAI API key

## 1. Clone the repository
```zsh
git clone <your-repo-url>
cd CodeAssistant
```

## 2. Create and activate a virtual environment
```zsh
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies
```zsh
pip install -r requirements.txt
```

## 4. Set environment variables
Create a `.env` file in the `backend/` directory with:
```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=your-pinecone-key (optional)
```

## 5. Run the backend API
```zsh
cd backend
uvicorn main:app --reload
```

## 6. Usage
- Use `/ingest` to ingest a local codebase directory
- Use `/upload` to upload a zipped codebase
- Use `/ask` to ask questions about the codebase

---

# Architecture Overview

- **FastAPI** backend for API endpoints
- **Ingestor** module for code parsing and chunking
- **Vector Store** (Chroma for dev, Pinecone for prod) for semantic search
- **OpenAI LLM** for answering questions
- **Logger** for observability
- **Streamlit UI** for interactive usage
- **Flexible Embedding/LLM Backend**: OpenAI, Ollama, local quantized models
- **Cross-file reasoning**: Expands context with related chunks/functions/classes

```
[User] ⇄ [Streamlit UI/API] ⇄ [FastAPI Backend] ⇄ [Ingestor] ⇄ [Vector Store] ⇄ [LLM]
```

---

# Productionization & Scalability
- Containerize with Docker
- Use managed vector DB (Pinecone)
- Deploy FastAPI on AWS ECS, GCP Cloud Run, or Azure App Service
- Add authentication, rate limiting, and monitoring
- Use cloud storage for uploads

---

# RAG/LLM Approach & Decisions
- **Chunking**: Configurable (line-based, AST, auto), overlap for context
- **Embedding Model**: OpenAI `text-embedding-3-small` or local Sentence-BERT/BERT
- **LLM**: OpenAI GPT-4 Turbo, Ollama, or local quantized (llama-cpp-python)
- **Vector DB**: Chroma (dev), Pinecone (prod)
- **Orchestration**: LangChain (optional), future: LangGraph
- **Prompt**: Context blocks + user query, instruct LLM to answer only from context
- **Guardrails**: LLM instructed to say "I don't know" if answer not in context
- **Quality**: Top-k retrieval, chunk overlap, logging
- **Observability**: Structured logs, error handling

---

# Key Technical Decisions
- Python for rapid prototyping and ecosystem
- FastAPI for async, modern API
- Chroma for local dev, Pinecone for scale
- Modular code for maintainability
- Simple, testable interfaces
- Flexible backend for embeddings and LLMs
- Cross-file reasoning for deeper code understanding

---

# Engineering Standards
- Type hints, docstrings, modularity
- Logging and error handling
- Separation of concerns
- Minimal dependencies
- Structured configuration with Pydantic

---

# Use of AI Coding Tools
- Used GitHub Copilot for boilerplate and code suggestions
- All architectural and README content written and reviewed manually
- AI tools used for code, not for README or design decisions

---

# What I'd Do Differently With More Time
- Add frontend UI (Vue/React)
- Add authentication and user management
- Add async background ingestion
- Add more advanced chunking (AST, function-level)
- Add tests and CI/CD
- Add usage analytics and monitoring
- Support for more LLMs and vector DBs

---

# Example API Usage & Payloads

### 1. Ingest Directory
**Endpoint:** `/ingest`  
**Method:** POST  
**Headers:** `Content-Type: application/x-www-form-urlencoded`
**Payload:**
```
directory=/path/to/codebase
```
**Curl Example:**
```
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "directory=/path/to/codebase"
```

---

### 2. Upload Zipped Codebase
**Endpoint:** `/upload`  
**Method:** POST  
**Headers:** `Content-Type: multipart/form-data`
**Payload:**
- `file`: zipped codebase file
**Curl Example:**
```
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/codebase.zip"
```

---

### 3. Ask a Question
**Endpoint:** `/ask`  
**Method:** POST  
**Headers:** `Content-Type: application/x-www-form-urlencoded`
**Payload:**
```
query=Where is the main API endpoint implemented?
```
**Curl Example:**
```
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=Where is the main API endpoint implemented?"
```

---

### Response Format
All endpoints return JSON. For `/ask`, the response includes:
- `answer`: LLM-generated answer
- `context`: List of code/document chunks used for context

---

### Notes
- Ensure the backend is running before making requests.
- Adjust URLs and payloads as needed for your environment.

---

# Practical Future Extensions & Reasoning

### 1. Support for More Languages
- Extend AST-based chunking and relationship extraction to other languages (JavaScript/TypeScript, Java, Go, etc.) using language-specific parsers.
- Reasoning: Enables deeper code understanding and cross-file reasoning for polyglot codebases.

### 2. Advanced Code Analysis
- Build call graphs, dependency graphs, and class hierarchies for richer context expansion.
- Reasoning: Allows the assistant to answer architectural and flow questions, not just local function/class queries.

### 3. Customizable Retrieval & Ranking
- Add hybrid retrieval (semantic + relationship-based + keyword search).
- Reasoning: Improves answer quality, especially for large or poorly documented codebases.

### 4. Authentication & Multi-user Support
- Add user authentication, session management, and per-user codebase isolation.
- Reasoning: Makes the system production-ready for teams and organizations.

---

## Next Steps & Future Enhancements

1. **Integrate LangGraph or Similar Orchestration Framework**
   - Use LangGraph or comparable frameworks to control and enhance query flow, enabling more advanced context management and multi-step reasoning.
   - Implement actor-critic or agent-based setups to refine context selection and improve answer precision.

2. **Efficient Retrieval Tools**
   - Explore and integrate more efficient retrieval libraries (e.g., FAISS, Milvus, Weaviate) for faster and more scalable vector search.
   - Experiment with hybrid retrieval (semantic + keyword + relationship-based) for improved relevance.

3. **Explanability & Query Flow Visualization**
   - Add features to visualize the flow of a user query, showing which chunks and relationships were used in the answer.
   - Provide UI and API endpoints for users to inspect context, retrieval steps, and reasoning paths.

4. **Evaluation Framework**
   - Build a framework for evaluating system performance, including metrics for retrieval accuracy, answer quality, and latency.
   - Support automated and manual test cases, and integrate with CI/CD for continuous evaluation.

5. **Prompt Versioning**
   - Implement prompt versioning to track changes and improvements in prompt engineering.
   - Allow rollback, comparison, and A/B testing of different prompt versions for quality control.

---

These steps will make the system more robust, explainable, and production-ready, while supporting ongoing research and improvement in codebase Q&A.
