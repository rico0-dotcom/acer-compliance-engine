from .engine import assess
from .adaptation import apply_tactic, applicable_tactics

class ComplianceOrchestrator:
    def __init__(self, requirements, tactics, max_steps=10):
        self.requirements=requirements
        self.tactics=tactics
        self.max_steps=max_steps

    def run(self, system):
        current=system
        history=[]
        seen_states=set()

        for step in range(self.max_steps):
            before=assess(current,self.requirements)
            if before.overall_status=="COMPLIANT":
                break

            state=tuple((r.requirement_id,r.status) for r in before.results)
            if state in seen_states:
                history.append({"step":step+1,"accepted":False,
                                 "reason":"Repeated compliance state; stopped to avoid a cycle."})
                break
            seen_states.add(state)

            failed_ids=[r.requirement_id for r in before.results if r.status=="FAIL"]
            candidates=applicable_tactics(self.tactics,failed_ids)

            if not candidates:
                history.append({"step":step+1,"accepted":False,
                                 "failed_requirements":failed_ids,
                                 "reason":"No applicable adaptation tactic."})
                break

            accepted=False
            before_failures=len(failed_ids)

            for tactic in candidates:
                candidate=apply_tactic(current,tactic)
                after=assess(candidate,self.requirements)
                after_failures=sum(r.status=="FAIL" for r in after.results)

                if after_failures < before_failures:
                    history.append({
                        "step":step+1,
                        "accepted":True,
                        "tactic_id":tactic["id"],
                        "addressed_requirements":[
                            rid for rid in failed_ids
                            if rid in tactic.get("addresses_requirements",[])
                        ],
                        "violations_before":before_failures,
                        "violations_after":after_failures,
                        "status_before":before.overall_status,
                        "status_after":after.overall_status
                    })
                    current=candidate
                    accepted=True
                    break

            if not accepted:
                history.append({"step":step+1,"accepted":False,
                                 "failed_requirements":failed_ids,
                                 "reason":"No candidate produced a strict compliance improvement."})
                break

        return current,history
