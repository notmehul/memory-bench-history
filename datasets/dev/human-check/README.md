# G2 human validation packets (prepared 2026-07-25)

Two human items remain for formal G2 closure (dataset-plan Phase 2):

## 1. Blinded salience spot-check (packets here)

Per seed: `seed-N/packet.json` holds 20 event excerpts, 10 embedding
probed facts and 10 distractor-only, same-topic siblings excluded —
prepared by the same `scripts/blind_check.py prep` used for the machine
rater protocol.

Protocol: read ONLY the packet (never `KEY-do-not-open.json`, never the
org dirs) and, for each excerpt id, guess `probed` or `distractor`.
Write answers as `seed-N/answers.json`: `{"<excerpt_id>": "probed" |
"distractor", ...}`. Then score:

    python scripts/blind_check.py score \
        datasets/dev/human-check/seed-N/KEY-do-not-open.json \
        datasets/dev/human-check/seed-N/answers.json

Gate: the human rater must NOT beat 65% accuracy (salience is flat).
Do the guessing in one sitting per seed, before any read-through of that
seed (a read-through primes you on which topics recur).

## 2. Narrative read-through

After the spot-check for a seed is scored: read the seed's
`events.jsonl` start to finish and note anything incoherent (broken
references, impossible timelines, personas acting out of character).
File notes as `seed-N/readthrough-notes.md`. One org minimum for G2;
all released orgs recommended.

Known context: seed 3 carries a documented salience residual
(validation-report §known limitation) — a mild spot-check signal there
is expected and already disclosed.
