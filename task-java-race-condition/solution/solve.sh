#!/bin/bash
# Solution for task-java-race-condition (Python Vehicle Damage Detection Service)
set -euo pipefail

cd /app

cat << 'EOF' > /app/src/damage_aggregator.py
"""Fixed Vehicle Damage & Inspection Event Telemetry Aggregator."""
import os
import queue
import sys
import threading
from pathlib import Path
from typing import Dict, List

DAMAGE_TYPES: List[str] = ["SCRATCH", "DENT", "CRACK", "GLASS_DAMAGE", "BROKEN_LAMP"]


class DamageAggregator:
    """Aggregates vehicle damage events safely across concurrent worker threads."""

    def __init__(self, output_path: str, num_workers: int = 6):
        self.output_path = output_path
        self.num_workers = num_workers
        self.counts: Dict[str, int] = {dtype: 0 for dtype in DAMAGE_TYPES}
        self.event_queue: queue.Queue = queue.Queue()
        self.workers: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()

        self._start_workers()

    def _start_workers(self):
        self._running = True
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker_loop(self):
        while self._running:
            try:
                event_type = self.event_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if event_type is None:
                self.event_queue.task_done()
                break

            if event_type in self.counts:
                with self._lock:
                    self.counts[event_type] += 1

            self.event_queue.task_done()

    def record_event(self, event_type: str):
        self.event_queue.put(event_type)

    def shutdown(self):
        self.event_queue.join()
        self._running = False
        for _ in range(self.num_workers):
            self.event_queue.put(None)
        for t in self.workers:
            t.join()

        self.write_report()

    def write_report(self):
        out_file = Path(self.output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            lines = [f"{dtype}={self.counts[dtype]}" for dtype in DAMAGE_TYPES]
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/app/output/counts.txt"
    aggregator = DamageAggregator(output_path=output_path, num_workers=6)

    total_events = 50000
    for i in range(total_events):
        aggregator.record_event(DAMAGE_TYPES[i % len(DAMAGE_TYPES)])

    aggregator.shutdown()
    print("Damage event processing complete.")


if __name__ == "__main__":
    main()
EOF

echo "[Solution] Concurrency race condition fix applied to /app/src/damage_aggregator.py"
