#!/usr/bin/python3
"""Count upgrade candidates from local APT lists; never update or install."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def count_upgrades(output):
    return sum(line.startswith("Inst ") for line in output.splitlines())


def refresh(cache):
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    code, text = 0, "?"
    try:
        result = subprocess.run(["apt-get", "--simulate", "upgrade"],
                                env={**os.environ, "LC_ALL": "C"},
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=25, check=True)
        text = str(count_upgrades(result.stdout))
    except (OSError, subprocess.SubprocessError):
        print("Could not read local APT upgrade candidates", file=sys.stderr)
        code = 1
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=cache,
                                     prefix=".updates-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(text + "\n")
            stream.flush()
            os.replace(temporary, cache / "updates.txt")
        finally:
            temporary.unlink(missing_ok=True)
    return code


if __name__ == "__main__":
    sys.exit(refresh(Path.home() / ".cache/mbp-sway"))
