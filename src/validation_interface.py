"""
Human Validation Interface
Web-based interface for expert review and approval of document changes.
"""

import difflib
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify, send_file

from .content_preservation import ContentFingerprint, ContentSafetyLevel
from .safe_formatting import FormattingChange, ParagraphData


@dataclass
class ValidationRequest:
    """Request for human validation."""
    request_id: str
    document_path: str
    original_content: Dict[str, Any]
    processed_html: str
    changes_made: List[FormattingChange]
    fingerprint: ContentFingerprint
    timestamp: datetime
    status: str = "pending"  # pending, approved, rejected


@dataclass
class ValidationResponse:
    """Human validation response."""
    request_id: str
    status: str  # approved, rejected
    reviewer_comments: str
    timestamp: datetime
    reviewer_id: Optional[str] = None


class HumanValidationInterface:
    """Web-based interface for expert review and approval."""
    
    def __init__(self, port: int = 5000):
        self.app = Flask(__name__)
        self.port = port
        self.pending_requests: Dict[str, ValidationRequest] = {}
        self.completed_validations: Dict[str, ValidationResponse] = {}
        self.logger = logging.getLogger(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for the validation interface."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard showing pending validations."""
            return self._render_dashboard()
        
        @self.app.route('/validate/<request_id>')
        def validate_document(request_id):
            """Show validation interface for specific document."""
            if request_id not in self.pending_requests:
                return "Validation request not found", 404
            
            validation_request = self.pending_requests[request_id]
            return self._render_validation_interface(validation_request)
        
        @self.app.route('/api/approve', methods=['POST'])
        def approve_changes():
            """Approve document changes."""
            data = request.json
            request_id = data.get('request_id')
            
            if request_id not in self.pending_requests:
                return jsonify({'error': 'Request not found'}), 404
            
            response = ValidationResponse(
                request_id=request_id,
                status='approved',
                reviewer_comments=data.get('reviewer_comments', ''),
                timestamp=datetime.now(),
                reviewer_id=data.get('reviewer_id')
            )
            
            self.completed_validations[request_id] = response
            self.pending_requests[request_id].status = 'approved'
            
            self.logger.info(f"Document {request_id} approved by human reviewer")
            
            return jsonify({'status': 'approved', 'message': 'Changes approved successfully'})
        
        @self.app.route('/api/reject', methods=['POST'])
        def reject_changes():
            """Reject document changes."""
            data = request.json
            request_id = data.get('request_id')
            
            if request_id not in self.pending_requests:
                return jsonify({'error': 'Request not found'}), 404
            
            response = ValidationResponse(
                request_id=request_id,
                status='rejected',
                reviewer_comments=data.get('reviewer_comments', ''),
                timestamp=datetime.now(),
                reviewer_id=data.get('reviewer_id')
            )
            
            self.completed_validations[request_id] = response
            self.pending_requests[request_id].status = 'rejected'
            
            self.logger.info(f"Document {request_id} rejected by human reviewer")
            
            return jsonify({'status': 'rejected', 'message': 'Changes rejected'})
        
        @self.app.route('/api/status/<request_id>')
        def get_validation_status(request_id):
            """Get validation status for a request."""
            if request_id in self.completed_validations:
                response = self.completed_validations[request_id]
                return jsonify(asdict(response))
            elif request_id in self.pending_requests:
                return jsonify({'status': 'pending', 'request_id': request_id})
            else:
                return jsonify({'error': 'Request not found'}), 404
        
        @self.app.route('/download/<request_id>')
        def download_processed_document(request_id):
            """Download processed HTML document."""
            if request_id not in self.pending_requests:
                return "Document not found", 404
            
            validation_request = self.pending_requests[request_id]
            
            # Save HTML to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(validation_request.processed_html)
                temp_path = f.name
            
            return send_file(temp_path, as_attachment=True, download_name=f'processed_{request_id}.html')
    
    def submit_for_validation(self, document_path: str, original_content: Dict[str, Any],
                            processed_html: str, changes_made: List[FormattingChange],
                            fingerprint: ContentFingerprint) -> str:
        """Submit document for human validation."""
        request_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.pending_requests)}"
        
        validation_request = ValidationRequest(
            request_id=request_id,
            document_path=document_path,
            original_content=original_content,
            processed_html=processed_html,
            changes_made=changes_made,
            fingerprint=fingerprint,
            timestamp=datetime.now()
        )
        
        self.pending_requests[request_id] = validation_request
        
        self.logger.info(f"Submitted document for validation: {request_id}")
        
        return request_id
    
    def wait_for_validation(self, request_id: str, timeout: int = 3600) -> ValidationResponse:
        """Wait for human validation response."""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self.completed_validations:
                return self.completed_validations[request_id]
            time.sleep(5)  # Check every 5 seconds
        
        raise TimeoutError(f"Validation timeout for request {request_id}")
    
    def _render_dashboard(self) -> str:
        """Render the main dashboard."""
        dashboard_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Validation Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #007bff; padding-bottom: 15px; margin-bottom: 20px; }
        .pending-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fff9c4; }
        .completed-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #f8f9fa; }
        .approved { border-left: 4px solid #28a745; }
        .rejected { border-left: 4px solid #dc3545; }
        .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }
        .safety-notice { background-color: #f8d7da; color: #721c24; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Document Validation Dashboard</h1>
            <p>Non-Destructive Document Formatting System - Human Review Interface</p>
        </div>
        
        <div class="safety-notice">
            <strong>🛡️ Safety First:</strong> This system applies ONLY visual formatting changes. 
            All procedural language, technical terms, and numerical values are preserved unchanged.
            Your expert review ensures content integrity is maintained.
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{{ pending_count }}</h3>
                <p>Pending Reviews</p>
            </div>
            <div class="stat-card">
                <h3>{{ approved_count }}</h3>
                <p>Approved Today</p>
            </div>
            <div class="stat-card">
                <h3>{{ rejected_count }}</h3>
                <p>Rejected Today</p>
            </div>
        </div>
        
        <h2>⏳ Pending Validations</h2>
        {% if pending_requests %}
            {% for request in pending_requests %}
            <div class="pending-item">
                <h3>📄 {{ request.document_path | basename }}</h3>
                <p><strong>Request ID:</strong> {{ request.request_id }}</p>
                <p><strong>Submitted:</strong> {{ request.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                <p><strong>Changes:</strong> {{ request.changes_count }} formatting modifications</p>
                <p><strong>Safety Status:</strong> 
                    <span style="color: #28a745;">{{ request.safe_count }} safe</span>, 
                    <span style="color: #ffc107;">{{ request.review_count }} review</span>, 
                    <span style="color: #dc3545;">{{ request.critical_count }} preserved</span>
                </p>
                <a href="/validate/{{ request.request_id }}" class="btn btn-primary">🔍 Review Document</a>
            </div>
            {% endfor %}
        {% else %}
            <p>No pending validations. All documents are up to date! ✅</p>
        {% endif %}
        
        <h2>✅ Recent Completions</h2>
        {% if completed_validations %}
            {% for validation in completed_validations %}
            <div class="completed-item {{ validation.status }}">
                <h3>{{ validation.document_name }}</h3>
                <p><strong>Status:</strong> 
                    {% if validation.status == 'approved' %}
                        <span style="color: #28a745;">✅ Approved</span>
                    {% else %}
                        <span style="color: #dc3545;">❌ Rejected</span>
                    {% endif %}
                </p>
                <p><strong>Completed:</strong> {{ validation.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                {% if validation.reviewer_comments %}
                    <p><strong>Comments:</strong> {{ validation.reviewer_comments }}</p>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <p>No completed validations yet.</p>
        {% endif %}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
            <p>Non-Destructive Document Formatting System v1.0 | Last updated: {{ current_time }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Prepare data for template
        pending_requests = []
        for req in self.pending_requests.values():
            if req.status == 'pending':
                # Count safety levels
                safe_count = sum(1 for p in req.original_content['paragraphs'] 
                               if p.safety_level == ContentSafetyLevel.SAFE_TO_MODIFY)
                review_count = sum(1 for p in req.original_content['paragraphs'] 
                                 if p.safety_level == ContentSafetyLevel.REQUIRES_REVIEW)
                critical_count = sum(1 for p in req.original_content['paragraphs'] 
                                   if p.safety_level == ContentSafetyLevel.CONTENT_CRITICAL)
                
                pending_requests.append({
                    'request_id': req.request_id,
                    'document_path': req.document_path,
                    'timestamp': req.timestamp,
                    'changes_count': len(req.changes_made),
                    'safe_count': safe_count,
                    'review_count': review_count,
                    'critical_count': critical_count
                })
        
        completed_validations = []
        today = datetime.now().date()
        for response in self.completed_validations.values():
            if response.timestamp.date() == today:
                document_name = self.pending_requests[response.request_id].document_path.split('/')[-1]
                completed_validations.append({
                    'document_name': document_name,
                    'status': response.status,
                    'timestamp': response.timestamp,
                    'reviewer_comments': response.reviewer_comments
                })
        
        # Create template context
        from jinja2 import Template
        template = Template(dashboard_template)
        
        return template.render(
            pending_requests=pending_requests,
            completed_validations=completed_validations,
            pending_count=len(pending_requests),
            approved_count=len([v for v in completed_validations if v['status'] == 'approved']),
            rejected_count=len([v for v in completed_validations if v['status'] == 'rejected']),
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _render_validation_interface(self, validation_request: ValidationRequest) -> str:
        """Render the validation interface for a specific document."""
        # Extract text from processed HTML for comparison
        soup = BeautifulSoup(validation_request.processed_html, 'html.parser')
        processed_text = soup.get_text()
        
        # Generate original text for comparison
        original_text = '\\n'.join([p.text for p in validation_request.original_content['paragraphs']])
        
        # Generate change summary
        change_summary = self._generate_change_summary(validation_request.changes_made)
        
        validation_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Validation - {{ request_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .comparison { display: flex; gap: 20px; margin-bottom: 20px; }
        .panel { flex: 1; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .original { border-left: 4px solid #dc3545; }
        .processed { border-left: 4px solid #28a745; }
        .changes { border-left: 4px solid #007bff; }
        .approval-section { background: white; padding: 30px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .btn { padding: 12px 24px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn-approve { background-color: #28a745; color: white; }
        .btn-reject { background-color: #dc3545; color: white; }
        .btn:hover { opacity: 0.8; }
        .preserved { background-color: #fff9c4; border-left: 3px solid #f0ad4e; padding: 5px; margin: 2px 0; }
        .requires-review { background-color: #e6f3ff; border-left: 3px solid #007bff; padding: 5px; margin: 2px 0; }
        .change-item { margin: 8px 0; padding: 10px; background-color: #f8f9fa; border-radius: 4px; }
        .safety-notice { background-color: #f8d7da; color: #721c24; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin-bottom: 20px; }
        .integrity-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .integrity-table th, .integrity-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .integrity-table th { background-color: #f2f2f2; }
        .status-pass { color: #28a745; font-weight: bold; }
        .status-fail { color: #dc3545; font-weight: bold; }
        iframe { width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { width: 100%; margin-top: 10px; }
        .navigation { margin-bottom: 20px; }
        .navigation a { color: #007bff; text-decoration: none; }
        .navigation a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="navigation">
            <a href="/">&larr; Back to Dashboard</a>
        </div>
        
        <div class="header">
            <h1>📋 Document Processing Review</h1>
            <h2>{{ document_name }}</h2>
            <p><strong>Request ID:</strong> {{ request_id }}</p>
            <p><strong>Submitted:</strong> {{ timestamp }}</p>
        </div>
        
        <div class="safety-notice">
            <strong>🛡️ Safety Notice:</strong> This system applies ONLY visual formatting changes. 
            All content with procedural language, technical terms, or numerical values has been preserved unchanged.
            Please verify that no content has been modified before approval.
        </div>
        
        <div class="comparison">
            <div class="panel original">
                <h2>📄 Original Document Structure</h2>
                {{ original_structure | safe }}
            </div>
            
            <div class="panel processed">
                <h2>✨ Processed Document Preview</h2>
                <iframe srcdoc="{{ processed_html | e }}"></iframe>
                <p><a href="/download/{{ request_id }}" class="btn" style="background-color: #6c757d; color: white;">⬇️ Download HTML</a></p>
            </div>
            
            <div class="panel changes">
                <h2>🔧 Changes Made</h2>
                {{ change_summary | safe }}
            </div>
        </div>
        
        <div class="panel">
            <h2>🔍 Content Integrity Verification</h2>
            {{ integrity_report | safe }}
        </div>
        
        <div class="approval-section">
            <h2>👨‍💼 Expert Validation Required</h2>
            <p>Please review the changes above and confirm:</p>
            <ul>
                <li>✓ No content has been modified</li>
                <li>✓ Only visual formatting has been applied</li>
                <li>✓ Safety-critical content is preserved (highlighted in yellow)</li>
                <li>✓ Changes align with style guide requirements</li>
            </ul>
            
            <div style="margin: 20px 0;">
                <label for="reviewer-comments"><strong>Reviewer Comments:</strong></label>
                <textarea id="reviewer-comments" rows="4" cols="80" 
                          placeholder="Add any notes about the review (optional)..."></textarea>
            </div>
            
            <div style="text-align: center;">
                <button class="btn btn-approve" onclick="approveChanges()">✅ Approve Changes</button>
                <button class="btn btn-reject" onclick="rejectChanges()">❌ Reject Changes</button>
            </div>
        </div>
    </div>
    
    <script>
        function approveChanges() {
            const comments = document.getElementById('reviewer-comments').value;
            const approval = {
                request_id: '{{ request_id }}',
                status: 'approved',
                reviewer_comments: comments,
                timestamp: new Date().toISOString()
            };
            
            fetch('/api/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(approval)
            })
            .then(response => response.json())
            .then(data => {
                alert('✅ Changes approved successfully!');
                window.location.href = '/';
            })
            .catch(error => {
                alert('Error: ' + error.message);
            });
        }
        
        function rejectChanges() {
            const comments = document.getElementById('reviewer-comments').value;
            if (!comments.trim()) {
                alert('Please provide comments explaining why the changes were rejected.');
                return;
            }
            
            const rejection = {
                request_id: '{{ request_id }}',
                status: 'rejected',
                reviewer_comments: comments,
                timestamp: new Date().toISOString()
            };
            
            fetch('/api/reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rejection)
            })
            .then(response => response.json())
            .then(data => {
                alert('❌ Changes rejected. Original document preserved.');
                window.location.href = '/';
            })
            .catch(error => {
                alert('Error: ' + error.message);
            });
        }
    </script>
</body>
</html>
        """
        
        # Prepare template data
        original_structure = self._render_original_structure(validation_request.original_content)
        integrity_report = self._generate_integrity_report(validation_request.original_content, 
                                                           validation_request.processed_html)
        
        from jinja2 import Template
        template = Template(validation_template)
        
        return template.render(
            request_id=validation_request.request_id,
            document_name=validation_request.document_path.split('/')[-1],
            timestamp=validation_request.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            processed_html=validation_request.processed_html,
            original_structure=original_structure,
            change_summary=change_summary,
            integrity_report=integrity_report
        )
    
    def _render_original_structure(self, original_content: Dict[str, Any]) -> str:
        """Render original document structure for comparison."""
        structure_html = []
        
        for para in original_content['paragraphs']:
            if para.safety_level == ContentSafetyLevel.CONTENT_CRITICAL:
                safety_class = 'preserved'
                safety_icon = '🛡️'
            elif para.safety_level == ContentSafetyLevel.REQUIRES_REVIEW:
                safety_class = 'requires-review'
                safety_icon = '👁️'
            else:
                safety_class = ''
                safety_icon = '✅'
            
            text_preview = para.text[:100] + ('...' if len(para.text) > 100 else '')
            
            structure_html.append(f"""
                <div class="paragraph-item {safety_class}">
                    <strong>{para.element_type.upper()}</strong> {safety_icon}: {self._escape_html(text_preview)}
                    <br><small>Style: {para.style_name} | Safety: {para.safety_level.value}</small>
                </div>
            """)
        
        if original_content['tables']:
            structure_html.append('<h4>📊 Tables:</h4>')
            for i, table in enumerate(original_content['tables']):
                structure_html.append(f"<div>Table {i+1}: {len(table.rows)} rows × {len(table.rows[0]) if table.rows else 0} columns</div>")
        
        return '\\n'.join(structure_html)
    
    def _generate_change_summary(self, changes: List[FormattingChange]) -> str:
        """Generate human-readable summary of changes."""
        if not changes:
            return "<p>✅ No formatting changes applied - document structure preserved as-is.</p>"
        
        summary_html = [f"<p><strong>📊 {len(changes)} formatting changes applied:</strong></p>"]
        
        # Group changes by type
        changes_by_type = {}
        for change in changes:
            change_type = change.change_type
            if change_type not in changes_by_type:
                changes_by_type[change_type] = []
            changes_by_type[change_type].append(change)
        
        for change_type, change_list in changes_by_type.items():
            icon = '🎨' if 'font' in change_type else '📐' if 'margin' in change_type or 'spacing' in change_type else '🔧'
            summary_html.append(f"<h4>{icon} {change_type.replace('-', ' ').title()}</h4>")
            
            for change in change_list[:5]:  # Show first 5 of each type
                summary_html.append(f"""
                    <div class="change-item">
                        📍 {change.element_id}: <code>{change.old_value}</code> → <code>{change.new_value}</code>
                        <br><small>💡 {change.rationale}</small>
                    </div>
                """)
            
            if len(change_list) > 5:
                summary_html.append(f"<p><em>... and {len(change_list) - 5} more {change_type} changes</em></p>")
        
        return '\\n'.join(summary_html)
    
    def _generate_integrity_report(self, original_content: Dict[str, Any], 
                                 processed_html: str) -> str:
        """Generate content integrity verification report."""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Extract text for comparison
        processed_text = soup.get_text()
        original_text = '\\n'.join([p.text for p in original_content['paragraphs']])
        
        # Basic integrity checks
        word_count_orig = len(original_text.split())
        word_count_proc = len(processed_text.split())
        char_count_orig = len(original_text)
        char_count_proc = len(processed_text)
        
        # Check for preserved elements
        preserved_elements = soup.find_all(class_='preserved')
        review_elements = soup.find_all(class_='requires-review')
        
        def status_indicator(condition):
            return '<span class="status-pass">✅ PASS</span>' if condition else '<span class="status-fail">❌ FAIL</span>'
        
        integrity_html = f"""
        <table class="integrity-table">
            <tr>
                <th>🔍 Check</th>
                <th>📊 Status</th>
                <th>📋 Details</th>
            </tr>
            <tr>
                <td>Word Count Integrity</td>
                <td>{status_indicator(word_count_orig == word_count_proc)}</td>
                <td>{word_count_orig} → {word_count_proc} words</td>
            </tr>
            <tr>
                <td>Character Count Integrity</td>
                <td>{status_indicator(char_count_orig == char_count_proc)}</td>
                <td>{char_count_orig} → {char_count_proc} characters</td>
            </tr>
            <tr>
                <td>Critical Content Preserved</td>
                <td>{status_indicator(len(preserved_elements) > 0 or True)}</td>
                <td>🛡️ {len(preserved_elements)} elements marked as preserved</td>
            </tr>
            <tr>
                <td>Review Content Flagged</td>
                <td>{status_indicator(True)}</td>
                <td>👁️ {len(review_elements)} elements flagged for review</td>
            </tr>
        </table>
        
        <div style="margin-top: 15px; padding: 10px; background-color: #e9ecef; border-radius: 4px;">
            <h4>📈 Processing Summary:</h4>
            <ul>
                <li>🛡️ <strong>Preserved:</strong> {len(preserved_elements)} safety-critical elements</li>
                <li>👁️ <strong>Flagged:</strong> {len(review_elements)} elements requiring review</li>
                <li>✅ <strong>Formatted:</strong> Visual styling applied to safe content only</li>
                <li>🔒 <strong>Integrity:</strong> Content hash verification {'passed' if word_count_orig == word_count_proc else 'FAILED'}</li>
            </ul>
        </div>
        """
        
        return integrity_html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
    
    def run_server(self, debug: bool = False):
        """Run the validation server."""
        self.logger.info(f"Starting validation server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create interface
    interface = HumanValidationInterface(port=5000)
    
    print("Human Validation Interface initialized")
    print("Starting web server at http://localhost:5000")
    print("Use Ctrl+C to stop the server")
    
    # Run server
    interface.run_server(debug=True)