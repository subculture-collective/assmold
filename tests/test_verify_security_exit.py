"""The canonical verifier must stop when security dispositions are invalid."""

import os
import subprocess
from pathlib import Path


def test_verifier_stops_on_invalid_security_exceptions(tmp_path: Path) -> None:
    tools = tmp_path / "bin"
    tools.mkdir()
    calls = tmp_path / "calls"
    programs = {
        "docker": '#!/bin/sh\nprintf "%s\\n" "docker $*" >> "$CALLS"\ncase "$*" in *" port "*) echo "127.0.0.1:15432";; esac\n',
        "npm": '#!/bin/sh\necho "npm reached" >> "$CALLS"\n',
        "fixture-python": '#!/bin/sh\ncase "$1" in -c) echo "3.11";; esac\ncase "$*" in *check_security_exceptions.py*) echo "expired policy" >&2; exit 23;; *pip_audit*) echo "audit reached" >> "$CALLS";; esac\n',
    }
    for name, source in programs.items():
        command = tools / name
        command.write_text(source)
        command.chmod(0o755)
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.update(PATH=f"{tools}:/usr/bin:/bin", PYTHON_BIN=str(tools / "fixture-python"), CALLS=str(calls))
    result = subprocess.run(["bash", str(root / "scripts/verify.sh")], env=env, capture_output=True, text=True)
    assert result.returncode == 23
    assert "expired policy" in result.stderr
    commands = calls.read_text()
    assert "audit reached" not in commands
    assert "npm reached" not in commands
    assert "down --volumes --remove-orphans" in commands
