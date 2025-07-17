# Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python start_server.py
```

### 3. Open the Application
Visit: **http://localhost:8000**

## 🎯 How to Use

### Step 1: Load a Document
- Click "Load Example" for a demo document
- Or click "Upload Document" to upload your own DOCX file

### Step 2: Create Rules
1. Click on any paragraph in the **Original Document** (left pane)
2. Type your formatting intent in the chat (e.g., "This should be a heading")
3. Press Enter to generate a rule
4. Watch the **Target Document** (middle pane) update with the applied rule

### Step 3: Manage Rules
- View all created rules in the **Rules Panel** (right pane)
- Edit or delete rules as needed
- Export rules as JSON when finished

## 💡 Example Commands

- **"This should be a heading"** → Creates heading rule
- **"Make this a bullet list"** → Creates list rule  
- **"This is body text"** → Creates body text rule
- **"Remove this content"** → Creates filter rule

## 📊 Features

- ✅ **Visual Training**: Side-by-side document comparison
- ✅ **Smart Rules**: Template-based rule generation
- ✅ **Real-time Preview**: See changes immediately
- ✅ **Rule Management**: Edit, delete, organize rules
- ✅ **Export**: Download rules as JSON

## 🔧 Optional Features

Install these for enhanced functionality:

```bash
# For PDF support
pip install PyMuPDF

# For enhanced file validation
pip install python-magic

# For AI-powered rule generation
pip install google-generativeai
export GOOGLE_API_KEY=your_api_key
```

## 🌐 API Documentation

Visit: **http://localhost:8000/docs** for interactive API documentation

## 🎉 Ready to Train!

The application is now ready for document formatting rule training!