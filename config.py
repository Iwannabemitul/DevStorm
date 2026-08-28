import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

with open(DATA_DIR / "jobs.json", encoding="utf-8") as file:
    JOB_DATA = json.load(file)

with open(DATA_DIR / "skills.json", encoding="utf-8") as file:
    ALL_TECH_SKILLS = json.load(file)

PROFICIENCY_OPTIONS = ["Beginner (0.4)", "Intermediate (0.8)", "Advanced (1.0)"]
PROFICIENCY_WEIGHTS = {
    "Beginner (0.4)": 0.4,
    "Intermediate (0.8)": 0.8,
    "Advanced (1.0)": 1.0,
}
