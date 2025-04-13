# app/models.py

from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, Table, ForeignKey, Text # Added Text for longer strings if needed
)
# Use relationship from SQLAlchemy ORM
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Import Base from your db module to ensure all models use the same metadata
from .db import Base

# --- NEW: Association Table for User<->Role Many-to-Many relationship ---
# Use SQLAlchemy Core Table construct for association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# --- NEW: Role Model ---
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    # Increased length slightly for name, ensure unique
    name = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    # --- RBAC Relationship ---
    # Defines the 'users' attribute on the Role model
    users = relationship(
        "User",
        secondary=user_roles, # Link through the association table
        back_populates="roles" # Link back to the 'roles' attribute on User
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


# --- NEW: User Model ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Email is likely the main identifier, especially with OAuth
    email = Column(String(255), unique=True, index=True, nullable=False)
    # Optional username, unique if provided
    username = Column(String(100), unique=True, index=True, nullable=True)
    # Password hash for local users, nullable for OAuth users
    hashed_password = Column(String(255), nullable=True) # Store hash, not plain text

    # --- Authentication Provider Info ---
    # e.g., 'local', 'google', 'microsoft'
    auth_provider = Column(String(50), nullable=False, default='local', index=True)
    # The unique ID provided by the OAuth provider (e.g., Google's 'sub' claim)
    # Nullable for local users. Index for faster lookup.
    provider_user_id = Column(String(255), nullable=True, index=True)
    # Consider a composite unique constraint if needed:
    # from sqlalchemy import UniqueConstraint
    # __table_args__ = (UniqueConstraint('auth_provider', 'provider_user_id', name='uq_provider_user'),)


    # --- Standard Flags ---
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False) # Bypasses role checks

    # --- RBAC Relationship ---
    # Defines the 'roles' attribute on the User model
    roles = relationship(
        "Role",
        secondary=user_roles, # Link through the association table
        back_populates="users", # Link back to the 'users' attribute on Role
        lazy="selectin" # Use 'selectin' for efficient loading of roles with the user
    )

    # --- OPTIONAL: Relationship to Rulesets owned by the user ---
    # Uncomment if you want users to own rulesets
    # owned_rulesets = relationship("Ruleset", back_populates="owner", lazy="dynamic") # 'dynamic' might be better if many rulesets

    def __repr__(self):
        role_names = ', '.join([role.name for role in self.roles]) if self.roles else 'No Roles'
        return f"<User(id={self.id}, email='{self.email}', provider='{self.auth_provider}', roles='{role_names}')>"


# --- EXISTING MODELS (Integrated) ---

class Ruleset(Base):
    __tablename__ = "rulesets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)

    # Relationship to Rule (One-to-Many: Ruleset -> Rules)
    # - cascade: Operations on Ruleset (like delete) affect related Rules.
    # - lazy: How related Rules are loaded. 'selectin' loads them efficiently with the Ruleset query.
    rules = relationship("Rule", back_populates="ruleset", cascade="all, delete-orphan", lazy="selectin")

    # --- OPTIONAL: Relationship back to User owner ---
    # Uncomment if you want users to own rulesets
    # owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Allow null if some rulesets are system-wide?
    # owner = relationship("User", back_populates="owned_rulesets")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=True) # Added length limit
    # Foreign key back to Ruleset
    ruleset_id = Column(Integer, ForeignKey("rulesets.id"), nullable=False, index=True)
    # Unique foreign key for One-to-One relationship with Action
    action_id = Column(Integer, ForeignKey("actions.id"), unique=True, nullable=False)

    # Relationship back to Ruleset (Many-to-One: Rules -> Ruleset)
    ruleset = relationship("Ruleset", back_populates="rules")
    # Relationship to Action (One-to-One: Rule <-> Action)
    # - uselist=False signifies a one-to-one relationship from the Rule side.
    action = relationship("Action", back_populates="rule", cascade="all, delete-orphan", uselist=False)
    # Relationship to Condition (One-to-Many: Rule -> Conditions)
    conditions = relationship("Condition", back_populates="rule", cascade="all, delete-orphan", lazy="selectin")


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False) # e.g., 'set_value', 'remove_tag'
    params = Column(Text, nullable=True) # Use Text for potentially long JSON strings

    # Relationship back to Rule (One-to-One: Action <-> Rule)
    rule = relationship("Rule", back_populates="action")


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    # Storing DICOM tag as string, e.g., "(0010,0020)"
    attribute = Column(String(50), nullable=False)
    operator = Column(String(50), nullable=False) # e.g., 'equals', 'contains'
    value = Column(Text, nullable=True) # Use Text for potentially long values, nullable for operators like 'exists'
    # Foreign key back to Rule
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False, index=True)

    # Relationship back to Rule (Many-to-One: Conditions -> Rule)
    rule = relationship("Rule", back_populates="conditions")
