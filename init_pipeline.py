import asyncio
from alm.pipeline.offline import whole_pipeline
from alm.utils.phoenix import register_phoenix
import os
import glob
from pathlib import Path

# dotenv is optional - only used for local development
# In Kubernetes, all config comes from ConfigMaps/Secrets
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # Running in Kubernetes, no .env file needed


def build_rag_index():
    """
    Build RAG index from knowledge base PDFs.
    This runs during the init job to create the FAISS index and metadata.
    """
    from src.alm.config import config
    from src.alm.rag.ingest_and_chunk import AnsibleErrorParser
    from src.alm.rag.embed_and_index import AnsibleErrorEmbedder

    # Check if RAG is enabled
    rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
    if not rag_enabled:
        print("RAG is disabled (RAG_ENABLED=false), skipping RAG index build")
        return

    # Check if index already exists (skip rebuild for faster upgrades)
    index_path = Path(config.storage.index_path)
    metadata_path = Path(config.storage.metadata_path)

    if index_path.exists() and metadata_path.exists():
        print("✓ RAG index already exists, skipping rebuild")
        print(f"  Index: {index_path}")
        print(f"  Metadata: {metadata_path}")
        print("  To force rebuild, delete the PVC or these files")
        return

    print("\n" + "=" * 70)
    print("BUILDING RAG INDEX FROM KNOWLEDGE BASE")
    print("=" * 70)

    try:
        # Validate configuration
        config.print_config()
        config.validate()

        # Initialize components
        parser = AnsibleErrorParser()
        embedder = AnsibleErrorEmbedder()

        # Find PDFs in knowledge base
        kb_dir = config.storage.knowledge_base_dir
        pdf_files = sorted(glob.glob(str(kb_dir / "*.pdf")))

        if not pdf_files:
            print(f"⚠ WARNING: No PDF files found in {kb_dir}")
            print("  RAG index will not be created")
            return

        print(f"\n✓ Found {len(pdf_files)} PDF files in knowledge base:")
        for pdf in pdf_files:
            print(f"  - {Path(pdf).name}")

        # Process all PDFs
        all_chunks = []
        for pdf_path in pdf_files:
            print(f"\n📄 Processing: {Path(pdf_path).name}")
            try:
                chunks = parser.parse_pdf_to_chunks(pdf_path)
                all_chunks.extend(chunks)
                print(f"  ✓ Extracted {len(chunks)} chunks")
            except Exception as e:
                print(f"  ✗ Error processing {Path(pdf_path).name}: {e}")
                continue

        if not all_chunks:
            print("\n⚠ WARNING: No chunks extracted from PDFs")
            print("  RAG index will not be created")
            return

        print(f"\n{'=' * 70}")
        print(f"TOTAL: {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
        print(f"{'=' * 70}")

        # Build and save index
        embedder.ingest_and_index(all_chunks)

        print("\n" + "=" * 70)
        print("✓ RAG INDEX BUILD COMPLETE")
        print("=" * 70)
        print(f"  Index: {index_path}")
        print(f"  Metadata: {metadata_path}")

    except Exception as e:
        print(f"\n✗ ERROR building RAG index: {e}")
        print("  The system will continue without RAG functionality")
        import traceback

        traceback.print_exc()


async def main():
    # Build RAG index first (only in init job)
    print("\n" + "=" * 70)
    print("ANSIBLE LOG MONITOR - INITIALIZATION PIPELINE")
    print("=" * 70)

    # Step 1: Build RAG index
    build_rag_index()

    # Step 2: Run main pipeline (clustering, summarization, etc.)
    print("\n" + "=" * 70)
    print("RUNNING MAIN PIPELINE")
    print("=" * 70)
    await whole_pipeline()

    print("\n" + "=" * 70)
    print("✓ INITIALIZATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    register_phoenix()
    asyncio.run(main())
