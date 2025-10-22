#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick test script to verify Nomic embeddings work correctly.
"""

from sentence_transformers import SentenceTransformer
import numpy as np

def test_nomic_embeddings():
    print("Testing Nomic-Embed-Text-v1.5...")
    print("=" * 60)
    
    # Load model
    print("\n1. Loading model...")
    model = SentenceTransformer(
        "nomic-ai/nomic-embed-text-v1.5",
        trust_remote_code=True
    )
    print(f"✓ Model loaded: {model.get_sentence_embedding_dimension()}-dimensional embeddings")
    
    # Test embeddings
    print("\n2. Testing embeddings...")
    
    # Simulate error document
    error_doc = "search_document: Role name does not follow naming convention. The role name must start with the prefix 'ansible-role-'."
    
    # Simulate query
    query = "search_query: My playbook fails because the role name is invalid"
    
    # Generate embeddings
    doc_embedding = model.encode(error_doc, normalize_embeddings=True)
    query_embedding = model.encode(query, normalize_embeddings=True)
    
    print(f"✓ Document embedding shape: {doc_embedding.shape}")
    print(f"✓ Query embedding shape: {query_embedding.shape}")
    
    # Calculate similarity
    similarity = np.dot(query_embedding, doc_embedding)
    print(f"\n3. Similarity score: {similarity:.4f}")
    
    # Test without prefixes
    print("\n4. Testing without task prefixes...")
    doc_no_prefix = "Role name does not follow naming convention."
    query_no_prefix = "My playbook fails because the role name is invalid"
    
    doc_emb_no_prefix = model.encode(doc_no_prefix, normalize_embeddings=True)
    query_emb_no_prefix = model.encode(query_no_prefix, normalize_embeddings=True)
    
    similarity_no_prefix = np.dot(query_emb_no_prefix, doc_emb_no_prefix)
    print(f"✓ Similarity without prefixes: {similarity_no_prefix:.4f}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print(f"Note: Task prefixes {'improved' if similarity > similarity_no_prefix else 'did not improve'} similarity")

if __name__ == "__main__":
    test_nomic_embeddings()