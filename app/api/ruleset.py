# app/api/ruleset.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# --- Ensure these imports are correct ---
from app import crud # This might be okay if crud/__init__.py imports ruleset, but specific import is safer
# Specifically import the ruleset submodule from crud and alias it
from app.crud import ruleset as ruleset_crud
# Specifically import the ruleset submodule from schemas and alias it
from app.schemas import ruleset as ruleset_schemas
from app.db import SessionLocal
# --- End Imports ---

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# --- Ruleset Endpoints ---

# Use the specific schema alias and CRUD alias
@router.post("", response_model=ruleset_schemas.Ruleset, status_code=status.HTTP_201_CREATED)
def create_new_ruleset(ruleset: ruleset_schemas.RulesetCreate, db: Session = Depends(get_db)):
    """Creates a new ruleset."""
    db_ruleset_check = ruleset_crud.get_ruleset_by_name(db, name=ruleset.name) # Use alias
    if db_ruleset_check:
        raise HTTPException(status_code=400, detail=f"Ruleset name '{ruleset.name}' already registered")
    created_ruleset = ruleset_crud.create_ruleset(db=db, ruleset=ruleset) # Use alias
    refetched_ruleset = ruleset_crud.get_ruleset(db, created_ruleset.id) # Use alias
    if not refetched_ruleset:
         raise HTTPException(status_code=500, detail="Failed to retrieve created ruleset")
    return refetched_ruleset

# Use the specific schema alias and CRUD alias
@router.get("", response_model=List[ruleset_schemas.Ruleset])
def read_rulesets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a list of rulesets."""
    rulesets = ruleset_crud.get_rulesets(db, skip=skip, limit=limit) # Use alias
    return rulesets

# Use the specific schema alias and CRUD alias
@router.get("/{ruleset_id}", response_model=ruleset_schemas.Ruleset)
def read_ruleset(ruleset_id: int, db: Session = Depends(get_db)):
    """Retrieves a single ruleset by ID."""
    db_ruleset = ruleset_crud.get_ruleset(db, ruleset_id=ruleset_id) # Use alias
    if db_ruleset is None:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return db_ruleset

# Use the specific schema alias and CRUD alias
@router.put("/{ruleset_id}", response_model=ruleset_schemas.Ruleset)
def update_existing_ruleset(ruleset_id: int, ruleset_update: ruleset_schemas.RulesetUpdate, db: Session = Depends(get_db)):
    """Updates an existing ruleset's name or description."""
    if ruleset_update.name:
         existing = ruleset_crud.get_ruleset_by_name(db, ruleset_update.name) # Use alias
         if existing and existing.id != ruleset_id:
              raise HTTPException(status_code=400, detail=f"Ruleset name '{ruleset_update.name}' already exists.")

    updated_ruleset = ruleset_crud.update_ruleset(db=db, ruleset_id=ruleset_id, ruleset_update=ruleset_update) # Use alias
    if updated_ruleset is None:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    refetched_ruleset = ruleset_crud.get_ruleset(db, updated_ruleset.id) # Use alias
    if not refetched_ruleset:
         raise HTTPException(status_code=500, detail="Failed to retrieve updated ruleset")
    return refetched_ruleset

# Use the CRUD alias
@router.delete("/{ruleset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_ruleset(ruleset_id: int, db: Session = Depends(get_db)):
    """Deletes a ruleset and all its associated rules/conditions/actions."""
    deleted_ruleset = ruleset_crud.delete_ruleset(db=db, ruleset_id=ruleset_id) # Use alias
    if deleted_ruleset is None:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return None


# --- Rule Endpoints (within a Ruleset) ---

# Use the specific schema alias and CRUD alias
@router.post("/{ruleset_id}/rules/", response_model=ruleset_schemas.Rule, status_code=status.HTTP_201_CREATED)
def create_new_rule_for_ruleset(ruleset_id: int, rule: ruleset_schemas.RuleCreate, db: Session = Depends(get_db)):
    """Creates a new rule (with conditions and actions) within a specific ruleset."""
    created_rule = ruleset_crud.create_rule_for_ruleset(db=db, rule=rule, ruleset_id=ruleset_id) # Use alias
    if created_rule is None:
        raise HTTPException(status_code=404, detail=f"Ruleset ID {ruleset_id} not found")
    return created_rule

# --- TODO: Endpoints for reading, updating, deleting individual rules ---
# ... (placeholders remain the same) ...
