#!/usr/bin/env python3
"""Study 4: IMR hybrid ansatz on the heavy-BBH deficit (preregistered).

Executes docs/research/preregistrations/2026-07-12-imr-ansatz-heavy-events.md:
gates G-a/G-b/G-c first, then the 7 heavy GWTC-1 events (P1), the 2 low-mass
no-degradation controls (P2), and the reused 7-event GWTC-3 cross-catalog
development arm (P3). The frozen preregistration retains its historical OOS
label; new receipts use the corrected cohort description.
Checkpointed; single pass; registers regardless of outcome.
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

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_CHECKPOINT = _RECEIPT_DIR / "IMR_heavy_checkpoint.json"
_PREREG = "docs/research/preregistrations/2026-07-12-imr-ansatz-heavy-events.md"

# Locked sets (transcription of the committed preregistration).
# Baselines are Study 2 (GWTC-1) / Study 3 (GWTC-3) spin-template recoveries.
HEAVY_GWTC1: list[dict[str, Any]] = [
    {
        "name": "GW170104",
        "gps": 1167559936.6,
        "published_snr": 13.0,
        "m1": 30.8,
        "m2": 20.0,
        "z": 0.20,
        "chi": -0.04,
        "baseline": 0.480,
    },
    {
        "name": "GW170814",
        "gps": 1186741861.5,
        "published_snr": 17.2,
        "m1": 30.6,
        "m2": 25.2,
        "z": 0.12,
        "chi": 0.07,
        "baseline": 0.554,
    },
    {
        "name": "GW170809",
        "gps": 1186302519.8,
        "published_snr": 12.4,
        "m1": 35.0,
        "m2": 23.8,
        "z": 0.20,
        "chi": 0.08,
        "baseline": 0.261,
    },
    {
        "name": "GW150914",
        "gps": 1126259462.4,
        "published_snr": 25.2,
        "m1": 35.6,
        "m2": 30.6,
        "z": 0.09,
        "chi": -0.01,
        "baseline": 0.445,
    },
    {
        "name": "GW170818",
        "gps": 1187058327.1,
        "published_snr": 11.3,
        "m1": 35.4,
        "m2": 26.7,
        "z": 0.21,
        "chi": -0.09,
        "baseline": 0.410,
    },
    {
        "name": "GW170823",
        "gps": 1187529256.5,
        "published_snr": 11.5,
        "m1": 39.5,
        "m2": 29.0,
        "z": 0.35,
        "chi": 0.09,
        "baseline": 0.438,
    },
    {
        "name": "GW170729",
        "gps": 1185389807.3,
        "published_snr": 10.8,
        "m1": 50.2,
        "m2": 34.0,
        "z": 0.49,
        "chi": 0.37,
        "baseline": 0.210,
    },
]
LOW_MASS_CONTROLS: list[dict[str, Any]] = [
    {
        "name": "GW170608",
        "gps": 1180922494.5,
        "published_snr": 15.4,
        "m1": 11.0,
        "m2": 7.6,
        "z": 0.07,
        "chi": 0.03,
        "baseline": 0.909,
    },
    {
        "name": "GW151226",
        "gps": 1135136350.6,
        "published_snr": 13.1,
        "m1": 13.7,
        "m2": 7.7,
        "z": 0.09,
        "chi": 0.18,
        "baseline": 0.789,
    },
]
HEAVY_GWTC3: list[dict[str, Any]] = [
    {"name": "GW200220_124850", "gps": 1266238148.1, "published_snr": 8.5, "baseline": 0.258},
    {"name": "GW200219_094415", "gps": 1266140673.1, "published_snr": 10.7, "baseline": 0.239},
    {"name": "GW200128_022011", "gps": 1264213229.9, "published_snr": 10.6, "baseline": 0.443},
    {"name": "GW191230_180458", "gps": 1261764316.4, "published_snr": 10.4, "baseline": 0.254},
    {"name": "GW191222_033537", "gps": 1261020955.1, "published_snr": 12.5, "baseline": 0.298},
    {"name": "GW191127_050227", "gps": 1258866165.5, "published_snr": 9.2, "baseline": 0.398},
    {"name": "GW191109_010717", "gps": 1257296855.2, "published_snr": 17.3, "baseline": 0.098},
]
_P1_MEDIAN_MIN = 0.65
_P1_STRONG_MIN = 0.75
_P2_MAX_LOSS = 0.05
_P3_MEDIAN_GAIN = 0.15


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _event_masses(event: dict[str, Any]) -> tuple[float, float, float, float]:
    """(m1, m2, z, chi) - from the locked row or the eventapi for GWTC-3 rows."""
    if "m1" in event:
        return event["m1"], event["m2"], event["z"], event["chi"]
    import urllib.request  # noqa: PLC0415

    with urllib.request.urlopen(f"https://gwosc.org/eventapi/json/event/{event['name']}/", timeout=45) as resp:  # noqa: S310
        payload = json.load(resp)
    inner = payload["events"][sorted(payload["events"])[-1]]
    chi = inner.get("chi_eff")
    return (
        float(inner["mass_1_source"]),
        float(inner["mass_2_source"]),
        float(inner["redshift"]),
        float(chi if chi is not None else 0.0),
    )


def _run_event(mf, imr, sweep, event: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN001
    m1, m2, z, chi = _event_masses(event)
    mc_det = (m1 * m2) ** 0.6 / (m1 + m2) ** 0.2 * (1 + z)
    m_det = (m1 + m2) * (1 + z)

    template = imr.imr_time_domain(
        n_samples=131072,
        sample_rate=4096.0,
        chirp_mass_det_msun=mc_det,
        mass1_msun=m1,
        mass2_msun=m2,
        f_low=30.0,
        chi_eff=chi,
    )
    template_sha = hashlib.sha256(template.tobytes()).hexdigest()

    mf._EVENT = event["name"]
    mf._CATALOG_GPS = event["gps"]
    mf._ON_SOURCE = (event["gps"] - 16.0, event["gps"] + 16.0)
    mf._fetch_template = lambda: (template, template_sha)

    row: dict[str, Any] = {
        "event": event["name"],
        "m_det": round(m_det, 1),
        "chi_eff": chi,
        "published_snr": event["published_snr"],
        "baseline_r": event["baseline"],
    }

    control = None
    for segment in sweep._offsource_candidates(event["gps"]):
        try:
            h1 = mf._fetch_strain("H1", segment)
            l1 = mf._fetch_strain("L1", segment)
            if np.isnan(h1).any() or np.isnan(l1).any():
                continue
            mf._OFF_SOURCE = segment
            control = mf.run_control()
            break
        except Exception:  # noqa: BLE001,S112
            continue
    if control is None:
        row["status"] = "data_unavailable"
        return row
    row["offsource_max"] = control["network_snr_max_offsource"]
    if control["network_snr_max_offsource"] >= 8.0:
        row["status"] = "instrument_invalid_no_verdict"
        return row

    confirm = mf.run_confirm()
    recovered = float(confirm["network_snr"])
    r = round(recovered / event["published_snr"], 3)
    row.update(
        {
            "recovered_snr": recovered,
            "recovery_fraction": r,
            "delta_vs_baseline": round(r - event["baseline"], 3),
            "status": "measured",
        },
    )
    return row


def main() -> int:
    imr = _load("imr_ansatz")
    sweep = _load("gwtc1_taylorf2_sweep")
    mf = sweep._load_instrument()

    # gates G-a and G-b (hard prerequisites)
    g_a = imr.anchor_tripwire()
    g_b = imr.inspiral_limit_regression()
    if not (g_a["passed"] and g_b["passed"]):
        raise SystemExit(f"integrity gates failed: G-a={g_a['passed']} G-b={g_b['passed']} - no run")

    # G-c: instrument validation with an IMR template on off-source noise
    # (GW150914's off-source segment; injection machinery from the validated
    # instrument, template swapped for the hybrid)
    heavy_anchor = HEAVY_GWTC1[3]  # GW150914
    m1, m2, z, chi = _event_masses(heavy_anchor)
    mc_det = (m1 * m2) ** 0.6 / (m1 + m2) ** 0.2 * (1 + z)
    template = imr.imr_time_domain(
        n_samples=131072,
        sample_rate=4096.0,
        chirp_mass_det_msun=mc_det,
        mass1_msun=m1,
        mass2_msun=m2,
        f_low=30.0,
        chi_eff=chi,
    )
    mf._EVENT = "GW150914"
    mf._CATALOG_GPS = heavy_anchor["gps"]
    mf._ON_SOURCE = (heavy_anchor["gps"] - 16.0, heavy_anchor["gps"] + 16.0)
    mf._OFF_SOURCE = (heavy_anchor["gps"] - 272.0, heavy_anchor["gps"] - 240.0)
    mf._fetch_template = lambda: (template, hashlib.sha256(template.tobytes()).hexdigest())
    g_c = mf.run_validate()
    if not g_c["instrument_valid"]:
        raise SystemExit(f"G-c instrument validation failed: {g_c} - no run")
    print(
        "gates: G-a pass | G-b pass | G-c pass (recovered "
        f"{g_c['recovered_snr']}/{g_c['injected_target_snr']}, {g_c['peak_time_offset_ms']} ms)",
        flush=True,
    )

    checkpoint: dict[str, Any] = json.loads(_CHECKPOINT.read_text()) if _CHECKPOINT.is_file() else {}
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}
    for group, events in (
        ("heavy_gwtc1", HEAVY_GWTC1),
        ("low_mass_control", LOW_MASS_CONTROLS),
        ("heavy_gwtc3", HEAVY_GWTC3),
    ):
        for event in events:
            if event["name"] in done:
                continue
            row = _run_event(mf, imr, sweep, event)
            row["group"] = group
            rows.append(row)
            _CHECKPOINT.write_text(json.dumps({"rows": rows}, indent=1, default=str))
            print(
                f"[{group}] {row['event']}: R={row.get('recovery_fraction', '-')} "
                f"baseline={row['baseline_r']} d={row.get('delta_vs_baseline', '-')} [{row['status']}]",
                flush=True,
            )

    total_expected = len(HEAVY_GWTC1) + len(LOW_MASS_CONTROLS) + len(HEAVY_GWTC3)
    if len({r["event"] for r in rows}) < total_expected:
        print("checkpointed; re-run to continue")
        return 0

    heavy1 = [r for r in rows if r["group"] == "heavy_gwtc1" and r["status"] == "measured"]
    controls = [r for r in rows if r["group"] == "low_mass_control" and r["status"] == "measured"]
    heavy3 = [r for r in rows if r["group"] == "heavy_gwtc3" and r["status"] == "measured"]

    p2_pass = bool(controls) and all(r["recovery_fraction"] >= r["baseline_r"] - _P2_MAX_LOSS for r in controls)
    median_heavy1 = float(np.median([r["recovery_fraction"] for r in heavy1]))
    p1_pass = bool(heavy1) and median_heavy1 >= _P1_MEDIAN_MIN
    p1_strong = bool(heavy1) and median_heavy1 >= _P1_STRONG_MIN
    median_heavy3 = float(np.median([r["recovery_fraction"] for r in heavy3]))
    baseline_heavy3 = 0.258
    p3_pass = bool(heavy3) and (median_heavy3 - baseline_heavy3) >= _P3_MEDIAN_GAIN

    study = {
        "receipt_type": "imr_ansatz_heavy_study",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "gates": {
            "G_a": g_a,
            "G_b": g_b,
            "G_c": {
                k: g_c[k]
                for k in ("instrument_valid", "recovered_snr", "peak_time_offset_ms", "noise_baseline_max_snr")
            },
        },
        "rows": rows,
        "predictions": {
            "P1_heavy_recovery": {
                "criterion": f"median R (7 heavy GWTC-1) >= {_P1_MEDIAN_MIN} (baseline 0.438)",
                "median": round(median_heavy1, 3),
                "passed": p1_pass,
                "strong_criterion": f">= {_P1_STRONG_MIN}",
                "strong_passed": p1_strong,
            },
            "P2_no_degradation_control": {
                "criterion": f"low-mass controls lose < {_P2_MAX_LOSS}",
                "deltas": {r["event"]: r["delta_vs_baseline"] for r in controls},
                "passed": p2_pass,
            },
            "P3_cross_catalog_development_arm": {
                "criterion": f"median R (7 heavy GWTC-3) gains >= +{_P3_MEDIAN_GAIN} (baseline {baseline_heavy3})",
                "median": round(median_heavy3, 3),
                "gain": round(median_heavy3 - baseline_heavy3, 3),
                "passed": p3_pass,
            },
        },
        "can_influence_belief": False,
    }
    if not p2_pass:
        study["verdict"] = "ASSAY_INVALID_P2_ARTIFACT - no P1/P3 verdicts issued"
        study["predictions"]["P1_heavy_recovery"]["passed"] = None
        study["predictions"]["P3_cross_catalog_development_arm"]["passed"] = None

    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"IMR_heavy_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["predictions"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
