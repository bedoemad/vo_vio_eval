import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config import (
    find_method,
    find_sequence,
    load_methods_config,
    load_sequences_config,
)


def test_find_existing_method():
    methods = load_methods_config(str(PROJECT_ROOT / "configs" / "methods.json"))

    method = find_method(methods, methods[0].name)

    assert method.name == methods[0].name


def test_find_missing_method_raises_error():
    methods = load_methods_config(str(PROJECT_ROOT / "configs" / "methods.json"))

    with pytest.raises(ValueError):
        find_method(methods, "non_existing_method")


def test_find_existing_sequence():
    sequences = load_sequences_config(str(PROJECT_ROOT / "configs" / "sequences.json"))

    sequence = find_sequence(sequences, sequences[0].name)

    assert sequence.name == sequences[0].name


def test_find_missing_sequence_raises_error():
    sequences = load_sequences_config(str(PROJECT_ROOT / "configs" / "sequences.json"))

    with pytest.raises(ValueError):
        find_sequence(sequences, "non_existing_sequence")
