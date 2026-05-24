from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, List, Optional

from config_utils import load_json, resolve_sequence_paths


@dataclass
class MethodConfig:
    name: str
    command_template: str
    output_trajectory: str


@dataclass
class SequenceConfig:
    name: str
    dataset: str
    path: str
    groundtruth: str
    camera_topic_or_folder: Optional[str] = None
    imu_path: Optional[str] = None


@dataclass
class RunResult:
    method: str
    sequence: str
    success: bool
    runtime_sec: float
    peak_memory_mb: float
    avg_memory_mb: float
    result_dir: str
    predicted_trajectory: Optional[str]
    error_message: Optional[str] = None


def load_methods_config(path: str) -> List[MethodConfig]:
    data = load_json(path)
    return [MethodConfig(**method) for method in data["methods"]]


def load_sequences_config(path: str) -> List[SequenceConfig]:
    data = load_json(path)

    sequences = []
    for sequence in data["sequences"]:
        resolved = resolve_sequence_paths(sequence)
        sequences.append(SequenceConfig(**resolved))

    return sequences


def find_method(methods: List[MethodConfig], name: str) -> MethodConfig:
    for method in methods:
        if method.name == name:
            return method

    available = [method.name for method in methods]
    raise ValueError(f"Method not found: {name}. Available methods: {available}")


def find_sequence(sequences: List[SequenceConfig], name: str) -> SequenceConfig:
    for sequence in sequences:
        if sequence.name == name:
            return sequence

    available = [sequence.name for sequence in sequences]
    raise ValueError(f"Sequence not found: {name}. Available sequences: {available}")


def object_to_dict(obj: Any) -> Dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)

    raise TypeError(f"Cannot convert object to dict: {type(obj)}")


def dict_to_run_result(data: Dict[str, Any]) -> RunResult:
    return RunResult(
        method=data["method"],
        sequence=data["sequence"],
        success=bool(data["success"]),
        runtime_sec=float(data.get("runtime_sec", 0.0)),
        peak_memory_mb=float(data.get("peak_memory_mb", 0.0)),
        avg_memory_mb=float(data.get("avg_memory_mb", 0.0)),
        result_dir=str(data["result_dir"]),
        predicted_trajectory=data.get("predicted_trajectory"),
        error_message=data.get("error_message"),
    )