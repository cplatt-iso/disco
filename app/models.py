# app/models.py
"""
Defines the SQLAlchemy ORM models for the application database.
All models should inherit from the Base object defined in app.db.
"""

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
# Remove the local declarative_base import and definition
# from sqlalchemy.orm import declarative_base
from datetime import datetime

# --- Import the Base object from app.db ---
# This is the single source of truth for table metadata
from app.db import Base
# --- End Import ---

# Base = declarative_base() # <-- REMOVE THIS LINE


class RuleSet(Base):
    __tablename__ = 'rulesets'
    id = Column(Integer, primary_key=True, index=True) # Added index=True for primary key
    name = Column(String(255), unique=True, nullable=False, index=True) # Added index=True for unique name
    description = Column(Text, nullable=True) # Explicitly allow NULL
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Define the relationship to Rule model
    # cascade options might be useful depending on desired behavior when a RuleSet is deleted
    rules = relationship("Rule", back_populates="ruleset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RuleSet(id={self.id}, name='{self.name}')>"

class Rule(Base):
    __tablename__ = 'rules'
    id = Column(Integer, primary_key=True, index=True)
    ruleset_id = Column(Integer, ForeignKey('rulesets.id'), nullable=False, index=True) # Added index=True
    name = Column(String(255), nullable=True) # Allow NULL name? Consider adding nullable=False if required
    description = Column(Text, nullable=True) # Added description field
    logic_operator = Column(String(50), default="ALL", nullable=False)  # "ALL" or "ANY"
    priority = Column(Integer, default=0, nullable=False, index=True) # Added index=True
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    ruleset = relationship("RuleSet", back_populates="rules")
    conditions = relationship("Condition", back_populates="rule", cascade="all, delete-orphan", lazy='joined') # Consider lazy loading strategy
    actions = relationship("Action", back_populates="rule", cascade="all, delete-orphan", lazy='joined') # Consider lazy loading strategy

    def __repr__(self):
        return f"<Rule(id={self.id}, name='{self.name}', ruleset_id={self.ruleset_id})>"

class Condition(Base):
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False, index=True) # Added index=True
    attribute = Column(String(255), nullable=False)  # e.g. "ae_title", "dicom_tag:0010,0020"
    operator = Column(String(50), nullable=False)    # e.g. "equals", "starts_with", "regex", "contains"
    value = Column(String(255), nullable=False)      # Value to compare against

    # Relationship
    rule = relationship("Rule", back_populates="conditions")

    def __repr__(self):
         return f"<Condition(id={self.id}, attribute='{self.attribute}', operator='{self.operator}', value='{self.value}', rule_id={self.rule_id})>"


class Action(Base):
    __tablename__ = 'actions'
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False, index=True) # Added index=True
    action_type = Column(String(50), nullable=False)  # e.g. "modify", "delete_tag", "send_to_aet", "log", "route_to_storage", "execute_script"
    # Target could be optional depending on action_type
    target = Column(String(255), nullable=True)       # e.g., "dicom_tag:0010,0010", AE Title, Storage Path ID
    # Parameters store additional info, often as JSON
    parameters = Column(Text, nullable=True)          # e.g. {"new_value": "ANONYMIZED"}, {"script_path": "/opt/scripts/process.py"}

    # Relationship
    rule = relationship("Rule", back_populates="actions")

    def __repr__(self):
         return f"<Action(id={self.id}, action_type='{self.action_type}', target='{self.target}', rule_id={self.rule_id})>"
