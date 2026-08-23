def rename_config(config, rules, version):
    result = dict(config)
    for old, new in rules.items():
        if old in result:
            result[new] = result.pop(old)
    result["version"] = version
    return result
