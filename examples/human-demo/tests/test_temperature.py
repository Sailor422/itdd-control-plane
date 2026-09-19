import subprocess
import sys


def test_valid_conversion():
    result = subprocess.run([sys.executable, "temperature.py", "212"], text=True, capture_output=True)
    assert result.returncode == 0 and result.stdout.strip() == "100.0"


def test_invalid_input_is_rejected():
    result = subprocess.run([sys.executable, "temperature.py", "warm"], text=True, capture_output=True)
    assert result.returncode != 0 and "numeric" in result.stderr
