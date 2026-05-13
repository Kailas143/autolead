from sqlalchemy.orm import Session
from app.models.audit import SystemLog, AIUsage
from typing import Optional, Any, Dict
import traceback

class AuditService:
    def log_error(self, db: Session, category: str, message: str, error: Optional[Exception] = None):
        """
        Record a system error with optional stack trace.
        """
        details = {}
        if error:
            details["error_type"] = type(error).__name__
            details["error_message"] = str(error)
            details["stack_trace"] = traceback.format_exc()

        log = SystemLog(
            level="ERROR",
            category=category,
            message=message,
            details=details
        )
        db.add(log)
        db.commit()

    def log_info(self, db: Session, category: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Record a system event.
        """
        log = SystemLog(
            level="INFO",
            category=category,
            message=message,
            details=details
        )
        db.add(log)
        db.commit()

    def track_ai_usage(
        self, 
        db: Session, 
        user_id: int, 
        model_name: str, 
        prompt_tokens: int, 
        completion_tokens: int, 
        task_type: str
    ):
        """
        Track token usage for AI operations.
        """
        usage = AIUsage(
            user_id=user_id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            task_type=task_type
        )
        db.add(usage)
        db.commit()

audit_service = AuditService()
