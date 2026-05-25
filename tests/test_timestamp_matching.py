import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from run_generic_failure_diagnostics import nearest_merge


def test_nearest_merge_matches_within_tolerance():
    left = pd.DataFrame(
        {
            "timestamp": [1.00, 2.00],
            "error_m": [0.1, 0.2],
        }
    )

    right = pd.DataFrame(
        {
            "timestamp": [1.03, 2.04],
            "brightness_mean": [120.0, 130.0],
        }
    )

    merged = nearest_merge(left, right, tolerance=0.05)

    assert merged.loc[0, "brightness_mean"] == 120.0
    assert merged.loc[1, "brightness_mean"] == 130.0


def test_nearest_merge_rejects_outside_tolerance():
    left = pd.DataFrame(
        {
            "timestamp": [1.00, 2.00],
            "error_m": [0.1, 0.2],
        }
    )

    right = pd.DataFrame(
        {
            "timestamp": [1.20, 2.30],
            "brightness_mean": [120.0, 130.0],
        }
    )

    merged = nearest_merge(left, right, tolerance=0.05)

    assert pd.isna(merged.loc[0, "brightness_mean"])
    assert pd.isna(merged.loc[1, "brightness_mean"])
