import json


class FileConditionsProvider:
    """Reads rainfall (mm in next 3h, per ward) and reservoir level (%) from a JSON file.
    Replace with a provider that calls IMD / Water Resources Dept. feeds in production."""

    def __init__(self, path):
        self.path = path

    def get(self, ward_id):
        with open(self.path, encoding="utf-8") as f:
            d = json.load(f)
        return float(d["rainfall_mm_3h"].get(ward_id, 0.0)), float(d.get("reservoir_level_pct", 0.0))
