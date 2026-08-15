# Deferred from v1 (v1 freeze, 2026-08-15)

Cut from v1 with **no work** — see the FREEZE section at the bottom of
`docs/dataset-plan.md` ("Cut from v1"). Each line says where the material lives
so nothing is lost; none of it is touched before the pilot numbers ship.

- **Typed-memory reference implementation (baseline #6)** — spec
  `docs/specs/typed-memory-reference.md` (status line marked DEFERRED);
  code `src/membench/typed_memory.py` + `prompts/typed-memory-extract.md`
  (registered as adapter `typed` in `membench.pilot`, unused in v1).
- **Summarize-then-RAG (baseline #4)** — description only, `docs/dataset-plan.md`
  Phase 5 list; never built.
- **Full-transcript silo** — `FullTranscriptAdapter(shared=False)` in
  `src/membench/adapters.py`; silo ablation runs on Mem0 instead (freeze, 2026-08-15).
- **K=3 worker resamples beyond the one variance subset** — protocol text in
  `docs/decision-log.md` §2026-07-25 (pilot protocol hardening); power analysis
  `docs/power-analysis.md`.
- **G2 human read-through (≥1 org)** — instructions `docs/human-review.md`; the
  machine-side G2 record is `docs/validation-report.md` + `docs/decision-log.md`
  §2026-07-18. Seeds 4/5 blinded spot-checks that were done stay on record.
- **Industry matrix (v2 factor)** — paragraph kept in `docs/dataset-plan.md`
  "Standing decisions" → v2 queue (added 2026-08-05).
- **L3 difficulty sizing** — `docs/vision.md` (ladder, crossover mapping) and
  the plan's risk register.
- **Model-grid / consumer-portability track (H3)** — `docs/vision.md` §6;
  hypothesis text `docs/decision-log.md` §2026-07-25 (H1–H3).
- **Seeds 4–5 screening** — unscreened holdouts; seed 4 partial cache
  (327/486, judged) under `datasets/dev/screening/org-00004/`; seed 5 manifest
  written; commands in `docs/decision-log.md` §2026-08-15 ("remaining: seeds 4–5").
- **Further vendor-survey verification** — `docs/vendor-survey.md` (cells marked
  not independently verified stay marked; only the top-4-stars selection was applied).
