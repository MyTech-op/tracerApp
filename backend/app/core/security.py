import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import bcrypt
from cryptography.fernet import Fernet
from jose import jwt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def _fernet() -> Fernet:
    """Fernet key deterministically derived from SECRET_KEY (for OAuth token at-rest encryption)."""
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    """Encrypt a sensitive value (OAuth token) for storage at rest."""
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Decrypt a value previously stored with encrypt_secret."""
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")


def sign_state(payload: str, ttl_seconds: int = 600) -> str:
    """HMAC-sign an OAuth state payload with an expiry, e.g. 'website_id.expiry.nonce.sig'."""
    expiry = int(datetime.now(timezone.utc).timestamp()) + ttl_seconds
    nonce = secrets_token_hex()
    body = f"{payload}.{expiry}.{nonce}"
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_state(state: str, ttl_seconds: int = 600) -> Optional[str]:
    """Verify an HMAC-signed OAuth state and return the payload (or None if invalid/expired)."""
    try:
        parts = state.split(".")
        if len(parts) != 4:
            return None
        payload, expiry, nonce, sig = parts
        body = f"{payload}.{expiry}.{nonce}"
        expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        if int(expiry) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except Exception:
        return None


def secrets_token_hex(nbytes: int = 16) -> str:
    import secrets
    return secrets.token_hex(nbytes)
