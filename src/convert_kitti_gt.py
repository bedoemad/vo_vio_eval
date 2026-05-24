import argparse
from pathlib import Path
import numpy as np


def rotation_matrix_to_quaternion(R):
    """
    Converts 3x3 rotation matrix to quaternion qx qy qz qw.
    """
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

    return qx, qy, qz, qw


parser = argparse.ArgumentParser()
parser.add_argument("--poses", required=True)
parser.add_argument("--times", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

poses_path = Path(args.poses)
times_path = Path(args.times)
out_path = Path(args.output)
out_path.parent.mkdir(parents=True, exist_ok=True)

poses = np.loadtxt(poses_path)
times = np.loadtxt(times_path)

with open(out_path, "w") as f:
    for i, pose_row in enumerate(poses):
        T = pose_row.reshape(3, 4)

        R = T[:, :3]
        t = T[:, 3]

        qx, qy, qz, qw = rotation_matrix_to_quaternion(R)

        timestamp = times[i]

        f.write(
            f"{timestamp:.9f} "
            f"{t[0]:.9f} {t[1]:.9f} {t[2]:.9f} "
            f"{qx:.9f} {qy:.9f} {qz:.9f} {qw:.9f}\n"
        )

print(f"Wrote KITTI ground truth TUM file to {out_path}")
