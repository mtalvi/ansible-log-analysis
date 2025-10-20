"""
FIXED v2: Step 1 - PDF Ingestion with better whitespace handling
"""

import re
import uuid
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document


class AnsibleErrorParser:
    """
    Parses Ansible error documentation PDFs into structured chunks.
    FIXED: Handles leading whitespace in numbered sections.
    """
    
    def __init__(self):
        # FIXED: Allow optional leading whitespace before the number
        self.error_title_pattern = re.compile(
            r'^\s*\d+\.\s*.+$',  # Optional whitespace at start
            re.MULTILINE
        )
        
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Load PDF and return documents with page metadata"""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✓ Loaded PDF: {pdf_path}")
        print(f"  Total pages: {len(documents)}")
        return documents
    
    def extract_errors_from_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extract individual error entries from the PDF documents.
        """
        # Combine all pages into one text
        full_text = "\n".join([doc.page_content for doc in documents])
        
        # Find all error titles
        error_matches = list(self.error_title_pattern.finditer(full_text))
        
        print(f"[DEBUG] Found {len(error_matches)} error title matches")
        for i, match in enumerate(error_matches[:5]):  # Show first 5
            print(f"  Match {i+1}: {match.group(0).strip()[:60]}")
        
        errors = []
        
        for i, match in enumerate(error_matches):
            error_start = match.start()
            error_end = error_matches[i + 1].start() if i + 1 < len(error_matches) else len(full_text)
            
            error_text = full_text[error_start:error_end]
            error_title = match.group(0).strip()  # Strip whitespace from title
            
            # Determine page number
            page_num = self._find_page_number(documents, error_start, full_text)
            
            # Parse the error into sections
            parsed_error = self._parse_error_sections(
                error_text, 
                error_title, 
                page_num, 
                documents[0].metadata.get('source', 'unknown')
            )
            errors.append(parsed_error)
        
        print(f"✓ Extracted {len(errors)} error entries")
        return errors
    
    def _find_page_number(self, documents: List[Document], char_position: int, full_text: str) -> int:
        """Find which page a character position belongs to"""
        current_pos = 0
        for i, doc in enumerate(documents):
            current_pos += len(doc.page_content)
            if char_position < current_pos:
                return i + 1
        return len(documents)
    
    def _parse_error_sections(self, error_text: str, error_title: str, page: int, source_file: str) -> Dict[str, Any]:
        """
        Parse an error entry into its component sections.
        """
        sections = {
            'error_title': error_title,
            'description': '',
            'symptoms': '',
            'resolution': '',
            'code': ''
        }
        
        # Find Description
        desc_match = re.search(
            r'Description:\s*(.*?)(?=Symptoms:|Resolution:|Code:|$)',
            error_text, 
            re.DOTALL | re.IGNORECASE
        )
        if desc_match:
            sections['description'] = desc_match.group(1).strip()
        
        # Find Symptoms
        symp_match = re.search(
            r'Symptoms:\s*(.*?)(?=Resolution:|Code:|$)',
            error_text,
            re.DOTALL | re.IGNORECASE
        )
        if symp_match:
            sections['symptoms'] = symp_match.group(1).strip()
        
        # Find Resolution
        res_match = re.search(
            r'Resolution:\s*(.*?)(?=Code:|Benefits|$)',
            error_text,
            re.DOTALL | re.IGNORECASE
        )
        if res_match:
            sections['resolution'] = res_match.group(1).strip()
        
        # Find Code
        code_match = re.search(
            r'Code:\s*(.*?)(?=Benefits|\d+\.\s+\w+|$)',
            error_text,
            re.DOTALL | re.IGNORECASE
        )
        if code_match:
            sections['code'] = code_match.group(1).strip()
        
        return {
            'sections': sections,
            'page': page,
            'source_file': source_file
        }
    
    def create_chunks(self, errors: List[Dict[str, Any]]) -> List[Document]:
        """
        Create LangChain Document chunks from parsed errors.
        """
        chunks = []
        
        for error in errors:
            error_id = str(uuid.uuid4())
            error_title = error['sections']['error_title']
            
            section_types = ['description', 'symptoms', 'resolution', 'code']
            
            for section_type in section_types:
                content = error['sections'][section_type]
                
                if not content or content.strip() == '':
                    continue
                
                metadata = {
                    'error_id': error_id,
                    'error_title': error_title,
                    'section_type': section_type,
                    'source_file': error['source_file'],
                    'page': error['page']
                }
                
                chunk_content = f"Error: {error_title}\n\n"
                chunk_content += f"Section: {section_type.capitalize()}\n\n"
                chunk_content += content
                
                chunk = Document(
                    page_content=chunk_content,
                    metadata=metadata
                )
                
                chunks.append(chunk)
        
        print(f"✓ Created {len(chunks)} chunks from {len(errors)} errors")
        return chunks
    
    def parse_pdf_to_chunks(self, pdf_path: str) -> List[Document]:
        """
        Main method: Parse a PDF file into structured chunks.
        """
        documents = self.load_pdf(pdf_path)
        errors = self.extract_errors_from_documents(documents)
        chunks = self.create_chunks(errors)
        return chunks


def main():
    """Test the parser"""
    print("=" * 60)
    print("ANSIBLE ERROR KNOWLEDGE BASE - STEP 1: PDF PARSING (FIXED)")
    print("=" * 60)
    print()
    
    parser = AnsibleErrorParser()
    
    pdf_path = "/home/mtalvi/ansible-log-analysis/knowledge_base/file_10.pdf"
    chunks = parser.parse_pdf_to_chunks(pdf_path)
    
    print()
    print("=" * 60)
    print("ALL ERROR TITLES FOUND:")
    print("=" * 60)
    
    # Group chunks by error_id to see unique errors
    seen_errors = {}
    for chunk in chunks:
        error_id = chunk.metadata['error_id']
        error_title = chunk.metadata['error_title']
        if error_id not in seen_errors:
            seen_errors[error_id] = error_title
    
    # Sort by error number
    sorted_errors = sorted(seen_errors.values(), key=lambda x: int(x.split('.')[0]))
    
    for i, error_title in enumerate(sorted_errors, 1):
        print(f"  {i}. {error_title}")
    
    print(f"\n✓ Total chunks created: {len(chunks)}")
    print(f"✓ Total unique errors: {len(seen_errors)}")
    print(f"✓ Expected: 12 errors")
    
    if len(seen_errors) == 12:
        print("\n🎉 SUCCESS: All 12 errors captured!")
    else:
        print(f"\n⚠️  WARNING: Only {len(seen_errors)} errors found (expected 12)")
    
    return chunks


if __name__ == "__main__":
    chunks = main()