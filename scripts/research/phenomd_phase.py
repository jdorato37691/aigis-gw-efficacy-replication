#!/usr/bin/env python3
"""Sourced-PhenomD phase on the Study-4 amplitude ansatz (Study 6).

Phase model transcribed from Khan et al. 2016 (arXiv:1508.07253) via the
sha256-stamped source artifact written by ``phenomd_coefficients.py`` — no
fitted number in this file comes from memory. Regions (geometric f = Mf):

  inspiral   Mf < 0.018          psi_TF2 + (1/eta)(s1 f + 3/4 s2 f^{4/3}
                                  + 3/5 s3 f^{5/3} + 1/2 s4 f^2)   [equ:phiins]
  intermediate [0.018, 0.5 f_RD] (1/eta)(b1 f + b2 ln f - b3/3 f^{-3})
                                                                   [eqn:IntPhase]
  merger-ringdown >= 0.5 f_RD    (1/eta)(a1 f - a2/f + 4/3 a3 f^{3/4}
                                  + a4 arctan((f - a5 f_RD)/f_damp))
                                                                   [eqn:MRDPhase]

Integration constants (s0/b0/a0) are fixed by C^1 continuity at both region
boundaries, per the paper ("fixed by requiring a smooth connection"). The
amplitude is EXACTLY the Study-4 coherence-proven ansatz — this study swaps
only the phase, targeting the mechanism both preserved negatives isolated.

Deviation history (Study-6 prereg D1-D4; 2026-07-16 oracle spin-sector retry
prereg closes the spin sector):
  D1 CLOSED - psi_TF2 now carries the paper's complete aligned-spin series
     (sourced_physics.phi_tf2_two_spin, transcribed from the 1508.07253
     appendix sec:app_pncoeffs under gates W1-W4).
  D2 f_RD/f_damp inputs are caller-provided; the oracle path supplies the
     sourced Paper-1 fits (sourced_physics.remnant_sourced), narrowing D2 to
     the Berti-Cardoso-Will fitted QNM conversion.
  D3 CLOSED - phenomd_psi accepts two aligned spins (chi1z, chi2z); the
     default keeps chi1 = chi2 = chi_eff for committed callers.
  D4 amplitude stays the Study-4 ansatz (phase-only swap).
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_MSUN_SECONDS = 4.925491025543576e-06
_F_INS_JOIN = 0.018  # region I -> IIa boundary in Mf [tex line 999]

_ALPHA5_PHYSICAL_RANGE = (0.95, 1.05)  # paper states [0.98, 1.04] in-calibration


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pc = _load("phenomd_coefficients")
_imr = _load("imr_ansatz")
_tf2 = _load("taylorf2")
_sp = _load("sourced_physics")

_COEFFS = _pc.load_artifact()["coefficients"]


def _stitch(
    regions: list[tuple[float, Callable[[np.ndarray], np.ndarray], Callable[[float], float]]],
    boundaries: list[float],
) -> list[tuple[float, float]]:
    """C^1 connection constants (c0_i, c1_i) so phi_i + c0_i + c1_i f joins smoothly.

    ``regions`` = [(start, phi, dphi), ...] ordered; region 0 is the reference
    (c0=c1=0). At each boundary the next region gets c1 from derivative match
    and c0 from value match against the already-corrected previous region.
    """
    constants = [(0.0, 0.0)]
    for i, boundary in enumerate(boundaries):
        _, phi_prev, dphi_prev = regions[i]
        _, phi_next, dphi_next = regions[i + 1]
        c0_prev, c1_prev = constants[i]
        c1 = (dphi_prev(boundary) + c1_prev) - dphi_next(boundary)
        f_arr = np.asarray([boundary])
        value_prev = float(phi_prev(f_arr)[0]) + c0_prev + c1_prev * boundary
        c0 = value_prev - float(phi_next(f_arr)[0]) - c1 * boundary
        constants.append((c0, c1))
    return constants


def phenomd_psi(
    freqs_hz: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
    chi_eff: float,
    f_rd_hz: float,
    f_damp_hz: float,
    chi1z: float | None = None,
    chi2z: float | None = None,
) -> np.ndarray:
    """The sourced PhenomD-family Fourier phase Psi(f) on the analysis grid.

    ``chi1z``/``chi2z`` are the aligned spins of the heavier/lighter body
    (m1 >= m2). When omitted, both default to ``chi_eff`` (the committed
    single-effective-spin call convention). When provided, ``chi_eff`` is
    recomputed from them as (m1 chi1 + m2 chi2)/M and the mapping spin uses
    the source's full two-spin form chi_PN = chi_eff - (38 eta/113)(chi1+chi2)
    [1508.07253 tex line 289].
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    if chi1z is None or chi2z is None:
        chi1z = chi2z = chi_eff
    else:
        delta = float(np.sqrt(max(0.0, 1.0 - 4.0 * eta)))
        chi_eff = 0.5 * ((1.0 + delta) * chi1z + (1.0 - delta) * chi2z)
    chi_pn = chi_eff - (38.0 * eta / 113.0) * (chi1z + chi2z)
    lam = _pc.phenomd_lambda(_COEFFS, eta, chi_pn)
    f_rd = f_rd_hz * m_sec
    f_dm = f_damp_hz * m_sec
    f2 = 0.5 * f_rd

    def psi_tf2_of_mf(f: np.ndarray) -> np.ndarray:
        return _sp.phi_tf2_two_spin(
            np.asarray(f) / m_sec,
            total_mass_msun=total_mass_msun,
            eta=eta,
            chi1=chi1z,
            chi2=chi2z,
        )

    def phi_ins(f: np.ndarray) -> np.ndarray:
        f = np.asarray(f, dtype=float)
        sigma = (
            lam["sigma_1"] * f
            + 0.75 * lam["sigma_2"] * f ** (4.0 / 3.0)
            + 0.6 * lam["sigma_3"] * f ** (5.0 / 3.0)
            + 0.5 * lam["sigma_4"] * f**2
        )
        return psi_tf2_of_mf(f) + sigma / eta

    def dphi_ins(f0: float) -> float:
        step = f0 * 1e-6
        two_point = np.asarray([f0 - step, f0 + step])
        dtf2 = float(np.diff(psi_tf2_of_mf(two_point))[0]) / (2.0 * step)
        dsigma = (
            lam["sigma_1"]
            + lam["sigma_2"] * f0 ** (1.0 / 3.0)
            + lam["sigma_3"] * f0 ** (2.0 / 3.0)
            + lam["sigma_4"] * f0
        )
        return dtf2 + dsigma / eta

    def phi_int(f: np.ndarray) -> np.ndarray:
        f = np.asarray(f, dtype=float)
        return (lam["beta_1"] * f + lam["beta_2"] * np.log(f) - lam["beta_3"] / 3.0 * f**-3) / eta

    def dphi_int(f0: float) -> float:
        return (lam["beta_1"] + lam["beta_2"] / f0 + lam["beta_3"] * f0**-4) / eta

    def phi_mr(f: np.ndarray) -> np.ndarray:
        f = np.asarray(f, dtype=float)
        return (
            lam["alpha_1"] * f
            - lam["alpha_2"] / f
            + 4.0 / 3.0 * lam["alpha_3"] * f ** (3.0 / 4.0)
            + lam["alpha_4"] * np.arctan((f - lam["alpha_5"] * f_rd) / f_dm)
        ) / eta

    def dphi_mr(f0: float) -> float:
        lorentz = f_dm / (f_dm**2 + (f0 - lam["alpha_5"] * f_rd) ** 2)
        return (lam["alpha_1"] + lam["alpha_2"] * f0**-2 + lam["alpha_3"] * f0**-0.25 + lam["alpha_4"] * lorentz) / eta

    regions = [(0.0, phi_ins, dphi_ins), (_F_INS_JOIN, phi_int, dphi_int), (f2, phi_mr, dphi_mr)]
    constants = _stitch(regions, [_F_INS_JOIN, f2])

    mf = np.asarray(freqs_hz, dtype=float) * m_sec
    mf_safe = np.where(mf > 0, mf, 1e-9)
    psi = np.empty_like(mf_safe)
    masks = [mf_safe < _F_INS_JOIN, (mf_safe >= _F_INS_JOIN) & (mf_safe < f2), mf_safe >= f2]
    for mask, (start, phi, _), (c0, c1) in zip(masks, regions, constants, strict=True):
        del start
        if mask.any():
            psi[mask] = phi(mf_safe[mask]) + c0 + c1 * mf_safe[mask]
    return psi


def phenomd_time_domain(
    *,
    n_samples: int,
    sample_rate: float,
    chirp_mass_det_msun: float,
    mass1_msun: float,
    mass2_msun: float,
    f_low: float,
    chi_eff: float = 0.0,
    merger_position: float = 0.75,
    phase_model: str = "phenomd",
    scramble_added_band_seed: int | None = None,
) -> np.ndarray:
    """Study-4 amplitude ansatz with the sourced PhenomD phase (D4: phase-only swap).

    ``phase_model="tf2_continued"`` must reproduce ``imr_ansatz.imr_time_domain``
    exactly (gate G6-d): it proves the amplitude construction here is a faithful
    copy, so any Study-6 delta is attributable to the phase alone.
    ``scramble_added_band_seed`` scrambles the phase for Mf >= 0.018 — the full
    band where this model deviates from the validated inspiral (the Study-5
    coherence-twin construction, band widened to the phase-modified region).
    """
    total = mass1_msun + mass2_msun
    eta = mass1_msun * mass2_msun / total**2
    total_det = chirp_mass_det_msun / eta**0.6
    m_sec = total_det * _MSUN_SECONDS
    f_isco = 1.0 / (6.0**1.5 * np.pi * m_sec)

    scale = total_det / total
    rem = _imr.remnant_quantities(mass1_msun * scale, mass2_msun * scale, chi_eff)
    f_rd, f_damp = rem["f_rd_hz"], rem["f_damp_hz"]
    f_end = min(f_rd + 4.0 * f_damp, sample_rate / 2.0 - 1.0)

    freqs = np.fft.rfftfreq(n_samples, d=1.0 / sample_rate)
    amplitude = np.zeros_like(freqs)

    inspiral = (freqs >= f_low) & (freqs < min(f_isco, f_end))
    amplitude[inspiral] = freqs[inspiral] ** (-7.0 / 6.0)

    if f_rd > f_isco:
        a_isco = f_isco ** (-7.0 / 6.0)
        merger = (freqs >= f_isco) & (freqs < min(f_rd, f_end))
        amplitude[merger] = a_isco * (freqs[merger] / f_isco) ** (-2.0 / 3.0)
        a_rd = a_isco * (f_rd / f_isco) ** (-2.0 / 3.0)
        ringdown = (freqs >= f_rd) & (freqs <= f_end)
        lorentz = f_damp**2 / ((freqs[ringdown] - f_rd) ** 2 + f_damp**2)
        amplitude[ringdown] = a_rd * lorentz

    band = amplitude > 0
    psi = np.zeros_like(freqs)
    if phase_model == "phenomd":
        psi[band] = phenomd_psi(
            freqs[band],
            total_mass_msun=total_det,
            eta=eta,
            chi_eff=chi_eff,
            f_rd_hz=f_rd,
            f_damp_hz=f_damp,
        )
    elif phase_model == "tf2_continued":
        psi[band] = _tf2.taylorf2_phase_35pn(
            freqs[band],
            total_mass_msun=total_det,
            eta=eta,
            chi_eff=chi_eff,
        )
    else:
        raise ValueError(f"unknown phase_model: {phase_model}")

    t_c = merger_position * n_samples / sample_rate
    phase = -2.0 * np.pi * freqs * t_c - psi - np.pi / 4.0
    if scramble_added_band_seed is not None:
        rng = np.random.default_rng(scramble_added_band_seed)
        modified = band & (freqs >= _F_INS_JOIN / m_sec)
        phase[modified] = rng.uniform(0.0, 2.0 * np.pi, size=int(modified.sum()))

    h_plus_fd = amplitude * np.exp(1j * phase)
    h_cross_fd = h_plus_fd * np.exp(1j * np.pi / 2.0)
    template = np.fft.irfft(h_plus_fd, n=n_samples) + 1j * np.fft.irfft(h_cross_fd, n=n_samples)
    peak = float(np.max(np.abs(template)))
    return template / peak if peak > 0 else template


# --------------------------------------------------------------------------
# Integrity gates (all required to pass BEFORE any on-source run; Rule 26)
# --------------------------------------------------------------------------


def gate_parse_and_map(event_configs: list[tuple[float, float, float]]) -> dict[str, object]:
    """G6-a: artifact digest + parse tripwire + alpha_5 physical range per event."""
    artifact = _pc.load_artifact()
    parse_gate = _pc.integrity_check(artifact["coefficients"])
    alpha5_checks = []
    for m1, m2, chi in event_configs:
        eta = m1 * m2 / (m1 + m2) ** 2
        chi_pn = chi * (1.0 - 76.0 * eta / 113.0)
        a5 = _pc.phenomd_lambda(artifact["coefficients"], eta, chi_pn)["alpha_5"]
        alpha5_checks.append(
            {
                "eta": round(eta, 4),
                "chi_eff": chi,
                "alpha_5": round(a5, 4),
                "passed": _ALPHA5_PHYSICAL_RANGE[0] <= a5 <= _ALPHA5_PHYSICAL_RANGE[1],
            },
        )
    passed = parse_gate["passed"] and all(c["passed"] for c in alpha5_checks)
    return {"passed": passed, "parse": parse_gate["passed"], "alpha5": alpha5_checks}


def gate_stitch_positive_control() -> dict[str, object]:
    """G6-b: the C^1 stitcher fed TF2 as ALL regions must be the identity.

    If every region model IS the same smooth function, the connection
    constants must vanish and the assembled phase must equal that function —
    a stitcher that adds structure to a structureless input is broken.
    """
    total, eta, chi = 65.0, 0.247, 0.0

    def psi(f_mf: np.ndarray) -> np.ndarray:
        m_sec = total * _MSUN_SECONDS
        return _tf2.taylorf2_phase_35pn(
            np.asarray(f_mf) / m_sec,
            total_mass_msun=total,
            eta=eta,
            chi_eff=chi,
        )

    def dpsi(f0: float) -> float:
        step = f0 * 1e-6
        return float(np.diff(psi(np.asarray([f0 - step, f0 + step])))[0]) / (2.0 * step)

    regions = [(0.0, psi, dpsi), (0.018, psi, dpsi), (0.03, psi, dpsi)]
    constants = _stitch(regions, [0.018, 0.03])
    grid = np.linspace(0.01, 0.05, 4096)
    assembled = np.empty_like(grid)
    masks = [grid < 0.018, (grid >= 0.018) & (grid < 0.03), grid >= 0.03]
    for mask, (_, phi, _), (c0, c1) in zip(masks, regions, constants, strict=True):
        assembled[mask] = phi(grid[mask]) + c0 + c1 * grid[mask]
    worst = float(np.max(np.abs(assembled - psi(grid))))
    max_const = float(max(abs(v) for pair in constants for v in pair))
    return {
        "worst_identity_residual_rad": worst,
        "max_connection_constant": max_const,
        "passed": bool(worst < 1e-6 and max_const < 1e-4),
    }


def gate_c1_continuity(event_configs: list[tuple[float, float, float]]) -> dict[str, object]:
    """G6-c: assembled phase is C^1 across both boundaries for every event config."""
    rows = []
    for m1, m2, chi in event_configs:
        total = m1 + m2
        eta = m1 * m2 / total**2
        rem = _imr.remnant_quantities(m1, m2, chi)
        m_sec = total * _MSUN_SECONDS
        for boundary_mf in (_F_INS_JOIN, 0.5 * rem["f_rd_hz"] * m_sec):
            f0 = boundary_mf / m_sec
            eps = f0 * 1e-5
            grid = np.asarray([f0 - 2 * eps, f0 - eps, f0 + eps, f0 + 2 * eps])
            psi = phenomd_psi(
                grid,
                total_mass_msun=total,
                eta=eta,
                chi_eff=chi,
                f_rd_hz=rem["f_rd_hz"],
                f_damp_hz=rem["f_damp_hz"],
            )
            slope_below = float(psi[1] - psi[0]) / eps
            slope_above = float(psi[3] - psi[2]) / eps
            # extrapolate each side TO the boundary so the genuine slope does
            # not masquerade as a discontinuity; residual is O(eps^2 * psi'')
            value_below = float(psi[1]) + slope_below * eps
            value_above = float(psi[2]) - slope_above * eps
            jump = abs(value_above - value_below)
            slope_rel = abs(slope_above - slope_below) / max(abs(slope_below), 1e-12)
            rows.append(
                {
                    "eta": round(eta, 4),
                    "chi": chi,
                    "boundary_mf": round(boundary_mf, 5),
                    "value_jump_rad": jump,
                    "slope_rel_mismatch": slope_rel,
                    "passed": bool(jump < 1e-3 and slope_rel < 1e-2),
                },
            )
    return {
        "passed": all(r["passed"] for r in rows),
        "boundaries_checked": len(rows),
        "worst_slope_rel": max(r["slope_rel_mismatch"] for r in rows),
        "rows": rows,
    }


def gate_amplitude_regression() -> dict[str, object]:
    """G6-d: phase_model='tf2_continued' must reproduce imr_ansatz exactly.

    Proves the amplitude construction is a faithful copy of the Study-4/5
    coherence-proven code path, so any Study-6 delta is the phase's alone.
    """
    kwargs = {
        "n_samples": 131072,
        "sample_rate": 4096.0,
        "chirp_mass_det_msun": 30.2,
        "mass1_msun": 35.6,
        "mass2_msun": 30.6,
        "f_low": 30.0,
        "chi_eff": -0.01,
    }
    reference = _imr.imr_time_domain(**kwargs)
    copy = phenomd_time_domain(**kwargs, phase_model="tf2_continued")
    worst = float(np.max(np.abs(reference - copy)))
    return {"max_abs_diff": worst, "passed": bool(worst < 1e-12)}


def run_all_gates(event_configs: list[tuple[float, float, float]]) -> dict[str, object]:
    gates = {
        "G6_a_parse_and_map": gate_parse_and_map(event_configs),
        "G6_b_stitch_positive_control": gate_stitch_positive_control(),
        "G6_c_c1_continuity": gate_c1_continuity(event_configs),
        "G6_d_amplitude_regression": gate_amplitude_regression(),
    }
    return {"passed": all(g["passed"] for g in gates.values()), "gates": gates}


if __name__ == "__main__":
    import json

    study4 = _load("imr_heavy_study")
    configs = []
    for event in study4.HEAVY_GWTC1 + study4.HEAVY_GWTC3:
        m1, m2, _z, chi = study4._event_masses(event)
        configs.append((m1, m2, chi))
    result = run_all_gates(configs)
    slim = {
        "passed": result["passed"],
        "G6_a": result["gates"]["G6_a_parse_and_map"]["passed"],
        "G6_b": result["gates"]["G6_b_stitch_positive_control"],
        "G6_c": {
            "passed": result["gates"]["G6_c_c1_continuity"]["passed"],
            "worst_slope_rel": result["gates"]["G6_c_c1_continuity"]["worst_slope_rel"],
        },
        "G6_d": result["gates"]["G6_d_amplitude_regression"],
    }
    print(json.dumps(slim, indent=1, default=str))
