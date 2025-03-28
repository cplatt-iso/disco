# tests/test_rule_engine.py
import pytest
from app.db import SessionLocal, init_db
from app.services.rule_engine import RuleEvaluator
from app.models import RuleSet
import pydicom
from pydicom.dataset import Dataset

@pytest.fixture
def db_session():
    # For a real test, you might use an in-memory SQLite, ephemeral DB, etc.
    init_db()
    yield SessionLocal()

def test_basic_rule(db_session):
    # Prepare a pydicom dataset
    ds = Dataset()
    ds.PatientName = "Dr.Jones"
    ds.AccessionNumber = "ABC123"
    ds[0x0008, 0x0090] = "Dr.Jones"  # for the "regex" action example

    # Suppose rule_set_id = 1 is the seeded "Test RuleSet"
    rule_set_id = 1
    evaluator = RuleEvaluator(db_session)

    context = {
        "port": "10104",
        "ae_title": "PACS123",
    }

    evaluator.evaluate_ruleset(rule_set_id, context, ds)
    
    # After applying "delete" action, AccessionNumber (0010,0020) should be gone
    # or in your code it might be something else; adjust accordingly
    # Example: if your sample rule used 0010,0020 => check it's gone
    # Also check the regex change was applied
    # e.g. "Dr.Jones" => "MDJones"
    
    # Make sure ds[0x0008,0x0090] was updated:
    assert ds[0x0008,0x0090].value == "MDJones"

