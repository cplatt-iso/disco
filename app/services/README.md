# DISCO Service Utilities

This directory contains core service scripts used by the DISCO processing system. These utilities include the DICOM tag morphing rule engine, DICOM SCP listener, and command-line tools for managing rulesets.

---

## Contents

- `ruleset_cli.py`: Manage rulesets and rules via command line
- `rule_engine.py`: Core rule evaluation engine
- `cstore_scp.py`: DICOM Store SCP that receives and processes DICOM objects

---

## `ruleset_cli.py`

A command-line utility for creating, viewing, modifying, and deleting rulesets and rules.

### Usage Examples

#### List all rulesets

```bash
python -m app.services.ruleset_cli --list
```

#### Inspect a specific ruleset by ID

```bash
python -m app.services.ruleset_cli --id 1
```

#### Create a new ruleset (and optionally, an initial rule)

```bash
python -m app.services.ruleset_cli --create \
  --name "Fix DICOM Fields" \
  --desc "Handles anonymization of test data" \
  --logic ALL \
  --priority 10 \
  --act '{"action_type": "regex", "target": "dicom_tag", "parameters": {"tag": "0010,0010", "pattern": "(.*)\\^(.*)", "replace": "Anon\\2"}}' \
  --act '{"action_type": "delete", "target": "dicom_tag", "parameters": {"tag": "0010,0020"}}'
```

#### Add a rule to an existing ruleset

```bash
python -m app.services.ruleset_cli --add-rule 1 \
  --name "Remove Study UID" \
  --logic ANY \
  --priority 20 \
  --cond "ae_title:equals:PACS123" \
  --act '{"action_type": "delete", "target": "dicom_tag", "parameters": {"tag": "0020,000D"}}'
```

#### Update an existing ruleset

```bash
python -m app.services.ruleset_cli --update 1 --name "Updated Name" --desc "Updated description"
```

#### Delete a ruleset

```bash
python -m app.services.ruleset_cli --delete 1
```

---

## `rule_engine.py`

Core rule processor that applies actions to a DICOM object based on context and metadata.

### Features

- Match DICOM attributes or contextual fields (`ae_title`, `port`, etc.)
- Evaluate rules using logical operators (ALL / ANY)
- Perform actions:
  - `delete`: remove a tag
  - `regex`: transform tag value via regex
  - `script`: placeholder for external script integration

### Example Usage (Python)

```python
from app.services.rule_engine import RuleEvaluator
from app.db import SessionLocal

db = SessionLocal()
evaluator = RuleEvaluator(db)

context = {"ae_title": "STORESCU", "port": "127.0.0.1"}
evaluator.evaluate_ruleset(ruleset_id=1, context=context, dicom_data=ds)
```

---

## `cstore_scp.py`

A DICOM Store SCP that receives images via DIMSE C-STORE and processes them using the rule engine.

### Usage

```bash
python -m app.services.cstore_scp
```

### Behavior

- Accepts all storage SOP classes
- Writes incoming DICOMs to `dicom_inbound/` by default
- Applies all known rulesets to each object
- Supports extracting context like AE title and IP address for rule matching

---

## Notes

- All actions must conform to the updated JSON structure:
  ```json
  {
    "action_type": "regex",
    "target": "dicom_tag",
    "parameters": {
      "tag": "0010,0010",
      "pattern": "(.*)\\^(.*)",
      "replace": "Anon\\2"
    }
  }
  ```
- All tag values must be in `gggg,eeee` hex format.
- All parameters must be JSON-serializable and passed as strings on the CLI.

---

