#!/usr/bin/env python3
"""GWTC-1 inspiral-only template efficacy sweep (preregistered).

Executes docs/research/preregistrations/2026-07-12-gwtc1-taylorf2-efficacy.md:
one validated matched-filter configuration, ten BBH events, TaylorF2 3.5PN
templates at the locked catalog masses, recovery fraction R vs detector-frame
total mass, with the three locked hypotheses evaluated exactly as written.
Single pass; the study registers regardless of outcome.
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
REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "platforms" / "backend" / "apps" / "backend" / "src"))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_PREREG = "docs/research/preregistrations/2026-07-12-gwtc1-taylorf2-efficacy.md"

# Locked table (transcription of the committed preregistration)
EVENTS: list[dict[str, Any]] = [
    {"name": "GW170608", "gps": 1180922494.5, "published_snr": 15.4, "m1": 11.0, "m2": 7.6, "z": 0.07},
    {"name": "GW151226", "gps": 1135136350.6, "published_snr": 13.1, "m1": 13.7, "m2": 7.7, "z": 0.09},
    {"name": "GW151012", "gps": 1128678900.4, "published_snr": 10.0, "m1": 23.2, "m2": 13.6, "z": 0.21},
    {"name": "GW170104", "gps": 1167559936.6, "published_snr": 13.0, "m1": 30.8, "m2": 20.0, "z": 0.20},
    {"name": "GW170814", "gps": 1186741861.5, "published_snr": 17.2, "m1": 30.6, "m2": 25.2, "z": 0.12},
    {"name": "GW170809", "gps": 1186302519.8, "published_snr": 12.4, "m1": 35.0, "m2": 23.8, "z": 0.20},
    {"name": "GW150914", "gps": 1126259462.4, "published_snr": 25.2, "m1": 35.6, "m2": 30.6, "z": 0.09},
    {"name": "GW170818", "gps": 1187058327.1, "published_snr": 11.3, "m1": 35.4, "m2": 26.7, "z": 0.21},
    {"name": "GW170823", "gps": 1187529256.5, "published_snr": 11.5, "m1": 39.5, "m2": 29.0, "z": 0.35},
    {"name": "GW170729", "gps": 1185389807.3, "published_snr": 10.8, "m1": 50.2, "m2": 34.0, "z": 0.49},
]
_LOW_MASS_CUTOFF = 30.0
_H1_THRESHOLD = 0.85
_H2_RHO_MAX = -0.6
_OFFSOURCE_MAX = 8.0
_ANCHOR = {"name": "GW170817", "m_total_det": 2.78, "recovery_fraction": round(30.48 / 32.4, 3)}


def _load_instrument():  # noqa: ANN202
    spec = importlib.util.spec_from_file_location("mf_instrument", _HERE / "matched_filter_gw150914.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    mf._BAND = (30.0, 2048.0)
    return mf


def _offsource_candidates(gps: float) -> list[tuple[float, float]]:
    return [
        (gps - 272.0, gps - 240.0),
        (gps + 240.0, gps + 272.0),
        (gps - 528.0, gps - 496.0),
        (gps + 496.0, gps + 528.0),
    ]


def _run_event(mf, taylorf2, event: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN001
    m_total_det = (event["m1"] + event["m2"]) * (1 + event["z"])
    mc_source = (event["m1"] * event["m2"]) ** 0.6 / (event["m1"] + event["m2"]) ** 0.2
    mc_det = mc_source * (1 + event["z"])
    n_samples = 131072  # 32 s @ 4096 Hz

    template = taylorf2.taylorf2_time_domain(
        n_samples=n_samples,
        sample_rate=4096.0,
        chirp_mass_det_msun=mc_det,
        mass1_msun=event["m1"],
        mass2_msun=event["m2"],
        f_low=30.0,
    )
    template_sha = hashlib.sha256(template.tobytes()).hexdigest()

    mf._EVENT = event["name"]
    mf._CATALOG_GPS = event["gps"]
    mf._ON_SOURCE = (event["gps"] - 16.0, event["gps"] + 16.0)
    mf._fetch_template = lambda: (template, template_sha)

    row: dict[str, Any] = {
        "event": event["name"],
        "m_total_det": round(m_total_det, 1),
        "chirp_mass_det": round(mc_det, 3),
        "published_snr": event["published_snr"],
        "f_isco_hz": round(
            1.0
            / (
                6.0**1.5
                * np.pi
                * (mc_det / ((event["m1"] * event["m2"] / (event["m1"] + event["m2"]) ** 2) ** 0.6) * 4.925491e-6)
            ),
            1,
        ),
    }

    # H3 off-source control with the mechanical fallback chain
    control = None
    for segment in _offsource_candidates(event["gps"]):
        try:
            data = mf._fetch_strain("H1", segment)
            if np.isnan(data).any():
                continue
            mf._OFF_SOURCE = segment
            control = mf.run_control()
            break
        except Exception:  # noqa: BLE001,S112 - fallback chain is mechanical
            continue
    if control is None:
        row["status"] = "data_unavailable"
        return row
    row["offsource_max"] = control["network_snr_max_offsource"]
    row["h3_valid"] = bool(control["network_snr_max_offsource"] < _OFFSOURCE_MAX)
    if not row["h3_valid"]:
        row["status"] = "instrument_invalid_no_verdict"
        return row

    confirm = mf.run_confirm()
    recovered = float(confirm["network_snr"])
    row.update(
        {
            "recovered_snr": recovered,
            "recovery_fraction": round(recovered / event["published_snr"], 3),
            "h1_peak_gps": confirm["h1"]["peak_gps"],
            "l1_peak_gps": confirm["l1"]["peak_gps"],
            "status": "measured",
        },
    )
    return row


def main() -> int:
    from scipy.stats import spearmanr  # noqa: PLC0415

    mf = _load_instrument()
    spec = importlib.util.spec_from_file_location("taylorf2", _HERE / "taylorf2.py")
    taylorf2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(taylorf2)

    rows = []
    for event in EVENTS:
        row = _run_event(mf, taylorf2, event)
        rows.append(row)
        print(
            f"{row['event']}: M_det={row['m_total_det']} f_isco={row.get('f_isco_hz')} "
            f"published={row['published_snr']} recovered={row.get('recovered_snr', '-')} "
            f"R={row.get('recovery_fraction', '-')} [{row['status']}]",
            flush=True,
        )

    measured = [r for r in rows if r["status"] == "measured"]
    low_mass = [r for r in measured if r["m_total_det"] < _LOW_MASS_CUTOFF]
    h1_pass = bool(low_mass) and all(r["recovery_fraction"] >= _H1_THRESHOLD for r in low_mass)
    masses = [r["m_total_det"] for r in measured]
    fractions = [r["recovery_fraction"] for r in measured]
    rho, pvalue = spearmanr(masses, fractions)
    h2_pass = bool(rho <= _H2_RHO_MAX)

    study = {
        "receipt_type": "gwtc1_taylorf2_efficacy_sweep",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "anchor_bns": _ANCHOR,
        "rows": rows,
        "n_measured": len(measured),
        "hypotheses": {
            "H1_low_mass_adequacy": {
                "criterion": f"R >= {_H1_THRESHOLD} for M_det < {_LOW_MASS_CUTOFF}",
                "events": [r["event"] for r in low_mass],
                "passed": h1_pass,
            },
            "H2_mass_dependence": {
                "criterion": f"spearman rho <= {_H2_RHO_MAX}",
                "rho": round(float(rho), 3),
                "p_value": round(float(pvalue), 5),
                "passed": h2_pass,
            },
            "H3_validity": {
                "criterion": f"off-source max < {_OFFSOURCE_MAX} per event",
                "excluded_events": [r["event"] for r in rows if r["status"] != "measured"],
            },
        },
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"GWTC1_taylorf2_sweep_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["hypotheses"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
