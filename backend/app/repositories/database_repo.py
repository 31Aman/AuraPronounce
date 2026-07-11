from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Type
from app.models.database import (
    User, Upload, Analysis, Scores, WordScore, Feedback, ConsentLog, AuditLog, DeletionRequest
)
from app.core.security import encrypt_data, decrypt_data, get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        if not email:
            return None
        return self.db.query(User).filter(User.email.ilike(email.strip())).first()

    def create_user(self, email: str, password_raw: str) -> User:
        db_user = User(
            email=email,
            hashed_password=get_password_hash(password_raw)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: str) -> bool:
        db_user = self.get_user(user_id)
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
            return True
        return False


class UploadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_upload(self, user_id: Optional[str], file_path: str, file_size: int, duration: float, mime_type: str) -> Upload:
        db_upload = Upload(
            user_id=user_id,
            file_path=file_path,
            file_size=file_size,
            duration=duration,
            mime_type=mime_type,
            status="pending"
        )
        self.db.add(db_upload)
        self.db.commit()
        self.db.refresh(db_upload)
        return db_upload

    def get_upload(self, upload_id: str) -> Optional[Upload]:
        return self.db.query(Upload).filter(Upload.id == upload_id).first()

    def update_status(self, upload_id: str, status: str) -> Optional[Upload]:
        db_upload = self.get_upload(upload_id)
        if db_upload:
            db_upload.status = status
            self.db.commit()
            self.db.refresh(db_upload)
        return db_upload


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_analysis(
        self,
        upload_id: str,
        overall_score: float,
        fluency_score: float,
        accuracy_score: float,
        completeness_score: float,
        confidence_score: float,
        suggestions: Optional[str],
        feedback_text: Optional[str],
        scores_data: dict,
        words_data: List[dict],
        feedback_data: List[dict]
    ) -> Analysis:
        analysis = Analysis(
            upload_id=upload_id,
            overall_score=overall_score,
            fluency_score=fluency_score,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            confidence_score=confidence_score,
            suggestions=suggestions,
            feedback_text=feedback_text
        )
        self.db.add(analysis)
        self.db.flush()  # Get analysis ID

        # Save acoustic scores breakdown
        db_scores = Scores(
            analysis_id=analysis.id,
            stress_score=scores_data.get("stress_score", 0.0),
            rhythm_score=scores_data.get("rhythm_score", 0.0),
            pauses_score=scores_data.get("pauses_score", 0.0),
            timing_score=scores_data.get("timing_score", 0.0),
            intonation_score=scores_data.get("intonation_score", 0.0),
            phoneme_similarity_score=scores_data.get("phoneme_similarity_score", 0.0)
        )
        self.db.add(db_scores)

        # Save word level scores
        for w in words_data:
            db_word = WordScore(
                analysis_id=analysis.id,
                word=w["word"],
                start_time=w["start_time"],
                end_time=w["end_time"],
                score=w["score"],
                is_mispronounced=w.get("is_mispronounced", False),
                is_unclear=w.get("is_unclear", False),
                phonemes_expected=w.get("phonemes_expected"),
                phonemes_actual=w.get("phonemes_actual")
            )
            self.db.add(db_word)

        # Save specific LLM recommendations
        for f in feedback_data:
            db_fb = Feedback(
                analysis_id=analysis.id,
                word=f["word"],
                issue=f["issue"],
                correct_pronunciation=f["correct_pronunciation"],
                suggestion=f["suggestion"],
                difficulty_level=f.get("difficulty_level", "Medium")
            )
            self.db.add(db_fb)

        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        return self.db.query(Analysis).filter(Analysis.id == analysis_id).first()

    def get_user_analyses(self, user_id: str) -> List[Analysis]:
        return (
            self.db.query(Analysis)
            .join(Upload)
            .filter(Upload.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .all()
        )

    def delete_analysis(self, analysis_id: str) -> bool:
        analysis = self.get_analysis(analysis_id)
        if analysis:
            self.db.delete(analysis)
            self.db.commit()
            return True
        return False


class ConsentLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, user_id: Optional[str], session_id: str, consented: bool, purpose: str, ip_address: str) -> ConsentLog:
        log = ConsentLog(
            user_id=user_id,
            session_id=session_id,
            consented=consented,
            purpose=purpose,
            ip_address_encrypted=encrypt_data(ip_address)
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, user_id: Optional[str], analysis_id: Optional[str], action: str, resource: str, details: str, ip_address: str) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            analysis_id=analysis_id,
            action=action,
            resource=resource,
            details_encrypted=encrypt_data(details),
            ip_address_encrypted=encrypt_data(ip_address)
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs(self, limit: int = 100) -> List[AuditLog]:
        # Return audit logs with details decrypted for display/admin
        logs = self.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        for log in logs:
            log.details_decrypted = decrypt_data(log.details_encrypted)
            log.ip_address_decrypted = decrypt_data(log.ip_address_encrypted)
        return logs


class DeletionRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, user_id: Optional[str], email: str) -> DeletionRequest:
        req = DeletionRequest(
            user_id=user_id,
            email_encrypted=encrypt_data(email),
            status="pending"
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def get_pending_requests(self) -> List[DeletionRequest]:
        reqs = self.db.query(DeletionRequest).filter(DeletionRequest.status == "pending").all()
        for req in reqs:
            req.email_decrypted = decrypt_data(req.email_encrypted)
        return reqs

    def complete_request(self, request_id: str) -> bool:
        req = self.db.query(DeletionRequest).filter(DeletionRequest.id == request_id).first()
        if req:
            req.status = "completed"
            req.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
