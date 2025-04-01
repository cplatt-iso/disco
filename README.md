# DISCO: DICOM Scrubbing & Compliance Orchestrator

**Author**: Chris Platt
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
  - **Action** → A single transformation, now using structured JSON parameters (e.g., `{"action_type": "regex", "target": "dicom_tag", "parameters": {"tag": "0010,0010", "pattern": "(.*)\\^(.*)", "replace": "Anon\\2"}}`).

- **Rule Engine**:
  - Retrieves RuleSets from the database.
  - Evaluates each Rule’s conditions against the incoming DICOM object and context.
  - Applies the first matching Rule’s actions.
  - Supports structured `parameters` for extensible action configuration.

- **Ruleset CLI Utility**:
  - Create, update, delete, and inspect rules and RuleSets.
  - Structured action input via JSON on the command line.
  - Outputs rule definitions as JSON for verification.

- **Database**:
  - SQLite/Postgres/MySQL (via SQLAlchemy).
  - Uses migrations (Alembic) for schema evolution (optional at this stage).

- **Python-based**:
  - **pydicom** for reading, modifying, and saving DICOM files.
  - **pynetdicom** as a DICOM Store SCP for real-time ingestion and transformation.

- **Local Dev**:
  - A Python virtual environment (`venv`).
  - Logging is enabled for debugging transformations and evaluation flow.
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
│       ├── rule_engine.py      # Core logic for evaluating rules and applying actions
│       ├── ruleset_api.py      # Business logic for CRUD on rules and RuleSets
│       ├── ruleset_cli.py      # CLI interface for ruleset operations
│       └── cstore_scp.py       # pynetdicom-based DICOM Store SCP handler
├── tests/
│   ├── __init__.py
│   ├── test_rules.py           # Unit tests for rules & conditions
│   └── test_actions.py         # Unit tests for actions
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Container orchestration (not yet fully implemented)
├── Dockerfile                  # Build instructions for containerizing the app
├── .gitignore                  # Ignores venv, pyc, etc.
└── README.md                   # This file

