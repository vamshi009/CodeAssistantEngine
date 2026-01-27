"""
Code ingestion and processing module
Handles reading code files, parsing, and chunking
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from backend.logger import get_logger
from backend.config import settings
import ast
from collections import defaultdict
from charset_normalizer import from_bytes
from chromadb import Client


logger = get_logger(__name__)


class CodeDocument:
    """Represents a code document with metadata"""
    
    def __init__(self, path: str, content: str, file_type: str):
        self.path = path
        self.content = content
        self.file_type = file_type
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def chunk(self) -> List[Dict[str, Any]]:
        """
        Chunk document into smaller pieces for embedding
        Strategy is configurable: 'ast' (default for .py), 'lines', or 'auto'.
        """
        strategy = getattr(settings, 'chunking_strategy', 'auto')
        if strategy == 'lines':
            return self._chunk_by_lines()
        elif strategy == 'ast':
            if self.file_type == '.py':
                return self._chunk_python()
            else:
                return self._chunk_by_lines()
        else:  # 'auto' or fallback
            if self.file_type == '.py':
                return self._chunk_python()
            else:
                return self._chunk_by_lines()

    def _chunk_python(self) -> List[Dict[str, Any]]:
        """Chunk Python code by function, class, and module docstring using AST. Also extract function calls and imports for cross-file reasoning."""
        chunks = []
        try:
            tree = ast.parse(self.content)
            module_docstring = ast.get_docstring(tree)
            imports = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for n in node.names:
                            imports.append(n.name)
                    elif isinstance(node, ast.ImportFrom):
                        imports.append(node.module)
            if module_docstring:
                chunks.append({
                    'content': f"# Module docstring\n{module_docstring}",
                    'metadata': {
                        'file_path': self.path,
                        'file_type': self.file_type,
                        'chunk_type': 'module_docstring',
                        'chunk_index': len(chunks),
                        'imports': imports
                    }
                })
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno - 1
                    end_line = getattr(node, 'end_lineno', None)
                    if end_line is None:
                        siblings = list(ast.iter_child_nodes(tree))
                        idx = siblings.index(node)
                        if idx + 1 < len(siblings):
                            end_line = siblings[idx + 1].lineno - 1
                        else:
                            end_line = len(self.content.splitlines())
                    code_lines = self.content.splitlines()[start_line:end_line]
                    code_chunk = '\n'.join(code_lines)
                    chunk_type = 'class' if isinstance(node, ast.ClassDef) else 'function'
                    name = getattr(node, 'name', 'unknown')
                    # Extract function calls within this node
                    calls = []
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            if isinstance(subnode.func, ast.Name):
                                calls.append(subnode.func.id)
                            elif isinstance(subnode.func, ast.Attribute):
                                calls.append(subnode.func.attr)
                    chunks.append({
                        'content': code_chunk,
                        'metadata': {
                            'file_path': self.path,
                            'file_type': self.file_type,
                            'chunk_type': chunk_type,
                            'name': name,
                            'chunk_index': len(chunks),
                            'calls': list(set(calls)),
                            'imports': imports
                        }
                    })
        except Exception as e:
            logger.warning(f"AST chunking failed, falling back to line-based chunking", file=self.path, error=str(e))
            return self._chunk_by_lines()
        return chunks if chunks else self._chunk_by_lines()

    def _chunk_by_lines(self) -> List[Dict[str, Any]]:
        """Fallback: chunk by lines with overlap (original logic)."""
        chunks = []
        lines = self.content.split('\n')
        chunk_lines = []
        for i, line in enumerate(lines):
            chunk_lines.append(line)
            chunk_text = '\n'.join(chunk_lines)
            if len(chunk_text) > self.chunk_size:
                overlap_lines = max(len(chunk_lines) - self.chunk_overlap // 50, 0)
                chunk_text = '\n'.join(chunk_lines)
                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        'file_path': self.path,
                        'file_type': self.file_type,
                        'chunk_index': len(chunks),
                        'total_lines': len(lines),
                    }
                })
                chunk_lines = chunk_lines[overlap_lines:]
        if chunk_lines:
            chunk_text = '\n'.join(chunk_lines)
            chunks.append({
                'content': chunk_text,
                'metadata': {
                    'file_path': self.path,
                    'file_type': self.file_type,
                    'chunk_index': len(chunks),
                    'total_lines': len(lines),
                }
            })
        logger.info(f"Chunked file into {len(chunks)} pieces", file=self.path, chunks=len(chunks))
        return chunks


class CodebaseIngestor:
    """Ingests and processes codebases"""
    
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', 
        '.h', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.md',
        '.txt', '.sh', '.bash'
    }
    
    IGNORE_DIRS = {
        '__pycache__', '.git', 'node_modules', '.venv', 'venv',
        'dist', 'build', '.pytest_cache', 'htmlcov'
    }
    
    def __init__(self):
        self.documents: List[CodeDocument] = []
        self.chunks: List[Dict[str, Any]] = []
        self.function_index = defaultdict(list)  # name -> list of (file_path, chunk_index)
        self.class_index = defaultdict(list)     # name -> list of (file_path, chunk_index)
    
    def ingest_directory(self, directory_path: str) -> int:
        """
        Recursively ingest all code files from a directory
        Returns count of documents processed
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            raise ValueError(f"Directory not found: {directory_path}")
        
        logger.info(f"Starting ingestion of directory", path=str(directory_path))
        
        for file_path in directory_path.rglob('*'):
            # Skip directories and ignored paths
            if file_path.is_dir():
                if file_path.name in self.IGNORE_DIRS:
                    continue
                continue
            
            # Skip unsupported file types
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            try:
                self._ingest_file(file_path)
            except Exception as e:
                logger.error(f"Failed to ingest file", 
                           file=str(file_path), error=str(e))
                continue
        
        # Chunk all documents
        for doc in self.documents:
            doc_chunks = doc.chunk()
            self.chunks.extend(doc_chunks)
            # Build function/class index for cross-file lookup
            for chunk in doc_chunks:
                meta = chunk.get('metadata', {})
                if meta.get('chunk_type') == 'function' and meta.get('name'):
                    self.function_index[meta['name']].append((meta['file_path'], meta['chunk_index']))
                if meta.get('chunk_type') == 'class' and meta.get('name'):
                    self.class_index[meta['name']].append((meta['file_path'], meta['chunk_index']))
        
        logger.info(f"Ingestion complete", 
                   files_processed=len(self.documents),
                   total_chunks=len(self.chunks))
        
        return len(self.documents)
    
    def ingest_file(self, file_path: str) -> int:
        """Ingest a single file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        self._ingest_file(file_path)
        
        # Chunk the document
        for doc in self.documents:
            self.chunks.extend(doc.chunk())
        
        return len(self.documents)
    
    def _ingest_file(self, file_path: Path):
        """Internal method to read and parse a file"""
        try:
            # Detect encoding using charset-normalizer
            #from charset_normalizer import from_bytes
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = from_bytes(raw_data).best()
                encoding = result.encoding if result else 'utf-8'
            # Read file content
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            file_type = file_path.suffix.lower()
            relative_path = str(file_path)
            doc = CodeDocument(relative_path, content, file_type)
            self.documents.append(doc)
            logger.debug(f"Ingested file", 
                        file=relative_path, 
                        size_bytes=len(content))
        except Exception as e:
            logger.error(f"Error reading file", 
                       file=str(file_path), 
                       error=str(e))
            raise
    
    def get_chunks(self) -> List[Dict[str, Any]]:
        """Get all chunks"""
        return self.chunks
    
    def get_documents(self) -> List[CodeDocument]:
        """Get all documents"""
        return self.documents

    def get_related_chunks(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Given a chunk, find related chunks (e.g., called functions/classes) for cross-file reasoning."""
        related = []
        meta = chunk.get('metadata', {})
        # Add called functions
        for func in meta.get('calls', []):
            for file_path, chunk_idx in self.function_index.get(func, []):
                for c in self.chunks:
                    m = c.get('metadata', {})
                    if m.get('file_path') == file_path and m.get('chunk_index') == chunk_idx:
                        related.append(c)
        # Add imported modules' docstrings if available
        for mod in meta.get('imports', []):
            for c in self.chunks:
                m = c.get('metadata', {})
                if m.get('chunk_type') == 'module_docstring' and mod and mod in m.get('file_path', ''):
                    related.append(c)
        return related


def add_chunks_to_chroma(chunks, vector_store=None):
    if(vector_store is not None):
        collection = vector_store
    else:
        client = Client()
        collection = client.get_or_create_collection(name="chroma_docs")
    ids = [f"{chunk['metadata']['file_path']}:{chunk['metadata']['chunk_index']}" for chunk in chunks]
    documents = [chunk['content'] for chunk in chunks]
    # Sanitize metadata: convert lists to comma-separated strings
    def sanitize_metadata(meta):
        return {k: (",".join(v) if isinstance(v, list) else v) for k, v in meta.items()}
    metadatas = [sanitize_metadata(chunk['metadata']) for chunk in chunks]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    #print colection metadata for debugging
    print("Chroma Collection Metadata:", collection.count)
    print("collectin info:", collection.get())
