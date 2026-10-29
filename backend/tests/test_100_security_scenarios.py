"""
SIGMA_ASR_VTT - 100 Security & Anti-Tamper Test Scenarios
Developer: أصيل السويدي
"""

import sys
import subprocess
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
SCRIPT_PATH = ROOT_DIR / "scratch" / "run_100_scenarios.py"

def test_100_adversarial_and_edge_case_scenarios():
    """Executes the full 100-scenario security matrix and verifies 100% pass rate."""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=30
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Passed (Secure):         100 / 100" in result.stdout
    assert "Vulnerable / Regressed:  0 / 100" in result.stdout
    assert "PERFECT SCORE" in result.stdout
