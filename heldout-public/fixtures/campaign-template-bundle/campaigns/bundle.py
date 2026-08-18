import json


def load_campaign_template(root, manifest):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / spec["template_file"]
    if candidate.suffix != ".html":
        raise ValueError("campaign template must be HTML")
    return candidate.read_text(encoding="utf-8")
