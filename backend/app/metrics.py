"""
Application Telemetry, Metrics Collector, and Performance Monitor.
"""

import time
import os
import resource
from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import defaultdict

class MetricsCollector:
    """In-memory thread-safe metrics collector for real-time monitoring."""

    def __init__(self):
        self.start_time = time.time()
        self.total_requests = 0
        self.active_requests = 0
        self.requests_by_endpoint = defaultdict(int)
        self.requests_by_status = defaultdict(int)
        self.latencies_ms: List[float] = []
        self.max_latencies_retained = 1000

        # Quality analysis business metrics
        self.total_images_analyzed = 0
        self.quality_label_counts = {
            "ACCEPTABLE": 0,
            "DEGRADED": 0,
            "DEFECTIVE": 0,
        }
        self.defects_detected_by_type = defaultdict(int)

    def record_request_start(self):
        self.total_requests += 1
        self.active_requests += 1

    def record_request_end(self, method: str, path: str, status_code: int, duration_ms: float):
        self.active_requests = max(0, self.active_requests - 1)
        normalized_path = self._normalize_path(path)
        self.requests_by_endpoint[f"{method} {normalized_path}"] += 1
        self.requests_by_status[str(status_code)] += 1

        self.latencies_ms.append(duration_ms)
        if len(self.latencies_ms) > self.max_latencies_retained:
            self.latencies_ms.pop(0)

    def record_analysis(self, quality_label: str, issues: list = None):
        self.total_images_analyzed += 1
        if quality_label in self.quality_label_counts:
            self.quality_label_counts[quality_label] += 1
        else:
            self.quality_label_counts[quality_label] = 1

        if issues:
            for issue in issues:
                itype = issue.get("type", "unknown")
                self.defects_detected_by_type[itype] += 1

    def _normalize_path(self, path: str) -> str:
        # Collapse IDs in paths like /api/v1/analyses/12 -> /api/v1/analyses/{id}
        parts = path.strip("/").split("/")
        normalized = []
        for p in parts:
            if p.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(p)
        return "/" + "/".join(normalized)

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        uptime_seconds = round(time.time() - self.start_time, 2)
        
        # Calculate latency percentiles
        if self.latencies_ms:
            sorted_lat = sorted(self.latencies_ms)
            avg_lat = round(sum(sorted_lat) / len(sorted_lat), 2)
            p50_lat = round(sorted_lat[int(len(sorted_lat) * 0.50)], 2)
            p95_lat = round(sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)], 2)
            min_lat = round(sorted_lat[0], 2)
            max_lat = round(sorted_lat[-1], 2)
        else:
            avg_lat = p50_lat = p95_lat = min_lat = max_lat = 0.0

        # Memory footprint in MB (macOS/Linux)
        try:
            # maxrss is in bytes on macOS, KB on Linux
            rusage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if os.uname().sysname == "Darwin":
                memory_mb = round(rusage / (1024 * 1024), 2)
            else:
                memory_mb = round(rusage / 1024, 2)
        except Exception:
            memory_mb = 0.0

        return {
            "service": "QualiVision AI Engine",
            "uptime_seconds": uptime_seconds,
            "started_at": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
            "http": {
                "total_requests": self.total_requests,
                "active_requests": self.active_requests,
                "requests_by_endpoint": dict(self.requests_by_endpoint),
                "requests_by_status": dict(self.requests_by_status),
                "latency_ms": {
                    "avg": avg_lat,
                    "p50": p50_lat,
                    "p95": p95_lat,
                    "min": min_lat,
                    "max": max_lat,
                    "sample_window": len(self.latencies_ms),
                }
            },
            "domain_metrics": {
                "total_images_analyzed": self.total_images_analyzed,
                "quality_label_distribution": dict(self.quality_label_counts),
                "defect_breakdown": dict(self.defects_detected_by_type),
            },
            "system": {
                "process_memory_mb": memory_mb,
                "pid": os.getpid(),
            }
        }

metrics_collector = MetricsCollector()
