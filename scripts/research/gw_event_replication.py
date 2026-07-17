#!/usr/bin/env python3
"""Generalized GW event reproduction driver - one controlled instrument, N events.

Reuses the matched-filter pipeline from ``matched_filter_gw150914.py``
UNCHANGED (the instrument that passed injection/scale/alignment validation and
recovered GW150914 with a legacy two-detector statistic of 22.76). Per-event
locked parameters come
from the EVENTS registry below, each backed by its own committed
preregistration. Historical registry enums are preserved as machine metadata;
this within-project alternate-PSD run is not independent experimental
validation.

Usage:
    gw_event_replication.py --event GW151226 --validate|--control|--confirm|--replicate|--promote
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import platform as _platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "platforms" / "backend" / "apps" / "backend" / "src"))

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"

# Per-event locked parameters. Each entry mirrors a committed preregistration
# in docs/research/preregistrations/ - the prereg is the authority; this dict
# is its executable transcription.
EVENTS: dict[str, dict[str, Any]] = {
    "GW170817": {
        "citation": "Abbott et al. 2017, Phys. Rev. Lett. 119, 161101",
        "published_network_snr": 32.4,
        "tolerance": 0.15,
        "catalog_gps": 1187008882.4,
        "on_source": (1187008762.4, 1187008890.4),  # 128 s: BNS inspiral
        "off_source": (1187008250.4, 1187008378.4),  # 512 s earlier, NaN-free (recon)
        "template_taylorf2": {
            "chirp_mass_det_msun": 1.1977,
            "mass1_msun": 1.46,
            "mass2_msun": 1.27,
            "f_low": 30.0,
        },
        "band_hz": (30.0, 2048.0),
        "l1_glitch_rule": {  # mechanical, locked in prereg; decided without peeking
            "window_before_tc": (2.0, 0.5),
            "threshold_sigma": 15.0,
            "gate_half_width_s": 0.2,
            "taper_s": 0.1,
        },
        "grb": {"trigger_gps": 1187008884.47, "delay_window_s": (1.5, 2.0)},
        "preregistration": "docs/research/preregistrations/2026-07-12-gw170817-matched-filter.md",
        "domain": "physics_math",
    },
    "GW151226": {
        "citation": "Abbott et al. 2016, Phys. Rev. Lett. 116, 241103",
        "published_network_snr": 13.0,
        "tolerance": 0.25,
        "catalog_gps": 1135136350.6,
        "on_source": (1135136334.6, 1135136366.6),
        "off_source": (1135136462.6, 1135136494.6),  # prereg v2: original window is 100% NaN (pre-science-mode)
        "template_url": "https://gwosc.org/s/events/GW151226/GW151226_4_template.hdf5",
        "preregistration": "docs/research/preregistrations/2026-07-12-gw151226-matched-filter.md",
        "domain": "physics_math",
    },
}


def _load_instrument(event: str, cfg: dict[str, Any]):  # noqa: ANN202
    """Load the validated pipeline module and bind this event's locked params."""
    spec = importlib.util.spec_from_file_location("mf_instrument", _HERE / "matched_filter_gw150914.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    mf._EVENT = event
    mf._CITATION = cfg["citation"]
    mf._PUBLISHED_NETWORK_SNR = cfg["published_network_snr"]
    mf._TOLERANCE = cfg["tolerance"]
    mf._CATALOG_GPS = cfg["catalog_gps"]
    mf._ON_SOURCE = cfg["on_source"]
    mf._OFF_SOURCE = cfg["off_source"]
    if "template_url" in cfg:
        mf._TEMPLATE_URL = cfg["template_url"]
        mf._TEMPLATE_CACHE = _RECEIPT_DIR / cfg["template_url"].rsplit("/", 1)[-1]
    if "band_hz" in cfg:
        mf._BAND = tuple(cfg["band_hz"])

    if "template_taylorf2" in cfg:
        import numpy as np  # noqa: PLC0415

        sys.path.insert(0, str(_HERE))
        from taylorf2 import coefficient_integrity_check, taylorf2_time_domain  # noqa: PLC0415

        params = dict(cfg["template_taylorf2"])
        n_samples = round((cfg["on_source"][1] - cfg["on_source"][0]) * 4096.0)

        def _built_template() -> tuple[Any, str]:
            eta = params["mass1_msun"] * params["mass2_msun"] / (params["mass1_msun"] + params["mass2_msun"]) ** 2
            total_det = params["chirp_mass_det_msun"] / eta**0.6
            tripwire = coefficient_integrity_check(total_mass_msun=total_det, eta=eta)
            if not tripwire["passed"]:
                raise SystemExit(f"TaylorF2 coefficient tripwire FAILED: {tripwire}")
            template = taylorf2_time_domain(
                n_samples=n_samples,
                sample_rate=4096.0,
                **params,
            )
            return template, _sha({"builder": "taylorf2_35pn_v1", **params, "n": n_samples})

        mf._fetch_template = _built_template

    if "l1_glitch_rule" in cfg:
        import numpy as np  # noqa: PLC0415
        from scipy.signal import welch  # noqa: PLC0415
        from scipy.signal.windows import tukey  # noqa: PLC0415

        rule = cfg["l1_glitch_rule"]
        tc = cfg["catalog_gps"]
        on_source = tuple(cfg["on_source"])
        original_fetch = mf._fetch_strain
        mf._GLITCH_GATE_RECORD = {"checked": False, "fired": False}

        def _gated_fetch(detector: str, segment: tuple[float, float]):  # noqa: ANN202
            data = original_fetch(detector, segment)
            if detector != "L1" or tuple(segment) != on_source:
                return data
            fs = 4096.0
            n = len(data)
            times = segment[0] + np.arange(n) / fs
            # FD whiten with a Welch PSD (mechanical; locked rule)
            nper = int(4 * fs)
            pf, psd = welch(data, fs=fs, nperseg=nper, noverlap=nper // 2)
            freqs = np.fft.rfftfreq(n, d=1 / fs)
            pv = np.interp(freqs, pf, psd)
            pv[pv <= 0] = np.inf
            white = np.fft.irfft(np.fft.rfft(data * tukey(n, 1.0 / 8.0)) / np.sqrt(pv), n=n)
            baseline_mask = times < (tc - 4.0)
            sigma = float(np.std(white[baseline_mask])) or 1.0
            lo, hi = tc - rule["window_before_tc"][0], tc - rule["window_before_tc"][1]
            window_mask = (times >= lo) & (times <= hi)
            z = np.abs(white) / sigma
            mf._GLITCH_GATE_RECORD["checked"] = True
            mf._GLITCH_GATE_RECORD["max_z_in_window"] = round(float(np.max(z[window_mask])), 2)
            if float(np.max(z[window_mask])) > rule["threshold_sigma"]:
                glitch_idx = int(np.argmax(z * window_mask))
                t_glitch = float(times[glitch_idx])
                half = rule["gate_half_width_s"]
                gate_mask = (times >= t_glitch - half) & (times <= t_glitch + half)
                gate_len = int(gate_mask.sum())
                inverse_tukey = 1.0 - tukey(gate_len, min(1.0, 2 * rule["taper_s"] / (2 * half)))
                data = data.copy()
                data[gate_mask] = data[gate_mask] * inverse_tukey
                mf._GLITCH_GATE_RECORD.update({"fired": True, "t_glitch_gps": round(t_glitch, 4)})
            return data

        mf._fetch_strain = _gated_fetch

    if "grb" in cfg:
        grb = cfg["grb"]
        original_receipt = mf._receipt

        def _receipt_with_grb(mode: str, payload: dict[str, Any]):  # noqa: ANN202
            if mode in ("confirm", "replicate") and "h1" in payload and "l1" in payload:
                merger = (float(payload["h1"]["peak_gps"]) + float(payload["l1"]["peak_gps"])) / 2.0
                delay = grb["trigger_gps"] - merger
                lo, hi = grb["delay_window_s"]
                payload["grb_association"] = {
                    "grb_trigger_gps": grb["trigger_gps"],
                    "recovered_merger_gps": round(merger, 4),
                    "gw_to_grb_delay_s": round(delay, 3),
                    "published_delay_s": 1.74,
                    "delay_window_s": [lo, hi],
                    "delay_consistent": bool(lo <= delay <= hi),
                }
            if mode == "confirm" and getattr(mf, "_GLITCH_GATE_RECORD", None):
                payload["l1_glitch_gate"] = dict(mf._GLITCH_GATE_RECORD)
            return original_receipt(mode, payload)

        mf._receipt = _receipt_with_grb
    return mf


def _canonical(value: Any) -> str:  # noqa: ANN401
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:  # noqa: ANN401
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _latest_receipt(event: str, mode: str) -> dict[str, Any]:
    candidates = sorted(_RECEIPT_DIR.glob(f"{event}_mf_{mode}_*.json"))
    if not candidates:
        raise SystemExit(f"missing {mode} receipt for {event} - run the preregistered sequence first")
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


async def promote(event: str, cfg: dict[str, Any]) -> int:
    """Register + attach external evidence + record replication + verify rung."""
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
    validate = _latest_receipt(event, "validate")
    control = _latest_receipt(event, "control")
    confirm = _latest_receipt(event, "confirm")
    replicate = _latest_receipt(event, "replicate")

    if not validate.get("instrument_valid"):
        raise SystemExit("instrument validation did not pass - no promotion")
    if not control.get("control_passed"):
        raise SystemExit("off-source control did not pass - no promotion")
    if not confirm.get("success"):
        raise SystemExit("confirmatory run did not succeed - preserve the negative, no promotion")
    close = abs(float(replicate["network_snr"]) - float(confirm["network_snr"])) / float(confirm["network_snr"]) <= 0.10
    if not (replicate.get("within_published_tolerance") and close):
        raise SystemExit("replication did not meet the preregistered criteria - no promotion")

    published = cfg["published_network_snr"]
    low = round(published * (1 - cfg["tolerance"]), 3)
    high = round(published * (1 + cfg["tolerance"]), 3)
    source_ref = f"GWOSC open data H1+L1 GPS {list(cfg['on_source'])}; {cfg['citation']}"
    hypothesis = (
        f"The public {event} strain data (GWOSC, H1+L1, GPS {list(cfg['on_source'])}) produce a "
        "quadrature sum of independently maximized single-detector matched-filter SNRs within "
        f"{int(cfg['tolerance'] * 100)} percent of the published network SNR {published}. This is a "
        "benchmark comparison, not an equivalent coincident network statistic."
    )
    primary_executor = "matched_filter_pipeline"

    record = await experiment_registry.register_experiment(
        redis,
        source="gw_replication",
        domain=cfg["domain"],
        hypothesis=hypothesis,
        status="graded",
        falsifier=f"Legacy two-detector recovery statistic outside the preregistered interval [{low}, {high}].",
        method=(
            "preregistered FFT matched filter, independently maximized H1/L1 peaks, quadrature sum, "
            "GWOSC template, Welch PSD, band 20-2048 Hz"
        ),
        rationale="Charter replication target: reproduce a published GW detection under a preregistered protocol.",
        inputs={
            "on_source_gps": confirm["h1"]["segment_gps"],
            "template_sha256": confirm["template_sha256"],
            "band_hz": [20.0, 2048.0],
            "preregistration": cfg["preregistration"],
        },
        parameters={"psd": "welch_mean_4s", "tolerance": cfg["tolerance"], "peak_window_s": 0.1},
        models_used=[],
        tools_used=["gwpy.fetch_open_data", "scipy.signal.welch", "numpy.fft"],
        primary_executor=primary_executor,
        source_refs=[source_ref],
        metrics={"confirmed": True, "recovered_statistic_value": confirm["network_snr"]},
        result={
            "network_snr": confirm["network_snr"],
            "recovered_statistic": confirm.get("recovered_statistic"),
            "published_network_snr": published,
            "preregistered_interval": confirm["preregistered_interval"],
            "h1_snr": confirm["h1"]["snr_peak"],
            "l1_snr": confirm["l1"]["snr_peak"],
            "h1_peak_gps": confirm["h1"]["peak_gps"],
            "l1_peak_gps": confirm["l1"]["peak_gps"],
            "offsource_control_max": control["network_snr_max_offsource"],
            # secondary preregistered claims ride in the same record, pass or
            # fail - a failed criterion is preserved, never dropped
            "grb_association": confirm.get("grb_association"),
            "l1_glitch_gate": confirm.get("l1_glitch_gate"),
        },
        tags=["gw_replication", "charter", event],
        artifact_payloads={
            "prereg_confirm_receipt.json": confirm,
            "prereg_control_receipt.json": control,
            "prereg_validate_receipt.json": validate,
        },
    )
    experiment_id = record.experiment_id
    print("registered:", experiment_id)

    observation = {
        "network_snr": confirm["network_snr"],
        "recovered_statistic": confirm.get("recovered_statistic"),
        "h1_snr": confirm["h1"]["snr_peak"],
        "l1_snr": confirm["l1"]["snr_peak"],
        "h1_peak_gps": confirm["h1"]["peak_gps"],
        "l1_peak_gps": confirm["l1"]["peak_gps"],
        "published_network_snr": published,
        "data_source": "GWOSC open strain data",
        "confirm_receipt_sha256": confirm.get("receipt_sha256", ""),
    }
    evidence_receipt = {
        "schema": "aigis.scientific_evidence_receipt.v1",
        "experiment_id": experiment_id,
        "verifier_id": "external_evidence_intake_v1",
        "source_ref": source_ref,
        "source_origin": "external",
        "produced_by": primary_executor,
        "observation_digest": _sha(observation),
        "observation": observation,
        "citation": cfg["citation"],
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    evidence_path = _RECEIPT_DIR / f"{experiment_id}_external_evidence.json"
    evidence_path.write_text(json.dumps(evidence_receipt, indent=2), encoding="utf-8")
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()

    evidence = make_evidence(
        kind=EvidenceKind.EXTERNAL_EXPERIMENTAL_RESULT,
        relation=EvidenceRelation.SUPPORTS,
        summary=(
            f"Preregistered matched filter produces legacy two-detector recovery statistic "
            f"{confirm['network_snr']} (published network SNR {published}) from public LIGO strain; off-source control max "
            f"{control['network_snr_max_offsource']} < 8. The LIGO measurement is the physical "
            "experiment; this computation is a benchmark and is not an equivalent coincident "
            "network statistic or physical validation."
        ),
        source_origin=EvidenceOrigin.EXTERNAL,
        source_ref=source_ref,
        receipt_ref=str(evidence_path),
        receipt_sha256=evidence_sha,
        produced_by=primary_executor,
        method_id="matched_filter_gwosc_template_v1",
        meaningful_test=True,
        metadata={"preregistration": cfg["preregistration"]},
    )
    updated = await experiment_registry.append_evidence(redis, experiment_id, evidence, actor="gw_replication")
    print("evidence attached; status:", updated.scientific_record.evidence_status.value)

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
        "primary_executor": primary_executor,
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
                abs(float(replicate["network_snr"]) - float(confirm["network_snr"])) / float(confirm["network_snr"]), 4
            ),
        },
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    repro_path = _RECEIPT_DIR / f"{experiment_id}_replication_receipt.json"
    repro_path.write_text(json.dumps(repro_receipt, indent=2), encoding="utf-8")

    attempt = make_reproduction_attempt(
        experiment_id=experiment_id,
        hypothesis=sci.hypothesis,
        outcome=ReproductionOutcome.CONFIRMED,
        executed_by="matched_filter_replicator",
        primary_executor=primary_executor,
        method_id="welch_median_16s_matched_filter_v1",
        receipt_ref=str(repro_path),
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

    import redis as redis_sync  # noqa: PLC0415

    raw = redis_sync.Redis(decode_responses=True).get(f"aigis:experiments:record:{experiment_id}")
    print("RAW re-read evidence_status:", json.loads(raw)["scientific_record"]["evidence_status"])
    print("experiment_id:", experiment_id)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, choices=sorted(EVENTS))
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--replicate", action="store_true")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()

    cfg = EVENTS[args.event]
    if args.promote:
        return asyncio.run(promote(args.event, cfg))

    mf = _load_instrument(args.event, cfg)
    if args.validate:
        out = mf.run_validate()
    elif args.control:
        out = mf.run_control()
    elif args.confirm:
        out = mf.run_confirm()
    elif args.replicate:
        out = mf.run_replicate()
    else:
        parser.print_help()
        return 2
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
