#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "/Users/radiohead/Dev/memory-bench/.tmp_fix_twin_b01.py"],
    cwd="/Users/radiohead/Dev/memory-bench",
    capture_output=True,
    text=True
)

print(result.stdout, end='')
print(result.stderr, end='', file=sys.stderr)
sys.exit(result.returncode)
