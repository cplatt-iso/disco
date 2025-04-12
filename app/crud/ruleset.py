# app/crud/ruleset.py
"""
CRUD operations for RuleSet, Rule, Condition, Action models.
These functions interact directly with the database via SQLAlchemy Session.
"""
import logging
from sqlalchemy.orm import Session, joinedload, contains_eager, defer, undefer
from typing import List, Optional
from datetime import datetime

from app import models
# --- Updated Import ---
# Import the specific schemas module and alias it
from app.schemas import ruleset as ruleset_schemas
# --- End Updated Import ---

logger = logging.getLogger(__name__)

# --- Ruleset CRUD ---

def get_ruleset(db: Session, ruleset_id: int) -> Optional[models.RuleSet]:
    """
    Gets a single ruleset by ID, eagerly loading its rules,
    and their associated conditions and actions.
    """
    logger.debug(f"Fetching ruleset with ID: {ruleset_id}")
    return db.query(models.RuleSet).options(
        joinedload(models.RuleSet.rules).options( # Load rules
            joinedload(models.Rule.conditions),     # Load conditions for each rule
            joinedload(models.Rule.actions)       # Load actions for each rule
        )
    ).filter(models.RuleSet.id == ruleset_id).first()

def get_rulesets(db: Session, skip: int = 0, limit: int = 100) -> List[models.RuleSet]:
    """
    Gets a list of rulesets with pagination.
    Uses joinedload for nested relationships, which might be heavy.
    Consider using selectinload or removing options for performance on large datasets.
    """
    logger.debug(f"Fetching rulesets list, skip: {skip}, limit: {limit}")
    # Using joinedload can cause cartesian product issues if rules/conditions/actions are numerous.
    # selectinload is often better for loading collections across relationships.
    # Example using selectinload:
    # from sqlalchemy.orm import selectinload
    # return db.query(models.RuleSet).options(
    #     selectinload(models.RuleSet.rules).options(
    #         selectinload(models.Rule.conditions),
    #         selectinload(models.Rule.actions)
    #     )
    # ).order_by(models.RuleSet.name).offset(skip).limit(limit).all()

    # Sticking with joinedload as per original for now:
    return db.query(models.RuleSet).options(
         joinedload(models.RuleSet.rules).options(
             joinedload(models.Rule.conditions),
             joinedload(models.Rule.actions)
         )
     ).order_by(models.RuleSet.name).offset(skip).limit(limit).all()

def get_ruleset_by_name(db: Session, name: str) -> Optional[models.RuleSet]:
    """Gets a single ruleset by name."""
    logger.debug(f"Fetching ruleset by name: {name}")
    return db.query(models.RuleSet).filter(models.RuleSet.name == name).first()

def create_ruleset(db: Session, ruleset: ruleset_schemas.RulesetCreate) -> models.RuleSet:
    """Creates a new ruleset."""
    logger.info(f"Creating new ruleset with name: {ruleset.name}")
    db_ruleset = models.RuleSet(
        name=ruleset.name,
        description=ruleset.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    try:
        db.add(db_ruleset)
        db.commit()
        db.refresh(db_ruleset)
        logger.info(f"Ruleset '{db_ruleset.name}' created successfully with ID: {db_ruleset.id}")
        return db_ruleset
    except Exception as e:
        logger.error(f"Failed to create ruleset '{ruleset.name}': {e}", exc_info=True)
        db.rollback()
        raise # Re-raise the exception after rollback

def update_ruleset(db: Session, ruleset_id: int, ruleset_update: ruleset_schemas.RulesetUpdate) -> Optional[models.RuleSet]:
    """Updates an existing ruleset's name and/or description."""
    logger.info(f"Updating ruleset ID: {ruleset_id}")
    db_ruleset = get_ruleset(db, ruleset_id) # Use get_ruleset to ensure eager loading if needed later
    if not db_ruleset:
        logger.warning(f"Update failed: Ruleset ID {ruleset_id} not found.")
        return None

    update_data = ruleset_update.dict(exclude_unset=True) # Get only provided fields
    updated = False
    for key, value in update_data.items():
        if getattr(db_ruleset, key) != value:
             setattr(db_ruleset, key, value)
             updated = True

    if updated:
        db_ruleset.updated_at = datetime.utcnow()
        try:
            db.commit()
            db.refresh(db_ruleset)
            logger.info(f"Ruleset ID {ruleset_id} updated successfully.")
            return db_ruleset
        except Exception as e:
            logger.error(f"Failed to update ruleset ID {ruleset_id}: {e}", exc_info=True)
            db.rollback()
            raise
    else:
         logger.info(f"No changes detected for ruleset ID {ruleset_id}. Skipping update commit.")
         return db_ruleset # Return the existing object even if no changes


def delete_ruleset(db: Session, ruleset_id: int) -> Optional[models.RuleSet]:
    """
    Deletes a ruleset. Cascade settings on the models should handle deletion
    of associated rules, conditions, and actions.
    """
    logger.warning(f"Attempting to delete ruleset ID: {ruleset_id}")
    # Query first to return the object details upon successful deletion
    db_ruleset = db.query(models.RuleSet).filter(models.RuleSet.id == ruleset_id).first()
    if db_ruleset:
        try:
            deleted_name = db_ruleset.name # Capture name before deletion
            db.delete(db_ruleset)
            db.commit()
            logger.info(f"Successfully deleted ruleset ID {ruleset_id} (Name: '{deleted_name}')")
            return db_ruleset # Return the object (now detached from session)
        except Exception as e:
            logger.error(f"Failed to delete ruleset ID {ruleset_id}: {e}", exc_info=True)
            db.rollback()
            raise
    else:
        logger.warning(f"Deletion failed: Ruleset ID {ruleset_id} not found.")
        return None


# --- Rule CRUD (within a Ruleset) ---

def create_rule_for_ruleset(db: Session, rule: ruleset_schemas.RuleCreate, ruleset_id: int) -> Optional[models.Rule]:
    """
    Creates a new rule with its conditions and actions and associates
    it with an existing ruleset.
    """
    logger.info(f"Attempting to add rule '{rule.name}' to ruleset ID: {ruleset_id}")
    # Check if ruleset exists first
    db_ruleset = db.query(models.RuleSet).filter(models.RuleSet.id == ruleset_id).first()
    if not db_ruleset:
        logger.error(f"Cannot add rule: Ruleset ID {ruleset_id} not found.")
        return None # Ruleset not found

    # Create the Rule object from the schema, excluding nested lists initially
    db_rule = models.Rule(
        **rule.dict(exclude={'conditions', 'actions'}), # Unpack base rule fields
        ruleset_id=ruleset_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Create associated conditions from the schema and add to the rule's collection
    if rule.conditions:
        logger.debug(f"Adding {len(rule.conditions)} conditions to rule '{rule.name}'")
        for condition_in in rule.conditions:
            db_condition = models.Condition(**condition_in.dict())
            db_rule.conditions.append(db_condition) # Appending associates them via relationship

    # Create associated actions from the schema and add to the rule's collection
    if rule.actions:
        logger.debug(f"Adding {len(rule.actions)} actions to rule '{rule.name}'")
        for action_in in rule.actions:
            db_action = models.Action(**action_in.dict())
            db_rule.actions.append(db_action) # Appending associates them via relationship

    try:
        # Add the rule. SQLAlchemy handles inserting conditions/actions
        # due to the relationships and cascade settings (if configured correctly).
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule) # Refresh to get the rule's ID and potentially defaults

        # Eagerly load conditions/actions for the returned object if needed,
        # although accessing them later would lazy-load them anyway.
        # db.refresh(db_rule, attribute_names=['conditions', 'actions'])
        logger.info(f"Rule '{db_rule.name}' (ID: {db_rule.id}) added successfully to ruleset ID {ruleset_id}.")

        return db_rule
    except Exception as e:
        logger.error(f"Failed to add rule '{rule.name}' to ruleset ID {ruleset_id}: {e}", exc_info=True)
        db.rollback()
        raise


# --- Functions for reading/updating/deleting individual Rules, Conditions, Actions ---

def get_rule(db: Session, rule_id: int) -> Optional[models.Rule]:
     """Gets a single rule by ID, loading associated conditions and actions."""
     logger.debug(f"Fetching rule with ID: {rule_id}")
     return db.query(models.Rule).options(
         joinedload(models.Rule.conditions), # Use joinedload or selectinload
         joinedload(models.Rule.actions)
     ).filter(models.Rule.id == rule_id).first()

# --- Placeholders for more complex CRUD needed for a full UI editor ---

# TODO: Implement update_rule function
# def update_rule(db: Session, rule_id: int, rule_update: ruleset_schemas.RuleUpdate) -> Optional[models.Rule]:
#     """Updates an existing rule, including managing nested conditions/actions."""
#     # 1. Fetch the existing rule with conditions/actions loaded.
#     # 2. Update base fields (name, desc, priority, logic_operator).
#     # 3. Determine conditions/actions to add, remove, update based on rule_update payload.
#     #    This often involves comparing IDs or using a specific payload structure.
#     # 4. Perform DB operations (add, delete, update children).
#     # 5. Commit and refresh.
#     pass

# TODO: Implement delete_rule function
# def delete_rule(db: Session, rule_id: int) -> Optional[models.Rule]:
#     """Deletes a specific rule. Cascade should handle conditions/actions."""
#     # 1. Fetch the rule.
#     # 2. If found, db.delete(rule) and db.commit().
#     # 3. Return the deleted rule object (or None).
#     pass

# TODO: CRUD functions for individual Conditions and Actions if the UI needs to manage them independently.
# Example: add_condition_to_rule, delete_condition, update_action, etc.
