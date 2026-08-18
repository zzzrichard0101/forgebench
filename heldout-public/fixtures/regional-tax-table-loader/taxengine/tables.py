import csv
import json


def load_tax_table(root, manifest):
    spec = json.loads(manifest.read_text(encoding="utf-8"))
    candidate = root / spec["table_file"]
    if candidate.suffix != ".csv":
        raise ValueError("tax table must be CSV")
    with candidate.open(encoding="utf-8", newline="") as stream:
        return {
            row["jurisdiction"]: float(row["rate"])
            for row in csv.DictReader(stream)
        }
