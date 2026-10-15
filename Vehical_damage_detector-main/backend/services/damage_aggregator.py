"""Vehicle Damage & Inspection Event Telemetry Aggregator.

Processes high-volume vehicle damage inspection streams across concurrent
worker threads and generates summary audit reports for insurance adjusters
and depot managers.
"""
import os
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

# Core vehicle damage types aligned with backend/services/damage_detector.py
DAMAGE_TYPES: List[str] = ["SCRATCH", "DENT", "CRACK", "GLASS_DAMAGE", "BROKEN_LAMP"]


class DamageAggregator:
    """Aggregates vehicle damage events across concurrent worker threads."""

    def __init__(self, output_path: str, num_workers: int = 6):
        self.output_path = output_path
        self.num_workers = num_workers
        self.counts: Dict[str, int] = {dtype: 0 for dtype in DAMAGE_TYPES}
        self.event_queue: queue.Queue = queue.Queue()
        self.workers: List[threading.Thread] = []
        self._running = False
        # NOTE: Missing thread synchronization lock (threading.Lock) here causes race conditions!

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
                # -------------------------------------------------------------
                # CONCURRENCY BUG / RACE CONDITION:
                # Non-atomic read-modify-write without thread synchronization.
                # When multiple worker threads process damage events concurrently,
                # updates are overwritten and lost.
                # -------------------------------------------------------------
                current = self.counts[event_type]
                time.sleep(0)  # Context switch / thread yield during inspection validation
                self.counts[event_type] = current + 1

            self.event_queue.task_done()

    def record_event(self, event_type: str):
        """Dispatches an incoming vehicle inspection damage event to the worker pool."""
        self.event_queue.put(event_type)

    def shutdown(self):
        """Flushes the event queue, stops worker threads, and writes the summary report."""
        self.event_queue.join()
        self._running = False
        for _ in range(self.num_workers):
            self.event_queue.put(None)
        for t in self.workers:
            t.join()

        self.write_report()

    def write_report(self):
        """Writes the damage audit report in KEY=VALUE format."""
        out_file = Path(self.output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"{dtype}={self.counts[dtype]}" for dtype in DAMAGE_TYPES]
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/app/output/counts.txt"
    aggregator = DamageAggregator(output_path=output_path, num_workers=6)

    # Simulate 50,000 vehicle inspection events (10,000 per damage type)
    total_events = 50000
    for i in range(total_events):
        aggregator.record_event(DAMAGE_TYPES[i % len(DAMAGE_TYPES)])

    aggregator.shutdown()
    print("Damage event processing complete.")


if __name__ == "__main__":
    main()
