#!/usr/bin/env python3
"""
Simple startup script for the Document Formatting Rule Trainer
"""

import os
import sys
import uvicorn
from pathlib import Path

# Set up the path correctly
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Change to the project root
os.chdir(current_dir)

if __name__ == "__main__":
    print("🚀 Starting Document Formatting Rule Trainer")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000")
    print("📁 Working directory:", os.getcwd())
    
    try:
        # Import and run the app directly
        from backend.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid import issues
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure you've installed the requirements: pip install -r requirements.txt")