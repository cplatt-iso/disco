# tests/test_engine.py
import pytest
import pydicom
from pydicom.dataset import Dataset
from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.models import RuleSet, Rule, Condition, Action
from app.services.rule_engine import RuleEvaluator


@pytest.fixture(scope="module")
def db_session():
    """
    Sets up an in-memory SQLite database for testing.
    For a real test environment, you might also use a
    temp file or a test container for Postgres.
    """
    # Overwrite the default DB to in-memory for testing
    # You can also do this by setting an env variable before engine creation
    import os
    os.environ["TESTING"] = "1"
    
    # Initialize schema in memory
    init_db()
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_ruleset(db_session: Session):
    """
    Creates a sample RuleSet with one Rule that deletes PatientID
    if port=10104 and AE_TITLE=PACS123
    """
    rs = RuleSet(name="Test RuleSet")
    rule = Rule(name="Port10104_AND_AE_PACS123", logic_operator="ALL", priority=10)
    rule.conditions = [
        Condition(attribute="port", operator="equals", value="10104"),
        Condition(attribute="ae_title", operator="equals", value="PACS123"),
    ]
    rule.actions = [
        Action(action_type="delete", target="dicom_tag:0010,0020"),  # PatientID
    ]
    rs.rules.append(rule)
    db_session.add(rs)
    db_session.commit()
    return rs


def test_rule_engine_deletes_tag(db_session: Session, sample_ruleset: RuleSet):
    """
    Verify that the rule engine deletes PatientID (0010,0020)
    when port=10104 and AE_TITLE=PACS123 match the conditions.
    """
    # Create a pydicom dataset with a PatientID
    ds = Dataset()
    ds.PatientID = "12345"  # This is tag (0010,0020)

    # Build the context that should match the rule
    context = {
        "port": "10104",
        "ae_title": "PACS123",
    }

    evaluator = RuleEvaluator(db_session)
    # Evaluate the entire ruleset
    evaluator.evaluate_ruleset(sample_ruleset.id, context, ds)

    # Check that the tag is removed
    assert not hasattr(ds, "PatientID"), "PatientID tag should have been deleted"

