from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.core.config import settings

# Setup password context
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Setup field encryption context
# Use setting's encryption key. Generate one if it's invalid
try:
    fernet = Fernet(settings.ENCRYPTION_KEY.encode())
except Exception:
    # Fallback/Safe generation for development
    fallback_key = Fernet.generate_key()
    fernet = Fernet(fallback_key)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Union[str, None]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


def encrypt_data(plain_text: str) -> str:
    """Encrypt sensitive string data (e.g. Email, IP Address) for DPDP compliance."""
    if not plain_text:
        return ""
    encrypted_bytes = fernet.encrypt(plain_text.encode())
    return encrypted_bytes.decode()


def decrypt_data(cipher_text: str) -> str:
    """Decrypt sensitive string data."""
    if not cipher_text:
        return ""
    try:
        decrypted_bytes = fernet.decrypt(cipher_text.encode())
        return decrypted_bytes.decode()
    except Exception:
        return "[ENCRYPTED_DECRYPTION_FAILED]"
