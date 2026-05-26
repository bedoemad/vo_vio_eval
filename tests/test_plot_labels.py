import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from plot_final_benchmark_figures import auto_method_label


def test_auto_method_label_removes_dataset_tokens():
    assert auto_method_label("orbslam3_euroc_mono_inertial") == "ORB-SLAM3 Mono-Inertial"


def test_auto_method_label_handles_future_model_name():
    assert auto_method_label("my_new_vio_model") == "My New VIO Model"


def test_auto_method_label_handles_openvins():
    assert auto_method_label("openvins_euroc") == "OpenVINS"
