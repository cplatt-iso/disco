# app/schemas/ruleset.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

# --- Condition Schemas ---
class ConditionBase(BaseModel):
    attribute: str = Field(..., examples=["calling_ae_title", "dicom_tag:0010,0020"])
    operator: str = Field(..., examples=["equals", "not_equals", "starts_with", "contains", "regex", "in", "not_in"])
    value: str # For 'in'/'not_in', this could be a comma-separated string handled in logic

class ConditionCreate(ConditionBase):
    pass

class Condition(ConditionBase):
    id: int

    class Config:
        orm_mode = True # Pydantic V1 use -> from_attributes = True in V2

# --- Action Schemas ---
class ActionBase(BaseModel):
    action_type: str = Field(..., examples=["modify", "delete_tag", "route_to_aet", "log", "discard"])
    target: Optional[str] = Field(None, examples=["dicom_tag:0010,0010", "TARGET_AET", "/path/to/storage"])
    parameters: Optional[str] = Field(None, description="JSON string containing action-specific parameters") # Keep as string for flexibility

    @field_validator('parameters')
    @classmethod
    def validate_parameters_json(cls, v):
        if v is None:
            return v
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError('parameters must be a valid JSON string or null')

class ActionCreate(ActionBase):
    pass

class Action(ActionBase):
    id: int

    class Config:
        orm_mode = True

# --- Rule Schemas ---
class RuleBase(BaseModel):
    name: Optional[str] = "Unnamed Rule"
    description: Optional[str] = None
    logic_operator: str = Field("ALL", examples=["ALL", "ANY"])
    priority: int = 0

class RuleCreate(RuleBase):
    conditions: List[ConditionCreate] = []
    actions: List[ActionCreate] = []

class RuleUpdate(RuleBase):
    name: Optional[str] = None # Make fields optional for partial update
    description: Optional[str] = None
    logic_operator: Optional[str] = None
    priority: Optional[int] = None
    # Still require full lists for replacement strategy
    conditions: List[ConditionCreate] = []
    actions: List[ActionCreate] = []


class Rule(RuleBase):
    id: int
    conditions: List[Condition] = []
    actions: List[Action] = []

    class Config:
        orm_mode = True

# --- Ruleset Schemas ---
class RulesetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class RulesetCreate(RulesetBase):
    pass

class RulesetUpdate(RulesetBase):
    # Allow optional fields for updates
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class Ruleset(RulesetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    rules: List[Rule] = [] # Include nested rules in the response

    class Config:
        orm_mode = True
