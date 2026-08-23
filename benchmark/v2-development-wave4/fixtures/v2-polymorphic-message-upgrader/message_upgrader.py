def upgrade_message(payload):
    result = dict(payload)
    result["version"] = 3
    return result
