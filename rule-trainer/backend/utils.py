import os
import re
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from werkzeug.utils import secure_filename
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, List
import hashlib
import uuid

try:
    from .models import DocumentContent, DocumentElement, ElementProperties, TextCase, Alignment
except ImportError:
    from models import DocumentContent, DocumentElement, ElementProperties, TextCase, Alignment

class DocumentProcessor:
    """Handles document parsing and property extraction"""
    
    def __init__(self):
        self.supported_types = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx
        }
        
        # Only add PDF support if PyMuPDF is available
        try:
            import fitz
            self.supported_types['application/pdf'] = self._process_pdf
        except ImportError:
            pass
    
    def process_file(self, file_path: str, content_type: str) -> DocumentContent:
        """Process a file and extract document content"""
        if content_type not in self.supported_types:
            raise ValueError(f"Unsupported file type: {content_type}")
        
        processor = self.supported_types[content_type]
        return processor(file_path)
    
    def _process_pdf(self, file_path: str) -> DocumentContent:
        """Process PDF file using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            elements = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    element = self._create_element_from_pdf_span(
                                        text, span, page_num + 1
                                    )
                                    elements.append(element)
            
            doc.close()
            
            return DocumentContent(
                title=os.path.basename(file_path),
                elements=elements
            )
            
        except ImportError:
            raise ValueError("PyMuPDF not installed. Please install with: pip install PyMuPDF")
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def _process_docx(self, file_path: str) -> DocumentContent:
        """Process DOCX file using python-docx"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            elements = []
            
            for i, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    element = self._create_element_from_docx_paragraph(text, paragraph, i)
                    elements.append(element)
            
            return DocumentContent(
                title=os.path.basename(file_path),
                elements=elements
            )
            
        except ImportError:
            raise ValueError("python-docx not installed. Please install with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to process DOCX: {str(e)}")
    
    def _create_element_from_pdf_span(self, text: str, span: Dict, page_num: int) -> DocumentElement:
        """Create document element from PDF span"""
        properties = ElementProperties(
            font_name=span.get("font", "Arial"),
            font_size=span.get("size", 12.0),
            is_bold=bool(span.get("flags", 0) & 2**4),
            is_italic=bool(span.get("flags", 0) & 2**1),
            rgb_color=self._parse_color(span.get("color", 0))
        )
        
        # Add semantic properties
        properties = self._enrich_properties(text, properties)
        
        return DocumentElement(
            id=str(uuid.uuid4()),
            text=text,
            properties=properties,
            page_number=page_num,
            position={
                "x": span.get("bbox", [0, 0, 0, 0])[0],
                "y": span.get("bbox", [0, 0, 0, 0])[1],
                "width": span.get("bbox", [0, 0, 0, 0])[2] - span.get("bbox", [0, 0, 0, 0])[0],
                "height": span.get("bbox", [0, 0, 0, 0])[3] - span.get("bbox", [0, 0, 0, 0])[1]
            }
        )
    
    def _create_element_from_docx_paragraph(self, text: str, paragraph, index: int) -> DocumentElement:
        """Create document element from DOCX paragraph"""
        # Extract formatting from first run
        run = paragraph.runs[0] if paragraph.runs else None
        
        properties = ElementProperties(
            font_name=run.font.name if run and run.font.name else "Arial",
            font_size=float(run.font.size.pt) if run and run.font.size else 12.0,
            is_bold=run.bold if run and run.bold is not None else False,
            is_italic=run.italic if run and run.italic is not None else False,
            is_underline=run.underline if run and run.underline else False,
            alignment=self._parse_alignment(paragraph.alignment)
        )
        
        # Add semantic properties
        properties = self._enrich_properties(text, properties)
        
        return DocumentElement(
            id=str(uuid.uuid4()),
            text=text,
            properties=properties,
            page_number=1  # DOCX doesn't have easy page detection
        )
    
    def _enrich_properties(self, text: str, properties: ElementProperties) -> ElementProperties:
        """Add semantic properties to element"""
        # Text case analysis
        if text.isupper():
            properties.text_case = TextCase.UPPER
        elif text.islower():
            properties.text_case = TextCase.LOWER
        elif text.istitle():
            properties.text_case = TextCase.TITLE
        
        # Content analysis
        properties.contains_code = bool(re.search(r'\(.*?\)', text))
        properties.is_date = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text))
        properties.is_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        properties.is_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text))
        properties.is_url = bool(re.search(r'https?://\S+', text))
        properties.starts_with_bullet = text.startswith(('•', '●', '○', '-'))
        properties.starts_with_number = bool(re.match(r'^\d+\.', text))
        properties.is_standalone = len(text.split()) <= 5 and not text.endswith('.')
        properties.word_count = len(text.split())
        
        return properties
    
    def _parse_color(self, color_int: int) -> List[int]:
        """Parse color integer to RGB list"""
        if color_int == 0:
            return [0, 0, 0]  # Black
        
        # Convert from BGR to RGB
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        return [r, g, b]
    
    def _parse_alignment(self, alignment) -> Alignment:
        """Parse alignment from docx alignment enum"""
        if alignment is None:
            return Alignment.LEFT
        
        alignment_map = {
            0: Alignment.LEFT,
            1: Alignment.CENTER,
            2: Alignment.RIGHT,
            3: Alignment.JUSTIFY
        }
        
        return alignment_map.get(alignment, Alignment.LEFT)

def validate_file_security(file: UploadFile):
    """Validate uploaded file for security"""
    # Check file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
    
    # Sanitize filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    secure_name = secure_filename(file.filename)
    if not secure_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    allowed_extensions = {'.pdf', '.docx'}
    file_ext = os.path.splitext(secure_name)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Supported types: {', '.join(allowed_extensions)}"
        )
    
    # MIME type validation would go here
    # Note: This requires the file content to be read, which is done in the main handler
    
    return secure_name

def generate_element_hash(element: DocumentElement) -> str:
    """Generate unique hash for document element"""
    content = f"{element.text}_{element.properties.font_name}_{element.properties.font_size}"
    return hashlib.md5(content.encode()).hexdigest()[:8]