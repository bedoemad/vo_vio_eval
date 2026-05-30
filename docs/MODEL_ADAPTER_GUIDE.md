# Model Adapter Guide

This guide explains how to add a new VO/VIO method to the VO/VIO Deployment-Oriented Evaluation Framework.

The framework is method-agnostic: it does not need to know the internal implementation of the VO/VIO model. Instead, each external model is connected through an **adapter**.

An adapter is a small script or wrapper that:

1. receives a dataset sequence path from the framework,
2. runs the external VO/VIO method,
3. converts the method output into a standard trajectory format,
4. writes the final trajectory to the output path expected by the framework.

After that, the framework handles:

* runtime and memory profiling
* APE/RPE metric computation
* Sim(3) and SE(3) alignment
* visual-condition diagnostics
* motion-condition diagnostics
* failure analysis
* final tables
* plots
* HTML reports

---

## 1. Adapter Contract

Every adapter must satisfy the following contract.

### Required Input

The adapter should accept at least:

```text
--sequence <path_to_sequence>
--output <path_to_predicted_trajectory>
```

Recommended additional arguments:

```text
--sequence-name <configured_sequence_name>
--groundtruth <path_to_groundtruth>
--result-dir <path_to_result_directory>
```

The framework usually provides these through placeholders in `configs/methods.json`.

---

### Required Output

The adapter must create a trajectory file at:

```text
{output_path}
```

The output trajectory must be in **TUM format**:

```text
timestamp tx ty tz qx qy qz qw
```

Example:

```text
1403636634.258555412 -38.016112588 63.857904258 -10.787924312 0.695577709 -0.128360175 0.640165835 0.299804970
```

Where:

```text
timestamp = timestamp in seconds
tx ty tz  = translation
qx qy qz qw = quaternion orientation
```

The trajectory should use timestamps that can be matched with the ground-truth trajectory.

---

## 2. Why TUM Format?

Different VO/VIO methods produce different output formats.

Examples:

```text
KITTI pose matrices
frame-indexed text files
ROS topics
ORB-SLAM trajectory files
model-specific CSV files
```

The framework converts all method outputs into a common format:

```text
timestamp tx ty tz qx qy qz qw
```

This makes it possible to evaluate different methods with the same metric pipeline.

---

## 3. Method Configuration

Methods are configured in:

```text
configs/methods.json
```

Each method entry tells the framework how to run the adapter.

Example:

```json
{
  "name": "my_model",
  "command_template": "python adapters/run_my_model.py --sequence-name {sequence_name} --sequence {sequence_path} --groundtruth {groundtruth_path} --output {output_path}",
  "output_trajectory": "{output_path}"
}
```

---

## 4. Supported Placeholders

The framework supports these placeholders in `command_template`:

```text
{sequence_name}
{sequence_path}
{groundtruth_path}
{output_path}
{result_dir}
```

Meaning:

| Placeholder          | Meaning                                                      |
| -------------------- | ------------------------------------------------------------ |
| `{sequence_name}`    | Configured sequence name, such as `euroc_mh01` or `kitti_10` |
| `{sequence_path}`    | Path to the dataset sequence                                 |
| `{groundtruth_path}` | Path to the ground-truth trajectory                          |
| `{output_path}`      | Required final predicted trajectory path                     |
| `{result_dir}`       | Result folder for the current method/sequence run            |

---

## 5. Minimal Adapter Example

This is the simplest possible adapter.

```python
import argparse
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--groundtruth", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Example only: copy ground truth as fake prediction.
    shutil.copyfile(args.groundtruth, output_path)

    print(f"Saved predicted trajectory to: {output_path}")


if __name__ == "__main__":
    main()
```

This is useful for testing the framework interface, but it is not a real VO/VIO method.

---

## 6. Adapter Responsibilities

A real adapter usually needs to handle several tasks.

### 1. Validate input paths

The adapter should check that required paths exist:

```python
required_paths = [sequence_path, model_root, executable]

for path in required_paths:
    if not path.exists():
        raise FileNotFoundError(f"Required path not found: {path}")
```

### 2. Run the external method

The adapter can run an external command using `subprocess`.

```python
import subprocess

completed = subprocess.run(command, cwd=str(model_root))

if completed.returncode != 0:
    raise RuntimeError(f"Command failed with return code {completed.returncode}")
```

### 3. Locate the model's raw output

Some methods write output files in their own folders.

Examples:

```text
CameraTrajectory.txt
KeyFrameTrajectory.txt
result.txt
trajectory.csv
estimated_pose.txt
```

The adapter should locate the correct output file.

### 4. Convert to TUM format

If the raw output is not already in TUM format, the adapter must convert it.

Required final format:

```text
timestamp tx ty tz qx qy qz qw
```

### 5. Save to framework output path

The adapter must write the final trajectory to:

```text
{output_path}
```

This is the file that the framework uses for metrics.

---

## 7. Example Method Config

Example for a Python adapter:

```json
{
  "name": "my_model",
  "command_template": "python adapters/run_my_model.py --sequence-name {sequence_name} --sequence {sequence_path} --groundtruth {groundtruth_path} --output {output_path}",
  "output_trajectory": "{output_path}"
}
```

Example for a shell wrapper:

```json
{
  "name": "my_shell_model",
  "command_template": "bash examples/run_my_shell_model.sh {sequence_path} {output_path}",
  "output_trajectory": "{output_path}"
}
```

---

## 8. Local Paths

External model paths should not be hardcoded inside adapters.

Machine-specific paths should be stored in:

```text
configs/local_paths.json
```

This file is not committed to GitHub.

Example:

```json
{
  "ORB_SLAM3_ROOT": "/path/to/ORB_SLAM3",
  "DPVO_ROOT": "/path/to/DPVO",
  "EUROC_ROOT": "/path/to/euroc",
  "EUROC_BAG_ROOT": "/path/to/euroc_bags",
  "KITTI_COLOR_ROOT": "/path/to/data_odometry_color/dataset",
  "KITTI_POSES_ROOT": "/path/to/data_odometry_poses/dataset/poses"
}
```

Adapters can load these paths using:

```python
from config_utils import load_local_paths

local_paths = load_local_paths()
model_root = Path(local_paths["MODEL_ROOT"]).expanduser().resolve()
```

---

## 9. Timestamp Handling

Correct timestamps are critical.

The framework matches predicted trajectories with ground truth using timestamps. If timestamps are wrong, metrics may fail with errors such as:

```text
found no matching timestamps
```

Common timestamp sources:

| Dataset / Method | Timestamp source                              |
| ---------------- | --------------------------------------------- |
| EuRoC images     | image filenames                               |
| EuRoC bag / ROS  | ROS message timestamps                        |
| KITTI            | `times.txt`                                   |
| DPVO             | frame indices converted to dataset timestamps |
| ORB-SLAM3        | method output converted to dataset timestamps |

Adapters should ensure the final trajectory timestamps are compatible with the ground truth.

---

## 10. KITTI Pose Conversion

KITTI ground truth and some predictions may be stored as 3x4 pose matrices.

A KITTI pose row usually has 12 values:

```text
r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz
```

This must be converted to TUM format:

```text
timestamp tx ty tz qx qy qz qw
```

The timestamp usually comes from:

```text
sequences/<sequence_id>/times.txt
```

---

## 11. EuRoC Handling

EuRoC image sequences are usually stored as:

```text
MH_01_easy/mav0/cam0/data
```

EuRoC ground truth is usually stored as:

```text
MH_01_easy/mav0/state_groundtruth_estimate0/data.csv
```

The framework prepares a TUM ground-truth file such as:

```text
data_tum.txt
```

Some VIO methods, such as OpenVINS, use EuRoC bag files instead of image folders.

---

## 12. OpenVINS Adapter Notes

OpenVINS is different from simple file-based methods because it runs through ROS.

The OpenVINS adapter:

1. launches OpenVINS,
2. records `/ov_msckf/poseimu`,
3. plays the EuRoC bag file,
4. converts the recorded poses to TUM format,
5. writes the final output to `predicted_trajectory.txt`,
6. validates the trajectory.

The OpenVINS adapter performs additional validation because ROS/VIO runs may produce output files that are not reliable.

Validation checks include:

```text
minimum number of poses
minimum trajectory duration
unrealistic frame-to-frame jumps
suspicious trajectory length behavior
```

If the trajectory fails validation, the adapter exits with an error so the framework marks the run as failed.

This is intentional: deployment-oriented evaluation should not treat every produced trajectory file as a valid result.

---

## 13. ORB-SLAM3 Adapter Notes

ORB-SLAM3 may write output files such as:

```text
CameraTrajectory.txt
KeyFrameTrajectory.txt
f_dataset-*.txt
kf_dataset-*.txt
```

An ORB-SLAM3 wrapper should:

1. run the correct ORB-SLAM3 executable,
2. pass vocabulary, settings, sequence path, and timestamps,
3. locate the produced trajectory,
4. copy or convert it to `{output_path}`.

For EuRoC monocular-inertial mode, ORB-SLAM3 expects:

```text
Vocabulary/ORBvoc.txt
Examples/Monocular-Inertial/EuRoC.yaml
EuRoC sequence root
EuRoC timestamp file
```

For KITTI monocular mode, ORB-SLAM3 expects KITTI sequence paths and timestamps.

---

## 14. DPVO Adapter Notes

DPVO requires a separate environment and local installation.

The DPVO adapter should:

1. call the DPVO Python executable,
2. run DPVO on the sequence,
3. collect the raw DPVO output,
4. convert frame indices to dataset timestamps,
5. write the final TUM trajectory to `{output_path}`.

For EuRoC, timestamps usually come from image filenames.

For KITTI, timestamps come from:

```text
times.txt
```

---

## 15. Run One Adapter Through the Framework

After adding the method to `configs/methods.json`, run:

```bash
python src/voeval.py run-one \
  --method my_model \
  --sequence euroc_mh01 \
  --metrics
```

Or directly:

```bash
python src/main.py \
  --method my_model \
  --sequence euroc_mh01 \
  --metrics
```

Expected output folder:

```text
results/my_model/euroc_mh01/
```

Expected files:

```text
predicted_trajectory.txt
run_result.json
resource_usage.csv
stdout.log
stderr.log
metrics/
```

---

## 16. Recompute Metrics Without Rerunning the Model

If a prediction already exists, metrics can be recomputed without rerunning the external model:

```bash
python src/voeval.py run-one \
  --method my_model \
  --sequence euroc_mh01 \
  --skip-run \
  --metrics
```

This reuses:

```text
results/my_model/euroc_mh01/run_result.json
results/my_model/euroc_mh01/predicted_trajectory.txt
```

This is useful when metric logic or reporting changes.

---

## 17. Metrics Generated by the Framework

If `--metrics` is used, the framework computes:

```text
APE Sim(3)
RPE Sim(3)
APE SE(3)
RPE SE(3)
```

Conceptually:

```bash
evo_ape tum groundtruth.txt predicted.txt --align --correct_scale
evo_rpe tum groundtruth.txt predicted.txt --align --correct_scale
evo_ape tum groundtruth.txt predicted.txt --align
evo_rpe tum groundtruth.txt predicted.txt --align
```

Meaning:

| Metric type | Alignment                      | Meaning                                          |
| ----------- | ------------------------------ | ------------------------------------------------ |
| Sim(3)      | rotation + translation + scale | trajectory-shape accuracy after scale correction |
| SE(3)       | rotation + translation only    | metric-scale deployment accuracy                 |

---

## 18. Adapter Logging

The framework captures adapter output into:

```text
stdout.log
stderr.log
```

Use these files to debug failures.

Example:

```bash
cat results/my_model/euroc_mh01/stderr.log
tail -100 results/my_model/euroc_mh01/stdout.log
```

Adapters should print useful progress messages such as:

```text
Loading model...
Running sequence...
Converting trajectory...
Saved trajectory to...
```

---

## 19. Common Adapter Errors

### Missing output trajectory

Problem:

```text
predicted_trajectory.txt was not created
```

Fix:

* check that the adapter writes to `--output`
* check the method's raw output location
* check stdout/stderr logs

---

### No matching timestamps

Problem:

```text
found no matching timestamps
```

Fix:

* check timestamp units: seconds vs nanoseconds
* check whether predicted timestamps match the dataset
* check whether the adapter used frame IDs instead of timestamps
* check tolerance in diagnostic matching if the issue is in diagnostics

---

### Empty trajectory

Problem:

```text
trajectory file exists but has no valid poses
```

Fix:

* check model execution
* check raw output file
* check conversion script

---

### Wrong scale

Problem:

```text
Sim(3) error is low but SE(3) error is high
```

Meaning:

```text
the trajectory shape may be good, but metric scale is wrong
```

Fix:

* check whether the model is monocular-only
* check whether scale should be expected
* check timestamp or pose conversion
* check coordinate-frame conversion

---

### Unrealistic trajectory jumps

Problem:

```text
large frame-to-frame position jump
```

Meaning:

```text
the method may have lost tracking or produced a corrupted trajectory
```

Fix:

* inspect logs
* inspect raw trajectory
* check if the external method failed or reset
* consider adapter-specific validation

---

## 20. Adding a New Method: Checklist

Use this checklist when adding a new VO/VIO model.

```text
[ ] Create adapter script in adapters/
[ ] Adapter accepts --sequence and --output
[ ] Adapter optionally accepts --sequence-name, --groundtruth, and --result-dir
[ ] Adapter runs the external model
[ ] Adapter finds the raw model output
[ ] Adapter converts output to TUM format
[ ] Adapter writes final trajectory to {output_path}
[ ] Add method entry to configs/methods.json
[ ] Add example entry to configs/methods.example.json if appropriate
[ ] Add local paths to configs/local_paths.example.json if needed
[ ] Run one small sequence
[ ] Check predicted_trajectory.txt
[ ] Run with --metrics
[ ] Check run_result.json
[ ] Check metrics folder
[ ] Run summarize/plot/report
[ ] Add notes to README if the method has special requirements
```

---

## 21. Minimal Testing Procedure

After adding an adapter, run:

```bash
python src/voeval.py check
```

Then run one sequence:

```bash
python src/voeval.py run-one \
  --method my_model \
  --sequence euroc_mh01 \
  --metrics
```

Then inspect:

```bash
ls results/my_model/euroc_mh01
cat results/my_model/euroc_mh01/run_result.json
```

Then regenerate summaries:

```bash
python src/voeval.py summarize
python src/voeval.py plot
python src/voeval.py report
```

Finally run tests:

```bash
pytest
```

---

## 22. Design Principle

The adapter should contain only model-specific logic.

The framework should handle generic evaluation logic.

Adapter responsibilities:

```text
run external model
find raw output
convert to TUM
copy to output path
perform method-specific validation if needed
```

Framework responsibilities:

```text
load configs
create result directories
monitor runtime and memory
compute APE/RPE
summarize results
generate visual diagnostics
generate motion diagnostics
generate reports
```

This separation keeps the framework reusable and makes it easier to add future VO/VIO methods.

---

## 23. Recommended Adapter Template

```python
import argparse
import shutil
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-name", required=True)
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--groundtruth", required=False)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    sequence_name = args.sequence_name
    sequence_path = Path(args.sequence).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not sequence_path.exists():
        raise FileNotFoundError(f"Sequence path not found: {sequence_path}")

    # 1. Run external model.
    command = [
        "python",
        "external_model_runner.py",
        "--sequence",
        str(sequence_path),
    ]

    print("Running external model:")
    print(" ".join(command))

    completed = subprocess.run(command)

    if completed.returncode != 0:
        raise RuntimeError(f"External model failed with code {completed.returncode}")

    # 2. Locate raw output.
    raw_output = Path("path/to/raw_output.txt")

    if not raw_output.exists():
        raise FileNotFoundError(f"Raw output not found: {raw_output}")

    # 3. Convert/copy to framework output.
    # Replace this with real conversion logic if needed.
    shutil.copyfile(raw_output, output_path)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Adapter did not create a valid output trajectory.")

    print(f"Saved trajectory to: {output_path}")


if __name__ == "__main__":
    main()
```

---

## 24. Summary

To add a new VO/VIO method:

```text
write adapter
configure method
run one sequence
verify TUM trajectory
compute metrics
regenerate summaries and reports
```

The adapter is the bridge between an external VO/VIO model and the framework's deployment-oriented evaluation pipeline.
