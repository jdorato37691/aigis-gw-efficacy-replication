#!/usr/bin/env python3
"""Study 3: GWTC-3 out-of-sample test (preregistered, checkpointed).

Executes docs/research/preregistrations/2026-07-12-gwtc3-out-of-sample.md:
the spin-extended TaylorF2 pipeline scored on 20 seeded unseen GWTC-3 events
against the locked GWTC-1-derived predictor curve. Checkpoints after every
event so interrupted runs resume without re-measuring.
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
_CHECKPOINT = _RECEIPT_DIR / "GWTC3_oos_checkpoint.json"
_PREREG = "docs/research/preregistrations/2026-07-12-gwtc3-out-of-sample.md"

# Locked sample (transcription of the committed preregistration)
SAMPLE: list[dict[str, Any]] = [
    {"name": "GW200316_215756", "gps": 1268431094.1, "published_snr": 10.3, "m_det": 25.5, "chi": 0.13},
    {"name": "GW200311_115853", "gps": 1267963151.3, "published_snr": 17.8, "m_det": 76.1, "chi": -0.02},
    {"name": "GW200302_015811", "gps": 1267149509.5, "published_snr": 10.8, "m_det": 74.0, "chi": 0.01},
    {"name": "GW200225_060421", "gps": 1266645879.3, "published_snr": 12.5, "m_det": 40.6, "chi": -0.12},
    {"name": "GW200224_222234", "gps": 1266618172.4, "published_snr": 20.0, "m_det": 96.0, "chi": 0.10},
    {"name": "GW200220_124850", "gps": 1266238148.1, "published_snr": 8.5, "m_det": 110.9, "chi": -0.07},
    {"name": "GW200219_094415", "gps": 1266140673.1, "published_snr": 10.7, "m_det": 102.7, "chi": -0.08},
    {"name": "GW200202_154313", "gps": 1264693411.5, "published_snr": 10.8, "m_det": 19.0, "chi": 0.04},
    {"name": "GW200128_022011", "gps": 1264213229.9, "published_snr": 10.6, "m_det": 116.7, "chi": 0.12},
    {"name": "GW200112_155838", "gps": 1262879936.0, "published_snr": 19.8, "m_det": 79.2, "chi": 0.06},
    {"name": "GW191230_180458", "gps": 1261764316.4, "published_snr": 10.4, "m_det": 146.0, "chi": -0.05},
    {"name": "GW191222_033537", "gps": 1261020955.1, "published_snr": 12.5, "m_det": 120.5, "chi": -0.04},
    {"name": "GW191216_213338", "gps": 1260567236.4, "published_snr": 18.6, "m_det": 21.2, "chi": 0.11},
    {"name": "GW191215_223052", "gps": 1260484270.3, "published_snr": 11.2, "m_det": 58.1, "chi": -0.04},
    {"name": "GW191204_171526", "gps": 1259514944.0, "published_snr": 17.4, "m_det": 22.7, "chi": 0.16},
    {"name": "GW191204_110529", "gps": 1259492747.5, "published_snr": 8.9, "m_det": 62.3, "chi": 0.05},
    {"name": "GW191129_134029", "gps": 1259070047.1, "published_snr": 13.1, "m_det": 20.2, "chi": 0.06},
    {"name": "GW191127_050227", "gps": 1258866165.5, "published_snr": 9.2, "m_det": 120.9, "chi": 0.18},
    {"name": "GW191126_115259", "gps": 1258804397.6, "published_snr": 8.3, "m_det": 26.5, "chi": 0.21},
    {"name": "GW191109_010717", "gps": 1257296855.2, "published_snr": 17.3, "m_det": 140.0, "chi": -0.29},
]


# Locked predictor (GWTC-1 in-sample only)
def r_hat(m_det: float) -> float:
    if m_det < 30.0:
        return 0.849
    if m_det < 70.0:
        return 0.554
    if m_det < 100.0:
        return 0.428
    return 0.210


_O1_RHO_MAX = -0.5
_O2_MAE_MAX = 0.15


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_event(mf, taylorf2, sweep, event: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN001
    """One OOS event through the spin-extended pipeline (Study-2 configuration)."""
    # masses for eta: infer a plausible split from M_det via equal-mass
    # assumption? NO - eta matters. Use catalog masses: fetch once from the
    # eventapi (metadata endpoint fixed 2026-07-12) and cache in the row.
    import urllib.request  # noqa: PLC0415

    with urllib.request.urlopen(f"https://gwosc.org/eventapi/json/event/{event['name']}/", timeout=45) as resp:  # noqa: S310
        payload = json.load(resp)
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

    mf._EVENT = event["name"]
    mf._CATALOG_GPS = event["gps"]
    mf._ON_SOURCE = (event["gps"] - 16.0, event["gps"] + 16.0)
    mf._fetch_template = lambda: (template, template_sha)

    row: dict[str, Any] = {
        "event": event["name"],
        "m_det": event["m_det"],
        "chi_eff": event["chi"],
        "published_snr": event["published_snr"],
        "r_hat": r_hat(event["m_det"]),
    }

    # on-source availability (O3 rule): NaN-free H1+L1 required
    try:
        for det in ("H1", "L1"):
            data = mf._fetch_strain(det, mf._ON_SOURCE)
            if np.isnan(data).any():
                row["status"] = "data_unavailable"
                return row
    except Exception:  # noqa: BLE001
        row["status"] = "data_unavailable"
        return row

    control = None
    for segment in sweep._offsource_candidates(event["gps"]):
        try:
            data = mf._fetch_strain("H1", segment)
            if np.isnan(data).any():
                continue
            l1 = mf._fetch_strain("L1", segment)
            if np.isnan(l1).any():
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
    row.update(
        {
            "recovered_snr": recovered,
            "recovery_fraction": round(recovered / event["published_snr"], 3),
            "abs_error_vs_r_hat": round(abs(recovered / event["published_snr"] - row["r_hat"]), 3),
            "status": "measured",
        },
    )
    return row


def main() -> int:
    from scipy.stats import spearmanr  # noqa: PLC0415

    sweep = _load("gwtc1_taylorf2_sweep")
    taylorf2 = _load("taylorf2")
    mf = sweep._load_instrument()

    checkpoint: dict[str, Any] = {}
    if _CHECKPOINT.is_file():
        checkpoint = json.loads(_CHECKPOINT.read_text())

    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}
    for event in SAMPLE:
        if event["name"] in done:
            continue
        row = _run_event(mf, taylorf2, sweep, event)
        rows.append(row)
        _CHECKPOINT.write_text(json.dumps({"rows": rows}, indent=1, default=str))
        print(
            f"{row['event']}: M={row['m_det']} chi={row['chi_eff']:+.2f} "
            f"R={row.get('recovery_fraction', '-')} r_hat={row['r_hat']} [{row['status']}]",
            flush=True,
        )

    if len({r["event"] for r in rows}) < len(SAMPLE):
        print("checkpointed; re-run to continue")
        return 0

    measured = [r for r in rows if r["status"] == "measured"]
    rho, pvalue = spearmanr([r["m_det"] for r in measured], [r["recovery_fraction"] for r in measured])
    mae_median = float(np.median([r["abs_error_vs_r_hat"] for r in measured]))
    o1_pass = bool(rho <= _O1_RHO_MAX)
    o2_pass = bool(mae_median <= _O2_MAE_MAX)

    study = {
        "receipt_type": "gwtc3_oos_study",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "n_measured": len(measured),
        "excluded": [r["event"] for r in rows if r["status"] != "measured"],
        "predictions": {
            "O1_trend_generalizes": {
                "criterion": f"spearman rho <= {_O1_RHO_MAX}",
                "rho": round(float(rho), 3),
                "p_value": round(float(pvalue), 6),
                "passed": o1_pass,
            },
            "O2_curve_predicts": {
                "criterion": f"median |R - r_hat| <= {_O2_MAE_MAX}",
                "median_abs_error": round(mae_median, 3),
                "passed": o2_pass,
            },
        },
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"GWTC3_oos_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["predictions"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
