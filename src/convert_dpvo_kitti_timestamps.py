import argparse
from pathlib import Path
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--times", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--stride", type=int, default=2)
args = parser.parse_args()

input_path = Path(args.input)
times_path = Path(args.times)
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

times = np.loadtxt(times_path)

with open(input_path) as fin:
    lines = [
        line.strip()
        for line in fin
        if line.strip() and not line.strip().startswith("#")
    ]

converted = []

for line in lines:
    parts = line.split()

    if len(parts) != 8:
        print(f"[SKIP] Expected 8 columns, got {len(parts)}: {line[:80]}")
        continue

    frame_id = int(round(float(parts[0])))
    image_index = frame_id * args.stride

    if image_index >= len(times):
        print(f"[SKIP] frame_id={frame_id}, image_index={image_index} out of range")
        continue

    timestamp_sec = float(times[image_index])
    converted.append(f"{timestamp_sec:.9f} " + " ".join(parts[1:]))

with open(output_path, "w") as fout:
    for row in converted:
        fout.write(row + "\n")

print(f"Input lines: {len(lines)}")
print(f"Converted lines: {len(converted)}")
print(f"Wrote: {output_path}")
