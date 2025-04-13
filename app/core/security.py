# app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

# --- Password Hashing ---
# Use bcrypt as the hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Handling ---
# In a real app, get these from environment variables or a config file!
SECRET_KEY = "your-very-secret-key-that-is-long-and-random" # CHANGE THIS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Example: tokens expire after 30 mins

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Use 'sub' (subject) for the main identifier (e.g., username or email)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
     """Decodes a JWT token, returns payload or None if invalid/expired."""
     try:
         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
         # Optional: Check for expiration within the payload ('exp' claim)
         # username: str = payload.get("sub")
         # if username is None:
         #     return None # Or raise exception
         return payload
     except JWTError:
         return None # Invalid token (bad signature, expired, etc.)
