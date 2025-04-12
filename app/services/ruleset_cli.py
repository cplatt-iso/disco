# app/services/ruleset_cli.py
import argparse
import json
import logging
from datetime import datetime
from app.db import SessionLocal
# --- Updated Import ---
from app.crud import ruleset as ruleset_crud # Import the specific module and alias it
# --- End Updated Import ---
from app import schemas # Import schemas for creation/update

# Setup basic logging for CLI operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - CLI - %(message)s')
logger = logging.getLogger(__name__)

# Simple serialization for CLI output (can be more sophisticated)
def serialize_model_for_cli(model):
     """Basic serialization using Pydantic models if possible, else basic dict."""
     if hasattr(model, '__tablename__'): # Check if it's a SQLAlchemy model
        try:
            # Attempt to map to a corresponding Pydantic schema for richer output
            # Ensure schema imports are correct here if needed, or pass schema explicitly
            from app.schemas import ruleset as ruleset_schemas # Import inside if not top-level
            schema_map = {
                 "rulesets": ruleset_schemas.Ruleset,
                 "rules": ruleset_schemas.Rule,
                 "conditions": ruleset_schemas.Condition,
                 "actions": ruleset_schemas.Action,
            }
            schema = schema_map.get(model.__tablename__)
            if schema:
                 # Use model_dump() for Pydantic V2, dict() for V1
                 if hasattr(schema, 'model_validate'): # Check for Pydantic V2 method
                     return schema.model_validate(model).model_dump(mode='json')
                 else: # Assume Pydantic V1
                     return schema.from_orm(model).dict() # noqa
        except Exception as e:
             logger.debug(f"Schema mapping/serialization failed for {model}: {e}")
             pass # Fallback to basic dict

        # Basic fallback (relationships won't be included unless loaded by CRUD)
        data = {}
        for c in model.__table__.columns:
            # Handle datetime objects specifically for JSON serialization
            value = getattr(model, c.name)
            if isinstance(value, datetime):
                 data[c.name] = value.isoformat()
            else:
                 data[c.name] = value

        # Manually add loaded relationships if needed for inspection
        # Check if relationships are loaded before trying to access
        if 'rules' in model.__dict__ and model.rules: data['rules'] = [serialize_model_for_cli(r) for r in model.rules]
        if 'conditions' in model.__dict__ and model.conditions: data['conditions'] = [serialize_model_for_cli(c) for c in model.conditions]
        if 'actions' in model.__dict__ and model.actions: data['actions'] = [serialize_model_for_cli(a) for a in model.actions]
        return data
     return str(model)


def main():
    parser = argparse.ArgumentParser(description="Ruleset CLI Utility - Interacts directly with DB via CRUD functions")
    # Keep most arguments the same
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", action="store_true", help="List all rulesets")
    group.add_argument("-i", "--id", type=int, help="Inspect a ruleset by ID")
    group.add_argument("--create", action="store_true", help="Create a new ruleset")
    group.add_argument("--update", type=int, metavar="RULESET_ID", help="Update an existing ruleset by ID")
    group.add_argument("--delete", type=int, metavar="RULESET_ID", help="Delete a ruleset by ID")
    group.add_argument("--add-rule", type=int, metavar="RULESET_ID", help="Add a rule to the specified ruleset ID")

    # Arguments for create/update/add-rule
    parser.add_argument("--name", type=str, help="Name for create/update ruleset or rule")
    parser.add_argument("--desc", type=str, help="Description for create/update ruleset or rule")
    parser.add_argument("--logic", type=str, choices=["ALL", "ANY"], default="ALL", help="Logic operator for rule (default: ALL)")
    parser.add_argument("--priority", type=int, default=0, help="Priority for rule (default: 0)")
    # Condition format: attribute;operator;value (use semicolon to avoid shell splitting issues)
    parser.add_argument("--cond", action="append", help="Condition in format attribute;operator;value")
     # Action format: JSON string like '{"action_type": "log", "parameters": "{\"level\":\"info\"}"}'
    parser.add_argument("--act", action="append", help="Action as a JSON string")

    args = parser.parse_args()
    session = SessionLocal()

    try: # Wrap CLI logic in try/finally to ensure session close
        if args.list:
            logger.info("Listing all rulesets...")
            # --- Use Alias ---
            rulesets = ruleset_crud.get_rulesets(session)
            if not rulesets:
                 print("No rulesets found.")
            for rs in rulesets:
                # Basic output for list view
                print(f"ID: {rs.id}, Name: {rs.name}, Rules: {len(rs.rules) if rs.rules else 0}")

        elif args.id:
            logger.info(f"Inspecting ruleset ID: {args.id}...")
            # --- Use Alias ---
            rs = ruleset_crud.get_ruleset(session, ruleset_id=args.id)
            if rs:
                # Use helper for better serialization
                print(json.dumps(serialize_model_for_cli(rs), indent=2, default=str)) # default=str for datetime
            else:
                print(f"Ruleset ID {args.id} not found")

        elif args.create:
            if not args.name:
                print("Error: --name is required to create a ruleset")
            else:
                logger.info(f"Creating ruleset '{args.name}'...")
                # Ensure schema import is correct if needed here, or use the top-level import
                from app.schemas import ruleset as ruleset_schemas # Import inside if needed
                ruleset_in = ruleset_schemas.RulesetCreate(name=args.name, description=args.desc)
                # --- Use Alias ---
                rs = ruleset_crud.create_ruleset(session, ruleset=ruleset_in)
                print(f"Created ruleset ID {rs.id}: {rs.name}")
                # Optionally print the full created object
                print(json.dumps(serialize_model_for_cli(rs), indent=2, default=str))

        elif args.update:
            if not args.name and args.desc is None: # Check if desc is explicitly provided (can be empty string)
                print("Error: Specify at least --name or --desc to update")
            else:
                 logger.info(f"Updating ruleset ID: {args.update}...")
                 ruleset_update_data = {}
                 if args.name: ruleset_update_data['name'] = args.name
                 if args.desc is not None: ruleset_update_data['description'] = args.desc

                 from app.schemas import ruleset as ruleset_schemas # Import inside if needed
                 ruleset_in = ruleset_schemas.RulesetUpdate(**ruleset_update_data)
                 # --- Use Alias ---
                 rs = ruleset_crud.update_ruleset(session, ruleset_id=args.update, ruleset_update=ruleset_in)
                 if rs:
                    print(f"Updated ruleset ID {rs.id}: {rs.name}")
                    print(json.dumps(serialize_model_for_cli(rs), indent=2, default=str))
                 else:
                    print(f"Ruleset ID {args.update} not found")

        elif args.delete:
             logger.warning(f"Attempting to delete ruleset ID: {args.delete} and all its contents...")
             # --- Use Alias ---
             deleted_rs = ruleset_crud.delete_ruleset(session, ruleset_id=args.delete)
             if deleted_rs:
                print(f"Successfully deleted ruleset ID {args.delete} (Name: '{deleted_rs.name}')")
             else:
                print(f"Ruleset ID {args.delete} not found")

        elif args.add_rule:
            if not args.name:
                print("Error: --name is required to add a rule")
            else:
                logger.info(f"Adding rule '{args.name}' to ruleset ID: {args.add_rule}...")
                from app.schemas import ruleset as ruleset_schemas # Import inside if needed
                # Parse conditions
                conditions_in = []
                if args.cond:
                    for c_str in args.cond:
                        parts = c_str.split(';', 2)
                        if len(parts) == 3:
                             conditions_in.append(ruleset_schemas.ConditionCreate(attribute=parts[0], operator=parts[1], value=parts[2]))
                        else:
                             print(f"Warning: Skipping invalid condition format: '{c_str}'. Use 'attribute;operator;value'.")

                # Parse actions
                actions_in = []
                if args.act:
                     for a_json in args.act:
                         try:
                             action_dict = json.loads(a_json)
                             actions_in.append(ruleset_schemas.ActionCreate(**action_dict))
                         except json.JSONDecodeError:
                             print(f"Warning: Skipping invalid JSON for action: {a_json}")
                         except Exception as e:
                              print(f"Warning: Skipping invalid action data ({e}): {a_json}")

                rule_in = ruleset_schemas.RuleCreate(
                    name=args.name,
                    description=args.desc,
                    logic_operator=args.logic,
                    priority=args.priority,
                    conditions=conditions_in,
                    actions=actions_in
                )

                try:
                     # --- Use Alias ---
                     created_rule = ruleset_crud.create_rule_for_ruleset(session, rule=rule_in, ruleset_id=args.add_rule)
                     if created_rule:
                         print(f"Successfully added rule ID {created_rule.id} ('{created_rule.name}') to ruleset ID {args.add_rule}")
                         # Optionally inspect the updated ruleset
                         rs = ruleset_crud.get_ruleset(session, ruleset_id=args.add_rule)
                         print("\nUpdated Ruleset:")
                         print(json.dumps(serialize_model_for_cli(rs), indent=2, default=str))
                     else:
                         # This happens if ruleset_id was not found by create_rule_for_ruleset
                         print(f"Error: Ruleset ID {args.add_rule} not found.")
                except Exception as e:
                     logger.error(f"Failed to add rule: {e}", exc_info=True)
                     print(f"Error: Failed to add rule. Check logs.")


    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An error occurred. Check logs.")
    finally:
        logger.info("Closing database session.")
        session.close()

if __name__ == "__main__":
    main()
