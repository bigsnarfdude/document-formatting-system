"""
Test Rollback Manager and Audit System
Tests for backup, rollback, and audit functionality.
"""

import pytest
import tempfile
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.rollback_manager import (
    RollbackManager,
    AuditEntry,
    BackupRecord,
    OperationType
)
from src.content_preservation import ContentFingerprint
from src.validation_interface import ValidationRequest, ValidationResponse


class TestRollbackManager:
    """Test the rollback manager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def rollback_manager(self, temp_dir):
        """Create a rollback manager with temporary directories."""
        backup_dir = Path(temp_dir) / "backups"
        audit_file = Path(temp_dir) / "audit.json"
        return RollbackManager(str(backup_dir), str(audit_file))
    
    @pytest.fixture
    def sample_document(self, temp_dir):
        """Create a sample document for testing."""
        doc_path = Path(temp_dir) / "test_document.txt"
        doc_path.write_text("This is a test document with important content.")
        return str(doc_path)
    
    @pytest.fixture
    def sample_fingerprint(self):
        """Create a sample content fingerprint."""
        return ContentFingerprint(
            full_text_hash="test_hash_123",
            paragraph_hashes=["para_hash_1", "para_hash_2"],
            structure_hash="struct_hash_456",
            word_count=10,
            character_count=50,
            numerical_values=["$100.00"],
            timestamp=datetime.now()
        )
    
    def test_backup_creation(self, rollback_manager, sample_document, sample_fingerprint):
        """Test creating backups of documents."""
        operation_id = "test_operation_001"
        metadata = {"user": "test_user", "reason": "formatting update"}
        
        backup_id = rollback_manager.create_backup(
            document_path=sample_document,
            fingerprint=sample_fingerprint,
            operation_id=operation_id,
            metadata=metadata
        )
        
        # Verify backup was created
        assert backup_id.startswith("backup_")
        assert operation_id in backup_id
        assert backup_id in rollback_manager.backup_records
        
        # Verify backup record
        backup_record = rollback_manager.backup_records[backup_id]
        assert backup_record.original_path == sample_document
        assert backup_record.operation_id == operation_id
        assert backup_record.fingerprint == sample_fingerprint
        assert backup_record.metadata == metadata
        
        # Verify backup file exists
        backup_path = Path(backup_record.backup_path)
        assert backup_path.exists()
        
        # Verify backup content matches original
        original_content = Path(sample_document).read_text()
        backup_content = backup_path.read_text()
        assert original_content == backup_content
        
        # Verify audit entry was created
        assert len(rollback_manager.audit_entries) > 0
        audit_entry = rollback_manager.audit_entries[-1]
        assert audit_entry.operation_type == OperationType.DOCUMENT_PROCESSED
        assert audit_entry.operation_id == operation_id
    
    def test_rollback_functionality(self, rollback_manager, sample_document, sample_fingerprint, temp_dir):
        """Test rolling back documents to previous state."""
        # Create backup
        operation_id = "test_operation_001"
        backup_id = rollback_manager.create_backup(
            document_path=sample_document,
            fingerprint=sample_fingerprint,
            operation_id=operation_id
        )
        
        # Modify the original document
        modified_content = "This document has been modified!"
        Path(sample_document).write_text(modified_content)
        
        # Verify document was modified
        assert Path(sample_document).read_text() == modified_content
        
        # Perform rollback
        success = rollback_manager.rollback_document(backup_id, sample_document)
        assert success == True
        
        # Verify document was restored
        restored_content = Path(sample_document).read_text()
        assert restored_content == "This is a test document with important content."
        assert restored_content != modified_content
        
        # Verify rollback audit entry was created
        rollback_entries = [entry for entry in rollback_manager.audit_entries 
                          if entry.operation_type == OperationType.ROLLBACK_EXECUTED]
        assert len(rollback_entries) > 0
        
        rollback_entry = rollback_entries[-1]
        assert rollback_entry.document_path == sample_document
        assert rollback_entry.details['restored_from_backup'] == backup_id
    
    def test_validation_event_logging(self, rollback_manager, sample_fingerprint):
        """Test logging of validation events."""
        # Create mock validation request
        validation_request = ValidationRequest(
            request_id="val_001",
            document_path="/test/document.docx",
            original_content={'paragraphs': [], 'tables': []},
            processed_html="<html></html>",
            changes_made=[],
            fingerprint=sample_fingerprint,
            timestamp=datetime.now()
        )
        
        # Log validation submission
        rollback_manager.log_validation_event(validation_request)
        
        # Verify submission was logged
        submission_entries = [entry for entry in rollback_manager.audit_entries 
                            if entry.operation_type == OperationType.VALIDATION_SUBMITTED]
        assert len(submission_entries) > 0
        
        submission_entry = submission_entries[-1]
        assert submission_entry.operation_id == "val_001"
        assert submission_entry.document_path == "/test/document.docx"
        
        # Create mock validation response (approval)
        validation_response = ValidationResponse(
            request_id="val_001",
            status="approved",
            reviewer_comments="Looks good",
            timestamp=datetime.now(),
            reviewer_id="reviewer_123"
        )
        
        # Log validation approval
        rollback_manager.log_validation_event(validation_request, validation_response)
        
        # Verify approval was logged
        approval_entries = [entry for entry in rollback_manager.audit_entries 
                          if entry.operation_type == OperationType.VALIDATION_APPROVED]
        assert len(approval_entries) > 0
        
        approval_entry = approval_entries[-1]
        assert approval_entry.operation_id == "val_001"
        assert approval_entry.user_id == "reviewer_123"
        assert "Looks good" in approval_entry.details['reviewer_comments']
    
    def test_document_history_retrieval(self, rollback_manager, sample_document, sample_fingerprint):
        """Test retrieving audit history for specific documents."""
        # Create multiple operations for the document
        operation_ids = ["op_001", "op_002", "op_003"]
        
        for op_id in operation_ids:
            rollback_manager.create_backup(
                document_path=sample_document,
                fingerprint=sample_fingerprint,
                operation_id=op_id
            )
        
        # Retrieve document history
        history = rollback_manager.get_document_history(sample_document)
        
        # Verify all operations are in history
        assert len(history) >= len(operation_ids)
        
        operation_ids_in_history = {entry.operation_id for entry in history}
        for op_id in operation_ids:
            assert op_id in operation_ids_in_history
        
        # Verify all entries are for the correct document
        for entry in history:
            assert entry.document_path == sample_document
    
    def test_available_backups_retrieval(self, rollback_manager, sample_document, sample_fingerprint):
        """Test retrieving available backups for a document."""
        # Create multiple backups
        backup_ids = []
        for i in range(3):
            backup_id = rollback_manager.create_backup(
                document_path=sample_document,
                fingerprint=sample_fingerprint,
                operation_id=f"op_{i:03d}"
            )
            backup_ids.append(backup_id)
        
        # Retrieve available backups
        backups = rollback_manager.get_available_backups(sample_document)
        
        # Verify all backups are returned
        assert len(backups) == 3
        
        backup_ids_retrieved = {backup.backup_id for backup in backups}
        for backup_id in backup_ids:
            assert backup_id in backup_ids_retrieved
        
        # Verify all backups are for the correct document
        for backup in backups:
            assert backup.original_path == sample_document
    
    def test_old_backup_cleanup(self, rollback_manager, sample_document, sample_fingerprint, temp_dir):
        """Test cleanup of old backups."""
        # Create backups with different timestamps
        old_backup_id = rollback_manager.create_backup(
            document_path=sample_document,
            fingerprint=sample_fingerprint,
            operation_id="old_operation"
        )
        
        # Manually modify timestamp to be old
        old_backup = rollback_manager.backup_records[old_backup_id]
        old_backup.timestamp = datetime.now() - timedelta(days=35)  # 35 days old
        
        # Create recent backup
        recent_backup_id = rollback_manager.create_backup(
            document_path=sample_document,
            fingerprint=sample_fingerprint,
            operation_id="recent_operation"
        )
        
        # Verify both backups exist
        assert len(rollback_manager.backup_records) >= 2
        assert old_backup_id in rollback_manager.backup_records
        assert recent_backup_id in rollback_manager.backup_records
        
        # Cleanup old backups (30 day retention)
        cleaned_count = rollback_manager.cleanup_old_backups(retention_days=30)
        
        # Verify old backup was cleaned up
        assert cleaned_count >= 1
        assert old_backup_id not in rollback_manager.backup_records
        assert recent_backup_id in rollback_manager.backup_records
    
    def test_audit_report_generation(self, rollback_manager, sample_document, sample_fingerprint):
        """Test generation of audit reports."""
        # Create some operations
        operation_ids = ["report_op_001", "report_op_002"]
        for op_id in operation_ids:
            rollback_manager.create_backup(
                document_path=sample_document,
                fingerprint=sample_fingerprint,
                operation_id=op_id
            )
        
        # Generate overall report
        overall_report = rollback_manager.generate_audit_report(days_back=7)
        
        # Verify report structure
        assert 'report_period' in overall_report
        assert 'scope' in overall_report
        assert 'operation_summary' in overall_report
        assert 'backup_summary' in overall_report
        assert 'recent_activities' in overall_report
        
        # Verify report contains our operations
        assert overall_report['scope']['total_entries'] >= len(operation_ids)
        
        # Generate document-specific report
        doc_report = rollback_manager.generate_audit_report(
            document_path=sample_document,
            days_back=7
        )
        
        # Verify document-specific report
        assert doc_report['scope']['document_path'] == sample_document
        assert doc_report['scope']['total_entries'] >= len(operation_ids)
        
        # Verify recent activities
        recent_activities = doc_report['recent_activities']
        assert len(recent_activities) >= len(operation_ids)
        
        # Verify activity structure
        for activity in recent_activities[:2]:  # Check first 2
            assert 'timestamp' in activity
            assert 'operation' in activity
            assert 'document' in activity
            assert 'user' in activity
            assert 'details' in activity
    
    def test_audit_data_persistence(self, rollback_manager, sample_document, sample_fingerprint, temp_dir):
        """Test saving and loading of audit data."""
        # Create some operations
        operation_id = "persistence_test_001"
        backup_id = rollback_manager.create_backup(
            document_path=sample_document,
            fingerprint=sample_fingerprint,
            operation_id=operation_id
        )
        
        # Verify data exists
        assert len(rollback_manager.audit_entries) > 0
        assert len(rollback_manager.backup_records) > 0
        assert backup_id in rollback_manager.backup_records
        
        # Create new manager instance (should load existing data)
        backup_dir = Path(temp_dir) / "backups"
        audit_file = Path(temp_dir) / "audit.json"
        new_manager = RollbackManager(str(backup_dir), str(audit_file))
        
        # Verify data was loaded
        assert len(new_manager.audit_entries) > 0
        assert len(new_manager.backup_records) > 0
        assert backup_id in new_manager.backup_records
        
        # Verify specific data integrity
        loaded_backup = new_manager.backup_records[backup_id]
        original_backup = rollback_manager.backup_records[backup_id]
        
        assert loaded_backup.backup_id == original_backup.backup_id
        assert loaded_backup.original_path == original_backup.original_path
        assert loaded_backup.operation_id == original_backup.operation_id
    
    def test_backup_storage_calculation(self, rollback_manager, sample_document, sample_fingerprint):
        """Test calculation of backup storage usage."""
        # Create backups
        for i in range(3):
            rollback_manager.create_backup(
                document_path=sample_document,
                fingerprint=sample_fingerprint,
                operation_id=f"storage_test_{i:03d}"
            )
        
        # Calculate storage (private method test)
        storage_info = rollback_manager._calculate_backup_storage()
        
        # Verify storage calculation returns a string with units
        assert isinstance(storage_info, str)
        assert any(unit in storage_info for unit in ['bytes', 'KB', 'MB', 'GB'])
    
    def test_error_handling(self, rollback_manager):
        """Test error handling in rollback manager."""
        # Test backup creation with non-existent file
        fake_fingerprint = ContentFingerprint(
            full_text_hash="fake", paragraph_hashes=[], structure_hash="fake",
            word_count=0, character_count=0, numerical_values=[], timestamp=datetime.now()
        )
        
        with pytest.raises(FileNotFoundError):
            rollback_manager.create_backup(
                document_path="/non/existent/file.txt",
                fingerprint=fake_fingerprint,
                operation_id="error_test"
            )
        
        # Test rollback with non-existent backup
        success = rollback_manager.rollback_document("non_existent_backup")
        assert success == False
        
        # Test empty document history
        history = rollback_manager.get_document_history("/non/existent/document.txt")
        assert len(history) == 0
        
        # Test empty backup list
        backups = rollback_manager.get_available_backups("/non/existent/document.txt")
        assert len(backups) == 0


class TestAuditDataStructures:
    """Test audit entry and backup record data structures."""
    
    def test_audit_entry_creation(self):
        """Test creation of audit entries."""
        entry = AuditEntry(
            operation_id="test_op_001",
            operation_type=OperationType.DOCUMENT_PROCESSED,
            timestamp=datetime.now(),
            document_path="/test/doc.txt",
            user_id="test_user",
            details={"change_count": 5},
            fingerprint_before="hash_before",
            fingerprint_after="hash_after"
        )
        
        assert entry.operation_id == "test_op_001"
        assert entry.operation_type == OperationType.DOCUMENT_PROCESSED
        assert entry.user_id == "test_user"
        assert entry.details["change_count"] == 5
    
    def test_backup_record_creation(self):
        """Test creation of backup records."""
        fingerprint = ContentFingerprint(
            full_text_hash="test", paragraph_hashes=[], structure_hash="test",
            word_count=0, character_count=0, numerical_values=[], timestamp=datetime.now()
        )
        
        record = BackupRecord(
            backup_id="backup_001",
            original_path="/original/path.txt",
            backup_path="/backup/path.txt",
            timestamp=datetime.now(),
            fingerprint=fingerprint,
            operation_id="op_001",
            metadata={"user": "test"}
        )
        
        assert record.backup_id == "backup_001"
        assert record.original_path == "/original/path.txt"
        assert record.operation_id == "op_001"
        assert record.metadata["user"] == "test"
    
    def test_operation_type_enum(self):
        """Test operation type enumeration."""
        # Verify all expected operation types exist
        expected_types = [
            "DOCUMENT_PROCESSED",
            "VALIDATION_SUBMITTED", 
            "VALIDATION_APPROVED",
            "VALIDATION_REJECTED",
            "ROLLBACK_EXECUTED"
        ]
        
        for type_name in expected_types:
            assert hasattr(OperationType, type_name)
            op_type = getattr(OperationType, type_name)
            assert isinstance(op_type, OperationType)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])