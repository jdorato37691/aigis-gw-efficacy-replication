#!/usr/bin/env python3
"""External waveform-oracle comparison: AIGIS sourced-PhenomD phase vs LALSimulation IMRPhenomD (referee item 1).

Every AIGIS waveform control so far is a SELF-injection: a template generated and
recovered by the same code. A shared convention or transcription error passes all
of them. The decisive missing test is agreement with an INDEPENDENT reference
implementation. This computes, over a preregistered parameter grid, the
noise-weighted match between the AIGIS Fourier phase (phenomd_phase.phenomd_psi,
transcribed from the arXiv:1508.07253 LaTeX) and LALSimulation's IMRPhenomD phase,
using a COMMON amplitude so the match isolates the transcribed phase, plus the
per-region phase residual after the time/phase alignment a matched filter removes.

MUST be run with the ISOLATED lal venv (prod .venv is never touched):
  ~/.aigis/research/lal_venv/bin/python scripts/research/lal_oracle_compare.py
belief_moved=false.

2026-07-16 spin-sector retry (prereg
docs/research/preregistrations/2026-07-16-phenomd-oracle-spin-sector-retry.md,
follow-up to the preserved FAIL receipt LAL_oracle_20260716T113628Z.json):
T1 the AIGIS phase now carries the complete sourced two-spin 3.5PN aligned-spin
sector; T2 f_RD/f_damp come from the sourced Paper-1 fits
(sourced_physics.remnant_sourced; narrowed D2 = BCW-fit QNM conversion vs LAL's
Berti-table interpolation); T3 the time maximization is evaluated sub-bin
(32x zero-padded correlation + parabolic peak) and BOTH the refined and the
discrete-grid match are reported per point. Grid, floor, PSD, and comparison
mode are frozen by the 2026-07-16 grid preregistration.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lal
import lalsimulation as ls
import numpy as np

_HERE = Path(__file__).resolve().parent
_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_MSUN = lal.MSUN_SI
_MPC = 1e6 * lal.PC_SI
_F_LOW, _DF = 20.0, 0.125

# Preregistered grid (m1, m2, chi_eff): light -> heavy, non-spinning -> aligned-spin.
# Locked in docs/research/preregistrations/2026-07-16-phenomd-oracle-match-grid.md
# (13 unique points; superset of the original 5). chi1z = chi2z = chi_eff (D3),
# f_min_hz = _F_LOW for every point.
GRID = [
    (36.0, 29.0, 0.0),
    (30.0, 30.0, 0.0),
    (60.0, 40.0, 0.0),
    (50.0, 45.0, 0.0),
    (50.0, 40.0, 0.2),
    (36.0, 30.0, 0.2),
    (70.0, 50.0, 0.2),
    (45.0, 40.0, 0.3),
    (80.0, 70.0, 0.3),
    (60.0, 55.0, 0.4),
    (65.0, 55.0, 0.4),
    (40.0, 35.0, 0.5),
    (55.0, 48.0, 0.6),
]

# Read-only fail-closed readiness artifact destination (v1 oracle schema).
_VERIFICATION_ARTIFACT = (
    _HERE.parent.parent
    / "docs"
    / "research"
    / "papers"
    / "gw-inspiral-template-efficacy"
    / "verification"
    / "phenomd_external_oracle.json"
)
# Code-owned oracle match floor (mirrors gw_evidence_controls.MIN_ORACLE_MATCH).
_MATCH_FLOOR = 0.99


def _load(name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _lal_fd(m1: float, m2: float, chi: float) -> tuple[np.ndarray, np.ndarray]:
    hp, _ = ls.SimInspiralChooseFDWaveform(
        m1 * _MSUN,
        m2 * _MSUN,
        0.0,
        0.0,
        chi,
        0.0,
        0.0,
        chi,
        400.0 * _MPC,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        _DF,
        _F_LOW,
        2048.0,
        _F_LOW,
        None,
        ls.IMRPhenomD,
    )
    f = np.arange(hp.data.length) * hp.deltaF
    return f, np.asarray(hp.data.data)


def _aligo_psd(freqs: np.ndarray) -> np.ndarray:
    """Analytic aLIGO ZeroDetHighPower PSD (LIGO-T0900288 / Ajith fit)."""
    x = np.maximum(freqs, _F_LOW) / 215.0
    psd = 1e-49 * (x ** (-4.14) - 5.0 * x ** (-2.0) + 111.0 * (1.0 - x**2 + 0.5 * x**4) / (1.0 + 0.5 * x**2))
    psd[freqs < _F_LOW] = np.inf
    return psd


_TIME_PAD_FACTOR = 32  # retry-prereg T3: sub-bin time-shift sampling factor


def _match(h1: np.ndarray, h2: np.ndarray, psd: np.ndarray, df: float) -> dict[str, float]:
    """Noise-weighted match, maximized over time and phase (abs).

    Returns BOTH evaluations of the same locked quantity max_t |<h1,h2>(t)|
    (retry-prereg T3): ``discrete`` = peak on the native IFFT time grid (the
    previously committed metric, bin 1/(N df)); ``refined`` = the identical
    correlation zero-padded x32 in time (same integrand, no new freedom) with
    3-point parabolic interpolation around the peak. The refinement removes
    only time-grid quantization; real phase residuals are invariant under it.
    """
    integ = h1 * np.conj(h2) / psd
    n = len(integ)
    n1 = np.sqrt(np.sum(np.abs(h1) ** 2 / psd).real)
    n2 = np.sqrt(np.sum(np.abs(h2) ** 2 / psd).real)
    if n1 <= 0 or n2 <= 0:
        return {"refined": 0.0, "discrete": 0.0}
    norm = n1 * n2
    discrete = float(np.max(np.abs(np.fft.ifft(integ))) * n / norm)
    n_pad = _TIME_PAD_FACTOR * n
    mag = np.abs(np.fft.ifft(integ, n=n_pad)) * n_pad
    k = int(np.argmax(mag))
    y1, y2, y3 = mag[(k - 1) % n_pad], mag[k], mag[(k + 1) % n_pad]
    denom = y1 - 2.0 * y2 + y3
    peak = y2 - 0.125 * (y1 - y3) ** 2 / denom if denom < 0 else y2
    refined = min(float(peak / norm), 1.0)
    return {"refined": refined, "discrete": discrete}


def _compare(pp, sp, m1: float, m2: float, chi: float) -> dict[str, Any]:  # noqa: ANN001
    f, h_lal = _lal_fd(m1, m2, chi)
    total = m1 + m2
    eta = m1 * m2 / total**2
    band = (np.abs(h_lal) > 0) & (f >= _F_LOW)
    fb = f[band]
    a_lal = np.abs(h_lal[band])
    psi_lal = np.unwrap(np.angle(h_lal[band]))

    # T2: sourced Paper-1 remnant (equal spins on this grid, Shat = chi_eff)
    rem = sp.remnant_sourced(m1, m2, chi)
    psi_aigis = pp.phenomd_psi(
        fb,
        total_mass_msun=total,
        eta=eta,
        chi_eff=chi,
        f_rd_hz=rem["f_rd_hz"],
        f_damp_hz=rem["f_damp_hz"],
        chi1z=chi,
        chi2z=chi,
    )
    psd = _aligo_psd(fb)

    # common amplitude a_lal -> the match isolates phase. Try both phase-sign
    # conventions and keep the better (a wrong sign scores ~0 -> a built-in check).
    h_ref = a_lal * np.exp(1j * psi_lal)
    by_sign = {sgn: _match(h_ref, a_lal * np.exp(sgn * 1j * psi_aigis), psd, _DF) for sgn in (1.0, -1.0)}
    sgn = 1.0 if by_sign[1.0]["refined"] >= by_sign[-1.0]["refined"] else -1.0
    best = by_sign[sgn]

    # phase residual after removing the best-fit (a + b*f) alignment a filter absorbs
    d = sgn * psi_aigis - psi_lal
    coef = np.polyfit(fb, d, 1)
    resid = d - np.polyval(coef, fb)
    # inspiral/merger split at f2 = 0.5 f_rd (the phenomd_psi intermediate boundary)
    f_split = rem["f_rd_hz"] * 0.5
    ins, mrg = fb < f_split, fb >= f_split
    return {
        "m1": m1,
        "m2": m2,
        "chi_eff": chi,
        "m_total": round(total, 1),
        "band_hz": [round(float(fb[0]), 1), round(float(fb[-1]), 1)],
        "phase_match": round(best["refined"], 5),
        "phase_match_discrete_time": round(best["discrete"], 5),
        "phase_resid_rms_rad_inspiral": round(float(np.sqrt(np.mean(resid[ins] ** 2))) if ins.any() else 0.0, 4),
        "phase_resid_rms_rad_merger": round(float(np.sqrt(np.mean(resid[mrg] ** 2))) if mrg.any() else 0.0, 4),
    }


def _oracle_environment_sha256() -> str:
    """sha256 of the sorted lal-venv package list (the oracle environment description)."""
    from importlib.metadata import distributions

    packages = sorted(f"{d.metadata['Name']}=={d.version}" for d in distributions() if d.metadata["Name"])
    return hashlib.sha256("\n".join(packages).encode("utf-8")).hexdigest()


def _oracle_artifact(rows: list[dict[str, Any]], env_sha256: str) -> dict[str, Any]:
    """Transcribe the phase-match rows into the aigis.gw.phenomd_oracle.v1 schema.

    Envelope/schema fields only; the per-row match is the noise-weighted phase
    match computed by _compare (physics unchanged). chi1z = chi2z = chi_eff (D3),
    f_min_hz = _F_LOW for every point.
    """
    return {
        "schema": "aigis.gw.phenomd_oracle.v1",
        "backend": "lalsimulation",
        "independent_implementation": True,
        "comparison_mode": "exact_phenomd",
        "oracle_environment_sha256": env_sha256,
        "match_floor": _MATCH_FLOOR,
        "reference": "LALSimulation IMRPhenomD (lalsimulation, isolated lal_venv)",
        "preregistration": "docs/research/preregistrations/2026-07-16-phenomd-oracle-match-grid.md",
        "retry_preregistration": "docs/research/preregistrations/2026-07-16-phenomd-oracle-spin-sector-retry.md",
        "provenance_notes": (
            "Reflects the CURRENT implementation after the preregistered spin-sector retry: "
            "full sourced two-spin 3.5PN aligned-spin TaylorF2 sector (T1), sourced Paper-1 "
            "remnant fits (T2), and sub-bin time-alignment evaluation of the locked match "
            "(T3; per-row 'match' is refined, 'match_discrete_time' is the prior discrete-grid "
            "evaluation). The prior honest FAIL is preserved at "
            "~/.aigis/research/gw_replication/LAL_oracle_20260716T113628Z.json and in git "
            "history (commit 2203e431a)."
        ),
        "belief_moved": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "declared_deviations": (
            "narrowed D2: Berti-Cardoso-Will fitted QNM conversion (a_f -> f_RD, f_damp) vs "
            "LAL's Berti-table interpolation; D4 common amplitude (LAL's) so the match "
            "isolates the transcribed phase"
        ),
        "rows": [
            {
                "parameters": {
                    "mass1_msun": r["m1"],
                    "mass2_msun": r["m2"],
                    "chi1z": r["chi_eff"],
                    "chi2z": r["chi_eff"],
                    "f_min_hz": _F_LOW,
                },
                "match": r["phase_match"],
                "match_discrete_time": r["phase_match_discrete_time"],
                "phase_resid_rms_rad_inspiral": r["phase_resid_rms_rad_inspiral"],
                "phase_resid_rms_rad_merger": r["phase_resid_rms_rad_merger"],
                "band_hz": r["band_hz"],
            }
            for r in rows
        ],
    }


def main() -> int:
    pp = _load("phenomd_phase")
    sp = _load("sourced_physics")
    gates = sp.run_all_gates()
    if not gates["passed"]:
        print(json.dumps(gates, indent=1, default=str))
        raise SystemExit("sourced-physics tripwire gates FAILED - retry BLOCKED, no grid run (prereg W1-W4)")
    rows = [_compare(pp, sp, *cfg) for cfg in GRID]
    for r in rows:
        print(
            f"m=({r['m1']:.0f}+{r['m2']:.0f}, chi={r['chi_eff']}): match={r['phase_match']:.4f} "
            f"(discrete {r['phase_match_discrete_time']:.4f}) "
            f"resid_rad ins={r['phase_resid_rms_rad_inspiral']:.3f} mrg={r['phase_resid_rms_rad_merger']:.3f} "
            f"band={r['band_hz']}"
        )
    body = {
        "receipt_type": "lal_oracle_phase_comparison",
        "belief_moved": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "reference": "LALSimulation IMRPhenomD (lalsuite 7.26.15, isolated venv)",
        "metric": (
            "noise-weighted phase match (common amplitude, aLIGO design PSD, max over "
            "time+phase; time max evaluated sub-bin per retry-prereg T3, discrete-grid "
            "value reported alongside)"
        ),
        "retry_preregistration": "docs/research/preregistrations/2026-07-16-phenomd-oracle-spin-sector-retry.md",
        "prior_fail_receipt": "LAL_oracle_20260716T113628Z.json (min 0.91751, commit 2203e431a)",
        "declared_deviations": (
            "narrowed D2: BCW-fit QNM conversion vs LAL Berti-table interpolation; D4 common amplitude"
        ),
        "tripwire_gates": {name: bool(g["passed"]) for name, g in gates["gates"].items()},
        "rows": rows,
        "median_phase_match": round(float(np.median([r["phase_match"] for r in rows])), 5),
        "min_phase_match": round(float(min(r["phase_match"] for r in rows)), 5),
        "median_phase_match_discrete": round(float(np.median([r["phase_match_discrete_time"] for r in rows])), 5),
        "min_phase_match_discrete": round(float(min(r["phase_match_discrete_time"] for r in rows)), 5),
    }
    body["receipt_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    out = _RECEIPT_DIR / f"LAL_oracle_{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json"
    out.write_text(json.dumps(body, indent=2))
    print(
        f"\nmedian phase match={body['median_phase_match']}  min={body['min_phase_match']}  "
        f"(discrete-grid: median={body['median_phase_match_discrete']} min={body['min_phase_match_discrete']})"
    )
    print(f"receipt: {out}\nsha256: {body['receipt_sha256']}")

    # Emit the read-only readiness artifact (aigis.gw.phenomd_oracle.v1).
    artifact = _oracle_artifact(rows, _oracle_environment_sha256())
    _VERIFICATION_ARTIFACT.write_text(json.dumps(artifact, indent=2))
    passed = body["min_phase_match"] >= _MATCH_FLOOR
    print(
        f"artifact: {_VERIFICATION_ARTIFACT}\n"
        f"min match={body['min_phase_match']} vs floor {_MATCH_FLOOR} -> "
        f"{'PASS' if passed else 'FAIL (honest negative)'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
