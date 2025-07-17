# Legacy HTML-Based Document Formatting System

This directory contains the original HTML-based document formatting system we are working on DOCX-focused approach for now. 

## ⚠️ Legacy Status

This system is **deprecated** and maintained for reference only. For current document formatting, use the main system in the parent directory.

## 🏗️ Legacy Architecture

The legacy system used an HTML-based approach with the following components:

### Core Components
- **src/content_preservation.py**: Content fingerprinting & safety
- **src/safe_formatting.py**: HTML generation with visual formatting
- **src/validation_interface.py**: Web-based human validation
- **src/rollback_manager.py**: Backup, rollback & audit

### Testing
- **tests/**: Comprehensive test suite for HTML-based processing
- **examples/**: HTML-based examples and demonstrations

### Dependencies
- **requirements.txt**: Full dependencies including Flask, BeautifulSoup4, lxml
- **setup.py**: Original package setup for HTML-based system

## 🔄 Migration Path

If you were using the legacy system, migrate to the new DOCX-focused system:

### Old Approach (Legacy)
```bash
# HTML-based processing
python examples/demo_complete_workflow.py
python examples/run_validation_server.py
```

### New Approach (Current)
```bash
# DOCX-based processing
python multi_stage_formatter.py
python pattern_based_formatter.py
python overnight_llm_formatter.py
```

## 🚀 Why the Change?

The new DOCX-focused system provides:
- **Native DOCX Processing**: No HTML conversion needed
- **Better Performance**: Direct document manipulation
- **Simpler Workflow**: No web interface required
- **Improved Accuracy**: AI-powered classification
- **Easier Deployment**: Fewer dependencies

## 📚 Legacy Documentation

The legacy system documentation includes:
- HTML-based workflow examples
- Flask web interface setup
- Content safety framework
- Rollback and audit capabilities

## 🔧 Running Legacy System

If you need to run the legacy system:

```bash
cd legacy/

# Install legacy dependencies
pip install -r requirements.txt

# Install legacy package
pip install -e .

# Run legacy examples
python examples/demo_complete_workflow.py
python examples/run_validation_server.py
```

## 🎯 Current System Benefits

The current system (parent directory) offers:
- **3-Stage Filtering**: Systematic content cleaning
- **Multiple Approaches**: Multi-stage, pattern-based, LLM-powered
- **Better Results**: 69 paragraph gap vs 108 original
- **Easier Setup**: Minimal dependencies
- **Production Ready**: Tested and optimized

## 📄 License

This legacy system is licensed under the MIT License - see the LICENSE file for details.

## 🔄 Support

For legacy system issues, please migrate to the current system in the parent directory. The legacy system is no longer actively maintained.
