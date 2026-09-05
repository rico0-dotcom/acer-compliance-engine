from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))


def test_ground_truth_documentation_exists():
    readme = BASE / "data" / "ground_truth" / "README.md"
    assert readme.exists()
    text = readme.read_text(encoding="utf-8")
    assert "independently" in text.lower()
    assert "UNCERTAIN" in text
