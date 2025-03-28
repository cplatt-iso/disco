# DISCO: DICOM Insite Scrubbing & Compliance Orchestrator

**Author**: InsiteOne  
**Description**: DISCO is a tag morphing engine designed to match incoming DICOM objects (or file-based images) to specific conditions, then apply configurable actions (e.g., regex modifications, deletions, anonymization). Although initially built using Python and [pydicom](https://github.com/pydicom/pydicom), DISCO is designed with a pluggable adapter architecture that can later support [dcm4che](https://github.com/dcm4che/dcm4che) or other libraries.

---

## Project Overview

### Goals

1. **Tag Morphing Engine**: Evaluate DICOM metadata (and contextual info like AE title, port, IP) against a set of rules/conditions, then apply transformations.
2. **Flexible Matching**: Match on DICOM tags, network attributes, or even file paths.
3. **Custom Actions**: From simple deletes or regex replacements to advanced external script calls or SQL lookups.
4. **Future-Proof Design**: Containerized microservices, robust rule storage, and easy extensibility to new features (e.g., advanced anonymization).

### Key Components

- **Data Model** (SQLAlchemy):  
  - **RuleSet** → Groups multiple rules (e.g., “Research Anonymization”).  
  - **Rule** → Defines conditions and actions, plus priority/order.  
  - **Condition** → A single match criterion (e.g., `attribute='ae_title', operator='equals', value='PACS123'`).  
  - **Action** → A single transformation (e.g., `action_type='delete'`, `target='dicom_tag:0010,0020'`).

- **Rule Engine**:  
  - Retrieves RuleSets from the database.  
  - Evaluates each Rule’s conditions against the incoming DICOM object and context.  
  - Applies any matching actions in sequence (or stops after the first match if desired).

- **Database**:  
  - SQLite/Postgres/MySQL (via SQLAlchemy).  
  - Uses migrations (Alembic) for schema evolution (optional at this stage).

- **Python-based**:
  - **pydicom** for reading, modifying, and saving DICOM files (in progress).  
  - Potential to integrate dcm4che as a separate microservice in the future.

- **Local Dev**:  
  - A Python virtual environment (`venv`).  
  - Basic testing with [pytest](https://docs.pytest.org/en/stable/) (coming soon).

---

## Project Structure

```plaintext
disco/                          # Project root
├── app/
│   ├── __init__.py
│   ├── db.py                   # Database setup / session creation
│   ├── models.py               # SQLAlchemy models (RuleSet, Rule, Condition, Action)
│   ├── main.py                 # Entry point for setup tasks (db init, seeding, etc.)
│   └── services/
│       ├── __init__.py
│       └── rule_engine.py      # Core logic for evaluating rules and applying actions
├── tests/
│   ├── __init__.py
│   ├── test_rules.py           # Unit tests for rules & conditions
│   └── test_actions.py         # Unit tests for actions
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Container orchestration (not yet fully implemented)
├── Dockerfile                  # Build instructions for containerizing the app
├── .gitignore                  # Ignores venv, pyc, etc.
└── README.md                   # This file

