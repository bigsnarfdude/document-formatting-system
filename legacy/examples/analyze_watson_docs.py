#!/usr/bin/env python3
"""
Analyze Watson Document Collection
Identifies training pairs and analyzes document structure.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from docx import Document
import logging

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def analyze_docx_structure(file_path: str) -> Dict[str, Any]:
    """Analyze structure of a DOCX document."""
    try:
        doc = Document(file_path)
        
        # Basic document stats
        paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        total_paragraphs = len(paragraphs)
        
        # Analyze text lengths
        text_lengths = [len(p.text) for p in paragraphs]
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        # Classify paragraph types
        headings = []
        body_paragraphs = []
        
        for i, para in enumerate(paragraphs):
            text = para.text.strip()
            if not text:
                continue
                
            # Simple heading detection
            is_heading = (
                len(text) < 100 and 
                not text.endswith('.') and
                (text.isupper() or text.istitle() or any(char.isdigit() for char in text[:10]))
            )
            
            if is_heading:
                headings.append({
                    'index': i,
                    'text': text[:50] + '...' if len(text) > 50 else text,
                    'style': para.style.name if para.style else 'Unknown'
                })
            else:
                body_paragraphs.append(i)
        
        # Analyze fonts and formatting
        fonts_used = set()
        font_sizes = []
        
        for para in paragraphs:
            for run in para.runs:
                if run.font.name:
                    fonts_used.add(run.font.name)
                if run.font.size:
                    font_sizes.append(float(run.font.size.pt))
        
        # Calculate document fingerprint
        full_text = '\n'.join([p.text for p in paragraphs])
        word_count = len(full_text.split())
        
        return {
            'file_path': file_path,
            'total_paragraphs': total_paragraphs,
            'heading_count': len(headings),
            'body_paragraph_count': len(body_paragraphs),
            'sample_headings': headings[:5],  # First 5 headings
            'fonts_used': list(fonts_used),
            'font_sizes': font_sizes,
            'avg_font_size': sum(font_sizes) / len(font_sizes) if font_sizes else 0,
            'word_count': word_count,
            'avg_paragraph_length': avg_length,
            'document_fingerprint': hash(full_text) % 1000000  # Simple fingerprint
        }
        
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'analysis_failed': True
        }

def identify_document_pairs(watson_dir: str) -> List[Tuple[str, str]]:
    """Identify potential before/after document pairs."""
    watson_path = Path(watson_dir)
    
    if not watson_path.exists():
        print(f"❌ Directory not found: {watson_dir}")
        return []
    
    # Get all files
    all_files = list(watson_path.glob('*'))
    docx_files = [f for f in all_files if f.suffix.lower() == '.docx']
    pdf_files = [f for f in all_files if f.suffix.lower() == '.pdf']
    
    print(f"📁 Found {len(docx_files)} DOCX files and {len(pdf_files)} PDF files")
    
    # Try to match pairs based on naming patterns
    potential_pairs = []
    
    for docx_file in docx_files:
        # Look for corresponding "DONE" PDF
        base_name = docx_file.stem
        
        # Check for DONE version
        done_pdf = watson_path / f"DONE {base_name}.pdf"
        if done_pdf.exists():
            potential_pairs.append((str(docx_file), str(done_pdf)))
            print(f"✅ Found pair: {docx_file.name} → {done_pdf.name}")
            continue
        
        # Check for similar named PDF
        for pdf_file in pdf_files:
            if base_name.lower() in pdf_file.name.lower() and 'done' not in pdf_file.name.lower():
                potential_pairs.append((str(docx_file), str(pdf_file)))
                print(f"🔍 Potential pair: {docx_file.name} → {pdf_file.name}")
                break
    
    return potential_pairs

def main():
    """Main analysis function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("📊 Watson Document Collection Analysis")
    print("=" * 50)
    
    watson_dir = "/Users/vincent/Desktop/watson"
    
    # Identify document pairs
    print("\n🔍 Identifying Document Pairs...")
    pairs = identify_document_pairs(watson_dir)
    
    if not pairs:
        print("❌ No document pairs found!")
        return
    
    print(f"\n📋 Found {len(pairs)} potential training pairs:")
    
    # Analyze each document
    print("\n📖 Analyzing Document Structure...")
    
    for i, (original, formatted) in enumerate(pairs, 1):
        print(f"\n--- Pair {i} ---")
        print(f"Original: {Path(original).name}")
        print(f"Formatted: {Path(formatted).name}")
        
        # Analyze original (DOCX)
        if Path(original).suffix.lower() == '.docx':
            print("\n🔍 Original Document Analysis:")
            analysis = analyze_docx_structure(original)
            
            if 'error' not in analysis:
                print(f"   • Paragraphs: {analysis['total_paragraphs']}")
                print(f"   • Headings: {analysis['heading_count']}")
                print(f"   • Word count: {analysis['word_count']}")
                print(f"   • Fonts: {', '.join(analysis['fonts_used'][:3])}{'...' if len(analysis['fonts_used']) > 3 else ''}")
                print(f"   • Avg font size: {analysis['avg_font_size']:.1f}px")
                
                # Show sample headings
                if analysis['sample_headings']:
                    print("   • Sample headings:")
                    for heading in analysis['sample_headings']:
                        print(f"     - {heading['text']} (Style: {heading['style']})")
            else:
                print(f"   ❌ Analysis failed: {analysis['error']}")
        
        # Note about formatted version
        if Path(formatted).suffix.lower() == '.pdf':
            print("\n📄 Formatted Document (PDF):")
            print("   • Cannot extract detailed formatting from PDF")
            print("   • Would need manual conversion or OCR analysis")
            print("   • Recommend converting PDF back to DOCX for training")
    
    # Provide recommendations
    print(f"\n💡 Recommendations:")
    print("1. Convert 'DONE' PDF files back to DOCX format for detailed analysis")
    print("2. Use online PDF to DOCX converters or Adobe Acrobat")
    print("3. Alternatively, manually recreate formatting patterns in DOCX")
    print("4. Once you have DOCX pairs, run the training command:")
    print()
    print("   python examples/train_from_examples.py \\")
    for i, (original, _) in enumerate(pairs):
        original_name = Path(original).name
        formatted_name = original_name.replace('.docx', '_formatted.docx')
        print(f"     --pair \"{original}\" \"/path/to/{formatted_name}\" \\")
    print("     --generate-rules")
    
    # Show what we can analyze now
    docx_files = [p[0] for p in pairs if Path(p[0]).suffix.lower() == '.docx']
    if docx_files:
        print(f"\n🎯 Current Analysis Capability:")
        print(f"   • Can analyze {len(docx_files)} original documents")
        print(f"   • Can extract current formatting patterns")
        print(f"   • Cannot compare with formatted versions (PDFs)")
        print(f"   • Limited learning without DOCX formatted versions")

if __name__ == '__main__':
    main()