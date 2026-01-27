"""
OpenAI LLM and embedding utilities
Handles prompt construction, context management, and LLM calls
"""
from typing import List, Dict, Any
from backend.config import settings
from backend.logger import get_logger
import os
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import openai

logger = get_logger(__name__)

SENTENCE_TRANSFORMERS_DIR = os.path.join(os.path.dirname(__file__), "models", "sentence_transformers")
os.makedirs(SENTENCE_TRANSFORMERS_DIR, exist_ok=True)

def get_sentence_transformers_model(model_name: str):
    """Download and cache the sentence-transformers model locally, then load from local dir."""
    local_model_path = os.path.join(SENTENCE_TRANSFORMERS_DIR, model_name)
    if not os.path.exists(local_model_path):
        # Download and save model to local path
        model = SentenceTransformer(model_name)
        model.save(local_model_path)
    # Always load from local path
    return SentenceTransformer(local_model_path)


def get_embedding(text: str) -> list:
    """Get embedding for a text chunk using the configured backend (OpenAI or Sentence-BERT)."""
    backend = getattr(settings, 'embedding_backend', 'openai')
    if backend == 'openai':
        try:
            import openai
            response = openai.embeddings.create(
                input=[text],
                model=settings.openai_embedding_model,
                api_key=settings.openai_api_key
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error("OpenAI embedding error", error=str(e))
            raise
    elif backend == 'sentence-transformers':
        try:
            model_name = getattr(settings, 'sentence_transformers_model', 'all-MiniLM-L6-v2')
            if not hasattr(get_embedding, '_model'):
                get_embedding._model = get_sentence_transformers_model(model_name)
            embedding = get_embedding._model.encode([text])[0].tolist()
            return embedding
        except Exception as e:
            logger.error("Sentence-BERT embedding error", error=str(e))
            raise
    else:
        raise ValueError(f"Unknown embedding backend: {backend}")


def build_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Construct prompt for LLM using retrieved context"""
    context_blocks = []
    for chunk in retrieved_chunks:
        meta = chunk.get('metadata', {})
        file_path = meta.get('file_path', 'unknown')
        chunk_index = meta.get('chunk_index', 0)
        context_blocks.append(f"File: {file_path} (chunk {chunk_index})\n{chunk['content']}\n---")
    context_str = '\n'.join(context_blocks)

    print("Context for prompt construction:", context_str)  # Debug print
    prompt = f"""
You are a helpful code documentation assistant. Use the following code context to answer the user's question. If the answer is not in the context, say you don't know.

Context:
{context_str}

User question: {query}

Answer as clearly and concisely as possible:
"""
    return prompt


def call_llm(prompt: str) -> str:
    """Call the configured LLM backend (OpenAI, Ollama, or local quantized) with prompt and return response."""
    backend = getattr(settings, 'llm_backend', 'openai')
    if backend == 'openai':
        try:
            response = openai.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=settings.openai_api_key,
                max_tokens=512,
                temperature=0.2
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            logger.error("OpenAI LLM error", error=str(e))
            raise
    elif backend == 'ollama':
        try:
            import requests
            ollama_url = "http://localhost:11434/api/generate"
            model = getattr(settings, 'ollama_model', 'llama2')
            payload = {"model": model, "prompt": prompt, "stream": False}
            response = requests.post(ollama_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "")
            return answer.strip()
        except Exception as e:
            logger.error("Ollama LLM error", error=str(e))
            raise
    elif backend == 'local-quantized':
        try:
            model_path = getattr(settings, 'local_quantized_model_path', None)
            if not model_path or not os.path.exists(model_path):
                raise ValueError(f"Local quantized model path not set or does not exist: {model_path}")
            if not hasattr(call_llm, '_llm'):
                call_llm._llm = Llama(model_path=model_path)
            output = call_llm._llm(prompt=prompt, max_tokens=512, temperature=0.2)
            answer = output["choices"][0]["text"] if "choices" in output else output.get("text", "")
            return answer.strip()
        except Exception as e:
            logger.error("Local quantized LLM error", error=str(e))
            raise
    else:
        raise ValueError(f"Unknown LLM backend: {backend}")
