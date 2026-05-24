import os
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import List

from config import MethodConfig, SequenceConfig, RunResult
from resource_monitor import ResourceMonitor
from utils import ensure_dir, save_json


class MethodRunner:
    def __init__(self, results_root: Path):
        self.results_root = results_root

    def run(self, method: MethodConfig, sequence: SequenceConfig) -> RunResult:
        result_dir = self.results_root / method.name / sequence.name
        ensure_dir(result_dir)

        stdout_path = result_dir / "stdout.log"
        stderr_path = result_dir / "stderr.log"
        monitor_path = result_dir / "resource_usage.csv"
        metadata_path = result_dir / "run_result.json"

        predicted_trajectory = result_dir / "predicted_trajectory.txt"
        output_path = str(predicted_trajectory)

        command = method.command_template.format(
            sequence_name=sequence.name,
            sequence_path=sequence.path,
            groundtruth_path=sequence.groundtruth,
            output_path=output_path,
            result_dir=str(result_dir),
        )

        start = time.time()
        memory_samples: List[float] = []

        try:
            with open(stdout_path, "w", encoding="utf-8") as stdout_file, open(
                stderr_path, "w", encoding="utf-8"
            ) as stderr_file:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    cwd=os.getcwd(),
                )

                monitor = ResourceMonitor(process.pid)

                with open(monitor_path, "w", encoding="utf-8") as monitor_file:
                    monitor_file.write("elapsed_sec,memory_mb\n")

                    while process.poll() is None:
                        elapsed = time.time() - start
                        monitor.sample()

                        mem = monitor.samples_mb[-1]
                        memory_samples.append(mem)

                        monitor_file.write(f"{elapsed:.4f},{mem:.4f}\n")
                        monitor_file.flush()

                        time.sleep(0.5)

                return_code = process.wait()
                runtime_sec = time.time() - start

                success = return_code == 0 and predicted_trajectory.exists()

                if return_code != 0:
                    error_message = (
                        f"Command failed with return code {return_code}. "
                        "Check stderr.log."
                    )
                elif not predicted_trajectory.exists():
                    error_message = (
                        "Command finished, but predicted trajectory was not created."
                    )
                else:
                    error_message = None

                result = RunResult(
                    method=method.name,
                    sequence=sequence.name,
                    success=success,
                    runtime_sec=runtime_sec,
                    peak_memory_mb=max(memory_samples) if memory_samples else 0.0,
                    avg_memory_mb=(
                        sum(memory_samples) / len(memory_samples)
                        if memory_samples
                        else 0.0
                    ),
                    result_dir=str(result_dir),
                    predicted_trajectory=(
                        str(predicted_trajectory)
                        if predicted_trajectory.exists()
                        else None
                    ),
                    error_message=error_message,
                )

        except Exception as exc:
            runtime_sec = time.time() - start

            result = RunResult(
                method=method.name,
                sequence=sequence.name,
                success=False,
                runtime_sec=runtime_sec,
                peak_memory_mb=max(memory_samples) if memory_samples else 0.0,
                avg_memory_mb=(
                    sum(memory_samples) / len(memory_samples)
                    if memory_samples
                    else 0.0
                ),
                result_dir=str(result_dir),
                predicted_trajectory=None,
                error_message=str(exc),
            )

        save_json(metadata_path, asdict(result))
        return result