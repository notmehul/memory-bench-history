# Vendor Survey — Memory System Candidates (Pre-Pilot)

**Date: 2026-08-15.** This enumeration was produced BEFORE any pilot run and
before any candidate was executed against the memory-bench SUT interface. It
is a complete candidate table, not a shortlist: every system considered is
listed with its status and exclusion reason where applicable, per the
dataset-plan requirement that inclusion decisions carry no silent selection.
No system in this document has been run, scored, or ranked. The benchmark
authors' own memory harness (Marshmallow) is not a candidate and does not
appear below.

> **Selection applied 2026-08-15 (v1 freeze):** top-4 dedicated-repo GitHub
> stars → Mem0 63.3k, Cognee 30.0k, Graphiti/Zep 29.9k, Supermemory 28.9k;
> next Letta 24.3k, Honcho 6.7k, Memobase 2.8k, LangMem 1.6k; LlamaIndex
> Memory not ranked (framework stars); Zep Cloud represented by Graphiti.
> Others: not run in v1 (budget).

## 1. Purpose

memory-bench evaluates memory systems for organizations of agents through a
fixed two-call interface: `ingest(principal, event)` — called once per
witnessing principal per event — and `run_task(principal, task) -> text`. The
task model behind every system is fixed by the benchmark; a memory system may
only supply context or tools to it. This document enumerates every market
candidate surfaced before the pilot, so that inclusion/exclusion is
prespecified rather than chosen post hoc.

## 2. Method

**Surfacing.** Candidates were surfaced from three sources: (a) the named
seed list in the dataset plan — Mem0, Zep, Letta, LangMem, Cognee; (b) web
search for "AI agent memory" open-source libraries and GA APIs, including the
`topoteretes/awesome-ai-memory` list; (c) systems that appear as comparison
points in recent memory benchmarks/papers (LoCoMo, LongMemEval, MemoryArena)
surfaced during search for those benchmarks. Search access date for all
queries: 2026-08-15.

**What was checked per candidate**, where available from public sources:
- License (OSS) or pricing model (hosted).
- Ingest + retrieve API shape (the concrete calls, e.g.
  `mem0.add(messages, user_id=...)` / `mem0.search(query, user_id=...)`).
- Multi-user / scoping / namespacing support — the mechanism (user_id,
  namespace, container tag, workspace/peer, dataset+ACL, etc.) that would
  back per-principal isolation, and whether it can also be pointed at one
  shared org-level store.
- Self-hostable vs. hosted-only.
- Last release/commit activity, as a freshness signal only (not a quality
  judgment).

**Citation discipline.** Every factual claim below carries a source URL,
accessed 2026-08-15. Several web searches returned indirect or
AI-summarized content rather than primary documentation; those cases are
flagged inline as "per [source], not independently verified against primary
docs." Where a search returned no usable result, that is stated rather than
guessed.

## 3. Candidate table

| System | Vendor/maintainer | Type | License / pricing | Availability (a) | Two-call adapter feasibility (b) | Per-principal isolation (c) | Status | Sources (accessed 2026-08-15) |
|---|---|---|---|---|---|---|---|---|
| **Mem0** | Mem0 (mem0ai) | OSS lib + hosted platform | Apache-2.0 (OSS core); hosted platform has separate commercial pricing | OSS pip package + self-hosted Docker server; hosted API (mem0.ai) also GA | `ingest`: `memory.add(event, user_id=principal)`. `run_task`: `memory.search(task, filters={"user_id": principal})` → feed hits as context to the fixed task model. | `user_id` (also `agent_id`/`run_id`) filter on add/search; can be widened to a shared org store by filtering on a constant tenant id instead. | INCLUDE | [mem0ai/mem0](https://github.com/mem0ai/mem0), [mem0ai/mem0 LLM.md](https://github.com/mem0ai/mem0/blob/main/LLM.md) |
| **Graphiti** | Zep (getzep) | OSS lib (Python) | Apache-2.0 | Self-hosted OSS library; requires a graph DB backend (e.g. Neo4j/FalkorDB) | `ingest`: `graphiti.add_episode(group_id=principal, episode_body=event)`. `run_task`: `graphiti.search(query=task, group_ids=[principal])` → feed edges/facts to the task model. | `group_id` parameter scopes episodes and search to a principal; a shared org store is a shared `group_id`. | INCLUDE | [getzep/zep (org repo, notes Graphiti is the maintained OSS project)](https://github.com/getzep/zep), [Zep OSS strategy announcement](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/) |
| **Zep Cloud** | Zep (getzep.com) | Hosted API (built on Graphiti) | Commercial; free tier + paid tiers, enterprise BYOC/BYOK available; no public price list found (contact sales) | Hosted GA API; BYOC self-hosted-in-customer-VPC option for enterprise | `ingest`: `zep_client.graph.add(user_id=principal, data=event)`. `run_task`: `zep_client.graph.search(user_id=principal, query=task)` / memory-get for session context → feed to task model. | `user_id`, `thread_id` scoping documented on the product site; org-wide graphs also supported. Community Edition (self-hosted, unmanaged) was discontinued April 2025 — only the hosted product and Graphiti remain actively maintained. | INCLUDE | [getzep.com](https://www.getzep.com/), [Zep OSS strategy announcement](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/) |
| **Letta (MemGPT)** | Letta AI | OSS framework + hosted cloud | Apache-2.0 (server/SDK) | Self-hosted App Server (Docker) or Letta Cloud ("Constellation") | `ingest`: create one persistent Letta agent per principal; feed event as a message (`client.agents.messages.create(agent_id, [event])`) so it lands in that agent's core/archival memory. `run_task`: send the task as a message to the same agent and read its reply. | One agent (with its own memory blocks + archival storage) per principal is the natural isolation unit; a shared org store means routing multiple principals' events into one shared agent or shared archival collection. | INCLUDE | [letta-ai/letta](https://github.com/letta-ai/letta) |
| **LangMem** | LangChain | OSS lib (Python) | MIT | pip package; storage backend pluggable (in-memory for dev, Postgres for production) — self-hosted | `ingest`: `create_manage_memory_tool(namespace=(principal,)).invoke({"content": event})`. `run_task`: `create_search_memory_tool(namespace=(principal,)).invoke({"query": task})` → feed results to task model. | Namespace tuple (e.g. `(principal,)`) passed to both tools; a shared org store is a shared namespace across principals. | INCLUDE | [langchain-ai/langmem](https://github.com/langchain-ai/langmem), [LangMem SDK launch post](https://www.langchain.com/blog/langmem-sdk-launch) |
| **Cognee** | Topoteretes | OSS platform (Python/TS SDKs, REST API) | Apache-2.0 | Self-hosted (pip / Docker); also offers a managed option | `ingest`: `cognee.add(event, dataset_name=principal)` then `cognee.cognify()` to build the graph. `run_task`: `cognee.search(task, dataset_name=principal)` → feed to task model. | Per-user datasets with an authorization/permissions layer (`resolve_authorized_user_dataset`); multi-tenant by design, and datasets can be shared to form one org store with per-user grants. | INCLUDE | [topoteretes/cognee](https://github.com/topoteretes/cognee), [Cognee multi-tenant announcement](https://www.cognee.ai/blog/cognee-news/product-announcement-user-management) |
| **Memobase** | memodb-io | OSS lib + server | Apache-2.0 | Self-hosted server (Docker) or cloud | `ingest`: add chat/event blob scoped to `user_id=principal` (profile update). `run_task`: fetch/search the user's profile+events for `principal` → feed to task model. | `user_id`-scoped profile is the isolation unit; shared org store not natively documented — would need a shared synthetic `user_id` or a wrapper layer. | INCLUDE | [memodb-io/memobase](https://github.com/memodb-io/memobase) |
| **MemoryOS** | BAI-LAB (Beijing Univ. of Posts and Telecom) | OSS research library + PyPI package + MCP server | Apache-2.0 | pip package (`memoryos-pro`... naming/maturity of "pro" vs free tiers not resolved from public docs), Docker, MCP server | `ingest`: `Memoryos(user_id=principal, assistant_id=org).add_memory(user_input=event)`. `run_task`: `.get_response(query=task)` or `.retrieve_memory()` → feed to task model. | `user_id` + `assistant_id` parameters; no evidence found of a documented shared-org-store mode distinct from per-user instances. | UNCLEAR — verify: exact package/license boundary implied by the `-pro` PyPI name, API stability (this is EMNLP 2025 research code with an added productized layer), and whether a shared-org configuration is supported before committing an adapter. | [BAI-LAB/MemoryOS](https://github.com/BAI-LAB/MemoryOS), [arXiv:2506.06326](https://arxiv.org/abs/2506.06326) |
| **A-MEM** | Rutgers/agiresearch (WujiangXu et al.) | Research code (NeurIPS 2025 paper) | MIT | Public GitHub repo, explicitly "designed to reproduce paper results," not a packaged library/server | Not sketched — see exclusion reason. | Not documented — no user/agent scoping mechanism found in the repo. | EXCLUDE (adapter not implementable without privileged effort) — the repository's own README states it is reproduction code, not intended for building agents, and points to a separate "official implementation" whose public availability/API was not confirmed. No stable ingest/retrieve API or multi-tenant isolation to adapt against without effectively building the memory system ourselves, which is out of scope for an adapter over an existing system. | [WujiangXu/A-mem](https://github.com/WujiangXu/A-mem) |
| **Supermemory** | Supermemory AI | OSS engine + hosted API | Core engine MIT-licensed; hosted usage-based pricing (free tier + $19/$100/$399 tiers, enterprise custom) | Self-hostable (stated "can be run fully locally") and hosted GA API | `ingest`: `client.add(event, containerTag=principal)`. `run_task`: `client.search(task, containerTag=principal)` → feed to task model. | `containerTag` (arbitrary string, e.g. principal id) isolates memory spaces; combining tags supports an org+principal hierarchy. | INCLUDE | [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory), [Supermemory pricing](https://supermemory.ai/pricing/), [Supermemory container tags docs](https://supermemory.ai/docs/concepts/container-tags) |
| **Honcho** | Plastic Labs | OSS server (FastAPI) + hosted API | AGPL-3.0 | Self-hosted (Docker/Postgres+pgvector) or managed at api.honcho.dev | `ingest`: `honcho.workspace(org).peer(principal).session(...).add_messages([event])`. `run_task`: query the peer's session context / `.chat(task)` → feed to task model. | Native two-tier model: `workspace` (org-level store) containing `peer`s (principals) in `session`s — matches the benchmark's "shared org store with per-principal access" requirement directly. | INCLUDE | [plastic-labs/honcho](https://github.com/plastic-labs/honcho) |
| **Motorhead** | Get Metal (getmetal) | OSS server (Rust) | Apache-2.0 | Self-hosted (Redis-backed) | `ingest`/`run_task` would map to `POST /sessions/:id/memory` and `POST /sessions/:id/retrieval`. | `session_id` path-scoped isolation. | EXCLUDE (unmaintained) — repository explicitly states "Support is no longer maintained for this project." Using an unmaintained memory server as protocol infrastructure risks undisclosed staleness/bugs the authors cannot get fixed. | [getmetal/motorhead](https://github.com/getmetal/motorhead) |
| **txtai** | NeuML | OSS embeddings/search library | Apache-2.0 | Self-hosted pip package | Not sketched — see exclusion reason. | Not a built-in concept; would be implemented manually via separate indexes/filters per principal. | EXCLUDE — txtai is a general-purpose embeddings/vector database and RAG pipeline toolkit, not an agent-memory system with built-in ingest/retrieve semantics or per-principal isolation. Adapting it would mean building a memory system on top of a search library rather than adapting an existing memory system, which is a different task than this survey is scoped to. | [txtintelligence/txtai](https://github.com/txtintelligence/txtai) |
| **Khoj** | Khoj AI | OSS self-hosted app + cloud | AGPL-3.0 | Self-hosted or cloud (app.khoj.dev) | Not sketched — see exclusion reason. | Not established from public docs; product surface is chat clients (web, Obsidian, Emacs, WhatsApp) rather than a documented headless multi-tenant ingest/retrieve API. | EXCLUDE — Khoj is a personal-assistant chat product built around its own end-user chat interfaces; public docs surfaced no clear standalone multi-user ingest+retrieve API suitable for a two-call adapter without privileged/undocumented access. | [khoj-ai/khoj](https://github.com/khoj-ai/khoj) |
| **LlamaIndex Memory** | LlamaIndex (run-llama) | OSS library module | MIT | Self-hosted pip package; pluggable backends (SQLite default, Postgres, vector stores) | `ingest`: `memory = Memory.from_defaults(session_id=principal); memory.put(event)`. `run_task`: `memory.get()` → feed retrieved context alongside `task` to the (external) task model. | `session_id` parameter scopes a `Memory` instance to one principal; a shared chat store keyed differently supports an org-wide store. | INCLUDE | [LlamaIndex Memory docs](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/), [LlamaIndex Memory API reference](https://developers.llamaindex.ai/python/framework-api-reference/memory/memory/) |
| **Mastra Memory** | Mastra AI | OSS framework module (TypeScript) | Apache-2.0 core (separate "Enterprise License" for `ee/`-directory code) | Self-hosted npm package | `ingest`: `memory.saveMessages({threadId: principal, resourceId: principal, messages: [event]})`. `run_task`: query the thread for context → feed to task model. | `resourceId` (principal/org) + `threadId` (conversation) is the documented scoping model. | UNCLEAR — verify: whether the `Memory` class can be driven directly (as sketched above) independent of a full Mastra `Agent`'s own generate/stream loop, since public docs describe it primarily as agent-internal infrastructure; also confirm no `ee/`-licensed code is required for the isolation features actually used. | [mastra-ai/mastra](https://github.com/mastra-ai/mastra), [Mastra memory docs](https://mastra.ai/docs/memory/overview), [Mastra threads-and-resources docs](https://mastra.ai/docs/memory/threads-and-resources) |
| **OpenAI memory (ChatGPT Memory / Assistants threads)** | OpenAI | Chat product feature / deprecated API | N/A | ChatGPT app feature; Assistants API (thread-based) deprecating Aug 26, 2026 | Not sketched — see exclusion reason. | N/A | EXCLUDE — per multiple sources, OpenAI's persistent "memory" is a ChatGPT app feature, not exposed through the API; the Assistants API's threads provide conversation state, not the kind of persistent, queryable, per-principal long-term memory the SUT interface needs, and it is being deprecated. Developers are directed to build a memory layer themselves on top of the (stateless) Responses API, which is not itself a candidate memory system. | [community.openai.com thread on persisting memory](https://community.openai.com/t/how-to-persist-user-context-or-memory-in-a-thread-in-assistants-api/1037146), [Assistants API deprecation note](https://learn.microsoft.com/en-za/answers/questions/5571874/openai-assistants-api-will-be-deprecated-in-august) |
| **Anthropic Claude memory tool** | Anthropic | API-level tool (beta) | N/A | GA-beta feature of the Claude API (`context-management-2025-06-27` beta header) | Not sketched — see exclusion reason. | Filesystem-style `/memories` directory, scoped however the calling application chooses. | EXCLUDE — the memory tool is a filesystem interface that Claude itself reads/writes to as part of its own tool-use loop; it is designed to be operated by a Claude model acting as the agent. memory-bench's pinned task model is gpt-5.4 (codex-cli), not Claude, so this tool cannot serve as an external memory layer supplying context to a different model's task loop without effectively reimplementing the tool-use harness around a non-Claude model — outside "implementable without privileged access." | [Claude memory tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) |

18 candidates enumerated (16 distinct products/projects; Zep is split into
its OSS core, Graphiti, and its hosted product, Zep Cloud, since they differ
on license/availability/pricing). 10 INCLUDE, 6 EXCLUDE, 2 UNCLEAR.

## 4. Right-of-reply plan

For every INCLUDE and UNCLEAR candidate, the plan is to send the frozen
adapter config and the resulting scores to the maintainer's public channel
below before publication, per the fairness protocol, and to log the date
sent and any response in `docs/standards-audit.md` or an equivalent ledger.

| System | Public contact channel |
|---|---|
| Mem0 | [github.com/mem0ai/mem0/issues](https://github.com/mem0ai/mem0/issues) |
| Graphiti | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) issues/discussions |
| Zep Cloud | [getzep.com](https://www.getzep.com/) contact/sales form; [blog.getzep.com](https://blog.getzep.com/) for public comment |
| Letta (MemGPT) | [github.com/letta-ai/letta/issues](https://github.com/letta-ai/letta) |
| LangMem | [github.com/langchain-ai/langmem/issues](https://github.com/langchain-ai/langmem) |
| Cognee | [github.com/topoteretes/cognee/issues](https://github.com/topoteretes/cognee) |
| Memobase | [github.com/memodb-io/memobase/issues](https://github.com/memodb-io/memobase) |
| MemoryOS | [github.com/BAI-LAB/MemoryOS/issues](https://github.com/BAI-LAB/MemoryOS) |
| Supermemory | [github.com/supermemoryai/supermemory/issues](https://github.com/supermemoryai/supermemory) |
| Honcho | [github.com/plastic-labs/honcho/issues](https://github.com/plastic-labs/honcho) |
| LlamaIndex Memory | [github.com/run-llama/llama_index/issues](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/) (repo: run-llama/llama_index) |
| Mastra Memory | [github.com/mastra-ai/mastra/issues](https://github.com/mastra-ai/mastra) |

Excluded candidates (A-MEM, Motorhead, txtai, Khoj, OpenAI memory, Anthropic
memory tool) are not owed right-of-reply under the fairness protocol since
they are not being run or scored, but the exclusion reasons above are public
in this document and each vendor's repo/docs URL is cited so the reasoning
is checkable and disputable by anyone, including the vendor.

## 5. Notes and limitations

- **Time-sensitivity.** Pricing pages, license terms, and release/maturity
  status (especially for Zep, Supermemory, and MemoryOS, all of which
  changed structure within the last 18 months) can change between this
  survey (2026-08-15) and adapter implementation time. Re-verify license,
  pricing, and API stability immediately before writing each adapter, not
  from this document alone.
- **Search reliability.** Several WebSearch results returned AI-generated
  summaries of primary sources rather than primary source text; where a
  claim above could not be cross-checked against a fetched primary page
  (repo README, docs page), it is flagged in the table cell itself rather
  than presented as fully verified. No claim in this document was guessed
  when a search returned nothing; in every case a search did return results.
- **UNCLEAR items require action before pilot.** MemoryOS and Mastra Memory
  need direct verification (installing the package / reading source, not
  just marketing docs) before either is promoted to INCLUDE or moved to
  EXCLUDE.
- **No ranking, no run.** No candidate in this table has been executed
  against the memory-bench SUT interface, scored, or benchmarked by the
  authors as of this document's date. No expectation of relative performance
  is stated or implied for any product. Order in the table is the order
  candidates were surfaced during research, not a ranking.
- **Scope boundary.** This survey does not evaluate whether the *task
  model* (gpt-5.4, codex-cli) can use each memory system's tool-calling
  conventions well — only whether an adapter to the two-call SUT interface
  is implementable without privileged access. That is a separate,
  later question.
