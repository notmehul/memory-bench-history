"""Naive RAG baseline (#3): lexical retriever ranking, top-k chronological
context, visibility via the shared/silo store, embedding seam, pinned
Gemini embedder (mocked client), shared retrieval prompt."""

from types import SimpleNamespace

from membench.adapters import MockWorker
from membench.rag import (
    EMBEDDING_MODEL,
    EmbeddingRetriever,
    GeminiEmbedder,
    LexicalRetriever,
    NaiveRAGAdapter,
    retrieval_prompt,
)


def _ev(i, content, surface="team:eng/standup"):
    return {"event_id": f"E-{i:04d}", "sim_time": f"2026-03-{i:02d}T09:00:00Z",
            "channel": "meeting", "surface": surface,
            "participants": ["persona:alice"], "content": content}


def test_lexical_retriever_prefers_query_terms_and_rare_terms():
    r = LexicalRetriever()
    docs = ["deploy freeze runs Thursday to Monday", "lunch menu and parking",
            "deploy window Tuesday", "the the the"]
    order = r.rank("when is the deploy freeze", docs)
    assert order[0] == 0 and order[1] == 2
    assert r.rank("", docs) == [0, 1, 2, 3]


def test_naive_rag_top_k_chronological_and_visibility():
    w = MockWorker()
    a = NaiveRAGAdapter(w, k=2)
    for i, c in enumerate(["parking update", "deploy freeze Thursday", "deploy window Tuesday",
                           "snack budget"], start=1):
        a.ingest("persona:alice", _ev(i, c))
    a.ingest("persona:bob", _ev(9, "bob-only deploy note"))
    a.run_task("persona:alice", "Task: write the deploy freeze note")
    p = w.calls[-1]
    assert "Retrieved workspace history" in p
    assert "deploy freeze Thursday" in p and "deploy window Tuesday" in p
    assert "parking" not in p and "snack" not in p
    assert p.index("deploy freeze Thursday") < p.index("deploy window Tuesday")  # oldest first
    assert "bob-only" not in p                                                  # not witnessed
    assert a.counters["retrieved"] == 2 and a.counters["last_context_chars"] > 0
    a.run_task("persona:cara", "Task: anything")
    assert "Retrieved" not in w.calls[-1] and a.counters["last_context_chars"] == 0


def test_embedding_retriever_seam_ranks_by_cosine():
    def embed(texts):
        return [[1.0, 0.0] if "deploy" in t else [0.0, 1.0] for t in texts]
    r = EmbeddingRetriever(embed, model_name="test-2d")
    assert r.rank("deploy", ["lunch", "deploy freeze", "menu"])[0] == 1
    a = NaiveRAGAdapter(MockWorker(), retriever=r, k=1)
    a.ingest("persona:alice", _ev(1, "lunch"))
    a.ingest("persona:alice", _ev(2, "deploy freeze"))
    a.run_task("persona:alice", "deploy?")
    assert "deploy freeze" in a.worker.calls[-1] and "lunch" not in a.worker.calls[-1]


def test_embedding_retriever_embeds_each_chunk_once():
    seen = []

    def embed(texts):
        seen.append(list(texts))
        return [[1.0, 0.0] if "deploy" in t else [0.0, 1.0] for t in texts]
    r = EmbeddingRetriever(embed)
    docs = ["lunch", "deploy freeze"]
    r.rank("deploy", docs)
    r.rank("deploy again", docs + ["deploy window"])
    assert seen == [docs, ["deploy"], ["deploy window"], ["deploy again"]]
    assert r.embed_calls == 4


def test_retrieval_prompt_lists_items_in_order_then_task():
    p = retrieval_prompt(["m1-first", "m2-second"], "Task: do it")
    assert p.startswith("Retrieved workspace history")
    assert p.index("m1-first") < p.index("m2-second") < p.index("Task: do it")
    assert p.endswith("Task: do it")
    assert retrieval_prompt([], "Task: bare") == "Task: bare"


class _FakeGenaiClient:
    def __init__(self):
        self.calls = []
        self.models = self

    def embed_content(self, model, contents):
        self.calls.append((model, list(contents)))
        return SimpleNamespace(embeddings=[
            SimpleNamespace(values=[float(len(c)), 1.0]) for c in contents])


def test_gemini_embedder_batches_with_pinned_model_no_network():
    fake = _FakeGenaiClient()
    e = GeminiEmbedder(batch_size=2)
    e._client = fake                          # monkeypatched client: no SDK, no key
    vecs = e.embed(["a", "bb", "ccc"])
    assert vecs == [[1.0, 1.0], [2.0, 1.0], [3.0, 1.0]]
    assert [m for m, _ in fake.calls] == [EMBEDDING_MODEL] * 2
    assert [c for _, c in fake.calls] == [["a", "bb"], ["ccc"]]
    assert e.counters == {"calls": 2, "texts": 3}
    assert EMBEDDING_MODEL == "gemini-embedding-001"


def test_pilot_rag_registration_builds_without_network(monkeypatch):
    from membench import pilot
    a = pilot.build_adapter("rag", MockWorker(), silo=True)
    assert isinstance(a, NaiveRAGAdapter) and a.shared is False
    assert isinstance(a.retriever, EmbeddingRetriever)
    assert a.retriever.model_name == EMBEDDING_MODEL
    # inject a fake client into the pinned embedder and run end to end
    embedder = a.retriever.embed.__self__
    assert isinstance(embedder, GeminiEmbedder)
    embedder._client = _FakeGenaiClient()
    a.ingest("persona:alice", _ev(1, "short"))
    a.ingest("persona:alice", _ev(2, "a much longer deploy freeze note here"))
    a.run_task("persona:alice", "Task: a long query string to match the longer chunk")
    assert "deploy freeze" in a.worker.calls[-1]
    assert a.counters["embed_calls"] == 2
