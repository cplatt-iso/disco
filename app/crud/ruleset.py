# app/crud/ruleset.py

from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional

# Import models using the correct casing ('Ruleset')
from app import models, schemas # Import the main schemas module
import json

# --- Helper function to safely parse JSON ---
def parse_params(params_str: Optional[str]) -> dict:
    """Safely parse JSON string from Action params."""
    if params_str is None:
        return {}
    try:
        params = json.loads(params_str)
        return params if isinstance(params, dict) else {}
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON params: {params_str}") # Use proper logging
        return {}

# --- RuleSet CRUD ---

def get_ruleset(db: Session, ruleset_id: int) -> Optional[models.Ruleset]:
    """Gets a single ruleset by ID, eagerly loading relationships."""
    return db.query(models.Ruleset).options(
        selectinload(models.Ruleset.rules)
        .selectinload(models.Rule.conditions),
        selectinload(models.Ruleset.rules)
        .joinedload(models.Rule.action) # joinedload suitable for one-to-one
    ).filter(models.Ruleset.id == ruleset_id).first()

def get_rulesets(db: Session, skip: int = 0, limit: int = 100) -> List[models.Ruleset]:
    """Gets a list of rulesets (consider adding ordering)."""
    # Avoid eager loading all details for list view unless specifically needed
    return db.query(models.Ruleset).order_by(models.Ruleset.name).offset(skip).limit(limit).all()

# Use schemas.RulesetCreate (lowercase 's')
def create_ruleset(db: Session, ruleset: schemas.RulesetCreate) -> models.Ruleset:
    """Creates a new ruleset with its rules, conditions, and actions."""
    db_ruleset = models.Ruleset(name=ruleset.name)
    db.add(db_ruleset)

    try:
        # Flush to get the ruleset ID before creating related items
        db.flush()

        if ruleset.rules:
            for rule_data in ruleset.rules:
                # Ensure action data exists before accessing attributes
                if not rule_data.action:
                     # Handle missing action data appropriately (skip rule, raise error?)
                     print(f"Warning: Rule '{rule_data.description}' missing action data. Skipping rule.")
                     continue # Or raise ValueError("Action data is required for each rule")

                action_params_str = json.dumps(rule_data.action.params or {})
                db_action = models.Action(
                    type=rule_data.action.type,
                    params=action_params_str
                )
                # Note: Action is linked via rule.action relationship below

                db_rule = models.Rule(
                    description=rule_data.description,
                    action=db_action, # Set the one-to-one relationship
                    ruleset=db_ruleset # Set the many-to-one relationship
                )
                # db.add(db_rule) # Not needed if cascade is set correctly on ruleset.rules

                if rule_data.conditions:
                    for cond_data in rule_data.conditions:
                        db_condition = models.Condition(
                            attribute=cond_data.attribute,
                            operator=cond_data.operator,
                            value=cond_data.value,
                            rule=db_rule # Set the many-to-one relationship
                        )
                        # db.add(db_condition) # Not needed if cascade is set correctly on rule.conditions

        # Commit the whole transaction
        db.commit()
        db.refresh(db_ruleset) # Refresh to load all relationships correctly
        return db_ruleset
    except Exception as e:
        db.rollback()
        print(f"Error creating ruleset: {e}") # Use proper logging
        raise

# Use schemas.RulesetUpdate (lowercase 's' - assuming this exists)
def update_ruleset(db: Session, ruleset_id: int, ruleset_update: schemas.RulesetUpdate) -> Optional[models.Ruleset]:
    """Updates an existing ruleset (currently only Name)."""
    # Fetch with relationship loading if you intend to update nested items later
    db_ruleset = db.query(models.Ruleset).filter(models.Ruleset.id == ruleset_id).first()

    if db_ruleset:
        # Get fields from update schema, excluding unset ones
        update_data = ruleset_update.model_dump(exclude_unset=True)

        # --- Simplified Update (Only Name) ---
        if "name" in update_data:
            db_ruleset.name = update_data["name"]

        # --- Complex Update (Handling Rules/Conditions/Actions - Placeholder) ---
        # if "rules" in update_data:
        #   Requires comparing incoming rules with existing, deleting removed ones,
        #   updating existing ones (which might involve deleting/recreating conditions/action),
        #   and adding new ones. This is significantly more complex logic.
        #   Example sketch:
        #   existing_rule_ids = {rule.id for rule in db_ruleset.rules}
        #   incoming_rule_ids = {rule.id for rule in ruleset_update.rules if rule.id}
        #   # ... logic to delete rules not in incoming_rule_ids ...
        #   # ... logic to update rules in both sets ...
        #   # ... logic to add rules only in incoming_rule_ids without an id ...
        #   pass # Requires detailed implementation

        try:
            db.commit()
            db.refresh(db_ruleset)
        except Exception as e:
             db.rollback()
             print(f"Error updating ruleset {ruleset_id}: {e}") # Use proper logging
             raise
    return db_ruleset


def delete_ruleset(db: Session, ruleset_id: int) -> Optional[models.Ruleset]:
    """Deletes a ruleset by ID. Cascading deletes handle related items."""
    db_ruleset = db.query(models.Ruleset).filter(models.Ruleset.id == ruleset_id).first()
    if db_ruleset:
        try:
            db.delete(db_ruleset)
            db.commit()
        except Exception as e:
             db.rollback()
             print(f"Error deleting ruleset {ruleset_id}: {e}") # Use proper logging
             raise # Optional: re-raise or return None/False
             # return None # Indicate failure if re-raise is not desired
    return db_ruleset # Returns the deleted object if found, or None if not found

# --- Rule CRUD ---
def get_rule(db: Session, rule_id: int) -> Optional[models.Rule]:
    """Gets a single rule by ID."""
    # Consider eager loading action/conditions if needed when getting rule directly
    return db.query(models.Rule).options(
        joinedload(models.Rule.action),
        selectinload(models.Rule.conditions)
    ).filter(models.Rule.id == rule_id).first()

# --- Condition CRUD ---
def get_condition(db: Session, condition_id: int) -> Optional[models.Condition]:
     """Gets a single condition by ID."""
     return db.query(models.Condition).filter(models.Condition.id == condition_id).first()

# --- Action CRUD ---
def get_action(db: Session, action_id: int) -> Optional[models.Action]:
     """Gets a single action by ID."""
     return db.query(models.Action).filter(models.Action.id == action_id).first()
