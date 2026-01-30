# Quick setup instructions for Code Documentation Assistant

About this project:

 - We have built a RAG system which is suitable for understanding the codebase (python) and answers the questions.
 - We have used  embedding models like sentence transformer for fast experimentation and protyping in compute minimal / local environments
 - We have use chromadb for local and added pinecone which can be used for large scale serving
 - We have AST based parsing which aids as metadata in prompt serving
 - We have used a local qunatized llama model for inference 
 - This is an initail setup we will be enhacing this with agent framwork to support question and answering of complex systems

 - Next Steps:
    - Query decomposition
    - Data Segregation (Metadata Index + Code Index)
    - Data Consolidation
    - Support for efficient retreival using async tool calls
    - explananbility in the systems
    - Prompt Versioning and Guardrails


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

# System Design Reasoning

## Vector Store Choices: Chroma (Local) & Pinecone (Production)
- **Chroma** is chosen for local development because it is lightweight, easy to set up, and requires no external cloud dependencies. This makes it ideal for rapid prototyping, testing, and individual developer workflows.
- **Pinecone** is used for production because it is a managed, scalable vector database that handles large-scale, concurrent queries and persistent storage. This enables the system to scale seamlessly for teams and organizations.
- **Flexibility:** The system can switch between Chroma and Pinecone via configuration, supporting both local and cloud deployments without code changes.

## Embedding Model Flexibility
- The system supports both **OpenAI embeddings** (cloud, high-quality, state-of-the-art) and **Sentence Transformers** (local, privacy-friendly, cost-effective).
- This allows users to choose between:
  - **OpenAI** for best-in-class embeddings when privacy and cost are less of a concern.
  - **Sentence Transformers** for running everything locally, ensuring data privacy and reducing costs.
- The embedding backend is configurable via environment variables or config files, making it easy to adapt to different requirements.

## LLM Flexibility: OpenAI, Ollama, Local Quantized Models
- The backend supports:
  - **OpenAI GPT-4** for high-quality, cloud-based completions.
  - **Ollama** for running open-source LLMs locally (e.g., Llama 2, Mistral) with minimal setup.
  - **Local quantized models** (via llama-cpp-python) for fully offline, resource-efficient inference.
- This flexibility allows users to optimize for cost, privacy, or performance as needed, and to experiment with new LLMs as they become available.

## Chunking & Cross-File Reasoning
- Chunking is configurable (line-based, AST, or auto) to best match the codebase structure and use case.
- Cross-file reasoning is enabled by extracting and storing function/class relationships, allowing the assistant to answer questions that span multiple files or modules.

## Modularity & Observability
- The system is highly modular, with clear separation of concerns (ingestion, vector store, LLM, UI, logging).
- Structured logging and error handling are built in, supporting debugging and future integration with observability platforms.

## Why These Choices?
- **Developer Experience:** Local-first tools (Chroma, Sentence Transformers) make it easy for developers to get started and iterate quickly.
- **Scalability:** Pinecone and OpenAI enable seamless scaling to production workloads.
- **Flexibility:** Configurable backends for embeddings and LLMs allow the system to adapt to different privacy, cost, and performance needs.
- **Maintainability:** Modular design and clear configuration make the system easy to extend and maintain.

System Design:
![alt text](<Screenshot 2026-01-25 at 8.48.15 PM.png>)


Working Demo:

Ask request:

![alt text](<Screenshot 2026-01-27 at 10.15.09 PM.png>)

Ingest Request:

![alt text](<Screenshot 2026-01-27 at 11.01.59 PM.png>)


![alt text](<Screenshot 2026-01-28 at 9.51.41 AM.png>)