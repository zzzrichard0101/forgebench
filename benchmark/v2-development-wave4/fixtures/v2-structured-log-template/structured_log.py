def build_log_record(template, fields, secret_fields=()):
    message = template.format(**fields)
    return {"message": message, "fields": dict(fields)}
