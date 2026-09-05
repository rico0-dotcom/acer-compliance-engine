from pathlib import Path
import yaml
from .models import Requirement, SystemModel, GroundTruthCase, RegulatoryRecord

def load_yaml(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_requirements(path):
    raw = load_yaml(path)
    return [Requirement.model_validate(x) for x in raw["requirements"]]

def load_system(path):
    return SystemModel.model_validate(load_yaml(path))

def load_ground_truth(path):
    raw = load_yaml(path)
    return [GroundTruthCase.model_validate(x) for x in raw["cases"]]

def load_regulations(path):
    raw = load_yaml(path)
    return [RegulatoryRecord.model_validate(x) for x in raw["records"]]
