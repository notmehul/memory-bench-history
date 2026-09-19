"""Every headline number in the paper must trace to a committed artifact.

The preprint checklist requires zero hand-typed values in the results core.
These tests recompute each number from the evidence it cites and assert the
rendered string is present in `paper/memory-bench.tex`, so a number can no longer drift
away from the artifact it came from — in either direction. A number that
legitimately changes fails here until the artifact and the prose agree again.

Scope is deliberately the numbers the paper asserts, not everything measured.
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import pytest
from conftest import DATASET, HISTORY, HOLDOUT, SEALED, require  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from membench.g3 import load_valid_instances  # noqa: E402

SEEDS = ("org-00001", "org-00002", "org-00003")


def _json(rel: str, why: str):
    return json.loads(require(rel, why).read_text())


def _agreement() -> dict:
    return _json("datasets/dev/calibration/judge-agreement.json", SEALED)


def _rater_key() -> dict:
    return _json("datasets/dev/calibration/packet-key.json", SEALED)


def _ratings() -> dict:
    return _json("datasets/dev/calibration/ratings-M.json", SEALED)


def _probes(org: str) -> Path:
    return require(f"datasets/dev/{org}/probes.jsonl", DATASET if org in SEEDS else HOLDOUT)


@pytest.fixture(scope="module")
def prose() -> str:
    """The published paper as a reader sees it, whitespace collapsed.

    The checks below were first written against a markdown working copy, so
    the LaTeX is rendered into the same conventions: \\code{x} becomes `x`,
    \\textbf{x} becomes **x**, 5{,}398 becomes 5,398, \\% becomes %. The .tex
    is the artifact that ships, so it is the one the numbers are held to.
    """
    return _plain((ROOT / "paper" / "memory-bench.tex").read_text())


@pytest.fixture(scope="module")
def tex() -> str:
    """The LaTeX submission artifact, whitespace collapsed, same as the draft."""
    return " ".join((ROOT / "paper" / "memory-bench.tex").read_text().split())


@pytest.fixture(scope="module")
def tex_raw() -> str:
    return (ROOT / "paper" / "memory-bench.tex").read_text()


def _plain(tex: str) -> str:
    """LaTeX prose to plain text with markdown-style emphasis. Only what the
    paper uses; this is not a general converter."""
    t = re.sub(r"(?<!\\)%.*$", "", tex, flags=re.M)
    t = t.replace("{,}", ",").replace("\\%", "%").replace("\\_", "_")
    t = t.replace("\\&", "&").replace("~", " ").replace("---", "—").replace("--", "–")
    t = t.replace("``", '"').replace("\'\'", '"').replace("\\S", "§")
    for macro, sym in (("kappa", "κ"), ("geq", "≥"), ("leq", "≤"), ("times", "×"),
                       ("rightarrow", "→"), ("pm", "±"), ("approx", "≈")):
        t = re.sub(rf"\\{macro}(?![A-Za-z])", sym, t)
    for _ in range(3):  # nested \textbf{\code{..}}
        t = re.sub(r"\\code\{([^{}]*)\}", r"`\1`", t)
        t = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", t)
        t = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", t)
        t = re.sub(r"\\textsc\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\(?:cite|ref|label)\{[^{}]*\}", "", t)
    t = t.replace("$", "")
    return " ".join(t.split())


def _wilson(successes: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval. Recomputed here rather than trusted from the
    artifact, so a scorer bug and a prose typo cannot agree with each other."""
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


@pytest.fixture(scope="module")
def g3() -> dict[str, dict]:
    return {org: json.loads((ROOT / "datasets/dev" / org / "g3-report.json").read_text())
            for org in SEEDS}


def test_valid_instance_total(prose: str, g3: dict):
    total = sum(r["n_valid_instances"] for r in g3.values())
    assert total == 371
    assert f"{total} valid paired" in prose


def test_per_seed_counts(prose: str, g3: dict):
    per = [g3[o]["n_valid_instances"] for o in SEEDS]
    assert per == [125, 131, 115]
    assert "/".join(str(n) for n in per) in prose


def test_cluster_survival(prose: str, g3: dict):
    survival = [f'{g3[o]["n_survivors"]}/{g3[o]["n_clusters"]}' for o in SEEDS]
    assert survival == ["46/54", "46/54", "40/54"]
    assert ", ".join(survival) in prose


def test_archetype_breakdown(prose: str):
    counts: Counter = Counter()
    for org in SEEDS:
        d = ROOT / "datasets/dev" / org
        valid = load_valid_instances(d)
        arch = {json.loads(x)["probe_id"]: json.loads(x)["archetype"]
                for x in _probes(org).read_text().splitlines() if x.strip()}
        counts.update(arch[pid] for pid in valid)
    assert sum(counts.values()) == 371
    claim = " ".join(f"{a} {counts[a]}," for a in ("A1", "A2", "A4", "A7")).rstrip(",")
    assert claim in prose, f"expected {claim!r} in the draft"


def test_gate_failures_are_reported_not_repaired(prose: str, g3: dict):
    """All three instance gates FAIL; only seed 3's cluster gate FAILs."""
    assert [g3[o]["gate_g3_instances"] for o in SEEDS] == [False, False, False]
    assert [g3[o]["gate_g3_clusters"] for o in SEEDS] == [True, True, False]
    low = prose.lower()
    assert "all three instance gates fail" in low
    assert "seed 3's cluster gate also fails" in low


def test_floor_run_numbers(prose: str):
    report = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    rungs = report["by_rung"]
    assert round(rungs["1"]["pair_credit_mean"], 3) == 0.022
    assert round(rungs["2"]["pair_credit_mean"], 3) == 0.118
    assert rungs["3"]["pair_credit_mean"] == 0.0
    assert [rungs[r]["n_instances"] for r in ("1", "2", "3")] == [92, 17, 16]
    for fragment in ("rung 1 pair credit 0.022", "rung 2 0.118", "rung 3 0.000",
                     "n=92", "n=17", "n=16"):
        assert fragment in prose, f"missing {fragment!r}"


def test_floor_is_reported_as_counts_and_wilson_bounds(prose: str, tex: str):
    """Rewritten 2026-09-17. This used to assert the Wald interval and the claim
    that every rung was statistically indistinguishable from zero. The Wald
    interval is invalid at these counts and degenerate at rung 3's zero
    successes, so the claim it licensed is retired; what the floor supports is a
    magnitude, and that is what is guarded now."""
    report = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    rungs = report["by_rung"]

    expected = {"1": (2, 92, 1.8019, 51.06), "2": (2, 17, 1.8814, 9.04),
                "3": (0, 16, 1.0, 16.0)}
    for rung, (successes, n, deff, n_eff) in expected.items():
        s = rungs[rung]
        assert (s["successes"], s["n_instances"]) == (successes, n), rung
        assert s["deff"] == deff and s["n_eff"] == n_eff, rung
        # the scorer's interval, recomputed from the counts it reports
        lo, hi = _wilson(s["pair_credit_mean"] * n_eff, n_eff)
        assert [round(lo, 3), round(hi, 3)] == [round(x, 3) for x in s["ci95_wilson"]], rung

    # only the zero-success rung is consistent with exactly zero
    assert [r for r in rungs if rungs[r]["ci95_wilson"][0] == 0.0] == ["3"]

    for fragment in ("2 successes of 92, 95% Wilson interval [0.004, 0.106]",
                     "rung 2 0.118**, 2 of 17, [0.022, 0.441]",
                     "rung 3 0.000**, 0 of 16, [0.000, 0.194]",
                     "Only rung 3, with no successes at all, is consistent with "
                     "exactly zero",
                     "The interval method changed on 2026-09-17"):
        assert fragment in prose, f"missing {fragment!r}"

    # the magnitude claim that replaced the null test, in both formats
    upper = "4 of 125 instances, with 95% upper bounds of 10.6%, 44.1% and 19.4%"
    assert upper in prose
    assert upper.replace("%", "\\%") in tex


def test_the_retired_floor_claim_is_gone_everywhere(prose: str, tex: str):
    """The Wald interval licensed two sentences the Wilson interval does not."""
    for banned in ("indistinguishable from zero", "every interval includes zero",
                   "near zero on every rung"):
        assert banned not in tex, f"memory-bench.tex still carries {banned!r}"
    release = require("paper/release-copy.md", HISTORY).read_text()
    assert not any(b in release for b in ("indistinguishable from zero",
                                          "every interval includes zero",
                                          "near zero on every rung"))
    # and the release copy's abstract still carries the replacement claim
    flat = " ".join(release.split())
    assert ("A memoryless worker earns pair credit on 4 of 125 instances, with 95% "
            "upper bounds of 10.6%, 44.1% and 19.4% by capability rung.") in flat


def test_floor_figure_draws_the_asymmetric_wilson_bars(tex_raw: str):
    """A Wilson interval is not symmetric about the point estimate, so the
    figure has to carry an explicit plus and minus per point."""
    rungs = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json"
         ).read_text())["by_rung"]
    plotted = {"1": 3, "2": 2, "3": 1}      # rung -> y coordinate in the figure
    for rung, y in plotted.items():
        s = rungs[rung]
        mean = round(s["pair_credit_mean"], 3)
        lo, hi = s["ci95_wilson"]
        coord = (f"({mean:.3f},{y}) += ({hi - mean:.3f},0) -= ({mean - lo:.3f},0)")
        assert coord in tex_raw, f"rung {rung}: expected {coord!r}"
    assert "+- (0.217,0)" not in tex_raw, "the symmetric Wald bars are still drawn"


def test_g4_judge_human_agreement(prose: str):
    """G4 FAILED. The paper must say so, with the measured numbers."""
    r = _agreement()
    assert r["n"] == 150
    assert round(r["raw_agreement"], 3) == 0.813
    assert round(r["kappa"], 3) == 0.537
    assert r["gate_g4_overall"] is False, "gate flipped: update the paper, not this test"
    assert len(r["criteria_below_threshold"]) == 28
    per = r["per_kind"]
    assert round(per["fact_absent"]["kappa"], 3) == 0.166
    for fragment in ("0.537", "0.813", "0.166", "κ ≥ 0.75"):
        assert fragment in prose, f"missing {fragment!r}"


def test_g4_kappa_confidence_intervals(prose: str, tex: str):
    """Added 2026-09-17 with the bootstrap. Post-hoc, and the paper says so."""
    r = _agreement()
    boot = r["kappa_bootstrap"]
    assert boot["replicates"] == 10000
    assert boot["n_clusters"] == 89, "the bootstrap resamples clusters, not items"
    assert boot["degenerate_replicates"] == 0
    assert boot["seed"] == 20260917

    def rendered(block) -> str:
        lo, hi = block["kappa_bootstrap"]["ci95"]
        return f"[{lo:.3f}, {hi:.3f}]"

    assert rendered(r) == "[0.370, 0.688]"
    for body in (prose, tex):
        assert rendered(r) in body
        for kind in ("fact_absent", "fact_applied", "scope_correct"):
            assert rendered(r["per_kind"][kind]) in body, kind

    # (a) the upper bound is below the gate, so the FAIL is not a point estimate
    assert boot["ci95"][1] < 0.75
    assert "The upper bound of the overall interval is 0.688, below the gate" in prose
    # and it is labelled post-hoc, because the gate was prespecified on the point
    low = prose.lower()
    assert "post-hoc and were never prespecified" in low
    # (b) the per-kind intervals overlap, and must not be read as more than that
    kinds = [r["per_kind"][k]["kappa_bootstrap"]["ci95"]
             for k in ("fact_absent", "fact_applied", "scope_correct")]
    assert max(lo for lo, _ in kinds) < min(hi for _, hi in kinds), \
        "the per-kind intervals no longer overlap; rewrite 4.4 before relaxing this"
    assert ("establish nothing about whether κ differs by criterion kind" in prose)


def test_g4_failure_is_not_softened(prose: str):
    """A failed gate is reported as failed, in the abstract and the disclosures.

    Anchors rewritten 2026-09-15 with the abstract. The old ones keyed on the
    abstract's boldface, which the replacement abstract does not carry; these
    key on the words instead, in both the abstract and the 4.4 table, so the
    guard now covers two places rather than one.
    """
    low = prose.lower()
    assert "fails our prespecified gate" in low, "the abstract must name the failure"
    assert "gate κ ≥ 0.75: fail" in low, "4.4 must table it as a FAIL"
    assert "g4 failed" in low
    # 2026-09-15: the count moved to disclosure 9, which spells it out.
    assert "twenty-eight criteria fall below" in low


def test_g4_symmetry_is_reported_as_a_cancellation(prose: str):
    """The 14/14 split hides two opposite kind-specific biases. An earlier draft
    read it as unbiased noise; that claim would not survive a reviewer who
    computed the marginals, so the corrected reading is pinned here."""
    key = _rater_key()
    gold = _ratings()

    def jsonl(p):
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    def last(rows):
        out = {}
        for r in rows:
            out[r["run_id"]] = r
        return out

    cache, cells = {}, Counter()
    for pid, ref in key.items():
        org = ref["org"]
        if org not in cache:
            d = ROOT / "datasets/dev/screening" / org
            cache[org] = (last(jsonl(d / "runs.jsonl")),
                          last(jsonl(d / "judgements.jsonl")))
        runs, judged = cache[org]
        run = runs[ref["run_id"]]
        a = next(x for x in run["assertions"] + (run.get("cf_assertions") or [])
                 if x["id"] == ref["assertion_id"])
        j = bool(judged[ref["run_id"]]["verdicts"][ref["assertion_id"]])
        cells[(a["kind"], gold[pid], j)] += 1

    # absence criteria: every judge error is an over-accept, none the other way
    assert cells[("fact_absent", False, True)] == 8
    assert cells[("fact_absent", True, False)] == 0
    # scope criteria: every judge error is an under-accept
    assert cells[("scope_correct", True, False)] == 7
    assert cells[("scope_correct", False, True)] == 0
    # and they cancel in aggregate
    over = sum(v for (k, h, j), v in cells.items() if not h and j)
    under = sum(v for (k, h, j), v in cells.items() if h and not j)
    assert over == under == 14

    low = prose.lower()
    assert "cancellation" in low, "the symmetry must not be reported as unbiased noise"
    assert "base-rate artifact" in low, "the fact_absent kappa needs its caveat"
    assert "1 of 44" in low


def test_g4_ratings_match_the_raw_submission(prose: str):
    """The committed labels are the ones the rater actually submitted."""
    packet = json.loads(
        (ROOT / "datasets/dev/calibration/rater-packet.json").read_text())
    ratings = _ratings()
    assert list(ratings) == [p["id"] for p in packet]
    assert all(isinstance(v, bool) for v in ratings.values())
    assert sum(ratings.values()) == 108
    assert (ROOT / "datasets/dev/calibration"
            / "rater-M-filled-2026-09-14.xlsx").is_file()


def _g4_records():
    """(human, judge, kind, side) for each of the 150 calibration pairs."""
    key = _rater_key()
    gold = _ratings()

    def jsonl(p):
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    cache, out = {}, []
    for pid, ref in key.items():
        org = ref["org"]
        if org not in cache:
            d = ROOT / "datasets/dev/screening" / org
            runs = {r["run_id"]: r for r in jsonl(d / "runs.jsonl")}
            judged = {r["run_id"]: r for r in jsonl(d / "judgements.jsonl")}
            cache[org] = (runs, judged)
        runs, judged = cache[org]
        run = runs[ref["run_id"]]
        a = next(x for x in run["assertions"] + (run.get("cf_assertions") or [])
                 if x["id"] == ref["assertion_id"])
        out.append((gold[pid],
                    bool(judged[ref["run_id"]]["verdicts"][ref["assertion_id"]]),
                    a["kind"],
                    "twin" if ref["assertion_id"].startswith("casrt") else "base"))
    return out


def test_decoy_audit_never_exercised_an_absence_criterion(prose: str):
    """The cheap judge check could not have caught the defect the human one found."""
    audit = json.loads(
        (ROOT / "datasets/dev/screening/judge-decoys/audit.json").read_text())
    # The decoys were built on seed 1. Probe ids repeat across orgs, so the
    # kinds must come from seed 1 alone: resolved over all five orgs, later
    # orgs overwrote earlier ones and the count matched only by coincidence.
    kinds: Counter = Counter()
    for org in ("org-00001",):
        for line in _probes(org).read_text().splitlines():
            if not line.strip():
                continue
            pr = json.loads(line)
            cf = pr.get("counterfactual_probe") or {}
            pool = (pr.get("assertions") or []) + (
                cf.get("assertions") if isinstance(cf, dict) else [] or [])
            for a in pool:
                kinds[(pr["probe_id"], a["id"])] = a.get("kind")
    seen = Counter(kinds.get((r["probe_id"], r["assertion_id"])) for r in audit["rows"])
    assert seen["fact_applied"] == 30
    assert seen["scope_correct"] == 11
    assert seen["fact_absent"] == 0, "a decoy DID cover an absence criterion; rewrite 4.4"
    # Anchored on 4.4 rather than the abstract, 2026-09-15: the replacement
    # abstract states the cancellation and leaves the mechanism to 4.4.
    assert "and none were `fact_absent`" in prose
    assert "structurally incapable of detecting a failure on absence criteria" \
        in prose


def test_over_accepts_concentrate_on_the_counterfactual_side(prose: str):
    recs = _g4_records()
    over = Counter(side for h, j, _, side in recs if not h and j)
    under = Counter(side for h, j, _, side in recs if h and not j)
    assert (over["twin"], over["base"]) == (11, 3)
    assert (under["twin"], under["base"]) == (7, 7)
    # Same move, 2026-09-15: 4.4 carries the split, the abstract carries the
    # claim it supports.
    assert "11 fall on twin-side criteria against 3 on base-side" in prose
    assert "counterfactual side" in prose


def test_absence_criterion_exposure_across_the_valid_set(prose: str):
    exposed = total = 0
    for org in SEEDS:
        d = ROOT / "datasets/dev" / org
        valid = set(load_valid_instances(d))
        for line in _probes(org).read_text().splitlines():
            if not line.strip():
                continue
            pr = json.loads(line)
            if pr["probe_id"] not in valid:
                continue
            total += 1
            cf = pr.get("counterfactual_probe") or {}
            pool = (pr.get("assertions") or []) + (
                cf.get("assertions") if isinstance(cf, dict) else [] or [])
            if any(a.get("kind") == "fact_absent" for a in pool):
                exposed += 1
    assert (total, exposed) == (371, 218)
    assert f"{exposed} of the {total}" in prose
    assert "58.8%" in prose


def test_no_side_is_scored_on_absence_criteria_alone(prose: str):
    """Containment: this is what stops judge leniency reaching the floor result."""
    sides_absence_only = instances_absence_only = total = 0
    for org in SEEDS:
        d = ROOT / "datasets/dev" / org
        valid = set(load_valid_instances(d))
        for line in _probes(org).read_text().splitlines():
            if not line.strip():
                continue
            pr = json.loads(line)
            if pr["probe_id"] not in valid:
                continue
            total += 1
            cf = pr.get("counterfactual_probe") or {}
            base = [a.get("kind") for a in (pr.get("assertions") or [])]
            twin = [a.get("kind") for a in (cf.get("assertions") or [])
                    ] if isinstance(cf, dict) else []
            for kinds in (base, twin):
                if kinds and set(kinds) == {"fact_absent"}:
                    sides_absence_only += 1
            allk = set(base) | set(twin)
            if allk and allk == {"fact_absent"}:
                instances_absence_only += 1
    assert total == 371
    assert instances_absence_only == 0
    assert sides_absence_only == 0, "a side is absence-only; the containment claim breaks"
    assert "no side of any instance is scored on absence criteria alone" in prose.lower()


def test_floor_pair_credit_instance_count(prose: str):
    """The empirical half of the containment argument."""
    rep = json.loads(
        (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1/report.json").read_text())
    insts = rep["instances"]
    vals = list(insts.values()) if isinstance(insts, dict) else insts
    credited = sum(1 for i in vals if isinstance(i, dict) and i.get("pair_credit"))
    assert (len(vals), credited) == (125, 4)
    assert "4 of 125" in prose


def test_repairing_the_absence_defect_still_fails_the_gate(prose: str):
    """Assumption-free counterfactual: flip verdicts we already have and recompute."""
    def kappa(rs):
        n = len(rs)
        po = sum(h == j for h, j, _ in rs) / n
        pa = sum(h for h, _, _ in rs) / n
        pb = sum(j for _, j, _ in rs) / n
        pe = pa * pb + (1 - pa) * (1 - pb)
        return po, (po - pe) / (1 - pe)

    recs = [[h, j, k] for h, j, k, _ in _g4_records()]
    po, k = kappa(recs)
    assert (round(po, 3), round(k, 3)) == (0.813, 0.537)

    fixed = [[h, False if (kind == "fact_absent" and not h and j) else j, kind]
             for h, j, kind in recs]
    po2, k2 = kappa(fixed)
    assert (round(po2, 3), round(k2, 3)) == (0.867, 0.688)
    assert k2 < 0.75, "repairing the absence defect now passes; rewrite 4.4"

    both = [[h, True if (kind == "scope_correct" and h and not j) else j, kind]
            for h, j, kind in fixed]
    po3, k3 = kappa(both)
    assert (round(po3, 3), round(k3, 3)) == (0.913, 0.787)

    low = prose.lower()
    assert "0.688" in low
    assert "still fails the gate" in low


def test_committed_verdict_count_under_rubric_v2(prose: str):
    """The re-judge cost quoted in 4.4, deduplicated by run_id as the scorer reads it."""
    def jsonl(p):
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    require("datasets/dev/screening/org-00004", HOLDOUT)
    total = 0
    for d in sorted((ROOT / "datasets/dev/screening").glob("org-*")):
        f = d / "judgements.jsonl"
        if f.is_file():
            rows = {r["run_id"]: r for r in jsonl(f)}
            total += sum(len(r.get("verdicts") or {}) for r in rows.values())
    for f in (ROOT / "datasets/dev/pilot/nomemory/seed-1/score-k1").glob("*judgements*.jsonl"):
        rows = {r["run_id"]: r for r in jsonl(f)}
        total += sum(len(r.get("verdicts") or {}) for r in rows.values())
    assert total == 5398
    assert "5,398 criterion verdicts" in prose


def test_kappa_paradox_diagnostics(prose: str):
    """Post-hoc reliability diagnostics. The gate stays failed; these explain why
    kappa collapses on a prevalence-skewed task."""
    def stats(rs):
        n = len(rs)
        a = sum(1 for h, j, _ in rs if h and j)
        b = sum(1 for h, j, _ in rs if h and not j)
        c = sum(1 for h, j, _ in rs if not h and j)
        d = sum(1 for h, j, _ in rs if not h and not j)
        po = (a + d) / n
        pa, pb = (a + b) / n, (a + c) / n
        pe = pa * pb + (1 - pa) * (1 - pb)
        pi = (pa + pb) / 2
        peg = 2 * pi * (1 - pi)
        return (round(po, 3), round((po - pe) / (1 - pe), 3), round(abs(a - d) / n, 3),
                round(abs(b - c) / n, 3), round(2 * po - 1, 3),
                round((po - peg) / (1 - peg), 3))

    recs = [(h, j, k) for h, j, k, _ in _g4_records()]
    assert stats([r for r in recs if r[2] == "fact_absent"]) == (
        0.818, 0.166, 0.773, 0.182, 0.636, 0.772)
    assert stats([r for r in recs if r[2] == "fact_applied"]) == (
        0.819, 0.605, 0.292, 0.014, 0.639, 0.667)
    assert stats([r for r in recs if r[2] == "scope_correct"]) == (
        0.794, 0.561, 0.324, 0.206, 0.588, 0.627)
    assert stats(recs) == (0.813, 0.537, 0.440, 0.000, 0.627, 0.687)

    # 2026-09-15: the per-kind diagnostics table was cut as appendix material.
    # What has to survive is the label and the range, so the adjusted figures
    # can still be checked and still cannot be made to lead.
    adjusted = [v for r in ("fact_absent", "fact_applied", "scope_correct")
                for v in stats([x for x in recs if x[2] == r])[4:]]
    assert (round(min(adjusted), 2), round(max(adjusted), 2)) == (0.59, 0.77)

    low = prose.lower()
    assert "kappa paradox" in low
    assert "post-hoc" in low, "the diagnostics must be labelled as not prespecified"
    assert "between 0.59 and 0.77" in low
    assert "we do not offer that as a defence" in low, \
        "the adjusted figures must not be offered as a defence of the gate"


def test_judge_decoy_audit(prose: str):
    audit = json.loads(
        (ROOT / "datasets/dev/screening/judge-decoys/audit.json").read_text())
    assert audit["false_accepts"] == 2
    assert audit["n_positive_criteria"] == 41
    adj = audit["adjudication_2026_08_15"]
    assert adj["as_measured"].startswith("2/41")
    assert adj["adjudicated"].startswith("0/39")
    assert "2/41" in prose and "0/39" in prose


def test_harness_agreement(prose: str):
    """The harness study failed its own prespecified 90% per-condition bar."""
    d = ROOT / "datasets/dev/screening/harness-study-2026-07-25"
    comp = json.loads((d / "comparison.json").read_text())
    proto = json.loads((d / "protocol.json").read_text())
    assert ">=90%" in proto["acceptance"], "the prespecified bar moved"

    pct = {k: round(100 * a / (a + b)) for k, (a, b) in comp["agree"].items()}
    assert pct == {"twin_ceiling_pass": 65, "ceiling_pass": 95,
                   "floor_pair_pass": 100, "floor_base_pass": 75}
    # the gated conditions: two clear the bar, twin-ceiling does not
    assert pct["floor_pair_pass"] >= 90 and pct["ceiling_pass"] >= 90
    assert pct["twin_ceiling_pass"] < 90

    low = prose.lower()
    for fragment in ("20/20", "19/20", "13/20", "15/20", "memoryless floor, at 100%",
                     "facts injected, at 95%", "65% of twin-ceiling outcomes"):
        assert fragment in prose, f"missing {fragment!r}"
    assert "90%" in prose
    assert "failed its own acceptance rule" in low


def test_salience_check_is_reported_as_an_interval(prose: str, tex: str):
    """Accepting a null at p = 0.067 on n = 100 is weak, so the paper leads with
    the interval. Both intervals are recomputed here from the counts in the
    validation report rather than read off the prose."""
    report = (ROOT / "docs" / "validation-report.md").read_text()
    agg = re.search(r"Aggregate: (\d+)/(\d+)", report)
    seed3 = re.search(r"\((\d+)/(\d+) across the first three", report)
    assert agg and seed3, "the validation report's counts moved"
    assert (int(agg.group(1)), int(agg.group(2))) == (58, 100)
    assert (int(seed3.group(1)), int(seed3.group(2))) == (42, 60)

    def rendered(k: int, n: int) -> str:
        lo, hi = _wilson(k, n)
        return f"[{100 * lo:.1f}%, {100 * hi:.1f}%]"

    assert rendered(58, 100) == "[48.2%, 67.2%]"
    assert rendered(42, 60) == "[57.5%, 80.1%]"
    for body, esc in ((prose, "%"), (tex, "\\%")):
        assert rendered(58, 100).replace("%", esc) in body
        assert rendered(42, 60).replace("%", esc) in body
    assert "bounds discrimination rather than demonstrating flatness" in prose
    assert "confirms it: raters told probed" not in prose, \
        "the check bounds discrimination, it does not confirm flatness"

    # G2's own bar sits inside the interval
    assert _wilson(58, 100)[1] * 100 > 65
    assert "G2 set the bar at a reviewer who cannot beat 65% accuracy" in prose
    assert "the comparison is approximate" in prose.lower(), \
        "the aggregate and the per-spot-check bar are not the same quantity"
    assert "is not re-litigated here" in prose, "G2's verdict does not move"

    # and the 65 is the plan's, not a number chosen after the fact
    plan = require("docs/dataset-plan.md", HISTORY).read_text()
    bar = re.search(r"cannot beat (\d+)% accuracy", plan)
    assert bar and bar.group(1) == "65", "G2's spot-check bar moved"

    # seed 3, worded as the validation report words it
    assert "scored 14/20 on four independent samples" in report
    assert "seed 3 scored 14/20 on four independent samples" in prose


def test_model_relativity(prose: str):
    """Sourced to the decision log; assert the paper and the log agree."""
    log = require("docs/decision-log.md", HISTORY).read_text()
    assert "17/54" in log and "37/54" in log
    assert "37/54" in prose and "17/54" in prose


def test_every_bibitem_is_cited(tex_raw: str):
    """The bibliography rendered as an uncited list until 2026-09-17: 21 entries
    and no \\cite anywhere. Every key must now be reachable from the body."""
    keys = re.findall(r"\\bibitem\{([^}]+)\}", tex_raw)
    assert len(keys) == len(set(keys)) == 22, f"{len(keys)} bibitems"
    cited: set[str] = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", tex_raw):
        cited |= {k.strip() for k in group.split(",")}
    assert not set(keys) - cited, f"uncited bibitems: {sorted(set(keys) - cited)}"
    assert not cited - set(keys), f"citations with no bibitem: {sorted(cited - set(keys))}"


# Author lists and titles verified against the arXiv abstract pages on
# 2026-09-17. That pass found seven entries with wrong given names and three
# titles that abbreviated what the source spells out. These are the corrected
# strings; an edit that reintroduces an old one fails here.
BIB_CORRECTIONS = {
    "membench": "Tan, H., Zhang, Z., Ma, C., Chen, X., Dai, Q., and Dong, Z.",
    "memoryarena": "He, Z., Wang, Y., Zhi, C., Hu, Y., et al.",
    "streammembench": "Liu, G., Ren, Y., Gu, H., Zhang, P., et al.",
    "gatemem": "Ren, Z., Yang, Y., Chen, Y., Zhao, Z., et al.",
    "longmemeval2": "Wu, D., Ji, Z., Kawatkar, A., Kwan, B., Gu, J.-C., Peng, N., "
                    "and Chang, K.-W.",
    "horizonbench": "Li, S. S., Paranjape, B., Oktar, K., et al.",
    "abc": "Zhu, Y., Jin, T., Pruksachatkun, Y., et al.",
    "construct": "Measuring what Matters: Construct Validity in Large Language "
                 "Model Benchmarks",
    "gsm1k": "A Careful Examination of Large Language Model Performance on Grade "
             "School Arithmetic",
    "miller": "Adding Error Bars to Evals: A Statistical Approach to Language "
              "Model Evaluations",
}

# What the 2026-09-17 pass replaced. None of these may come back.
BIB_RETIRED = (
    "Tan, H., Zhang, Y., Ma, C., Chen, L., Dai, W., and Dong, Y.",
    "He, Y., Wang, S., Zhi, R., Hu, J.",
    "Liu, X., Ren, H., Gu, Y., Zhang, K.",
    "Ren, S., Yang, Q., Chen, H., Zhao, L.",
    "Li, J., Paranjape, B.",
    "Zhu, Y., Jin, C., Pruksachatkun, Y.",
    "Construct Validity in LLM Benchmarks",
    "A Careful Examination of LLM Performance",
    "Adding Error Bars to Evals}",
)


def test_bibliography_authors_and_titles_are_the_verified_ones(tex_raw: str):
    """Ten entries were corrected on 2026-09-17 against the arXiv abstract pages."""
    flat = " ".join(tex_raw.split())
    for key, expected in BIB_CORRECTIONS.items():
        assert f"\\bibitem{{{key}}}" in tex_raw, f"{key}: bibitem gone"
        assert expected in flat, f"{key}: expected {expected!r}"
    for retired in BIB_RETIRED:
        assert retired not in flat, f"a corrected citation regressed: {retired!r}"


def test_the_citation_note_says_what_each_pass_checked(prose: str, tex: str):
    """The note is a claim about process, so it carries both passes and the
    corrections the second one made, rather than fixing them quietly."""
    for body in (prose, tex):
        assert "2026-09-17" in body
        assert "Author lists were not in that pass's scope" in body
        assert "seven entries carrying wrong given names" in body
        assert "abbreviated what the source spells out" in body


def test_companion_paper_is_cited_where_it_is_used(tex_raw: str, prose: str):
    """Track B reuses Track A's measurements and Track A leans on its judge-panel
    result, so each has to name the other."""
    assert "\\bibitem{pipeline}" in tex_raw
    assert ("Constructing a Benchmark When Every\nComponent Is a Language Model"
            in tex_raw)
    assert tex_raw.count("\\cite{pipeline}") >= 4, \
        "cite the companion in 1.4, 1.5, 4.4 and disclosure 2"


    # the judge-panel result 4.4 carries, against the artifact it came from
    rep = json.loads(
        (ROOT / "datasets/methods/judge-panel/report.json").read_text())
    panel = [t for t in rep["vs_human_sampled"] if "committed v1" not in t]
    assert len(panel) == 4, "four further blinded judges"
    vs_human = [rep["vs_human_sampled"][t]["overall"]["kappa"] for t in panel]
    vs_v1 = [rep["vs_v1_committed"][t]["overall"]["kappa"] for t in panel]
    assert (round(min(vs_human), 3), round(max(vs_human), 3)) == (0.518, 0.563)
    assert (round(min(vs_v1), 3), round(max(vs_v1), 3)) == (0.927, 0.966)
    assert all(k < 0.75 for k in vs_human) and all(k > 0.75 for k in vs_v1), \
        "the panel agrees with itself above the gate and with the rater below it"
    for fragment in ("κ 0.927 to 0.966", "κ 0.518 to 0.563",
                     "all four returned identical verdict vectors",
                     "κ 0.537, 0.524 and 0.544, at or below the best single judge "
                     "at 0.563"):
        assert fragment in prose, f"missing {fragment!r}"


def test_construct_validity_disclosure_is_present(prose: str, tex: str):
    """Added 2026-09-17: probe difficulty has no human anchor anywhere."""
    for body in (prose, tex):
        assert "Nothing anchors probe difficulty to a human" in body
        assert "no human performance baseline anywhere" in body
    assert "argued from the design and never measured" in prose


def test_no_comparative_system_claim(prose: str):
    """The reframe's central promise: no system is ranked against another."""
    low = prose.lower()
    for banned in ("expected to win", "outperforms", "beats the baseline",
                   "best-performing system", "state of the art"):
        assert banned not in low, f"comparative language survived: {banned!r}"


def test_no_single_aggregate_score(prose: str):
    low = prose.lower()
    assert "single aggregate" in low          # stated as a prohibition
    assert "overall score" not in low


SENSITIVITY = ROOT / "datasets/dev/screening/sub07-sensitivity/summary.json"


@pytest.fixture(scope="module")
def sub07() -> dict:
    return json.loads(SENSITIVITY.read_text())


def test_sub07_sensitivity_matches_the_rescored_reports(sub07: dict):
    """The summary must agree with the three re-scored reports beside it."""
    total = 0
    for org in SEEDS:
        rep = json.loads(
            (SENSITIVITY.parent / f"g3-report-drop-{org}.json").read_text())
        seed = sub07["seeds"][org]["after_drop"]
        assert seed["survivors"] == rep["n_survivors"]
        assert seed["valid_instances"] == rep["n_valid_instances"]
        assert seed["unscorable_instances"] == rep.get("n_unscorable_instances", 0)
        total += rep["n_valid_instances"]
    assert total == sub07["total_valid_instances"]["after_drop"] == 341


def test_sub07_sensitivity_numbers_are_in_the_draft(prose: str, sub07: dict):
    assert sub07["total_valid_instances"]["canon"] == 371
    # One telling, in disclosure 9, since 2026-09-15.
    assert "371 to 341 valid instances" in prose
    assert "fails all six gates instead of three" in prose


def test_canon_is_unchanged_by_the_declined_rule(g3: dict, sub07: dict):
    """Declining the rule means canon still reads 371, not 341."""
    assert sum(r["n_valid_instances"] for r in g3.values()) == 371
    for org in SEEDS:
        assert g3[org]["n_valid_instances"] == sub07["seeds"][org]["canon"]["valid_instances"]


def test_all_six_gates_fail_under_the_drop(sub07: dict):
    """The claim that applying the rule fails all six gates, not three."""
    after = [sub07["seeds"][o]["after_drop"] for o in SEEDS]
    assert not any(s["gate_clusters"] for s in after)
    assert not any(s["gate_instances"] for s in after)
    canon = [sub07["seeds"][o]["canon"] for o in SEEDS]
    assert sum(s["gate_clusters"] for s in canon) == 2
    assert not any(s["gate_instances"] for s in canon)




# --- front and back matter, added 2026-09-19 --------------------------------
# Apparatus, not results. These guards exist because every one of them is a
# statement about the author or about provenance that is cheap to widen by
# accident and expensive to have widened in print.

ORCID = "0009-0008-1031-304X"
ORCID_SHAPED = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b")

# The two Zenodo records, minted 2026-09-19. This paper's own identifier and the
# methodology paper's are the only two DOIs that exist in this project; any other
# DOI-shaped token in these files is one nobody minted. arXiv DOIs in the
# bibliography are other people's papers and are exempt.
OWN_DOI = "10.5281/zenodo.22838321"
COMPANION_DOI = "10.5281/zenodo.22838603"
# Concept DOIs resolve to a record's latest version. The README cites these, so
# a corrected version of either paper never strands a reader on the old one.
CONCEPT_DOIS = {"10.5281/zenodo.22838320", "10.5281/zenodo.22838602"}
DOI_LIKE = re.compile(r"\b10\.\d{4,9}/[^\s,;)}\]\\]+")

BACK_MATTER = (
    "Acknowledgements",
    "Author contributions",
    "Competing interests and funding",
    "Ethics",
    "Data and code availability",
    "Reproducibility",
)



def test_orcid_is_the_authors_and_nothing_else(tex: str, prose: str):
    """The iD is the author's identity in the record. One value."""
    for body in (tex, prose):
        assert ORCID in body
        found = set(ORCID_SHAPED.findall(body))
        assert found == {ORCID}, f"unexpected ORCID-shaped ids: {found - {ORCID}}"
    assert f"https://orcid.org/{ORCID}" in tex, "the .tex iD must resolve"


def test_back_matter_sections_are_present(tex: str):
    """Matched as the whole heading: a section renamed past its contract
    ("Ethics notes") is a missing section, not a present one."""
    for heading in BACK_MATTER:
        assert f"\\section*{{{heading}}}" in tex, f"tex: missing {heading}"


def test_acknowledgement_keeps_its_scope_qualifier(tex: str, prose: str):
    """The reviewer read the measurement design and nothing else. If the thanks
    ever widen past that, they misdescribe what he saw, so the qualifier is
    guarded alongside the name."""
    for body in (tex, prose):
        assert "Harshit Agarwal" in body
        assert "He reviewed the measurement design only" in body
        assert ("he saw no seed content, no fact ledger and no results, and he is "
                "not a rater in any measurement reported in this paper") in body



@pytest.mark.parametrize("rel", ["paper/memory-bench.tex", "README.md"])
def test_only_the_two_minted_dois_appear(rel: str):
    """Two records exist. A third DOI-shaped token is one nobody minted, and a
    digit dropped from either of these two points a reader at someone else's
    record, so the exact strings are pinned rather than the shape."""
    found = {d.rstrip(".").rstrip(")") for d in DOI_LIKE.findall((ROOT / rel).read_text())
             if not d.startswith("10.48550/arXiv")}
    minted = {OWN_DOI, COMPANION_DOI, *CONCEPT_DOIS}
    assert found <= minted, f"{rel}: unminted DOI: {sorted(found - minted)}"


def test_the_tex_defines_both_record_identifiers(tex_raw: str):
    """The .tex reaches its DOIs through two macros, so the value lives in one
    place per paper. \\zenodoDOI is this paper; \\companionDOI is the other."""
    assert f"\\newcommand{{\\zenodoDOI}}{{{OWN_DOI}}}" in tex_raw
    assert f"\\newcommand{{\\companionDOI}}{{{COMPANION_DOI}}}" in tex_raw


def test_the_record_identifier_is_on_page_one_and_resolvable(tex: str, prose: str):
    """A printed DOI a reader cannot click is a string, not an identifier."""
    assert "DOI: \\href{https://doi.org/\\zenodoDOI}{\\zenodoDOI}}" in tex


def test_the_companion_citation_carries_the_companion_doi(tex: str, prose: str):
    """The pair is only navigable if each paper names the other's record. The
    companion is deposited now, so it is no longer described as unpublished."""
    assert "DOI: \\href{https://doi.org/\\companionDOI}{\\companionDOI}" in tex
    assert "Unpublished companion preprint" not in tex


