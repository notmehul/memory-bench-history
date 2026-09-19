"""Every number in the Track B pipeline paper traces to a committed artifact.

`paper/pipeline.tex` carries most of its evidence as TikZ coordinates, where a
typo is invisible: a wrong dot position still renders. These tests recompute the
data from the artifacts and assert the coordinate is present in the source.

The aggregation numbers in the paper's Figure 6 exist nowhere else. They are a
post-hoc re-aggregation of the prespecified judge panel, so they are recomputed
here from the raw panel verdicts rather than read from a report file. Nothing in
this module writes to any artifact.
"""

import itertools
import json
import re
import sys
from math import comb
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "pipeline.tex"
sys.path.insert(0, str(ROOT / "scripts"))

import methods_judge_panel as M  # noqa: E402
from calibration import _cohens_kappa  # noqa: E402
from conftest import SEALED, require  # noqa: E402

AGREEMENT = "datasets/dev/calibration/judge-agreement.json"
RATER_KEY = "datasets/dev/calibration/packet-key.json"

PANEL = ("haiku-4.5", "sonnet-5", "opus-5", "fable-5.1")

# The comparison in the paper's 6.4 has FIVE raters, not four: the four panel
# judges plus the committed v1 judge, whose verdicts the packet was rated
# against. Five is what makes ten judge-to-judge pairs and five judge-to-human
# comparisons. An earlier draft said "four judges" and then reported ten pairs.
RATERS = PANEL + ("v1",)


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


@pytest.fixture(scope="module")
def flat(tex: str) -> str:
    return " ".join(tex.split())


@pytest.fixture(scope="module")
def anchor() -> dict:
    """The frozen human labels, keyed (org, run, assertion). Read-only."""
    key = json.loads(require(RATER_KEY, SEALED).read_text())
    raw = json.loads((M.CALIB / "ratings-M.json").read_text())
    pairs = {pid: (v["org"], v["run_id"], v["assertion_id"]) for pid, v in key.items()}
    return {pairs[pid]: bool(raw[pid]) for pid in pairs}


@pytest.fixture(scope="module")
def verdicts() -> dict:
    return {t: M._panel_verdicts(M.PANEL / t) for t in PANEL}


@pytest.fixture(scope="module")
def kinds(anchor: dict) -> dict:
    return M._kind_map({o for o, _, _ in anchor})


def test_tex_is_complete(tex: str):
    assert tex.startswith("%")
    assert "\\begin{document}" in tex and "\\end{document}" in tex
    assert tex.count("\\begin{figure}") == 6, "six figures expected"
    assert tex.count("\\begin{table}") == 3, "three tables expected"


def test_control_the_v1_baseline_still_recomputes(anchor: dict, kinds: dict):
    """Reproduce a known number before trusting any new one (paper 5.4)."""
    v1 = M._v1_verdicts({o for o, _, _ in anchor})
    pairs = sorted(anchor)
    block = M._agree_block(pairs, anchor, v1, kinds)["overall"]
    assert (block["n"], block["agreement"], block["kappa"]) == (150, 0.8133, 0.537)


@pytest.fixture(scope="module")
def raters(verdicts: dict) -> dict:
    """The four panel judges plus the committed v1 judge. Five, not four."""
    v = dict(verdicts)
    v["v1"] = M._v1_verdicts({"org-00001", "org-00002"})
    assert set(v) == set(RATERS)
    return v


def test_judge_to_judge_kappa_range_in_the_prose(raters: dict, flat: str):
    """All ten pairs, not each judge against the committed v1 run."""
    v = raters
    common = sorted(set.intersection(*(set(d) for d in v.values())))
    assert len(common) == 478
    stats = [_cohens_kappa([v[a][k] for k in common], [v[b][k] for k in common])
             for a, b in itertools.combinations(v, 2)]
    kap = [k for _, k, _ in stats]
    agr = [p for p, _, _ in stats]
    assert f"{min(kap):.3f}--{max(kap):.3f}" == "0.927--0.970"
    assert f"{min(agr):.3f}--{max(agr):.3f}" == "0.964--0.985"
    assert "judge-to-judge $\\kappa$ runs 0.927--0.970 at 0.964--0.985" in flat


def test_the_rater_count_is_five_and_the_prose_says_so(raters: dict, flat: str):
    """The four/five error: four judges give six pairs, the paper reports ten.

    Ten pairs and five judge-to-human comparisons require five raters. This
    pins the arithmetic to the roster and the roster to the prose, in the
    abstract as well as 6.4, so the miscount cannot come back.
    """
    n = len(raters)
    assert n == 5
    assert len(list(itertools.combinations(raters, 2))) == 10

    # 6.4 states the roster, the fifth rater, and where ten and five come from.
    assert "four blinded judges" in flat, "the PANEL is still four"
    assert ("The committed v1 judge, whose verdicts the packet was rated "
            "against, enters every comparison below as a fifth rater.") in flat
    assert ("Five raters give ten judge-to-judge pairs and five "
            "judge-to-human comparisons.") in flat
    assert "against the human anchor all five run $\\kappa$ 0.518--0.563" in flat

    # The abstract inherited the error and must state the fifth rater too.
    abstract = flat.split("\\end{abstract}")[0]
    assert "set beside the committed judge as a fifth rater" in abstract
    assert "all ten rater pairs" in abstract
    assert "in every one of the five comparisons" in abstract

    # No surviving claim that the self-agreement figure spans four raters.
    assert "four judge" not in flat.replace("four blinded judges", "")
    assert "Across all ten pairs" in flat


def test_the_v1_judge_shares_a_model_with_one_panel_member(flat: str):
    """sonnet-5 is both a panel arm and the committed v1 judge's model.

    That is why the five raters are only four distinct models, and why the
    sonnet-5 arm is a test-retest rather than a fifth opinion.
    """
    assert "sonnet-5" in M.V1_TAG, M.V1_TAG
    assert "sonnet-5" in PANEL
    assert ("One panel member runs the same model as that v1 judge, sonnet-5, "
            "so the five raters are four distinct models") in flat

    rep = json.loads((M.PANEL / "report.json").read_text())
    retest = rep["vs_v1_committed"]["sonnet-5"]["overall"]
    assert retest["n"] == 478
    assert f"agrees at {retest['agreement']:.3f}" in flat
    assert f"$\\kappa$ {retest['kappa']:.3f} over the 478" in flat
    assert "the sonnet-5 arm is what supplies it" in flat


def test_figure_6_top_panel_plots_ten_pairs_and_five_human_comparisons(
        raters: dict, anchor: dict, tex: str):
    """Coordinates, where a typo is invisible: recompute and match exactly."""
    top = tex.split("name=top,")[1].split("at={(top.outer south west)}")[0]
    plotted = re.findall(r"\(([01]\.\d+),(\d)\)", top.replace(" ", ""))
    jj = sorted(float(x) for x, row in plotted if row == "1")
    jh = sorted(float(x) for x, row in plotted if row == "0")
    assert len(jj) == 10, "ten judge-to-judge pairs"
    assert len(jh) == 5, "five judge-to-human comparisons"

    common = sorted(set.intersection(*(set(d) for d in raters.values())))
    want_jj = sorted(round(_cohens_kappa([raters[a][k] for k in common],
                                         [raters[b][k] for k in common])[1], 4)
                     for a, b in itertools.combinations(raters, 2))
    assert jj == want_jj

    pairs = sorted(anchor)
    want_jh = sorted(round(_kappa(raters[t], anchor, pairs), 4) for t in raters)
    assert jh == want_jh


def test_kappa_bootstrap_intervals_match_the_committed_artifact(flat: str):
    """Post-hoc CIs added 2026-09-17. Strings must match the artifact."""
    g4 = json.loads(require(AGREEMENT, SEALED).read_text())

    def interval(block: dict) -> str:
        lo, hi = block["kappa_bootstrap"]["ci95"]
        return f"[{lo:.3f}, {hi:.3f}]"

    assert interval(g4) == "[0.370, 0.688]"
    assert f"puts the 95\\% interval at {interval(g4)}" in flat
    for kind in ("fact_absent", "fact_applied", "scope_correct"):
        block = g4["per_kind"][kind]
        assert f"{block['kappa']:.3f}" in flat
        assert interval(block) in flat, kind

    boot = g4["kappa_bootstrap"]
    assert boot["replicates"] == 10000 and boot["degenerate_replicates"] == 0
    assert boot["n_clusters"] == 89
    assert "the 89 fact clusters the packet spans" in flat
    assert "10,000 replicates at a fixed seed with no degenerate replicate" in flat

    # The FAIL must be stated as independent of the point estimate, and the
    # gate itself must still be the prespecified one.
    hi = boot["ci95"][1]
    assert hi < 0.75
    assert ("The upper bound is below the gate, so the FAIL does not depend "
            "on the point estimate.") in flat
    assert "prespecified $\\kappa \\geq 0.75$" in flat


def test_the_by_kind_claim_rests_on_direction_not_on_three_kappas(
        anchor: dict, kinds: dict, flat: str):
    """Recompute the one-sided error counts and their exact binomial p."""
    v1 = M._v1_verdicts({o for o, _, _ in anchor})
    tally: dict[str, list[int]] = {}
    for p in sorted(anchor):
        if anchor[p] != v1[p]:
            # index 0: judge accepts where the human rejected (over-accept).
            tally.setdefault(kinds[p]["kind"], [0, 0])[0 if v1[p] else 1] += 1
    assert tally["fact_absent"] == [8, 0]
    assert tally["scope_correct"] == [0, 7]

    def two_sided(n: int) -> float:
        """All n disagreements one way, p=0.5: both tails of the exact test."""
        return 2 * sum(comb(n, k) * 0.5 ** n for k in (n,))

    assert f"{two_sided(8):.3f}" == "0.008"
    assert f"{two_sided(7):.3f}" == "0.016"
    assert ("two-sided exact binomial $p = 0.008$ and $p = 0.016$ against an "
            "even split") in flat
    assert ("Every pair of those intervals overlaps, so they do not establish "
            "that $\\kappa$ differs by criterion kind, and the claim of this "
            "section does not rest on comparing them.") in flat

    # ...and the overlap claim is true of the committed intervals.
    g4 = json.loads(require(AGREEMENT, SEALED).read_text())
    cis = [g4["per_kind"][k]["kappa_bootstrap"]["ci95"]
           for k in ("fact_absent", "fact_applied", "scope_correct")]
    for (alo, ahi), (blo, bhi) in itertools.combinations(cis, 2):
        assert min(ahi, bhi) > max(alo, blo), "a pair of per-kind CIs is disjoint"


# Author lists and titles checked against the arXiv abstract pages on
# 2026-09-17. The earlier 2026-09-14 pass checked id-to-title only, which is how
# six entries carried right surnames with invented given names. Substrings, so
# reflowing an entry across lines is still allowed.
BIB_VERIFIED = {
    "memoryarena": ("He, Z., Wang, Y., Zhi, C., Hu, Y., et al.",),
    "gatemem": ("Ren, Z., Yang, Y., Chen, Y., Zhao, Z., et al.",),
    "abc": ("Zhu, Y., Jin, T., Pruksachatkun, Y., et al.",),
    "construct": ("Construct Validity in Large Language Model Benchmarks",),
    "gsm1k": ("A Careful Examination of Large Language Model Performance on "
              "Grade School Arithmetic",),
    "miller": ("Adding Error Bars to Evals: A Statistical Approach to "
               "Language Model Evaluations",),
}


@pytest.mark.parametrize("key,wanted", sorted(BIB_VERIFIED.items()))
def test_corrected_bibliography_entries_stay_corrected(
        key: str, wanted: tuple, flat: str):
    """Six entries had invented given names or an abbreviated title."""
    entry = flat.split(f"\\bibitem{{{key}}}")[1].split("\\bibitem{")[0]
    for want in wanted:
        assert want in entry, f"{key}: expected {want!r} in {entry!r}"
    # The specific wrong strings, so a revert is caught by name.
    for wrong in ("He, Y., Wang, S., Zhi, R., Hu, J.",
                  "Ren, S., Yang, Q., Chen, H., Zhao, L.",
                  "Jin, C.", "Construct Validity in LLM Benchmarks",
                  "Examination of LLM Performance"):
        assert wrong not in entry, f"{key}: reverted to {wrong!r}"


def test_every_bibitem_is_cited_at_least_once(tex: str):
    items = re.findall(r"\\bibitem\{([^}]+)\}", tex)
    assert len(items) == 15, "14 originals plus the companion paper"
    cited: set[str] = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", tex):
        cited |= {k.strip() for k in group.split(",")}
    assert not [k for k in items if k not in cited], "dangling bibliography"
    assert not cited - set(items), "citation with no entry"
    assert "companion" in cited


def test_panel_is_byte_identical_on_the_sampled_absence_criteria(
        verdicts: dict, anchor: dict, kinds: dict, flat: str):
    ks = [p for p in sorted(anchor) if kinds[p]["kind"] == "fact_absent"]
    assert len(ks) == 44
    vecs = {t: tuple(verdicts[t][p] for p in ks) for t in PANEL}
    assert len(set(vecs.values())) == 1, "the byte-identical claim"
    n_true = sum(next(iter(vecs.values())))
    assert (n_true, len(ks) - n_true) == (42, 2)
    assert sum(anchor[p] for p in ks) == 35
    assert "42 true and 2 false in the same positions" in flat
    assert "the human gave 35/9" in flat


def _kappa(pred, anchor, pairs):
    return _cohens_kappa([anchor[p] for p in pairs], [pred[p] for p in pairs])[1]


def test_figure_6_dot_coordinates_match_the_recomputed_kappas(
        verdicts: dict, anchor: dict, kinds: dict, tex: str):
    """Figure 6, lower panel: single judges then the three aggregation rules."""
    pairs = sorted(anchor)
    rules = {
        "fable-5.1": verdicts["fable-5.1"],
        "opus-5": verdicts["opus-5"],
        "haiku-4.5": verdicts["haiku-4.5"],
        "sonnet-5": verdicts["sonnet-5"],
        "majority": {p: sum(verdicts[t][p] for t in PANEL) >= 2 for p in pairs},
        "AND": {p: all(verdicts[t][p] for t in PANEL) for p in pairs},
        "OR": {p: any(verdicts[t][p] for t in PANEL) for p in pairs},
    }
    # Row order in the figure is bottom-up: OR=0 ... fable=6.
    rows = {"fable-5.1": 6, "opus-5": 5, "haiku-4.5": 4, "sonnet-5": 3,
            "majority": 2, "AND": 1, "OR": 0}
    for name, pred in rules.items():
        overall = round(_kappa(pred, anchor, pairs), 4)
        assert f"({overall:.4f},{rows[name]})" in tex.replace(" ", ""), name

    absent = [p for p in pairs if kinds[p]["kind"] == "fact_absent"]
    for name, pred in rules.items():
        # Identical vectors on this class, so every rule lands on one column.
        assert round(_kappa(pred, anchor, absent), 4) == 0.3125, name
    assert "(0.3125,6)" in tex.replace(" ", "")
    assert "$\\kappa=0.313$" in tex

    # No aggregation rule beats the best single judge.
    best_single = max(round(_kappa(rules[t], anchor, pairs), 4) for t in PANEL)
    best_rule = max(round(_kappa(rules[r], anchor, pairs), 4)
                    for r in ("majority", "AND", "OR"))
    assert best_rule <= best_single


def test_unanimous_subset_claim(verdicts: dict, anchor: dict, kinds: dict, flat: str):
    pairs = sorted(anchor)
    unan = [p for p in pairs if len({verdicts[t][p] for t in PANEL}) == 1]
    assert len(unan) == 141
    dis = [p for p in unan if verdicts["haiku-4.5"][p] != anchor[p]]
    assert len(dis) == 24
    kap = _kappa(verdicts["haiku-4.5"], anchor, unan)
    assert f"{kap:.3f}" == "0.575"
    by = {}
    for p in dis:
        over = verdicts["haiku-4.5"][p]
        by.setdefault(kinds[p]["kind"], [0, 0])[0 if over else 1] += 1
    assert by["fact_absent"] == [7, 0]
    assert by["scope_correct"] == [0, 6]
    assert "unanimous on 141 of 150 items" in flat
    assert "$\\kappa$ is 0.575" in flat
    assert "7 of 7 panel over-accepts on absence, 6 of 6 under-accepts on scope" \
        in flat


def test_slopegraph_coordinates_match_the_committed_report(tex: str, flat: str):
    d = json.loads((ROOT / "datasets/methods/corpus-kind-rates/slopegraph.json"
                    ).read_text())
    for kind in ("fact_absent", "fact_applied", "scope_correct"):
        a = d[kind]["screening"]["rate"]
        b = d[kind]["floor"]["rate"]
        assert f"(\\xa,{{\\sy{{{a}}}" in tex.replace(" ", ""), kind
        assert f"(\\xb,{{\\sy{{{b}}}" in tex.replace(" ", ""), kind
    ns = [d[k][p]["n"] for p in ("screening", "floor")
          for k in ("fact_absent", "fact_applied", "scope_correct")]
    assert ns == [1359, 2481, 1188, 104, 196, 70]
    assert "$n=1{,}359$ / $2{,}481$ / $1{,}188$" in flat
    assert "$n=104$ / $196$ / $70$" in flat


def test_pooled_corpus_rates_in_the_prose(flat: str):
    d = json.loads((ROOT / "datasets/methods/corpus-kind-rates/report.json"
                    ).read_text())
    assert d["n_verdicts_total"] == 5398 and d["unmatched_total"] == 0
    pooled = d["pooled"]["by_kind"]
    assert "all 5,398 committed verdicts" in flat
    for kind, want in (("fact_absent", "96.4"), ("fact_applied", "39.0"),
                       ("scope_correct", "36.9")):
        assert f"{pooled[kind]['positive_rate'] * 100:.1f}" == want
        assert f"{want}\\%" in flat
    rates = [p["by_kind"]["fact_absent"]["positive_rate"] for p in d["per_dir"]]
    assert f"{min(rates) * 100:.1f}--{max(rates) * 100:.1f}\\%" == "93.2--98.9\\%"
    assert "93.2--98.9\\%" in flat


def test_gate_table_matches_the_g3_reports(flat: str):
    want = {"org-00001": (46, 125), "org-00002": (46, 131), "org-00003": (40, 115)}
    total = 0
    for org, (clusters, inst) in want.items():
        rep = json.loads((ROOT / "datasets/dev" / org / "g3-report.json").read_text())
        assert rep["n_survivors"] == clusters, org
        assert rep["n_valid_instances"] == inst, org
        total += inst
        assert f"{clusters}/54 & {inst} &" in flat
    assert total == 371
    assert "\\textbf{371}" in flat


def test_harness_study_numbers_and_the_prespecified_bar(tex: str, flat: str):
    proto = json.loads((ROOT / "datasets/dev/screening/harness-study-2026-07-25"
                        / "protocol.json").read_text())
    assert ">=90%" in proto["acceptance"].replace(" ", "")
    for pct, row in ((65, 0), (95, 1), (100, 2)):
        assert f"({pct},{row})" in tex.replace(" ", "")
    assert "(axiscs:90,-0.7)" in tex.replace(" ", ""), "the bar must be drawn"
    assert "13/20" in flat and "19/20" in flat and "20/20" in flat


def test_no_comparative_system_claim_anywhere(flat: str):
    lowered = flat.lower()
    for banned in ("outperform", "state of the art", "best performing",
                   "leaderboard result", "beats mem0"):
        assert banned not in lowered, banned


# ---------------------------------------------------------------------------
# Front and back matter, added 2026-09-19 for the Zenodo/arXiv deposit.
#
# None of this is a measured number, so none of it can be checked against an
# artifact. What it can be checked against is fabrication and quiet widening: an
# acknowledgement whose scope creeps from "reviewed the measurement design"
# towards "contributed to the results", or a DOI nobody minted.
# ---------------------------------------------------------------------------

ORCID = "0009-0008-1031-304X"

# The two Zenodo records, minted 2026-09-19. OWN_DOI is this paper's concept
# DOI (all versions, resolves to the latest): v1, 10.5281/zenodo.22838603,
# misstated the 5.2 exploit count and must not be what page one points at.
# COMPANION_DOI is the dataset and validity paper's. arXiv DOIs belong to other
# people's papers in the bibliography and are exempt.
OWN_DOI = "10.5281/zenodo.22838602"
COMPANION_DOI = "10.5281/zenodo.22838321"
ANY_DOI = re.compile(r"10\.\d{4,9}/[^\s{},;\\]+")

BACK_MATTER = (
    "Acknowledgements",
    "Author contributions",
    "Competing interests and funding",
    "Ethics",
    "Data and code availability",
    "Reproducibility",
)


def _macro_body(tex: str, name: str) -> str:
    """The balanced-brace body of \\newcommand{\\name}{...}."""
    m = re.search(rf"\\newcommand\{{\\{name}\}}\{{", tex)
    assert m, f"\\{name} is not defined"
    depth, i, out = 1, m.end(), []
    while depth:
        assert i < len(tex), f"\\{name}: unbalanced braces"
        c = tex[i]
        depth += {"{": 1, "}": -1}.get(c, 0)
        if depth:
            out.append(c)
        i += 1
    return "".join(out)


def test_the_orcid_id_is_the_authors(tex: str, flat: str):
    """One real iD, supplied by the author, in the author block and linked."""
    assert tex.count(ORCID) == 2, "expected the iD once in the href and once as text"
    assert f"\\href{{https://orcid.org/{ORCID}}}{{{ORCID}}}" in flat
    author = flat.split("\\author{")[1].split("\\date{")[0]
    assert ORCID in author, "the iD is not in the author block"
    assert "Independent researcher" in author


def test_both_record_identifiers_are_defined_once_each(tex: str):
    """The .tex reaches its DOIs through two macros, so each value lives in one
    place. A digit dropped from either points a reader at someone else's
    record, so the exact strings are pinned rather than the shape."""
    assert f"\\newcommand{{\\zenodoDOI}}{{{OWN_DOI}}}" in tex
    assert f"\\newcommand{{\\companionDOI}}{{{COMPANION_DOI}}}" in tex
    found = {d.rstrip(".").rstrip(")") for d in ANY_DOI.findall(tex)
             if not d.startswith("10.48550/arXiv")}
    assert found == {OWN_DOI, COMPANION_DOI}, \
        f"unminted DOI: {sorted(found - {OWN_DOI, COMPANION_DOI})}"


def test_the_record_identifier_is_on_page_one(flat: str):
    """A printed DOI a reader cannot click is a string, not an identifier."""
    assert "DOI: \\href{https://doi.org/\\zenodoDOI}{\\zenodoDOI}}" in flat


def test_the_companion_citation_carries_the_companion_doi(flat: str):
    """The pair is only navigable if each paper names the other's record."""
    bib = flat.split("\\bibitem{companion}")[1].split("\\bibitem{judge}")[0]
    assert "DOI: \\href{https://doi.org/\\companionDOI}{\\companionDOI}" in bib


def test_every_back_matter_section_is_present_and_placed_after_the_body(tex: str):
    body_end = tex.index("\\section{Release}")
    bib = tex.index("\\begin{thebibliography}")
    for name in BACK_MATTER:
        at = tex.find(f"\\section*{{{name}}}")
        assert at != -1, f"missing back matter: {name}"
        assert body_end < at < bib, f"{name} is not between the body and the bibliography"


def test_the_acknowledgement_scope_cannot_be_quietly_widened(flat: str):
    """Harshit Agarwal reviewed the design, not the data or the results.

    The wording was settled with the reviewer. Each clause below is what keeps
    the credit accurate, so each is pinned separately rather than as one blob.
    """
    ack = flat.split("\\section*{Acknowledgements}")[1].split("\\section*{")[0]
    assert "Harshit Agarwal" in ack
    for clause in (
        "He reviewed the measurement design only",
        "he saw no seed content, no fact ledger and no results",
        "he is not a rater in any measurement reported in this paper",
    ):
        assert clause in ack, f"scope qualifier dropped: {clause!r}"






# ---------------------------------------------------------------------------
# Scorer-exploit audit, §5.2. Added 2026-09-19 after the published v1 of this
# paper attached the post-detector count (18) to the pre-detector condition.
# Three measurements, three artifacts, and the prose has to keep each number
# on the condition it was measured under.
# ---------------------------------------------------------------------------

EXPLOIT = ROOT / "datasets/dev/screening/exploit-audit"


def _first_audit_enumerate() -> dict:
    """The 2026-08-06 audit, run before any cross-side detector existed. Its
    report was overwritten in place on 2026-08-15; this is the committed copy of
    the original, extracted verbatim from commit b21cf8c of the history repo."""
    raw = (EXPLOIT / "report-first-audit-2026-08-06.json").read_text()
    return json.loads(raw)["stats"]["enumerate_all"]


def test_exploit_audit_numbers_sit_on_the_conditions_they_measured(flat: str):
    first = _first_audit_enumerate()
    refined = json.loads((EXPLOIT / "report-post-refinement.json").read_text())["enumerate_all"]
    canon = json.loads((EXPLOIT / "report.json").read_text())["stats"]

    assert (first["pair_pass"], first["n"]) == (27, 45)
    assert (refined["pair"], refined["n"]) == (18, 45)
    assert {k: v["pair_pass"] for k, v in canon.items()} == dict.fromkeys(canon, 0)
    assert {v["n"] for v in canon.values()} == {46}

    assert ("before any cross-side absence detector existed, found the "
            "enumerate-both-values hedge earning full pair credit on 27 of them") in flat
    assert "18 still did after mechanical detectors were added" in flat
    assert "46 pairs per type, every degenerate type scores zero pair-passes" in flat
    assert "Before cross-side absence detectors existed, the enumerate-both-values" \
           " hedge earned full pair credit on 18" not in flat, "the published v1 error is back"


# ---------------------------------------------------------------------------
# What ships. Added 2026-09-19: v1 of this paper said the generator ships, while
# Track A and scripts/release.py withhold it. The generator is a deterministic
# function of the seed and rebuilds the holdout ledgers' structure exactly, so
# release.py is right and the paper has to agree with it.
# ---------------------------------------------------------------------------

def test_the_generator_is_withheld_as_release_py_says(flat: str):
    policy = " ".join((ROOT / "scripts" / "release.py").read_text().split())
    assert "the generator itself" in policy.split("Withheld:")[1].split("Canary")[0], \
        "release.py no longer withholds the generator; revisit this paper"
    release = flat.split("\\section{Release}")[1].split("\\section*{")[0]
    assert "alongside the generator" not in flat
    assert "the generator and screening pipeline" not in flat
    assert "The generator, the ledger" in release, "9 must list the generator as withheld"


def test_no_sentence_is_left_dangling_in_the_availability_section(flat: str):
    """v1 shipped 'the harness is MIT. The generator, Section 9 lists ...' after a
    compression edit matched one line late."""
    avail = flat.split("\\section*{Data and code availability}")[1].split("\\section*{")[0]
    assert "The generator, Section" not in avail


def test_availability_says_where_the_code_and_record_are(flat: str):
    """Written for the state v2 describes: dataset, code and history all public."""
    avail = flat.split("\\section*{Data and code availability}")[1].split("\\section*{")[0]
    assert "https://github.com/notmehul/memory-bench}" in avail
    assert "https://github.com/notmehul/memory-bench-history}" in avail
    assert "private until" not in avail
