# app/services/initialize.py
"""
Contains functions for initializing system components, like seeding default data.
"""
import logging
# Only import SessionLocal and the necessary models
from app.db import SessionLocal
from app.models import RuleSet, Rule # Assuming Action is not needed for default seeding

# Get a logger for this module
logger = logging.getLogger(__name__)

def seed_default_ruleset():
    """
    Seeds the database with a default ruleset if one doesn't already exist.
    This function assumes the database tables have already been created.
    """
    db = SessionLocal()
    logger.info("Attempting to seed default ruleset...")
    try:
        # Check if a ruleset named "DEFAULT" already exists
        exists = db.query(RuleSet).filter(RuleSet.name == "DEFAULT").first()

        if not exists:
            logger.info("DEFAULT ruleset not found. Creating...")
            # Create the default ruleset record
            default_rs = RuleSet(name="DEFAULT", description="Allow all DICOM traffic and store unmodified")
            db.add(default_rs)
            db.commit() # Commit to get the ID for the ruleset
            db.refresh(default_rs) # Refresh to load the generated ID

            logger.info(f"DEFAULT ruleset created with ID: {default_rs.id}")

            # Create the default rule associated with the ruleset
            # A rule that applies no conditions (matches everything)
            # and specifies no actions (implies pass-through or requires further logic)
            rule = Rule(
                ruleset_id=default_rs.id,
                name="AllowAllPassThrough", # More descriptive name
                description="Matches all incoming data and performs no modifications.",
                logic_operator="ALL", # 'ALL' conditions must match (vacuously true if no conditions)
                priority=0 # Lowest priority (or highest depending on interpretation)
                # Conditions list is empty
                # Actions list is empty
            )
            db.add(rule)
            db.commit()
            logger.info(f"Default rule '{rule.name}' created for ruleset '{default_rs.name}'.")
            logger.info("Default ruleset seeding complete.")
        else:
            logger.info("DEFAULT ruleset already exists. Skipping seeding.")

    except Exception as e:
        logger.error(f"Error during default ruleset seeding: {e}", exc_info=True)
        db.rollback() # Rollback any partial changes on error
    finally:
        db.close() # Always close the session

# The initialize_system function is removed as its logic is handled elsewhere
# (partly in main.py lifespan, partly by the database initialization API endpoint)
