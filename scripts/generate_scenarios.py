import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.scenarios import write_scenarios

parser=argparse.ArgumentParser()
parser.add_argument("--n",type=int,default=30)
parser.add_argument("--seed",type=int,default=42)
parser.add_argument("--out",default="data/systems/generated")
args=parser.parse_args()

out=Path(args.out)
if not out.is_absolute():
    out=ROOT/out
scenarios=write_scenarios(out,args.n,args.seed)
print(f"Generated {len(scenarios)} scenarios in {out}")
