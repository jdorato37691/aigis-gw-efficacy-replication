#!/usr/bin/env python3
"""P2 Step C: the mechanical release-day grader for the O4c inspiral-recovery prediction.

Fires when the GWOSC O4c bulk release (planned Dec 2026) drops. Runs the frozen
cohort rule + frozen band table + frozen matched-filter pipeline and returns
CONFIRMED / FALSIFIED / INCONCLUSIVE with the coverage number and per-event
covered flags, with ZERO human input. Executes the grading rule frozen in
docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md (Sections 4-5).

Split:
  * `event_band(...)` and `grade_cohort(...)` are PURE (no network, no matched
    filter) and drive the CONFIRMED/FALSIFIED decision. Unit-tested against
    synthetic O4c cohorts (Rule 26 positive + negative control).
  * `freeze_o4c_cohort(...)` and `run_release_day(...)` are the live release-day
    driver: they fetch the O4c catalog, apply the frozen cohort rule, run the
    frozen `_run_event`, and grade with `grade_cohort`.

The frozen predictor and frozen pipeline are imported read-only and NEVER refit.
belief_moved=false; sandbox lane; the external anchor is operator-gated per G0.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_PREREG = "docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md"
_BANDS_PATH = (
    _HERE.parents[1]
    / "docs"
    / "research"
    / "papers"
    / "gw-inspiral-template-efficacy"
    / "verification"
    / "p2_prospective_bands.json"
)

# frozen grade thresholds (prereg Section 5)
_COVERAGE_CONFIRMED = 0.80
_COVERAGE_FALSIFIED = 0.70
_MIN_MEASURED = 8
_N_MAX = 40  # GPS-sorted compute bound (prereg Section 4)
_M2_MIN = 3.0
_FAR_MAX = 1.0
_SNR_MIN = 12.0
_TREND_EXPECTED = -0.9  # secondary reported metric


def _load_module(name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _content_sha256(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_bands(path: Path = _BANDS_PATH) -> dict[str, Any]:
    """Load and self-verify the frozen P2 band table."""
    table = json.loads(path.read_text())
    if table.get("schema") != "aigis.gw.p2_prospective_bands.v1":
        raise SystemExit(f"unexpected band-table schema {table.get('schema')!r}")
    body = {k: v for k, v in table.items() if k != "self_sha256"}
    recomputed = _content_sha256(body)
    if recomputed != table.get("self_sha256"):
        raise SystemExit(f"band-table self_sha256 mismatch: {recomputed} != {table.get('self_sha256')}")
    return table


def _c_const(predictor) -> float:  # noqa: ANN001
    return 1.0 / (6.0**1.5 * math.pi * predictor._MSUN_SECONDS)


def event_band(
    m1_source: float,
    m2_source: float,
    redshift: float,
    bands: dict[str, Any],
    predictor,  # noqa: ANN001
) -> dict[str, Any]:
    """Frozen 90% prediction interval for one event (prereg Sections 3-4).

    Regime is set by f_ISCO position; r_mech is the frozen predictor on the true
    masses; the band is r_mech + regime residual offsets clipped to [0,1], or the
    frozen [0, epsilon] R->0 band for ISCO-below-band (heavy) events.
    """
    c = _c_const(predictor)
    m_det = (m1_source + m2_source) * (1.0 + redshift)
    f_isco = c / m_det
    r_mech = float(predictor.predict_r_mech(m1_source, m2_source, redshift))
    f_low = float(bands["frozen_frequencies_hz"]["f_low"])
    f_ref = float(bands["frozen_frequencies_hz"]["f_ref"])
    clip_lo, clip_hi = bands["clip"]
    epsilon = float(bands["epsilon_r_to_zero"])

    if f_isco <= f_low:
        regime = "heavy"
        lo, hi = 0.0, epsilon
    elif f_isco >= f_ref:
        regime = "light"
        off = bands["bands"]["light"]
        lo = min(max(r_mech + float(off["band_offset_lo"]), clip_lo), clip_hi)
        hi = min(max(r_mech + float(off["band_offset_hi"]), clip_lo), clip_hi)
    else:
        regime = "intermediate"
        off = bands["bands"]["intermediate"]
        lo = min(max(r_mech + float(off["band_offset_lo"]), clip_lo), clip_hi)
        hi = min(max(r_mech + float(off["band_offset_hi"]), clip_lo), clip_hi)

    return {
        "regime": regime,
        "m_det": round(m_det, 4),
        "f_isco_hz": round(f_isco, 3),
        "r_mech": round(r_mech, 6),
        "band_lo": round(lo, 6),
        "band_hi": round(hi, 6),
        "isco_below_band": bool(f_isco <= f_low),
    }


def grade_cohort(measured_rows: list[dict[str, Any]], bands: dict[str, Any], predictor) -> dict[str, Any]:  # noqa: ANN001
    """PURE coverage grade over measured O4c events (prereg Section 5).

    Each row must carry m1_source, m2_source, redshift, recovery_fraction (the
    measured R). Returns coverage, per-event covered flags, the R->0 sub-check,
    the secondary trend rho, and the frozen CONFIRMED / FALSIFIED / INCONCLUSIVE
    verdict.
    """
    epsilon = float(bands["epsilon_r_to_zero"])
    graded: list[dict[str, Any]] = []
    for r in measured_rows:
        band = event_band(float(r["m1_source"]), float(r["m2_source"]), float(r["redshift"]), bands, predictor)
        recovery = float(r["recovery_fraction"])
        covered = bool(band["band_lo"] <= recovery <= band["band_hi"])
        graded.append(
            {
                "event": r.get("event"),
                "m_det": band["m_det"],
                "recovery_fraction": recovery,
                "r_mech": band["r_mech"],
                "band_lo": band["band_lo"],
                "band_hi": band["band_hi"],
                "regime": band["regime"],
                "isco_below_band": band["isco_below_band"],
                "covered": covered,
            }
        )

    n = len(graded)
    covered_n = sum(1 for g in graded if g["covered"])
    coverage = (covered_n / n) if n else None

    isco_rows = [g for g in graded if g["isco_below_band"]]
    r_to_zero_violations = [g for g in isco_rows if g["recovery_fraction"] > epsilon]
    r_to_zero_verdict = (
        "not_applicable" if not isco_rows else ("CONFIRMED" if not r_to_zero_violations else "FALSIFIED")
    )

    if n >= 3 and len({g["m_det"] for g in graded}) > 1:
        rho, pvalue = spearmanr([g["m_det"] for g in graded], [g["recovery_fraction"] for g in graded])
        rho = float(rho)
        pvalue = float(pvalue)
    else:
        rho = pvalue = float("nan")

    if n < _MIN_MEASURED:
        verdict = "INCONCLUSIVE"
    elif coverage >= _COVERAGE_CONFIRMED:
        verdict = "CONFIRMED"
    elif coverage < _COVERAGE_FALSIFIED:
        verdict = "FALSIFIED"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "verdict": verdict,
        "n_measured": n,
        "n_covered": covered_n,
        "coverage": None if coverage is None else round(coverage, 4),
        "coverage_confirmed_at_or_above": _COVERAGE_CONFIRMED,
        "coverage_falsified_below": _COVERAGE_FALSIFIED,
        "r_to_zero_subclaim": {
            "verdict": r_to_zero_verdict,
            "n_isco_below_band": len(isco_rows),
            "epsilon": epsilon,
            "violations": [
                {"event": g["event"], "m_det": g["m_det"], "recovery_fraction": g["recovery_fraction"]}
                for g in r_to_zero_violations
            ],
        },
        "trend_rho_M_det_R": {
            "rho": None if not np.isfinite(rho) else round(rho, 4),
            "p_value": None if not np.isfinite(pvalue) else round(pvalue, 6),
            "expected": _TREND_EXPECTED,
            "note": "secondary reported metric; not part of the coverage pass/fail",
        },
        "graded_rows": graded,
    }


# --- synthetic controls (Rule 26; used by tests and --self-control) ----------
def synthetic_cohort(
    bands: dict[str, Any],
    predictor,  # noqa: ANN001
    *,
    n: int = 24,
    mode: str = "calibrated",
    seed: int = 20260717,
) -> list[dict[str, Any]]:
    """Fabricate an O4c-like cohort with KNOWN R for grader control (Rule 26).

    mode='calibrated'  -> R drawn inside the frozen band ~90% of the time
                          (well-calibrated -> expect CONFIRMED).
    mode='biased'      -> R systematically shoved far outside the band
                          (mis-calibrated -> expect FALSIFIED).
    Masses span the three regimes; redshift fixed small so M_det ~ (m1+m2).
    """
    rng = np.random.default_rng(seed)
    # M_det targets spanning light (<20.45), intermediate, heavy (>=146.57)
    m_dets = np.concatenate(
        [
            rng.uniform(12.0, 20.0, size=max(2, n // 8)),  # light
            rng.uniform(25.0, 140.0, size=n - max(2, n // 8) - max(2, n // 8)),  # intermediate
            rng.uniform(150.0, 320.0, size=max(2, n // 8)),  # heavy
        ]
    )
    rows: list[dict[str, Any]] = []
    for i, m_det in enumerate(m_dets):
        z = 0.1
        total_source = float(m_det) / (1.0 + z)
        m1 = total_source * 0.6
        m2 = total_source * 0.4
        band = event_band(m1, m2, z, bands, predictor)
        lo, hi = band["band_lo"], band["band_hi"]
        if mode == "calibrated":
            if band["isco_below_band"]:
                r = 0.0  # heavy: true R->0, lands in [0, eps]
            elif rng.random() < 0.90:
                r = float(rng.uniform(lo, hi))  # inside band
            else:
                r = float(hi + 0.10) if rng.random() < 0.5 else float(max(0.0, lo - 0.10))  # 10% outside
        elif mode == "biased":
            if band["isco_below_band"]:
                r = 0.60  # heavy events recover high -> R->0 sub-claim FALSIFIED
            else:
                r = float(min(1.0, hi + 0.30))  # shoved well above the band
        else:
            raise ValueError(f"unknown mode {mode!r}")
        rows.append(
            {
                "event": f"SYN{i:03d}_{mode}",
                "m1_source": round(m1, 4),
                "m2_source": round(m2, 4),
                "redshift": z,
                "recovery_fraction": round(min(max(r, 0.0), 1.0), 6),
            }
        )
    return rows


# --- live release-day driver (runs against the O4c catalog on release) -------
def freeze_o4c_cohort(catalog_release: str, bands: dict[str, Any]) -> dict[str, Any]:
    """Apply the frozen cohort rule against the O4c catalog (prereg Section 4)."""
    import urllib.request  # noqa: PLC0415

    dev_events = set(bands["development_manifest"]["events"])
    dev_prefix = {e[:8] for e in dev_events}
    predictor = _load_module("r_predictor")
    c = _c_const(predictor)

    url = f"https://gwosc.org/eventapi/json/{catalog_release}/"
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310
        payload = json.load(resp)
    best: dict[str, dict[str, Any]] = {}
    for entry in payload["events"].values():
        name = str(entry.get("commonName") or "").strip()
        if not name:
            continue
        version = int(entry.get("version") or 0)
        if name not in best or version > int(best[name].get("version") or 0):
            best[name] = entry

    eligible: list[dict[str, Any]] = []
    excluded_dev: list[str] = []
    for name, ev in best.items():
        if name in dev_events or name[:8] in dev_prefix:
            excluded_dev.append(name)
            continue
        snr, far = ev.get("network_matched_filter_snr"), ev.get("far")
        m1, m2, z, gps = ev.get("mass_1_source"), ev.get("mass_2_source"), ev.get("redshift"), ev.get("GPS")
        if None in (snr, far, m1, m2, z, gps):
            continue
        if float(m2) < _M2_MIN or float(far) >= _FAR_MAX or float(snr) < _SNR_MIN:
            continue
        m_det = (float(m1) + float(m2)) * (1.0 + float(z))
        eligible.append(
            {
                "name": name,
                "gps": float(gps),
                "published_snr": float(snr),
                "m1_source": float(m1),
                "m2_source": float(m2),
                "redshift": float(z),
                "chi": float(ev.get("chi_eff") or 0.0),
                "m_det": round(m_det, 1),
                "f_isco_hz": round(c / m_det, 2),
                "isco_below_band": bool(c / m_det <= 30.0),
            }
        )
    eligible.sort(key=lambda r: (r["gps"], r["name"]))
    cohort = eligible[:_N_MAX]
    return {
        "catalog_release": catalog_release,
        "cohort_frozen_at": datetime.now(UTC).isoformat(),
        "n_eligible": len(eligible),
        "n_excluded_development": len(excluded_dev),
        "excluded_development": sorted(excluded_dev),
        "cohort_rows": cohort,
        "cap_dropped": [
            {"name": r["name"], "m_det": r["m_det"], "published_snr": r["published_snr"]} for r in eligible[_N_MAX:]
        ],
    }


def run_release_day(catalog_release: str) -> dict[str, Any]:
    """Full release-day run: freeze cohort, measure R, grade. Live network + pipeline."""
    bands = load_bands()
    frozen = freeze_o4c_cohort(catalog_release, bands)
    cohort = frozen["cohort_rows"]

    oos = _load_module("gwtc3_oos_study")
    sweep = _load_module("gwtc1_taylorf2_sweep")
    taylorf2 = _load_module("taylorf2")
    predictor = _load_module("r_predictor")
    mf = sweep._load_instrument()
    predictor.assert_twin([r["m_det"] for r in cohort])

    rows: list[dict[str, Any]] = []
    for event in cohort:
        row = oos._run_event(mf, taylorf2, sweep, event)
        rows.append(row)
        print(
            f"{row['event']}: M_det={row['m_det']} R={row.get('recovery_fraction', '-')} [{row['status']}]", flush=True
        )

    measured = []
    by_name = {r["name"]: r for r in cohort}
    for r in rows:
        if r.get("status") != "measured":
            continue
        crow = by_name[r["event"]]
        measured.append(
            {
                "event": r["event"],
                "m1_source": crow["m1_source"],
                "m2_source": crow["m2_source"],
                "redshift": crow["redshift"],
                "recovery_fraction": r["recovery_fraction"],
            }
        )
    result = grade_cohort(measured, bands, predictor)

    receipt = {
        "receipt_type": "p2_release_day_grade",
        "preregistration": _PREREG,
        "catalog_release": catalog_release,
        "band_table_self_sha256": bands["self_sha256"],
        "predictor_commit": bands["predictor_commit"],
        "template_commit_sha256": bands["template_commit_sha256"],
        "graded_at": datetime.now(UTC).isoformat(),
        "cohort_frozen_at": frozen["cohort_frozen_at"],
        "n_cohort": len(cohort),
        "n_eligible": frozen["n_eligible"],
        "n_excluded_development": frozen["n_excluded_development"],
        "excluded": [{"event": r["event"], "status": r.get("status")} for r in rows if r.get("status") != "measured"],
        "result": result,
        "verdict": result["verdict"],
        "can_influence_belief": False,
    }
    _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (_RECEIPT_DIR / f"P2_RELEASE_GRADE_{stamp}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, default=str)
    )
    print(
        json.dumps(
            {"verdict": result["verdict"], "coverage": result["coverage"], "n_measured": result["n_measured"]}, indent=1
        )
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog-release", help="O4c GWOSC catalog release name (e.g. GWTC-6.0); required on release day"
    )
    parser.add_argument(
        "--self-control", action="store_true", help="run the synthetic positive+negative grader controls (Rule 26)"
    )
    args = parser.parse_args()

    if args.self_control:
        bands = load_bands()
        predictor = _load_module("r_predictor")
        pos = grade_cohort(synthetic_cohort(bands, predictor, mode="calibrated"), bands, predictor)
        neg = grade_cohort(synthetic_cohort(bands, predictor, mode="biased"), bands, predictor)
        print(
            json.dumps(
                {
                    "positive_control": {"verdict": pos["verdict"], "coverage": pos["coverage"], "expect": "CONFIRMED"},
                    "negative_control": {
                        "verdict": neg["verdict"],
                        "coverage": neg["coverage"],
                        "r_to_zero": neg["r_to_zero_subclaim"]["verdict"],
                        "expect": "FALSIFIED",
                    },
                },
                indent=1,
            )
        )
        ok = pos["verdict"] == "CONFIRMED" and neg["verdict"] == "FALSIFIED"
        return 0 if ok else 1

    if not args.catalog_release:
        parser.error("provide --catalog-release on release day, or --self-control")
    run_release_day(args.catalog_release)
    return 0


if __name__ == "__main__":
    sys.exit(main())
