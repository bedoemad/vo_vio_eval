import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--sequence", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)

# For this dummy test, copy the EuRoC ground truth trajectory.
gt = Path("data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt")

if not gt.exists():
    raise FileNotFoundError(f"Ground truth not found: {gt}")

shutil.copy(gt, out)

print(f"Copied ground truth to dummy prediction: {out}")