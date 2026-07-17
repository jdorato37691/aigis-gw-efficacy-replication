"""Study-3 coincidence gate artifact (schema aigis.gw.study3_coincidence.v1).

Fills verification gate `study3_coincidence.json`, checked by
`scripts/research/gw_package_readiness.py` via
`gw_evidence_controls.validate_study3_coincidence_artifact`.

The existing `coincidence_audit_gwtc3.py` recomputes the OOS mass-trend on the
coincident subset but its rows keep only the H1-L1 SEPARATION, not the raw
per-detector peak SNR + GPS the gate schema requires. This runner reuses the
exact same fixed pipeline (masses from the GWOSC eventapi, Study-3 TaylorF2
template, on-source mean-4s peak via `_detector_snr`) but records the raw
`h1_snr / l1_snr / h1_peak_gps / l1_peak_gps` for every measured event, so the
validator can independently recompute each event's window disposition and the
locked Study-3 mass-recovery correlation + prediction-error criteria.

Disposition, per-row content hash, and the recomputed-metrics hash are all built
with the VALIDATOR's own `independent_peak_statistic` / `_finite` /
`_content_sha256`, so the artifact binds to exactly what the gate recomputes -
no inline reimplementation that could silently drift from the assay (Rule 26).

`predicted_recovery` is the locked, pre-registered OOS band predictor
`gwtc3_oos_study.r_hat(m_det)`; `recovery_fraction` is the freshly measured
network SNR over the published network SNR. Belief unchanged (research artifact,
belief_moved=false).

Run: ~/aigis/.venv/bin/python3 scripts/research/study3_coincidence_gate.py
     (add --smoke for the first 2 events)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
_PACKAGE = _HERE.parents[1] / "docs" / "research" / "papers" / "gw-inspiral-template-efficacy"
_ARTIFACT = _PACKAGE / "verification" / "study3_coincidence.json"
_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_CKPT = _RECEIPT_DIR / "study3_gate_ckpt.json"


def _load(name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _measure_event(mf, taylorf2, sweep, event: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN001
    """Rebuild the Study-3 template and read the raw H1/L1 peak SNR + GPS.

    Applies the SAME mechanical availability + off-source validity rules as the
    primary Study-3 analysis (`gwtc3_oos_study._measure`): NaN-free on-source
    H1+L1, plus an off-source control excluded when its max network SNR reaches
    the 8.0 detection scale. This reproduces the pre-registered 16-event cohort
    (20 seeded - 3 no clean H1+L1 - 1 off-source) that the gate validates, rather
    than the looser availability-only recompute (17). Returns a dict with a
    ``status`` field; only ``measured`` rows carry the peak fields.
    """
    on_source = (event["gps"] - 16.0, event["gps"] + 16.0)
    try:
        for det in ("H1", "L1"):
            if np.isnan(mf._fetch_strain(det, on_source)).any():
                return {"event": event["name"], "status": "data_unavailable"}
    except Exception:  # noqa: BLE001
        return {"event": event["name"], "status": "data_unavailable"}
    try:
        with urllib.request.urlopen(  # noqa: S310
            f"https://gwosc.org/eventapi/json/event/{event['name']}/", timeout=45
        ) as resp:
            payload = json.load(resp)
    except Exception:  # noqa: BLE001
        return {"event": event["name"], "status": "data_unavailable"}
    inner = payload["events"][sorted(payload["events"])[-1]]
    m1, m2, z = float(inner["mass_1_source"]), float(inner["mass_2_source"]), float(inner["redshift"])
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
    template_sha = hashlib.sha256(template.tobytes()).hexdigest()
    mf._EVENT, mf._CATALOG_GPS, mf._ON_SOURCE = event["name"], event["gps"], on_source
    mf._fetch_template = lambda: (template, template_sha)

    # Off-source validity control (same rule as the primary Study-3 analysis).
    control = None
    for segment in sweep._offsource_candidates(event["gps"]):
        try:
            if np.isnan(mf._fetch_strain("H1", segment)).any() or np.isnan(mf._fetch_strain("L1", segment)).any():
                continue
            mf._OFF_SOURCE = segment
            control = mf.run_control()
            break
        except Exception:  # noqa: BLE001,S112
            continue
    if control is None:
        return {"event": event["name"], "status": "data_unavailable"}
    offsource_max = float(control["network_snr_max_offsource"])
    if offsource_max >= 8.0:
        return {
            "event": event["name"],
            "status": "instrument_invalid_no_verdict",
            "offsource_max": round(offsource_max, 4),
        }

    h1 = mf._detector_snr(
        "H1", on_source, template, fft_seconds=mf._WELCH_FFT_S, psd_average="mean", peak_mode="on_source"
    )
    l1 = mf._detector_snr(
        "L1", on_source, template, fft_seconds=mf._WELCH_FFT_S, psd_average="mean", peak_mode="on_source"
    )
    net_value = float(np.hypot(h1["snr_peak"], l1["snr_peak"]))
    return {
        "event": event["name"],
        "status": "measured",
        "h1_snr": round(float(h1["snr_peak"]), 4),
        "l1_snr": round(float(l1["snr_peak"]), 4),
        "h1_peak_gps": float(h1["peak_gps"]),
        "l1_peak_gps": float(l1["peak_gps"]),
        "m_total_det": float(event["m_det"]),
        "recovery_fraction": round(net_value / float(event["published_snr"]), 6),
        "predicted_recovery": float(event["_r_hat"]),
        "offsource_max": round(offsource_max, 4),
        "template_sha256": template_sha,
    }


def _build_artifact(ec, raw_rows: list[dict[str, Any]], source_sha: str) -> dict[str, Any]:  # noqa: ANN001
    """Assemble the gate artifact, binding digests with the validator's helpers."""
    rows: list[dict[str, Any]] = []
    audited: list[dict[str, Any]] = []
    included: list[tuple[float, float, float]] = []
    for r in raw_rows:
        result = ec.independent_peak_statistic(
            h1_snr=r["h1_snr"], l1_snr=r["l1_snr"], h1_gps=r["h1_peak_gps"], l1_gps=r["l1_peak_gps"]
        )
        disposition = "included_within_window" if result["within_coincidence_window"] else "excluded_outside_window"
        mass = ec._finite(r["m_total_det"], name="m_total_det")
        recovery = ec._finite(r["recovery_fraction"], name="recovery_fraction")
        predicted = ec._finite(r["predicted_recovery"], name="predicted_recovery")
        rows.append({**r, "analysis_disposition": disposition})
        audited.append(
            {
                "event": r["event"],
                "analysis_disposition": disposition,
                "m_total_det": mass,
                "recovery_fraction": recovery,
                "predicted_recovery": predicted,
                **result,
            }
        )
        if disposition == "included_within_window":
            included.append((mass, recovery, predicted))

    recomputed: dict[str, Any] = {
        "n_included": len(included),
        "spearman_rho": None,
        "spearman_p": None,
        "median_abs_prediction_error": None,
    }
    if len(included) >= ec.MIN_STUDY3_COINCIDENT_EVENTS:
        masses = [m for m, _, _ in included]
        recoveries = [rec for _, rec, _ in included]
        if len(set(masses)) > 1 and len(set(recoveries)) > 1:
            rho, p_value = spearmanr(masses, recoveries)
            if np.isfinite(float(rho)) and np.isfinite(float(p_value)):
                recomputed.update(
                    {
                        "spearman_rho": float(rho),
                        "spearman_p": float(p_value),
                        "median_abs_prediction_error": statistics.median(abs(rec - pred) for _, rec, pred in included),
                    }
                )
    return {
        "schema": "aigis.gw.study3_coincidence.v1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "belief_moved": False,
        "source_receipt_sha256": source_sha,
        "physical_light_travel_bound_ms": ec.H1_L1_LIGHT_TRAVEL_MS,
        "analysis_timing_margin_ms": ec.DEFAULT_TIMING_MARGIN_MS,
        "predicted_recovery_source": "gwtc3_oos_study.r_hat (locked OOS band predictor)",
        "rows": rows,
        "audited_rows_sha256": ec._content_sha256(audited),
        "recomputed_result_sha256": ec._content_sha256(recomputed),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    oos = _load("gwtc3_oos_study")
    taylorf2 = _load("taylorf2")
    sweep = _load("gwtc1_taylorf2_sweep")
    ec = _load("gw_evidence_controls")
    mf = sweep._load_instrument()

    events = list(oos.SAMPLE)[:2] if args.smoke else list(oos.SAMPLE)
    for e in events:
        e["_r_hat"] = oos.r_hat(float(e["m_det"]))

    _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt = json.loads(_CKPT.read_text()) if (_CKPT.is_file() and not args.smoke) else {}
    raw_rows: list[dict[str, Any]] = ckpt.get("rows", [])
    skipped: list[dict[str, Any]] = ckpt.get("skipped", [])
    seen = {r["event"] for r in raw_rows} | {s["event"] for s in skipped}

    for event in events:
        if event["name"] in seen:
            continue
        row = _measure_event(mf, taylorf2, sweep, event)
        if row["status"] == "measured":
            raw_rows.append(row)
            sep_ms = abs(row["h1_peak_gps"] - row["l1_peak_gps"]) * 1000.0
            print(
                f"{row['event']:18s} M={row['m_total_det']:6.1f} R={row['recovery_fraction']:.3f} "
                f"pred={row['predicted_recovery']:.3f} |H1-L1|={sep_ms:8.2f}ms "
                f"(H1 {row['h1_snr']:.2f}, L1 {row['l1_snr']:.2f}) offsrc={row['offsource_max']:.2f}",
                flush=True,
            )
        else:
            extra = f" (offsrc={row['offsource_max']:.2f})" if "offsource_max" in row else ""
            print(f"{event['name']:18s} {row['status']} (excluded){extra}", flush=True)
            skipped.append(row)
        if not args.smoke:
            _CKPT.write_text(json.dumps({"rows": raw_rows, "skipped": skipped}, indent=1))

    # Durable raw receipt -> its sha256 is the artifact's source_receipt_sha256.
    raw_receipt = {
        "receipt_type": "study3_coincidence_gate_run",
        "belief_moved": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "n_measured": len(raw_rows),
        "skipped_events": skipped,
        "rows": raw_rows,
    }
    raw_bytes = json.dumps(raw_receipt, sort_keys=True).encode("utf-8")
    source_sha = hashlib.sha256(raw_bytes).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = _RECEIPT_DIR / f"study3_coincidence_gate_{'smoke_' if args.smoke else ''}{stamp}.json"
    receipt_path.write_text(json.dumps({**raw_receipt, "receipt_sha256": source_sha}, indent=2))

    artifact = _build_artifact(ec, raw_rows, source_sha)
    if args.smoke:
        print(f"\n[smoke] {len(raw_rows)} measured, source_sha={source_sha[:16]} (artifact NOT written)")
        return 0

    _ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    _ARTIFACT.write_text(json.dumps(artifact, indent=1))
    verdict = ec.validate_study3_coincidence_artifact(artifact)
    print(
        f"\nWROTE {_ARTIFACT}\n"
        f"n_audited={verdict['n_audited']}/{verdict['n_expected']} "
        f"included={verdict['recomputed_metrics']['n_included']} "
        f"rho={verdict['recomputed_metrics']['spearman_rho']} "
        f"med_err={verdict['recomputed_metrics']['median_abs_prediction_error']}\n"
        f"digests_match: rows={verdict['audited_rows_digest_matches']} "
        f"result={verdict['recomputed_result_digest_matches']}\n"
        f"STATUS={verdict['status']} scientific_pass={verdict['scientific_pass']} "
        f"reason={verdict['reason']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
