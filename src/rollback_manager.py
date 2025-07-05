"""
Rollback Manager and Audit System
Provides comprehensive rollback capabilities and audit trail for all document operations.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .content_preservation import ContentFingerprint
from .validation_interface import ValidationRequest, ValidationResponse


class OperationType(Enum):
    DOCUMENT_PROCESSED = "document_processed"
    VALIDATION_SUBMITTED = "validation_submitted"
    VALIDATION_APPROVED = "validation_approved"
    VALIDATION_REJECTED = "validation_rejected"
    ROLLBACK_EXECUTED = "rollback_executed"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    operation_id: str
    operation_type: OperationType
    timestamp: datetime
    document_path: str
    user_id: Optional[str]
    details: Dict[str, Any]
    fingerprint_before: Optional[str]
    fingerprint_after: Optional[str]


@dataclass
class BackupRecord:
    """Record of a document backup."""
    backup_id: str
    original_path: str
    backup_path: str
    timestamp: datetime
    fingerprint: ContentFingerprint
    operation_id: str
    metadata: Dict[str, Any]


class RollbackManager:
    """Manages document backups, rollbacks, and audit trails."""
    
    def __init__(self, backup_directory: str = "backups", audit_file: str = "audit_log.json"):
        self.backup_dir = Path(backup_directory)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.audit_file = Path(audit_file)
        self.audit_entries: List[AuditEntry] = []
        self.backup_records: Dict[str, BackupRecord] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Load existing audit data
        self._load_audit_data()
    
    def create_backup(self, document_path: str, fingerprint: ContentFingerprint, 
                     operation_id: str, metadata: Dict[str, Any] = None) -> str:
        """Create a backup of the original document."""
        try:
            source_path = Path(document_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Document not found: {document_path}")
            
            # Generate backup ID and path
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{operation_id}"
            backup_filename = f"{backup_id}_{source_path.name}"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup
            shutil.copy2(source_path, backup_path)
            
            # Create backup record
            backup_record = BackupRecord(
                backup_id=backup_id,
                original_path=str(source_path),
                backup_path=str(backup_path),
                timestamp=datetime.now(),
                fingerprint=fingerprint,
                operation_id=operation_id,
                metadata=metadata or {}
            )
            
            self.backup_records[backup_id] = backup_record
            
            # Log audit entry
            self._add_audit_entry(
                operation_id=operation_id,
                operation_type=OperationType.DOCUMENT_PROCESSED,
                document_path=document_path,
                details={
                    "backup_id": backup_id,
                    "backup_path": str(backup_path),
                    "metadata": metadata
                },
                fingerprint_before=fingerprint.full_text_hash
            )
            
            self.logger.info(f"Created backup {backup_id} for {document_path}")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {document_path}: {e}")
            raise
    
    def rollback_document(self, backup_id: str, target_path: str = None) -> bool:
        """Rollback document to a previous state."""
        try:
            if backup_id not in self.backup_records:
                raise ValueError(f"Backup not found: {backup_id}")
            
            backup_record = self.backup_records[backup_id]
            
            # Determine target path
            if target_path is None:
                target_path = backup_record.original_path
            
            # Verify backup file exists
            backup_path = Path(backup_record.backup_path)
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create backup of current state before rollback
            current_path = Path(target_path)
            if current_path.exists():
                rollback_backup_id = f"pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                rollback_backup_path = self.backup_dir / f"{rollback_backup_id}_{current_path.name}"
                shutil.copy2(current_path, rollback_backup_path)
                
                self.logger.info(f"Created pre-rollback backup: {rollback_backup_path}")
            
            # Perform rollback
            shutil.copy2(backup_path, target_path)
            
            # Generate rollback operation ID
            rollback_operation_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Log audit entry
            self._add_audit_entry(
                operation_id=rollback_operation_id,
                operation_type=OperationType.ROLLBACK_EXECUTED,
                document_path=target_path,
                details={
                    "restored_from_backup": backup_id,
                    "backup_timestamp": backup_record.timestamp.isoformat(),
                    "original_operation": backup_record.operation_id
                },
                fingerprint_after=backup_record.fingerprint.full_text_hash
            )
            
            self.logger.info(f"Successfully rolled back {target_path} to backup {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for backup {backup_id}: {e}")
            return False
    
    def log_validation_event(self, validation_request: ValidationRequest, 
                           validation_response: ValidationResponse = None):
        """Log validation events to audit trail."""
        try:
            if validation_response is None:
                # Validation submitted
                operation_type = OperationType.VALIDATION_SUBMITTED
                details = {
                    "request_id": validation_request.request_id,
                    "changes_count": len(validation_request.changes_made),
                    "fingerprint": asdict(validation_request.fingerprint)
                }
                fingerprint_before = validation_request.fingerprint.full_text_hash
                fingerprint_after = None
            else:
                # Validation completed
                if validation_response.status == "approved":
                    operation_type = OperationType.VALIDATION_APPROVED
                else:
                    operation_type = OperationType.VALIDATION_REJECTED
                
                details = {
                    "request_id": validation_request.request_id,
                    "reviewer_comments": validation_response.reviewer_comments,
                    "reviewer_id": validation_response.reviewer_id,
                    "changes_count": len(validation_request.changes_made)
                }
                fingerprint_before = validation_request.fingerprint.full_text_hash
                fingerprint_after = validation_request.fingerprint.full_text_hash if validation_response.status == "approved" else None
            
            self._add_audit_entry(
                operation_id=validation_request.request_id,
                operation_type=operation_type,
                document_path=validation_request.document_path,
                user_id=validation_response.reviewer_id if validation_response else None,
                details=details,
                fingerprint_before=fingerprint_before,
                fingerprint_after=fingerprint_after
            )
            
            self.logger.info(f"Logged validation event: {operation_type.value} for {validation_request.request_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to log validation event: {e}")
    
    def get_document_history(self, document_path: str) -> List[AuditEntry]:
        """Get complete audit history for a document."""
        return [entry for entry in self.audit_entries if entry.document_path == document_path]
    
    def get_available_backups(self, document_path: str) -> List[BackupRecord]:
        """Get all available backups for a document."""
        return [record for record in self.backup_records.values() 
                if record.original_path == document_path]
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Clean up backups older than specified days."""
        try:
            cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
            cleaned_count = 0
            
            backups_to_remove = []
            for backup_id, record in self.backup_records.items():
                if record.timestamp.timestamp() < cutoff_date:
                    backup_path = Path(record.backup_path)
                    if backup_path.exists():
                        backup_path.unlink()
                        self.logger.debug(f"Removed old backup: {backup_path}")
                    
                    backups_to_remove.append(backup_id)
                    cleaned_count += 1
            
            # Remove from records
            for backup_id in backups_to_remove:
                del self.backup_records[backup_id]
            
            self.logger.info(f"Cleaned up {cleaned_count} old backups")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def generate_audit_report(self, document_path: str = None, 
                            days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 60 * 60)
            
            # Filter entries
            if document_path:
                relevant_entries = [e for e in self.audit_entries 
                                  if e.document_path == document_path and 
                                     e.timestamp.timestamp() > cutoff_date]
            else:
                relevant_entries = [e for e in self.audit_entries 
                                  if e.timestamp.timestamp() > cutoff_date]
            
            # Calculate statistics
            operation_counts = {}
            for entry in relevant_entries:
                op_type = entry.operation_type.value
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            
            # Get backup statistics
            active_backups = len([r for r in self.backup_records.values() 
                                if r.timestamp.timestamp() > cutoff_date])
            
            report = {
                "report_period": {
                    "days_back": days_back,
                    "start_date": datetime.fromtimestamp(cutoff_date).isoformat(),
                    "end_date": datetime.now().isoformat()
                },
                "scope": {
                    "document_path": document_path or "All documents",
                    "total_entries": len(relevant_entries)
                },
                "operation_summary": operation_counts,
                "backup_summary": {
                    "active_backups": active_backups,
                    "total_backup_storage": self._calculate_backup_storage()
                },
                "recent_activities": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "operation": entry.operation_type.value,
                        "document": Path(entry.document_path).name,
                        "user": entry.user_id or "System",
                        "details": entry.details
                    }
                    for entry in sorted(relevant_entries, key=lambda x: x.timestamp, reverse=True)[:10]
                ]
            }
            
            self.logger.info(f"Generated audit report: {len(relevant_entries)} entries over {days_back} days")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate audit report: {e}")
            return {"error": str(e)}
    
    def _add_audit_entry(self, operation_id: str, operation_type: OperationType,
                        document_path: str, details: Dict[str, Any],
                        user_id: str = None, fingerprint_before: str = None,
                        fingerprint_after: str = None):
        """Add entry to audit log."""
        entry = AuditEntry(
            operation_id=operation_id,
            operation_type=operation_type,
            timestamp=datetime.now(),
            document_path=document_path,
            user_id=user_id,
            details=details,
            fingerprint_before=fingerprint_before,
            fingerprint_after=fingerprint_after
        )
        
        self.audit_entries.append(entry)
        self._save_audit_data()
    
    def _load_audit_data(self):
        """Load existing audit data from file."""
        try:
            if self.audit_file.exists():
                with open(self.audit_file, 'r') as f:
                    data = json.load(f)
                
                # Load audit entries
                for entry_data in data.get('audit_entries', []):
                    entry = AuditEntry(
                        operation_id=entry_data['operation_id'],
                        operation_type=OperationType(entry_data['operation_type']),
                        timestamp=datetime.fromisoformat(entry_data['timestamp']),
                        document_path=entry_data['document_path'],
                        user_id=entry_data.get('user_id'),
                        details=entry_data['details'],
                        fingerprint_before=entry_data.get('fingerprint_before'),
                        fingerprint_after=entry_data.get('fingerprint_after')
                    )
                    self.audit_entries.append(entry)
                
                # Load backup records
                for backup_data in data.get('backup_records', []):
                    from .content_preservation import ContentFingerprint
                    fp_data = backup_data['fingerprint']
                    fingerprint = ContentFingerprint(
                        full_text_hash=fp_data['full_text_hash'],
                        paragraph_hashes=fp_data['paragraph_hashes'],
                        structure_hash=fp_data['structure_hash'],
                        word_count=fp_data['word_count'],
                        character_count=fp_data['character_count'],
                        numerical_values=fp_data['numerical_values'],
                        timestamp=datetime.fromisoformat(fp_data['timestamp'])
                    )
                    
                    record = BackupRecord(
                        backup_id=backup_data['backup_id'],
                        original_path=backup_data['original_path'],
                        backup_path=backup_data['backup_path'],
                        timestamp=datetime.fromisoformat(backup_data['timestamp']),
                        fingerprint=fingerprint,
                        operation_id=backup_data['operation_id'],
                        metadata=backup_data['metadata']
                    )
                    self.backup_records[record.backup_id] = record
                
                self.logger.info(f"Loaded {len(self.audit_entries)} audit entries and {len(self.backup_records)} backup records")
                
        except Exception as e:
            self.logger.warning(f"Could not load existing audit data: {e}")
    
    def _save_audit_data(self):
        """Save audit data to file."""
        try:
            data = {
                'audit_entries': [],
                'backup_records': []
            }
            
            # Save audit entries
            for entry in self.audit_entries:
                data['audit_entries'].append({
                    'operation_id': entry.operation_id,
                    'operation_type': entry.operation_type.value,
                    'timestamp': entry.timestamp.isoformat(),
                    'document_path': entry.document_path,
                    'user_id': entry.user_id,
                    'details': entry.details,
                    'fingerprint_before': entry.fingerprint_before,
                    'fingerprint_after': entry.fingerprint_after
                })
            
            # Save backup records
            for record in self.backup_records.values():
                data['backup_records'].append({
                    'backup_id': record.backup_id,
                    'original_path': record.original_path,
                    'backup_path': record.backup_path,
                    'timestamp': record.timestamp.isoformat(),
                    'fingerprint': asdict(record.fingerprint),
                    'operation_id': record.operation_id,
                    'metadata': record.metadata
                })
            
            with open(self.audit_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save audit data: {e}")
    
    def _calculate_backup_storage(self) -> str:
        """Calculate total backup storage used."""
        try:
            total_size = 0
            for record in self.backup_records.values():
                backup_path = Path(record.backup_path)
                if backup_path.exists():
                    total_size += backup_path.stat().st_size
            
            # Convert to human readable format
            if total_size > 1024**3:  # GB
                return f"{total_size / (1024**3):.2f} GB"
            elif total_size > 1024**2:  # MB
                return f"{total_size / (1024**2):.2f} MB"
            elif total_size > 1024:  # KB
                return f"{total_size / 1024:.2f} KB"
            else:
                return f"{total_size} bytes"
                
        except Exception as e:
            self.logger.error(f"Failed to calculate backup storage: {e}")
            return "Unknown"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create rollback manager
    rollback_manager = RollbackManager()
    
    print("Rollback Manager initialized")
    print(f"Backup directory: {rollback_manager.backup_dir}")
    print(f"Audit entries loaded: {len(rollback_manager.audit_entries)}")
    print(f"Backup records loaded: {len(rollback_manager.backup_records)}")
    
    # Generate sample audit report
    report = rollback_manager.generate_audit_report(days_back=7)
    print(f"\nAudit Report (7 days):")
    print(f"Total entries: {report['scope']['total_entries']}")
    print(f"Operations: {report['operation_summary']}")
    print(f"Active backups: {report['backup_summary']['active_backups']}")