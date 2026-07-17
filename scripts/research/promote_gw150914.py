#!/usr/bin/env python3
"""Record the preregistered GW150914 matched-filter benchmark in the ladder.

Runs AFTER the four preregistered runs (validate/control/confirm/replicate)
have all passed. Registers the experiment in the canonical registry, attaches
the confirmatory recovery as receipt-bound EXTERNAL_EXPERIMENTAL_RESULT
evidence (the LIGO strain measurement is the physical experiment - the
template is never called the validation), records the within-project
alternative-PSD reproduction through the reproduction machinery, and verifies
the derived ladder position by a raw-store re-read.

Expected: externally_grounded after the evidence lands. The same-project
reproduction deliberately carries no independence basis and cannot promote the
record to reproduced or experimentally validated.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import platform as _platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "platforms" / "backend" / "apps" / "backend" / "src"))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_HYPOTHESIS = (
    "The public GW150914 strain data (GWOSC, H1+L1, GPS 1126259446-1126259478) contain a "
    "signal whose quadrature sum of independently maximized single-detector matched-filter SNRs "
    "falls within 15 percent of the published network SNR 23.7. This is a benchmark comparison, "
    "not an equivalent coincident network statistic."
)
_FALSIFIER = "Legacy two-detector recovery statistic outside the preregistered interval [20.145, 27.255]."
_CITATION = "Abbott et al. 2016, Phys. Rev. Lett. 116, 061102"
_SOURCE_REF = "GWOSC open data H1+L1 GPS [1126259446, 1126259478]; " + _CITATION
_PRIMARY_EXECUTOR = "matched_filter_pipeline"
_METHOD = (
    "preregistered FFT matched filter, independently maximized H1/L1 peaks, quadrature sum, "
    "GWOSC NR template, Welch PSD, band 20-2048 Hz"
)


def _canonical(value: Any) -> str:  # noqa: ANN401
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:  # noqa: ANN401
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _latest_receipt(mode: str) -> dict[str, Any]:
    candidates = sorted(_RECEIPT_DIR.glob(f"GW150914_mf_{mode}_*.json"))
    if not candidates:
        raise SystemExit(f"missing {mode} receipt - run the preregistered sequence first")
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


async def main() -> int:
    from platforms.backend.apps.backend.src.services.intelligence import (  # noqa: PLC0415
        experiment_registry,
    )
    from platforms.backend.apps.backend.src.services.intelligence.scientific_memory import (  # noqa: PLC0415
        EvidenceKind,
        EvidenceOrigin,
        EvidenceRelation,
        ReproductionOutcome,
        make_evidence,
        make_reproduction_attempt,
        registered_run_digests,
    )
    from shared.redis_pool import get_redis_from_env  # noqa: PLC0415

    redis = await get_redis_from_env()

    validate = _latest_receipt("validate")
    control = _latest_receipt("control")
    confirm = _latest_receipt("confirm")
    replicate = _latest_receipt("replicate")

    # hard preconditions: the preregistered gates must all have passed
    if not validate.get("instrument_valid"):
        raise SystemExit("instrument validation did not pass - no promotion")
    if not control.get("control_passed"):
        raise SystemExit("off-source control did not pass - no promotion")
    if not confirm.get("success"):
        raise SystemExit("confirmatory run did not succeed - preserve the negative, no promotion")
    within = replicate.get("within_published_tolerance")
    close_to_confirm = (
        abs(float(replicate["network_snr"]) - float(confirm["network_snr"])) / float(confirm["network_snr"]) <= 0.10
    )
    if not (within and close_to_confirm):
        raise SystemExit("replication did not meet the preregistered criteria - no promotion")

    # 1. Register the experiment (graded; conclusion stays OPEN - the ladder
    #    speaks through evidence, not through a self-declared conclusion)
    record = await experiment_registry.register_experiment(
        redis,
        source="gw_replication",
        domain="physics_math",
        hypothesis=_HYPOTHESIS,
        status="graded",
        falsifier=_FALSIFIER,
        method=_METHOD,
        rationale=(
            "Charter Day-90 gate: reproduce a published GW detection with a genuine "
            "matched-filter benchmark under a preregistered protocol while keeping "
            "the legacy statistic distinct from a coincident network SNR."
        ),
        inputs={
            "on_source_gps": confirm["h1"]["segment_gps"],
            "template_sha256": confirm["template_sha256"],
            "band_hz": [20.0, 2048.0],
            "preregistration": "docs/research/preregistrations/2026-07-12-gw150914-matched-filter.md",
        },
        parameters={"psd": "welch_mean_4s", "tolerance": 0.15, "peak_window_s": 0.1},
        models_used=[],  # no model authored this result; the pipeline is deterministic
        tools_used=["gwpy.fetch_open_data", "scipy.signal.welch", "numpy.fft"],
        primary_executor=_PRIMARY_EXECUTOR,
        source_refs=[_SOURCE_REF],
        metrics={"confirmed": True, "recovered_statistic_value": confirm["network_snr"]},
        result={
            "network_snr": confirm["network_snr"],
            "recovered_statistic": confirm.get("recovered_statistic"),
            "published_network_snr": confirm["published_network_snr"],
            "preregistered_interval": confirm["preregistered_interval"],
            "h1_snr": confirm["h1"]["snr_peak"],
            "l1_snr": confirm["l1"]["snr_peak"],
            "h1_peak_gps": confirm["h1"]["peak_gps"],
            "l1_peak_gps": confirm["l1"]["peak_gps"],
            "offsource_control_max": control["network_snr_max_offsource"],
        },
        tags=["gw_replication", "charter_day90", "GW150914"],
        artifact_payloads={
            "prereg_confirm_receipt.json": confirm,
            "prereg_control_receipt.json": control,
            "prereg_validate_receipt.json": validate,
        },
    )
    experiment_id = record.experiment_id
    print("registered:", experiment_id)

    # 2. External evidence: the confirmatory recovery, receipt-bound to the
    #    registry's external-observation schema
    observation = {
        "network_snr": confirm["network_snr"],
        "recovered_statistic": confirm.get("recovered_statistic"),
        "h1_snr": confirm["h1"]["snr_peak"],
        "l1_snr": confirm["l1"]["snr_peak"],
        "h1_peak_gps": confirm["h1"]["peak_gps"],
        "l1_peak_gps": confirm["l1"]["peak_gps"],
        "published_network_snr": confirm["published_network_snr"],
        "data_source": "GWOSC open strain data",
        "confirm_receipt_sha256": confirm.get("receipt_sha256", ""),
    }
    evidence_receipt = {
        "schema": "aigis.scientific_evidence_receipt.v1",
        "experiment_id": experiment_id,
        "verifier_id": "external_evidence_intake_v1",
        "source_ref": _SOURCE_REF,
        "source_origin": "external",
        "produced_by": _PRIMARY_EXECUTOR,
        "observation_digest": _sha(observation),
        "observation": observation,
        "citation": _CITATION,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    evidence_receipt_path = _RECEIPT_DIR / f"{experiment_id}_external_evidence.json"
    evidence_receipt_path.write_text(json.dumps(evidence_receipt, indent=2), encoding="utf-8")
    evidence_sha = hashlib.sha256(evidence_receipt_path.read_bytes()).hexdigest()

    evidence = make_evidence(
        kind=EvidenceKind.EXTERNAL_EXPERIMENTAL_RESULT,
        relation=EvidenceRelation.SUPPORTS,
        summary=(
            f"Preregistered matched filter produces legacy two-detector recovery statistic "
            f"{confirm['network_snr']} (published network SNR {confirm['published_network_snr']}) from public LIGO strain; off-source "
            f"control max {control['network_snr_max_offsource']} < 8. The LIGO measurement is the "
            "physical experiment; this computation is a benchmark and is not an equivalent "
            "coincident network statistic or physical validation."
        ),
        source_origin=EvidenceOrigin.EXTERNAL,
        source_ref=_SOURCE_REF,
        receipt_ref=str(evidence_receipt_path),
        receipt_sha256=evidence_sha,
        produced_by=_PRIMARY_EXECUTOR,
        method_id="matched_filter_gwosc_template_v1",
        meaningful_test=True,
        metadata={"preregistration_commit": "locked before any on-source run"},
    )
    updated = await experiment_registry.append_evidence(redis, experiment_id, evidence, actor="gw_replication")
    print("evidence attached; status:", updated.scientific_record.evidence_status.value)

    # 3. Within-project robustness reproduction -> non-independent attempt.
    sci = updated.scientific_record
    targets = registered_run_digests(sci)
    run_digests = {
        "input_digest": _sha(
            {"segments": replicate["h1"]["segment_gps"], "template_sha256": replicate["template_sha256"]}
        ),
        "protocol_digest": _sha({"psd": "welch_median_16s", "band_hz": [20.0, 2048.0]}),
        "result_digest": _sha({"network_snr": replicate["network_snr"]}),
    }
    executor_identity_digest = _sha({"executor": "matched_filter_replicator", "host": _platform.node()})
    environment_digest = _sha(replicate.get("environment", {}))
    repro_receipt = {
        "experiment_id": experiment_id,
        "claim_digest": targets["claim_digest"],
        "executed_by": "matched_filter_replicator",
        "primary_executor": _PRIMARY_EXECUTOR,
        "method_id": "welch_median_16s_matched_filter_v1",
        "outcome": "confirmed",
        "target_input_digest": targets["input_digest"],
        "target_protocol_digest": targets["protocol_digest"],
        "target_result_digest": targets["result_digest"],
        "input_digest": run_digests["input_digest"],
        "protocol_digest": run_digests["protocol_digest"],
        "result_digest": run_digests["result_digest"],
        "executor_identity_digest": executor_identity_digest,
        "environment_digest": environment_digest,
        "observation": {
            "network_snr": replicate["network_snr"],
            "confirm_network_snr": confirm["network_snr"],
            "relative_difference": round(
                abs(float(replicate["network_snr"]) - float(confirm["network_snr"])) / float(confirm["network_snr"]),
                4,
            ),
            "replicate_receipt_sha256": replicate.get("receipt_sha256", ""),
        },
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    repro_receipt_path = _RECEIPT_DIR / f"{experiment_id}_replication_receipt.json"
    repro_receipt_path.write_text(json.dumps(repro_receipt, indent=2), encoding="utf-8")

    attempt = make_reproduction_attempt(
        experiment_id=experiment_id,
        hypothesis=sci.hypothesis,
        outcome=ReproductionOutcome.CONFIRMED,
        executed_by="matched_filter_replicator",
        primary_executor=_PRIMARY_EXECUTOR,
        method_id="welch_median_16s_matched_filter_v1",
        receipt_ref=str(repro_receipt_path),
        executor_identity_digest=executor_identity_digest,
        environment_digest=environment_digest,
        independence_basis="",
        target_input_digest=targets["input_digest"],
        target_protocol_digest=targets["protocol_digest"],
        target_result_digest=targets["result_digest"],
        input_digest=run_digests["input_digest"],
        protocol_digest=run_digests["protocol_digest"],
        result_digest=run_digests["result_digest"],
        notes=(
            f"within-project alternate-PSD recovery statistic {replicate['network_snr']} vs confirm "
            f"{confirm['network_snr']}; shared data, template machinery, project, and development history"
        ),
    )
    final = await experiment_registry.append_reproduction(redis, experiment_id, attempt, actor="gw_replication")
    print("replication recorded; status:", final.scientific_record.evidence_status.value)

    # 4. Raw-store persistence verification (not scientific independence).
    import redis as redis_sync  # noqa: PLC0415

    raw = redis_sync.Redis(decode_responses=True).get(f"aigis:experiments:record:{experiment_id}")
    stored = json.loads(raw)
    print("RAW re-read evidence_status:", stored["scientific_record"]["evidence_status"])
    print("experiment_id:", experiment_id)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
