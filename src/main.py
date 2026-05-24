from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict, is_dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from config_utils import load_json, resolve_sequence_paths
from method_runner import MethodRunner
from metrics import run_evo_ape, run_evo_rpe


@dataclass
class MethodConfig:
    name: str
    command_template: str
    output_trajectory: str


@dataclass
class SequenceConfig:
    name: str
    dataset: str
    path: str
    groundtruth: str
    camera_topic_or_folder: Optional[str] = None
    imu_path: Optional[str] = None


@dataclass
class RunResult:
    method: str
    sequence: str
    success: bool
    runtime_sec: float
    peak_memory_mb: float
    avg_memory_mb: float
    result_dir: str
    predicted_trajectory: Optional[str]
    error_message: Optional[str] = None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def object_to_dict(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError(f"Cannot convert object to dict: {type(obj)}")


def dict_to_run_result(data: Dict[str, Any]) -> RunResult:
    return RunResult(
        method=data["method"],
        sequence=data["sequence"],
        success=bool(data["success"]),
        runtime_sec=float(data.get("runtime_sec", 0.0)),
        peak_memory_mb=float(data.get("peak_memory_mb", 0.0)),
        avg_memory_mb=float(data.get("avg_memory_mb", 0.0)),
        result_dir=str(data["result_dir"]),
        predicted_trajectory=data.get("predicted_trajectory"),
        error_message=data.get("error_message"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run VO/VIO deployment-oriented evaluation."
    )

    parser.add_argument(
        "--methods",
        type=str,
        default="configs/methods.json",
        help="Path to methods config JSON.",
    )

    parser.add_argument(
        "--sequences",
        type=str,
        default="configs/sequences.json",
        help="Path to sequences config JSON.",
    )

    parser.add_argument(
        "--results",
        type=str,
        default="results",
        help="Root directory for results.",
    )

    parser.add_argument(
        "--method",
        type=str,
        required=True,
        help="Method name to run.",
    )

    parser.add_argument(
        "--sequence",
        type=str,
        required=True,
        help="Sequence name to run.",
    )

    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only compute metrics for an existing prediction.",
    )

    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Run evo APE/RPE after successful run.",
    )

    return parser.parse_args()


def load_methods_config(path: str) -> List[MethodConfig]:
    data = load_json(path)
    return [MethodConfig(**m) for m in data["methods"]]


def load_sequences_config(path: str) -> List[SequenceConfig]:
    data = load_json(path)

    sequences = []

    for seq in data["sequences"]:
        resolved = resolve_sequence_paths(seq)
        sequences.append(SequenceConfig(**resolved))

    return sequences


def find_method(methods: List[MethodConfig], name: str) -> MethodConfig:
    for method in methods:
        if method.name == name:
            return method

    available = [m.name for m in methods]
    raise ValueError(f"Method not found: {name}. Available methods: {available}")


def find_sequence(sequences: List[SequenceConfig], name: str) -> SequenceConfig:
    for sequence in sequences:
        if sequence.name == name:
            return sequence

    available = [s.name for s in sequences]
    raise ValueError(f"Sequence not found: {name}. Available sequences: {available}")


def make_skip_run_result(
    method: MethodConfig,
    sequence: SequenceConfig,
    results_root: Path,
) -> RunResult:
    result_dir = results_root / method.name / sequence.name
    predicted = result_dir / "predicted_trajectory.txt"

    return RunResult(
        method=method.name,
        sequence=sequence.name,
        success=predicted.exists(),
        runtime_sec=0.0,
        peak_memory_mb=0.0,
        avg_memory_mb=0.0,
        result_dir=str(result_dir),
        predicted_trajectory=str(predicted) if predicted.exists() else None,
        error_message=None if predicted.exists() else "Prediction file not found.",
    )


def save_run_result(result: RunResult) -> None:
    result_dir = Path(result.result_dir)
    ensure_dir(result_dir)

    save_json(result_dir / "run_result.json", asdict(result))


def run_metrics_if_requested(sequence: SequenceConfig, result: RunResult) -> None:
    if not result.success or not result.predicted_trajectory:
        return

    metrics_dir = Path(result.result_dir) / "metrics"
    ensure_dir(metrics_dir)

    ape = run_evo_ape(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
    )

    rpe = run_evo_rpe(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
    )

    print(f"APE result: {ape}")
    print(f"RPE result: {rpe}")


def main() -> None:
    args = parse_args()

    results_root = Path(args.results)

    methods = load_methods_config(args.methods)
    sequences = load_sequences_config(args.sequences)

    method = find_method(methods, args.method)
    sequence = find_sequence(sequences, args.sequence)

    print(f"Running method={method.name}, sequence={sequence.name}")

    if args.skip_run:
        result = make_skip_run_result(method, sequence, results_root)
    else:
        runner = MethodRunner(results_root=results_root)
        raw_result = runner.run(method, sequence)
        result = dict_to_run_result(object_to_dict(raw_result))

    save_run_result(result)

    print(json.dumps(asdict(result), indent=2))

    if args.metrics:
        run_metrics_if_requested(sequence, result)

    summary_path = results_root / "summary_runs.json"
    save_json(summary_path, {"runs": [asdict(result)]})

    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()