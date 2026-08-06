"""Power-analysis math (scripts/power_analysis.py): hand-checked cases."""

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "power_analysis",
    Path(__file__).resolve().parents[1] / "scripts" / "power_analysis.py",
)
pa = importlib.util.module_from_spec(_SPEC)
sys.modules["power_analysis"] = pa
_SPEC.loader.exec_module(pa)


def test_clustered_se_reduces_to_iid_at_rho_zero():
    # p=0.5, N=100, unclustered: SE = sqrt(0.25/100) = 0.05 exactly.
    assert abs(pa.se_single(0.5, 100, 3.0, 0.0) - 0.05) < 1e-12
    # rho>0 strictly inflates.
    assert pa.se_single(0.5, 100, 3.0, 0.4) > 0.05


def test_mdd_hand_computed():
    # p=0.5, N=100, m_bar=1 (DE=1), K=1: Var(D)=2*0.25=0.5,
    # SE=sqrt(0.5/100)=0.0707107, MDD=2.8015852*SE=0.198104.
    got = pa.mdd_paired(0.5, 100, 1.0, 0.0, 1, lam=0.5)
    assert abs(got - 0.198104) < 1e-4


def test_mdd_decreases_with_k_and_lam_matters():
    base = pa.mdd_paired(0.5, 625, 2.78, 0.4, 1)
    k2 = pa.mdd_paired(0.5, 625, 2.78, 0.4, 2)
    k3 = pa.mdd_paired(0.5, 625, 2.78, 0.4, 3)
    assert base > k2 > k3
    # With no transient share, K does nothing.
    assert pa.mdd_paired(0.5, 625, 2.78, 0.4, 3, lam=0.0) == \
        pa.mdd_paired(0.5, 625, 2.78, 0.4, 1, lam=0.0)


def test_icc_extremes():
    # Perfect within-cluster agreement, distinct cluster means -> high ICC.
    high = pa.icc_oneway([[1.0, 1.0, 1.0], [0.0, 0.0, 0.0],
                          [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]])
    assert high > 0.9
    # Identical values everywhere -> degenerate -> 0.
    assert pa.icc_oneway([[1.0, 1.0], [1.0, 1.0]]) == 0.0
    # Within-cluster variation with equal cluster means -> ~0 (clamped).
    low = pa.icc_oneway([[0.0, 1.0], [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    assert low == 0.0
