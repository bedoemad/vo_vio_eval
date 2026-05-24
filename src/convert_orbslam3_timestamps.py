import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

inp = Path(args.input)
out = Path(args.output)

with open(inp) as fin, open(out, "w") as fout:
    for line in fin:
        if not line.strip() or line.startswith("#"):
            continue

        parts = line.strip().split()
        t = float(parts[0])

        if t > 1e12:
            t *= 1e-9

        fout.write(f"{t:.9f} " + " ".join(parts[1:]) + "\n")

print(f"Wrote {out}")
