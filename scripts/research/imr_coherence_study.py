#!/usr/bin/env python3
"""Study 5: coherence-controlled IMR test on heavy BBH (preregistered).

Executes docs/research/preregistrations/2026-07-12-imr-coherence-controlled.md:
hybrid vs phase-scrambled twin on the 14 heavy events. Q2 is the decisive
control - a norm artifact survives phase scrambling, coherent physics does not.
The frozen protocol's Q3 OOS wording remains provenance; new receipts identify
the reused GWTC-3 rows as a cross-catalog development arm.
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
_CHECKPOINT = _RECEIPT_DIR / "IMR_coherence_checkpoint.json"
_PREREG = "docs/research/preregistrations/2026-07-12-imr-coherence-controlled.md"
_BASE_SEED = 20260712

_Q1_MEDIAN_MIN = 0.65
_Q2_MEDIAN_MARGIN = 0.10
_Q2_MIN_EVENTS = 6
_Q3_MEDIAN_MIN = 0.408  # baseline 0.258 + locked +0.15


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _measure(mf, sweep, event: dict[str, Any], template: np.ndarray) -> dict[str, Any]:  # noqa: ANN001
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
    if control["network_snr_max_offsource"] >= 8.0:
        return {"status": "instrument_invalid_no_verdict", "offsource_max": control["network_snr_max_offsource"]}
    confirm = mf.run_confirm()
    return {
        "status": "measured",
        "offsource_max": control["network_snr_max_offsource"],
        "recovered_snr": float(confirm["network_snr"]),
    }


def main() -> int:
    imr = _load("imr_ansatz")
    study4 = _load("imr_heavy_study")
    sweep = _load("gwtc1_taylorf2_sweep")
    mf = sweep._load_instrument()

    g_a = imr.anchor_tripwire()
    g_b = imr.inspiral_limit_regression()
    if not (g_a["passed"] and g_b["passed"]):
        raise SystemExit("integrity gates failed - no run")

    checkpoint: dict[str, Any] = json.loads(_CHECKPOINT.read_text()) if _CHECKPOINT.is_file() else {}
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    done = {r["event"] for r in rows}

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
            hybrid = imr.imr_time_domain(**kwargs)
            event_seed = _BASE_SEED ^ zlib.adler32(event["name"].encode())
            scrambled = imr.imr_time_domain(**kwargs, scramble_added_band_seed=event_seed)

            hybrid_out = _measure(mf, sweep, event, hybrid)
            scrambled_out = _measure(mf, sweep, event, scrambled)
            row: dict[str, Any] = {
                "event": event["name"],
                "group": group,
                "baseline_r": event["baseline"],
                "published_snr": event["published_snr"],
                "scramble_seed": event_seed,
            }
            if hybrid_out["status"] == "measured" and scrambled_out["status"] == "measured":
                r_h = round(hybrid_out["recovered_snr"] / event["published_snr"], 3)
                r_s = round(scrambled_out["recovered_snr"] / event["published_snr"], 3)
                row.update(
                    {
                        "status": "measured",
                        "r_hybrid": r_h,
                        "r_scrambled": r_s,
                        "coherence_margin": round(r_h - r_s, 3),
                    },
                )
            else:
                row["status"] = hybrid_out["status"] if hybrid_out["status"] != "measured" else scrambled_out["status"]
            rows.append(row)
            _CHECKPOINT.write_text(json.dumps({"rows": rows}, indent=1, default=str))
            print(
                f"[{group}] {row['event']}: R_hyb={row.get('r_hybrid', '-')} R_scr={row.get('r_scrambled', '-')} "
                f"margin={row.get('coherence_margin', '-')} [{row['status']}]",
                flush=True,
            )

    expected = len(study4.HEAVY_GWTC1) + len(study4.HEAVY_GWTC3)
    if len({r["event"] for r in rows}) < expected:
        print("checkpointed; re-run to continue")
        return 0

    heavy1 = [r for r in rows if r["group"] == "heavy_gwtc1" and r["status"] == "measured"]
    heavy3 = [r for r in rows if r["group"] == "heavy_gwtc3" and r["status"] == "measured"]

    q1_median = float(np.median([r["r_hybrid"] for r in heavy1]))
    q1_pass = q1_median >= _Q1_MEDIAN_MIN
    q2_margin_median = float(np.median([r["coherence_margin"] for r in heavy1]))
    q2_wins = sum(1 for r in heavy1 if r["r_hybrid"] >= r["r_scrambled"])
    q2_pass = q2_margin_median >= _Q2_MEDIAN_MARGIN and q2_wins >= _Q2_MIN_EVENTS
    q3_median = float(np.median([r["r_hybrid"] for r in heavy3]))
    q3_margin = float(np.median([r["coherence_margin"] for r in heavy3]))
    q3_pass = q3_median >= _Q3_MEDIAN_MIN and q3_margin >= _Q2_MEDIAN_MARGIN

    study = {
        "receipt_type": "imr_coherence_study",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "gates": {"G_a": g_a["passed"], "G_b": g_b["passed"]},
        "rows": rows,
        "predictions": {
            "Q1_heavy_recovery": {
                "criterion": f"median R_hybrid >= {_Q1_MEDIAN_MIN}",
                "median": round(q1_median, 3),
                "passed": q1_pass,
            },
            "Q2_coherence_control": {
                "criterion": f"median margin >= +{_Q2_MEDIAN_MARGIN} AND hybrid wins >= {_Q2_MIN_EVENTS}/7",
                "median_margin": round(q2_margin_median, 3),
                "hybrid_wins": f"{q2_wins}/7",
                "passed": q2_pass,
            },
            "Q3_cross_catalog_development_arm": {
                "criterion": f"median R_hybrid >= {_Q3_MEDIAN_MIN} AND margin >= +{_Q2_MEDIAN_MARGIN}",
                "median": round(q3_median, 3),
                "median_margin": round(q3_margin, 3),
                "passed": q3_pass,
            },
        },
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"IMR_coherence_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["predictions"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
