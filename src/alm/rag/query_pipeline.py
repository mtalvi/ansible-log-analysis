#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ansible Error RAG System - Query Pipeline

This module implements Step 5 from ADR-001:
- Receives log summaries from agents
- Generates embeddings for queries
- Performs similarity search in FAISS
- Reconstructs complete error entries
- Returns ranked results with confidence scores

Input: Log summary (few sentences)
Output: Complete error entries with all sections
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from alm.rag.embed_and_index import AnsibleErrorEmbedder, EmbeddingClient
from alm.config import config


@dataclass
class ErrorSection:
    """Represents a single error section."""
    description: str
    symptoms: str
    resolution: str
    code: Optional[str] = None
    benefits: Optional[str] = None


@dataclass
class ErrorResult:
    """Represents a single error result from the query."""
    error_id: str
    error_title: str
    similarity_score: float
    source_file: str
    page: int
    sections: ErrorSection
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['sections'] = asdict(self.sections)
        return result


@dataclass
class QueryResponse:
    """Complete response from the RAG query."""
    query: str
    results: List[ErrorResult]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'results': [r.to_dict() for r in self.results],
            'metadata': self.metadata
        }


class AnsibleErrorQueryPipeline:
    """
    Query pipeline for retrieving relevant Ansible errors.
    
    Pipeline stages (per ADR-001):
    1. Generate query embedding
    2. Similarity search (top-k candidates)
    3. Filter by threshold
    4. Rank and return top-n results
    """
    
    def __init__(
        self,
        embedder: Optional[AnsibleErrorEmbedder] = None,
        top_k: int = 10,
        top_n: int = 3,
        similarity_threshold: float = 0.6
    ):
        """
        Initialize the query pipeline.
        
        Args:
            embedder: Pre-initialized embedder (will create if None)
            top_k: Number of candidates to retrieve from FAISS
            top_n: Number of final results to return
            similarity_threshold: Minimum cosine similarity score (0-1)
        """
        self.top_k = top_k
        self.top_n = top_n
        self.similarity_threshold = similarity_threshold
        
        # Initialize or use provided embedder
        if embedder is None:
            print("Initializing embedder from config...")
            self.embedder = AnsibleErrorEmbedder()
            self.embedder.load_index()
        else:
            self.embedder = embedder
        
        # Validate that index is loaded
        if self.embedder.index is None:
            raise ValueError("Embedder must have a loaded index")
        
        print(f"✓ Query pipeline initialized")
        print(f"  Top-k candidates: {self.top_k}")
        print(f"  Top-n results: {self.top_n}")
        print(f"  Similarity threshold: {self.similarity_threshold}")
        print(f"  Total errors in index: {len(self.embedder.error_store)}")
    
    def query(
        self,
        log_summary: str,
        top_k: Optional[int] = None,
        top_n: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> QueryResponse:
        """
        Query the RAG system with a log summary.
        
        Args:
            log_summary: Error description from logs
            top_k: Override default top_k
            top_n: Override default top_n
            similarity_threshold: Override default threshold
        
        Returns:
            QueryResponse with ranked error results
        """
        start_time = time.time()
        
        # Use defaults if not overridden
        top_k = top_k or self.top_k
        top_n = top_n or self.top_n
        similarity_threshold = similarity_threshold or self.similarity_threshold
        
        print(f"\n{'=' * 70}")
        print(f"QUERYING RAG SYSTEM")
        print(f"{'=' * 70}")
        print(f"Query: {log_summary[:100]}{'...' if len(log_summary) > 100 else ''}")
        print(f"Parameters: top_k={top_k}, top_n={top_n}, threshold={similarity_threshold}")
        
        # Step 5.1: Receive log summary (done)
        
        # Step 5.2: Generate embedding for log summary
        query_embedding = self._generate_query_embedding(log_summary)
        
        # Step 5.3: Similarity search in FAISS
        candidates = self._similarity_search(query_embedding, top_k)
        
        # Step 5.4: Fetch complete error data (already done in similarity_search)
        
        # Step 5.5: Filter by similarity threshold
        filtered_results = self._filter_by_threshold(candidates, similarity_threshold)
        
        # Step 5.6: Rank and return top-N errors
        final_results = self._rank_and_select(filtered_results, top_n)
        
        # Calculate metadata
        search_time_ms = (time.time() - start_time) * 1000
        
        metadata = {
            'num_results': len(final_results),
            'num_candidates': len(candidates),
            'num_filtered': len(filtered_results),
            'search_time_ms': round(search_time_ms, 2),
            'top_k': top_k,
            'top_n': top_n,
            'similarity_threshold': similarity_threshold,
            'model': self.embedder.model_name
        }
        
        print(f"\n✓ Query complete in {search_time_ms:.2f}ms")
        print(f"  Retrieved: {len(candidates)} candidates")
        print(f"  Filtered: {len(filtered_results)} above threshold")
        print(f"  Returned: {len(final_results)} results")
        
        return QueryResponse(
            query=log_summary,
            results=final_results,
            metadata=metadata
        )
    
    def _generate_query_embedding(self, log_summary: str) -> np.ndarray:
        """
        Generate embedding for the query.
        
        Step 5.2: Uses same model as indexing, with query-specific prefix for Nomic.
        """
        print(f"\nStep 5.2: Generating query embedding...")
        
        # Add task prefix for Nomic models
        use_task_prefix = 'nomic' in self.embedder.model_name.lower()
        
        if use_task_prefix:
            query_text = f"search_query: {log_summary}"
            print(f"  Using task prefix: 'search_query:'")
        else:
            query_text = log_summary
        
        # Generate embedding
        embedding = self.embedder.client.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False
        )[0]
        
        # Verify normalization
        norm = np.linalg.norm(embedding)
        print(f"  ✓ Embedding generated (norm={norm:.4f})")
        
        return embedding
    
    def _similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int
    ) -> List[ErrorResult]:
        """
        Perform similarity search in FAISS.
        
        Step 5.3: Retrieves top-k most similar error embeddings.
        """
        print(f"\nStep 5.3: Similarity search (top-k={top_k})...")
        
        # Reshape for FAISS (needs 2D array)
        query_vector = query_embedding.reshape(1, -1)
        
        # Search FAISS index
        # Returns: distances (similarity scores), indices (positions in index)
        similarities, indices = self.embedder.index.search(query_vector, top_k)
        
        # Flatten results
        similarities = similarities[0]
        indices = indices[0]
        
        print(f"  ✓ Found {len(indices)} candidates")
        
        # Step 5.4: Fetch complete error data
        results = []
        for idx, similarity in zip(indices, similarities):
            # Handle case where FAISS returns -1 for not enough results
            if idx == -1:
                continue
            
            # Get error_id from index mapping
            error_id = self.embedder.index_to_error_id[idx]
            error_data = self.embedder.error_store[error_id]
            
            # Create ErrorResult
            sections = ErrorSection(
                description=error_data['sections'].get('description', ''),
                symptoms=error_data['sections'].get('symptoms', ''),
                resolution=error_data['sections'].get('resolution', ''),
                code=error_data['sections'].get('code'),
                benefits=error_data['sections'].get('benefits')
            )
            
            result = ErrorResult(
                error_id=error_id,
                error_title=error_data['error_title'],
                similarity_score=float(similarity),
                source_file=error_data['metadata']['source_file'],
                page=error_data['metadata']['page'],
                sections=sections
            )
            
            results.append(result)
        
        # Log top results
        if results:
            print(f"\n  Top candidates:")
            for i, result in enumerate(results[:3], 1):
                print(f"    {i}. {result.error_title[:60]}... (score: {result.similarity_score:.4f})")
        
        return results
    
    def _filter_by_threshold(
        self,
        candidates: List[ErrorResult],
        threshold: float
    ) -> List[ErrorResult]:
        """
        Filter results by similarity threshold.
        
        Step 5.5: Keeps only results above minimum similarity score.
        """
        print(f"\nStep 5.5: Filtering by threshold ({threshold})...")
        
        filtered = [r for r in candidates if r.similarity_score >= threshold]
        
        if not filtered:
            print(f"  ⚠ No results above threshold")
            print(f"  Best score: {candidates[0].similarity_score:.4f}" if candidates else "N/A")
        else:
            print(f"  ✓ {len(filtered)} results pass threshold")
            print(f"  Score range: {filtered[-1].similarity_score:.4f} - {filtered[0].similarity_score:.4f}")
        
        return filtered
    
    def _rank_and_select(
        self,
        filtered_results: List[ErrorResult],
        top_n: int
    ) -> List[ErrorResult]:
        """
        Rank and select top-N results.
        
        Step 5.6: Returns top-N highest scoring results.
        """
        print(f"\nStep 5.6: Selecting top-{top_n} results...")
        
        # Results are already sorted by FAISS, just take top N
        final_results = filtered_results[:top_n]
        
        print(f"  ✓ Returning {len(final_results)} results")
        
        return final_results
    
    def query_simple(self, log_summary: str) -> Dict[str, Any]:
        """
        Simplified query interface that returns a dictionary.
        Useful for API integration.
        """
        response = self.query(log_summary)
        return response.to_dict()


def format_result_for_display(result: ErrorResult) -> str:
    """
    Format a single result for human-readable display.
    """
    output = []
    output.append("=" * 70)
    output.append(f"ERROR: {result.error_title}")
    output.append(f"Similarity Score: {result.similarity_score:.4f}")
    output.append(f"Source: {result.source_file} (page {result.page})")
    output.append("=" * 70)
    
    if result.sections.description:
        output.append(f"\n📋 DESCRIPTION:")
        output.append(result.sections.description)
    
    if result.sections.symptoms:
        output.append(f"\n⚠️  SYMPTOMS:")
        output.append(result.sections.symptoms)
    
    if result.sections.resolution:
        output.append(f"\n✅ RESOLUTION:")
        output.append(result.sections.resolution)
    
    if result.sections.code:
        output.append(f"\n💻 CODE:")
        output.append(result.sections.code)
    
    if result.sections.benefits:
        output.append(f"\n⭐ BENEFITS:")
        output.append(result.sections.benefits)
    
    return "\n".join(output)


def format_response_for_display(response: QueryResponse) -> str:
    """
    Format the complete query response for human-readable display.
    """
    output = []
    
    output.append("\n" + "=" * 70)
    output.append("QUERY RESULTS")
    output.append("=" * 70)
    output.append(f"Query: {response.query}")
    output.append(f"Found: {response.metadata['num_results']} results")
    output.append(f"Search time: {response.metadata['search_time_ms']:.2f}ms")
    output.append("=" * 70)
    
    if not response.results:
        output.append("\n⚠️  No results found above similarity threshold")
        output.append(f"Try lowering the threshold (current: {response.metadata['similarity_threshold']})")
    else:
        for i, result in enumerate(response.results, 1):
            output.append(f"\n\n{'#' * 70}")
            output.append(f"RESULT {i} of {len(response.results)}")
            output.append(format_result_for_display(result))
    
    return "\n".join(output)


def main():
    """
    Test the query pipeline with sample queries.
    """
    print("=" * 70)
    print("ANSIBLE ERROR RAG SYSTEM - QUERY PIPELINE TEST")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = AnsibleErrorQueryPipeline(
        top_k=5,
        top_n=3,
        similarity_threshold=0.6
    )
    
    # Test queries
    test_queries = [
        "Role name does not match the required naming convention with prefix",
        "Task is missing a name attribute",
        "Variable is not defined in the playbook",
        "YAML syntax error in the configuration file",
        "Permission denied when executing the playbook"
    ]
    
    print(f"\nRunning {len(test_queries)} test queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'*' * 70}")
        print(f"TEST QUERY {i}/{len(test_queries)}")
        print(f"{'*' * 70}")
        
        # Query the system
        response = pipeline.query(query)
        
        # Display results
        print(format_response_for_display(response))
        
        # Wait between queries
        if i < len(test_queries):
            print("\n" + "=" * 70)
            input("Press Enter to continue to next query...")
    
    print("\n" + "=" * 70)
    print("✓ ALL TEST QUERIES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()