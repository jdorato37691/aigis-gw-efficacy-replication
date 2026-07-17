#!/usr/bin/env python3
"""PSD-estimator robustness sweep of the GWTC-1 mass trend (referee item 2).

The referee noted the recovered R is sensitive to PSD estimation, and that using
one on-source estimator for every event does not guarantee a like-for-like R
across the mass range -- so the mass trend (Spearman rho = -0.891, Study 1) could
entangle template truncation with PSD behavior. This recomputes R for all ten
GWTC-1 events under the four PSD regimes locked in
docs/research/preregistrations/2026-07-16-psd-robustness-artifact-regimes.md and
re-derives rho under each, testing whether the trend is a PSD artifact.

Regimes (schema field psd_config):
  * onsource_welch_mean_4s        -- PSD from the on-source segment, mean, 4 s.
                                     This is the Study-1 confirm config = the
                                     positive control.
  * offsource_welch_mean_4s       -- PSD from an off-source segment (mean, 4 s),
                                     used to whiten the on-source data.
  * onsource_welch_median_many_4s -- PSD from the on-source segment, median of
                                     the 15 four-second sub-segments.
  * gated_onsource_welch_mean_4s  -- loud pre-merger transients excised by the
                                     GW170817-locked mechanical gate, then PSD
                                     (mean, 4 s) and filter on the gated data.

Reuses the validated Study-1 pipeline UNCHANGED: the same taylorf2 template and
the same matched_filter_gw150914._detector_snr / _network_statistic, driven only
through the existing psd_override and _fetch_strain seams. belief_moved=false; no
new data source.

Usage: python3 scripts/research/psd_robustness_sweep.py
Writes the aigis.gw.psd_robustness.v1 artifact to the verification directory and
a sha256-stamped provenance receipt to ~/.aigis/research/gw_replication/.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import welch
from scipy.signal.windows import tukey
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_ARTIFACT_PATH = (
    _REPO_ROOT
    / "docs"
    / "research"
    / "papers"
    / "gw-inspiral-template-efficacy"
    / "verification"
    / "psd_robustness.json"
)
_PREREG = "docs/research/preregistrations/2026-07-16-psd-robustness-artifact-regimes.md"
_SCHEMA = "aigis.gw.psd_robustness.v1"

# The four required regimes, in run order (names must match REQUIRED_PSD_CONFIGS
# in gw_evidence_controls.py exactly).
_ONSOURCE_MEAN = "onsource_welch_mean_4s"
_OFFSOURCE_MEAN = "offsource_welch_mean_4s"
_ONSOURCE_MEDIAN = "onsource_welch_median_many_4s"
_GATED_MEAN = "gated_onsource_welch_mean_4s"
_REQUIRED_CONFIGS = (_ONSOURCE_MEAN, _OFFSOURCE_MEAN, _ONSOURCE_MEDIAN, _GATED_MEAN)

_FFT_SECONDS = 4.0

# Mechanical gate, values locked in 2026-07-12-gw170817-matched-filter.md and
# reused here per the 2026-07-16 addendum. window_before_tc is strictly earlier
# than the +/-0.1 s recovery peak window, so gating never touches the signal.
_GATE_RULE: dict[str, Any] = {
    "window_before_tc": (2.0, 0.5),
    "threshold_sigma": 15.0,
    "gate_half_width_s": 0.2,
    "taper_s": 0.1,
    "psd_fft_s": _FFT_SECONDS,
}


def _load(name: str, filename: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _network_recovery(
    mf,  # noqa: ANN001
    template: np.ndarray,
    published: float,
    *,
    fft: float,
    avg: str,
    psd_override_by_det: dict[str, Any] | None = None,
) -> tuple[float, dict[str, Any], dict[str, Any]]:
    override = psd_override_by_det or {}
    h1 = mf._detector_snr(
        "H1",
        mf._ON_SOURCE,
        template,
        fft_seconds=fft,
        psd_average=avg,
        peak_mode="on_source",
        psd_override=override.get("H1"),
    )
    l1 = mf._detector_snr(
        "L1",
        mf._ON_SOURCE,
        template,
        fft_seconds=fft,
        psd_average=avg,
        peak_mode="on_source",
        psd_override=override.get("L1"),
    )
    net = float(mf._network_statistic(h1, l1)["value"])
    return net / published, h1, l1


def _offsource_psd(mf, sweep, detector: str, gps: float):  # noqa: ANN001,ANN202
    """First NaN-free off-source candidate -> (welch mean 4 s PSD, segment)."""
    for segment in sweep._offsource_candidates(gps):
        try:
            data = mf._fetch_strain(detector, segment)
        except Exception:  # noqa: BLE001,S112 - mechanical fallback chain
            continue
        if np.isnan(data).any():
            continue
        return mf._psd(data, fft_seconds=_FFT_SECONDS, average="mean"), list(segment)
    return None, None


def _make_gated_fetch(mf, original_fetch, on_source, tc: float, rule, records):  # noqa: ANN001,ANN202
    """Wrap _fetch_strain to gate loud pre-merger transients on the on-source
    segment for either detector, using the locked mechanical rule."""

    def _gated(detector: str, segment):  # noqa: ANN202
        data = original_fetch(detector, segment)
        if tuple(segment) != tuple(on_source):
            return data
        fs = mf._SAMPLE_RATE
        n = len(data)
        times = segment[0] + np.arange(n) / fs
        nper = int(rule["psd_fft_s"] * fs)
        pf, psd = welch(data, fs=fs, nperseg=nper, noverlap=nper // 2)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        pv = np.interp(freqs, pf, psd)
        pv[pv <= 0] = np.inf
        white = np.fft.irfft(np.fft.rfft(data * tukey(n, 1.0 / 8.0)) / np.sqrt(pv), n=n)
        interior = (times > segment[0] + 1.0) & (times < segment[1] - 1.0)
        sigma = float(np.std(white[interior])) or 1.0
        z = np.abs(white) / sigma
        lo, hi = tc - rule["window_before_tc"][0], tc - rule["window_before_tc"][1]
        window_mask = (times >= lo) & (times <= hi)
        max_z = float(np.max(z[window_mask])) if window_mask.any() else 0.0
        record = {"detector": detector, "fired": False, "max_z_in_window": round(max_z, 2)}
        if window_mask.any() and max_z > rule["threshold_sigma"]:
            glitch_idx = int(np.argmax(z * window_mask))
            t_glitch = float(times[glitch_idx])
            half = rule["gate_half_width_s"]
            gate_mask = (times >= t_glitch - half) & (times <= t_glitch + half)
            gate_len = int(gate_mask.sum())
            inverse_tukey = 1.0 - tukey(gate_len, min(1.0, 2 * rule["taper_s"] / (2 * half)))
            data = data.copy()
            data[gate_mask] = data[gate_mask] * inverse_tukey
            record.update({"fired": True, "t_glitch_gps": round(t_glitch, 4)})
        records.append(record)
        return data

    return _gated


def _study1_recovery() -> dict[str, float]:
    """The Study-1 receipt recovery_fraction per event (mean-4s), for the control."""
    receipts = sorted(_RECEIPT_DIR.glob("GWTC1_taylorf2_sweep_*.json"))
    if not receipts:
        return {}
    data = json.loads(receipts[-1].read_text())
    return {r["event"]: r["recovery_fraction"] for r in data.get("rows", []) if "recovery_fraction" in r}


def main() -> int:
    sweep = _load("gwtc1_taylorf2_sweep", "gwtc1_taylorf2_sweep.py")
    taylorf2 = _load("taylorf2", "taylorf2.py")
    mf = sweep._load_instrument()  # sets band [30, 2048]
    study1 = _study1_recovery()

    rows: list[dict[str, Any]] = []
    manifest_events: list[dict[str, Any]] = []
    gate_events: list[dict[str, Any]] = []
    control_devs: list[float] = []

    for event in sweep.EVENTS:
        name = event["name"]
        gps = event["gps"]
        published = float(event["published_snr"])
        m_total_det = round((event["m1"] + event["m2"]) * (1 + event["z"]), 1)
        mc_det = (event["m1"] * event["m2"]) ** 0.6 / (event["m1"] + event["m2"]) ** 0.2 * (1 + event["z"])
        template = taylorf2.taylorf2_time_domain(
            n_samples=131072,
            sample_rate=4096.0,
            chirp_mass_det_msun=mc_det,
            mass1_msun=event["m1"],
            mass2_msun=event["m2"],
            f_low=30.0,
        )
        on_source = (gps - 16.0, gps + 16.0)
        mf._EVENT = name
        mf._CATALOG_GPS = gps
        mf._ON_SOURCE = on_source

        recoveries: dict[str, float | None] = {}

        # 1. on-source welch mean 4 s (positive control)
        r_on_mean, _, _ = _network_recovery(mf, template, published, fft=_FFT_SECONDS, avg="mean")
        recoveries[_ONSOURCE_MEAN] = round(r_on_mean, 4)

        # 2. on-source welch median (many) 4 s
        r_on_median, _, _ = _network_recovery(mf, template, published, fft=_FFT_SECONDS, avg="median")
        recoveries[_ONSOURCE_MEDIAN] = round(r_on_median, 4)

        # 3. off-source welch mean 4 s (PSD from off-source, whiten on-source)
        h1_psd, h1_seg = _offsource_psd(mf, sweep, "H1", gps)
        l1_psd, l1_seg = _offsource_psd(mf, sweep, "L1", gps)
        if h1_psd is not None and l1_psd is not None:
            r_off, _, _ = _network_recovery(
                mf,
                template,
                published,
                fft=_FFT_SECONDS,
                avg="mean",
                psd_override_by_det={"H1": h1_psd, "L1": l1_psd},
            )
            recoveries[_OFFSOURCE_MEAN] = round(r_off, 4)
        else:
            recoveries[_OFFSOURCE_MEAN] = None

        # 4. gated on-source welch mean 4 s
        original_fetch = mf._fetch_strain
        gate_records: list[dict[str, Any]] = []
        mf._fetch_strain = _make_gated_fetch(mf, original_fetch, on_source, gps, _GATE_RULE, gate_records)
        try:
            r_gated, _, _ = _network_recovery(mf, template, published, fft=_FFT_SECONDS, avg="mean")
        finally:
            mf._fetch_strain = original_fetch
        recoveries[_GATED_MEAN] = round(r_gated, 4)
        gate_events.append({"event": name, "detectors": gate_records})

        for config in _REQUIRED_CONFIGS:
            value = recoveries[config]
            if value is None:
                continue  # honest structural gap; breaks same-event-set check
            rows.append(
                {
                    "event": name,
                    "psd_config": config,
                    "m_total_det": m_total_det,
                    "recovery_fraction": value,
                    "published_snr": published,
                }
            )

        manifest_events.append(
            {
                "event": name,
                "catalog_gps": gps,
                "on_source": [on_source[0], on_source[1]],
                "offsource_h1": h1_seg,
                "offsource_l1": l1_seg,
            }
        )

        ctrl = study1.get(name)
        if ctrl is not None:
            control_devs.append(abs(ctrl - recoveries[_ONSOURCE_MEAN]))
        gate_fired = any(d.get("fired") for d in gate_records)
        print(
            f"{name:10s} M={m_total_det:6.1f}  "
            + "  ".join(
                f"{c.split('_welch_')[0]}={format(recoveries[c], '.3f') if recoveries[c] is not None else 'NA'}"
                for c in _REQUIRED_CONFIGS
            )
            + f"  gate_fired={gate_fired}  study1={ctrl}",
            flush=True,
        )

    manifest = {
        "sample_rate": 4096.0,
        "band_hz": [30.0, 2048.0],
        "on_source_halfwidth_s": 16.0,
        "offsource_psd_fft_s": _FFT_SECONDS,
        "events": manifest_events,
    }
    manifest_sha = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    # Local rho per config (informational; the validator recomputes independently).
    rho_by_config: dict[str, Any] = {}
    for config in _REQUIRED_CONFIGS:
        masses = [r["m_total_det"] for r in rows if r["psd_config"] == config]
        recs = [r["recovery_fraction"] for r in rows if r["psd_config"] == config]
        if len(set(masses)) > 1 and len(set(recs)) > 1:
            rho, p = spearmanr(masses, recs)
            rho_by_config[config] = {"rho": round(float(rho), 4), "p": float(f"{float(p):.3g}"), "n": len(masses)}
        else:
            rho_by_config[config] = {"rho": None, "p": None, "n": len(masses)}

    control_max_dev = round(max(control_devs), 4) if control_devs else None

    artifact = {
        "schema": _SCHEMA,
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "belief_moved": False,
        "can_influence_belief": False,
        "strain_manifest_sha256": manifest_sha,
        "strain_manifest": manifest,
        "psd_configs": list(_REQUIRED_CONFIGS),
        "gate_rule": {k: (list(v) if isinstance(v, tuple) else v) for k, v in _GATE_RULE.items()},
        "gate_activity": gate_events,
        "rows": rows,
        "spearman_rho_by_config": rho_by_config,
        "positive_control_onsource_mean4s_vs_study1_max_dev": control_max_dev,
    }
    artifact["artifact_sha256"] = hashlib.sha256(
        json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    _ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = _RECEIPT_DIR / f"PSD_robustness_{stamp}.json"
    receipt_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print("\nrho(M,R) by PSD config:", {k: v["rho"] for k, v in rho_by_config.items()})
    print(f"positive control (onsource_mean_4s vs Study-1) max dev: {control_max_dev}")
    print(f"artifact: {_ARTIFACT_PATH}")
    print(f"receipt:  {receipt_path}")
    print(f"strain_manifest_sha256: {manifest_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
