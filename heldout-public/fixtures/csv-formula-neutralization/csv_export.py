def export_cell(value):
    text = str(value)
    if text.startswith("="):
        return "'" + text
    return text
