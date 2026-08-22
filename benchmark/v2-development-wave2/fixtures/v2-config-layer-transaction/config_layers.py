def merge_layers(defaults: dict, file_config: dict, env_config: dict) -> dict:
    result = dict(defaults)
    result.update(file_config)
    result.update(env_config)
    return result

