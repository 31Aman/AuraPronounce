from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.repositories.database_repo import UserRepository, AuditLogRepository

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    email_norm = user_in.email.lower().strip()
    user = user_repo.get_user_by_email(email_norm)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    new_user = user_repo.create_user(email=email_norm, password_raw=user_in.password)
    access_token = create_access_token(subject=new_user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "email": new_user.email
    }


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    email_norm = form_data.username.lower().strip()
    user = user_repo.get_user_by_email(email_norm)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


# Standard JSON login for web client
class LoginJson(BaseModel):
    email: EmailStr
    password: str

@router.post("/login-json", response_model=Token)
def login_json(credentials: LoginJson, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    email_norm = credentials.email.lower().strip()
    user = user_repo.get_user_by_email(email_norm)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Simulates forgot password link generation and logging."""
    user_repo = UserRepository(db)
    email_norm = req.email.lower().strip()
    user = user_repo.get_user_by_email(email_norm)
    
    # Return 200/success even if email doesn't exist for security (anti-scraping)
    if not user:
        return {"message": "If this email is registered, a password reset link has been sent."}
        
    import secrets
    reset_token = secrets.token_urlsafe(32)
    print(f"\n[PASSWORD RESET SIMULATION] email={email_norm} reset_token={reset_token}\n")
    
    audit_repo = AuditLogRepository(db)
    audit_repo.create_log(
        user_id=user.id,
        analysis_id=None,
        action="REQUEST_PASSWORD_RESET",
        resource="user",
        details=f"Secure password reset request logged for {email_norm}.",
        ip_address="0.0.0.0"
    )
    
    return {"message": "If this email is registered, a password reset link has been sent."}
