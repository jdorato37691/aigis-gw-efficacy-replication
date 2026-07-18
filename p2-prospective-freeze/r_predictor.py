#!/usr/bin/env python3
"""Posterior-robust recovery-fraction predictors for the GW inspiral-efficacy program (P1).

Preregistration: docs/research/preregistrations/2026-07-17-p1-posterior-robust-predictor.md
(committed before any evaluation-cohort grading). This module is the pluggable
predictor family the posterior harness (posterior_propagation.py) scores against
the UNCHANGED original O2 gauge (median |R - R_pred(M_det)| <= 0.15 in >= 90% of
the 100 Study-3 joint posterior draws; withdrawn baseline 54/100).

The mechanism (physics): to first order R is the fraction of matched-filter SNR
the inspiral-only template accumulates in band before its validity cutoff.
Filtering an inspiral-only template against the full signal gives a recovered
fraction equal to the noise-weighted normalized overlap, which for a template
equal to the signal on [f_low, f_end] and zero above reduces exactly to

    R_mech = sqrt( I(f_low, f_end(M)) / I(f_low, f_high) )
    I(a, b) = integral from a to b of  |h(f)|^2 / S_n(f)  df

with |h(f)|^2 = f^(-7/3) (leading TaylorF2 amplitude; the chirp-mass prefactor
cancels in the ratio), f_end = Schwarzschild f_ISCO of the detector-frame total
mass (clamped to the band), band [30, 2048] Hz, and S_n the Ajith (2011) aLIGO
design analytic PSD. Because R_mech is evaluated on the DRAW's masses, posterior
mass-smearing propagates through the predictor instead of breaking a static
curve.

belief_moved=false; this module authors no belief and fetches nothing at grading
time (all development calibration inputs are frozen constants below).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from functools import lru_cache

import numpy as np

# --- frozen physical constants (prereg-locked) ------------------------------
_MSUN_SECONDS = 4.925491025543576e-06  # G*Msun/c^3, matches taylorf2.py
F_LOW = 30.0  # pipeline band floor (gwtc1_taylorf2_sweep._load_instrument)
F_HIGH = 2048.0  # pipeline band ceiling
_PSD_F0 = 215.0  # Ajith (2011) reference frequency
_AMP_POWER = -7.0 / 3.0  # |h(f)|^2 ~ f^(-7/3), leading TaylorF2 amplitude squared

# twin-integral disagreement gate (prereg-locked)
TWIN_TOLERANCE = 1.0e-3


def psd_aligo_design(freqs: np.ndarray) -> np.ndarray:
    """Advanced LIGO design-sensitivity analytic PSD (Ajith 2011, arXiv:0909.2867 Eq. 4.7).

    Only the SHAPE matters here: the overall scale S0 cancels in the R_mech
    ratio. Defined for the analysis band [30, 2048] Hz (well above the ~20 Hz
    low-frequency wall where the fit diverges).
    """
    x = np.asarray(freqs, dtype=float) / _PSD_F0
    return x ** (-4.14) - 5.0 * x ** (-2.0) + 111.0 * (1.0 - x**2 + 0.5 * x**4) / (1.0 + 0.5 * x**2)


def f_isco(m_det_msun: float) -> float:
    """Schwarzschild ISCO frequency of the detector-frame total mass (Hz).

    Identical to taylorf2.taylorf2_time_domain's default f_cut:
    1 / (6^1.5 * pi * M_det_seconds).
    """
    m_sec = m_det_msun * _MSUN_SECONDS
    return 1.0 / (6.0**1.5 * math.pi * m_sec)


def _clamped_f_end(m_det_msun: float) -> float:
    return min(max(f_isco(m_det_msun), F_LOW), F_HIGH)


# --- twin A: trapezoid on a dense LINEAR frequency grid ----------------------
def _integral_linear(a: float, b: float) -> float:
    if b <= a:
        return 0.0
    # ~0.02 Hz spacing, floored so short intervals still resolve the integrand
    n = max(2000, int((b - a) / 0.02))
    grid = np.linspace(a, b, n)
    integrand = grid**_AMP_POWER / psd_aligo_design(grid)
    return float(np.trapezoid(integrand, grid))


@lru_cache(maxsize=1)
def _denominator_linear() -> float:
    return _integral_linear(F_LOW, F_HIGH)


def _r_mech_linear(m_det_msun: float) -> float:
    f_end = _clamped_f_end(m_det_msun)
    if f_end <= F_LOW:
        return 0.0
    return math.sqrt(_integral_linear(F_LOW, f_end) / _denominator_linear())


# --- twin B: Simpson on a LOG frequency grid via u = ln f substitution -------
# independently re-derived: with u = ln f, df = f du, so the integrand
# f^(-7/3)/S_n(f) df becomes f^(-4/3)/S_n(f) du. Different grid, different rule,
# different organization from twin A.
def _integral_logsimpson(a: float, b: float) -> float:
    from scipy.integrate import simpson  # noqa: PLC0415

    if b <= a:
        return 0.0
    n = max(2001, int((math.log(b) - math.log(a)) / 1.0e-5))
    if n % 2 == 0:
        n += 1  # Simpson needs an odd number of samples
    u = np.linspace(math.log(a), math.log(b), n)
    f = np.exp(u)
    integrand_u = f ** (_AMP_POWER + 1.0) / psd_aligo_design(f)
    return float(simpson(integrand_u, x=u))


@lru_cache(maxsize=1)
def _denominator_logsimpson() -> float:
    return _integral_logsimpson(F_LOW, F_HIGH)


def _r_mech_logsimpson(m_det_msun: float) -> float:
    f_end = _clamped_f_end(m_det_msun)
    if f_end <= F_LOW:
        return 0.0
    return math.sqrt(_integral_logsimpson(F_LOW, f_end) / _denominator_logsimpson())


def r_mech(m_det_msun: float, *, impl: str = "linear") -> float:
    """Pure-mechanism recovery fraction R_mech(M_det), zero fitted parameters.

    impl selects the twin implementation ("linear" = twin A, "logsimpson" =
    twin B). The two must agree to TWIN_TOLERANCE (checked by assert_twin).
    """
    if impl == "linear":
        return _r_mech_linear(m_det_msun)
    if impl == "logsimpson":
        return _r_mech_logsimpson(m_det_msun)
    raise ValueError(f"unknown impl {impl!r}")


def twin_max_disagreement(m_dets: Iterable[float]) -> float:
    """Max |R_mech_A - R_mech_B| over the given detector-frame total masses."""
    worst = 0.0
    for m in m_dets:
        worst = max(worst, abs(_r_mech_linear(m) - _r_mech_logsimpson(m)))
    return worst


def assert_twin(m_dets: Iterable[float], tolerance: float = TWIN_TOLERANCE) -> float:
    """Independent-check tripwire: raise if the two integral twins disagree.

    Must pass before any grading run (prereg-locked). Returns the observed max
    disagreement.
    """
    m_list = list(m_dets)
    worst = twin_max_disagreement(m_list)
    if worst > tolerance:
        raise AssertionError(f"R_mech twin disagreement {worst:.3e} exceeds tolerance {tolerance:.3e}")
    return worst


# --- baseline: the withdrawn r_hat step predictor (positive control) ---------
# Byte-identical to gwtc3_oos_study.r_hat (the locked GWTC-1-derived bins). Kept
# inline so this module loads both as a package import and via file-spec load.
def _r_hat_bins(m_det: float) -> float:
    if m_det < 30.0:
        return 0.849
    if m_det < 70.0:
        return 0.554
    if m_det < 100.0:
        return 0.428
    return 0.210


# --- frozen GWTC-1 development calibration inputs ----------------------------
# Study-2 spin-template recoveries that r_hat itself was built from (the r_hat
# prereg table), the ONLY calibration data candidates 2 and 3 may use.
_DEV_POINTS: tuple[tuple[float, float], ...] = (
    # (M_det, R_dev)
    (19.9, 0.909),
    (23.3, 0.789),
    (44.5, 0.683),
    (61.0, 0.480),
    (62.5, 0.554),
    (70.6, 0.261),
    (72.2, 0.445),
    (75.1, 0.410),
    (92.5, 0.438),
    (125.5, 0.210),
)

# eventapi median + asymmetric 90% CI offsets for the same 10 GWTC-1 events
# (fetched read-only 2026-07-17; frozen so candidate 3 needs no network at
# grading). Keyed to _DEV_POINTS by row order.
_DEV_POSTERIOR_CI: tuple[dict[str, float], ...] = (
    {
        "m1": 10.6,
        "m1_lo": -1.4,
        "m1_hi": 4.0,
        "m2": 7.8,
        "m2_lo": -1.9,
        "m2_hi": 1.2,
        "z": 0.07,
        "z_lo": -0.03,
        "z_hi": 0.03,
    },
    {
        "m1": 14.2,
        "m1_lo": -3.6,
        "m1_hi": 11.1,
        "m2": 7.5,
        "m2_lo": -2.8,
        "m2_hi": 2.4,
        "z": 0.1,
        "z_lo": -0.04,
        "z_hi": 0.03,
    },
    {
        "m1": 24.8,
        "m1_lo": -6.3,
        "m1_hi": 14.5,
        "m2": 13.6,
        "m2_lo": -4.9,
        "m2_hi": 4.5,
        "z": 0.2,
        "z_lo": -0.09,
        "z_hi": 0.11,
    },
    {
        "m1": 28.7,
        "m1_lo": -4.2,
        "m1_hi": 6.6,
        "m2": 20.8,
        "m2_lo": -4.7,
        "m2_hi": 4.1,
        "z": 0.22,
        "z_lo": -0.09,
        "z_hi": 0.07,
    },
    {
        "m1": 30.9,
        "m1_lo": -3.3,
        "m1_hi": 5.4,
        "m2": 24.9,
        "m2_lo": -4.0,
        "m2_hi": 3.0,
        "z": 0.13,
        "z_lo": -0.05,
        "z_hi": 0.03,
    },
    {
        "m1": 34.1,
        "m1_lo": -5.3,
        "m1_hi": 8.0,
        "m2": 24.2,
        "m2_lo": -5.3,
        "m2_hi": 4.8,
        "z": 0.21,
        "z_lo": -0.07,
        "z_hi": 0.05,
    },
    {
        "m1": 34.6,
        "m1_lo": -2.6,
        "m1_hi": 4.4,
        "m2": 30.0,
        "m2_lo": -4.6,
        "m2_hi": 2.9,
        "z": 0.1,
        "z_lo": -0.03,
        "z_hi": 0.03,
    },
    {
        "m1": 34.8,
        "m1_lo": -4.2,
        "m1_hi": 6.5,
        "m2": 27.6,
        "m2_lo": -5.1,
        "m2_hi": 4.1,
        "z": 0.21,
        "z_lo": -0.07,
        "z_hi": 0.07,
    },
    {
        "m1": 38.3,
        "m1_lo": -6.2,
        "m1_hi": 9.5,
        "m2": 29.0,
        "m2_lo": -7.8,
        "m2_hi": 6.5,
        "z": 0.36,
        "z_lo": -0.15,
        "z_hi": 0.13,
    },
    {
        "m1": 54.7,
        "m1_lo": -12.8,
        "m1_hi": 12.7,
        "m2": 30.2,
        "m2_lo": -10.2,
        "m2_hi": 11.9,
        "z": 0.44,
        "z_lo": -0.19,
        "z_hi": 0.24,
    },
)
_DEV_RNG_SEED = 20260717
_Z90 = 1.6449  # 90% CI half-width in sigmas (matches posterior_propagation._Z90)


@lru_cache(maxsize=1)
def calibration_constant() -> float:
    """Candidate 2's single global constant: median(R_dev / R_mech(M_dev)) on GWTC-1."""
    ratios = [r_dev / r_mech(m_det) for m_det, r_dev in _DEV_POINTS]
    return float(np.median(ratios))


def _split_normal(median: float, lower: float, upper: float, n: int, rng: np.random.Generator) -> np.ndarray:
    s_lo = abs(lower) / _Z90 if lower else 1e-9
    s_hi = abs(upper) / _Z90 if upper else 1e-9
    z = rng.standard_normal(n)
    return median + np.where(z < 0, z * s_lo, z * s_hi)


def _dev_posterior_mdet(draws_per_event: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct GWTC-1 development posterior M_det draws paired with point R_dev.

    Uses the SAME split-normal machinery as posterior_propagation; per-draw R is
    the event's frozen point recovery (no per-draw matched filter exists for the
    development set), so the curve is calibrated to the development MASS
    posterior. Deterministic seed.
    """
    rng = np.random.default_rng(_DEV_RNG_SEED)
    m_dets: list[float] = []
    r_vals: list[float] = []
    for (_, r_dev), ci in zip(_DEV_POINTS, _DEV_POSTERIOR_CI, strict=True):
        m1 = _split_normal(ci["m1"], ci["m1_lo"], ci["m1_hi"], draws_per_event, rng)
        m2 = _split_normal(ci["m2"], ci["m2_lo"], ci["m2_hi"], draws_per_event, rng)
        z = _split_normal(ci["z"], ci["z_lo"], ci["z_hi"], draws_per_event, rng)
        m1, m2 = np.maximum(m1, m2), np.minimum(m1, m2)
        m1 = np.clip(m1, 1.0, None)
        m2 = np.clip(m2, 1.0, None)
        z = np.clip(z, 1e-3, None)
        m_det = (m1 + m2) * (1 + z)
        m_dets.extend(m_det.tolist())
        r_vals.extend([r_dev] * draws_per_event)
    return np.asarray(m_dets), np.asarray(r_vals)


def _logistic(m_det: float | np.ndarray, params: Sequence[float]) -> float | np.ndarray:
    lvl, k, log_m0 = params
    return lvl / (1.0 + np.exp(k * (np.log10(m_det) - log_m0)))


@lru_cache(maxsize=1)
def curve_params() -> tuple[float, float, float]:
    """Candidate 3's monotone-decreasing logistic fit on GWTC-1 development posteriors.

    R = L / (1 + exp(k (log10 M_det - log10 M0))), k >= 0 (monotone decreasing),
    least-squares on the reconstructed development posterior draws.
    """
    from scipy.optimize import least_squares  # noqa: PLC0415

    m_dets, r_vals = _dev_posterior_mdet()

    def resid(params: np.ndarray) -> np.ndarray:
        return _logistic(m_dets, params) - r_vals

    # init: L~1, k~2 (decreasing), log10 M0 ~ log10(60)
    result = least_squares(
        resid,
        x0=np.array([1.0, 2.0, math.log10(60.0)]),
        bounds=(np.array([0.5, 0.0, 1.0]), np.array([1.2, 20.0, 2.6])),
    )
    lvl, k, log_m0 = result.x
    return float(lvl), float(k), float(log_m0)


# --- pluggable predictor registry: predict(m1, m2, z) -> float ---------------
def _m_det(mass_1_source: float, mass_2_source: float, redshift: float) -> float:
    return (mass_1_source + mass_2_source) * (1.0 + redshift)


def predict_r_hat_baseline(mass_1_source: float, mass_2_source: float, redshift: float) -> float:
    """Baseline: the withdrawn r_hat step predictor (positive control -> 54/100)."""
    return _r_hat_bins(_m_det(mass_1_source, mass_2_source, redshift))


def predict_r_mech(mass_1_source: float, mass_2_source: float, redshift: float) -> float:
    """Candidate 1: pure mechanism, zero fitted parameters."""
    return r_mech(_m_det(mass_1_source, mass_2_source, redshift))


def predict_r_mech_cal(mass_1_source: float, mass_2_source: float, redshift: float) -> float:
    """Candidate 2: R_mech scaled by one global calibration constant, clipped to [0, 1]."""
    value = calibration_constant() * r_mech(_m_det(mass_1_source, mass_2_source, redshift))
    return float(min(max(value, 0.0), 1.0))


def predict_r_curve(mass_1_source: float, mass_2_source: float, redshift: float) -> float:
    """Candidate 3: monotone logistic curve fit on development posteriors."""
    return float(_logistic(_m_det(mass_1_source, mass_2_source, redshift), curve_params()))


PredictorFn = Callable[[float, float, float], float]

PREDICTORS: dict[str, PredictorFn] = {
    "r_hat_baseline": predict_r_hat_baseline,
    "r_mech": predict_r_mech,
    "r_mech_cal": predict_r_mech_cal,
    "r_curve": predict_r_curve,
}

# frozen grading order for the candidate family (stop at first pass)
CANDIDATE_ORDER: tuple[str, ...] = ("r_mech", "r_mech_cal", "r_curve")


def get_predictor(name: str) -> PredictorFn:
    if name not in PREDICTORS:
        raise KeyError(f"unknown predictor {name!r}; known: {sorted(PREDICTORS)}")
    return PREDICTORS[name]
