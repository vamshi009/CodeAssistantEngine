"""
Vector store and retrieval module
Handles embeddings and semantic search
"""
from typing import List, Dict, Any, Optional
from backend.logger import get_logger
from backend.config import settings
from backend.llm_utils import get_embedding
import os
from chromadb import Client

logger = get_logger(__name__)


class VectorStore:
    """
    Abstract vector store interface
    Implementations can use Pinecone, Chroma, FAISS, etc.
    """
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Add documents to vector store"""
        raise NotImplementedError
    
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query"""
        raise NotImplementedError
    
    def delete_all(self):
        """Clear the vector store"""
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """
    Chroma-based vector store for local development
    Lightweight, no external dependencies needed
    """
    
    def __init__(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            raise ImportError(
                "chromadb not installed. Install with: pip install chromadb"
            )
        
        self.chroma = chromadb
        
        # Initialize Chroma with persistent storage
        chroma_settings = ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_data",
            anonymized_telemetry=False,
        )
        
        self.client = chromadb.Client(chroma_settings)
        self.collection = None
        logger.info("Initialized ChromaVectorStore")
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Add chunks to Chroma"""
        if not chunks:
            logger.warning("No chunks to add")
            return 0
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="code_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare documents for insertion
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            ids.append(f"chunk_{i}")
            documents.append(chunk['content'])
            metadatas.append(chunk.get('metadata', {}))
            # Compute embedding using the configured backend
            embeddings.append(get_embedding(chunk['content']))
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector store")
        return len(chunks)
    
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the vector store"""
        if not self.collection:
            logger.warning("Collection not initialized, returning empty results")
            return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results
        retrieved_docs = []
        if results and results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                retrieved_docs.append({
                    'content': doc,
                    'metadata': metadata,
                    'similarity_score': 1 - distance  # Convert distance to similarity
                })
        
        logger.debug(f"Retrieved {len(retrieved_docs)} documents", query=query)
        return retrieved_docs
    
    def delete_all(self):
        """Clear all collections"""
        try:
            self.client.delete_collection(name="code_docs")
            self.collection = None
            logger.info("Cleared vector store")
        except Exception as e:
            logger.warning(f"Error clearing vector store: {e}")


class PineconeVectorStore(VectorStore):
    """
    Pinecone-based vector store for production
    Scalable, serverless vector database
    """
    
    def __init__(self):
        try:
            from pinecone import Pinecone
        except ImportError:
            raise ImportError(
                "pinecone-client not installed. Install with: pip install pinecone-client"
            )
        
        api_key = settings.pinecone_api_key
        if not api_key:
            raise ValueError("PINECONE_API_KEY not set in environment")
        
        self.pc = Pinecone(api_key=api_key)
        self.index_name = settings.pinecone_index_name
        
        logger.info(f"Initialized PineconeVectorStore with index: {self.index_name}")
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Add chunks to Pinecone"""
        try:
            from langchain.embeddings.openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError("langchain not installed")
        
        if not chunks:
            return 0
        
        # Would implement Pinecone integration here
        # For now, logging placeholder
        logger.info(f"Would add {len(chunks)} chunks to Pinecone")
        return len(chunks)
    
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query Pinecone"""
        # Placeholder for Pinecone query
        logger.info(f"Would query Pinecone: {query}")
        return []
    
    def delete_all(self):
        """Clear index"""
        logger.info("Would clear Pinecone index")


def get_vector_store_2() -> VectorStore:
    """Factory function to get appropriate vector store"""
    # For development, use Chroma (no external service needed)
    # For production, use Pinecone
    
    vector_store_type = os.getenv('VECTOR_STORE', 'chroma').lower()
    
    if vector_store_type == 'pinecone':
        return PineconeVectorStore()
    else:
        return ChromaVectorStore()

def get_vector_store():
    """Factory to get or create a ChromaDB collection for vector storage."""
    client = Client()
    # Use get_or_create_collection to avoid errors if collection doesn't exist
    collection = client.get_or_create_collection(name="chroma_docs")
    return collection

# Example usage for adding and retrieving documents:
def add_document_to_chroma(doc_id: str, content: str):
    collection = get_vector_store()
    collection.add(ids=[doc_id], documents=[content])

def get_document_from_chroma(doc_id: str):
    collection = get_vector_store()
    result = collection.get(ids=[doc_id])
    return result["documents"]
