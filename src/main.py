from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from config import (
    MethodConfig,
    RunResult,
    SequenceConfig,
    dict_to_run_result,
    find_method,
    find_sequence,
    load_methods_config,
    load_sequences_config,
    object_to_dict,
)
from method_runner import MethodRunner
from metrics import run_evo_ape, run_evo_rpe
from utils import ensure_dir, save_json

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

    ape_sim3 = run_evo_ape(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
        mode="sim3",
    )

    rpe_sim3 = run_evo_rpe(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
        mode="sim3",
    )

    ape_se3 = run_evo_ape(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
        mode="se3",
    )

    rpe_se3 = run_evo_rpe(
        sequence.groundtruth,
        result.predicted_trajectory,
        metrics_dir,
        mode="se3",
    )

    print(f"APE Sim(3) result: {ape_sim3}")
    print(f"RPE Sim(3) result: {rpe_sim3}")
    print(f"APE SE(3) result: {ape_se3}")
    print(f"RPE SE(3) result: {rpe_se3}")

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

    latest_summary_path = results_root / "latest_run_summary.json"
    save_json(latest_summary_path, {"latest_run": asdict(result)})

    print(f"Saved latest run summary to {latest_summary_path}")


if __name__ == "__main__":
    main()