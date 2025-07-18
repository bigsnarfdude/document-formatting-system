# Document Formatting Rule Trainer

A human-in-the-loop tool for creating document formatting rules through visual training with LLM based chat.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server (choose one method):**
   
   **Method 1: Simple startup (recommended)**
   ```bash
   python start_server.py
   ```
   
   **Method 2: Direct backend**
   ```bash
   python backend/main.py
   ```

3. **Open the application:**
   ```bash
   open http://localhost:8000
   ```

## Project Structure

```
rule-trainer/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── utils.py             # Document processing utilities
│   └── rule_engine.py       # Rule generation logic
├── frontend/
│   ├── index.html           # Main interface
│   ├── styles.css           # Styling
│   └── app.js               # Frontend logic
├── examples/
│   └── example_document.json # Sample document data
└── requirements.txt         # Python dependencies
```

## Features

- **Visual Document Comparison**: Side-by-side view of original vs formatted documents
- **Natural Language Rule Creation**: Chat interface for defining formatting rules
- **Real-time Rule Application**: Immediate visual feedback when rules are created
- **Rule Management**: Edit, delete, and organize formatting rules
- **Export Functionality**: Download rules as JSON for production use

## API Endpoints

- `POST /upload` - Upload and process documents
- `GET /load-example` - Load example document
- `POST /generate-rule` - Create formatting rule from user intent
- `POST /export-rules` - Export rule set as JSON

## Security Features

- File type validation with MIME type checking
- Filename sanitization
- Size limits (10MB)
- Ephemeral file storage
