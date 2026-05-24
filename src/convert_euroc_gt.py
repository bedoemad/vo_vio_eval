import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

inp = Path(args.input)
out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(inp)
df.columns = [c.strip().lstrip("#").strip() for c in df.columns]

print("Detected columns:")
print(df.columns.tolist())

timestamp_col = df.columns[0]

with open(out, "w") as f:
    for _, row in df.iterrows():
        t = float(row[timestamp_col]) * 1e-9

        tx = row["p_RS_R_x [m]"]
        ty = row["p_RS_R_y [m]"]
        tz = row["p_RS_R_z [m]"]

        qw = row["q_RS_w []"]
        qx = row["q_RS_x []"]
        qy = row["q_RS_y []"]
        qz = row["q_RS_z []"]

        f.write(f"{t:.9f} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n")

print(f"Wrote {out}")