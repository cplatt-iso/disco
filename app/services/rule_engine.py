# app/services/rule_engine.py
import re
import json
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.models import RuleSet, Rule, Condition, Action

class RuleEvaluator:
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_ruleset(self, ruleset_id: int, context: Dict[str, Any], dicom_data: Any) -> None:
        """
        Evaluate all rules in the given ruleset against the context and apply matching actions.
        
        :param ruleset_id: ID of the ruleset to evaluate
        :param context: a dict of attributes (e.g. {"port": "10104", "ae_title": "PACS123"})
        :param dicom_data: a pydicom dataset or wrapper
        """
        ruleset = self.db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()
        if not ruleset:
            return  # or raise exception

        # Sort rules by priority, descending or ascending depending on your logic
        sorted_rules = sorted(ruleset.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if self._rule_matches(rule, context, dicom_data):
                self._apply_actions(rule.actions, dicom_data)
                # Decide if you want to continue or break if you only apply the first match
                # break

    def _rule_matches(self, rule: Rule, context: Dict[str, Any], dicom_data: Any) -> bool:
        """Return True if all/any conditions match (depending on rule.logic_operator)."""
        results = []
        for cond in rule.conditions:
            result = self._condition_matches(cond, context, dicom_data)
            results.append(result)
        
        if rule.logic_operator == "ALL":
            return all(results)
        else:  # "ANY"
            return any(results)

    def _condition_matches(self, cond: Condition, context: Dict[str, Any], dicom_data: Any) -> bool:
        """
        Evaluate a single condition:
          - cond.attribute might be 'port', 'ae_title', 'dicom_tag:0010,0020', etc.
          - cond.operator might be 'equals', 'regex', etc.
          - cond.value is the comparison value.
        """
        attr_value = self._get_attribute_value(cond.attribute, context, dicom_data)
        if attr_value is None:
            return False
        
        if cond.operator == "equals":
            return str(attr_value) == cond.value
        elif cond.operator == "starts_with":
            return str(attr_value).startswith(cond.value)
        elif cond.operator == "regex":
            return re.search(cond.value, str(attr_value)) is not None
        # ... add more operators as needed
        return False

    def _get_attribute_value(self, attribute: str, context: Dict[str, Any], dicom_data: Any) -> Any:
        """
        If attribute = "port" => context["port"]
        If attribute starts with "dicom_tag:" => read that tag from dicom_data
        etc.
        """
        if attribute in context:
            return context[attribute]
        
        if attribute.startswith("dicom_tag:"):
            tag_str = attribute.split("dicom_tag:")[1]
            # parse "0010,0020" => (0x0010, 0x0020)
            group, elem = tag_str.split(',')
            group = int(group, 16)
            elem = int(elem, 16)
            # For pydicom:
            if (group, elem) in dicom_data:
                return dicom_data[(group, elem)].value
            return None
        
        return None

    def _apply_actions(self, actions: List[Action], dicom_data: Any):
        """Apply each action to the dicom_data (or context if needed)."""
        for act in actions:
            if act.action_type == "delete":
                self._delete_tag(act.target, dicom_data)
            elif act.action_type == "regex":
                self._apply_regex(act.target, act.parameters, dicom_data)
            elif act.action_type == "script":
                self._run_script(act.parameters, dicom_data)
            # etc.

    def _delete_tag(self, target: str, dicom_data: Any):
        if target.startswith("dicom_tag:"):
            tag_str = target.split("dicom_tag:")[1]
            group, elem = tag_str.split(',')
            group = int(group, 16)
            elem = int(elem, 16)
            if (group, elem) in dicom_data:
                del dicom_data[(group, elem)]

    def _apply_regex(self, target: str, parameters: str, dicom_data: Any):
        # parse parameters JSON
        params = json.loads(parameters)
        pattern = params.get("pattern")
        replacement = params.get("replace", "")
        if not pattern:
            return
        
        if target.startswith("dicom_tag:"):
            tag_str = target.split("dicom_tag:")[1]
            group, elem = tag_str.split(',')
            group = int(group, 16)
            elem = int(elem, 16)
            
            if (group, elem) in dicom_data:
                original_val = str(dicom_data[(group, elem)].value)
                print("DEBUG - Original Val:", repr(original_val))
                print("DEBUG - Pattern:", pattern, "Replacement:", replacement)

                new_val = re.sub(pattern, replacement, original_val)
                print("DEBUG: new_val =", repr(new_val))
                dicom_data[(group, elem)].value = new_val
    
    def _run_script(self, parameters: str, dicom_data: Any):
        # Potentially call an external script with relevant data
        # This can get complex: you might pass the DICOM or context to the script
        pass

