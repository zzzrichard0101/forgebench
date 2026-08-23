def load_environment(schema, environ, prefix="APP_"):
    result = {}
    for name, spec in schema.items():
        env_name = spec["env"]
        if env_name in environ:
            value = environ[env_name]
        elif "default" in spec:
            value = spec["default"]
        else:
            raise ValueError(f"missing {env_name}")
        if spec["type"] == "int":
            value = int(value)
        elif spec["type"] == "bool":
            value = str(value).lower() == "true"
        result[name] = value
    return result
