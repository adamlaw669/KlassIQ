import json
from pathlib import Path

CURRICULUM_PATH = Path(__file__).resolve().parents[1] / "data" / "curriculum_map.json"

def get_curriculum_objectives(grade: str, subject: str, topic: str):
    try:
        with open(CURRICULUM_PATH, "r") as f:
            data = json.load(f)
        return data.get(grade, {}).get(subject, {}).get(topic, {}).get("objectives", [])
    except Exception as e:
        return [f"Error loading curriculum: {e}"]
