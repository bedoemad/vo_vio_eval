import json
from pathlib import Path

CONFIG = Path("configs/sequences.json")
KITTI_ROOT = "/mnt/d/Games/data_odometry_color/dataset/sequences"

# Change this to include "10" if needed
KITTI_SEQS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

with open(CONFIG, "r") as f:
    config = json.load(f)

existing = {seq["name"] for seq in config["sequences"]}

for seq in KITTI_SEQS:
    name = f"kitti_{seq}"

    if name in existing:
        print(f"Already exists: {name}")
        continue

    config["sequences"].append({
        "name": name,
        "dataset": "KITTI",
        "path": f"{KITTI_ROOT}/{seq}",
        "groundtruth": f"data/kitti/poses/{seq}_tum.txt",
        "camera_topic_or_folder": "image_0"
    })

    print(f"Added: {name}")

with open(CONFIG, "w") as f:
    json.dump(config, f, indent=2)

print(f"Updated {CONFIG}")
