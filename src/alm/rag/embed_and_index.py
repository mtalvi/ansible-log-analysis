"""
Ansible Error RAG System - Embedding and Indexing Module

This module implements:
- Groups chunks by error_id
- Creates composite embeddings (description + symptoms)
- Builds FAISS index for similarity search
- Persists index and metadata to disk
"""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import faiss


class AnsibleErrorEmbedder:
    """
    Handles embedding generation and FAISS index creation for Ansible errors.
    
    Architecture (per ADR-001):
    - Model: sentence-transformers/all-mpnet-base-v2
    - Embedding dimension: 768
    - Strategy: Composite embeddings (description + symptoms per error)
    - Vector DB: FAISS IndexFlatIP with L2-normalized vectors
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        index_path: str = "./data/ansible_errors.index",
        metadata_path: str = "./data/error_metadata.pkl"
    ):
        """
        Initialize the embedder with specified model and storage paths.
        
        Args:
            model_name: Sentence transformer model to use
            index_path: Path to save FAISS index
            metadata_path: Path to save error metadata
        """
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded. Embedding dimension: {self.embedding_dim}")
        
        self.index = None
        self.error_store = {}
        
    def group_chunks_by_error(self, chunks: List[Document]) -> Dict[str, Dict[str, Any]]:
        """
        Group chunks by error_id and organize into structured format.
        
        Args:
            chunks: List of Document chunks from parser
            
        Returns:
            Dictionary mapping error_id to complete error data
        """
        print("\n" + "=" * 60)
        print("STEP 4.4: INGESTION - Grouping chunks by error_id")
        print("=" * 60)
        
        errors_by_id = defaultdict(lambda: {
            'error_id': None,
            'error_title': None,
            'sections': {},
            'metadata': {}
        })
        
        for chunk in chunks:
            error_id = chunk.metadata.get('error_id')
            section_type = chunk.metadata.get('section_type')
            
            if not error_id or not section_type:
                continue
            
            # Initialize error entry
            if errors_by_id[error_id]['error_id'] is None:
                errors_by_id[error_id]['error_id'] = error_id
                errors_by_id[error_id]['error_title'] = chunk.metadata.get('error_title')
                errors_by_id[error_id]['metadata'] = {
                    'source_file': chunk.metadata.get('source_file'),
                    'page': chunk.metadata.get('page')
                }
            
            # Extract content (remove the header added by chunking)
            content = chunk.page_content
            # Remove "Error: X\n\nSection: Y\n\n" prefix
            lines = content.split('\n\n', 2)
            if len(lines) >= 3:
                content = lines[2]
            else:
                content = lines[-1]
            
            errors_by_id[error_id]['sections'][section_type] = content
        
        print(f"✓ Grouped {len(chunks)} chunks into {len(errors_by_id)} unique errors")
        
        # Statistics
        section_counts = defaultdict(int)
        for error in errors_by_id.values():
            for section in error['sections'].keys():
                section_counts[section] += 1
        
        print("\nSection distribution:")
        for section, count in sorted(section_counts.items()):
            print(f"  {section}: {count} errors")
        
        return dict(errors_by_id)
    
    def create_composite_embeddings(
        self,
        error_store: Dict[str, Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create composite embeddings from description + symptoms for each error.
        
        We concatenate description and symptoms sections because
        log summaries describe problems, not solutions.
        
        Args:
            error_store: Dictionary of errors grouped by error_id
            
        Returns:
            Tuple of (embedding_matrix, error_ids)
        """
        print("\n" + "=" * 60)
        print("GENERATING COMPOSITE EMBEDDINGS")
        print("=" * 60)
        
        composite_texts = []
        error_ids = []
        skipped = 0
        
        for error_id, error_data in error_store.items():
            sections = error_data['sections']
            
            # Extract description and symptoms
            description = sections.get('description', '').strip()
            symptoms = sections.get('symptoms', '').strip()
            
            # Skip errors without description or symptoms
            if not description and not symptoms:
                print(f"⚠ Skipping error {error_data['error_title']}: No description or symptoms")
                skipped += 1
                continue
            
            # Create composite text
            composite_parts = []
            if description:
                composite_parts.append(description)
            if symptoms:
                composite_parts.append(symptoms)
            
            composite_text = "\n\n".join(composite_parts)
            
            # Store composite text in error_store for reference
            error_data['composite_text'] = composite_text
            
            composite_texts.append(composite_text)
            error_ids.append(error_id)
        
        print(f"✓ Created {len(composite_texts)} composite texts")
        if skipped > 0:
            print(f"⚠ Skipped {skipped} errors (missing description and symptoms)")
        
        # Generate embeddings
        print(f"\nGenerating embeddings using {self.model_name}...")
        embeddings = self.model.encode(
            composite_texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        print(f"✓ Generated embeddings: shape={embeddings.shape}")
        
        return embeddings, error_ids
    
    def build_faiss_index(
        self,
        embeddings: np.ndarray,
        error_ids: List[str],
        error_store: Dict[str, Dict[str, Any]]
    ):
        """
        Build FAISS index from embeddings.
        
        Using IndexFlatIP (Inner Product) with L2-normalized vectors
        for exact cosine similarity search.
        
        Args:
            embeddings: Numpy array of embedding vectors
            error_ids: List of error_ids corresponding to embeddings
            error_store: Complete error data store
        """
        print("\n" + "=" * 60)
        print("CREATING FAISS INDEX")
        print("=" * 60)
        
        # Create FAISS index (IndexFlatIP for cosine similarity with normalized vectors)
        print(f"Building FAISS IndexFlatIP with dimension {self.embedding_dim}...")
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Add vectors to index
        self.index.add(embeddings)
        
        print(f"✓ Index created with {self.index.ntotal} vectors")
        
        # Create mapping from index position to error_id
        self.index_to_error_id = {i: error_id for i, error_id in enumerate(error_ids)}
        
        # Store only errors that have embeddings
        self.error_store = {
            error_id: error_store[error_id]
            for error_id in error_ids
        }
        
        print(f"✓ Stored metadata for {len(self.error_store)} errors")
    
    def save_index(self):
        """
        Persist FAISS index and metadata to disk.
        """
        print("\n" + "=" * 60)
        print("SAVING INDEX AND METADATA")
        print("=" * 60)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, self.index_path)
        print(f"✓ FAISS index saved to: {self.index_path}")
        
        # Save metadata (error_store + index mapping)
        metadata = {
            'error_store': self.error_store,
            'index_to_error_id': self.index_to_error_id,
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'total_errors': len(self.error_store)
        }
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✓ Metadata saved to: {self.metadata_path}")
        print(f"\nIndex Statistics:")
        print(f"  Total vectors: {self.index.ntotal}")
        print(f"  Total errors: {len(self.error_store)}")
        print(f"  Model: {self.model_name}")
        print(f"  Embedding dimension: {self.embedding_dim}")
    
    def load_index(self):
        """
        Load FAISS index and metadata from disk.
        """
        print("\n" + "=" * 60)
        print("LOADING INDEX AND METADATA")
        print("=" * 60)
        
        # Load FAISS index
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index not found at {self.index_path}")
        
        self.index = faiss.read_index(self.index_path)
        print(f"✓ FAISS index loaded from: {self.index_path}")
        print(f"  Total vectors: {self.index.ntotal}")
        
        # Load metadata
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata not found at {self.metadata_path}")
        
        with open(self.metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        self.error_store = metadata['error_store']
        self.index_to_error_id = metadata['index_to_error_id']
        
        print(f"✓ Metadata loaded from: {self.metadata_path}")
        print(f"  Total errors: {len(self.error_store)}")
        print(f"  Model: {metadata['model_name']}")
        print(f"  Embedding dimension: {metadata['embedding_dim']}")
        
        # Verify model consistency
        if metadata['model_name'] != self.model_name:
            print(f"⚠ Warning: Model mismatch!")
            print(f"  Index built with: {metadata['model_name']}")
            print(f"  Current model: {self.model_name}")
    
    def ingest_and_index(self, chunks: List[Document]):
        """
        Complete ingestion and indexing pipeline.
        
        This is the main method that orchestrates:
        1. Grouping chunks by error_id
        2. Creating composite embeddings
        3. Building FAISS index
        4. Saving to disk
        
        Args:
            chunks: List of Document chunks from parser
        """
        print("\n" + "=" * 70)
        print("ANSIBLE ERROR RAG SYSTEM - INGESTION AND INDEXING PIPELINE")
        print("=" * 70)
        
        # Step 4.4: Ingestion
        error_store = self.group_chunks_by_error(chunks)
        
        # Generate embeddings
        embeddings, error_ids = self.create_composite_embeddings(error_store)
        
        # Step 4.5: Build index
        self.build_faiss_index(embeddings, error_ids, error_store)
        
        # Save to disk
        self.save_index()
        
        print("\n" + "=" * 70)
        print("✓ INGESTION AND INDEXING COMPLETE")
        print("=" * 70)
        print(f"\nNext steps:")
        print(f"  1. Test similarity search with sample queries")
        print(f"  2. Implement query pipeline")
        print(f"  3. Integrate with agent system")


def main():
    """
    Example usage: Process all PDFs in knowledge_base directory.
    """
    from ingest_and_chunk import AnsibleErrorParser
    import glob
    
    print("=" * 70)
    print("ANSIBLE ERROR KNOWLEDGE BASE - EMBEDDING AND INDEXING")
    print("=" * 70)
    print()
    
    # Initialize parser and embedder
    parser = AnsibleErrorParser()
    embedder = AnsibleErrorEmbedder(
        index_path="/home/mtalvi/ansible-log-analysis/data/ansible_errors.index",
        metadata_path="/home/mtalvi/ansible-log-analysis/data/error_metadata.pkl"
    )
    
    # Find all PDFs in knowledge_base directory
    kb_path = "/home/mtalvi/ansible-log-analysis/knowledge_base"
    pdf_files = glob.glob(os.path.join(kb_path, "*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files in {kb_path}")
    for pdf in pdf_files:
        print(f"  - {os.path.basename(pdf)}")
    print()
    
    # Process all PDFs
    all_chunks = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        chunks = parser.parse_pdf_to_chunks(pdf_path)
        all_chunks.extend(chunks)
        print(f"  ✓ Extracted {len(chunks)} chunks")
    
    print(f"\n{'=' * 70}")
    print(f"TOTAL: {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
    print(f"{'=' * 70}\n")
    
    # Ingest and index
    embedder.ingest_and_index(all_chunks)
    
    return embedder


if __name__ == "__main__":
    embedder = main()