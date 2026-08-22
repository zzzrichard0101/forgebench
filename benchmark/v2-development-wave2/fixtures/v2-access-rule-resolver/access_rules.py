def is_allowed(user: str, resource: str, action: str, rules: list[dict], groups: dict[str, list[str]]) -> bool:
    for rule in rules:
        if rule["subject"] == user and rule["resource"] == resource and rule["action"] == action:
            return rule["effect"] == "allow"
    return False

