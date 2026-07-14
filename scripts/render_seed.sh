#!/usr/bin/env bash
# Render one org through the full realization pipeline.
# Usage: scripts/render_seed.sh datasets/dev/org-00002
# Content generation runs on the cursor agent CLI; every accept/assemble
# step validates via membench.pipeline and aborts the seed on failure.
set -euo pipefail
D="$1"
NAME=$(basename "$D")
PROMPT_CANON="Read ${D}/_missing.json: keys are fact templates '<<type | topic=slug | variant>>', values are context sentences (or templates when no context exists). Write ${D}/_missing_realized.json with the SAME keys mapped to realized one-sentence business statements. Rules: fit type/topic/variant; 'counterfactual-of-*' materially inverts the context sentence AND has exactly the same word count as it (same topic, opposite/different stance or value); v1/v2/v3 on one topic = ONE evolving policy, same statement shape with changing concrete values; 'near-miss-*' same topic as sibling, perturbed per variant name; 'distractor' variants are inert opinions/references/outcomes; every sentence unique; uniform business tone; concrete numbers/names where natural. Write ONLY that file — no scripts, no scratch files."

echo "[$NAME] step 1: canonical realization"
if [ ! -f "$D/events.jsonl" ]; then
  uv run python -m membench.pipeline missing --org "$D"
  if grep -q '"<<' "$D/_missing.json"; then
    for attempt in 1 2; do
      agent -p --trust --output-format text "$PROMPT_CANON" > /dev/null || true
      [ -f "$D/_missing_realized.json" ] && break
      echo "[$NAME] retry canonical realization"
    done
  fi
  uv run python -m membench.pipeline accept --org "$D"
fi

echo "[$NAME] step 2: event rendering"
uv run python -m membench.pipeline batches --org "$D"
for B in "$D"/render/batch-0*.json; do
  case "$B" in *".out.json") continue;; esac
  OUT="${B%.json}.out.json"
  [ -f "$OUT" ] && continue
  for attempt in 1 2; do
    agent -p --trust --output-format text "Read datasets/dev/org-00001/render/PROMPT.md and follow it exactly. Your batch file is ${B}. Write ${OUT} (a JSON object: event_id -> rendered content string, covering EVERY event in the batch). Write ONLY that file — no scripts, no scratch files." > /dev/null || true
    [ -f "$OUT" ] && break
    echo "[$NAME] retry $B"
  done
  [ -f "$OUT" ] || { echo "[$NAME] FAILED to render $B"; exit 1; }
done
uv run python -m membench.pipeline assemble --org "$D"

echo "[$NAME] step 3: twin"
uv run python -m membench.pipeline twin-prep --org "$D"
TD="${D}-twin"
for B in "$TD"/render/batch-0*.json; do
  case "$B" in *".out.json") continue;; esac
  OUT="${B%.json}.out.json"
  [ -f "$OUT" ] && continue
  for attempt in 1 2; do
    agent -p --trust --output-format text "Read datasets/dev/org-00001/render/PROMPT.md and follow it exactly. Your batch file is ${B}. Write ${OUT} (a JSON object: event_id -> rendered content string, covering EVERY event in the batch). Write ONLY that file — no scripts, no scratch files." > /dev/null || true
    [ -f "$OUT" ] && break
    echo "[$NAME] retry $B"
  done
  [ -f "$OUT" ] || { echo "[$NAME] FAILED to render twin $B"; exit 1; }
done
uv run python -m membench.pipeline twin-assemble --org "$D"
echo "[$NAME] DONE"
