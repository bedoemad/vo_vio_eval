import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config import dict_to_run_result


def test_dict_to_run_result_preserves_runtime_metadata():
    data = {
        "method": "orbslam3_euroc_mono_inertial",
        "sequence": "euroc_mh01",
        "success": True,
        "runtime_sec": 208.1876,
        "peak_memory_mb": 1065.0,
        "avg_memory_mb": 852.5,
        "result_dir": "results/orbslam3_euroc_mono_inertial/euroc_mh01",
        "predicted_trajectory": "results/orbslam3_euroc_mono_inertial/euroc_mh01/predicted_trajectory.txt",
        "error_message": None,
    }

    result = dict_to_run_result(data)

    assert result.success is True
    assert result.runtime_sec == 208.1876
    assert result.peak_memory_mb == 1065.0
    assert result.avg_memory_mb == 852.5
    assert result.predicted_trajectory.endswith("predicted_trajectory.txt")
