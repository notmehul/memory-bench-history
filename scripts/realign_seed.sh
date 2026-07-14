#!/usr/bin/env bash
# Re-align one org after a planner change: regenerate the ledger, reuse every
# unchanged render, re-render only the diff, then rebuild the twin.
# Usage: scripts/realign_seed.sh datasets/dev/org-00002
set -euo pipefail
D="$1"
NAME=$(basename "$D")
SEED=$((10#$(echo "$NAME" | sed 's/org-0*//')))
PROMPT_CANON="Read ${D}/_missing.json: keys are fact templates '<<type | topic=slug | variant>>', values are context sentences (or templates when no context exists). Write ${D}/_missing_realized.json with the SAME keys mapped to realized one-sentence business statements of 9-13 words each. Rules: fit type/topic/variant; 'counterfactual-of-*' materially inverts the context sentence AND has exactly the same word count as it; v1/v2/v3 same topic = ONE evolving policy with changing concrete values; 'near-miss-*' same topic as sibling, perturbed per variant name; 'distractor' variants inert; every sentence unique; uniform business tone. Write ONLY that file — no scripts, no scratch files."
RENDER_RULES="Read datasets/dev/org-00001/render/PROMPT.md and follow it EXACTLY, especially rule 3: each marked paraphrase within ±2 words of its statement, no hedges inside markers. Output must be VALID JSON (no trailing commas)."

echo "[$NAME] snapshot + regenerate"
cp "$D/org.json" "$D/org.prev.json"
[ -f "$D/events.annotated.jsonl" ] && cp "$D/events.annotated.jsonl" "$D/events.prev.jsonl"
uv run python -m membench.generate --seed "$SEED" --out "$(dirname "$D")" | tail -1

echo "[$NAME] canonical realization"
uv run python -m membench.pipeline missing --org "$D"
if grep -q '"<<' "$D/_missing.json"; then
  for attempt in 1 2; do
    agent -p --trust --output-format text "$PROMPT_CANON" > /dev/null || true
    [ -f "$D/_missing_realized.json" ] && break
  done
fi
uv run python -m membench.pipeline accept --org "$D"

echo "[$NAME] rediff + render"
uv run python -m membench.pipeline rediff --org "$D"
for B in "$D"/render3/batch-0*.json; do
  case "$B" in *".out.json") continue;; esac
  OUT="${B%.json}.out.json"
  [ -f "$OUT" ] && continue
  for attempt in 1 2; do
    agent -p --trust --output-format text "$RENDER_RULES Your batch file is ${B}. Write ${OUT} (JSON object: event_id -> rendered content string, EVERY event covered). Write ONLY that file." > /dev/null || true
    [ -f "$OUT" ] && break
    echo "[$NAME] retry $B"
  done
  [ -f "$OUT" ] || { echo "[$NAME] FAILED $B"; exit 1; }
done
uv run python -m membench.pipeline reassemble --org "$D" || {
  echo "[$NAME] LINT FAILED — leaving for outlier repair"; exit 2; }

echo "[$NAME] twin"
rm -rf "${D}-twin"
uv run python -m membench.pipeline twin-prep --org "$D"
for B in "${D}-twin"/render/batch-0*.json; do
  case "$B" in *".out.json") continue;; esac
  OUT="${B%.json}.out.json"
  for attempt in 1 2; do
    agent -p --trust --output-format text "$RENDER_RULES Your batch file is ${B}. Write ${OUT} (JSON object: event_id -> rendered content string, EVERY event covered). Write ONLY that file." > /dev/null || true
    [ -f "$OUT" ] && break
  done
  [ -f "$OUT" ] || { echo "[$NAME] FAILED twin $B"; exit 1; }
done
uv run python -m membench.pipeline twin-assemble --org "$D"
echo "[$NAME] REALIGNED"
