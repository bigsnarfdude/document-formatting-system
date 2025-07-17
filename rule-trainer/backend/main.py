from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Any

try:
    # Try relative imports first (when run as module)
    from .models import (
        DocumentContent, 
        RuleGenerationRequest, 
        RuleGenerationResponse,
        RuleExportRequest,
        FileUploadResponse,
        ErrorResponse
    )
    from .utils import DocumentProcessor, validate_file_security
    from .rule_engine import RuleEngine
except ImportError:
    # Fall back to absolute imports (when run directly)
    from models import (
        DocumentContent, 
        RuleGenerationRequest, 
        RuleGenerationResponse,
        RuleExportRequest,
        FileUploadResponse,
        ErrorResponse
    )
    from utils import DocumentProcessor, validate_file_security
    from rule_engine import RuleEngine

app = FastAPI(
    title="Document Formatting Rule Trainer",
    description="A human-in-the-loop tool for creating document formatting rules",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
rule_engine = RuleEngine()

# Serve static files
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
async def root():
    """Root endpoint redirects to frontend"""
    frontend_index = os.path.join(frontend_dir, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    else:
        return {"message": "Frontend not found. Please run from project root directory."}

@app.get("/styles.css")
async def get_styles():
    """Serve CSS file"""
    css_path = os.path.join(frontend_dir, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    else:
        return {"error": "CSS file not found"}

@app.get("/app.js")
async def get_app_js():
    """Serve JavaScript file"""
    js_path = os.path.join(frontend_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    else:
        return {"error": "JavaScript file not found"}

@app.get("/debug.css")
async def get_debug_css():
    """Serve debug CSS file"""
    css_path = os.path.join(frontend_dir, "debug.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    else:
        return {"error": "Debug CSS file not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/load-example")
async def load_example() -> DocumentContent:
    """Load example document for demo purposes"""
    try:
        # Try multiple possible locations for the example file
        possible_paths = [
            "examples/example_document.json",
            "../examples/example_document.json",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "example_document.json")
        ]
        
        example_data = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    example_data = json.load(f)
                break
        
        if example_data:
            return DocumentContent(**example_data)
        else:
            raise FileNotFoundError("Example file not found")
    except FileNotFoundError:
        # Create a simple example if file doesn't exist
        example = DocumentContent(
            title="Example Policy Document",
            elements=[
                {
                    "id": "elem_1",
                    "text": "EMPLOYMENT POLICIES",
                    "properties": {
                        "font_name": "Arial",
                        "font_size": 16.0,
                        "is_bold": True,
                        "text_case": "UPPER",
                        "is_standalone": True,
                        "word_count": 2
                    }
                },
                {
                    "id": "elem_2", 
                    "text": "This section covers all employment-related policies.",
                    "properties": {
                        "font_name": "Arial",
                        "font_size": 12.0,
                        "word_count": 7
                    }
                },
                {
                    "id": "elem_3",
                    "text": "HIRING PROCEDURES (RC-THPPH-001)",
                    "properties": {
                        "font_name": "Arial",
                        "font_size": 14.0,
                        "is_bold": True,
                        "contains_code": True,
                        "word_count": 3
                    }
                }
            ]
        )
        return example

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """Upload and process a document file"""
    try:
        # Security validation
        validate_file_security(file)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Process document
            document = document_processor.process_file(tmp_file.name, file.content_type)
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return FileUploadResponse(
                document=document,
                success=True,
                message=f"Successfully processed {file.filename}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )

@app.post("/generate-rule")
async def generate_rule(request: RuleGenerationRequest) -> RuleGenerationResponse:
    """Generate a formatting rule from user intent"""
    try:
        response = await rule_engine.generate_rule(request.element, request.intent)
        return response
        
    except Exception as e:
        return RuleGenerationResponse(
            type="error",
            message=f"Failed to generate rule: {str(e)}"
        )

@app.post("/export-rules")
async def export_rules(request: RuleExportRequest):
    """Export rules as downloadable JSON file"""
    try:
        export_data = {
            "rules": [rule.dict() for rule in request.rules],
            "exported_at": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(export_data, tmp_file, indent=2)
            tmp_file.flush()
            
            return FileResponse(
                tmp_file.name,
                media_type="application/json",
                filename="formatting_rules.json",
                background=None  # Keep file until download completes
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export rules: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=exc.status_code
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

# Catch-all route for static files (must be last)
@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    """Serve static files from frontend directory"""
    # Only serve specific file types for security
    allowed_extensions = {'.css', '.js', '.html', '.ico', '.png', '.jpg', '.svg'}
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=404, detail="File type not allowed")
    
    file_path = os.path.join(frontend_dir, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # Set appropriate media type
        media_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.html': 'text/html',
            '.ico': 'image/x-icon',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml'
        }
        media_type = media_types.get(file_extension, 'text/plain')
        return FileResponse(file_path, media_type=media_type)
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    print("🚀 Starting Document Formatting Rule Trainer")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000")
    
    # Change to parent directory for proper file paths
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    uvicorn.run(
        app,  # Use app directly instead of string
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid module issues
        log_level="info"
    )