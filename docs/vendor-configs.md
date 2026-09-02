# Frozen system configurations — v1 pilot (2026-08-27)

Written and committed BEFORE any live run against any system (vendor-fairness
protocol; "prespecified" = corroborated by this file's git history). Every value
below is read from the adapter code, not from intent. Live smokes (status queue
item 4) may surface SDK breakage; the only permitted post-smoke changes are
**mechanical availability fixes** (auth flags, timeouts, API-shape corrections)
recorded here as dated amendments — never retrieval-quality tuning. No config
changes of any kind once seed runs start.

## Shared across all systems (identical by construction)

| Parameter | Value | Where |
| :--- | :--- | :--- |
| Task worker | gpt-5.4, effort medium, codex-cli 0.144.5 (pinned via `membench.codex_bin`) | AGENTS.md hard rule |
| Retrieval depth | top-k = 8 (every retrieval system) | `rag.py` `k=8`; `top_k=8` in each `sut_*.py` |
| Prompt template | `retrieval_prompt(memories, task)` — one shared template; bare task when no hits | `rag.py` |
| Event rendering | `_render_event(event)` — identical text into every system | `adapters.py` |
| Shared-store scope | one org-wide store; dedupe by `event_id`; per-principal visibility NOT enforced (v1 scores no leakage; disclosed) | each adapter |
| Silo ablation | Mem0 only (`mem0-silo`): per-principal stores, event added under every witness | `pilot.py` registry |
| Ingestion | full pass per side/K, fresh adapter/store per run | `pilot.py run_side` |

## Baselines

- **no-memory** — bare task to the worker (cached floor).
- **full-transcript** — entire witnessed stream in the prompt (ceiling anchor).
- **grep-agent** — worker greps the raw stream files itself.
- **naive-RAG** (`rag`) — chunk = one event; embeddings pinned
  `gemini-embedding-001` (`GeminiEmbedder`, batch 100, chunk vector cached per
  event text); cosine; top-8 in chronological order. Lexical ablation
  `rag-lexical` = same adapter, stdlib BM25 (k1=1.5, b=0.75).

## Market systems (top-4-by-stars rule, applied 2026-08-15)

Principle: vendor-default behaviour wherever the SDK allows, embedded/local
storage (no docker on the run machine), internal LLM = Gemini where
configurable (one key, one billing surface; disclosed as a deviation from
vendor default in each case).

### Mem0 (`mem0ai>=2.0,<3`, local mode)
- LLM `gemini-2.5-flash`; embedder `models/gemini-embedding-001` @ 768 dims;
  vector store embedded Qdrant (scratch dir, `on_disk=False`); sqlite history.
  Vendor defaults displaced: OpenAI gpt-5-mini + text-embedding-3-small.
- Ingest `Memory.add(text, user_id=scope, infer=True)` — vendor-default LLM
  extraction/consolidation ON. Search `Memory.search(task, filters={"user_id":
  scope}, top_k=8)` (2.0.x rejects top-level `user_id=`). Hits rendered
  `[created_at] memory`. `MEM0_TELEMETRY=false`.

### Cognee (`cognee>=1.4`, embedded)
- LLM `gemini/gemini-2.5-flash`; embedder `gemini/gemini-embedding-001` @ 3072
  dims (env-configured before first import, `configure_gemini_env`). Vendor
  defaults displaced: OpenAI gpt-5-mini + text-embedding-3-large. Storage =
  cognee defaults: sqlite relational, lancedb vector, kuzu graph — embedded.
- `cognee.add(text, dataset_name=scope)`; `cognify` lazily once per scope per
  dirty period (at most once per probe injection). Search
  `SearchType.CHUNKS, top_k=8` — raw chunk texts, no LLM answer generation.
- Known risk for smoke: cognee 1.5.x enables auth/multi-tenant by default;
  any needed flag is an availability amendment, recorded here.

### Graphiti (`graphiti-core[kuzu,google-genai]>=0.29`, embedded)
- Graph driver embedded **Kuzu** (in 0.29.3; deprecated upstream — disclosed;
  no docker ⇒ no Neo4j/FalkorDB). LLM/embedder/reranker = graphiti's Gemini
  clients at their own defaults (gemini-3-flash-preview + gemini-2.5-flash-lite,
  text-embedding-001). Vendor defaults displaced: OpenAI.
- `add_episode(name=event_id, episode_body=rendered, source_description=surface,
  reference_time=sim_time, group_id=scope)` — LLM extraction/dedup/temporal
  invalidation per event (cost counted). Search = `graphiti.search(task,
  group_ids=[scope], num_results=8)` → edge facts, `[valid_at] fact`.
  `GRAPHITI_TELEMETRY_ENABLED=false`.

### Supermemory (`supermemory>=3.59`, hosted)
- Hosted only; internal LLM/embedder vendor-managed and NOT configurable — the
  one system running fully on vendor defaults (disclosed; no Gemini wiring).
- Ingest `documents.add(content, container_tag=scope, custom_id, document_date=
  sim_time, metadata)`; search `search.memories(q=task, container_tag=scope,
  limit=8)` → `.memory`/`.chunk`, rendered `[sim_time] text`.
- **Settle policy (frozen; ingestion is async server-side):** before the first
  search after new ingests, sleep 5 s then poll `documents.list_processing()`
  until the queue drains, bounded at 600 s (`ingest_settle_seconds=5,
  wait_for_processing=True, settle_timeout=600` — wired in the `pilot.py`
  registry; waits recorded in `settle_waits`/`settle_seconds` counters).
  Timeout hits are reported, never silently absorbed.

## Mechanical amendments (dated; isolation/availability only, never capability)

- **2026-09-02 — Supermemory container-tag namespacing.** The hosted store
  persists across runs while every other adapter's store is per-run (Mem0
  fresh tempdir, Cognee root wiped on first use, Graphiti in-memory Kuzu).
  With the fixed `org` tag, a twin run would retrieve base-run documents and
  seeds would stack. Fix: every container tag (and custom_id) is prefixed
  with the org side's dir name (`org-00001`, `org-00001-twin`, ...), passed
  by `pilot.run_side`; smokes use a dated `smoke-YYYY-MM-DD` prefix. Changes
  nothing about retrieval within a run; caught before any live call.

- **2026-09-02 — Supermemory live-smoke amendments (mechanical).** First live
  calls surfaced three API realities, all fixed before any protocol run:
  (1) container tags/custom ids reject dots — namespace separator is `:`,
  parts sanitized to `[A-Za-z0-9_-]`; (2) null values are rejected —
  `document_date` and null metadata entries are omitted (v1 streams carry no
  `sim_time`; see the dataset note below); (3) `search.memories` defaults to
  extracted-memories-only, which stays empty until the vendor's batched
  "dreaming" extraction lands minutes after ingest — searches now pin
  `search_mode="hybrid"` (the mode the vendor's own docs recommend: memories
  + document chunks). Ingestion stays on the vendor-default `dreaming:
  "dynamic"`; whatever memories exist at probe time are what the product
  provides, and the settle policy bounds only queue processing, not
  extraction — disclosed.
- **2026-09-02 — dataset carries no timestamps (applies to every system).**
  Every event in the frozen streams has `sim_time: null` (the generator never
  emitted times; screening anchors never rendered events, so nothing frozen
  is affected). Temporal order is positional — stream order only. Adapters
  now render events without a `[None]` bracket, Graphiti gets a synthetic
  monotonic `reference_time` encoding stream order only (the same signal
  every adapter gets from sequential ingestion), and Supermemory sends no
  `document_date`. Disclosed as a paper limitation.

- **2026-09-02 — Graphiti live-smoke amendments (mechanical).** Four upstream
  problems in the frozen `graphiti-core` 0.29.3 + embedded Kuzu path, all
  availability, none capability: (1) `KuzuDriver` never initializes
  `_database` though `add_episode`/`search` read it — the adapter pins it to
  the group in use (the clone-per-database branch is a Neo4j multi-db concept
  inapplicable to one embedded file); (2) the Kuzu FTS extension is never
  installed/loaded and the FTS indices its search queries expect are never
  created — the adapter runs `INSTALL FTS` / `LOAD EXTENSION FTS` and the
  library's own `get_fulltext_indices(KUZU)` statements on the driver
  connection at first use; (3) `execute_query` drops None-valued parameters
  that the library's own save queries reference unconditionally
  ("Parameter invalid_at not found") — patched to bind NULL for referenced
  parameters and drop only unreferenced ones; (4) default Gemini models 404
  for this key (`gemini-3-flash-preview`, small `gemini-2.5-flash-lite` "no
  longer available to new users", embedder `text-embedding-001` not found) —
  pinned to the benchmark's market-internal `gemini-2.5-flash` and
  `gemini-embedding-001`, superseding the "graphiti defaults" line above.
  Measured: ~48 s per episode ingested (Gemini extraction); an org side
  (204 events) is ≈ 2.7 h of ingestion.

## Excluded / deferred

Letta (24.3k stars, rank 5 — below the top-4 line), typed-memory reference
implementation (registered, DEFERRED by the v1 freeze). Full candidate table
and exclusion reasons: `docs/vendor-survey.md`.
