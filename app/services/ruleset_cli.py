# app/services/ruleset_cli.py
import argparse
import json
from app.db import SessionLocal
from app.services import ruleset_api

def main():
    parser = argparse.ArgumentParser(description="Ruleset CLI Utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", action="store_true", help="List all rulesets")
    group.add_argument("-i", "--id", type=int, help="Inspect a ruleset by ID")
    group.add_argument("--create", action="store_true", help="Create a new ruleset")
    group.add_argument("--update", type=int, help="Update an existing ruleset by ID")
    group.add_argument("--delete", type=int, help="Delete a ruleset by ID")
    group.add_argument("--add-rule", type=int, help="Add a rule to the specified ruleset ID")

    parser.add_argument("--name", type=str, help="Name for create/update or rule")
    parser.add_argument("--desc", type=str, help="Description for create/update")
    parser.add_argument("--logic", type=str, choices=["ALL", "ANY"], help="Logic operator for rule")
    parser.add_argument("--priority", type=int, help="Priority for rule")
    parser.add_argument("--cond", action="append", help="Condition in format attribute:operator:value")
    parser.add_argument("--act", action="append", help="Action in format type:parameters_json")

    args = parser.parse_args()
    session = SessionLocal()

    if args.list:
        for rs in ruleset_api.get_all_rulesets(session):
            print(f"{rs.id}: {rs.name}")

    elif args.id:
        rs = ruleset_api.get_ruleset_by_id(session, args.id)
        if rs:
            print(json.dumps(ruleset_api.serialize_ruleset(rs), indent=2))
        else:
            print(f"Ruleset ID {args.id} not found")

    elif args.create:
        if not args.name:
            print("--name is required to create a ruleset")
        else:
            rs = ruleset_api.create_ruleset(session, args.name, args.desc)
            print(f"Created ruleset {rs.id}: {rs.name}")

            if args.logic and args.priority is not None:
                conds = []
                if args.cond:
                    for c in args.cond:
                        try:
                            attr, op, val = c.rsplit(":", 2)
                            conds.append({"attribute": attr, "operator": op, "value": val})
                        except ValueError:
                            print(f"Invalid condition format: {c}")

                acts = []
                if args.act:
                    for a in args.act:
                        try:
                            act_data = json.loads(a)
                            # Serialize parameters back to JSON string if it's a dict
                            if isinstance(act_data.get("parameters"), dict):
                                act_data["parameters"] = json.dumps(act_data["parameters"])
                            acts.append(act_data)

                        except json.JSONDecodeError:
                            print(f"Invalid JSON format in action: {a}")

                rule = ruleset_api.add_rule_to_ruleset(
                    session,
                    ruleset_id=rs.id,
                    name=args.name,
                    logic_operator=args.logic,
                    priority=args.priority,
                    conditions=conds,
                    actions=acts
                )
                print(f"Added rule {rule.id} to newly created ruleset {rs.id}")
                rs = ruleset_api.get_ruleset_by_id(session, rs.id)
                print(json.dumps(ruleset_api.serialize_ruleset(rs), indent=2))

    elif args.update:
        if not args.name and not args.desc:
            print("Specify at least one of --name or --desc to update")
        else:
            rs = ruleset_api.update_ruleset(session, args.update, args.name, args.desc)
            if rs:
                print(f"Updated ruleset {rs.id}: {rs.name}")
                print(json.dumps(ruleset_api.serialize_ruleset(rs), indent=2))
            else:
                print(f"Ruleset ID {args.update} not found")

    elif args.delete:
        success = ruleset_api.delete_ruleset(session, args.delete, cascade=True)
        if success:
            print(f"Deleted ruleset ID {args.delete}")
        else:
            print(f"Ruleset ID {args.delete} not found")

    elif args.add_rule:
        rs = ruleset_api.get_ruleset_by_id(session, args.add_rule)
        if not rs:
            print(f"Ruleset ID {args.add_rule} not found")
        elif not args.name or not args.logic or args.priority is None:
            print("--name, --logic, and --priority are required to add a rule")
        else:
            conds = []
            if args.cond:
                for c in args.cond:
                    try:
                        attr, op, val = c.rsplit(":", 2)
                        conds.append({"attribute": attr, "operator": op, "value": val})
                    except ValueError:
                        print(f"Invalid condition format: {c}")

            acts = []
            if args.act:
                for a in args.act:
                    try:
                        act_data = json.loads(a)
                        acts.append(act_data)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON format in action: {a}")

            rule = ruleset_api.add_rule_to_ruleset(
                session,
                ruleset_id=args.add_rule,
                name=args.name,
                logic_operator=args.logic,
                priority=args.priority,
                conditions=conds,
                actions=acts
            )
            print(f"Added rule {rule.id} to ruleset {args.add_rule}")
            rs = ruleset_api.get_ruleset_by_id(session, args.add_rule)
            print(json.dumps(ruleset_api.serialize_ruleset(rs), indent=2))

    session.close()

if __name__ == "__main__":
    main()
