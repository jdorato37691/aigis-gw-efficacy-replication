#!/usr/bin/env python3
"""P2 Step B: mechanically derive the frozen prospective bands from the committed residual pool.

Executes the band-derivation PROCEDURE frozen in
docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md (committed at
`8e43efdb5` BEFORE this script runs; freeze-before-compute). This script chooses
NO parameter after seeing coverage: it loads the 48 already-measured residuals
`(R_measured - r_mech(M_det))` from three named receipts, partitions them into the
three frozen ISCO-in-band regimes, and emits the empirical [5th, 95th]-percentile
band offsets (LIGHT / INTERMEDIATE) plus the frozen R->0 sub-claim band (HEAVY,
[0, epsilon]).

Twin/again discipline: percentiles are computed two independent ways
(numpy.percentile vs. a manual sort-index interpolation) that must agree exactly;
r_mech is checked against the P1.5 receipt's stored per-row r_mech (positive
control on the extraction, Rule 26). The frozen predictor is imported read-only
and NEVER refit.

Output: docs/research/papers/gw-inspiral-template-efficacy/verification/
p2_prospective_bands.json (schema aigis.gw.p2_prospective_bands.v1,
belief_moved=false, sha256 self-bound). No network fetch: the residuals already
exist in the committed receipts.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_PREREG = "docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md"
_PREREG_COMMIT = "8e43efdb5ca6a3d29b8fddce7e938feb7beccd03"  # Step A (procedure) commit
_PREDICTOR_COMMIT = "767d93bbd576d598f81e9b16c71bdff095c97f22"  # frozen r_mech
_TEMPLATE_COMMIT_SHA256 = "4c43f31143db2a98cf53c19d8fce6f062d18c5c920cd6c4c4ca5d54a62340446"
_FROZEN_DATE = "2026-07-17"  # fixed; the table is fully deterministic (no now() -> byte-reproducible)

_OUT = (
    _HERE.parents[1]
    / "docs"
    / "research"
    / "papers"
    / "gw-inspiral-template-efficacy"
    / "verification"
    / "p2_prospective_bands.json"
)

# --- frozen band-model constants (prereg Section 3) --------------------------
_F_LOW = 30.0  # Hz, band floor  -> f_ISCO <= f_low => HEAVY (r_mech = 0)
_F_REF = 215.0  # Hz, Ajith design-PSD reference (_PSD_F0) -> f_ISCO >= f_ref => LIGHT
_EPSILON_R_TO_ZERO = 0.05  # HEAVY band = [0, epsilon]
_COVERAGE_TARGET = 0.90
_CLIP = (0.0, 1.0)
_EXTRACTION_CTRL_TOL = 0.005  # max |r_mech(m_det) - stored_r_mech| over P1.5 rows

# --- the three residual-pool receipts (prereg Section 2) ---------------------
# Study-3 located by receipt_sha256 (its filename carries a UTC stamp); the other
# two by fixed filename. Expected receipt_sha256 where the receipt stamps one.
_RECEIPTS = (
    {
        "cohort": "study3_oos",
        "filename": "GWTC3_oos_20260712T023453Z.json",
        "expected_receipt_sha256": "e38e953f1d89bc280a2ef7c7562b665129ee0e5c6f40e8c01c048f24c70ced53",
        "measured_rows_path": "rows",  # top-level rows[], filter status==measured
        "expected_measured": 15,
    },
    {
        "cohort": "o3a_fresh_holdout",
        "filename": "FRESH_HOLDOUT_eval_20260716T232341Z.json",
        "expected_receipt_sha256": None,  # this receipt stamps no receipt_sha256
        "measured_rows_path": "rows",
        "expected_measured": 7,
    },
    {
        "cohort": "p15_o4_expanded",
        "filename": "O4_EXPANDED_eval_20260717T214059Z.json",
        "expected_receipt_sha256": "82738cf926a3e2d9693df3453f3779fdb3cf604918eabcd9ab2c6570d76da020",
        "measured_rows_path": "rows",
        "expected_measured": 26,
    },
)
_COHORT_ORDER = {"study3_oos": 0, "o3a_fresh_holdout": 1, "p15_o4_expanded": 2}


def _load_module(name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _content_sha256(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _f_isco(m_det: float, c_const: float) -> float:
    return c_const / m_det


def _regime(m_det: float, c_const: float) -> str:
    """Frozen ISCO-in-band regime by f_ISCO position (prereg Section 3)."""
    f_isco = _f_isco(m_det, c_const)
    if f_isco <= _F_LOW:
        return "heavy"
    if f_isco >= _F_REF:
        return "light"
    return "intermediate"


def _percentiles_twin(residuals: list[float]) -> tuple[float, float, float]:
    """Return (q05, q95, max_twin_disagreement) via numpy and manual sort-index.

    Twin A: numpy.percentile (default linear interpolation).
    Twin B: manual sorted-index linear interpolation, re-derived independently.
    They must agree to machine precision; the observed max disagreement is
    returned for the receipt.
    """
    arr = np.asarray(residuals, dtype=float)
    q05_np = float(np.percentile(arr, 5.0))
    q95_np = float(np.percentile(arr, 95.0))

    def _manual(pct: float) -> float:
        s = sorted(float(x) for x in residuals)
        n = len(s)
        if n == 1:
            return s[0]
        rank = (pct / 100.0) * (n - 1)  # numpy 'linear' == C=1 interpolation
        lo = math.floor(rank)
        hi = min(lo + 1, n - 1)
        frac = rank - lo
        return s[lo] + frac * (s[hi] - s[lo])

    q05_manual = _manual(5.0)
    q95_manual = _manual(95.0)
    disagree = max(abs(q05_np - q05_manual), abs(q95_np - q95_manual))
    return q05_np, q95_np, disagree


def _read_receipt(spec: dict[str, Any]) -> tuple[dict[str, Any], str]:
    path = _RECEIPT_DIR / spec["filename"]
    raw = path.read_bytes()
    file_bytes_sha256 = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw)
    stamped = payload.get("receipt_sha256")
    if spec["expected_receipt_sha256"] is not None:
        if stamped != spec["expected_receipt_sha256"]:
            raise SystemExit(
                f"receipt_sha256 mismatch for {spec['cohort']}: "
                f"stamped {stamped!r} != expected {spec['expected_receipt_sha256']!r}"
            )
    return payload, file_bytes_sha256


def build() -> dict[str, Any]:
    predictor = _load_module("r_predictor")
    o4 = _load_module("o4_expanded_validation")
    c_const = 1.0 / (6.0**1.5 * math.pi * predictor._MSUN_SECONDS)

    pool: list[dict[str, Any]] = []
    receipt_meta: list[dict[str, Any]] = []
    all_event_names: set[str] = set()
    ctrl_max_delta = 0.0

    ctrl_n = 0
    for spec in _RECEIPTS:
        payload, file_sha = _read_receipt(spec)
        rows = payload[spec["measured_rows_path"]]
        for r in rows:
            all_event_names.add(str(r["event"]))
        # stored r_mech (computed by the frozen pipeline on un-rounded catalog
        # masses) lives in result.measured_rows, NOT the top-level rows[]. Build
        # an event->stored_r_mech map for the positive control (only P1.5 stamps
        # it; Study-3 / fresh-holdout graded r_hat only).
        stored_r_mech: dict[str, float] = {}
        result = payload.get("result") or {}
        for g in result.get("measured_rows", []):
            if g.get("r_mech") is not None:
                stored_r_mech[str(g["event"])] = float(g["r_mech"])
        measured = [r for r in rows if r.get("status") == "measured"]
        if len(measured) != spec["expected_measured"]:
            raise SystemExit(
                f"{spec['cohort']}: expected {spec['expected_measured']} measured rows, got {len(measured)}"
            )
        for r in measured:
            m_det = float(r["m_det"])
            recovery = float(r["recovery_fraction"])
            r_mech = float(predictor.r_mech(m_det))
            # positive control: cross-check r_mech(m_det) vs the frozen pipeline's
            # stored per-event r_mech (Rule 26). Rounding m_det to 0.1 perturbs
            # r_mech by < 0.005 (verified).
            stored_val = stored_r_mech.get(str(r["event"]))
            if stored_val is not None:
                ctrl_max_delta = max(ctrl_max_delta, abs(r_mech - stored_val))
                ctrl_n += 1
            pool.append(
                {
                    "cohort": spec["cohort"],
                    "event": str(r["event"]),
                    "m_det": m_det,
                    "R_measured": recovery,
                    "r_mech": round(r_mech, 6),
                    "residual": round(recovery - r_mech, 6),
                    "f_isco_hz": round(_f_isco(m_det, c_const), 3),
                    "regime": _regime(m_det, c_const),
                    "stored_r_mech": stored_val,
                }
            )
        receipt_meta.append(
            {
                "cohort": spec["cohort"],
                "filename": spec["filename"],
                "receipt_sha256_field": payload.get("receipt_sha256"),
                "file_bytes_sha256": file_sha,
                "n_measured": len(measured),
            }
        )

    if ctrl_n < 26:
        # the P1.5 receipt stamps 26 stored r_mech values; if the control ran on
        # fewer, it is a no-op and cannot be trusted (Rule 26).
        raise SystemExit(f"extraction positive-control is a NO-OP: only {ctrl_n} rows cross-checked (expected >= 26)")
    if ctrl_max_delta > _EXTRACTION_CTRL_TOL:
        raise SystemExit(
            f"extraction positive-control FAILED: max |r_mech(m_det) - stored_r_mech| "
            f"{ctrl_max_delta:.4f} > tol {_EXTRACTION_CTRL_TOL}"
        )

    if len(pool) != 48:
        raise SystemExit(f"expected 48 pool rows, got {len(pool)}")

    # stable, enumerable ordering
    pool.sort(key=lambda x: (_COHORT_ORDER[x["cohort"]], x["m_det"], x["event"]))

    # twin tripwire on the frozen predictor over every pool mass
    twin_r_mech = float(predictor.assert_twin([p["m_det"] for p in pool]))

    # --- per-regime bands ---------------------------------------------------
    bands: dict[str, Any] = {}
    twin_pct_max = 0.0
    for regime in ("light", "intermediate", "heavy"):
        rows = [p for p in pool if p["regime"] == regime]
        resids = [p["residual"] for p in rows]
        entry: dict[str, Any] = {
            "n": len(rows),
            "residuals": [{"event": p["event"], "m_det": p["m_det"], "residual": p["residual"]} for p in rows],
        }
        if regime == "heavy":
            # R -> 0 sub-claim: pre-committed [0, epsilon]; NOT an empirical percentile
            entry["rule"] = "[0, epsilon] (R->0 sub-claim, frozen)"
            entry["epsilon"] = _EPSILON_R_TO_ZERO
            entry["band_lo"] = 0.0
            entry["band_hi"] = _EPSILON_R_TO_ZERO
            entry["all_pool_R_measured_zero"] = all(p["R_measured"] == 0.0 for p in rows)
        else:
            if not rows:
                raise SystemExit(f"regime {regime} is empty; cannot form a percentile band")
            q05, q95, disagree = _percentiles_twin(resids)
            twin_pct_max = max(twin_pct_max, disagree)
            entry["rule"] = "point + empirical [5th,95th] residual percentile, clipped [0,1]"
            entry["band_offset_lo"] = round(q05, 6)
            entry["band_offset_hi"] = round(q95, 6)
            entry["residual_min"] = round(min(resids), 6)
            entry["residual_max"] = round(max(resids), 6)
            entry["twin_percentile_disagreement"] = disagree
        bands[regime] = entry

    # --- P2 development manifest (prereg Section 4 item 5) -------------------
    dev_names: set[str] = set(all_event_names)
    dev_names.update(o4.EXCLUSION_EVENTS)  # 42-event P1.5 exclusion set
    # all O4a/O4b eligible (cohort + cap-dropped) from the P1.5 freeze receipt
    freeze_latest = _RECEIPT_DIR / "O4_EXPANDED_freeze_latest.json"
    if freeze_latest.is_file():
        fr = json.loads(freeze_latest.read_text())
        dev_names.update(fr.get("events", []))
        dev_names.update(r["name"] for r in fr.get("cap_dropped", []))
        dev_names.update(r["name"] for r in fr.get("cohort_rows", []))
    dev_events = sorted(dev_names)
    dev_manifest = {
        "n": len(dev_events),
        "events": dev_events,
        "sha256": _content_sha256(dev_events),
        "note": (
            "union of the P1.5 42-event exclusion set, every event named in the three "
            "residual-pool receipts, and all O4a/O4b eligible+cap-dropped events; O4c "
            "cohort excludes any event whose commonName or GWYYMMDD prefix is in this set"
        ),
    }

    table: dict[str, Any] = {
        "schema": "aigis.gw.p2_prospective_bands.v1",
        "preregistration": _PREREG,
        "preregistration_commit": _PREREG_COMMIT,
        "predictor_commit": _PREDICTOR_COMMIT,
        "template_commit_sha256": _TEMPLATE_COMMIT_SHA256,
        "frozen_date": _FROZEN_DATE,
        "belief_moved": False,
        "can_influence_belief": False,
        "frozen_frequencies_hz": {"f_low": _F_LOW, "f_ref": _F_REF, "f_high": 2048.0},
        "regime_boundaries": {
            "c_hz_msun": round(c_const, 6),
            "light_max_m_det_msun": round(c_const / _F_REF, 4),
            "heavy_min_m_det_msun": round(c_const / _F_LOW, 4),
            "rule": "f_ISCO<=30 -> heavy; f_ISCO>=215 -> light; else intermediate",
        },
        "coverage_target": _COVERAGE_TARGET,
        "clip": list(_CLIP),
        "epsilon_r_to_zero": _EPSILON_R_TO_ZERO,
        "percentile_rule": "numpy.percentile linear interp on (R_measured - r_mech), twin-checked",
        "twin_max_disagreement_r_mech": twin_r_mech,
        "twin_max_disagreement_percentile": twin_pct_max,
        "extraction_positive_control_max_r_mech_delta": round(ctrl_max_delta, 6),
        "extraction_positive_control_n_rows": ctrl_n,
        "residual_pool": {
            "n_total": len(pool),
            "receipts": receipt_meta,
            "rows": pool,
        },
        "bands": bands,
        "development_manifest": dev_manifest,
    }

    # content_sha256 = the deterministic scientific payload EXCLUDING the hashes
    # themselves; the table carries no wall-clock timestamp, so a third party
    # re-running this script reproduces the ENTIRE file byte-for-byte.
    _volatile = {"self_sha256", "content_sha256"}
    table["content_sha256"] = _content_sha256({k: v for k, v in table.items() if k not in _volatile})
    table["self_sha256"] = _content_sha256({k: v for k, v in table.items() if k != "self_sha256"})
    return table


def main() -> int:
    table = build()
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(table, indent=2, sort_keys=True), encoding="utf-8")

    print(f"P2 bands written: {_OUT}")
    print(f"self_sha256: {table['self_sha256']}")
    print(
        f"pool: {table['residual_pool']['n_total']} rows; "
        f"extraction ctrl delta {table['extraction_positive_control_max_r_mech_delta']}; "
        f"twin r_mech {table['twin_max_disagreement_r_mech']:.2e}; "
        f"twin pct {table['twin_max_disagreement_percentile']:.2e}"
    )
    for regime in ("light", "intermediate", "heavy"):
        b = table["bands"][regime]
        if regime == "heavy":
            print(f"  {regime:12s} n={b['n']:2d}  band=[0, {b['epsilon']}] (R->0 sub-claim)")
        else:
            print(
                f"  {regime:12s} n={b['n']:2d}  residual [5th,95th] = "
                f"[{b['band_offset_lo']:+.3f}, {b['band_offset_hi']:+.3f}]  "
                f"(raw min/max [{b['residual_min']:+.3f}, {b['residual_max']:+.3f}])"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
