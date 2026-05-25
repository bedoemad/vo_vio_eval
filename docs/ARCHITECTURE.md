# Framework Architecture

The VO/VIO Deployment-Oriented Evaluation Framework is organized into four main layers.

## 1. Configuration Layer

The configuration layer defines which methods and datasets are evaluated.

Main files:

- `configs/methods.json`
- `configs/sequences.json`
- `configs/benchmark_presets.json`
- `configs/local_paths.json`

This layer separates machine-specific paths from reusable experiment definitions.

## 2. Execution Layer

The execution layer runs VO/VIO methods through a method-agnostic interface.

Main files:

- `src/main.py`
- `src/method_runner.py`
- `src/run_full_benchmark.py`
- `adapters/`

Each method is called through a command template and must output a TUM-format trajectory.

## 3. Evaluation Layer

The evaluation layer computes accuracy and deployment metrics.

Main files:

- `src/metrics.py`
- `src/resource_monitor.py`
- `src/summarize_results.py`

The framework evaluates:

- APE/RPE with Sim(3) alignment
- APE/RPE with SE(3) alignment
- runtime
- memory usage
- processed FPS
- runtime per frame
- runtime per meter

## 4. Diagnostic and Reporting Layer

The diagnostic layer analyzes when and why VO/VIO methods fail.

Main files:

- `src/analyze_visual_conditions.py`
- `src/analyze_motion_conditions.py`
- `src/run_generic_failure_diagnostics.py`
- `src/create_final_*_table.py`
- `src/plot_*`
- `src/generate_report.py`

This layer links trajectory error with visual and motion conditions such as blur, texture, brightness, speed, and rotation.

## Data Flow

```text
configs
  ↓
method runner / adapters
  ↓
predicted trajectory + resource logs
  ↓
evo metrics + runtime/memory summaries
  ↓
visual and motion condition analysis
  ↓
failure diagnostics
  ↓
final tables, plots, and HTML report
