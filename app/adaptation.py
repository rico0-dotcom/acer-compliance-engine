from copy import deepcopy
from .models import Component, Flow

def apply_tactic(system, tactic):
    u=deepcopy(system); a=tactic["action"]
    if a["type"]=="add_component":
        if not any(c.id==a["id"] for c in u.components):
            u.components.append(Component(id=a["id"], type=a["component_type"], properties=a.get("properties",{})))
    elif a["type"]=="add_flow":
        if not any(f.source==a["source"] and f.target==a["target"] for f in u.flows):
            u.flows.append(Flow(source=a["source"], target=a["target"], data=a.get("data")))
    elif a["type"]=="set_property":
        for c in u.components:
            if c.id==a["component_id"]:
                c.properties[a["property"]]=a["value"]
                break
        else:
            raise ValueError(f"Component not found: {a['component_id']}")
    elif a["type"]=="set_attribute":
        u.attributes[a["attribute"]]=a["value"]
    else:
        raise ValueError(f"Unsupported action: {a['type']}")
    u.version=f"{system.version}+adaptive"
    return u

def tactic_score(tactic):
    return (float(tactic.get("compliance_gain",0))*10
            -float(tactic.get("cost",0))
            -float(tactic.get("disruption",0))
            -float(tactic.get("risk",0)))

def rank_tactics(tactics):
    return sorted(tactics,key=tactic_score,reverse=True)

def applicable_tactics(tactics, failed_requirement_ids):
    failed=set(failed_requirement_ids)
    return rank_tactics([
        t for t in tactics
        if failed.intersection(set(t.get("addresses_requirements",[])))
    ])

def load_tactics(path):
    import yaml
    with open(path,encoding="utf-8") as f:
        return yaml.safe_load(f)["tactics"]
