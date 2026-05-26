import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from generate_filtered_report import auto_method_label, filter_dataframe


def test_filtered_report_auto_method_label():
    assert auto_method_label("orbslam3_euroc_mono_inertial") == "ORB-SLAM3 Mono-Inertial"


def test_filter_dataframe_by_dataset():
    df = pd.DataFrame(
        {
            "dataset": ["EuRoC", "KITTI"],
            "method": ["a", "b"],
            "sequence": ["euroc_mh01", "kitti_00"],
        }
    )

    filtered = filter_dataframe(df, dataset="EuRoC", methods=None, sequences=None)

    assert len(filtered) == 1
    assert filtered.iloc[0]["sequence"] == "euroc_mh01"


def test_filter_dataframe_by_methods():
    df = pd.DataFrame(
        {
            "dataset": ["EuRoC", "EuRoC"],
            "method": ["orbslam3_mono", "dpvo_euroc"],
            "sequence": ["euroc_mh01", "euroc_mh01"],
        }
    )

    filtered = filter_dataframe(
        df,
        dataset=None,
        methods=["dpvo_euroc"],
        sequences=None,
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["method"] == "dpvo_euroc"


def test_filter_dataframe_by_sequences():
    df = pd.DataFrame(
        {
            "dataset": ["EuRoC", "EuRoC"],
            "method": ["a", "a"],
            "sequence": ["euroc_mh01", "euroc_mh02"],
        }
    )

    filtered = filter_dataframe(
        df,
        dataset=None,
        methods=None,
        sequences=["euroc_mh02"],
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["sequence"] == "euroc_mh02"
