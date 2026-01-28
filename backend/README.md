# Code Documentation Assistant – Backend Design Choices

## Overview
This backend powers a conversational AI assistant that answers questions about a codebase using Retrieval-Augmented Generation (RAG). It is designed for clarity, modularity, and ease of extension, with a focus on maintainability and production readiness.

---

## Key Design Choices

### 1. **Tech Stack**
- **Python**: Chosen for its rich AI/ML ecosystem and rapid prototyping.
- **FastAPI**: Modern, async-ready web framework with automatic OpenAPI docs and type safety.
- **OpenAI GPT-4, Ollama & Local Quantized LLMs**: Flexible LLM backend, supporting cloud (OpenAI), local (Ollama), and local quantized models (e.g., GGML/GPTQ via llama-cpp-python) for privacy, cost control, and experimentation.
- **Chroma (dev) / Pinecone (prod)**: Chroma for local vector storage, Pinecone for scalable, managed vector DB.
- **Sentence-BERT/BERT (sentence-transformers)**: Flexible embedding backend for local, privacy-friendly, or cloud-based workflows.
- **Streamlit**: Simple, interactive UI for codebase upload, ingestion, and Q&A.
- **Pydantic**: For robust, type-safe configuration and environment management.

### 2. **Configuration Management**
- Centralized in `config.py` using Pydantic's `BaseSettings`.
- All sensitive keys (OpenAI, Pinecone) and tunable parameters (chunk size, logging, chunking strategy, embedding/LLM backend) are loaded from environment variables or `.env` file.
- The `chunking_strategy`, `embedding_backend`, and `llm_backend` settings allow you to choose between multiple strategies and providers. You can also specify a local quantized model path for running LLMs entirely offline.

### 3. **Code Ingestion, Chunking, and Cross-File Reasoning**
- The `ingestor.py` module recursively reads code files, ignoring common build and cache directories.
- **Python files are parsed using AST** to extract functions, classes, and docstrings as chunks, preserving code structure.
- **Cross-file relationships** are extracted:
  - Function calls and imports are stored as metadata in each chunk.
  - The ingestor builds indices mapping function/class names to their locations.
  - Related chunks (e.g., called functions, imported modules) can be retrieved for richer context.
- For other languages, line-based chunking is used as a fallback.
- Chunking parameters and strategy are configurable for experimentation and tuning.
- **Embedding backend is flexible:** You can use OpenAI embeddings (default) or local Sentence-BERT/BERT models (via `sentence-transformers`) for local development or privacy.

### 4. **Vector Store Abstraction**
- `vector_store.py` defines an abstract `VectorStore` interface.
- Two implementations: `ChromaVectorStore` (local, file-based) and `PineconeVectorStore` (cloud, scalable).
- Factory pattern (`get_vector_store()`) allows seamless switching via environment variable.
- This abstraction supports future extension to other vector DBs (e.g., FAISS, Weaviate).

### 5. **LLM & Embedding Utilities**
- `llm_utils.py` handles prompt construction, context management, and LLM API calls.
- Prompts are engineered to instruct the LLM to answer only from retrieved context, with a fallback to "I don't know" for safety.
- Embeddings use OpenAI's latest model for accuracy and speed, or local models for privacy/cost.
- LLM backend is flexible: supports OpenAI, Ollama (local models), and local quantized models (llama-cpp-python) for cost, privacy, and experimentation.

### 6. **Cross-File Context Expansion in Q&A**
- When a user asks a question, the system retrieves relevant code chunks and automatically expands the context to include related chunks (such as called functions/classes and imported modules) using the cross-file relationship metadata.
- The LLM receives a richer, more connected context, enabling better answers to questions that span multiple files or components.

### 7. **Streamlit UI**
- Simple, interactive UI for uploading codebases, ingesting directories, and asking questions.
- Shows answers and context chunks for transparency and debugging.

### 8. **Observability & Logging**
- `logger.py` provides structured, context-rich logging for all major operations.
- Log level and enablement are configurable.
- This supports debugging, monitoring, and future integration with observability platforms.

### 9. **Testing & Extensibility**
- Example tests are provided for ingestion and vector store logic.
- Code is modular, with clear separation of concerns, making it easy to extend (e.g., add new file types, chunking strategies, or LLMs).

### 10. **Containerization & Deployment**
- Dockerfile and docker-compose are included for reproducible, portable deployment.
- Environment variables and volumes are used for configuration and persistence.
- Ready for deployment to any cloud or on-prem environment.

---

## Example API Usage & Payloads

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

## Practical Future Extensions & Reasoning

### 1. **Support for More Languages**
- Extend AST-based chunking and relationship extraction to other languages (JavaScript/TypeScript, Java, Go, etc.) using language-specific parsers.
- Reasoning: Enables deeper code understanding and cross-file reasoning for polyglot codebases.

### 2. **Advanced Code Analysis**
- Build call graphs, dependency graphs, and class hierarchies for richer context expansion.
- Reasoning: Allows the assistant to answer architectural and flow questions, not just local function/class queries.

### 3. **Customizable Retrieval & Ranking**
- Add hybrid retrieval (semantic + relationship-based + keyword search).
- Reasoning: Improves answer quality, especially for large or poorly documented codebases.

### 4. **Authentication & Multi-user Support**
- Add user authentication, session management, and per-user codebase isolation.
- Reasoning: Makes the system production-ready for teams and organizations.

### 5. **Frontend Enhancements**
- Add code navigation, search, and visualization features to the Streamlit UI or migrate to a full-featured web frontend (React/Vue).
- Reasoning: Improves usability and adoption for non-technical users.

### 6. **Async & Scalable Ingestion**
- Use background workers (Celery, FastAPI tasks) for large codebases.
- Reasoning: Handles large projects efficiently and improves user experience.

### 7. **Observability & Monitoring**
- Integrate with tools like Prometheus, Grafana, or OpenTelemetry for metrics and tracing.
- Reasoning: Enables proactive maintenance and reliability in production.

### 8. **Model & Vector DB Flexibility**
- Add support for more LLMs (Anthropic, Google Gemini, local quantized models, etc.) and vector DBs (Weaviate, Qdrant).
- Reasoning: Future-proofs the system and allows cost/performance optimization, including fully offline and resource-efficient deployments.

### 9. **Automated Documentation Generation**
- Use LLMs to generate or update code documentation and architectural diagrams.
- Reasoning: Adds value for teams maintaining legacy or poorly documented codebases.

### 10. **Plugin/Extension System**
- Allow users to add custom analysis, retrieval, or visualization plugins.
- Reasoning: Makes the assistant adaptable to diverse workflows and requirements.

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

---

## Summary
This backend is designed for clarity, modularity, and production readiness, with a focus on maintainability and extensibility. All major design choices are documented and justified for future contributors and reviewers. The system is ready for practical extension in multiple directions, with clear reasoning for each.

![alt text](<Screenshot 2026-01-28 at 9.51.41 AM.png>)