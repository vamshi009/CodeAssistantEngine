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

```
[User] ⇄ [FastAPI API] ⇄ [Ingestor] ⇄ [Vector Store] ⇄ [OpenAI LLM]
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
- **Chunking**: Simple line-based with overlap for context
- **Embedding Model**: OpenAI `text-embedding-3-small` (fast, accurate)
- **LLM**: OpenAI GPT-4 Turbo (high quality)
- **Vector DB**: Chroma (dev), Pinecone (prod)
- **Orchestration**: LangChain (optional, not required for MVP)
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

---

# Engineering Standards
- Type hints, docstrings, modularity
- Logging and error handling
- Separation of concerns
- Minimal dependencies

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

# Next Steps
- Add frontend
- Add tests
- Add Dockerfile
- Add cloud deployment scripts
