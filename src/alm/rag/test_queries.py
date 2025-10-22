#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive testing tool for the query pipeline.
"""

import sys
from query_pipeline import AnsibleErrorQueryPipeline, format_response_for_display


def interactive_mode():
    """Run in interactive mode for testing queries."""
    print("=" * 70)
    print("ANSIBLE ERROR RAG - INTERACTIVE QUERY MODE")
    print("=" * 70)
    print("\nInitializing...")
    
    # Initialize pipeline
    pipeline = AnsibleErrorQueryPipeline(
        top_k=10,
        top_n=3,
        similarity_threshold=0.5
    )
    
    print("\n" + "=" * 70)
    print("Ready! Enter your log summaries below.")
    print("Commands:")
    print("  - Type your query and press Enter")
    print("  - 'quit' or 'exit' to exit")
    print("  - 'threshold X' to change threshold (e.g., 'threshold 0.7')")
    print("  - 'topn X' to change number of results (e.g., 'topn 5')")
    print("=" * 70)
    
    while True:
        try:
            # Get user input
            print("\n" + "-" * 70)
            query = input("Enter log summary (or command): ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if query.lower().startswith('threshold '):
                try:
                    new_threshold = float(query.split()[1])
                    pipeline.similarity_threshold = new_threshold
                    print(f"✓ Threshold set to {new_threshold}")
                    continue
                except (ValueError, IndexError):
                    print("⚠ Invalid threshold. Use: threshold 0.7")
                    continue
            
            if query.lower().startswith('topn '):
                try:
                    new_topn = int(query.split()[1])
                    pipeline.top_n = new_topn
                    print(f"✓ Top-N set to {new_topn}")
                    continue
                except (ValueError, IndexError):
                    print("⚠ Invalid top-n. Use: topn 5")
                    continue
            
            # Execute query
            response = pipeline.query(query)
            
            # Display results
            print(format_response_for_display(response))
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠ Error: {e}")
            import traceback
            traceback.print_exc()


def batch_mode(queries_file: str):
    """Run in batch mode from file."""
    print("=" * 70)
    print("ANSIBLE ERROR RAG - BATCH QUERY MODE")
    print("=" * 70)
    
    # Load queries from file
    with open(queries_file, 'r') as f:
        queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\nLoaded {len(queries)} queries from {queries_file}")
    
    # Initialize pipeline
    pipeline = AnsibleErrorQueryPipeline(
        top_k=10,
        top_n=3,
        similarity_threshold=0.6
    )
    
    # Process each query
    for i, query in enumerate(queries, 1):
        print(f"\n{'*' * 70}")
        print(f"QUERY {i}/{len(queries)}")
        print(f"{'*' * 70}")
        
        response = pipeline.query(query)
        print(format_response_for_display(response))
    
    print("\n" + "=" * 70)
    print(f"✓ PROCESSED {len(queries)} QUERIES")
    print("=" * 70)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Batch mode with file
        batch_mode(sys.argv[1])
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()