from pathlib import Path
from fastapi import FastAPI
from .loaders import load_requirements, load_system
from .engine import assess

BASE=Path(__file__).resolve().parent.parent
REQS=BASE/"data/requirements/demo_requirements.yaml"
SYSTEM=BASE/"data/systems/recruitment_noncompliant.yaml"

app=FastAPI(title="ACER v3",version="0.3.0")

@app.get("/")
def root():
    return {"project":"ACER v3","purpose":"Data and evaluation foundation"}

@app.get("/assess")
def assess_demo():
    return assess(load_system(SYSTEM),load_requirements(REQS)).model_dump()
