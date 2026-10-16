"""Tests for credential_tester module."""

from __future__ import annotations

import ast
import os
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_module_parseable():
    src = (ROOT / "wfh_modules" / "credential_tester.py").read_text()
    ast.parse(src)


def test_crack_result_dataclass():
    from wfh_modules.credential_tester import CrackResult
    r = CrackResult(total_hashes=100, cracked=25)
    assert r.success_rate == 25.0
    finding = r.to_finding()
    assert finding["schema"] == "xpl.finding.v1"
    assert finding["severity"] == "HIGH"
    assert "25" in finding["title"]


def test_severity_mapping():
    from wfh_modules.credential_tester import CrackResult
    assert CrackResult(total_hashes=100, cracked=60).to_finding()["severity"] == "CRITICAL"
    assert CrackResult(total_hashes=100, cracked=30).to_finding()["severity"] == "HIGH"
    assert CrackResult(total_hashes=100, cracked=15).to_finding()["severity"] == "MEDIUM"
    assert CrackResult(total_hashes=100, cracked=5).to_finding()["severity"] == "LOW"
    assert CrackResult(total_hashes=100, cracked=0).to_finding()["severity"] == "INFO"


def test_detect_hash_mode_md5():
    from wfh_modules.credential_tester import detect_hash_mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("5d41402abc4b2a76b9719d911017c592\n")
        fh.flush()
        mode = detect_hash_mode(fh.name)
    os.unlink(fh.name)
    assert mode == 0


def test_detect_hash_mode_ntlm():
    from wfh_modules.credential_tester import detect_hash_mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("user:31d6cfe0d16ae931b73c59d7e0c089c0\n")
        fh.flush()
        mode = detect_hash_mode(fh.name)
    os.unlink(fh.name)
    assert mode == 1000


def test_detect_hash_mode_netntlmv2():
    from wfh_modules.credential_tester import detect_hash_mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("user:1001:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::\n")
        fh.flush()
        mode = detect_hash_mode(fh.name)
    os.unlink(fh.name)
    assert mode == 5600


def test_detect_hash_mode_bcrypt():
    from wfh_modules.credential_tester import detect_hash_mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("$2b$12$LJ3m4ystWbNG/4cFnPUdKOE3RbZqFCCeMtjNJxzGihFkSxvKPjLgK\n")
        fh.flush()
        mode = detect_hash_mode(fh.name)
    os.unlink(fh.name)
    assert mode == 3200


def test_detect_hash_mode_kerberos_tgs():
    from wfh_modules.credential_tester import detect_hash_mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("$krb5tgs$23$*user$REALM$spn*$abcdef0123456789\n")
        fh.flush()
        mode = detect_hash_mode(fh.name)
    os.unlink(fh.name)
    assert mode == 13100


def test_hash_modes_dict():
    from wfh_modules.credential_tester import HASH_MODES
    assert "ntlm" in HASH_MODES
    assert "bcrypt" in HASH_MODES
    assert "kerberos_tgs" in HASH_MODES
    assert HASH_MODES["ntlm"] == 1000


def test_cli_test_subparser():
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "wlf.py", "test", "--help"],
        capture_output=True, text=True, timeout=10,
        cwd=str(ROOT),
    )
    assert result.returncode == 0
    assert "--target" in result.stdout
    assert "--model" in result.stdout
