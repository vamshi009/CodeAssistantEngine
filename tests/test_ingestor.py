import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from ingestor import CodebaseIngestor

def test_ingest_directory(tmp_path):
    # Create a sample Python file
    code = """
def foo():
    return 42
"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(code)
    ingestor = CodebaseIngestor()
    count = ingestor.ingest_directory(str(tmp_path))
    assert count == 1
    chunks = ingestor.get_chunks()
    assert len(chunks) >= 1
    assert 'foo' in chunks[0]['content']
