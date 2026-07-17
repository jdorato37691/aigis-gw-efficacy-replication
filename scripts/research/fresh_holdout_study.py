#!/usr/bin/env python3
"""Fresh untouched holdout: development-naive test of the mass-trend claim.

Executes docs/research/preregistrations/2026-07-16-fresh-untouched-holdout.md.

The frozen Study-1/2/3 matched-filter pipeline (spin-extended TaylorF2, H1+L1,
32 s on-source, band [30, 2048] Hz, Welch mean 4 s PSD, off-source validity) is
scored on a deterministically selected cohort of O3a / GWTC-2.1-confident BBH
events that appear NOWHERE in the development record. No new physics: the
evaluation engine reuses gwtc3_oos_study._run_event / r_hat unchanged.

Three phases, each idempotent and checkpointed so an interrupted run resumes
without re-measuring:

    --freeze          apply the locked cohort rule against the GWOSC event API,
                      write the freeze receipt (cohort_frozen_at = now)
    --evaluate        run the frozen pipeline over the frozen cohort, one event
                      per checkpoint write, and grade per the locked criteria
    --build-artifact  assemble docs/.../verification/fresh_untouched_holdout.json
                      with exact hash binding and self-validate it

Default (no flag) runs freeze -> evaluate -> build-artifact in order.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_HERE))

from gw_evidence_controls import _content_sha256  # noqa: E402

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_CHECKPOINT = _RECEIPT_DIR / "FRESH_HOLDOUT_checkpoint.json"
_FREEZE_LATEST = _RECEIPT_DIR / "FRESH_HOLDOUT_freeze_latest.json"
_EVAL_LATEST = _RECEIPT_DIR / "FRESH_HOLDOUT_eval_latest.json"
_PREREG = "docs/research/preregistrations/2026-07-16-fresh-untouched-holdout.md"
_ARTIFACT = (
    REPO_ROOT
    / "docs"
    / "research"
    / "papers"
    / "gw-inspiral-template-efficacy"
    / "verification"
    / "fresh_untouched_holdout.json"
)

# --- locked by the preregistration (2026-07-16) -----------------------------
CATALOG_RELEASE = "GWTC-2.1-confident"
_M2_MIN = 3.0  # BBH: source-frame secondary mass floor
_FAR_MAX = 1.0  # per year, confident-detection threshold
_SNR_MIN = 12.0  # published network SNR floor (recovery power)
_COHORT_N = 10  # loudest N by network SNR
_O1_RHO_MAX = -0.5  # mass trend generalizes
_O2_MAE_MAX = 0.15  # frozen curve predicts
_MIN_MEASURED = 5  # contract minimum for a graded outcome

# Frozen Study-1/2/3 pipeline (governing commit 79d3c2c5, 2026-07-14T20:20:13-04:00)
_TEMPLATE_LOCKED_AT = "2026-07-14T20:20:13-04:00"
_GOVERNING_PIPELINE_FILES = sorted(
    [
        "gwtc1_taylorf2_sweep.py",
        "gwtc3_oos_study.py",
        "matched_filter_gw150914.py",
        "taylorf2.py",
    ]
)

# Exhaustive development manifest (31 physically distinct contaminated events;
# see the preregistration Section 1 grep census, 42 raw strings -> 31 events).
DEVELOPMENT_EVENTS: list[str] = [
    # GWTC-1 / O1-O2 in-sample (11)
    "GW150914",
    "GW151012",
    "GW151226",
    "GW170104",
    "GW170608",
    "GW170729",
    "GW170809",
    "GW170814",
    "GW170817",
    "GW170818",
    "GW170823",
    # GWTC-3 / O3b Study-3 OOS + Studies 4-6 reuse + coincidence audits (20)
    "GW191109_010717",
    "GW191126_115259",
    "GW191127_050227",
    "GW191129_134029",
    "GW191204_110529",
    "GW191204_171526",
    "GW191215_223052",
    "GW191216_213338",
    "GW191222_033537",
    "GW191230_180458",
    "GW200112_155838",
    "GW200128_022011",
    "GW200202_154313",
    "GW200219_094415",
    "GW200220_124850",
    "GW200224_222234",
    "GW200225_060421",
    "GW200302_015811",
    "GW200311_115853",
    "GW200316_215756",
]
_DEV_SET = set(DEVELOPMENT_EVENTS)


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _template_commit_sha256() -> str:
    digest = hashlib.sha256()
    for name in _GOVERNING_PIPELINE_FILES:
        digest.update((_HERE / name).read_bytes())
    return digest.hexdigest()


def _fetch_catalog() -> dict[str, dict[str, Any]]:
    """Return one metadata row per event (highest version), keyed by commonName."""
    url = f"https://gwosc.org/eventapi/json/{CATALOG_RELEASE}/"
    with urllib.request.urlopen(url, timeout=90) as resp:  # noqa: S310
        payload = json.load(resp)
    best: dict[str, dict[str, Any]] = {}
    for entry in payload["events"].values():
        name = str(entry.get("commonName") or "").strip()
        if not name:
            continue
        version = int(entry.get("version") or 0)
        if name not in best or version > int(best[name].get("version") or 0):
            best[name] = entry
    return best


def freeze() -> dict[str, Any]:
    """Apply the locked cohort rule; write the freeze receipt (idempotent)."""
    if _FREEZE_LATEST.is_file():
        print("freeze receipt already exists; reusing", flush=True)
        return json.loads(_FREEZE_LATEST.read_text())

    catalog = _fetch_catalog()
    eligible: list[dict[str, Any]] = []
    for name, ev in catalog.items():
        snr = ev.get("network_matched_filter_snr")
        far = ev.get("far")
        m1 = ev.get("mass_1_source")
        m2 = ev.get("mass_2_source")
        z = ev.get("redshift")
        chi = ev.get("chi_eff")
        gps = ev.get("GPS")
        if None in (snr, far, m1, m2, z, gps):
            continue
        if float(m2) < _M2_MIN:  # BBH cut
            continue
        if float(far) >= _FAR_MAX:  # confident-detection FAR
            continue
        if float(snr) < _SNR_MIN:  # recovery-power floor
            continue
        if name in _DEV_SET:  # development-naive screen (base id)
            continue
        m_det = (float(m1) + float(m2)) * (1.0 + float(z))
        eligible.append(
            {
                "name": name,
                "gps": float(gps),
                "published_snr": float(snr),
                "far": float(far),
                "m1_source": float(m1),
                "m2_source": float(m2),
                "redshift": float(z),
                "chi": float(chi) if chi is not None else 0.0,
                "m_det": round(m_det, 1),
            }
        )

    # deterministic order: network SNR descending, tie-break base id ascending
    eligible.sort(key=lambda r: (-r["published_snr"], r["name"]))
    n_eligible = len(eligible)
    cohort = eligible[:_COHORT_N]
    events = [r["name"] for r in cohort]

    frozen_at = datetime.now(UTC).isoformat()
    receipt: dict[str, Any] = {
        "receipt_type": "fresh_untouched_holdout_freeze",
        "preregistration": _PREREG,
        "catalog_release": CATALOG_RELEASE,
        "cohort_frozen_at": frozen_at,
        "rule": {
            "bbh_m2_source_min_msun": _M2_MIN,
            "far_max_per_year": _FAR_MAX,
            "network_snr_min": _SNR_MIN,
            "development_naive": True,
            "order": "network_matched_filter_snr desc, base id asc",
            "cohort_size_n": _COHORT_N,
        },
        "n_eligible": n_eligible,
        "events": events,
        "cohort_rows": cohort,
        "development_events": DEVELOPMENT_EVENTS,
        "cohort_manifest_sha256": _content_sha256({"catalog_release": CATALOG_RELEASE, "events": events}),
        "development_manifest_sha256": _content_sha256(DEVELOPMENT_EVENTS),
        "template_commit_sha256": _template_commit_sha256(),
        "template_locked_at": _TEMPLATE_LOCKED_AT,
        "can_influence_belief": False,
    }
    if n_eligible < _MIN_MEASURED:
        receipt["status"] = "NEEDS_CONTEXT"
        receipt["reason"] = f"only {n_eligible} eligible events under the locked rule; minimum {_MIN_MEASURED}"

    _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(receipt, indent=2, sort_keys=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stamped = _RECEIPT_DIR / f"FRESH_HOLDOUT_freeze_{stamp}.json"
    stamped.write_text(body, encoding="utf-8")
    _FREEZE_LATEST.write_text(body, encoding="utf-8")
    print(f"FROZEN cohort ({len(events)} of {n_eligible} eligible): {events}", flush=True)
    print("freeze receipt:", stamped, flush=True)
    return receipt


def evaluate() -> dict[str, Any]:
    """Run the frozen pipeline over the frozen cohort; grade per locked rule."""
    if not _FREEZE_LATEST.is_file():
        raise SystemExit("freeze first: no frozen cohort receipt found")
    freeze_receipt = json.loads(_FREEZE_LATEST.read_text())
    cohort = freeze_receipt["cohort_rows"]

    oos = _load("gwtc3_oos_study")
    sweep = _load("gwtc1_taylorf2_sweep")
    taylorf2 = _load("taylorf2")
    mf = sweep._load_instrument()

    checkpoint: dict[str, Any] = json.loads(_CHECKPOINT.read_text()) if _CHECKPOINT.is_file() else {}
    rows: list[dict[str, Any]] = checkpoint.get("rows", [])
    started_at = checkpoint.get("evaluation_started_at") or datetime.now(UTC).isoformat()
    done = {r["event"] for r in rows}

    for event in cohort:
        if event["name"] in done:
            continue
        row = oos._run_event(mf, taylorf2, sweep, event)
        rows.append(row)
        _CHECKPOINT.write_text(json.dumps({"evaluation_started_at": started_at, "rows": rows}, indent=1, default=str))
        print(
            f"{row['event']}: M_det={row['m_det']} chi={row['chi_eff']:+.2f} "
            f"R={row.get('recovery_fraction', '-')} r_hat={row['r_hat']} [{row['status']}]",
            flush=True,
        )

    if len({r["event"] for r in rows}) < len(cohort):
        print("checkpointed; re-run --evaluate to continue", flush=True)
        return {}

    measured = [r for r in rows if r["status"] == "measured"]
    n_measured = len(measured)
    completed_at = datetime.now(UTC).isoformat()

    if n_measured >= _MIN_MEASURED:
        rho, pvalue = spearmanr([r["m_det"] for r in measured], [r["recovery_fraction"] for r in measured])
        rho = float(rho)
        pvalue = float(pvalue)
        mae = float(np.median([r["abs_error_vs_r_hat"] for r in measured]))
        o1_pass = bool(rho <= _O1_RHO_MAX)
        o2_pass = bool(mae <= _O2_MAE_MAX)
        if o1_pass and o2_pass:
            outcome = "confirmed"
        elif not o1_pass:
            outcome = "falsified"
        else:
            outcome = "inconclusive"  # trend transfers, absolute curve does not
    else:
        rho = pvalue = mae = float("nan")
        o1_pass = o2_pass = False
        outcome = "inconclusive"  # under-powered by mechanical exclusions

    result: dict[str, Any] = {
        "catalog_release": CATALOG_RELEASE,
        "n_cohort": len(cohort),
        "n_measured": n_measured,
        "excluded": [{"event": r["event"], "status": r["status"]} for r in rows if r["status"] != "measured"],
        "measured_rows": [
            {
                "event": r["event"],
                "m_det": r["m_det"],
                "chi_eff": r["chi_eff"],
                "published_snr": r["published_snr"],
                "recovered_snr": r["recovered_snr"],
                "recovery_fraction": r["recovery_fraction"],
                "r_hat": r["r_hat"],
                "abs_error_vs_r_hat": r["abs_error_vs_r_hat"],
            }
            for r in measured
        ],
        "O1_trend_generalizes": {
            "criterion": f"spearman rho(M_det, R) <= {_O1_RHO_MAX}",
            "rho": None if not np.isfinite(rho) else round(rho, 4),
            "p_value": None if not np.isfinite(pvalue) else round(pvalue, 6),
            "passed": o1_pass,
        },
        "O2_curve_predicts": {
            "criterion": f"median |R - r_hat(M_det)| <= {_O2_MAE_MAX}",
            "median_abs_error": None if not np.isfinite(mae) else round(mae, 4),
            "passed": o2_pass,
        },
        "outcome": outcome,
    }

    eval_receipt: dict[str, Any] = {
        "receipt_type": "fresh_untouched_holdout_eval",
        "preregistration": _PREREG,
        "catalog_release": CATALOG_RELEASE,
        "evaluation_started_at": started_at,
        "evaluation_completed_at": completed_at,
        "template_commit_sha256": _template_commit_sha256(),
        "rows": rows,
        "result": result,
        "outcome": outcome,
        "can_influence_belief": False,
    }
    body = json.dumps(eval_receipt, indent=2, sort_keys=True, default=str)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stamped = _RECEIPT_DIR / f"FRESH_HOLDOUT_eval_{stamp}.json"
    stamped.write_text(body, encoding="utf-8")
    _EVAL_LATEST.write_text(body, encoding="utf-8")
    print(
        json.dumps(
            {"outcome": outcome, "O1": result["O1_trend_generalizes"], "O2": result["O2_curve_predicts"]}, indent=1
        ),
        flush=True,
    )
    print("eval receipt:", stamped, flush=True)
    return eval_receipt


def build_artifact() -> dict[str, Any]:
    """Assemble the hash-bound artifact and self-validate it."""
    from gw_evidence_controls import validate_fresh_holdout_artifact  # noqa: PLC0415

    if not (_FREEZE_LATEST.is_file() and _EVAL_LATEST.is_file()):
        raise SystemExit("need both freeze and eval receipts before building the artifact")
    freeze_receipt = json.loads(_FREEZE_LATEST.read_text())
    eval_receipt = json.loads(_EVAL_LATEST.read_text())

    events = list(freeze_receipt["events"])
    development_events = list(freeze_receipt["development_events"])
    result = dict(eval_receipt["result"])

    freeze_sha = hashlib.sha256(_FREEZE_LATEST.read_bytes()).hexdigest()
    eval_sha = hashlib.sha256(_EVAL_LATEST.read_bytes()).hexdigest()

    artifact: dict[str, Any] = {
        "schema": "aigis.gw.fresh_holdout.v1",
        "catalog_release": CATALOG_RELEASE,
        "preregistration": _PREREG,
        "events": events,
        "development_events": development_events,
        "cohort_manifest_sha256": _content_sha256({"catalog_release": CATALOG_RELEASE, "events": events}),
        "development_manifest_sha256": _content_sha256(development_events),
        "template_commit_sha256": _template_commit_sha256(),
        "freeze_receipt_sha256": freeze_sha,
        "evaluation_receipt_sha256": eval_sha,
        "result": result,
        "result_sha256": _content_sha256(result),
        "outcome": eval_receipt["outcome"],
        "template_locked_at": _TEMPLATE_LOCKED_AT,
        "cohort_frozen_at": freeze_receipt["cohort_frozen_at"],
        "evaluation_started_at": eval_receipt["evaluation_started_at"],
        "evaluation_completed_at": eval_receipt["evaluation_completed_at"],
        "can_influence_belief": False,
    }
    verdict = validate_fresh_holdout_artifact(artifact)
    _ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    _ARTIFACT.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("artifact:", _ARTIFACT, flush=True)
    print("validator verdict:", json.dumps(verdict, indent=1), flush=True)
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--build-artifact", action="store_true")
    args = parser.parse_args()

    if not (args.freeze or args.evaluate or args.build_artifact):
        freeze()
        if evaluate():
            build_artifact()
        return 0
    if args.freeze:
        freeze()
    if args.evaluate:
        evaluate()
    if args.build_artifact:
        build_artifact()
    return 0


if __name__ == "__main__":
    sys.exit(main())
