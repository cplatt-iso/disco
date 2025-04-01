# app/services/ruleset_api.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import RuleSet, Rule, Condition, Action
from datetime import datetime

# ------- Ruleset APIs --------

def get_all_rulesets(db: Session) -> List[RuleSet]:
    return db.query(RuleSet).all()

def get_ruleset_by_id(db: Session, ruleset_id: int) -> Optional[RuleSet]:
    return db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()

def create_ruleset(db: Session, name: str, description: Optional[str] = None) -> RuleSet:
    now = datetime.utcnow()
    new_rs = RuleSet(name=name, description=description, created_at=now, updated_at=now)
    db.add(new_rs)
    db.commit()
    db.refresh(new_rs)
    return new_rs

def update_ruleset(db: Session, ruleset_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[RuleSet]:
    rs = get_ruleset_by_id(db, ruleset_id)
    if not rs:
        return None
    if name:
        rs.name = name
    if description:
        rs.description = description
    rs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rs)
    return rs

def delete_ruleset(db: Session, ruleset_id: int, cascade: bool = False) -> bool:
    rs = get_ruleset_by_id(db, ruleset_id)
    if not rs:
        return False

    if cascade:
        for rule in rs.rules:
            for cond in rule.conditions:
                db.delete(cond)
            for act in rule.actions:
                db.delete(act)
            db.delete(rule)

    db.delete(rs)
    db.commit()
    return True


# ------- Add Rule to Ruleset --------

def add_rule_to_ruleset(
    db: Session,
    ruleset_id: int,
    name: str,
    logic_operator: str,
    priority: int,
    conditions: List[dict],
    actions: List[dict]
) -> Rule:
    ruleset = get_ruleset_by_id(db, ruleset_id)
    if not ruleset:
        raise ValueError(f"Ruleset ID {ruleset_id} not found")

    rule = Rule(
        name=name,
        logic_operator=logic_operator,
        priority=priority,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    for cond in conditions:
        rule.conditions.append(Condition(**cond))

    for act in actions:
        rule.actions.append(Action(**act))

    ruleset.rules.append(rule)
    db.commit()
    db.refresh(rule)
    return rule

# ------- Helper to serialize --------

def serialize_ruleset(rs: RuleSet) -> dict:
    return {
        "id": rs.id,
        "name": rs.name,
        "description": rs.description,
        "created_at": rs.created_at.isoformat() if rs.created_at else None,
        "updated_at": rs.updated_at.isoformat() if rs.updated_at else None,
        "rules": [serialize_rule(r) for r in rs.rules]
    }

def serialize_rule(rule: Rule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "logic_operator": rule.logic_operator,
        "priority": rule.priority,
        "conditions": [serialize_condition(c) for c in rule.conditions],
        "actions": [serialize_action(a) for a in rule.actions]
    }

def serialize_condition(cond: Condition) -> dict:
    return {
        "id": cond.id,
        "attribute": cond.attribute,
        "operator": cond.operator,
        "value": cond.value
    }

def serialize_action(action: Action) -> dict:
    return {
        "id": action.id,
        "action_type": action.action_type,
        "target": action.target,
        "parameters": action.parameters
    }

