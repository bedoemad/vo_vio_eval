import psutil
from typing import List
class ResourceMonitor:
    """Monitors CPU memory usage of a subprocess tree."""

    def __init__(self, pid: int):
        self.pid = pid
        self.samples_mb: List[float] = []

    def _memory_tree_mb(self) -> float:
        try:
            root = psutil.Process(self.pid)
            processes = [root] + root.children(recursive=True)
            total_bytes = 0
            for proc in processes:
                try:
                    total_bytes += proc.memory_info().rss
                except psutil.Error:
                    pass
            return total_bytes / (1024 * 1024)
        except psutil.Error:
            return 0.0

    def sample(self) -> None:
        self.samples_mb.append(self._memory_tree_mb())

    @property
    def peak_mb(self) -> float:
        return max(self.samples_mb) if self.samples_mb else 0.0

    @property
    def avg_mb(self) -> float:
        return sum(self.samples_mb) / len(self.samples_mb) if self.samples_mb else 0.0
