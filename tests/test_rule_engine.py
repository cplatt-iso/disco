# tests/test_rule_engine.py

import pytest
from sqlalchemy.orm import Session
from pydicom.dataset import Dataset

from app.db import SessionLocal, init_db
from app.services.rule_engine import RuleEvaluator
from app.models import RuleSet, Rule, Condition, Action
import json

@pytest.fixture
def db_session():
    """Creates an in-memory DB and returns a fresh session."""
    import os
    os.environ["TESTING"] = "1"  # ensure we use in-memory if your db.py checks TESTING
    init_db()
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def sample_ruleset(db_session: Session):
    """
    Seeds a RuleSet with a single Rule that:
      - Matches port=10104 AND AE title=PACS123
      - Has two actions:
        1) Delete (0010,0020)
        2) Regex transform on (0008,0090) => "Dr^Jones" => "MDJones"
    """
    rs = RuleSet(name="RegexAndDeleteRuleSet")
    rule = Rule(name="RegexAndDeleteRule", logic_operator="ALL", priority=10)
    
    # Conditions: port=10104, ae_title=PACS123
    rule.conditions = [
        Condition(attribute="port", operator="equals", value="10104"),
        Condition(attribute="ae_title", operator="equals", value="PACS123"),
    ]

    # Actions:
    # (1) delete (0010,0020) => removes PatientID
    delete_action = Action(
        action_type="delete",
        target="dicom_tag:0010,0020"
    )
    # (2) regex => transforms ReferringPhysicianName (0008,0090)
    # pattern '^Dr\^(.*)' => capturing everything after 'Dr^'
    # replace 'MD\1' => yields "MDJones" if original is "Dr^Jones"
    parameters = json.dumps({
        "pattern": "^Dr\\^(.*)\\s*$",
        "replace": "MD\\1"
    })
    regex_action = Action(
        action_type="regex",
        target="dicom_tag:0008,0090",
        parameters=parameters
    )
    rule.actions.append(delete_action)
    rule.actions.append(regex_action)
    
    rs.rules.append(rule)
    db_session.add(rs)
    db_session.commit()
    return rs

def test_basic_rule(db_session: Session, sample_ruleset: RuleSet):
    """
    Test that the rule engine applies BOTH the delete and the regex actions:
      - port=10104, ae_title=PACS123 => remove (0010,0020) and transform (0008,0090).
    """
    ds = Dataset()
    ds.PatientName = "John^Doe"           # (0010,0010)
    ds.AccessionNumber = "ABC123"         # (0008,0050), not relevant here
    ds.ReferringPhysicianName = "Dr^Jones"  # (0008,0090) => should become "MDJones"
    ds.PatientID = "12345"               # (0010,0020) => should get deleted

    # Evaluate the new rule set
    evaluator = RuleEvaluator(db_session)
    evaluator.evaluate_ruleset(sample_ruleset.id, {
        "port": "10104",
        "ae_title": "PACS123",
    }, ds)

    # (1) "delete" action => (0010,0020) no longer present
    assert not hasattr(ds, "PatientID"), "PatientID tag should have been deleted"
    # (2) "regex" action => "Dr^Jones" => "MDJones"
    assert ds.ReferringPhysicianName == "MDJones"

