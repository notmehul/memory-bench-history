#!/bin/sh
cd /Users/radiohead/Dev/memory-bench
python3 .tmp_validate_twin_batch01.py
echo "---SEPARATOR---"
python3 .tmp_build_twin_batch01_full.py
