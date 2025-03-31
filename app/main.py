# app/main.py
from .db import init_db, SessionLocal
from .models import RuleSet, Rule, Condition, Action
import json

def seed_data():
    """Create a sample RuleSet with conditions and actions that
    match your test scenario."""
    db = SessionLocal()

    # Create a RuleSet named "Test RuleSet"
    rs = RuleSet(name="Test RuleSet")
    db.add(rs)
    db.commit()
    db.refresh(rs)  # so rs.id is available

    # Create a Rule that:
    # - Matches port=10104 AND ae_title=PACS123
    # - Applies two actions:
    #     1) Regex on (0008,0090) => transform "Dr^Jones" to "MDJones"
    #     2) Delete (0010,0020)
    rule = Rule(
        ruleset_id=rs.id,
        name="RegexAndDeleteRule",
        logic_operator="ALL",
        priority=10
    )

    # Two matching conditions
    rule.conditions = [
        Condition(attribute="port", operator="equals", value="10104"),
        Condition(attribute="ae_title", operator="equals", value="PACS123"),
    ]

    # Action 1: Regex transformation for (0008,0090)
    # pattern = '^Dr\^(.*)' and replace = 'MD\1'
    # This will transform "Dr^Jones" to "MDJones", allowing trailing whitespace
    import json
    parameters = json.dumps({
        "pattern": "^Dr\\^(.*)\\s*$",  # allows trailing whitespace
        "replace": "MD\\1"
    })
    regex_action = Action(
        action_type="regex",
        target="dicom_tag:0008,0090",
        parameters=parameters
    )
    rule.actions.append(regex_action)

    # Action 2: Delete PatientID (0010,0020)
    delete_action = Action(
        action_type="delete",
        target="dicom_tag:0010,0020"
    )
    rule.actions.append(delete_action)

    print("DEBUG: Seeding multi-action rule (regex + delete)")

    db.add(rule)
    db.commit()
    db.close()


def setup_database():
    """Create all tables and seed sample data."""
    init_db()     # Creates the tables
    seed_data()   # Inserts our test data

if __name__ == "__main__":
    setup_database()

