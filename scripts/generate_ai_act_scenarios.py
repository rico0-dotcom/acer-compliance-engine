from pathlib import Path
import argparse
import random
import yaml

BASE_COMPONENTS = [
    {"id":"candidate_portal","type":"user_interface","properties":{}},
    {"id":"resume_llm","type":"generative_ai","properties":{"purpose":"resume_information_extraction"}},
    {"id":"scoring_model","type":"decision_engine","properties":{}},
    {"id":"final_decision","type":"final_decision","properties":{"logging_enabled":True}},
    {"id":"hr_dashboard","type":"human_interface","properties":{}},
]

BASE_FLOWS = [
    {"source":"candidate_portal","target":"resume_llm","data":"candidate_data"},
    {"source":"resume_llm","target":"scoring_model","data":"candidate_data"},
    {"source":"scoring_model","target":"final_decision","data":"candidate_data"},
    {"source":"final_decision","target":"hr_dashboard","data":"candidate_data"},
]

DEFECTS = [
    "risk_management",
    "data_governance",
    "logging",
    "transparency_mechanism",
    "human_review",
    "human_intervention_flow",
    "performance_monitoring",
    "article50_notice",
    "clean",
]

def make_scenario(i, defect):
    comps=[dict(x, properties=dict(x.get("properties",{}))) for x in BASE_COMPONENTS]
    flows=list(BASE_FLOWS)
    attributes={
        "system_is_high_risk": True,
        "uses_training_data": True,
        "direct_ai_interaction": True,
    }

    if defect=="risk_management":
        pass
    elif defect=="data_governance":
        pass
    elif defect=="logging":
        comps[3]["properties"]["logging_enabled"]=False
    elif defect=="transparency_mechanism":
        pass
    elif defect=="human_review":
        pass
    elif defect=="human_intervention_flow":
        comps.append({"id":"human_review","type":"human_review",
                      "properties":{"can_override":True,"can_stop":True}})
    elif defect=="performance_monitoring":
        pass
    elif defect=="article50_notice":
        attributes["transparency_notice"]=False
    elif defect=="clean":
        pass

    return {
        "id":f"ai-act-scenario-{i:03d}",
        "name":f"EU AI Act Recruitment Scenario {i:03d}",
        "domain":"recruitment",
        "version":"1.0",
        "components":comps,
        "data":[{"id":"candidate_data","classification":"personal_data"}],
        "flows":flows,
        "attributes":attributes,
        "objectives":{"compliance":1.0,"performance":0.8,"cost":0.7},
        "defect_label":defect
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--n",type=int,default=30)
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--out",default="data/systems/eu_ai_act_scenarios")
    args=parser.parse_args()

    rnd=random.Random(args.seed)
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)

    manifest=[]
    for i in range(1,args.n+1):
        defect=rnd.choice(DEFECTS)
        s=make_scenario(i,defect)
        path=out/f"{s['id']}.yaml"
        path.write_text(
            yaml.safe_dump({k:v for k,v in s.items() if k!="defect_label"},sort_keys=False),
            encoding="utf-8"
        )
        manifest.append({"system_id":s["id"],"defect":defect})

    (out/"manifest.yaml").write_text(
        yaml.safe_dump({"seed":args.seed,"count":args.n,"cases":manifest},sort_keys=False),
        encoding="utf-8"
    )
    print(f"Generated {len(manifest)} AI Act scenarios in {out}")

if __name__=="__main__":
    main()
