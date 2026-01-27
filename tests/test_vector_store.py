import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from vector_store import ChromaVectorStore

def test_chroma_add_and_query(monkeypatch):
    # Monkeypatch chromadb for test
    class DummyCollection:
        def __init__(self):
            self.docs = []
        def add(self, ids, documents, metadatas):
            self.docs = list(zip(ids, documents, metadatas))
        def query(self, query_texts, n_results):
            return {
                'documents': [[doc for _, doc, _ in self.docs[:n_results]]],
                'metadatas': [[meta for _, _, meta in self.docs[:n_results]]],
                'distances': [[0.1]*n_results]
            }
    class DummyClient:
        def get_or_create_collection(self, name, metadata):
            return DummyCollection()
        def delete_collection(self, name):
            pass
    monkeypatch.setattr("vector_store.chromadb", type('chromadb', (), {}))
    monkeypatch.setattr("vector_store.chromadb.Client", lambda *a, **kw: DummyClient())
    monkeypatch.setattr("vector_store.chromadb.config", type('config', (), {'Settings': lambda **kw: {}}))
    store = ChromaVectorStore()
    chunks = [{
        'content': 'def foo():\n    return 42',
        'metadata': {'file_path': 'sample.py', 'chunk_index': 0}
    }]
    count = store.add_documents(chunks)
    assert count == 1
    results = store.query('foo', top_k=1)
    assert len(results) == 1
    assert 'foo' in results[0]['content']
