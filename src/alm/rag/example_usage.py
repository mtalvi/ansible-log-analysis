"""
Example Usage Script for Step 1: Document Ingestion & Extraction

This script demonstrates how to use the AnsibleErrorParser and provides
validation utilities to ensure your extraction is working correctly.
"""

from step1_document_ingestion import AnsibleErrorParser
from pathlib import Path
import json


def validate_document(doc) -> dict:
    """
    Validate a single document and return validation results
    
    Args:
        doc: LangChain Document object
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check required metadata fields
    required_fields = ['error_id', 'resource_file', 'page_numbers', 'pages', 
                       'has_code', 'error_title', 'chunk_type']
    
    for field in required_fields:
        if field not in doc.metadata:
            issues.append(f"Missing required metadata field: {field}")
    
    # Check content
    if not doc.page_content or len(doc.page_content.strip()) == 0:
        issues.append("Empty page content")
    
    if len(doc.page_content) < 50:
        warnings.append(f"Very short content ({len(doc.page_content)} chars)")
    
    # Check if essential sections are present
    content_lower = doc.page_content.lower()
    if 'resolution' not in content_lower:
        warnings.append("No 'resolution' section found in content")
    
    if 'description' not in content_lower:
        warnings.append("No 'description' section found in content")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }


def print_statistics(documents):
    """
    Print statistics about the extracted documents
    
    Args:
        documents: List of LangChain Document objects
    """
    print("\n" + "=" * 70)
    print("EXTRACTION STATISTICS")
    print("=" * 70)
    
    print(f"\nTotal Documents: {len(documents)}")
    
    # Count by source file
    sources = {}
    for doc in documents:
        source = doc.metadata.get('resource_file', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\nDocuments by Source File:")
    for source, count in sorted(sources.items()):
        print(f"  {source}: {count} errors")
    
    # Code examples
    with_code = sum(1 for doc in documents if doc.metadata.get('has_code', False))
    print(f"\nEntries with Code Examples: {with_code} ({with_code/len(documents)*100:.1f}%)")
    
    # Content length statistics
    lengths = [len(doc.page_content) for doc in documents]
    if lengths:
        print(f"\nContent Length Statistics:")
        print(f"  Average: {sum(lengths)/len(lengths):.0f} characters")
        print(f"  Minimum: {min(lengths)} characters")
        print(f"  Maximum: {max(lengths)} characters")
    
    # Multi-page errors
    multi_page = sum(1 for doc in documents 
                     if len(doc.metadata.get('page_numbers', [])) > 1)
    print(f"\nMulti-page Errors: {multi_page}")


def print_sample_documents(documents, num_samples=2):
    """
    Print sample documents for manual inspection
    
    Args:
        documents: List of LangChain Document objects
        num_samples: Number of samples to print
    """
    print("\n" + "=" * 70)
    print(f"SAMPLE DOCUMENTS (showing {min(num_samples, len(documents))} of {len(documents)})")
    print("=" * 70)
    
    for i, doc in enumerate(documents[:num_samples], 1):
        print(f"\n--- Sample {i} ---")
        print(f"Error Title: {doc.metadata.get('error_title', 'N/A')}")
        print(f"Source File: {doc.metadata.get('resource_file', 'N/A')}")
        print(f"Pages: {doc.metadata.get('pages', 'N/A')}")
        print(f"Has Code: {doc.metadata.get('has_code', False)}")
        print(f"\nContent Preview (first 400 chars):")
        print("-" * 70)
        print(doc.page_content[:400] + "...")
        print("-" * 70)


def export_metadata_to_json(documents, output_path="metadata_export.json"):
    """
    Export all metadata to JSON for analysis
    
    Args:
        documents: List of LangChain Document objects
        output_path: Path to save JSON file
    """
    metadata_list = []
    
    for doc in documents:
        metadata = doc.metadata.copy()
        # Add content preview
        metadata['content_preview'] = doc.page_content[:200]
        metadata['content_length'] = len(doc.page_content)
        metadata_list.append(metadata)
    
    with open(output_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    print(f"\n✓ Metadata exported to: {output_path}")


def run_validation(documents):
    """
    Run validation on all documents and report results
    
    Args:
        documents: List of LangChain Document objects
    """
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    
    all_issues = []
    all_warnings = []
    valid_count = 0
    
    for i, doc in enumerate(documents, 1):
        result = validate_document(doc)
        
        if result['valid']:
            valid_count += 1
        
        if result['issues']:
            all_issues.extend([f"Doc {i}: {issue}" for issue in result['issues']])
        
        if result['warnings']:
            all_warnings.extend([f"Doc {i}: {warning}" for warning in result['warnings']])
    
    print(f"\n✓ Valid Documents: {valid_count}/{len(documents)} ({valid_count/len(documents)*100:.1f}%)")
    
    if all_issues:
        print(f"\n⚠ Issues Found ({len(all_issues)}):")
        for issue in all_issues[:10]:  # Show first 10
            print(f"  • {issue}")
        if len(all_issues) > 10:
            print(f"  ... and {len(all_issues)-10} more")
    else:
        print("\n✓ No issues found!")
    
    if all_warnings:
        print(f"\n⚡ Warnings ({len(all_warnings)}):")
        for warning in all_warnings[:10]:  # Show first 10
            print(f"  • {warning}")
        if len(all_warnings) > 10:
            print(f"  ... and {len(all_warnings)-10} more")


def main():
    """
    Main execution function demonstrating complete workflow
    """
    # CONFIGURATION
    PDF_DIRECTORY = "/home/mtalvi/ansible-log-analysis/knowledge_base"  # Update this!
    EXPORT_METADATA = True
    SHOW_SAMPLES = True
    
    print("=" * 70)
    print("ANSIBLE ERROR RAG SYSTEM - STEP 1 EXAMPLE")
    print("=" * 70)
    
    # Check if directory exists
    pdf_path = Path(PDF_DIRECTORY)
    if not pdf_path.exists():
        print(f"\n❌ Error: Directory not found: {PDF_DIRECTORY}")
        print("\nPlease update the PDF_DIRECTORY variable in this script.")
        return
    
    # Count PDF files
    pdf_files = list(pdf_path.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files in directory")
    
    if len(pdf_files) == 0:
        print("\n❌ No PDF files found in directory!")
        return
    
    print("\nPDF Files to process:")
    for pdf in sorted(pdf_files):
        print(f"  • {pdf.name}")
    
    # Initialize parser
    print("\nInitializing parser...")
    parser = AnsibleErrorParser(PDF_DIRECTORY)
    
    # Extract documents
    print("\nExtracting documents from PDFs...")
    print("-" * 70)
    documents = parser.create_documents()
    
    if not documents:
        print("\n❌ No documents extracted! Check your PDFs and parser configuration.")
        return
    
    # Print statistics
    print_statistics(documents)
    
    # Run validation
    run_validation(documents)
    
    # Show samples
    if SHOW_SAMPLES:
        print_sample_documents(documents, num_samples=2)
    
    # Export metadata
    if EXPORT_METADATA:
        export_metadata_to_json(documents, "/home/mtalvi/ansible-log-analysis/metadata_export.json")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Successfully extracted {len(documents)} error entries")
    print(f"✓ Ready for Step 2: Embedding Generation")
    print("\nNext steps:")
    print("  1. Review the samples and statistics above")
    print("  2. Adjust parser configuration if needed")
    print("  3. Proceed to Step 2 for embedding generation")
    
    return documents


if __name__ == "__main__":
    documents = main()