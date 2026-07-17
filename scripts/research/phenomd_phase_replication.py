#!/usr/bin/env python3
"""Study 6 within-project robustness reproduction (preregistered protocol).

Executes docs/research/preregistrations/2026-07-12-phenomd-sourced-phase-replication.md:
re-measures the 13 confirm-pass events with the sourced-PhenomD template under
the distinct executor configuration (Welch MEDIAN PSD, 16 s segments,
``matched_filter_replicator``). Criteria R1-R3 locked; outcome recorded either
way in a local receipt. Any registry adoption is a separate governed step; this
same-project run is not an independent reproduction. The frozen R2 OOS label
remains provenance while new receipts use cross-catalog-development wording.
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
_CHECKPOINT = _RECEIPT_DIR / "PHENOMD_replication_checkpoint.json"
_PROTOCOL = "docs/research/preregistrations/2026-07-12-phenomd-sourced-phase-replication.md"
_EXPERIMENT_ID = "exp_83871cc6eeadf4d1b80ec4d8"

_R1_MEDIAN_MIN = 0.65
_R1_CONFIRM_MEDIAN = 0.902
_R1_ABS_TOL = 0.10
_R2_MEDIAN_MIN = 0.408
_R3_MEDIAN_ABS_DIFF_MAX = 0.10

# Confirm-pass per-event recoveries (receipt PHENOMD_phase_20260712T032158Z.json)
_CONFIRM_R = {
    "GW170104": 0.969,
    "GW170814": 0.865,
    "GW170809": 0.928,
    "GW150914": 0.890,
    "GW170818": 0.902,
    "GW170823": 0.955,
    "GW170729": 0.890,
    "GW200220_124850": 0.602,
    "GW200219_094415": 0.897,
    "GW200128_022011": 0.883,
    "GW191222_033537": 0.864,
    "GW191127_050227": 0.836,
    "GW191109_010717": 0.851,
}


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _measure_replicate(mf, sweep, event: dict[str, Any], template: np.ndarray) -> dict[str, Any]:  # noqa: ANN001
    template_sha = hashlib.sha256(template.tobytes()).hexdigest()
    mf._EVENT = event["name"]
    mf._CATALOG_GPS = event["gps"]
    mf._ON_SOURCE = (event["gps"] - 16.0, event["gps"] + 16.0)
    mf._PUBLISHED_NETWORK_SNR = event["published_snr"]
    mf._TOLERANCE = 0.25
    mf._fetch_template = lambda: (template, template_sha)

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
        return {"status": "data_unavailable"}
    if control["network_snr_max_offsource"] >= 8.0:
        return {"status": "instrument_invalid_no_verdict", "offsource_max": control["network_snr_max_offsource"]}
    replicate = mf.run_replicate()
    return {
        "status": "measured",
        "offsource_max": control["network_snr_max_offsource"],
        "recovered_snr": float(replicate["network_snr"]),
        "psd_estimator": replicate["psd_estimator"],
        "segment_gps": replicate["h1"]["segment_gps"],
        "template_sha256": template_sha,
    }


def main() -> int:
    pp = _load("phenomd_phase")
    study4 = _load("imr_heavy_study")
    sweep = _load("gwtc1_taylorf2_sweep")
    mf = sweep._load_instrument()

    configs = []
    for event in study4.HEAVY_GWTC1 + study4.HEAVY_GWTC3:
        m1, m2, _z, chi = study4._event_masses(event)
        configs.append((m1, m2, chi))
    gates = pp.run_all_gates(configs)
    if not gates["passed"]:
        print(json.dumps(gates, indent=1, default=str))
        raise SystemExit("G6 integrity gates failed - no replication run")

    checkpoint: dict[str, Any] = json.loads(_CHECKPOINT.read_text()) if _CHECKPOINT.is_file() else {}
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}

    for group, events in (("heavy_gwtc1", study4.HEAVY_GWTC1), ("heavy_gwtc3", study4.HEAVY_GWTC3)):
        for event in events:
            if event["name"] not in _CONFIRM_R:  # GW191230: excluded per protocol
                continue
            if event["name"] in done:
                continue
            m1, m2, z, chi = study4._event_masses(event)
            mc_det = (m1 * m2) ** 0.6 / (m1 + m2) ** 0.2 * (1 + z)
            template = pp.phenomd_time_domain(
                n_samples=131072,
                sample_rate=4096.0,
                chirp_mass_det_msun=mc_det,
                mass1_msun=m1,
                mass2_msun=m2,
                f_low=30.0,
                chi_eff=chi,
            )
            out = _measure_replicate(mf, sweep, event, template)
            row: dict[str, Any] = {
                "event": event["name"],
                "group": group,
                "published_snr": event["published_snr"],
                "r_confirm": _CONFIRM_R[event["name"]],
            }
            if out["status"] == "measured":
                r_rep = round(out["recovered_snr"] / event["published_snr"], 3)
                row.update(
                    {
                        "status": "measured",
                        "r_replicate": r_rep,
                        "abs_diff": round(abs(r_rep - row["r_confirm"]), 3),
                        "offsource_max": out["offsource_max"],
                        "psd_estimator": out["psd_estimator"],
                        "template_sha256": out["template_sha256"],
                        "segment_gps": out["segment_gps"],
                    },
                )
            else:
                row["status"] = out["status"]
            rows.append(row)
            _CHECKPOINT.write_text(json.dumps({"rows": rows}, indent=1, default=str))
            print(
                f"[{group}] {row['event']}: R_rep={row.get('r_replicate', '-')} "
                f"R_conf={row['r_confirm']} |d|={row.get('abs_diff', '-')} [{row['status']}]",
                flush=True,
            )

    if len({r["event"] for r in rows}) < len(_CONFIRM_R):
        print("checkpointed; re-run to continue")
        return 0

    heavy1 = [r for r in rows if r["group"] == "heavy_gwtc1" and r["status"] == "measured"]
    heavy3 = [r for r in rows if r["group"] == "heavy_gwtc3" and r["status"] == "measured"]
    measured = heavy1 + heavy3

    r1_median = float(np.median([r["r_replicate"] for r in heavy1]))
    r1_pass = r1_median >= _R1_MEDIAN_MIN and abs(r1_median - _R1_CONFIRM_MEDIAN) <= _R1_ABS_TOL
    r2_median = float(np.median([r["r_replicate"] for r in heavy3]))
    r2_pass = r2_median >= _R2_MEDIAN_MIN
    r3_median = float(np.median([r["abs_diff"] for r in measured]))
    r3_pass = r3_median <= _R3_MEDIAN_ABS_DIFF_MAX
    outcome = "confirmed" if (r1_pass and r2_pass and r3_pass) else "failed"

    study = {
        "receipt_type": "phenomd_phase_replication",
        "protocol": _PROTOCOL,
        "experiment_id": _EXPERIMENT_ID,
        "executor": "matched_filter_replicator",
        "generated_at": datetime.now(UTC).isoformat(),
        "gates": {name: g["passed"] for name, g in gates["gates"].items()},
        "rows": rows,
        "criteria": {
            "R1_headline": {
                "criterion": f"median heavy GWTC-1 >= {_R1_MEDIAN_MIN} AND within +/-{_R1_ABS_TOL} of {_R1_CONFIRM_MEDIAN}",
                "median": round(r1_median, 3),
                "passed": r1_pass,
            },
            "R2_cross_catalog_development_arm": {
                "criterion": f"median GWTC-3 >= {_R2_MEDIAN_MIN}",
                "median": round(r2_median, 3),
                "passed": r2_pass,
            },
            "R3_per_event_agreement": {
                "criterion": f"median |R_rep - R_conf| <= {_R3_MEDIAN_ABS_DIFF_MAX}",
                "median_abs_diff": round(r3_median, 3),
                "passed": r3_pass,
            },
        },
        "outcome": outcome,
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"PHENOMD_replication_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["criteria"], indent=1, default=str))
    print("outcome:", outcome)
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
