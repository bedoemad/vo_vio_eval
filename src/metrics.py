import subprocess
from pathlib import Path
from typing import Literal, Optional

from utils import ensure_dir


MetricMode = Literal["sim3", "se3"]


def _alignment_flags(mode: MetricMode) -> list[str]:
    """
    Returns evo alignment flags.

    sim3:
        Aligns pose and corrects scale.
        Useful for monocular VO where scale is ambiguous.

    se3:
        Aligns pose without scale correction.
        Useful for deployment-oriented metric-scale evaluation.
    """
    if mode == "sim3":
        return ["--align", "--correct_scale"]

    if mode == "se3":
        return ["--align"]

    raise ValueError(f"Unsupported metric mode: {mode}")


def run_evo_ape(
    groundtruth_path: str,
    predicted_path: str,
    result_dir: Path,
    mode: MetricMode = "sim3",
) -> Optional[Path]:
    """
    Runs evo APE evaluation.

    Assumes both files are in TUM trajectory format:
    timestamp tx ty tz qx qy qz qw
    """
    ensure_dir(result_dir)

    output_zip = result_dir / f"ape_{mode}_results.zip"

    command = [
        "evo_ape",
        "tum",
        str(groundtruth_path),
        str(predicted_path),
        *_alignment_flags(mode),
        "--save_results",
        str(output_zip),
    ]

    completed = subprocess.run(command)

    if completed.returncode == 0 and output_zip.exists():
        return output_zip

    return None


def run_evo_rpe(
    groundtruth_path: str,
    predicted_path: str,
    result_dir: Path,
    mode: MetricMode = "sim3",
) -> Optional[Path]:
    """
    Runs evo RPE evaluation.

    Assumes both files are in TUM trajectory format:
    timestamp tx ty tz qx qy qz qw
    """
    ensure_dir(result_dir)

    output_zip = result_dir / f"rpe_{mode}_results.zip"

    command = [
        "evo_rpe",
        "tum",
        str(groundtruth_path),
        str(predicted_path),
        *_alignment_flags(mode),
        "--save_results",
        str(output_zip),
    ]

    completed = subprocess.run(command)

    if completed.returncode == 0 and output_zip.exists():
        return output_zip

    return None