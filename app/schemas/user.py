# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# --- Role Schemas ---

class RoleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass # No extra fields needed for creation typically

class RoleUpdate(RoleBase):
    name: Optional[str] = Field(None, min_length=3, max_length=50) # Allow partial updates
    description: Optional[str] = None

# Schema for reading/returning role data (includes ID)
class Role(RoleBase):
    id: int

    # Pydantic V2 replaces Config with model_config
    model_config = {
        "from_attributes": True # Enable ORM mode for Pydantic V2+
    }
    # Pydantic V1 syntax:
    # class Config:
    #     orm_mode = True


# --- User Schemas ---

class UserBase(BaseModel):
    email: EmailStr # Use Pydantic's EmailStr for validation
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = True # Default to True if not provided
    is_superuser: Optional[bool] = False # Default to False

# Schema for creating a user (used in POST requests)
# Note: Password is included here but should NOT be in UserBase or User schema returned by API
class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8) # Required for local signup
    # These might be set during OAuth signup instead of password
    auth_provider: Optional[str] = 'local'
    provider_user_id: Optional[str] = None

# Schema for updating a user (PUT/PATCH requests)
# Allows partial updates, excludes sensitive fields like provider info typically
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8) # Allow password update
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    # Roles might be updated via separate endpoints

# Schema for reading/returning user data (used in GET responses)
# Excludes sensitive data like hashed_password
class User(UserBase):
    id: int
    auth_provider: str # Include provider info
    roles: List[Role] = [] # Include the list of assigned roles (using the Role schema)

    # Pydantic V2 replaces Config with model_config
    model_config = {
        "from_attributes": True # Enable ORM mode for Pydantic V2+
    }
    # Pydantic V1 syntax:
    # class Config:
    #     orm_mode = True

# You might also want schemas specifically for token data
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None # Or email/subject depending on JWT content
    # Add scopes/roles if needed in token data
