# app/services/rule_engine.py
import re
import json
import logging
logger = logging.getLogger(__name__)

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import RuleSet, Rule, Condition, Action


class RuleEvaluator:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_ruleset(self, ruleset_id: int, context: Dict[str, Any], dicom_data: Any) -> None:
        ruleset = self.db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()
        if not ruleset:
            return

        sorted_rules = sorted(ruleset.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if self._rule_matches(rule, context, dicom_data):
                self._apply_actions(rule.actions, dicom_data)
                # break  # Uncomment if only the first matching rule should apply

    def _rule_matches(self, rule: Rule, context: Dict[str, Any], dicom_data: Any) -> bool:
        results = []
        for cond in rule.conditions:
            result = self._condition_matches(cond, context, dicom_data)
            results.append(result)

        if rule.logic_operator == "ALL":
            return all(results)
        else:
            return any(results)

    def _condition_matches(self, cond: Condition, context: Dict[str, Any], dicom_data: Any) -> bool:
        attr_value = self._get_attribute_value(cond.attribute, context, dicom_data)
        if attr_value is None:
            return False

        if cond.operator == "equals":
            return str(attr_value) == cond.value
        elif cond.operator == "starts_with":
            return str(attr_value).startswith(cond.value)
        elif cond.operator == "regex":
            return re.search(cond.value, str(attr_value)) is not None
        return False

    def _get_attribute_value(self, attribute: str, context: Dict[str, Any], dicom_data: Any) -> Any:
        if attribute in context:
            return context[attribute]

        if attribute.startswith("dicom_tag:"):
            tag_str = attribute.split("dicom_tag:")[1]
            group, elem = tag_str.split(',')
            group = int(group, 16)
            elem = int(elem, 16)
            if (group, elem) in dicom_data:
                return dicom_data[(group, elem)].value
            return None

        return None

    def _apply_actions(self, actions: List[Action], dicom_data: Any):
        for act in actions:
            logger.debug(f"Applying action: {act.action_type} to {act.target}")
            parameters = json.loads(act.parameters) if act.parameters else {}
            if act.action_type == "delete":
                self._delete_tag(act.target, parameters, dicom_data)
            elif act.action_type == "regex":
                logger.debug(f"Regex action params: {parameters}")
                self._apply_regex(act.target, parameters, dicom_data)
            elif act.action_type == "script":
                self._run_script(parameters, dicom_data)

    def _delete_tag(self, target: str, parameters: dict, dicom_data: Any):
        tag_str = parameters.get("tag")
        if tag_str:
            group, elem = tag_str.split(',')
            group = int(group, 16)
            elem = int(elem, 16)
            if (group, elem) in dicom_data:
                del dicom_data[(group, elem)]

    def _apply_regex(self, target: str, parameters: dict, dicom_data: Any):
        tag_str = parameters.get("tag")
        pattern = parameters.get("pattern")
        replacement = parameters.get("replace", "")
        if not tag_str or not pattern:
            return

        group, elem = tag_str.split(',')
        group = int(group, 16)
        elem = int(elem, 16)

        if (group, elem) in dicom_data:
            original_val = str(dicom_data[(group, elem)].value)
            new_val = re.sub(pattern, replacement, original_val)

            logger.debug(f"Applying regex on tag ({group:04X},{elem:04X})")
            logger.debug(f"Original: {original_val}")
            logger.debug(f"Pattern: {pattern}")
            logger.debug(f"Replacement: {replacement}")
            logger.debug(f"New value: {new_val}")

            dicom_data[(group, elem)].value = new_val

    def _run_script(self, parameters: dict, dicom_data: Any):
        pass

