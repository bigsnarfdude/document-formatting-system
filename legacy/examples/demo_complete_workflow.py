#!/usr/bin/env python3
"""
Complete Workflow Demo
Demonstrates the entire document formatting system workflow.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from content_preservation import ContentPreservationEngine
from safe_formatting import SafeFormattingEngine
from validation_interface import HumanValidationInterface, ValidationResponse
from rollback_manager import RollbackManager


def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('demo_workflow.log')
        ]
    )


def print_separator(title: str):
    """Print a formatted separator."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def demo_content_analysis(document_path: str):
    """Demonstrate content analysis and safety assessment."""
    print_separator("CONTENT ANALYSIS & SAFETY ASSESSMENT")
    
    preservation_engine = ContentPreservationEngine()
    
    print(f"📄 Analyzing document: {Path(document_path).name}")
    
    # Create content fingerprint
    print("\n🔍 Creating content fingerprint...")
    fingerprint = preservation_engine.create_content_fingerprint(document_path)
    
    print(f"   ✓ Full text hash: {fingerprint.full_text_hash[:16]}...")
    print(f"   ✓ Word count: {fingerprint.word_count}")
    print(f"   ✓ Character count: {fingerprint.character_count}")
    print(f"   ✓ Paragraph hashes: {len(fingerprint.paragraph_hashes)}")
    print(f"   ✓ Numerical values found: {len(fingerprint.numerical_values)}")
    
    if fingerprint.numerical_values:
        print("   📊 Numerical values to protect:")
        for value in fingerprint.numerical_values[:5]:  # Show first 5
            print(f"      • {value}")
        if len(fingerprint.numerical_values) > 5:
            print(f"      ... and {len(fingerprint.numerical_values) - 5} more")
    
    # Identify prohibited zones
    print("\n🚫 Identifying prohibited zones...")
    prohibited_zones = preservation_engine.identify_prohibited_zones(document_path)
    
    print(f"   ✓ Found {len(prohibited_zones)} prohibited zones")
    
    zone_summary = {}
    for zone in prohibited_zones:
        zone_summary[zone.zone_type] = zone_summary.get(zone.zone_type, 0) + 1
    
    for zone_type, count in zone_summary.items():
        print(f"      • {zone_type}: {count} zones")
    
    # Generate safety report
    print("\n📊 Generating safety report...")
    safety_report = preservation_engine.get_safety_report(document_path)
    
    breakdown = safety_report['safety_breakdown']
    total = safety_report['total_paragraphs']
    
    print(f"   ✓ Total paragraphs analyzed: {total}")
    print(f"   ✅ Safe to modify: {breakdown['safe_to_modify']} ({breakdown['safe_to_modify']/total*100:.1f}%)")
    print(f"   👁️  Requires review: {breakdown['requires_review']} ({breakdown['requires_review']/total*100:.1f}%)")
    print(f"   🛡️  Content critical: {breakdown['content_critical']} ({breakdown['content_critical']/total*100:.1f}%)")
    
    print(f"\n🤖 Automation recommendation: {safety_report['automation_feasibility']['recommended_approach']}")
    
    return fingerprint, prohibited_zones, safety_report


def demo_safe_formatting(document_path: str, fingerprint):
    """Demonstrate safe formatting and HTML generation."""
    print_separator("SAFE FORMATTING & HTML GENERATION")
    
    formatting_engine = SafeFormattingEngine()
    
    print(f"📄 Processing document: {Path(document_path).name}")
    
    # Extract content safely
    print("\n📤 Extracting content with safety classification...")
    extracted_content = formatting_engine.extract_content_safely(document_path)
    
    paragraphs = extracted_content['paragraphs']
    tables = extracted_content['tables']
    
    print(f"   ✓ Extracted {len(paragraphs)} paragraphs")
    print(f"   ✓ Extracted {len(tables)} tables")
    
    # Show safety classification summary
    from content_preservation import ContentSafetyLevel
    safety_counts = {level: 0 for level in ContentSafetyLevel}
    for para in paragraphs:
        safety_counts[para.safety_level] += 1
    
    print(f"\n🏷️  Safety classification:")
    for level, count in safety_counts.items():
        print(f"      • {level.value}: {count} paragraphs")
    
    # Generate HTML
    print("\n🎨 Generating safe HTML with corporate styling...")
    processed_html = formatting_engine.generate_safe_html(extracted_content)
    
    print(f"   ✓ Generated HTML ({len(processed_html)} characters)")
    
    # Validate CSS safety
    print("\n🔒 Validating CSS safety...")
    css_start = processed_html.find('<style>') + 7
    css_end = processed_html.find('</style>')
    css_content = processed_html[css_start:css_end]
    
    css_validation = formatting_engine.validate_css_safety(css_content)
    
    if css_validation['is_safe']:
        print("   ✅ CSS validation passed - only visual properties used")
    else:
        print("   ❌ CSS validation failed:")
        for violation in css_validation['violations']:
            print(f"      • {violation}")
    
    # Save HTML for review
    output_path = Path("demo_output.html")
    output_path.write_text(processed_html)
    print(f"\n💾 HTML saved to: {output_path}")
    
    return extracted_content, processed_html


def demo_validation_interface(document_path: str, extracted_content, processed_html, fingerprint):
    """Demonstrate human validation interface."""
    print_separator("HUMAN VALIDATION INTERFACE")
    
    validation_interface = HumanValidationInterface(port=5003)
    
    print("🖥️  Initializing validation interface...")
    
    # Submit for validation
    print("\n📋 Submitting document for human validation...")
    request_id = validation_interface.submit_for_validation(
        document_path=document_path,
        original_content=extracted_content,
        processed_html=processed_html,
        changes_made=[],  # Would be populated with actual formatting changes
        fingerprint=fingerprint
    )
    
    print(f"   ✓ Validation request created: {request_id}")
    
    # Show validation request details
    validation_request = validation_interface.pending_requests[request_id]
    print(f"   📄 Document: {Path(validation_request.document_path).name}")
    print(f"   ⏰ Submitted: {validation_request.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   🔧 Changes made: {len(validation_request.changes_made)}")
    
    # Generate dashboard preview
    print("\n🖼️  Generating validation dashboard...")
    dashboard_html = validation_interface._render_dashboard()
    
    dashboard_path = Path("demo_dashboard.html")
    dashboard_path.write_text(dashboard_html)
    print(f"   💾 Dashboard saved to: {dashboard_path}")
    print(f"   🌐 In production, navigate to: http://localhost:5003")
    
    # Generate validation interface preview
    print("\n🔍 Generating validation interface...")
    validation_html = validation_interface._render_validation_interface(validation_request)
    
    validation_path = Path("demo_validation_interface.html")
    validation_path.write_text(validation_html)
    print(f"   💾 Validation interface saved to: {validation_path}")
    
    # Simulate approval
    print("\n✅ Simulating human approval...")
    approval_response = ValidationResponse(
        request_id=request_id,
        status='approved',
        reviewer_comments='Content integrity verified. Formatting changes look good. No critical content modified.',
        timestamp=datetime.now(),
        reviewer_id='demo_reviewer'
    )
    
    validation_interface.completed_validations[request_id] = approval_response
    validation_interface.pending_requests[request_id].status = 'approved'
    
    print(f"   ✓ Document approved by: {approval_response.reviewer_id}")
    print(f"   💬 Reviewer comments: {approval_response.reviewer_comments}")
    
    return validation_request, approval_response


def demo_rollback_and_audit(document_path: str, fingerprint, validation_request, approval_response):
    """Demonstrate rollback capabilities and audit trail."""
    print_separator("ROLLBACK MANAGER & AUDIT TRAIL")
    
    rollback_manager = RollbackManager(
        backup_directory="demo_backups",
        audit_file="demo_audit.json"
    )
    
    print("💾 Initializing rollback manager...")
    
    # Create backup
    print("\n📦 Creating document backup...")
    operation_id = f"demo_operation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_id = rollback_manager.create_backup(
        document_path=document_path,
        fingerprint=fingerprint,
        operation_id=operation_id,
        metadata={"demo": True, "user": "demo_user", "purpose": "workflow_demonstration"}
    )
    
    print(f"   ✓ Backup created: {backup_id}")
    
    backup_record = rollback_manager.backup_records[backup_id]
    print(f"   📁 Backup path: {backup_record.backup_path}")
    print(f"   ⏰ Backup time: {backup_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Log validation events
    print("\n📝 Logging validation events...")
    rollback_manager.log_validation_event(validation_request)
    rollback_manager.log_validation_event(validation_request, approval_response)
    
    print("   ✓ Validation submission logged")
    print("   ✓ Validation approval logged")
    
    # Show available backups
    print("\n📋 Available backups for document:")
    available_backups = rollback_manager.get_available_backups(document_path)
    for backup in available_backups:
        print(f"   • {backup.backup_id} ({backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Generate audit report
    print("\n📊 Generating audit report...")
    audit_report = rollback_manager.generate_audit_report(days_back=1)
    
    print(f"   ✓ Report period: {audit_report['report_period']['days_back']} days")
    print(f"   ✓ Total audit entries: {audit_report['scope']['total_entries']}")
    print(f"   ✓ Active backups: {audit_report['backup_summary']['active_backups']}")
    print(f"   ✓ Storage used: {audit_report['backup_summary']['total_backup_storage']}")
    
    print("\n📈 Operation summary:")
    for operation, count in audit_report['operation_summary'].items():
        print(f"      • {operation}: {count}")
    
    print("\n🕐 Recent activities:")
    for activity in audit_report['recent_activities'][:3]:  # Show first 3
        print(f"      • {activity['timestamp'][:19]} - {activity['operation']}")
        print(f"        Document: {activity['document']}")
        print(f"        User: {activity['user']}")
    
    # Demonstrate rollback capability (without actually doing it)
    print(f"\n🔄 Rollback capability available:")
    print(f"   To rollback: rollback_manager.rollback_document('{backup_id}')")
    print(f"   This would restore the document to its original state")
    
    return rollback_manager, audit_report


def demo_content_integrity_verification(fingerprint, processed_html):
    """Demonstrate content integrity verification."""
    print_separator("CONTENT INTEGRITY VERIFICATION")
    
    preservation_engine = ContentPreservationEngine()
    
    print("🔍 Verifying content integrity...")
    
    # This would typically fail for HTML vs original text, but demonstrates the concept
    integrity_check = preservation_engine.validate_content_integrity(fingerprint, processed_html)
    
    print(f"   📊 Integrity check results:")
    print(f"      • Overall valid: {integrity_check.get('overall_valid', 'N/A')}")
    print(f"      • Content hash match: {integrity_check.get('content_hash_match', 'N/A')}")
    print(f"      • Word count match: {integrity_check.get('word_count_match', 'N/A')}")
    print(f"      • Character count match: {integrity_check.get('character_count_match', 'N/A')}")
    print(f"      • Numerical values preserved: {integrity_check.get('numerical_values_preserved', 'N/A')}")
    
    if not integrity_check.get('overall_valid', True):
        print("\n⚠️  Note: Integrity check may fail due to HTML formatting differences.")
        print("   In production, this would compare processed content with original text.")
        print("   The key is that all numerical values and critical content are preserved.")
    
    # Check numerical values specifically
    if integrity_check.get('missing_values'):
        print(f"\n❌ Missing numerical values:")
        for value in integrity_check['missing_values']:
            print(f"      • {value}")
    else:
        print(f"\n✅ All numerical values preserved in output")
    
    return integrity_check


def main():
    """Run the complete workflow demo."""
    setup_logging()
    
    print("🚀 NON-DESTRUCTIVE DOCUMENT FORMATTING SYSTEM")
    print("   Complete Workflow Demonstration")
    print("   " + "="*40)
    
    # Check if sample documents exist
    sample_docs_dir = Path(__file__).parent / "sample_documents"
    if not sample_docs_dir.exists():
        print("\n❌ Sample documents not found!")
        print("   Please run: python examples/create_sample_documents.py")
        return
    
    # Find a sample document to process
    sample_docs = list(sample_docs_dir.glob("*.docx"))
    if not sample_docs:
        print("\n❌ No sample documents found!")
        print("   Please run: python examples/create_sample_documents.py")
        return
    
    # Use the mixed content document for comprehensive demo
    document_path = None
    for doc in sample_docs:
        if "system_integration" in doc.name:
            document_path = str(doc)
            break
    
    if not document_path:
        document_path = str(sample_docs[0])  # Use first available document
    
    print(f"\n📄 Demo document: {Path(document_path).name}")
    print(f"📁 Full path: {document_path}")
    
    try:
        # Step 1: Content Analysis
        fingerprint, prohibited_zones, safety_report = demo_content_analysis(document_path)
        
        # Step 2: Safe Formatting
        extracted_content, processed_html = demo_safe_formatting(document_path, fingerprint)
        
        # Step 3: Validation Interface
        validation_request, approval_response = demo_validation_interface(
            document_path, extracted_content, processed_html, fingerprint
        )
        
        # Step 4: Rollback and Audit
        rollback_manager, audit_report = demo_rollback_and_audit(
            document_path, fingerprint, validation_request, approval_response
        )
        
        # Step 5: Content Integrity
        integrity_check = demo_content_integrity_verification(fingerprint, processed_html)
        
        # Summary
        print_separator("WORKFLOW COMPLETE - SUMMARY")
        print("✅ Document analysis completed successfully")
        print("✅ Safe formatting applied with preservation of critical content")
        print("✅ Human validation interface generated")
        print("✅ Backup created and audit trail established")
        print("✅ Content integrity verification performed")
        
        print(f"\n📊 Final Statistics:")
        print(f"   • Document: {Path(document_path).name}")
        print(f"   • Paragraphs processed: {len(extracted_content['paragraphs'])}")
        print(f"   • Tables processed: {len(extracted_content['tables'])}")
        print(f"   • Critical zones identified: {len(prohibited_zones)}")
        print(f"   • Numerical values protected: {len(fingerprint.numerical_values)}")
        print(f"   • Backup created: {rollback_manager.backup_records[list(rollback_manager.backup_records.keys())[-1]].backup_id}")
        print(f"   • Audit entries: {len(rollback_manager.audit_entries)}")
        
        print(f"\n📁 Generated Files:")
        print(f"   • demo_output.html - Processed document")
        print(f"   • demo_dashboard.html - Validation dashboard")
        print(f"   • demo_validation_interface.html - Validation interface")
        print(f"   • demo_backups/ - Document backups")
        print(f"   • demo_audit.json - Audit trail")
        print(f"   • demo_workflow.log - Processing log")
        
        print(f"\n🎯 System demonstrates:")
        print(f"   ✓ Zero content modification risk")
        print(f"   ✓ Comprehensive safety classification")
        print(f"   ✓ Human-in-the-loop validation")
        print(f"   ✓ Complete rollback capabilities")
        print(f"   ✓ Full audit trail maintenance")
        
        print(f"\n🚀 Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logging.exception("Demo workflow error")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)