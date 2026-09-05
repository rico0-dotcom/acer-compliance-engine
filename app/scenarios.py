from pathlib import Path
import random
import yaml

COMPONENTS = [
    ("candidate_portal","user_interface",{}),
    ("resume_llm","generative_ai",{"purpose":"resume_information_extraction"}),
    ("scoring_model","decision_engine",{}),
    ("final_decision","final_decision",{"logging_enabled":True}),
    ("hr_dashboard","human_interface",{}),
]

BASE_FLOWS = [
    {"source":"candidate_portal","target":"resume_llm","data":"candidate_data"},
    {"source":"resume_llm","target":"scoring_model","data":"candidate_data"},
    {"source":"scoring_model","target":"final_decision","data":"candidate_data"},
    {"source":"final_decision","target":"hr_dashboard","data":"candidate_data"},
]

def generate_scenarios(n=30, seed=42):
    rnd=random.Random(seed)
    scenarios=[]
    for i in range(1,n+1):
        comps=[{"id":a,"type":b,"properties":dict(c)} for a,b,c in COMPONENTS]
        flows=list(BASE_FLOWS)
        attributes={"transparency_notice":True,"fairness_tested":True}

        defect_pool=["no_human","no_logging","no_transparency","unfair","clean"]
        defect=rnd.choice(defect_pool)

        if defect=="no_human":
            pass
        elif defect=="no_logging":
            comps[3]["properties"]["logging_enabled"]=False
        elif defect=="no_transparency":
            attributes["transparency_notice"]=False
        elif defect=="unfair":
            attributes["fairness_tested"]=False

        scenarios.append({
            "id":f"scenario-{i:03d}",
            "name":f"Recruitment AI Scenario {i:03d}",
            "domain":"recruitment",
            "version":"1.0",
            "components":comps,
            "data":[{"id":"candidate_data","classification":"personal_data"}],
            "flows":flows,
            "attributes":attributes,
            "objectives":{"compliance":1.0,"performance":0.8,"cost":0.7},
            "defect_label":defect
        })
    return scenarios

def write_scenarios(out_dir, n=30, seed=42):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    scenarios=generate_scenarios(n,seed)
    for s in scenarios:
        p=out/f"{s['id']}.yaml"
        p.write_text(yaml.safe_dump({k:v for k,v in s.items() if k!="defect_label"},sort_keys=False),encoding="utf-8")
    (out/"scenario_manifest.yaml").write_text(
        yaml.safe_dump({"seed":seed,"count":n,"labels":[{"id":s["id"],"defect":s["defect_label"]} for s in scenarios]},sort_keys=False),
        encoding="utf-8"
    )
    return scenarios
