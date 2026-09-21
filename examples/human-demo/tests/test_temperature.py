import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_valid_conversion():
    result = subprocess.run([sys.executable, "temperature.py", "212"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0 and result.stdout.strip() == "100.0"


def test_invalid_input_is_rejected():
    result = subprocess.run([sys.executable, "temperature.py", "warm"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode != 0 and "numeric" in result.stderr
