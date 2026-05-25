# VO/VIO Deployment-Oriented Evaluation Framework

This project is a deployment-oriented evaluation framework for Visual Odometry (VO) and Visual-Inertial Odometry (VIO) systems.

The framework evaluates VO/VIO methods not only by trajectory accuracy, but also by practical deployment metrics and interpretable failure behavior.

It is designed to answer:

```text
How accurate is the VO/VIO method?
How expensive is it to run?
Under which visual or motion conditions does it fail?
```

---

## 1. Motivation

Traditional VO/VIO evaluation often focuses mainly on trajectory accuracy. However, real deployment on constrained platforms such as e-bikes, smartphones, small robots, and embedded systems also requires understanding:

- runtime cost
- memory usage
- processed FPS
- visual conditions where the method fails
- motion conditions where the method fails
- sequence-specific robustness issues

This framework addresses that gap by jointly evaluating:

```text
accuracy + efficiency + visual diagnostics + motion diagnostics + failure effects
```

---

## 2. Main Features

### Accuracy Metrics

The framework computes:

- Absolute Pose Error (APE)
- Relative Pose Error (RPE)
- APE normalized by trajectory length
- Sim(3)-aligned APE/RPE with scale correction
- SE(3)-aligned APE/RPE without scale correction

APE/RPE are computed using `evo`.

Sim(3) metrics are useful for monocular VO trajectory-shape comparison because monocular scale can be ambiguous.

SE(3) metrics are useful for deployment-oriented metric-scale evaluation because they do not correct scale.

---

### Efficiency Metrics

The framework records:

- total runtime
- peak memory usage
- average memory usage
- number of frames
- runtime per frame
- processed FPS
- runtime per meter

This makes runtime analysis more meaningful because raw runtime depends on sequence length.

---

### Visual-Condition Diagnostics

The framework extracts per-frame visual indicators:

- blur score
- ORB texture score
- FAST texture score
- brightness
- contrast

These are used to analyze whether visual appearance conditions are associated with localization error.

---

### Motion-Condition Diagnostics

The framework computes motion indicators from ground truth:

- frame-to-frame translation
- translation speed
- frame-to-frame rotation
- rotation speed

These are useful for studying motion-induced VO failures, especially for unstable or fast-moving platforms.

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
```

---

## 4. Supported Methods

Current method adapters include:

```text
orbslam3_mono
orbslam3_kitti_mono
dpvo_euroc
dpvo_kitti
example_adapter
```

### ORB-SLAM3

ORB-SLAM3 is integrated through wrapper scripts in `examples/`.

Supported modes:

```text
ORB-SLAM3 monocular on EuRoC
ORB-SLAM3 monocular on KITTI
```

### DPVO

DPVO is integrated through adapters in `adapters/`.

Supported modes:

```text
DPVO on EuRoC
DPVO on KITTI
```

DPVO requires a separate conda environment and a local DPVO installation.

### Example Adapter

The `example_adapter` copies the ground truth as a fake prediction. It is only used to test the adapter interface.

---

## 5. Repository Structure

```text
vo_vio_eval/
├── adapters/
│   ├── example_adapter.py
│   ├── run_dpvo_euroc.py
│   └── run_dpvo_kitti.py
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
│   └── MODEL_ADAPTER_GUIDE.md
│
├── examples/
│   ├── dummy_vo.py
│   ├── noisy_dummy_vo.py
│   ├── run_orbslam3_mono.sh
│   └── run_orbslam3_kitti_mono.sh
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
│   ├── generate_report.py
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
│   └── plot_generic_failure_diagnostics.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

Generated outputs are saved under:

```text
results/
```

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

Typical `requirements.txt`:

```text
numpy
pandas
matplotlib
opencv-python
psutil
evo
scipy
```

Check that `evo` is installed:

```bash
evo_ape --help
evo_rpe --help
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

---

## Testing

The framework includes a lightweight test suite for core configuration loading, config lookup helpers, metric alignment modes, and timestamp-based diagnostic matching.

Install dependencies:

```bash
pip install -r requirements.txt
```
Run all tests:

pytest

Expected output:

11 passed

The tests currently check:

method and sequence configuration loading
method and sequence lookup behavior
Sim(3) and SE(3) metric alignment flags
timestamp tolerance behavior for diagnostic nearest-neighbor matching

Then run:

```bash
pytest
```
---

## 9. Dataset Preparation

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
python src/voeval.py prepare --sequences euroc_mh01 kitti_04
```

Force regeneration:

```bash
python src/voeval.py prepare --sequences kitti_04 --force
```

The preparation script creates ground-truth files such as:

```text
data/kitti/poses/04_tum.txt
data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt
```

---

## 10. Method Configuration

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

## 11. Dataset Sequence Configuration

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
  "name": "kitti_04",
  "dataset": "KITTI",
  "path": "${KITTI_COLOR_ROOT}/sequences/04",
  "groundtruth": "${PROJECT_ROOT}/data/kitti/poses/04_tum.txt",
  "camera_topic_or_folder": "image_2"
}
```

---

## 12. CLI Usage

The user-facing CLI is:

```bash
python src/voeval.py <command>
```

Available commands:

```text
check       check setup, configs, paths, and tools
prepare     prepare dataset ground-truth files
run         run full benchmark automation
summarize   regenerate benchmark summary tables
visual      generate visual-condition files
motion      generate motion-condition files
diagnose    run generic method-agnostic failure diagnostics
plot        regenerate plots
report      generate HTML report
``` 
The diagnostic stage supports configurable timestamp matching tolerance:

```bash
python src/run_generic_failure_diagnostics.py --timestamp-tolerance 0.05
```
---

## 13. Quickstart

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
  --skip-failure \
  --skip-motion
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

## 14. Running a Single Method

Run one method on one sequence:

```bash
python src/main.py --method orbslam3_mono --sequence euroc_mh01 --metrics
```

Run DPVO on one EuRoC sequence:

```bash
python src/main.py --method dpvo_euroc --sequence euroc_mh01 --metrics
```

Run DPVO on one KITTI sequence:

```bash
python src/main.py --method dpvo_kitti --sequence kitti_04 --metrics
```

If a prediction already exists and you only want to recompute metrics:

```bash
python src/main.py --method dpvo_kitti --sequence kitti_04 --skip-run --metrics
```

---

## 15. Full Automation

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
  --sequences kitti_04 kitti_05 \
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

## 16. Benchmark Presets

Presets are defined in:

```text
configs/benchmark_presets.json
```

Example:

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
      "kitti_09"
    ]
  }
}
```

Recommended presets:

```text
euroc_orbslam3
kitti_orbslam3
dpvo_euroc
dpvo_kitti
example_adapter_test
```

---

## 17. Output Structure

Each run produces:

```text
results/<method>/<sequence>/
```

Example:

```text
results/dpvo_kitti/kitti_04/
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

## 18. Final Tables

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

This includes method-generic diagnostics for ORB-SLAM3, DPVO, and future adapters.

---

## 19. Final Figures

Important final figure folders include:

```text
results/final_figures/benchmark_clean/
results/final_figures/visual_conditions/
results/final_figures/failure_effects/
results/final_figures/motion_failure_effects/
results/final_figures/generic_failure_diagnostics_clean/
```

Use the `benchmark_clean` and `generic_failure_diagnostics_clean` folders for presentation-ready figures.

---

## 20. HTML Report

Generate the report:

```bash
python src/voeval.py report
```

or:

```bash
python src/generate_report.py
```

Output:

```text
results/report.html
```

The report includes:

- final table links
- benchmark table preview
- benchmark figures
- visual-condition summary
- diagnostic-effect preview
- generic diagnostic figures

---

## 21. Adding a New VO/VIO Model

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

## 22. Adapter Guide

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
copying the final trajectory to output_path
```

The framework handles the rest.

---

## 23. DPVO Notes

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

## 24. ORB-SLAM3 Notes

ORB-SLAM3 must be installed separately.

The ORB-SLAM3 wrappers are in:

```text
examples/
```

Examples:

```text
examples/run_orbslam3_mono.sh
examples/run_orbslam3_kitti_mono.sh
```

The wrappers run ORB-SLAM3 and convert/copy the final trajectory into the framework output location.

---

## 25. Interpretation Notes

### Sim(3) vs SE(3) Metrics

For monocular VO, scale may be ambiguous. Therefore, the framework reports Sim(3)-aligned metrics with scale correction to compare trajectory shape.

For deployment-oriented evaluation, the framework also reports SE(3)-aligned metrics without scale correction. These better reflect whether the method preserves metric scale in practical use.

In the summary tables, legacy columns such as `ape_rmse_m` and `rpe_rmse_m` correspond to the Sim(3) metrics for backward compatibility. The explicit columns are:

```text
ape_sim3_rmse_m
rpe_sim3_rmse_m
ape_se3_rmse_m
rpe_se3_rmse_m

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
```

### Motion Failure Effects

For motion conditions, high motion is treated as the harder condition:

```text
high-motion error - low-motion error
```

Positive values generally mean the harder condition increased error.

---

## 26. GitHub Notes

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

## 27. Current Contribution

This project contributes a reusable deployment-oriented VO/VIO evaluation framework that supports:

- configurable datasets
- configurable methods
- portable local paths
- external model adapters
- automatic ground-truth preparation
- automatic visual-condition generation
- automatic motion-condition generation
- automated benchmark execution
- APE/RPE evaluation
- runtime and memory profiling
- normalized efficiency metrics
- visual-condition diagnostics
- motion-condition diagnostics
- method-generic failure analysis
- final CSV tables
- final plots
- HTML report generation

In short:

```text
The framework evaluates not only how accurate a VO/VIO method is,
but also how expensive it is and under what conditions it fails.
```

---

## 28. Planned Extensions

Possible future extensions:

- ORB-SLAM3 stereo
- OpenVINS
- MotionHint
- additional datasets
- feature coverage metrics
- optical-flow stability metrics
- dark/bright pixel ratios
- dynamic-object analysis
- artificial degradation experiments
- Docker support
- sample lightweight demo dataset
- interactive dashboard