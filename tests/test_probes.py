"""Probe constructor (Phase 3): expansion, hygiene lint, pattern cross-checks."""

import json
from pathlib import Path

import pytest
from conftest import require_ledger  # noqa: E402

from membench.belief import belief_hist, belief_state
from membench.ledger import load_event_index, load_ledger
from membench.probes import (
    MIN_INSTANCES,
    SERIES_METRICS,
    build_requests,
    cluster_forbidden_tokens,
    discriminative_tokens,
    expand_cluster,
    validate_authored_cluster,
)

ORG_DIR = Path(__file__).resolve().parents[1] / "datasets" / "dev" / "org-00001"


@pytest.fixture(scope="module")
def org():
    return json.loads(require_ledger().read_text())


@pytest.fixture(scope="module")
def plan_doc():
    return json.loads((ORG_DIR / "plan.json").read_text())


@pytest.fixture(scope="module")
def loaded(org):
    return load_ledger(org), load_event_index(org)


def test_every_cluster_expands_to_min_instances(loaded, plan_doc):
    ledger, index = loaded
    for plan in plan_doc["probe_plans"]:
        insts = expand_cluster(ledger, index, plan)
        assert len(insts) >= MIN_INSTANCES
        assert len({i.probe_id for i in insts}) == len(insts)


def test_expansion_is_deterministic(loaded, plan_doc):
    ledger, index = loaded
    for plan in plan_doc["probe_plans"][:10]:
        a = expand_cluster(ledger, index, plan)
        b = expand_cluster(ledger, index, plan)
        assert a == b


def test_series_clusters_keep_one_principal(loaded, plan_doc):
    ledger, index = loaded
    for plan in plan_doc["probe_plans"]:
        if plan["metric"] in SERIES_METRICS:
            insts = expand_cluster(ledger, index, plan)
            assert {i.principal for i in insts} == {plan["principal"]}


def test_expanded_instances_are_oracle_valid(loaded, plan_doc):
    ledger, index = loaded
    for plan in plan_doc["probe_plans"]:
        for inst in expand_cluster(ledger, index, plan):
            t = index.index_of(inst.inject_after_event)
            b = belief_state(ledger, index, inst.principal, t)
            hist = belief_hist(ledger, index, inst.principal, t)
            pool = hist if plan["kind"] == "historical" else b
            assert all(fid in pool for fid in plan["targets"]), inst.probe_id
            assert all(fid in hist for fid in plan["must_not_use"]), inst.probe_id


def test_discriminative_tokens_are_the_answer_diff():
    toks = discriminative_tokens(
        "Reviews run weekly with exec staff.",
        "Reviews run monthly with exec staff.",
    )
    assert toks == {"weekly", "monthly"}


def _request(org, plan_doc, cluster_id):
    return next(
        r for r in build_requests(org, plan_doc) if r["cluster_id"] == cluster_id
    )


def _valid_authored(req):
    target = req["targets"][0]
    return {
        "cluster_id": req["cluster_id"],
        "task": (
            "Draft a short update for the next sync covering how the group "
            "handles this area of work going forward, so newcomers can follow "
            "the current approach without asking around."
        ),
        "modality": "document",
        "assertions": [{
            "id": "asrt-1", "kind": "fact_applied", "fact_id": target["fact_id"],
            "checker": "semantic",
            "criterion": "The update tells engineers to use hyphenated "
                         "lowercase resource names in API paths.",
            "weight": 1.0,
        }],
        "counterfactual_assertions": [{
            "id": "casrt-1", "kind": "fact_applied", "fact_id": target["fact_id"],
            "checker": "semantic",
            "criterion": "The update tells engineers to use camelCase "
                         "resource identifiers in API paths.",
            "weight": 1.0,
        }],
    }


def test_valid_authored_cluster_passes(org, plan_doc):
    req = _request(org, plan_doc, "P-0001")
    assert validate_authored_cluster(req, _valid_authored(req)) == []


def test_task_leaking_answer_token_fails(org, plan_doc):
    req = _request(org, plan_doc, "P-0001")
    authored = _valid_authored(req)
    authored["task"] += " Note that " + req["forbidden_tokens"][0] + " applies."
    assert any("leaks answer tokens" in e for e in
               validate_authored_cluster(req, authored))


def test_pattern_matching_both_sides_fails(org, plan_doc):
    req = _request(org, plan_doc, "P-0001")
    authored = _valid_authored(req)
    # A fact_absent detector whose pattern hits both twin variants is not
    # discriminative -> rejected.
    shared = set(req["targets"][0]["canonical"].lower().split()) & set(
        req["targets"][0]["counterfactual"].lower().split()
    )
    authored["assertions"] = [{
        "id": "asrt-1", "kind": "fact_absent",
        "fact_id": req["targets"][0]["fact_id"], "checker": "pattern",
        "criterion": sorted(shared, key=len)[-1].strip(".,"), "weight": 1.0,
    }]
    errs = validate_authored_cluster(req, authored)
    assert any("also matches" in e for e in errs)


def test_pattern_reserved_for_fact_absent(org, plan_doc):
    req = _request(org, plan_doc, "P-0001")
    authored = _valid_authored(req)
    authored["assertions"][0]["checker"] = "pattern"
    authored["assertions"][0]["criterion"] = "kebab[- ]?case"
    errs = validate_authored_cluster(req, authored)
    assert any("reserved for fact_absent" in e for e in errs)


def test_forbidden_tokens_cover_both_directions(org, plan_doc):
    req = _request(org, plan_doc, "P-0003")
    banned = set(cluster_forbidden_tokens(req["targets"] + req["must_not_use"]))
    for f in req["targets"]:
        if f["counterfactual"]:
            assert discriminative_tokens(f["canonical"], f["counterfactual"]) <= banned
