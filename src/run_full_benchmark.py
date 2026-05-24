import argparse
import json
import subprocess
from pathlib import Path


PRESETS_PATH = Path("configs/benchmark_presets.json")


def run(cmd, allow_fail=False):
    print("\n" + "=" * 90)
    print(cmd)
    print("=" * 90)

    result = subprocess.run(cmd, shell=True)

    if result.returncode != 0:
        print(f"[ERROR] Command failed with code {result.returncode}: {cmd}")

        if not allow_fail:
            raise RuntimeError(f"Command failed: {cmd}")

    return result.returncode


def load_presets():
    if not PRESETS_PATH.exists():
        return {}

    with open(PRESETS_PATH, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Run the full VO/VIO benchmark pipeline."
    )

    parser.add_argument("--methods", nargs="+", default=None)
    parser.add_argument("--sequences", nargs="+", default=None)
    parser.add_argument("--preset", default=None)

    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--no-run", action="store_true")
    parser.add_argument("--allow-fail", action="store_true")

    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--skip-visual", action="store_true")
    parser.add_argument("--skip-motion", action="store_true")
    parser.add_argument("--skip-failure", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")

    args = parser.parse_args()

    methods = args.methods
    sequences = args.sequences

    if args.preset:
        presets = load_presets()

        if args.preset not in presets:
            raise ValueError(
                f"Unknown preset: {args.preset}. "
                f"Available presets: {list(presets.keys())}"
            )

        preset = presets[args.preset]
        methods = preset["methods"]
        sequences = preset["sequences"]

    if not methods or not sequences:
        raise ValueError("Provide --methods and --sequences, or use --preset.")

    print("Selected methods:", methods)
    print("Selected sequences:", sequences)
        # ------------------------------------------------------------
    # 0. Prepare dataset ground truth
    # ------------------------------------------------------------
    if not args.skip_prepare:
        seq_arg = " ".join(sequences)

        run(
            f"python src/prepare_datasets.py --sequences {seq_arg}",
            allow_fail=True,
        )

    # ------------------------------------------------------------
    # 1. Run selected methods/sequences
    # ------------------------------------------------------------
    if not args.no_run:
        total = len(methods) * len(sequences)
        counter = 0

        for method in methods:
            for sequence in sequences:
                counter += 1

                pred_path = (
                    Path("results")
                    / method
                    / sequence
                    / "predicted_trajectory.txt"
                )

                print(
                    f"\n[{counter}/{total}] "
                    f"method={method}, sequence={sequence}"
                )

                if args.skip_existing and pred_path.exists():
                    print(f"[SKIP] Existing prediction: {pred_path}")
                    continue

                run(
                    f"python src/main.py "
                    f"--method {method} "
                    f"--sequence {sequence} "
                    f"--metrics",
                    allow_fail=args.allow_fail,
                )

    # ------------------------------------------------------------
    # 2. Core benchmark summaries
    # ------------------------------------------------------------
    run("python src/summarize_results.py")
    run("python src/create_final_benchmark_table.py")

    # ------------------------------------------------------------
    # 3. Visual-condition analysis
    # ------------------------------------------------------------
    if not args.skip_visual:
        seq_arg = " ".join(sequences)

        run(
            f"python src/ensure_visual_conditions.py --sequences {seq_arg}",
            allow_fail=True,
        )

        run(
            "python src/create_final_visual_condition_table.py",
            allow_fail=True,
        )

    # ------------------------------------------------------------
    # 4. Existing visual failure-effect analysis
    # ------------------------------------------------------------
    if not args.skip_failure:
        run(
            "python src/create_final_failure_effect_table.py",
            allow_fail=True,
        )

    # ------------------------------------------------------------
    # 5. Motion-condition analysis
    # ------------------------------------------------------------
    if not args.skip_motion:
        run("python src/analyze_motion_conditions.py", allow_fail=True)
        run("python src/add_motion_to_error_correlation.py", allow_fail=True)
        run("python src/binned_motion_failure_analysis.py", allow_fail=True)
        run("python src/create_motion_failure_effect_table.py", allow_fail=True)

    # ------------------------------------------------------------
    # 6. Combined old diagnostic table
    # ------------------------------------------------------------
    if not args.skip_failure and not args.skip_motion:
        run(
            "python src/create_final_diagnostic_effect_table.py",
            allow_fail=True,
        )

    # ------------------------------------------------------------
    # 7. Generic method-agnostic diagnostics
    # ------------------------------------------------------------
    if not args.skip_failure and not args.skip_motion:
        run(
            "python src/run_generic_failure_diagnostics.py",
            allow_fail=True,
        )

    # ------------------------------------------------------------
    # 8. Final plots
    # ------------------------------------------------------------
    if not args.skip_plots:
        run("python src/plot_final_benchmark_figures.py", allow_fail=True)

        if not args.skip_visual:
            run(
                "python src/plot_final_visual_condition_figures.py",
                allow_fail=True,
            )

        if not args.skip_failure:
            run(
                "python src/plot_final_failure_effect_figures.py",
                allow_fail=True,
            )

        if not args.skip_motion:
            run("python src/plot_motion_failure_effects.py", allow_fail=True)

        if not args.skip_failure and not args.skip_motion:
            run(
                "python src/plot_final_diagnostic_effects.py",
                allow_fail=True,
            )

            run(
                "python src/plot_generic_failure_diagnostics.py",
                allow_fail=True,
            )

    run("python src/generate_report.py", allow_fail=True)
    
    print("\nFull benchmark pipeline finished.")


if __name__ == "__main__":
    main()