#!/usr/bin/env python3
"""Study 2: aligned-spin TaylorF2 sweep (preregistered).

Executes docs/research/preregistrations/2026-07-12-gwtc1-aligned-spin.md:
the Study-1 sweep re-run with chi_eff in the 1.5PN phasing, evaluating the
locked differential predictions P1/P2/P3 against Study 1's receipts.
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
_PREREG = "docs/research/preregistrations/2026-07-12-gwtc1-aligned-spin.md"

# Locked spins (transcription of the committed preregistration)
CHI_EFF: dict[str, float] = {
    "GW150914": -0.01,
    "GW151012": 0.05,
    "GW151226": 0.18,
    "GW170104": -0.04,
    "GW170608": 0.03,
    "GW170729": 0.37,
    "GW170809": 0.08,
    "GW170814": 0.07,
    "GW170818": -0.09,
    "GW170823": 0.09,
}
_P1_EVENT, _P1_MIN = "GW151226", 0.75
_P2_EVENTS = ("GW150914", "GW170104", "GW170608", "GW151012")  # |chi_eff| <= 0.05
_P2_MAX_DELTA = 0.05
_P3_RHO_MAX = -0.6


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    from scipy.stats import spearmanr  # noqa: PLC0415

    sweep = _load("gwtc1_taylorf2_sweep")
    taylorf2 = _load("taylorf2")
    mf = sweep._load_instrument()

    # zero-spin regression (preregistered gate before any run)
    ref = taylorf2.taylorf2_time_domain(
        n_samples=131072, sample_rate=4096.0, chirp_mass_det_msun=9.7, mass1_msun=13.7, mass2_msun=7.7, f_low=30.0
    )
    reg = taylorf2.taylorf2_time_domain(
        n_samples=131072,
        sample_rate=4096.0,
        chirp_mass_det_msun=9.7,
        mass1_msun=13.7,
        mass2_msun=7.7,
        f_low=30.0,
        chi_eff=0.0,
    )
    regression_diff = float(np.max(np.abs(ref - reg)))
    if regression_diff >= 1e-12:
        raise SystemExit(f"zero-spin regression FAILED ({regression_diff}) - no run")

    # Study-1 baseline rows from its receipt
    study1_path = sorted(_RECEIPT_DIR.glob("GWTC1_taylorf2_sweep_*.json"))[-1]
    study1 = json.loads(study1_path.read_text())
    baseline = {r["event"]: r for r in study1["rows"] if r.get("status") == "measured"}

    # patched template builder: same call path, chi_eff injected per event
    original_builder = taylorf2.taylorf2_time_domain

    def _run_all() -> list[dict[str, Any]]:
        rows = []
        for event in sweep.EVENTS:
            chi = CHI_EFF[event["name"]]

            def spun_builder(_chi: float = chi, **kwargs: Any) -> np.ndarray:  # noqa: ANN401
                return original_builder(**kwargs, chi_eff=_chi)

            taylorf2.taylorf2_time_domain = spun_builder
            try:
                row = sweep._run_event(mf, taylorf2, event)
            finally:
                taylorf2.taylorf2_time_domain = original_builder
            row["chi_eff"] = chi
            base = baseline.get(event["name"], {})
            if row.get("status") == "measured" and base:
                row["r_zero_spin"] = base["recovery_fraction"]
                row["delta_r"] = round(row["recovery_fraction"] - base["recovery_fraction"], 3)
            rows.append(row)
            print(
                f"{row['event']}: chi={chi:+.2f} R_spin={row.get('recovery_fraction', '-')} "
                f"R_zero={row.get('r_zero_spin', '-')} dR={row.get('delta_r', '-')} [{row['status']}]",
                flush=True,
            )
        return rows

    rows = _run_all()
    measured = [r for r in rows if r["status"] == "measured"]

    p1_row = next((r for r in measured if r["event"] == _P1_EVENT), None)
    p1_pass = bool(p1_row and p1_row["recovery_fraction"] >= _P1_MIN)
    p2_rows = [r for r in measured if r["event"] in _P2_EVENTS and "delta_r" in r]
    p2_pass = bool(p2_rows) and all(abs(r["delta_r"]) < _P2_MAX_DELTA for r in p2_rows)
    rho, pvalue = spearmanr([r["m_total_det"] for r in measured], [r["recovery_fraction"] for r in measured])
    p3_pass = bool(rho <= _P3_RHO_MAX)

    study = {
        "receipt_type": "gwtc1_aligned_spin_study",
        "preregistration": _PREREG,
        "generated_at": datetime.now(UTC).isoformat(),
        "zero_spin_regression_max_diff": regression_diff,
        "baseline_receipt": study1_path.name,
        "rows": rows,
        "predictions": {
            "P1_spinning_event_recovers": {
                "criterion": f"R({_P1_EVENT}) >= {_P1_MIN}",
                "r_spin": p1_row.get("recovery_fraction") if p1_row else None,
                "r_zero_spin": p1_row.get("r_zero_spin") if p1_row else None,
                "passed": p1_pass,
            },
            "P2_differential_control": {
                "criterion": f"|dR| < {_P2_MAX_DELTA} for {list(_P2_EVENTS)}",
                "deltas": {r["event"]: r["delta_r"] for r in p2_rows},
                "passed": p2_pass,
            },
            "P3_mass_trend_persists": {
                "criterion": f"spearman rho <= {_P3_RHO_MAX}",
                "rho": round(float(rho), 3),
                "p_value": round(float(pvalue), 5),
                "passed": p3_pass,
            },
        },
        "can_influence_belief": False,
    }
    body = json.dumps(study, indent=2, default=str)
    study["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"GWTC1_aligned_spin_{stamp}.json"
    path.write_text(json.dumps(study, indent=2, default=str), encoding="utf-8")
    print(json.dumps(study["predictions"], indent=1, default=str))
    print("receipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
