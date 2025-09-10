#!/usr/bin/env python3
"""
PDF Reader Script using PyPDF2
This script reads PDF files from the knowledge_base folder and extracts text content.
"""

import os
import sys
from pathlib import Path
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 is not installed. Please install it using: pip install PyPDF2")
    sys.exit(1)


def read_pdf(pdf_path):
    """
    Read a PDF file and extract text from all pages.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            print(f"Reading PDF: {os.path.basename(pdf_path)}")
            print(f"Number of pages: {len(pdf_reader.pages)}")
            print("-" * 50)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                text_content += f"\n--- Page {page_num} ---\n"
                text_content += page_text
                print(f"Processed page {page_num}")
            
            return text_content
            
    except FileNotFoundError:
        print(f"Error: File '{pdf_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None


def list_pdf_files(directory):
    """
    List all PDF files in the specified directory.
    
    Args:
        directory (str): Directory path to search for PDF files
        
    Returns:
        list: List of PDF file paths
    """
    pdf_files = []
    try:
        for file in os.listdir(directory):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(directory, file))
        return sorted(pdf_files)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return []


def main():
    """Main function to demonstrate PDF reading functionality."""
    
    # Define the knowledge_base directory path
    knowledge_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base')
    
    print("PDF Reader using PyPDF2")
    print("=" * 50)
    
    # List all PDF files in the knowledge_base directory
    pdf_files = list_pdf_files(knowledge_base_dir)
    
    if not pdf_files:
        print("No PDF files found in the knowledge_base directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"{i}. {os.path.basename(pdf_file)}")
    
    # Automatically read and print content from the first PDF file
    print("\n" + "="*60)
    print("AUTOMATICALLY READING FIRST PDF FILE")
    print("="*60)
    
    first_pdf = pdf_files[0]
    print(f"\nReading first file: {os.path.basename(first_pdf)}")
    text_content = read_pdf(first_pdf)
    
    if text_content:
        print("\nExtracted Text Content:")
        print("-" * 50)
        # Print first 2000 characters to avoid overwhelming output
        if len(text_content) > 2000:
            print(text_content[:2000])
            print(f"\n... (showing first 2000 characters out of {len(text_content)} total)")
        else:
            print(text_content)
        print("-" * 50)
    
    print("\nOptions:")
    print("1. Read a specific PDF file")
    print("2. Read all PDF files")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                # Read a specific PDF file
                print("\nSelect a PDF file to read:")
                for i, pdf_file in enumerate(pdf_files, 1):
                    print(f"{i}. {os.path.basename(pdf_file)}")
                
                file_choice = input(f"Enter file number (1-{len(pdf_files)}): ").strip()
                try:
                    file_index = int(file_choice) - 1
                    if 0 <= file_index < len(pdf_files):
                        selected_file = pdf_files[file_index]
                        text_content = read_pdf(selected_file)
                        if text_content:
                            print("\nExtracted Text:")
                            print("=" * 50)
                            print(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
                            
                            # Ask if user wants to save the extracted text
                            save_choice = input("\nDo you want to save the extracted text to a file? (y/n): ").strip().lower()
                            if save_choice == 'y':
                                output_file = f"extracted_text_{os.path.splitext(os.path.basename(selected_file))[0]}.txt"
                                with open(output_file, 'w', encoding='utf-8') as f:
                                    f.write(text_content)
                                print(f"Text saved to: {output_file}")
                    else:
                        print("Invalid file number.")
                except ValueError:
                    print("Please enter a valid number.")
                    
            elif choice == '2':
                # Read all PDF files
                print("\nReading all PDF files...")
                all_text = ""
                for pdf_file in pdf_files:
                    print(f"\nProcessing: {os.path.basename(pdf_file)}")
                    text_content = read_pdf(pdf_file)
                    if text_content:
                        all_text += f"\n\n{'='*60}\n"
                        all_text += f"FILE: {os.path.basename(pdf_file)}\n"
                        all_text += f"{'='*60}\n"
                        all_text += text_content
                
                if all_text:
                    print(f"\nTotal text extracted from {len(pdf_files)} files.")
                    save_choice = input("Do you want to save all extracted text to a file? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        output_file = "all_extracted_text.txt"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(all_text)
                        print(f"All text saved to: {output_file}")
                        
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
