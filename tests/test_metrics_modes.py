import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from metrics import _alignment_flags


def test_sim3_alignment_flags():
    assert _alignment_flags("sim3") == ["--align", "--correct_scale"]


def test_se3_alignment_flags():
    assert _alignment_flags("se3") == ["--align"]


def test_invalid_metric_mode_raises_error():
    with pytest.raises(ValueError):
        _alignment_flags("invalid")
