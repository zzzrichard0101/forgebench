import json


def load_catalog(root, manifest):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / spec["catalog"]
    if candidate.suffix.lower() != ".txt":
        raise ValueError("catalog must be text")
    entries = {}
    for line in candidate.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        entries[key.strip()] = value.strip()
    return entries
