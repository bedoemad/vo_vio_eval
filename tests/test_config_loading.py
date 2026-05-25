import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config import load_methods_config, load_sequences_config


def test_methods_config_loads():
    methods = load_methods_config(str(PROJECT_ROOT / "configs" / "methods.json"))

    assert len(methods) > 0
    assert all(method.name for method in methods)
    assert all(method.command_template for method in methods)
    assert all(method.output_trajectory for method in methods)


def test_sequences_config_loads():
    sequences = load_sequences_config(str(PROJECT_ROOT / "configs" / "sequences.json"))

    assert len(sequences) > 0
    assert all(sequence.name for sequence in sequences)
    assert all(sequence.dataset for sequence in sequences)
    assert all(sequence.path for sequence in sequences)
    assert all(sequence.groundtruth for sequence in sequences)
