def redact_headers(headers, sensitive=()):
    blocked = {name.lower() for name in sensitive}
    return [(name.lower(), "[REDACTED]" if name.lower() in blocked else value) for name, value in headers]
