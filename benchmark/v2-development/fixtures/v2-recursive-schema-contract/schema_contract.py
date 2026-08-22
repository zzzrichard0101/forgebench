def validate(value, schema: dict) -> bool:
    kind = schema.get("type")
    if kind == "integer":
        return isinstance(value, int)
    if kind == "string":
        return isinstance(value, str)
    if kind == "array":
        return isinstance(value, list) and all(validate(item, schema["items"]) for item in value)
    if kind == "object":
        if not isinstance(value, dict):
            return False
        return all(key in value and validate(value[key], child) for key, child in schema.get("properties", {}).items())
    return False

