import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dpvo-root", default=str(Path.home() / "vo_work" / "DPVO"))
    parser.add_argument("--conda-env", default="dpvo")
    parser.add_argument("--calib", default="calib/euroc.txt")
    parser.add_argument("--stride", type=int, default=2)
    args = parser.parse_args()

    dpvo_root = Path(args.dpvo_root).expanduser().resolve()
    sequence_path = Path(args.sequence).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    dpvo_python = Path.home() / "miniconda3" / "envs" / args.conda_env / "bin" / "python"

    if not dpvo_python.exists():
        raise RuntimeError(f"DPVO Python not found: {dpvo_python}")

    if not sequence_path.exists():
        raise RuntimeError(f"Sequence path not found: {sequence_path}")

    raw_traj = dpvo_root / "saved_trajectories" / "result.txt"

    if raw_traj.exists():
        raw_traj.unlink()

    cmd = [
        str(dpvo_python),
        "demo.py",
        "--imagedir",
        str(sequence_path),
        "--calib",
        args.calib,
        "--stride",
        str(args.stride),
        "--save_trajectory",
    ]

    print("Running DPVO command:")
    print(" ".join(cmd))
    print(f"Working directory: {dpvo_root}")

    result = subprocess.run(cmd, cwd=str(dpvo_root))

    if result.returncode != 0:
        raise RuntimeError(f"DPVO failed with return code {result.returncode}")

    if not raw_traj.exists():
        raise RuntimeError(f"DPVO output not found: {raw_traj}")

    raw_copy = output.with_name(output.stem + "_raw.txt")
    shutil.copy(raw_traj, raw_copy)

    project_root = Path(__file__).resolve().parents[1]
    converter_python = project_root / ".venv" / "bin" / "python"
    converter_script = project_root / "src" / "convert_dpvo_euroc_timestamps.py"

    convert_cmd = [
        str(converter_python),
        str(converter_script),
        "--input",
        str(raw_copy),
        "--image-dir",
        str(sequence_path),
        "--output",
        str(output),
        "--stride",
        str(args.stride),
    ]

    print("Running timestamp conversion:")
    print(" ".join(convert_cmd))

    result = subprocess.run(convert_cmd)

    if result.returncode != 0:
        raise RuntimeError(f"DPVO timestamp conversion failed with return code {result.returncode}")

    print("DPVO EuRoC adapter finished.")
    print(f"Raw trajectory: {raw_copy}")
    print(f"Converted trajectory: {output}")


if __name__ == "__main__":
    main()