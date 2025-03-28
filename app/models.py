# app/models.py

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class RuleSet(Base):
    __tablename__ = 'rulesets'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rules = relationship("Rule", back_populates="ruleset")

class Rule(Base):
    __tablename__ = 'rules'
    id = Column(Integer, primary_key=True)
    ruleset_id = Column(Integer, ForeignKey('rulesets.id'), nullable=False)
    name = Column(String(255))
    logic_operator = Column(String(50), default="ALL")  # "ALL" or "ANY"
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ruleset = relationship("RuleSet", back_populates="rules")
    conditions = relationship("Condition", back_populates="rule", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="rule", cascade="all, delete-orphan")

class Condition(Base):
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    attribute = Column(String(255), nullable=False)  # e.g. "ae_title", "dicom_tag:0010,0020"
    operator = Column(String(50), nullable=False)    # e.g. "equals", "starts_with", "regex"
    value = Column(String(255), nullable=False)      # e.g. "PACS123"

    rule = relationship("Rule", back_populates="conditions")

class Action(Base):
    __tablename__ = 'actions'
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    action_type = Column(String(50), nullable=False)  # e.g. "regex", "delete", "script", "lookup"
    target = Column(String(255))                      # e.g. "dicom_tag:0010,0010"
    parameters = Column(Text)                         # JSON or script details

    rule = relationship("Rule", back_populates="actions")

