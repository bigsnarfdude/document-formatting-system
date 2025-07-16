#!/usr/bin/env python3
"""
PDF to DOCX Conversion Helper
Provides guidance and tools for converting PDF documents to DOCX format.
"""

import sys
from pathlib import Path

def analyze_pdf_conversion_options():
    """Analyze options for converting PDFs to DOCX."""
    
    print("🔄 PDF to DOCX Conversion Options")
    print("=" * 40)
    
    print("\n1. 📱 Online Converters (Recommended for small files):")
    print("   • SmallPDF: https://smallpdf.com/pdf-to-word")
    print("   • ILovePDF: https://www.ilovepdf.com/pdf_to_word")
    print("   • PDF24: https://tools.pdf24.org/en/pdf-to-word")
    print("   • Pros: Easy, fast, good formatting preservation")
    print("   • Cons: File size limits, privacy concerns for sensitive docs")
    
    print("\n2. 🖥️ Desktop Software:")
    print("   • Adobe Acrobat Pro (Best quality)")
    print("   • Microsoft Word (Insert > Object > Text from File)")
    print("   • LibreOffice Writer (File > Open PDF)")
    print("   • Pros: Better control, works offline, handles large files")
    print("   • Cons: May require software purchase")
    
    print("\n3. 🐍 Python Libraries (Programmatic):")
    print("   • pdf2docx: pip install pdf2docx")
    print("   • pymupdf: pip install pymupdf")
    print("   • Pros: Automated, batch processing")
    print("   • Cons: Formatting may not be perfect")
    
    print("\n4. 🔧 Command Line Tools:")
    print("   • pandoc: brew install pandoc")
    print("   • LibreOffice headless mode")
    print("   • Pros: Scriptable, batch processing")
    print("   • Cons: Limited formatting preservation")

def create_conversion_script():
    """Create a Python script for automated PDF to DOCX conversion."""
    
    script_content = '''#!/usr/bin/env python3
"""
Automated PDF to DOCX Conversion
Uses pdf2docx library for conversion.
"""

import sys
from pathlib import Path

try:
    from pdf2docx import parse
except ImportError:
    print("❌ pdf2docx not installed. Run: pip install pdf2docx")
    sys.exit(1)

def convert_pdf_to_docx(pdf_path: str, docx_path: str = None):
    """Convert PDF to DOCX format."""
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    if docx_path is None:
        docx_path = pdf_file.with_suffix('.docx')
    
    print(f"🔄 Converting {pdf_file.name} to DOCX...")
    
    try:
        # Convert PDF to DOCX
        parse(pdf_path, str(docx_path), start=0, end=None)
        print(f"✅ Conversion complete: {docx_path}")
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def main():
    """Main conversion function."""
    if len(sys.argv) < 2:
        print("Usage: python convert_pdf.py <pdf_file> [output.docx]")
        return
    
    pdf_path = sys.argv[1]
    docx_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_pdf_to_docx(pdf_path, docx_path)

if __name__ == '__main__':
    main()
'''
    
    script_path = Path("convert_pdf_to_docx.py")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"📝 Created conversion script: {script_path}")
    print("Usage: python convert_pdf_to_docx.py <pdf_file> [output.docx]")

def main():
    """Main function."""
    
    print("🔄 PDF to DOCX Conversion Helper")
    print("=" * 50)
    
    watson_pdfs = [
        "/Users/vincent/Desktop/watson/DONE 777 FCTM Rev 10 (Entire Mnaual).pdf",
        "/Users/vincent/Desktop/watson/DONE 777 FM - Entire Manual.pdf", 
        "/Users/vincent/Desktop/watson/FA PPH Entire Manual.pdf"
    ]
    
    print(f"\n📋 Found {len(watson_pdfs)} PDF files to convert:")
    for pdf in watson_pdfs:
        if Path(pdf).exists():
            print(f"   ✅ {Path(pdf).name}")
        else:
            print(f"   ❌ {Path(pdf).name} (not found)")
    
    analyze_pdf_conversion_options()
    
    print(f"\n🎯 Recommended Workflow:")
    print("1. Convert DONE PDFs to DOCX using one of the methods above")
    print("2. Name converted files clearly (e.g., 'DONE_777_FM_formatted.docx')")
    print("3. Run training with original + converted pairs:")
    print()
    print("   python examples/train_from_examples.py \\")
    print('     --pair "777 FM - Entire Manual.docx" "DONE_777_FM_formatted.docx" \\')
    print('     --pair "777 FCTM Rev 10.docx" "DONE_777_FCTM_formatted.docx" \\')
    print("     --generate-rules")
    
    print(f"\n💡 Quick Start:")
    print("1. Install pdf2docx: pip install pdf2docx")
    
    create_conversion_script()
    
    print("\n2. Convert your PDFs:")
    for pdf in watson_pdfs:
        if Path(pdf).exists():
            output_name = Path(pdf).stem.replace("DONE ", "DONE_").replace(" ", "_") + "_formatted.docx"
            print(f'   python convert_pdf_to_docx.py "{pdf}" "{output_name}"')

if __name__ == '__main__':
    main()