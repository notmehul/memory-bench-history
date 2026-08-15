"""Naive RAG baseline (#3): lexical retriever ranking, top-k chronological
context, visibility via the shared/silo store, embedding seam."""

from membench.adapters import MockWorker
from membench.rag import EmbeddingRetriever, LexicalRetriever, NaiveRAGAdapter


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
