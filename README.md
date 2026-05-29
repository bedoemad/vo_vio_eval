# VO/VIO Deployment-Oriented Evaluation Framework

![Tests](https://github.com/bedoemad/vo_vio_eval/actions/workflows/tests.yml/badge.svg)

This project is a deployment-oriented evaluation framework for Visual Odometry (VO) and Visual-Inertial Odometry (VIO) systems.

The framework evaluates VO/VIO methods not only by trajectory accuracy, but also by practical deployment metrics, run validity, and interpretable failure behavior.

It is designed to answer:

```text
How accurate is the VO/VIO method?
How expensive is it to run?
Does it produce a valid trajectory?
Under which visual or motion conditions does it fail?
```

---

## 1. Motivation

Traditional VO/VIO evaluation often focuses mainly on trajectory accuracy. However, real deployment on constrained platforms such as e-bikes, smartphones, small robots, and embedded systems also requires understanding:

* runtime cost
* memory usage
* processed FPS
* metric-scale behavior
* whether a produced trajectory is valid
* visual conditions where the method fails
* motion conditions where the method fails
* sequence-specific robustness issues

This framework addresses that gap by jointly evaluating:

```text
accuracy + efficiency + run validity + visual diagnostics + motion diagnostics + failure effects
```

The goal is not only to rank methods by accuracy, but also to understand whether they are practical and reliable under deployment-like conditions.

---

## 2. Main Features

### Accuracy Metrics

The framework computes:

* Absolute Pose Error (APE)
* Relative Pose Error (RPE)
* APE normalized by trajectory length
* Sim(3)-aligned APE/RPE with scale correction
* SE(3)-aligned APE/RPE without scale correction

APE/RPE are computed using `evo`.

Sim(3) metrics are useful for monocular VO trajectory-shape comparison because monocular scale can be ambiguous.

SE(3) metrics are useful for deployment-oriented metric-scale evaluation because they do not correct scale.

---

### Efficiency Metrics

The framework records:

* total runtime
* peak memory usage
* average memory usage
* number of frames
* runtime per frame
* processed FPS
* runtime per meter

This makes runtime analysis more meaningful because raw runtime depends on sequence length.

---

### Run Validity

The framework preserves failed or invalid runs instead of silently ignoring them.

A run can fail because:

```text
the external method crashed
no predicted trajectory was produced
metrics could not be computed
the predicted trajectory failed validation
```

This is important for deployment-oriented evaluation because a method should not be considered successful only because it produced an output file.

For some adapters, such as OpenVINS, the framework performs extra trajectory-quality validation to detect unreliable outputs such as unrealistic trajectory jumps.

---

### Visual-Condition Diagnostics

The framework extracts per-frame visual indicators:

* blur score
* ORB texture score
* FAST texture score
* brightness
* contrast

These are used to analyze whether visual appearance conditions are associated with localization error.

---

### Motion-Condition Diagnostics

The framework computes motion indicators from ground truth:

* frame-to-frame translation
* translation speed
* frame-to-frame rotation
* rotation speed

These are useful for studying motion-induced VO/VIO failures, especially for unstable, fast-moving, or difficult trajectories.

---

### Failure Analysis

The framework merges trajectory error with visual and motion conditions, then performs binned failure-effect analysis.

Examples:

```text
low texture vs high texture
low blur score vs high blur score
low brightness vs high brightness
low speed vs high speed
low rotation vs high rotation
```

The final diagnostic tables show which conditions are most associated with increased VO/VIO error.

---

## 3. Supported Datasets

The framework currently supports:

### EuRoC MAV

Configured sequence names:

```text
euroc_mh01
euroc_mh02
euroc_mh03
euroc_mh04
euroc_mh05
```

Typical raw sequence names:

```text
MH_01_easy
MH_02_easy
MH_03_medium
MH_04_difficult
MH_05_difficult
```

EuRoC is used for both VO and VIO evaluation because it provides synchronized camera, IMU, and ground-truth trajectory data.

---

### KITTI Odometry

Configured sequence names:

```text
kitti_00
kitti_01
kitti_02
kitti_03
kitti_04
kitti_05
kitti_06
kitti_07
kitti_08
kitti_09
kitti_10
```

KITTI sequence `10` is included because it has ground-truth poses in the KITTI odometry benchmark.

KITTI is mainly used for outdoor driving-style VO evaluation and long-trajectory deployment analysis.

---

## 4. Supported Methods

Current method adapters include:

```text
orbslam3_mono
orbslam3_euroc_mono_inertial
orbslam3_kitti_mono
dpvo_euroc
dpvo_kitti
openvins_euroc
example_adapter
```

### ORB-SLAM3

ORB-SLAM3 is integrated through wrapper scripts in `examples/` and adapters.

Supported modes:

```text
ORB-SLAM3 monocular on EuRoC
ORB-SLAM3 monocular-inertial on EuRoC
ORB-SLAM3 monocular on KITTI
```

The monocular-inertial EuRoC mode allows comparison with other VIO methods such as OpenVINS.

### DPVO

DPVO is integrated through adapters in `adapters/`.

Supported modes:

```text
DPVO on EuRoC
DPVO on KITTI
```

DPVO requires a separate conda environment and a local DPVO installation.

DPVO outputs frame-indexed trajectories, so the framework adapter converts frame IDs to dataset timestamps before evaluation.

### OpenVINS

OpenVINS is integrated as a VIO method on EuRoC using ROS Noetic and EuRoC bag files.

Supported mode:

```text
OpenVINS monocular-inertial on EuRoC
```

The OpenVINS adapter records the `/ov_msckf/poseimu` topic and converts it to TUM trajectory format.

The adapter also performs trajectory-quality validation. This means unreliable outputs, such as trajectories with unrealistic jumps, are marked as failed instead of being treated as valid benchmark results.

### Example Adapter

The `example_adapter` copies the ground truth as a fake prediction. It is only used to test the adapter interface.

---

## 5. Repository Structure

```text
vo_vio_eval/
├── adapters/
│   ├── example_adapter.py
│   ├── run_dpvo_euroc.py
│   ├── run_dpvo_kitti.py
│   └── run_openvins_euroc.py
│
├── configs/
│   ├── benchmark_presets.json
│   ├── local_paths.example.json
│   ├── methods.example.json
│   ├── sequences.example.json
│   ├── methods.json
│   ├── sequences.json
│   └── local_paths.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── MODEL_ADAPTER_GUIDE.md
│
├── examples/
│   ├── dummy_vo.py
│   ├── noisy_dummy_vo.py
│   ├── run_orbslam3_mono.sh
│   ├── run_orbslam3_kitti_mono.sh
│   └── run_orbslam3_euroc_mono_inertial.sh
│
├── src/
│   ├── main.py
│   ├── voeval.py
│   ├── run_full_benchmark.py
│   ├── check_setup.py
│   ├── prepare_datasets.py
│   ├── ensure_visual_conditions.py
│   ├── analyze_motion_conditions.py
│   ├── run_generic_failure_diagnostics.py
│   ├── add_motion_to_error_correlation.py
│   ├── binned_motion_failure_analysis.py
│   ├── generate_report.py
│   ├── generate_filtered_report.py
│   ├── summarize_results.py
│   ├── create_final_benchmark_table.py
│   ├── create_final_visual_condition_table.py
│   ├── create_final_failure_effect_table.py
│   ├── create_motion_failure_effect_table.py
│   ├── create_final_diagnostic_effect_table.py
│   ├── plot_final_benchmark_figures.py
│   ├── plot_final_visual_condition_figures.py
│   ├── plot_final_failure_effect_figures.py
│   ├── plot_motion_failure_effects.py
│   ├── plot_final_diagnostic_effects.py
│   └── plot_generic_failure_diagnostics.py
│
├── tests/
├── requirements.txt
├── README.md
└── .gitignore
```

Generated outputs are saved under:

```text
results/
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the framework architecture.

---

## 6. Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Typical `requirements.txt` dependencies include:

```text
numpy
pandas
matplotlib
opencv-python-headless
psutil
evo
scipy
pytest
```

Check that `evo` is installed:

```bash
evo_ape --help
evo_rpe --help
```

Some method adapters require additional external installations:

```text
ORB-SLAM3
DPVO
ROS Noetic
OpenVINS
```

---

## 7. Local Path Configuration

Dataset and model paths vary from one machine to another. Therefore, this framework uses a local path file:

```text
configs/local_paths.json
```

This file should not be committed to GitHub.

First copy the example:

```bash
cp configs/local_paths.example.json configs/local_paths.json
```

Then edit:

```bash
nano configs/local_paths.json
```

Example:

```json
{
  "EUROC_ROOT": "/path/to/euroc",
  "EUROC_BAG_ROOT": "/path/to/euroc_bags",
  "KITTI_COLOR_ROOT": "/path/to/data_odometry_color/dataset",
  "KITTI_POSES_ROOT": "/path/to/data_odometry_poses/dataset/poses",
  "ORB_SLAM3_ROOT": "/path/to/ORB_SLAM3",
  "DPVO_ROOT": "/path/to/DPVO"
}
```

The framework supports placeholders such as:

```text
${PROJECT_ROOT}
${EUROC_ROOT}
${EUROC_BAG_ROOT}
${KITTI_COLOR_ROOT}
${KITTI_POSES_ROOT}
${ORB_SLAM3_ROOT}
${DPVO_ROOT}
```

Example sequence path:

```json
{
  "name": "kitti_04",
  "dataset": "KITTI",
  "path": "${KITTI_COLOR_ROOT}/sequences/04",
  "groundtruth": "${PROJECT_ROOT}/data/kitti/poses/04_tum.txt",
  "camera_topic_or_folder": "image_2"
}
```

---

## 8. Setup Check

Before running experiments, check that paths, tools, configs, and datasets are valid:

```bash
python src/voeval.py check
```

or directly:

```bash
python src/check_setup.py
```

The setup checker reports:

```text
[OK] valid config files
[OK] dataset paths found
[OK] ground-truth files found
[OK] evo tools found
[MISSING] missing paths or files
[WARN] optional paths not configured
```

---

## 9. Testing

The framework includes a lightweight test suite for core framework behavior, including:

```text
configuration loading
method and sequence lookup
metric alignment modes
timestamp-based diagnostic matching
skip-run result reuse
report and utility behavior
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
pytest
```

Expected output should show all tests passing.

---

## 10. Dataset Preparation

The framework can automatically prepare TUM-format ground-truth files.

Run:

```bash
python src/voeval.py prepare --all
```

or directly:

```bash
python src/prepare_datasets.py --dataset all
```

Prepare only EuRoC:

```bash
python src/voeval.py prepare --dataset euroc
```

Prepare only KITTI:

```bash
python src/voeval.py prepare --dataset kitti
```

Prepare specific sequences:

```bash
python src/voeval.py prepare --sequences euroc_mh01 kitti_04 kitti_10
```

Force regeneration:

```bash
python src/voeval.py prepare --sequences kitti_10 --force
```

The preparation script creates ground-truth files such as:

```text
data/kitti/poses/10_tum.txt
data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt
```

---

## 11. Method Configuration

Methods are defined in:

```text
configs/methods.json
```

Example:

```json
{
  "name": "dpvo_kitti",
  "command_template": "python adapters/run_dpvo_kitti.py --sequence {sequence_path} --output {output_path}",
  "output_trajectory": "{output_path}"
}
```

Supported placeholders:

```text
{sequence_name}
{sequence_path}
{groundtruth_path}
{output_path}
{result_dir}
```

The method adapter must create a trajectory at:

```text
{output_path}
```

in TUM format:

```text
timestamp tx ty tz qx qy qz qw
```

---

## 12. Dataset Sequence Configuration

Sequences are defined in:

```text
configs/sequences.json
```

Example EuRoC entry:

```json
{
  "name": "euroc_mh01",
  "dataset": "EuRoC",
  "path": "${EUROC_ROOT}/MH_01_easy/mav0/cam0/data",
  "groundtruth": "${EUROC_ROOT}/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt",
  "camera_topic_or_folder": "cam0"
}
```

Example KITTI entry:

```json
{
  "name": "kitti_10",
  "dataset": "KITTI",
  "path": "${KITTI_COLOR_ROOT}/sequences/10",
  "groundtruth": "${PROJECT_ROOT}/data/kitti/poses/10_tum.txt",
  "camera_topic_or_folder": "image_2"
}
```

---

## 13. CLI Usage

The user-facing CLI is:

```bash
python src/voeval.py <command>
```

Available commands:

```text
check              check setup, configs, paths, and tools
prepare            prepare dataset ground-truth files
run                run benchmark automation
run-one            run one method on one sequence
summarize          regenerate benchmark summary tables
visual             generate visual-condition files
motion             generate motion-condition files
diagnose           run generic method-agnostic failure diagnostics
plot               regenerate plots
report             generate the general HTML report
report-filtered    generate a focused filtered HTML report
```

The diagnostic stage supports configurable timestamp matching tolerance:

```bash
python src/run_generic_failure_diagnostics.py --timestamp-tolerance 0.05
```

---

## 14. Quickstart

### 1. Configure local paths

```bash
cp configs/local_paths.example.json configs/local_paths.json
nano configs/local_paths.json
```

### 2. Check setup

```bash
python src/voeval.py check
```

### 3. Prepare datasets

```bash
python src/voeval.py prepare --all
```

### 4. Run a small test with the example adapter

```bash
python src/voeval.py run \
  --methods example_adapter \
  --sequences euroc_mh01 \
  --skip-existing \
  --allow-fail
```

### 5. Generate report

```bash
python src/voeval.py report
```

Open:

```text
results/report.html
```

---

## 15. Running a Single Method

Run one method on one sequence:

```bash
python src/main.py --method orbslam3_mono --sequence euroc_mh01 --metrics
```

Run ORB-SLAM3 monocular-inertial on one EuRoC sequence:

```bash
python src/main.py --method orbslam3_euroc_mono_inertial --sequence euroc_mh01 --metrics
```

Run DPVO on one EuRoC sequence:

```bash
python src/main.py --method dpvo_euroc --sequence euroc_mh01 --metrics
```

Run DPVO on one KITTI sequence:

```bash
python src/main.py --method dpvo_kitti --sequence kitti_10 --metrics
```

Run OpenVINS on one EuRoC sequence:

```bash
python src/main.py --method openvins_euroc --sequence euroc_mh01 --metrics
```

If a prediction already exists and you only want to recompute metrics:

```bash
python src/main.py --method dpvo_kitti --sequence kitti_10 --skip-run --metrics
```

The same single-method workflow can also be run through the main CLI:

```bash
python src/voeval.py run-one \
  --method orbslam3_euroc_mono_inertial \
  --sequence euroc_mh01 \
  --metrics
```

To recompute metrics for an existing prediction without rerunning the model:

```bash
python src/voeval.py run-one \
  --method orbslam3_euroc_mono_inertial \
  --sequence euroc_mh01 \
  --skip-run \
  --metrics
```

When using `--skip-run --metrics`, the framework reuses the existing `run_result.json` and recomputes metrics without overwriting the original runtime and memory measurements.

---

## 16. Full Automation

The full automation script is:

```text
src/run_full_benchmark.py
```

It performs:

```text
prepare ground truth
run methods
compute APE/RPE
summarize results
generate visual-condition CSVs
generate motion-condition CSVs
create final tables
run diagnostics
generate plots
generate HTML report
```

Run using a preset:

```bash
python src/voeval.py run --preset kitti_orbslam3 --skip-existing
```

Run using explicit methods and sequences:

```bash
python src/voeval.py run \
  --methods dpvo_kitti \
  --sequences kitti_04 kitti_05 kitti_10 \
  --allow-fail
```

Skip model execution and regenerate outputs only:

```bash
python src/voeval.py run \
  --preset dpvo_kitti \
  --no-run
```

Skip existing predictions:

```bash
python src/voeval.py run \
  --preset dpvo_kitti \
  --skip-existing \
  --allow-fail
```

---

## 17. Benchmark Presets

Presets are defined in:

```text
configs/benchmark_presets.json
```

Example KITTI preset:

```json
{
  "kitti_orbslam3": {
    "methods": ["orbslam3_kitti_mono"],
    "sequences": [
      "kitti_00",
      "kitti_01",
      "kitti_02",
      "kitti_03",
      "kitti_04",
      "kitti_05",
      "kitti_06",
      "kitti_07",
      "kitti_08",
      "kitti_09",
      "kitti_10"
    ]
  }
}
```

Recommended presets:

```text
euroc_orbslam3
euroc_openvins
kitti_orbslam3
dpvo_euroc
dpvo_kitti
example_adapter_test
```

The preset system makes it possible to run repeatable experiments without manually listing methods and sequences every time.

---

## 18. Output Structure

Each run produces:

```text
results/<method>/<sequence>/
```

Example:

```text
results/dpvo_kitti/kitti_10/
├── predicted_trajectory.txt
├── predicted_trajectory_raw.txt
├── run_result.json
├── resource_usage.csv
├── stdout.log
├── stderr.log
└── metrics/
    ├── ape_sim3_results.zip
    ├── rpe_sim3_results.zip
    ├── ape_se3_results.zip
    └── rpe_se3_results.zip
```

The main combined summary is:

```text
results/comparison_summary.csv
```

Final tables are saved in:

```text
results/final_tables/
```

Final figures are saved in:

```text
results/final_figures/
```

The HTML report is:

```text
results/report.html
```

---

## 19. Final Tables

Important final tables include:

```text
results/final_tables/benchmark_summary_final.csv
results/final_tables/visual_conditions_summary_final.csv
results/final_tables/failure_effect_summary_final.csv
results/final_tables/motion_failure_effect_summary.csv
results/final_tables/diagnostic_effect_summary_final.csv
results/final_tables/all_methods_condition_effect_summary.csv
```

The most general diagnostic table is:

```text
results/final_tables/all_methods_condition_effect_summary.csv
```

This includes method-generic diagnostics for ORB-SLAM3, DPVO, OpenVINS, and future adapters.

---

## 20. Final Figures

Important final figure folders include:

```text
results/final_figures/benchmark_clean/
results/final_figures/visual_conditions/
results/final_figures/failure_effects/
results/final_figures/motion_failure_effects/
results/final_figures/diagnostic_effects/
results/final_figures/generic_failure_diagnostics_clean/
```

Use the `benchmark_clean` and `generic_failure_diagnostics_clean` folders for presentation-ready figures.

---

## 21. HTML Report

Generate the general report:

```bash
python src/voeval.py report
```

or directly:

```bash
python src/generate_report.py
```

Output:

```text
results/report.html
```

The HTML report is generated as a compact deployment-oriented dashboard. It includes:

* overview cards
* dataset coverage and run-validity summary
* failed or invalid run table
* method ranking
* best method per sequence
* searchable sequence-level results
* benchmark figures across available datasets
* visual-condition summaries
* visual failure-effect figures
* motion failure-effect figures
* diagnostic-effect figures
* generic diagnostic summaries
* links to final CSV tables

Heavy diagnostic sections are collapsible so the report remains readable while still preserving detailed evidence for analysis and thesis discussion.

### Filtered Reports

The framework can generate focused dashboard reports for a subset of datasets, methods, or sequences without moving or deleting result folders.

Generate a EuRoC-only report for one VIO method:

```bash
python src/generate_filtered_report.py \
  --dataset EuRoC \
  --methods orbslam3_euroc_mono_inertial \
  --name euroc_vio
```

Open:

```text
results/reports/euroc_vio/report.html
```

Generate a EuRoC comparison report:

```bash
python src/generate_filtered_report.py \
  --dataset EuRoC \
  --methods orbslam3_euroc_mono_inertial orbslam3_mono dpvo_euroc openvins_euroc \
  --name euroc_comparison
```

Open:

```text
results/reports/euroc_comparison/report.html
```

The same filtered report can also be generated through the CLI if configured:

```bash
python src/voeval.py report-filtered \
  --dataset EuRoC \
  --methods orbslam3_euroc_mono_inertial orbslam3_mono dpvo_euroc openvins_euroc \
  --name euroc_comparison
```

Filtered reports also save filtered CSV files:

```text
results/reports/<name>/benchmark_filtered.csv
results/reports/<name>/visual_conditions_filtered.csv
```

---

## 22. Adding a New VO/VIO Model

The framework is method-agnostic.

A new model can be evaluated by writing an adapter.

The adapter must:

1. accept a sequence path
2. accept an output trajectory path
3. run the model
4. save the predicted trajectory in TUM format

Required output format:

```text
timestamp tx ty tz qx qy qz qw
```

Example adapter command:

```bash
python adapters/run_my_model.py \
  --sequence /path/to/sequence \
  --output results/my_model/euroc_mh01/predicted_trajectory.txt
```

Example method config:

```json
{
  "name": "my_model",
  "command_template": "python adapters/run_my_model.py --sequence {sequence_path} --groundtruth {groundtruth_path} --output {output_path}",
  "output_trajectory": "{output_path}"
}
```

Then run:

```bash
python src/main.py --method my_model --sequence euroc_mh01 --metrics
```

or:

```bash
python src/voeval.py run \
  --methods my_model \
  --sequences euroc_mh01
```

---

## 23. Adapter Guide

See:

```text
docs/MODEL_ADAPTER_GUIDE.md
```

The adapter isolates model-specific logic from the framework.

Examples of model-specific logic:

```text
running the external model
activating the correct environment
finding the model's raw output file
converting KITTI pose matrices to TUM
converting frame IDs to timestamps
recording ROS topics
copying the final trajectory to output_path
validating model-specific trajectory output
```

The framework handles the rest.

---

## 24. DPVO Notes

DPVO requires a separate conda environment.

The framework adapter calls the DPVO Python executable directly, for example:

```text
~/miniconda3/envs/dpvo/bin/python
```

DPVO outputs frame-indexed trajectories, so the adapter converts frame indices to dataset timestamps before evaluation.

For EuRoC, timestamps come from image filenames.

For KITTI, timestamps come from:

```text
times.txt
```

---

## 25. ORB-SLAM3 Notes

ORB-SLAM3 must be installed separately.

The ORB-SLAM3 wrappers are in:

```text
examples/
```

Examples:

```text
examples/run_orbslam3_mono.sh
examples/run_orbslam3_kitti_mono.sh
examples/run_orbslam3_euroc_mono_inertial.sh
```

The wrappers run ORB-SLAM3 and convert or copy the final trajectory into the framework output location.

---

## 26. OpenVINS Notes

OpenVINS must be installed separately in a ROS Noetic catkin workspace.

The framework adapter runs OpenVINS on EuRoC bag files and records the following topic:

```text
/ov_msckf/poseimu
```

This topic is used because it provides the pose estimate suitable for trajectory evaluation.

The OpenVINS adapter converts the recorded trajectory to TUM format:

```text
timestamp tx ty tz qx qy qz qw
```

The adapter also performs trajectory-quality validation. Validation checks include:

```text
minimum number of poses
minimum trajectory duration
unrealistic frame-to-frame jumps
suspicious trajectory length behavior
```

If a trajectory fails validation, the run is marked as failed or unreliable. This is intentional: deployment-oriented evaluation should detect invalid outputs instead of reporting misleading APE/RPE values.

This behavior is especially useful for difficult VIO sequences where a model may produce a trajectory file even though the trajectory is not valid for evaluation.

---

## 27. Interpretation Notes

### Sim(3) vs SE(3) Metrics

For monocular VO, scale may be ambiguous. Therefore, the framework reports Sim(3)-aligned metrics with scale correction to compare trajectory shape.

For deployment-oriented evaluation, the framework also reports SE(3)-aligned metrics without scale correction. These better reflect whether the method preserves metric scale in practical use.

In the summary tables, legacy columns such as `ape_rmse_m` and `rpe_rmse_m` correspond to the Sim(3) metrics for backward compatibility.

The explicit metric columns are:

```text
ape_sim3_rmse_m
rpe_sim3_rmse_m
ape_se3_rmse_m
rpe_se3_rmse_m
```

### Raw Runtime

Raw runtime depends on sequence length and number of frames.

Therefore, the framework also reports:

```text
runtime_per_frame_sec
processed_fps
runtime_per_meter_sec
```

### Raw APE Across Datasets

Raw APE is not always directly comparable between EuRoC and KITTI because KITTI trajectories are much longer.

Therefore, the framework also reports:

```text
ape_rmse_percent_of_path
```

### Visual Failure Effects

For appearance conditions, the framework compares difficult/easy bins such as:

```text
low texture error - high texture error
low blur score error - high blur score error
low brightness error - high brightness error
```

These comparisons help identify visual conditions that are associated with increased trajectory error.

### Motion Failure Effects

For motion conditions, high motion is treated as the harder condition:

```text
high-motion error - low-motion error
```

Positive values generally mean the harder condition increased error.

### Failed or Invalid Runs

Failed or invalid runs are preserved in the results because deployment-oriented evaluation should expose robustness problems.

A run can fail because:

```text
the external method crashed
no predicted trajectory was produced
metrics could not be computed
the predicted trajectory failed validation
```

This is useful because a method should not be considered successful only because it produced an output file.

---

## 28. GitHub Notes

Do not commit datasets, model weights, local machine paths, or generated results.

Recommended `.gitignore` entries:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
*.egg-info/

# Local paths
configs/local_paths.json

# Datasets
data/euroc/
data/kitti/
datasets/
*.bag

# Results
results/
*.zip

# Model weights
*.pth
*.pt
*.ckpt
*.onnx

# Logs
*.log
stdout.log
stderr.log

# Editors
.vscode/
.idea/
.DS_Store
```

Upload example configs instead:

```text
configs/local_paths.example.json
configs/sequences.example.json
configs/methods.example.json
```

---

## 29. Current Contribution

This project contributes a reusable deployment-oriented VO/VIO evaluation framework that supports:

* configurable datasets
* configurable methods
* portable local paths
* external model adapters
* automatic ground-truth preparation
* automatic visual-condition generation
* automatic motion-condition generation
* automated benchmark execution
* APE/RPE evaluation
* Sim(3) and SE(3) metric reporting
* runtime and memory profiling
* normalized efficiency metrics
* visual-condition diagnostics
* motion-condition diagnostics
* method-generic failure analysis
* failed and invalid trajectory detection
* validated VIO evaluation with OpenVINS on EuRoC
* ORB-SLAM3 monocular-inertial evaluation on EuRoC
* KITTI odometry support through sequence 10
* final CSV tables
* final plots
* compact collapsible HTML report generation
* filtered HTML reports for focused comparisons

In short:

```text
The framework evaluates not only how accurate a VO/VIO method is,
but also how expensive it is and under what conditions it fails.
```

---

## 30. Planned Extensions

Possible future extensions:

* ORB-SLAM3 stereo
* stereo or RGB-D VIO methods
* MotionHint
* additional datasets
* feature coverage metrics
* optical-flow stability metrics
* dark/bright pixel ratios
* dynamic-object analysis
* artificial degradation experiments
* Docker support
* sample lightweight demo dataset
* interactive dashboard
