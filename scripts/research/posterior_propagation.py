#!/usr/bin/env python3
"""Parameter-posterior uncertainty propagation for the Study-3 OOS mass trend (referee item 4).

The frozen studies treat catalog masses/redshift as fixed point values. The referee
noted this omits posterior uncertainty and that multiplying separate posterior medians
by (1+z) is not the posterior median detector-frame mass. This propagates per-parameter
posteriors into M_det, f_ISCO, R, and the Spearman rho for the Study-3 out-of-sample
cohort (the arm that carries the locked O1/O2 criteria).

Scope: study3_oos. The event set, spin-extended TaylorF2 template family (locked chi_eff),
and R_hat(M_det) band predictor are the ones locked in
docs/research/preregistrations/2026-07-12-gwtc3-out-of-sample.md and executed by
scripts/research/gwtc3_oos_study.py. This runner does NOT re-open that single-pass study
or re-derive its measured cohort; it reuses the locked verdict-bearing event set and
propagates posterior uncertainty through the identical pipeline.

Posterior model: from the GWOSC eventapi median + asymmetric 90% CI (mass_1_source,
mass_2_source, redshift) we build a two-piece (split) normal marginal per parameter and
draw samples. M_det and f_ISCO propagate closed-form on the samples; R is recomputed per
draw by rebuilding the Study-2 spin-extended TaylorF2 template at the locked chi_eff and
matched-filtering it against the (gwpy-cached) on-source strain; rho is bootstrapped over
joint draws. Predicted recovery per draw is the locked band predictor R_hat evaluated at
the per-draw detector-frame total mass (the predictor is a locked function of M_det, so
posterior mass uncertainty propagates through it too). Honest limitation: these are
MARGINAL posteriors (m1,m2,z correlations not captured) from the GWTC catalog release; the
joint posterior would need the per-event PESummary HDF5 files. belief_moved=false; no new
pipeline, cached strain.

Usage:
  python3 scripts/research/posterior_propagation.py --smoke      # 2 events, N=5 (wiring only)
  python3 scripts/research/posterior_propagation.py --draws 100  # full (background); v1 needs >=100
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_CHECKPOINT = _RECEIPT_DIR / "POSTERIOR_prop_checkpoint.json"
_Z90 = 1.6449  # 90% CI half-width in sigmas (one-sided 95th percentile)
_SEED = 20260713
_RNG = np.random.default_rng(_SEED)
_ANALYSIS_SCOPE = "study3_oos"
_SCHEMA = "aigis.gw.posterior_uncertainty.v1"
_PREREG = "docs/research/preregistrations/2026-07-12-gwtc3-out-of-sample.md"

# Study-3 OOS verdict-bearing cohort, LOCKED by the single-pass preregistered study
# (scripts/research/gwtc3_oos_study.py): the 15 events that survived the O3 availability
# rule and the per-event off-source validity gate (offsource max < 8). The 5 excluded
# events (GW200302, GW200224, GW200112, GW191216, GW191204_110529) are documented
# data_unavailable / instrument_invalid and carry no verdict. Reusing this locked set
# respects the study's one-pass stopping rule; it is not re-derived here. Cross-check:
# docs/research/papers/gw-inspiral-template-efficacy/verification/study3_coincidence.json.
_MEASURED_COHORT = frozenset(
    {
        "GW200316_215756",
        "GW200311_115853",
        "GW200225_060421",
        "GW200220_124850",
        "GW200219_094415",
        "GW200202_154313",
        "GW200128_022011",
        "GW191230_180458",
        "GW191222_033537",
        "GW191215_223052",
        "GW191204_171526",
        "GW191129_134029",
        "GW191127_050227",
        "GW191126_115259",
        "GW191109_010717",
    }
)


def _load(name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _eventapi(name: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"https://gwosc.org/eventapi/json/event/{name}/", timeout=45) as r:  # noqa: S310
        p = json.load(r)
    return p["events"][sorted(p["events"])[-1]]


def _posterior_inputs(inner: dict[str, Any]) -> dict[str, float]:
    """The exact eventapi median + asymmetric 90% CI offsets that define the split-normal."""
    out: dict[str, float] = {}
    for p in ("mass_1_source", "mass_2_source", "redshift"):
        out[p] = float(inner[p])
        out[f"{p}_lower"] = float(inner[f"{p}_lower"])
        out[f"{p}_upper"] = float(inner[f"{p}_upper"])
    return out


def _split_normal(median: float, lower: float, upper: float, n: int) -> np.ndarray:
    """Two-piece normal from median + asymmetric 90% CI offsets (lower<0, upper>0)."""
    s_lo = abs(lower) / _Z90 if lower else 1e-9
    s_hi = abs(upper) / _Z90 if upper else 1e-9
    z = _RNG.standard_normal(n)
    return median + np.where(z < 0, z * s_lo, z * s_hi)


def _draws(inputs: dict[str, float], n: int) -> dict[str, np.ndarray]:
    out = {}
    for p in ("mass_1_source", "mass_2_source", "redshift"):
        out[p] = _split_normal(inputs[p], inputs[f"{p}_lower"], inputs[f"{p}_upper"], n)
    # physicality: m1>=m2>0, z>0
    m1, m2, z = out["mass_1_source"], out["mass_2_source"], out["redshift"]
    m1, m2 = np.maximum(m1, m2), np.minimum(m1, m2)
    out["mass_1_source"], out["mass_2_source"] = np.clip(m1, 1.0, None), np.clip(m2, 1.0, None)
    out["redshift"] = np.clip(z, 1e-3, None)
    return out


def _recovery(mf, taylorf2, event: dict[str, Any], m1: float, m2: float, z: float) -> float:  # noqa: ANN001
    """Recovery fraction for one posterior draw: net matched-filter SNR / published SNR.

    Identical statistic to the Study-2/3 confirm path (matched_filter run_confirm): on-source
    32 s segment, band [30, 2048] Hz, Welch mean 4 s PSD, on-source peak window. The template
    is the Study-2 spin-extended TaylorF2 at the locked event chi_eff, rebuilt at the draw's
    detector-frame chirp mass.
    """
    mc_det = (m1 * m2) ** 0.6 / (m1 + m2) ** 0.2 * (1 + z)
    template = taylorf2.taylorf2_time_domain(
        n_samples=131072,
        sample_rate=4096.0,
        chirp_mass_det_msun=mc_det,
        mass1_msun=m1,
        mass2_msun=m2,
        f_low=30.0,
        chi_eff=float(event["chi"]),
    )
    on = (event["gps"] - 16.0, event["gps"] + 16.0)
    mf._EVENT, mf._CATALOG_GPS, mf._ON_SOURCE = event["name"], event["gps"], on
    h1 = mf._detector_snr("H1", on, template, fft_seconds=mf._WELCH_FFT_S, psd_average="mean", peak_mode="on_source")
    l1 = mf._detector_snr("L1", on, template, fft_seconds=mf._WELCH_FFT_S, psd_average="mean", peak_mode="on_source")
    return float(mf._network_statistic(h1, l1)["value"]) / event["published_snr"]


def _pct(a: np.ndarray) -> list[float]:
    return [round(float(np.percentile(a, q)), 4) for q in (5, 50, 95)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=40)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    sweep = _load("gwtc1_taylorf2_sweep")
    taylorf2 = _load("taylorf2")
    oos = _load("gwtc3_oos_study")
    mf = sweep._load_instrument()

    events = [e for e in oos.SAMPLE if e["name"] in _MEASURED_COHORT]
    if args.smoke:
        events = events[:2]
    n = 5 if args.smoke else args.draws

    # Resume only a checkpoint that matches this scope AND draw count; a stale checkpoint
    # from a different event set or N would silently pollute the joint-draw grid.
    checkpoint: dict[str, Any] = {}
    if _CHECKPOINT.is_file() and not args.smoke:
        candidate = json.loads(_CHECKPOINT.read_text())
        if candidate.get("scope") == _ANALYSIS_SCOPE and candidate.get("n_draws") == n:
            checkpoint = candidate
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}

    for event in events:
        if event["name"] in done:
            continue
        inner = _eventapi(event["name"])
        inputs = _posterior_inputs(inner)
        d = _draws(inputs, n)
        m1d, m2d, zd = d["mass_1_source"], d["mass_2_source"], d["redshift"]
        m_det = (m1d + m2d) * (1 + zd)
        naive_point = (inputs["mass_1_source"] + inputs["mass_2_source"]) * (1 + inputs["redshift"])
        r_draws = np.array([_recovery(mf, taylorf2, event, m1d[i], m2d[i], zd[i]) for i in range(n)])
        row = {
            "event": event["name"],
            "chi_eff": float(event["chi"]),
            "published_snr": float(event["published_snr"]),
            "posterior_inputs": inputs,
            "m_det_naive_point": round(naive_point, 2),
            "m_det_posterior_pct_5_50_95": _pct(m_det),
            "r_posterior_pct_5_50_95": _pct(r_draws),
            "m1_draws": [round(float(x), 6) for x in m1d],
            "m2_draws": [round(float(x), 6) for x in m2d],
            "z_draws": [round(float(x), 6) for x in zd],
            "m_det_draws": [round(float(x), 4) for x in m_det],
            "r_draws": [round(float(x), 6) for x in r_draws],
        }
        rows.append(row)
        p = row["m_det_posterior_pct_5_50_95"]
        rp = row["r_posterior_pct_5_50_95"]
        print(f"{event['name']:16s} M_det naive={naive_point:6.1f} post[5/50/95]={p} R[5/50/95]={rp}", flush=True)
        if not args.smoke:
            _CHECKPOINT.write_text(json.dumps({"scope": _ANALYSIS_SCOPE, "n_draws": n, "rows": rows}, indent=2))

    # posterior-source hash: binds the eventapi medians + 90% CI offsets that define the
    # split-normal marginals, plus the draw-model constants. This is what "the posterior
    # inputs" are; it is independent of the sampled realizations.
    source_inputs = {
        "posterior_model": "split_normal_marginal_eventapi_90ci",
        "z90_sigma_half_width": _Z90,
        "rng_seed": _SEED,
        "events": {r["event"]: r["posterior_inputs"] for r in sorted(rows, key=lambda r: r["event"])},
    }
    posterior_source_sha256 = hashlib.sha256(
        json.dumps(source_inputs, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Flatten to per-(event, draw) rows with the SAME joint draw IDs across every event.
    draws: list[dict[str, Any]] = []
    for row in rows:
        for i in range(n):
            m1i, m2i, zi = row["m1_draws"][i], row["m2_draws"][i], row["z_draws"][i]
            m_det_i = (m1i + m2i) * (1 + zi)
            draws.append(
                {
                    "event": row["event"],
                    "draw_id": f"draw_{i:04d}",
                    "mass_1_source": m1i,
                    "mass_2_source": m2i,
                    "redshift": zi,
                    "recovery_fraction": row["r_draws"][i],
                    "predicted_recovery": oos.r_hat(m_det_i),
                }
            )

    # bootstrap rho over joint realizations (draw i across all events)
    rho_samples = []
    mae_samples = []
    for i in range(n):
        masses = [r["m_det_draws"][i] for r in rows]
        recov = [r["r_draws"][i] for r in rows]
        preds = [oos.r_hat((r["m1_draws"][i] + r["m2_draws"][i]) * (1 + r["z_draws"][i])) for r in rows]
        rho_samples.append(spearmanr(masses, recov)[0])
        mae_samples.append(float(np.median([abs(rc - pr) for rc, pr in zip(recov, preds, strict=True)])))
    rho_arr = np.array(rho_samples)
    mae_arr = np.array(mae_samples)

    body = {
        "schema": _SCHEMA,
        "analysis_scope": _ANALYSIS_SCOPE,
        "receipt_type": "posterior_uncertainty_propagation",
        "belief_moved": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "preregistration": _PREREG,
        "posterior_model": "two-piece normal from eventapi median + 90% CI (marginal, GWTC release)",
        "predicted_recovery_source": "gwtc3_oos_study.r_hat evaluated per-draw at M_det (locked OOS band predictor)",
        "posterior_source_sha256": posterior_source_sha256,
        "posterior_source_inputs": source_inputs,
        "n_draws": n,
        "n_events": len(rows),
        "draws": draws,
        "event_summary": [
            {k: v for k, v in r.items() if not k.endswith("_draws") and k != "posterior_inputs"} for r in rows
        ],
        "spearman_rho_pct_5_50_95": _pct(rho_arr),
        "median_abs_error_pct_5_50_95": _pct(mae_arr),
        "rho_all_below_zero": bool(np.all(rho_arr < 0)),
        "draws_preserving_rho_le_-0.5": round(float(np.mean(rho_arr <= -0.5)), 4),
        "draws_preserving_median_abs_error_le_0.15": round(float(np.mean(mae_arr <= 0.15)), 4),
        "max_naive_vs_posterior_median_m_det_dev": round(
            max(abs(r["m_det_naive_point"] - r["m_det_posterior_pct_5_50_95"][1]) for r in rows), 3
        ),
    }
    body["receipt_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = _RECEIPT_DIR / f"POSTERIOR_prop_{'smoke_' if args.smoke else ''}{stamp}.json"
    out.write_text(json.dumps(body, indent=2))
    print(
        f"\nSpearman rho posterior [5/50/95] = {body['spearman_rho_pct_5_50_95']}  all<0: {body['rho_all_below_zero']}"
    )
    print(f"median|R-Rhat| posterior [5/50/95] = {body['median_abs_error_pct_5_50_95']}")
    print(
        f"draws preserving rho<=-0.5: {body['draws_preserving_rho_le_-0.5']}  "
        f"median|R-Rhat|<=0.15: {body['draws_preserving_median_abs_error_le_0.15']}"
    )
    print(f"receipt: {out}\nposterior_source_sha256: {posterior_source_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
