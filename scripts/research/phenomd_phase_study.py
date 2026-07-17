#!/usr/bin/env python3
"""Study 6: sourced-PhenomD phase on heavy BBH (preregistered).

Executes docs/research/preregistrations/2026-07-12-phenomd-sourced-phase.md:
the Study-4 amplitude with the sourced PhenomD phase, vs a phase-scrambled
twin (S2 coherence control) and head-to-head against the locked Study-5
continued-TaylorF2 hybrid per-event values (S4, the decisive phase question).
The frozen S3 OOS label remains provenance; new receipts identify these reused
GWTC-3 events as a cross-catalog development arm.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_CHECKPOINT = _RECEIPT_DIR / "PHENOMD_phase_checkpoint.json"
_PREREG = "docs/research/preregistrations/2026-07-12-phenomd-sourced-phase.md"
_BASE_SEED = 20260712

_S1_MEDIAN_MIN = 0.65
_S2_MEDIAN_MARGIN = 0.10
_S2_MIN_WINS = 6
_S3_MEDIAN_MIN = 0.408

# Locked Study-5 hybrid per-event recoveries (receipt
# IMR_coherence_20260712T025157Z.json) - the S4 pairing baseline.
_STUDY5_R_HYBRID = {
    "GW170104": 0.540,
    "GW170814": 0.513,
    "GW170809": 0.608,
    "GW150914": 0.417,
    "GW170818": 0.473,
    "GW170823": 0.551,
    "GW170729": 0.631,
    "GW200220_124850": 0.559,
    "GW200219_094415": 0.584,
    "GW200128_022011": 0.542,
    "GW191222_033537": 0.566,
    "GW191127_050227": 0.607,
    "GW191109_010717": 0.518,
}


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _measure(mf, sweep, event: dict[str, Any], template: np.ndarray, *, validate_first: bool = False) -> dict[str, Any]:  # noqa: ANN001
    template_sha = hashlib.sha256(template.tobytes()).hexdigest()
    mf._EVENT = event["name"]
    mf._CATALOG_GPS = event["gps"]
    mf._ON_SOURCE = (event["gps"] - 16.0, event["gps"] + 16.0)
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
    validation = None
    if validate_first:
        validation = mf.run_validate()
        if not validation["instrument_valid"]:
            return {"status": "injection_validation_failed", "validation": validation}
    if control["network_snr_max_offsource"] >= 8.0:
        return {"status": "instrument_invalid_no_verdict", "offsource_max": control["network_snr_max_offsource"]}
    confirm = mf.run_confirm()
    out = {
        "status": "measured",
        "offsource_max": control["network_snr_max_offsource"],
        "recovered_snr": float(confirm["network_snr"]),
    }
    if validation is not None:
        out["injection_validation"] = {
            k: validation[k] for k in ("recovered_snr", "peak_time_offset_ms", "instrument_valid")
        }
    return out


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
        raise SystemExit("G6 integrity gates failed - no run")

    checkpoint: dict[str, Any] = json.loads(_CHECKPOINT.read_text()) if _CHECKPOINT.is_file() else {}
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}
    validated_once = checkpoint.get("validated_once", False)

    for group, events in (("heavy_gwtc1", study4.HEAVY_GWTC1), ("heavy_gwtc3", study4.HEAVY_GWTC3)):
        for event in events:
            if event["name"] in done:
                continue
            m1, m2, z, chi = study4._event_masses(event)
            mc_det = (m1 * m2) ** 0.6 / (m1 + m2) ** 0.2 * (1 + z)
            kwargs = {
                "n_samples": 131072,
                "sample_rate": 4096.0,
                "chirp_mass_det_msun": mc_det,
                "mass1_msun": m1,
                "mass2_msun": m2,
                "f_low": 30.0,
                "chi_eff": chi,
            }
            template = pp.phenomd_time_domain(**kwargs)
            event_seed = _BASE_SEED ^ zlib.adler32(event["name"].encode())
            scrambled = pp.phenomd_time_domain(**kwargs, scramble_added_band_seed=event_seed)

            main_out = _measure(mf, sweep, event, template, validate_first=not validated_once)
            if main_out["status"] == "injection_validation_failed":
                print(json.dumps(main_out, indent=1, default=str))
                raise SystemExit("G6-e injection validation failed - no on-source runs")
            if main_out["status"] == "measured" and not validated_once:
                validated_once = True
            scrambled_out = _measure(mf, sweep, event, scrambled)
            row: dict[str, Any] = {
                "event": event["name"],
                "group": group,
                "baseline_r": event["baseline"],
                "study5_r_hybrid": _STUDY5_R_HYBRID.get(event["name"]),
                "published_snr": event["published_snr"],
                "scramble_seed": event_seed,
            }
            if main_out["status"] == "measured" and scrambled_out["status"] == "measured":
                r_p = round(main_out["recovered_snr"] / event["published_snr"], 3)
                r_s = round(scrambled_out["recovered_snr"] / event["published_snr"], 3)
                row.update(
                    {
                        "status": "measured",
                        "r_phenomd": r_p,
                        "r_scrambled": r_s,
                        "coherence_margin": round(r_p - r_s, 3),
                        "delta_vs_study5": round(r_p - row["study5_r_hybrid"], 3)
                        if row["study5_r_hybrid"] is not None
                        else None,
                    },
                )
                if "injection_validation" in main_out:
                    row["injection_validation"] = main_out["injection_validation"]
            else:
                row["status"] = main_out["status"] if main_out["status"] != "measured" else scrambled_out["status"]
            rows.append(row)
            _CHECKPOINT.write_text(json.dumps({"rows": rows, "validated_once": validated_once}, indent=1, default=str))
            print(
                f"[{group}] {row['event']}: R_phD={row.get('r_phenomd', '-')} R_scr={row.get('r_scrambled', '-')} "
                f"margin={row.get('coherence_margin', '-')} dS5={row.get('delta_vs_study5', '-')} [{row['status']}]",
                flush=True,
            )

    expected = len(study4.HEAVY_GWTC1) + len(study4.HEAVY_GWTC3)
    if len({r["event"] for r in rows}) < expected:
        print("checkpointed; re-run to continue")
        return 0

    heavy1 = [r for r in rows if r["group"] == "heavy_gwtc1" and r["status"] == "measured"]
    heavy3 = [r for r in rows if r["group"] == "heavy_gwtc3" and r["status"] == "measured"]

    s1_median = float(np.median([r["r_phenomd"] for r in heavy1]))
    s1_pass = s1_median >= _S1_MEDIAN_MIN
    s2_margin = float(np.median([r["coherence_margin"] for r in heavy1]))
    s2_wins = sum(1 for r in heavy1 if r["r_phenomd"] >= r["r_scrambled"])
    s2_pass = s2_margin >= _S2_MEDIAN_MARGIN and s2_wins >= _S2_MIN_WINS
    s3_median = float(np.median([r["r_phenomd"] for r in heavy3]))
    s3_margin = float(np.median([r["coherence_margin"] for r in heavy3]))
    s3_pass = s3_median >= _S3_MEDIAN_MIN and s3_margin >= _S2_MEDIAN_MARGIN

    s4 = {}
    for name, group_rows in (("heavy_gwtc1", heavy1), ("heavy_gwtc3", heavy3)):
        deltas = [r["delta_vs_study5"] for r in group_rows if r["delta_vs_study5"] is not None]
        s4[name] = {
            "n_paired": len(deltas),
            "median_delta": round(float(np.median(deltas)), 3) if deltas else None,
            "passed": bool(deltas and float(np.median(deltas)) > 0.0),
        }
    s4_pass = all(v["passed"] for v in s4.values())

    study = {
        "receipt_type": "phenomd_phase_study",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "gates": {name: g["passed"] for name, g in gates["gates"].items()},
        "rows": rows,
        "predictions": {
            "S1_heavy_recovery": {
                "criterion": f"median R_phenomd >= {_S1_MEDIAN_MIN}",
                "median": round(s1_median, 3),
                "passed": s1_pass,
            },
            "S2_coherence_control": {
                "criterion": f"median margin >= +{_S2_MEDIAN_MARGIN} AND wins >= {_S2_MIN_WINS}/7",
                "median_margin": round(s2_margin, 3),
                "wins": f"{s2_wins}/{len(heavy1)}",
                "passed": s2_pass,
            },
            "S3_cross_catalog_development_arm": {
                "criterion": f"median R_phenomd >= {_S3_MEDIAN_MIN} AND margin >= +{_S2_MEDIAN_MARGIN}",
                "median": round(s3_median, 3),
                "median_margin": round(s3_margin, 3),
                "passed": s3_pass,
            },
            "S4_head_to_head_vs_study5": {
                "criterion": "median per-event (R_S6 - R_S5) > 0 on each event set",
                **s4,
                "passed": s4_pass,
            },
        },
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"PHENOMD_phase_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["predictions"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
