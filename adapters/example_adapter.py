import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--sequence", required=True)
    parser.add_argument("--groundtruth", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Example adapter:
    # This copies the ground-truth trajectory as a fake prediction.
    # A real adapter would run a VO/VIO model and save its predicted trajectory.
    shutil.copy(args.groundtruth, output)

    print(f"Example adapter wrote trajectory to {output}")


if __name__ == "__main__":
    main()
