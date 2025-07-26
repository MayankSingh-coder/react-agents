"""Vector-based memory for semantic similarity search."""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
import time


@dataclass
class VectorEntry:
    """A vector memory entry."""
    id: str
    content: Any
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: float
    importance: float = 0.5


class SimpleEmbedding:
    """Simple embedding implementation using hash-based approach."""
    
    def __init__(self, dim: int = 256):
        self.dim = dim
    
    def embed(self, text: str) -> np.ndarray:
        """Create embedding for text using hash-based approach."""
        # Create multiple hash values for better distribution
        embeddings = []
        
        for i in range(4):  # Use 4 different hash functions
            hash_input = f"{text}_{i}".encode()
            hash_obj = hashlib.sha256(hash_input)
            hash_bytes = hash_obj.digest()
            
            # Convert to float array
            vector_part = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
            embeddings.extend(vector_part[:self.dim // 4])
        
        # Pad or truncate to desired dimension
        vector = np.array(embeddings[:self.dim])
        if len(vector) < self.dim:
            vector = np.pad(vector, (0, self.dim - len(vector)), mode='constant')
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector


class VectorMemory:
    """Vector-based memory for semantic similarity search."""
    
    def __init__(self, embedding_dim: int = 256):
        self.embedding_dim = embedding_dim
        self.embedder = SimpleEmbedding(embedding_dim)
        self.entries: Dict[str, VectorEntry] = {}
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.entry_ids: List[str] = []
        self._needs_rebuild = True
    
    def add_entry(self, content: Any, metadata: Optional[Dict[str, Any]] = None, 
                  importance: float = 0.5) -> str:
        """Add an entry to vector memory."""
        # Convert content to text for embedding
        if isinstance(content, str):
            text = content
        else:
            text = json.dumps(content, default=str)
        
        # Generate ID
        entry_id = hashlib.md5(text.encode()).hexdigest()
        
        # Create embedding
        embedding = self.embedder.embed(text)
        
        # Create entry
        entry = VectorEntry(
            id=entry_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            timestamp=time.time(),
            importance=importance
        )
        
        self.entries[entry_id] = entry
        self._needs_rebuild = True
        
        return entry_id
    
    def search_similar(self, query: str, top_k: int = 5, 
                      min_similarity: float = 0.1) -> List[Tuple[VectorEntry, float]]:
        """Search for similar entries."""
        if not self.entries:
            return []
        
        # Create query embedding
        query_embedding = self.embedder.embed(query)
        
        # Rebuild embeddings matrix if needed
        if self._needs_rebuild:
            self._rebuild_embeddings_matrix()
        
        # Calculate similarities
        similarities = np.dot(self.embeddings_matrix, query_embedding)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = similarities[idx]
            if similarity >= min_similarity:
                entry_id = self.entry_ids[idx]
                entry = self.entries[entry_id]
                results.append((entry, float(similarity)))
        
        return results
    
    def get_entry(self, entry_id: str) -> Optional[VectorEntry]:
        """Get a specific entry."""
        return self.entries.get(entry_id)
    
    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry."""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._needs_rebuild = True
            return True
        return False
    
    def _rebuild_embeddings_matrix(self):
        """Rebuild the embeddings matrix."""
        if not self.entries:
            self.embeddings_matrix = None
            self.entry_ids = []
            return
        
        self.entry_ids = list(self.entries.keys())
        embeddings = [self.entries[entry_id].embedding for entry_id in self.entry_ids]
        self.embeddings_matrix = np.vstack(embeddings)
        self._needs_rebuild = False