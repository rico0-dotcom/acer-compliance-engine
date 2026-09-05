from pathlib import Path
import json, subprocess, sys, tempfile

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts/evaluate_multiseed_statistics.py"
MULTI = BASE / "scripts/run_multiseed_adaptation_evaluation.py"


def test_statistical_evaluation_runs_on_three_seed_dataset():
    # Keep this test independent from other tests that may overwrite the
    # project-level multiseed summary with smaller smoke-test datasets.
    p1 = subprocess.run(
        [sys.executable, str(MULTI),
         "--seeds", "20260904", "20260905", "20260906", "--count", "100"],
        capture_output=True, text=True
    )
    assert p1.returncode == 0, p1.stderr

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        source = BASE / "data/results/adaptation_multiseed/multiseed_summary.json"
        enriched = td / "multiseed_summary_with_llm_fixture.json"
        output = td / "statistical_evaluation.json"
        data = json.loads(source.read_text(encoding="utf-8"))

        # The deterministic regeneration above intentionally contains no LLM
        # metrics. Add small synthetic per-seed LLM metrics here solely to
        # exercise the evaluator's optional LLM-vs-no-LLM branch without
        # rerunning GPT-oss or depending on large external result artifacts.
        llm_fixture = [
            {"accepted_adaptation_steps": 350, "total_cost": 700, "total_complexity": 450,
             "llm_calls": 350, "llm_failures": 0},
            {"accepted_adaptation_steps": 351, "total_cost": 705, "total_complexity": 452,
             "llm_calls": 351, "llm_failures": 0},
            {"accepted_adaptation_steps": 349, "total_cost": 698, "total_complexity": 448,
             "llm_calls": 349, "llm_failures": 0},
        ]
        for row, fixture in zip(data["per_seed"], llm_fixture):
            row["llm_metrics"] = fixture

        enriched.write_text(json.dumps(data, indent=2), encoding="utf-8")
        p2 = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(enriched), "--output", str(output)],
            capture_output=True, text=True
        )
        assert p2.returncode == 0, p2.stderr

        result = json.loads(output.read_text(encoding="utf-8"))
        assert result["total_systems"] == 300
        assert "AGENTIC_vs_FIXED_ORDER" in result
        assert "AGENTIC_NO_LLM_vs_AGENTIC_LLM" in result


def test_no_significance_claim():
    text = (BASE/"scripts/evaluate_multiseed_statistics.py").read_text(encoding="utf-8").lower()
    assert "no statistical significance claim" in text
