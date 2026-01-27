# Code Documentation Assistant – Architecture Diagram

```mermaid
graph TD
    A[User] -- Asks Question / Uploads Codebase --> B[FastAPI Backend]
    B -- Ingests Codebase --> C[Ingestor]
    C -- Chunks Code & Extracts Relationships --> D[Vector Store (Chroma/Pinecone)]
    D -- Stores & Retrieves Chunks --> B
    B -- Builds Prompt with Context (including cross-file) --> E[OpenAI LLM]
    E -- Returns Answer --> B
    B -- Returns Answer & Context --> A
    C -- Extracts Function Calls & Imports --> F[Cross-file Relationship Index]
    B -- Expands Context with Related Chunks --> F
```

**Legend:**
- **User**: Interacts via API (or UI)
- **FastAPI Backend**: Main API server
- **Ingestor**: Reads, chunks, and analyzes code
- **Vector Store**: Stores and retrieves code/document chunks (Chroma for dev, Pinecone for prod)
- **Cross-file Relationship Index**: Maps functions/classes/imports for cross-file reasoning
- **OpenAI LLM**: Generates answers using retrieved and expanded context
