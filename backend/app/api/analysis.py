from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from celery.result import AsyncResult
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.database import User
from app.repositories.database_repo import (
    UploadRepository, AnalysisRepository, AuditLogRepository,
    DeletionRequestRepository, UserRepository
)
from app.worker.tasks import analyze_audio_task

router = APIRouter()


class AnalyzeRequest(BaseModel):
    upload_id: str
    reference_text: Optional[str] = None


class UserFeedbackRequest(BaseModel):
    analysis_id: str
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None


class DeletionRequestModel(BaseModel):
    email: str


# Schemas for API responses
class ScoreBreakdownSchema(BaseModel):
    stress_score: float
    rhythm_score: float
    pauses_score: float
    timing_score: float
    intonation_score: float
    phoneme_similarity_score: float


class WordScoreSchema(BaseModel):
    word: str
    start_time: float
    end_time: float
    score: float
    is_mispronounced: bool
    is_unclear: bool
    phonemes_expected: Optional[str]
    phonemes_actual: Optional[str]


class DetailFeedbackSchema(BaseModel):
    word: str
    issue: str
    correct_pronunciation: str
    suggestion: str
    difficulty_level: str


class AnalysisResponseSchema(BaseModel):
    id: str
    upload_id: str
    overall_score: float
    fluency_score: float
    accuracy_score: float
    completeness_score: float
    confidence_score: float
    suggestions: str
    created_at: str
    scores: ScoreBreakdownSchema
    word_scores: List[WordScoreSchema]
    feedback: List[DetailFeedbackSchema]


@router.post("/analyze")
def enqueue_analysis(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enqueues the pronunciation assessment task on Celery."""
    upload_repo = UploadRepository(db)
    upload = upload_repo.get_upload(req.upload_id)
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload record not found."
        )
        
    if upload.status in ["processing", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio is already {upload.status}."
        )

    # Trigger async Celery task
    task = analyze_audio_task.delay(req.upload_id, req.reference_text)
    
    return {
        "task_id": task.id,
        "status": "enqueued",
        "message": "Analysis started in background."
    }


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Check status of Celery background worker task."""
    task_result = AsyncResult(task_id, app=analyze_audio_task.app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = "completed"
        if isinstance(task_result.result, dict):
            analysis_id = task_result.result.get("analysis_id")
            response["result_id"] = analysis_id
            response["analysis_id"] = analysis_id
        else:
            response["result_id"] = str(task_result.result)
            response["analysis_id"] = str(task_result.result)
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result) or "Task failed."
        
    return response


@router.get("/analysis/{id}", response_model=AnalysisResponseSchema)
def get_analysis_result(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch completed scoring assessment from database."""
    analysis_repo = AnalysisRepository(db)
    analysis = analysis_repo.get_analysis(id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report not found."
        )
        
    # Return formatted schema
    return {
        "id": analysis.id,
        "upload_id": analysis.upload_id,
        "overall_score": analysis.overall_score,
        "fluency_score": analysis.fluency_score,
        "accuracy_score": analysis.accuracy_score,
        "completeness_score": analysis.completeness_score,
        "confidence_score": analysis.confidence_score,
        "suggestions": analysis.suggestions or "",
        "created_at": analysis.created_at.isoformat(),
        "scores": {
            "stress_score": analysis.scores.stress_score,
            "rhythm_score": analysis.scores.rhythm_score,
            "pauses_score": analysis.scores.pauses_score,
            "timing_score": analysis.scores.timing_score,
            "intonation_score": analysis.scores.intonation_score,
            "phoneme_similarity_score": analysis.scores.phoneme_similarity_score,
        },
        "word_scores": [
            {
                "word": w.word,
                "start_time": w.start_time,
                "end_time": w.end_time,
                "score": w.score,
                "is_mispronounced": w.is_mispronounced,
                "is_unclear": w.is_unclear,
                "phonemes_expected": w.phonemes_expected,
                "phonemes_actual": w.phonemes_actual
            } for w in analysis.word_scores
        ],
        "feedback": [
            {
                "word": f.word,
                "issue": f.issue,
                "correct_pronunciation": f.correct_pronunciation,
                "suggestion": f.suggestion,
                "difficulty_level": f.difficulty_level
            } for f in analysis.feedback
        ]
    }


@router.delete("/analysis/{id}")
def delete_analysis(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Wipe analysis reports and audit trace the deletion (Right to Erasure compliance)."""
    analysis_repo = AnalysisRepository(db)
    analysis = analysis_repo.get_analysis(id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report not found."
        )

    # Ensure user has authority to delete
    if current_user and analysis.upload.user_id != current_user.id:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="You do not have permission to delete this analysis."
         )

    success = analysis_repo.delete_analysis(id)
    if success:
        # Audit Log
        audit_repo = AuditLogRepository(db)
        audit_repo.create_log(
            user_id=current_user.id if current_user else None,
            analysis_id=None,
            action="DELETE_ANALYSIS_SUCCESS",
            resource="analysis",
            details=f"Analysis ID {id} deleted upon user request.",
            ip_address="0.0.0.0"
        )
        return {"status": "success", "message": "Analysis report wiped successfully."}
        
    return {"status": "error", "message": "Failed to delete analysis report."}


@router.post("/feedback")
def submit_analysis_feedback(
    req: UserFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log user rating feedback for quality audits."""
    audit_repo = AuditLogRepository(db)
    audit_repo.create_log(
        user_id=current_user.id if current_user else None,
        analysis_id=req.analysis_id,
        action="SUBMIT_USER_FEEDBACK",
        resource="feedback",
        details=f"Rating: {req.rating}/5. Comments: {req.comments or 'None'}",
        ip_address="0.0.0.0"
    )
    return {"status": "success", "message": "Thank you for your feedback!"}


@router.post("/user/deletion-request")
def submit_deletion_request(
    req: DeletionRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create formal deletion request to purge user data (DPDP Compliance)."""
    # Create request
    del_repo = DeletionRequestRepository(db)
    user_id = current_user.id if current_user else None
    
    email_norm = req.email.lower().strip()
    del_req = del_repo.create_request(user_id=user_id, email=email_norm)
    
    # In a full production app, this kicks off a database trigger/job.
    # We will immediately perform the account deletion if authenticated user matches email.
    if current_user and current_user.email.lower().strip() == email_norm:
        # Delete user
        user_repo = UserRepository(db)
        user_repo.delete_user(current_user.id)
        
        # Complete request record
        del_repo.complete_request(del_req.id)
        
        # Log audit
        audit_repo = AuditLogRepository(db)
        audit_repo.create_log(
            user_id=None,
            analysis_id=None,
            action="USER_SELF_PURGE",
            resource="user",
            details=f"User {email_norm} account and analyses purged successfully.",
            ip_address="0.0.0.0"
        )
        return {
            "status": "success",
            "message": "Your account and all associated analyses have been completely deleted from our servers."
        }

    return {
        "status": "pending",
        "message": "Deletion request received. Verification email will be sent to complete the process."
    }
