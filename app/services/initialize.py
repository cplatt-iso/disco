# app/services/initialize.py
import os
from app.db import init_db, SessionLocal
from app.models import RuleSet, Rule, Action
import json

def initialize_system():
    db_path = os.getenv("DATABASE_PATH", "sqlite:///./app.db")

    # Check if the DB file exists (basic check for SQLite)
    if db_path.startswith("sqlite") and not os.path.exists("app.db"):
        print("Initializing database and seeding DEFAULT ruleset...")
        init_db()
        seed_default_ruleset()
    else:
        print("Database already exists. Skipping seeding.")

def seed_default_ruleset():
    db = SessionLocal()

    default_rs = RuleSet(name="DEFAULT", description="Allow all DICOM traffic and store unmodified")
    db.add(default_rs)
    db.commit()
    db.refresh(default_rs)

    # A default rule that applies no conditions and just passes through the object
    rule = Rule(
        ruleset_id=default_rs.id,
        name="AllowAll",
        logic_operator="ALL",
        priority=0
    )

    # No conditions (matches everything)
    # No actions (passes data as-is)

    db.add(rule)
    db.commit()
    db.close()

