"""Unit tests for the P2 release-day grader (prospective O4c inspiral-recovery prediction).

Prereg: docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md
Band table: docs/research/papers/gw-inspiral-template-efficacy/verification/p2_prospective_bands.json

Covers: band-table self-verification (and rejection of a tampered table), the
frozen ISCO-in-band regime assignment + band formula, the coverage verdict
thresholds (CONFIRMED/FALSIFIED/INCONCLUSIVE incl. the finite-N and mid-coverage
edges), the R->0 sub-claim firing independently of the coverage headline, and the
Rule-26 synthetic positive+negative controls on the grader itself.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.research import (
    p2_release_day_grade as grader,
    r_predictor as rp,
)

_BANDS = grader.load_bands()


# --- band-table integrity ----------------------------------------------------
def test_band_table_self_verifies() -> None:
    assert _BANDS["schema"] == "aigis.gw.p2_prospective_bands.v1"
    assert _BANDS["belief_moved"] is False
    assert _BANDS["regime_boundaries"]["heavy_min_m_det_msun"] == pytest.approx(146.5725, abs=1e-3)
    assert _BANDS["regime_boundaries"]["light_max_m_det_msun"] == pytest.approx(20.452, abs=1e-3)
    assert _BANDS["epsilon_r_to_zero"] == 0.05
    assert _BANDS["residual_pool"]["n_total"] == 48


def test_load_bands_rejects_tampered_table(tmp_path: Path) -> None:
    table = dict(_BANDS)
    table["epsilon_r_to_zero"] = 0.9  # mutate a field WITHOUT recomputing self_sha256
    p = tmp_path / "tampered.json"
    p.write_text(json.dumps(table))
    with pytest.raises(SystemExit):
        grader.load_bands(p)


def test_load_bands_rejects_wrong_schema(tmp_path: Path) -> None:
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps({"schema": "not.p2", "self_sha256": "x"}))
    with pytest.raises(SystemExit):
        grader.load_bands(p)


# --- regime assignment + band formula ---------------------------------------
def test_event_band_heavy_is_r_to_zero() -> None:
    # M_det ~ 199.5 -> f_ISCO < 30 Hz -> heavy; band is the frozen [0, epsilon]
    band = grader.event_band(100.0, 90.0, 0.05, _BANDS, rp)
    assert band["regime"] == "heavy"
    assert band["isco_below_band"] is True
    assert band["r_mech"] == 0.0
    assert (band["band_lo"], band["band_hi"]) == (0.0, 0.05)


def test_event_band_light_uses_light_offsets() -> None:
    # M_det ~ 16.5 -> f_ISCO > 215 Hz -> light
    band = grader.event_band(9.0, 6.0, 0.1, _BANDS, rp)
    assert band["regime"] == "light"
    off = _BANDS["bands"]["light"]
    expected_lo = min(max(band["r_mech"] + off["band_offset_lo"], 0.0), 1.0)
    expected_hi = min(max(band["r_mech"] + off["band_offset_hi"], 0.0), 1.0)
    assert band["band_lo"] == pytest.approx(expected_lo, abs=1e-6)
    assert band["band_hi"] == pytest.approx(expected_hi, abs=1e-6)


def test_event_band_intermediate_uses_intermediate_offsets() -> None:
    band = grader.event_band(30.0, 25.0, 0.1, _BANDS, rp)  # M_det ~ 60.5
    assert band["regime"] == "intermediate"
    off = _BANDS["bands"]["intermediate"]
    assert band["band_lo"] == pytest.approx(min(max(band["r_mech"] + off["band_offset_lo"], 0.0), 1.0), abs=1e-6)
    assert band["band_hi"] == pytest.approx(min(max(band["r_mech"] + off["band_offset_hi"], 0.0), 1.0), abs=1e-6)


def test_band_clipped_to_unit_interval() -> None:
    for m1, m2, z in [(9.0, 6.0, 0.1), (30.0, 25.0, 0.1), (100.0, 90.0, 0.05)]:
        band = grader.event_band(m1, m2, z, _BANDS, rp)
        assert 0.0 <= band["band_lo"] <= band["band_hi"] <= 1.0


# --- helpers to build deterministic cohorts with known coverage --------------
def _covered_row(m1: float, m2: float, z: float, event: str) -> dict:
    band = grader.event_band(m1, m2, z, _BANDS, rp)
    mid = (band["band_lo"] + band["band_hi"]) / 2.0
    return {"event": event, "m1_source": m1, "m2_source": m2, "redshift": z, "recovery_fraction": mid}


def _uncovered_row(m1: float, m2: float, z: float, event: str) -> dict:
    band = grader.event_band(m1, m2, z, _BANDS, rp)
    r = max(0.0, band["band_lo"] - 0.15)  # strictly below the band for these masses
    assert r < band["band_lo"]
    return {"event": event, "m1_source": m1, "m2_source": m2, "redshift": z, "recovery_fraction": r}


# intermediate masses whose band_lo > 0.15 so an uncovered row sits below the band
_IM = (30.0, 25.0, 0.1)


def test_grade_confirmed_all_covered() -> None:
    rows = [_covered_row(*_IM, f"c{i}") for i in range(10)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["verdict"] == "CONFIRMED"
    assert res["coverage"] == 1.0
    assert res["n_measured"] == 10


def test_grade_falsified_low_coverage() -> None:
    rows = [_covered_row(*_IM, f"c{i}") for i in range(4)] + [_uncovered_row(*_IM, f"u{i}") for i in range(6)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["coverage"] == pytest.approx(0.4, abs=1e-9)
    assert res["verdict"] == "FALSIFIED"


def test_grade_inconclusive_small_n() -> None:
    rows = [_covered_row(*_IM, f"c{i}") for i in range(5)]  # n < 8
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["verdict"] == "INCONCLUSIVE"
    assert res["n_measured"] == 5


def test_grade_inconclusive_mid_coverage() -> None:
    # 15/20 covered = 0.75 -> in the [0.70, 0.80) buffer -> INCONCLUSIVE
    rows = [_covered_row(*_IM, f"c{i}") for i in range(15)] + [_uncovered_row(*_IM, f"u{i}") for i in range(5)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["coverage"] == pytest.approx(0.75, abs=1e-9)
    assert res["verdict"] == "INCONCLUSIVE"


def test_coverage_boundary_080_confirms() -> None:
    # exactly 0.80 -> CONFIRMED (>= threshold)
    rows = [_covered_row(*_IM, f"c{i}") for i in range(8)] + [_uncovered_row(*_IM, f"u{i}") for i in range(2)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["coverage"] == pytest.approx(0.80, abs=1e-9)
    assert res["verdict"] == "CONFIRMED"


def test_coverage_boundary_070_inconclusive_not_falsified() -> None:
    # exactly 0.70 -> NOT < 0.70 -> INCONCLUSIVE (falsified is strict <)
    rows = [_covered_row(*_IM, f"c{i}") for i in range(7)] + [_uncovered_row(*_IM, f"u{i}") for i in range(3)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["coverage"] == pytest.approx(0.70, abs=1e-9)
    assert res["verdict"] == "INCONCLUSIVE"


# --- R->0 sub-claim fires independently of the coverage headline -------------
def test_r_to_zero_subclaim_falsified_even_when_coverage_high() -> None:
    # 9 covered intermediates + 1 heavy (ISCO-below-band) event that recovers R=0.6.
    # coverage = 9/10 = 0.90 -> CONFIRMED headline, but the R->0 sub-claim is FALSIFIED.
    heavy = {"event": "heavy_hi", "m1_source": 100.0, "m2_source": 90.0, "redshift": 0.05, "recovery_fraction": 0.6}
    rows = [_covered_row(*_IM, f"c{i}") for i in range(9)] + [heavy]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["verdict"] == "CONFIRMED"
    assert res["coverage"] == pytest.approx(0.9, abs=1e-9)
    assert res["r_to_zero_subclaim"]["verdict"] == "FALSIFIED"
    assert res["r_to_zero_subclaim"]["violations"][0]["event"] == "heavy_hi"


def test_r_to_zero_subclaim_confirmed_when_heavy_events_recover_zero() -> None:
    heavy = {"event": "heavy_zero", "m1_source": 100.0, "m2_source": 90.0, "redshift": 0.05, "recovery_fraction": 0.0}
    rows = [_covered_row(*_IM, f"c{i}") for i in range(9)] + [heavy]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["r_to_zero_subclaim"]["verdict"] == "CONFIRMED"
    assert res["r_to_zero_subclaim"]["n_isco_below_band"] == 1


def test_r_to_zero_not_applicable_without_heavy_events() -> None:
    rows = [_covered_row(*_IM, f"c{i}") for i in range(9)]
    res = grader.grade_cohort(rows, _BANDS, rp)
    assert res["r_to_zero_subclaim"]["verdict"] == "not_applicable"


# --- Rule 26: synthetic positive + negative control on the grader ------------
@pytest.mark.parametrize("seed", [20260717, 1, 42, 777, 2026])
def test_synthetic_positive_control_confirms(seed: int) -> None:
    """A well-calibrated synthetic O4c cohort must yield CONFIRMED (Rule 26 positive control)."""
    cohort = grader.synthetic_cohort(_BANDS, rp, n=24, mode="calibrated", seed=seed)
    res = grader.grade_cohort(cohort, _BANDS, rp)
    assert res["verdict"] == "CONFIRMED"
    assert res["coverage"] >= grader._COVERAGE_CONFIRMED


@pytest.mark.parametrize("seed", [20260717, 1, 42, 777, 2026])
def test_synthetic_negative_control_falsifies(seed: int) -> None:
    """A systematically-biased synthetic cohort must yield FALSIFIED (Rule 26 negative control)."""
    cohort = grader.synthetic_cohort(_BANDS, rp, n=24, mode="biased", seed=seed)
    res = grader.grade_cohort(cohort, _BANDS, rp)
    assert res["verdict"] == "FALSIFIED"
    assert res["coverage"] < grader._COVERAGE_FALSIFIED
    assert res["r_to_zero_subclaim"]["verdict"] == "FALSIFIED"


def test_trend_reported_as_secondary() -> None:
    cohort = grader.synthetic_cohort(_BANDS, rp, n=24, mode="calibrated", seed=7)
    res = grader.grade_cohort(cohort, _BANDS, rp)
    assert "trend_rho_M_det_R" in res
    assert res["trend_rho_M_det_R"]["expected"] == -0.9
