import psutil
from typing import List
import subprocess
from pathlib import Path
from typing import Optional

from utils import ensure_dir

def run_evo_ape(groundtruth_path: str, predicted_path: str, result_dir: Path) -> Optional[Path]:
    """
    Runs evo APE evaluation.

    Assumes both files are in TUM trajectory format:
    timestamp tx ty tz qx qy qz qw

    Install:
        pip install evo
    """
    ensure_dir(result_dir)
    output_zip = result_dir / "ape_results.zip"
    command = (
        f"evo_ape tum {groundtruth_path} {predicted_path} "
        f"--align --correct_scale "
        f"--save_results {output_zip}"
    )

    completed = subprocess.run(command, shell=True)
    if completed.returncode == 0 and output_zip.exists():
        return output_zip
    return None


def run_evo_rpe(groundtruth_path: str, predicted_path: str, result_dir: Path) -> Optional[Path]:
    """
    Runs evo RPE evaluation.
    """
    ensure_dir(result_dir)
    output_zip = result_dir / "rpe_results.zip"
    command = (
        f"evo_rpe tum {groundtruth_path} {predicted_path} "
        f"--align --correct_scale "
        f"--save_results {output_zip}"
    )

    completed = subprocess.run(command, shell=True)
    if completed.returncode == 0 and output_zip.exists():
        return output_zip
    return None
