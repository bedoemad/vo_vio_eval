import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

inp = Path(args.input)
out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)

with open(inp) as fin, open(out, "w") as fout:
    for line in fin:
        if not line.strip() or line.startswith("#"):
            continue

        parts = line.strip().split()

        if len(parts) != 8:
            print(f"[SKIP] expected 8 columns, got {len(parts)}: {line[:80]}")
            continue

        t = float(parts[0])

        # KITTI timestamps accidentally saved as seconds * 1e9
        if t > 1e6:
            t *= 1e-9

        fout.write(f"{t:.9f} " + " ".join(parts[1:]) + "\n")

print(f"Wrote fixed trajectory to {out}")

