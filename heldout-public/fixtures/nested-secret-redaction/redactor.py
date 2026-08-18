SENSITIVE = {"password"}


def redact(record):
    if isinstance(record, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE else redact(value)
            for key, value in record.items()
        }
    if isinstance(record, list):
        return [redact(value) for value in record]
    return record
