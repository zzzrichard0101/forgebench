import json
import tomllib


def load_rollout_plan(root, manifest):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / spec["rollout_file"]
    if candidate.suffix != ".toml":
        raise ValueError("rollout plan must be TOML")
    with candidate.open("rb") as stream:
        return tomllib.load(stream)["cohorts"]
