import json


def load_fragment(root, manifest):
    config = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / config["fragment"]
    if candidate.suffix != ".json":
        raise ValueError("fragment must be JSON")
    return json.loads(candidate.read_text(encoding="utf-8"))
