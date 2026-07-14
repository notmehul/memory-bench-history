#!/bin/bash
cd /Users/radiohead/Dev/memory-bench
python3 .tmp_fix_twin_b01.py
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE"

if [ -f datasets/dev/org-00002-twin/render/batch-01.out.json ]; then
    wc -c datasets/dev/org-00002-twin/render/batch-01.out.json
fi

exit $EXIT_CODE
