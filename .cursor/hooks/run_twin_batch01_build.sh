#!/bin/sh
set -e
cd /Users/radiohead/Dev/memory-bench
python3 .tmp_build_twin_batch01_full.py > .tmp_build_stdout.txt 2>&1 || true
