"""Verification tests for Vehicle Damage Event Counter (Python)."""
import os
import subprocess
import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

APP_DIR = os.environ.get(
    "APP_DIR",
    "/app" if os.path.exists("/app/src/damage_aggregator.py") else str(Path(__file__).resolve().parent.parent / "environment" / "app")
)
SRC_PATH = os.environ.get("SRC_PATH", os.path.join(APP_DIR, "src", "damage_aggregator.py"))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(APP_DIR, "output"))
EXPECTED_TYPES = ["SCRATCH", "DENT", "CRACK", "GLASS_DAMAGE", "BROKEN_LAMP"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

if pytest is not None:
    @pytest.fixture(scope="module", autouse=True)
    def setup_output_dir():
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        yield


def parse_counts(path):
    """Parse output file into a dict of type -> count."""
    if not os.path.exists(path):
        return {}
    counts = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("=")
            if len(parts) == 2:
                counts[parts[0].strip()] = int(parts[1].strip())
    return counts


def run_aggregator(output_path, timeout=60.0):
    if os.path.exists(output_path):
        os.remove(output_path)

    cmd = [sys.executable, SRC_PATH, output_path]
    proc = subprocess.run(
        cmd,
        cwd=APP_DIR,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return proc


def test_single_threaded_correctness():
    """Verify the aggregator works and accounts for all 50,000 events."""
    small_out = os.path.join(OUTPUT_DIR, "small_counts.txt")
    proc = run_aggregator(small_out)

    assert proc.returncode == 0, f"Process failed: {proc.stderr}"
    assert os.path.exists(small_out), "Output file was not created."

    counts = parse_counts(small_out)
    total = sum(counts.values())
    assert total == 50000, f"Expected 50000 total events, got {total}. Counts: {counts}"
    for t in EXPECTED_TYPES:
        assert t in counts, f"Missing damage type: {t}"


def test_multi_run_consistency():
    """Verify running the aggregator multiple times produces identical, consistent counts."""
    results = []
    for i in range(3):
        out = os.path.join(OUTPUT_DIR, f"run_{i}.txt")
        proc = run_aggregator(out)
        assert proc.returncode == 0, f"Run {i} failed: {proc.stderr}"
        counts = parse_counts(out)
        results.append(counts)

    first = results[0]
    for i, r in enumerate(results[1:], 1):
        assert r == first, f"Run {i} produced inconsistent counts: expected {first}, got {r}"


def test_no_exceptions():
    """Verify application runs without throwing exceptions or tracebacks."""
    noerr_out = os.path.join(OUTPUT_DIR, "noerr.txt")
    proc = run_aggregator(noerr_out)

    assert proc.returncode == 0, f"Non-zero exit code: {proc.returncode}"
    assert "Traceback" not in proc.stderr, f"Traceback in stderr: {proc.stderr}"
    assert "Exception" not in proc.stderr, f"Exception in stderr: {proc.stderr}"
    assert "Error" not in proc.stderr, f"Error in stderr: {proc.stderr}"


def test_output_format():
    """Verify the output file adheres to KEY=VALUE per line."""
    fmt_out = os.path.join(OUTPUT_DIR, "fmt_test.txt")
    proc = run_aggregator(fmt_out)
    assert proc.returncode == 0, f"Process failed: {proc.stderr}"

    with open(fmt_out, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    assert len(lines) == 5, f"Expected 5 damage type lines, got {len(lines)}"
    for line in lines:
        parts = line.split("=")
        assert len(parts) == 2, f"Invalid format: {line}"
        assert parts[0] in EXPECTED_TYPES, f"Unknown damage type: {parts[0]}"
        assert parts[1].isdigit(), f"Count is not a valid number: {parts[1]}"
        assert int(parts[1]) > 0, f"Count must be positive: {parts[1]}"


def test_specific_known_values():
    """Verify all 50,000 events are accounted for with exactly 10,000 per damage type."""
    known_out = os.path.join(OUTPUT_DIR, "known.txt")
    proc = run_aggregator(known_out)
    assert proc.returncode == 0, f"Process failed: {proc.stderr}"

    counts = parse_counts(known_out)
    total = sum(counts.values())
    assert total == 50000, f"Expected 50000 total events, got {total}"

    for damage_type in EXPECTED_TYPES:
        actual = counts.get(damage_type, 0)
        assert actual == 10000, (
            f"Race condition detected! Wrong count for {damage_type}: expected 10000, got {actual}"
        )


if __name__ == "__main__":
    print("[Testing] Running test_no_exceptions...")
    test_no_exceptions()
    print("[Testing] Running test_output_format...")
    test_output_format()
    print("[Testing] Running test_single_threaded_correctness...")
    try:
        test_single_threaded_correctness()
    except AssertionError as e:
        print(f"FAILED (Expected for buggy code): {e}")
        sys.exit(1)
    print("[Testing] Running test_multi_run_consistency...")
    test_multi_run_consistency()
    print("[Testing] Running test_specific_known_values...")
    test_specific_known_values()
    print("ALL TESTS PASSED!")
