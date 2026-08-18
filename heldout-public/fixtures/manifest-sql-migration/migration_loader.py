import json


def load_migration(root, manifest):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / spec["script"]
    if ".sql" not in candidate.name:
        raise ValueError("migration must be SQL")
    return candidate.read_text(encoding="utf-8")
