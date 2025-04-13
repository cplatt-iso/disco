# app/crud/user.py
from sqlalchemy.orm import Session
from typing import List, Optional

# Assuming your models and schemas are defined as previously discussed
from app import models, schemas
# Import password hashing functions
from app.core.security import get_password_hash, verify_password

# --- User CRUD ---

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Gets a single user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Gets a single user by email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Gets a single user by username (if usernames are used)."""
    if not username:
        return None
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Gets a list of users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Creates a new local user."""
    hashed_password = get_password_hash(user.password) if user.password else None
    # Ensure hashed_password is not None if auth_provider is local
    if user.auth_provider == 'local' and not hashed_password:
        raise ValueError("Password is required for local users")

    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        auth_provider=user.auth_provider or 'local', # Default to local if not provided
        provider_user_id=user.provider_user_id,
        is_active=user.is_active if user.is_active is not None else True,
        is_superuser=user.is_superuser if user.is_superuser is not None else False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Optionally assign default roles here if needed
    return db_user

def update_user(db: Session, db_user: models.User, user_in: schemas.UserUpdate) -> models.User:
    """Updates an existing user."""
    update_data = user_in.model_dump(exclude_unset=True) # Get only provided fields

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"] # Don't try to set password directly again

    for key, value in update_data.items():
         # Prevent changing auth provider details via this update endpoint maybe?
        if key not in ['auth_provider', 'provider_user_id']:
             setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticates a user with email and password."""
    user = get_user_by_email(db, email=email)
    if not user:
        return None # User not found
    if user.auth_provider != 'local' or not user.hashed_password:
        return None # Cannot authenticate non-local user or user without password hash
    if not verify_password(password, user.hashed_password):
        return None # Incorrect password
    return user

# --- Role CRUD ---

def get_role(db: Session, role_id: int) -> Optional[models.Role]:
    return db.query(models.Role).filter(models.Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    return db.query(models.Role).filter(models.Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[models.Role]:
    return db.query(models.Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: schemas.RoleCreate) -> models.Role:
    db_role = models.Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# --- Role Assignment ---

def assign_role_to_user(db: Session, db_user: models.User, db_role: models.Role) -> models.User:
    """Assigns a role to a user if not already assigned."""
    if db_role not in db_user.roles:
        db_user.roles.append(db_role)
        db.commit()
        db.refresh(db_user)
    return db_user

def remove_role_from_user(db: Session, db_user: models.User, db_role: models.Role) -> models.User:
     """Removes a role from a user if assigned."""
     if db_role in db_user.roles:
         db_user.roles.remove(db_role)
         db.commit()
         db.refresh(db_user)
     return db_user
