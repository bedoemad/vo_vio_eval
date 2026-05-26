import argparse
import subprocess
import sys


def run(cmd, allow_fail=False):
    print("\n" + "=" * 90)
    print(" ".join(cmd))
    print("=" * 90)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[ERROR] Command failed with code {result.returncode}")

        if not allow_fail:
            sys.exit(result.returncode)

    return result.returncode


def cmd_check(args):
    run(["python", "src/check_setup.py"])


def cmd_prepare(args):
    cmd = ["python", "src/prepare_datasets.py"]

    if args.all:
        cmd += ["--dataset", "all"]
    elif args.dataset:
        cmd += ["--dataset", args.dataset]

    if args.sequences:
        cmd += ["--sequences"] + args.sequences

    if args.force:
        cmd += ["--force"]

    run(cmd)


def cmd_run(args):
    cmd = ["python", "src/run_full_benchmark.py"]

    if args.preset:
        cmd += ["--preset", args.preset]
    else:
        if not args.methods or not args.sequences:
            print("[ERROR] Provide --preset or both --methods and --sequences.")
            sys.exit(1)

        cmd += ["--methods"] + args.methods
        cmd += ["--sequences"] + args.sequences

    if args.skip_existing:
        cmd += ["--skip-existing"]

    if args.no_run:
        cmd += ["--no-run"]

    if args.allow_fail:
        cmd += ["--allow-fail"]

    if args.skip_prepare:
        cmd += ["--skip-prepare"]

    if args.skip_visual:
        cmd += ["--skip-visual"]

    if args.skip_motion:
        cmd += ["--skip-motion"]

    if args.skip_failure:
        cmd += ["--skip-failure"]

    if args.skip_plots:
        cmd += ["--skip-plots"]

    run(cmd)


def cmd_summarize(args):
    run(["python", "src/summarize_results.py"])
    run(["python", "src/create_final_benchmark_table.py"])


def cmd_visual(args):
    cmd = ["python", "src/ensure_visual_conditions.py"]

    if args.sequences:
        cmd += ["--sequences"] + args.sequences

    if args.force:
        cmd += ["--force"]

    run(cmd)
    run(["python", "src/create_final_visual_condition_table.py"])


def cmd_motion(args):
    run(["python", "src/analyze_motion_conditions.py"])


def cmd_diagnose(args):
    run(["python", "src/run_generic_failure_diagnostics.py"], allow_fail=args.allow_fail)


def cmd_plot(args):
    run(["python", "src/plot_final_benchmark_figures.py"], allow_fail=True)
    run(["python", "src/plot_final_visual_condition_figures.py"], allow_fail=True)
    run(["python", "src/plot_final_failure_effect_figures.py"], allow_fail=True)
    run(["python", "src/plot_motion_failure_effects.py"], allow_fail=True)
    run(["python", "src/plot_final_diagnostic_effects.py"], allow_fail=True)
    run(["python", "src/plot_generic_failure_diagnostics.py"], allow_fail=True)

def cmd_report(args):
    run(["python", "src/generate_report.py"])

def cmd_report_filtered(args):
    cmd = ["python", "src/generate_filtered_report.py"]

    if args.dataset:
        cmd += ["--dataset", args.dataset]

    if args.methods:
        cmd += ["--methods"] + args.methods

    if args.sequences:
        cmd += ["--sequences"] + args.sequences

    if args.name:
        cmd += ["--name", args.name]

    run(cmd)

def cmd_run_one(args):
    cmd = [
        "python",
        "src/main.py",
        "--method",
        args.method,
        "--sequence",
        args.sequence,
    ]

    if args.methods_config:
        cmd += ["--methods", args.methods_config]

    if args.sequences_config:
        cmd += ["--sequences", args.sequences_config]

    if args.results:
        cmd += ["--results", args.results]

    if args.skip_run:
        cmd += ["--skip-run"]

    if args.metrics:
        cmd += ["--metrics"]

    run(cmd)

def main():
    parser = argparse.ArgumentParser(
        description="VO/VIO evaluation framework command-line interface."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # check
    p = sub.add_parser("check", help="Check setup, configs, tools, and dataset paths.")
    p.set_defaults(func=cmd_check)

    # prepare
    p = sub.add_parser("prepare", help="Prepare dataset ground-truth files.")
    p.add_argument("--all", action="store_true", help="Prepare all datasets.")
    p.add_argument("--dataset", choices=["euroc", "kitti", "all"], default=None)
    p.add_argument("--sequences", nargs="+", default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_prepare)

    # run
    p = sub.add_parser("run", help="Run full benchmark automation.")
    p.add_argument("--preset", default=None)
    p.add_argument("--methods", nargs="+", default=None)
    p.add_argument("--sequences", nargs="+", default=None)
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--no-run", action="store_true")
    p.add_argument("--allow-fail", action="store_true")
    p.add_argument("--skip-prepare", action="store_true")
    p.add_argument("--skip-visual", action="store_true")
    p.add_argument("--skip-motion", action="store_true")
    p.add_argument("--skip-failure", action="store_true")
    p.add_argument("--skip-plots", action="store_true")
    p.set_defaults(func=cmd_run)

        # run-one
    p = sub.add_parser(
        "run-one",
        help="Run one method on one sequence.",
    )
    p.add_argument(
        "--method",
        required=True,
        help="Method name from configs/methods.json.",
    )
    p.add_argument(
        "--sequence",
        required=True,
        help="Sequence name from configs/sequences.json.",
    )
    p.add_argument(
        "--methods-config",
        default=None,
        help="Optional path to methods config JSON.",
    )
    p.add_argument(
        "--sequences-config",
        default=None,
        help="Optional path to sequences config JSON.",
    )
    p.add_argument(
        "--results",
        default=None,
        help="Optional results root directory.",
    )
    p.add_argument(
        "--skip-run",
        action="store_true",
        help="Reuse an existing prediction and run only post-processing/metrics.",
    )
    p.add_argument(
        "--metrics",
        action="store_true",
        help="Run evo APE/RPE metrics after the method finishes.",
    )
    p.set_defaults(func=cmd_run_one)

    # summarize
    p = sub.add_parser("summarize", help="Regenerate benchmark summary tables.")
    p.set_defaults(func=cmd_summarize)

    # visual
    p = sub.add_parser("visual", help="Generate visual-condition files and summary.")
    p.add_argument("--sequences", nargs="+", default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_visual)

    # motion
    p = sub.add_parser("motion", help="Generate motion-condition files.")
    p.set_defaults(func=cmd_motion)

    # diagnose
    p = sub.add_parser("diagnose", help="Run generic method-agnostic failure diagnostics.")
    p.add_argument("--allow-fail", action="store_true")
    p.set_defaults(func=cmd_diagnose)

    # plot
    p = sub.add_parser("plot", help="Regenerate final plots.")
    p.set_defaults(func=cmd_plot)

    # report
    p = sub.add_parser("report", help="Generate HTML report.")
    p.set_defaults(func=cmd_report)
        # report-filtered
    p = sub.add_parser(
        "report-filtered",
        help="Generate a filtered dashboard report for selected datasets, methods, or sequences.",
    )
    p.add_argument(
        "--dataset",
        default=None,
        help="Dataset filter, for example: EuRoC or KITTI.",
    )
    p.add_argument(
        "--methods",
        nargs="+",
        default=None,
        help="Optional method names to include.",
    )
    p.add_argument(
        "--sequences",
        nargs="+",
        default=None,
        help="Optional sequence names to include.",
    )
    p.add_argument(
        "--name",
        default="filtered_report",
        help="Report output folder name under results/reports/.",
    )
    p.set_defaults(func=cmd_report_filtered)
    

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
