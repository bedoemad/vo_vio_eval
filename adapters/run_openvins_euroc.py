import argparse
import csv
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config_utils import load_local_paths


BAG_FILES = {
    "euroc_mh01": "MH_01_easy.bag",
    "euroc_mh02": "MH_02_easy.bag",
    "euroc_mh03": "MH_03_medium.bag",
    "euroc_mh04": "MH_04_difficult.bag",
    "euroc_mh05": "MH_05_difficult.bag",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run OpenVINS on a EuRoC ROS bag.")
    parser.add_argument("--sequence-name", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def terminate_process(process: subprocess.Popen, name: str) -> None:
    if process.poll() is not None:
        return

    print(f"Stopping {name}...")

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        process.wait(timeout=10)
    except Exception:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except Exception:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)


def convert_openvins_csv_to_tum(input_csv: Path, output_tum: Path) -> None:
    df = pd.read_csv(input_csv)

    required = [
        "field.header.stamp",
        "field.pose.pose.position.x",
        "field.pose.pose.position.y",
        "field.pose.pose.position.z",
        "field.pose.pose.orientation.x",
        "field.pose.pose.orientation.y",
        "field.pose.pose.orientation.z",
        "field.pose.pose.orientation.w",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(
            f"OpenVINS CSV is missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    timestamp = df["field.header.stamp"].astype(float)

    # rostopic echo -p gives ROS timestamps in nanoseconds.
    # evo/TUM ground-truth files use seconds.
    timestamp = timestamp.where(timestamp < 1e12, timestamp / 1e9)

    out = pd.DataFrame(
        {
            "t": timestamp,
            "tx": df["field.pose.pose.position.x"],
            "ty": df["field.pose.pose.position.y"],
            "tz": df["field.pose.pose.position.z"],
            "qx": df["field.pose.pose.orientation.x"],
            "qy": df["field.pose.pose.orientation.y"],
            "qz": df["field.pose.pose.orientation.z"],
            "qw": df["field.pose.pose.orientation.w"],
        }
    )

    out = out.dropna()
    out = out.drop_duplicates(subset=["t"])
    out = out.sort_values("t")

    if out.empty:
        raise RuntimeError(f"No valid OpenVINS poses found in {input_csv}")

    output_tum.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(
        output_tum,
        sep=" ",
        header=False,
        index=False,
        float_format="%.9f",
    )

    print(f"Wrote {len(out)} OpenVINS poses to {output_tum}")


def main():
    args = parse_args()

    sequence_name = args.sequence_name
    output_path = Path(args.output).resolve()
    result_dir = output_path.parent
    result_dir.mkdir(parents=True, exist_ok=True)

    if sequence_name not in BAG_FILES:
        raise ValueError(f"Unsupported EuRoC sequence for OpenVINS: {sequence_name}")

    local_paths = load_local_paths()

    openvins_ws = Path(local_paths["OPENVINS_WS"]).expanduser().resolve()
    euroc_bag_root = Path(local_paths["EUROC_BAG_ROOT"]).expanduser().resolve()

    bag_path = euroc_bag_root / BAG_FILES[sequence_name]

    if not openvins_ws.exists():
        raise FileNotFoundError(f"OPENVINS_WS does not exist: {openvins_ws}")

    if not bag_path.exists():
        raise FileNotFoundError(f"EuRoC bag file does not exist: {bag_path}")

    raw_csv = result_dir / "openvins_poseimu.csv"

    if raw_csv.exists():
        raw_csv.unlink()

    launch_cmd = (
        "source /opt/ros/noetic/setup.bash && "
        f"source {openvins_ws}/devel/setup.bash && "
        "roslaunch ov_msckf subscribe.launch config:=euroc_mav"
    )

    record_cmd = (
        "source /opt/ros/noetic/setup.bash && "
        "rostopic echo -p /ov_msckf/poseimu"
    )

    bag_cmd = (
        "source /opt/ros/noetic/setup.bash && "
        f"rosbag play {bag_path}"
    )

    launch_log = open(result_dir / "openvins_launch.log", "w", encoding="utf-8")
    recorder_log = open(raw_csv, "w", encoding="utf-8")
    bag_log = open(result_dir / "rosbag_play.log", "w", encoding="utf-8")

    launch_process = None
    recorder_process = None
    bag_process = None

    try:
        print("Launching OpenVINS...")
        launch_process = subprocess.Popen(
            ["bash", "-lc", launch_cmd],
            stdout=launch_log,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

        time.sleep(8)

        print("Recording /ov_msckf/poseimu...")
        recorder_process = subprocess.Popen(
            ["bash", "-lc", record_cmd],
            stdout=recorder_log,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

        time.sleep(3)

        print(f"Playing bag: {bag_path}")
        bag_process = subprocess.Popen(
            ["bash", "-lc", bag_cmd],
            stdout=bag_log,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

        bag_return_code = bag_process.wait()

        if bag_return_code != 0:
            raise RuntimeError(f"rosbag play failed with return code {bag_return_code}")

        time.sleep(5)

    finally:
        if bag_process is not None:
            terminate_process(bag_process, "rosbag play")

        if recorder_process is not None:
            terminate_process(recorder_process, "OpenVINS pose recorder")

        if launch_process is not None:
            terminate_process(launch_process, "OpenVINS")

        launch_log.close()
        recorder_log.close()
        bag_log.close()

    if not raw_csv.exists() or raw_csv.stat().st_size == 0:
        raise RuntimeError(
            "OpenVINS CSV was not created. "
            "Check openvins_launch.log and rosbag_play.log."
        )

    raw_copy = result_dir / "predicted_trajectory_raw.csv"
    raw_copy.write_bytes(raw_csv.read_bytes())

    convert_openvins_csv_to_tum(raw_csv, output_path)

    print(f"Saved raw OpenVINS CSV to: {raw_copy}")
    print(f"Saved framework trajectory to: {output_path}")


if __name__ == "__main__":
    main()
