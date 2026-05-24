from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--sequence", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

gt = Path("data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt")
out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)

with open(gt) as fin, open(out, "w") as fout:
    for i, line in enumerate(fin):
        parts = line.strip().split()
        t, tx, ty, tz, qx, qy, qz, qw = parts

        drift = i * 0.00001
        tx = float(tx) + drift

        fout.write(f"{t} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n")

print(f"Wrote noisy dummy prediction to {out}")
