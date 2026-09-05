# ACER Randomized Adaptation Interaction Stress Benchmark

This benchmark expands the 12-scenario interaction stress test into a deterministic, seeded set of 100 synthetic systems. It preserves the same 8 curated ACER requirements and deterministic assessor, while varying multi-violation combinations and bundled repair opportunities.

The benchmark is intended to test whether the agentic selection policy retains an advantage beyond a small hand-designed set. It is still synthetic evidence and does not establish legal compliance or general superiority on unseen real systems.


## R14 semantic dependency

The current ACER curated rules define EUAI-R14-01 as a required `human_review` component and EUAI-R14-02 as a required `human_review -> final_decision` flow. Because the executable system model cannot contain the required flow without the required component, a scenario that declares R14-01 as failing must also fail R14-02. The generator therefore normalizes such cases before writing the manifest. R14-02 can still fail independently when R14-01 is satisfied but the intervention flow is absent. This keeps the benchmark's declared failure sets consistent with the actual deterministic assessor.
