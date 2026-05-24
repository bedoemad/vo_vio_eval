from dataclasses import dataclass
from typing import Optional

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