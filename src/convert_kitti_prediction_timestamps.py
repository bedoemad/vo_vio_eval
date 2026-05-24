import argparse
from pathlib import Path

import numpy as np


def rotation_matrix_to_quaternion(R):
    trace = np.trace(R)

    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / s
        qx = (R[2, 1] - R[1, 2]) * s
        qy = (R[0, 2] - R[2, 0]) * s
        qz = (R[1, 0] - R[0, 1]) * s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s

    q = np.array([qx, qy, qz, qw], dtype=float)
    q = q / np.linalg.norm(q)
    return q[0], q[1], q[2], q[3]


def timestamp_from_value(value, frame_index, times):
    """
    Handles:
    - frame ids: 0, 1, 2, ...
    - KITTI seconds: 0.0, 0.1037, ...
    - nanoseconds: very large values
    """
    v = float(value)

    if abs(v - round(v)) < 1e-9 and 0 <= int(round(v)) < len(times):
        return float(times[int(round(v))])

    if v > 1e12:
        return v * 1e-9

    return v


parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--times", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

inp = Path(args.input)
times_path = Path(args.times)
out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)

times = np.loadtxt(times_path)

with open(inp) as fin:
    raw_lines = [
        line.strip()
        for line in fin
        if line.strip() and not line.strip().startswith("#")
    ]

converted = []

for i, line in enumerate(raw_lines):
    parts = line.split()
    vals = [float(x) for x in parts]
    n = len(vals)

    # Case 1: already TUM-like:
    # timestamp tx ty tz qx qy qz qw
    if n == 8:
        t = timestamp_from_value(vals[0], i, times)
        tx, ty, tz = vals[1], vals[2], vals[3]
        qx, qy, qz, qw = vals[4], vals[5], vals[6], vals[7]

    # Case 2: KITTI pose matrix only:
    # r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz
    elif n == 12:
        if i >= len(times):
            continue

        t = float(times[i])
        T = np.array(vals, dtype=float).reshape(3, 4)
        R = T[:, :3]
        trans = T[:, 3]
        tx, ty, tz = trans
        qx, qy, qz, qw = rotation_matrix_to_quaternion(R)

    # Case 3: timestamp/frame_id + KITTI pose matrix
    elif n == 13:
        t = timestamp_from_value(vals[0], i, times)
        T = np.array(vals[1:], dtype=float).reshape(3, 4)
        R = T[:, :3]
        trans = T[:, 3]
        tx, ty, tz = trans
        qx, qy, qz, qw = rotation_matrix_to_quaternion(R)

    else:
        print(f"[SKIP] line {i}: unsupported column count {n}")
        continue

    converted.append((t, tx, ty, tz, qx, qy, qz, qw))

with open(out, "w") as fout:
    for row in converted:
        fout.write(
            f"{row[0]:.9f} "
            f"{row[1]:.9f} {row[2]:.9f} {row[3]:.9f} "
            f"{row[4]:.9f} {row[5]:.9f} {row[6]:.9f} {row[7]:.9f}\n"
        )

print(f"Input lines: {len(raw_lines)}")
print(f"Converted lines: {len(converted)}")
print(f"Wrote converted KITTI prediction to {out}")