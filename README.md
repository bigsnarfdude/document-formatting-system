# Non-Destructive Document Formatting System

A safety-first document formatting system that applies visual-only changes while preserving all content with zero modification risk.

## 🎯 Overview

This system processes Word documents to apply consistent formatting while guaranteeing that no content is modified. It uses advanced content fingerprinting, safety classification, and human-in-the-loop validation to ensure zero content risk.


## ✨ Key Features

- **🛡️ Zero Content Risk**: Advanced content preservation with SHA-256 fingerprinting
- **🤖 Smart Safety Classification**: Automatic detection of procedural, technical, numerical, and regulatory content
- **👁️ Human-in-the-Loop Validation**: Web-based interface for expert review and approval
- **🔄 Complete Rollback**: Full backup and audit trail for all operations
- **🎨 Visual-Only Formatting**: CSS-based styling that only affects presentation
- **📊 HTML Output**: Programmatically validatable output format

## 🏗️ Architecture

```
Input Document (.docx)
        ↓
Content Preservation Engine
    • SHA-256 Fingerprinting
    • Prohibited Zone Detection
    • Safety Classification
        ↓
Safe Formatting Engine
    • Content Extraction
    • Visual-Only CSS Application
    • HTML Generation
        ↓
Human Validation Interface
    • Side-by-Side Comparison
    • Approval/Rejection Workflow
    • Expert Review
        ↓
Rollback Manager & Audit
    • Document Backups
    • Complete Audit Trail
    • Rollback Capabilities
        ↓
Formatted Document (HTML)
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/bigsnarfdude/document-formatting-system
cd document-formatting-system

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Create Sample Documents

```bash
python examples/create_sample_documents.py
```

### Run Complete Demo

```bash
python examples/demo_complete_workflow.py
```

### Start Validation Server

```bash
python examples/run_validation_server.py
```

The validation interface will be available at `http://localhost:5000`

### Analyze a Document

```bash
python examples/analyze_document.py path/to/document.docx --detailed
```

## 📁 Project Structure

```
document-formatting-system/
├── src/
│   ├── content_preservation.py      # Content fingerprinting & safety
│   ├── safe_formatting.py          # HTML generation with visual formatting
│   ├── validation_interface.py     # Web-based human validation
│   └── rollback_manager.py         # Backup, rollback & audit
├── tests/
│   ├── test_content_preservation.py
│   ├── test_safe_formatting.py
│   ├── test_validation_interface.py
│   ├── test_rollback_manager.py
│   └── test_integration.py
├── examples/
│   ├── create_sample_documents.py  # Generate test documents
│   ├── demo_complete_workflow.py   # End-to-end demo
│   ├── run_validation_server.py    # Start validation UI
│   └── analyze_document.py         # Document analysis tool
└── requirements.txt
```

## 🔒 Safety Framework

### Content Safety Levels

- **🟢 SAFE_TO_MODIFY**: Regular text safe for formatting
- **🟡 REQUIRES_REVIEW**: Numerical content requiring human verification
- **🔴 CONTENT_CRITICAL**: Procedural, technical, or regulatory content that must not be modified

### Prohibited Content Patterns

The system automatically detects and protects:

- **Procedural Language**: Steps, warnings, instructions
- **Technical Terms**: API versions, protocols, product codes
- **Numerical Values**: Currency, measurements, dates, percentages
- **Regulatory Compliance**: Standards, certifications, requirements

### Content Preservation

- SHA-256 fingerprinting of all content
- Paragraph-level hash verification
- Numerical value extraction and protection
- Structure integrity validation

## 🖥️ Human Validation Interface

The web-based validation interface provides:

- **📋 Dashboard**: Overview of pending validations
- **🔍 Side-by-Side Comparison**: Original vs. processed content
- **🎨 Visual Highlighting**: Safety-critical content identification
- **✅ Approval Workflow**: Expert review and approval process
- **💬 Comment System**: Reviewer feedback and rationale
- **📊 Integrity Reports**: Content preservation verification

### Interface Features

- Responsive design for desktop and tablet use
- Real-time status updates
- Document download capabilities
- Comprehensive change summaries
- Safety violation detection

## 🔄 Rollback & Audit System

### Backup Management

- Automatic document backups before processing
- Configurable retention policies
- Fast rollback to any previous state
- Storage usage monitoring

### Audit Trail

Complete audit logging of:
- Document processing operations
- Validation submissions and responses
- Backup creation and rollback events
- User interactions and decisions

### Reporting

- Comprehensive audit reports
- Operation statistics
- Performance metrics
- Compliance documentation

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_content_preservation.py -v
pytest tests/test_integration.py -v

# Run with coverage
pytest --cov=src tests/
```

## 📖 Usage Examples

### Basic Document Processing

```python
from src.content_preservation import ContentPreservationEngine
from src.safe_formatting import SafeFormattingEngine

# Initialize engines
preservation = ContentPreservationEngine()
formatting = SafeFormattingEngine()

# Create content fingerprint
fingerprint = preservation.create_content_fingerprint("document.docx")

# Extract and format content
content = formatting.extract_content_safely("document.docx")
html = formatting.generate_safe_html(content)
```

### Validation Workflow

```python
from src.validation_interface import HumanValidationInterface

# Initialize validation interface
validator = HumanValidationInterface()

# Submit for validation
request_id = validator.submit_for_validation(
    document_path="document.docx",
    original_content=content,
    processed_html=html,
    changes_made=changes,
    fingerprint=fingerprint
)

# Start validation server
validator.run_server()
```

### Safety Analysis

```python
# Generate safety report
safety_report = preservation.get_safety_report("document.docx")

print(f"Safe to modify: {safety_report['safety_breakdown']['safe_to_modify']}")
print(f"Requires review: {safety_report['safety_breakdown']['requires_review']}")
print(f"Content critical: {safety_report['safety_breakdown']['content_critical']}")
```

## 🔧 Configuration

### Default Style Guide

The system includes a corporate style guide with:
- Professional fonts (Arial, sans-serif)
- Consistent spacing and margins
- Hierarchical heading styles
- Table formatting standards

### Custom Style Guides

Create custom formatting rules:

```python
from src.safe_formatting import SafeFormattingRule, ContentSafetyLevel

custom_rule = SafeFormattingRule(
    element_type='p',
    css_properties={
        'font-family': 'Times New Roman, serif',
        'font-size': '12px',
        'line-height': '1.5'
    },
    conditions=['is_body_text'],
    safety_level=ContentSafetyLevel.SAFE_TO_MODIFY
)
```

## 🛡️ Security Considerations

### Content Protection

- All critical content identified and preserved
- Numerical values tracked and verified
- Procedural language protection
- Technical specification preservation

### CSS Safety

- Only visual properties allowed
- Prohibited properties blocked
- No content modification capabilities
- No JavaScript execution

### Audit Security

- Immutable audit trails
- Cryptographic content hashes
- User action tracking
- Compliance reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions, issues, or contributions:

1. Check the existing issues in the repository
2. Create a new issue with detailed description
3. Include sample documents and error logs
4. Tag with appropriate labels

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with complete workflow
- Content preservation with SHA-256 fingerprinting
- HTML-based output with safety highlighting
- Human validation interface
- Complete rollback and audit system
- Comprehensive test suite

## 🎯 Roadmap

- [ ] Additional output formats (PDF, RTF)
- [ ] Advanced styling templates
- [ ] Integration with document management systems
- [ ] Machine learning for improved safety classification
- [ ] Real-time collaboration features
- [ ] Advanced analytics and reporting
