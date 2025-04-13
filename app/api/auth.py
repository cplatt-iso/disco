# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated # Use Annotated for Depends in newer FastAPI/Pydantic

from app import schemas # Import your schemas
from app.crud import user as crud_user # Import user CRUD functions
from app.core import security # Import JWT functions
from app.api.database import get_db # Import DB dependency

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Handles user login via username/password (email in this case)
    and returns a JWT access token.
    """
    # Use email as the username field for authentication
    user = crud_user.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Create JWT token - use email as the 'sub' (subject) claim
    access_token = security.create_access_token(
        data={"sub": user.email}
        # Optionally add roles/scopes here: "roles": [role.name for role in user.roles]
    )
    return {"access_token": access_token, "token_type": "bearer"}
