#!/usr/bin/env python3
"""Pure validation controls for the GW efficacy research package.

The original studies remain frozen.  This module validates follow-up evidence
without reading or writing AIGIS's live research stores.  Every control is
data-in/data-out so unit tests and future receipt builders can exercise the
same rules before an external-use claim is made.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

from scipy.stats import spearmanr  # type: ignore[missing-import]

# LIGO E950018-02 gives the approximately 10 ms maximum H1-L1 arrival-time
# separation. LIGO P1900004 describes a 10 ms time-of-flight term plus a 5 ms
# coalescence-time uncertainty for the analysis window. Keep them separate.
H1_L1_LIGHT_TRAVEL_MS = 10.0
DEFAULT_TIMING_MARGIN_MS = 5.0
MIN_SCRAMBLES_PER_EVENT = 100
MIN_PHASE_SCRAMBLE_EVENTS = 7
PHASE_SCRAMBLE_MEDIAN_MARGIN_MIN = 0.10
PHASE_SCRAMBLE_EMPIRICAL_P_MAX = 0.05
MIN_POSTERIOR_DRAWS_PER_EVENT = 100
MIN_POSTERIOR_EVENTS = 10
POSTERIOR_CRITERIA_PASS_FRACTION = 0.90
# Contract v3 (PI-approved 2026-07-16, OPERATOR-DECISIONS.md Decision B, commit
# 13eb7b848): the posterior gate's scientific PASS condition is the O1 trend
# criterion only -- rho(M_det, R) <= -0.5 preserved in at least 90% of joint
# draws. The revised paper (commit d66eddd5b) withdrew the posterior-robust-curve
# claim and now claims point-estimate-conditional transfer only, so the O2 curve
# criterion (median |R - R_hat| <= 0.15 preserved in at least 90% of draws) no
# longer gates PASS. O2 is NOT deleted: it stays computed and is reported in the
# gate output as the withdrawn-claim record -- its per-draw fraction, its original
# criterion, and its original fail verdict. The pre-v3 all-pass (O1 AND O2)
# contract is preserved here and in the record as the account of what was
# withdrawn; this is a documented block, not deleted history.
POSTERIOR_CONTRACT_VERSION = "v3"
POSTERIOR_V3_AUTHORIZATION = (
    "PI-approved 2026-07-16, OPERATOR-DECISIONS.md Decision B (commit 13eb7b848); "
    "original O2 per-draw criterion preserved below as the withdrawn-claim record"
)
MIN_ORACLE_GRID_POINTS = 12
MIN_ORACLE_MATCH = 0.99
MIN_PSD_EVENTS_PER_CONFIG = 10
MIN_FRESH_HOLDOUT_EVENTS = 5
# Study 3 has TWO distinct cohorts; one constant must not serve both.
# PRIMARY (inferential): the preregistration gives no verdict to events failing the
# off-source validity control, so they are excluded. 20 selected - 3 unavailable
# - 2 instrument-invalid = 15 verdict-bearing. This cohort carries the locked O1/O2
# claims (rho = -0.8704, p = 2.44e-05, median|R-Rhat| = 0.088) and is what
# STUDY3_RHO_MAX / STUDY3_MEDIAN_ABS_ERROR_MAX enforce.
STUDY3_EXPECTED_PRIMARY_VALID_EVENTS = 15
# AVAILABILITY-ONLY (diagnostic): 20 selected - 3 unavailable = 17, irrespective of
# the off-source verdict. Describes the paper's "6/17 non-coincident" count. Purely
# descriptive; it must never carry an inferential claim.
STUDY3_EXPECTED_AVAILABILITY_AUDIT_EVENTS = 17
MIN_STUDY3_COINCIDENT_EVENTS = 10
STUDY3_RHO_MAX = -0.5
STUDY3_MEDIAN_ABS_ERROR_MAX = 0.15
REQUIRED_PSD_CONFIGS = frozenset(
    {
        "onsource_welch_mean_4s",
        "offsource_welch_mean_4s",
        "onsource_welch_median_many_4s",
        "gated_onsource_welch_mean_4s",
    }
)

_MSUN_SECONDS = 4.925491025543576e-06


class EvidenceControlError(ValueError):
    """Raised when a proposed follow-up artifact cannot support its claim."""


def _finite(value: Any, *, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceControlError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise EvidenceControlError(f"{name} must be finite")
    return number


def _sha256(value: Any, *, name: str) -> str:
    digest = str(value).lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise EvidenceControlError(f"{name} must be a lowercase sha256 digest")
    return digest


def _content_sha256(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _timestamp(value: Any, *, name: str) -> datetime:
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise EvidenceControlError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceControlError(f"{name} must include a timezone")
    return parsed


def independent_peak_statistic(
    *,
    h1_snr: float,
    l1_snr: float,
    h1_gps: float,
    l1_gps: float,
    timing_margin_ms: float = DEFAULT_TIMING_MARGIN_MS,
) -> dict[str, Any]:
    """Describe the legacy quadrature statistic without calling it coincident.

    The physical H1-L1 light-travel bound and the analyst-selected timing
    margin are reported separately.  Passing the wider window is diagnostic;
    it does not retroactively turn independently selected peaks into a
    coincidence-enforcing search statistic.
    """

    h1 = _finite(h1_snr, name="h1_snr")
    l1 = _finite(l1_snr, name="l1_snr")
    t_h1 = _finite(h1_gps, name="h1_gps")
    t_l1 = _finite(l1_gps, name="l1_gps")
    margin = _finite(timing_margin_ms, name="timing_margin_ms")
    if h1 < 0 or l1 < 0:
        raise EvidenceControlError("SNR magnitudes must be non-negative")
    if margin < 0:
        raise EvidenceControlError("timing_margin_ms must be non-negative")

    separation_ms = abs(t_h1 - t_l1) * 1000.0
    window_ms = H1_L1_LIGHT_TRAVEL_MS + margin
    return {
        "statistic_name": "quadrature_of_independently_maximized_single_detector_snrs",
        "legacy_field_name": "network_snr",
        "value": round(math.hypot(h1, l1), 3),
        "coincidence_enforced": False,
        "h1_l1_separation_ms": round(separation_ms, 3),
        "physical_light_travel_bound_ms": H1_L1_LIGHT_TRAVEL_MS,
        "timing_margin_ms": margin,
        "coincidence_window_ms": window_ms,
        "within_physical_light_travel_bound": separation_ms <= H1_L1_LIGHT_TRAVEL_MS,
        "within_coincidence_window": separation_ms <= window_ms,
    }


def summarize_phase_scramble_ensemble(
    *,
    event: str,
    physical_recovery: float,
    scrambled_recoveries: Sequence[float],
) -> dict[str, Any]:
    """Return a finite-sample one-sided scramble-null summary.

    The empirical p-value uses the standard plus-one correction.  Fewer than
    100 scrambles remains an explicitly uncharacterized control rather than a
    small-sample pass.
    """

    physical = _finite(physical_recovery, name="physical_recovery")
    samples = [_finite(value, name="scrambled_recovery") for value in scrambled_recoveries]
    if not samples:
        raise EvidenceControlError("scrambled_recoveries cannot be empty")
    if any(value < 0 for value in [physical, *samples]):
        raise EvidenceControlError("recovery fractions must be non-negative")

    n_ge = sum(value >= physical for value in samples)
    n = len(samples)
    characterized = n >= MIN_SCRAMBLES_PER_EVENT
    return {
        "event": event,
        "physical_recovery": physical,
        "n_scrambles": n,
        "minimum_required": MIN_SCRAMBLES_PER_EVENT,
        "scramble_median": statistics.median(samples),
        "margin_vs_scramble_median": physical - statistics.median(samples),
        "scrambles_at_least_physical": n_ge,
        "empirical_p_one_sided": (n_ge + 1) / (n + 1),
        "characterized_ensemble": characterized,
        "claim_status": "computed_ensemble_null" if characterized else "insufficient_scramble_count",
    }


def validate_phase_scramble_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a multi-event phase-scramble artifact without grading novelty."""

    if payload.get("schema") != "aigis.gw.phase_scramble_ensemble.v1":
        raise EvidenceControlError("unexpected phase-scramble artifact schema")
    _sha256(payload.get("template_sha256"), name="template_sha256")
    rows_raw = payload.get("rows")
    if not isinstance(rows_raw, list) or not rows_raw:
        raise EvidenceControlError("phase-scramble artifact requires rows")
    rows: list[dict[str, Any]] = []
    seen_events: set[str] = set()
    for index, row in enumerate(rows_raw):
        if not isinstance(row, Mapping):
            raise EvidenceControlError(f"rows[{index}] must be an object")
        event = str(row.get("event", "")).strip()
        if not event or event in seen_events:
            raise EvidenceControlError("phase-scramble events must be non-empty and unique")
        seen_events.add(event)
        scrambles = row.get("scrambles")
        if not isinstance(scrambles, list):
            raise EvidenceControlError("each phase-scramble row requires a scrambles list")
        seeds: list[str] = []
        recoveries: list[float] = []
        for scramble_index, scramble in enumerate(scrambles):
            if not isinstance(scramble, Mapping):
                raise EvidenceControlError(f"scrambles[{scramble_index}] must be an object")
            seed = str(scramble.get("seed", "")).strip()
            if not seed:
                raise EvidenceControlError("every scramble requires a seed")
            seeds.append(seed)
            recoveries.append(_finite(scramble.get("recovery"), name="scramble recovery"))
        if len(set(seeds)) != len(seeds):
            raise EvidenceControlError(f"{event} contains duplicate scramble seeds")
        rows.append(
            summarize_phase_scramble_ensemble(
                event=event,
                physical_recovery=_finite(
                    row.get("physical_recovery"),
                    name="physical_recovery",
                ),
                scrambled_recoveries=recoveries,
            )
        )
    structurally_complete = bool(
        len(rows) >= MIN_PHASE_SCRAMBLE_EVENTS and all(row["characterized_ensemble"] for row in rows)
    )
    median_margin = statistics.median(row["margin_vs_scramble_median"] for row in rows)
    significant_events = sum(
        row["margin_vs_scramble_median"] > 0 and row["empirical_p_one_sided"] <= PHASE_SCRAMBLE_EMPIRICAL_P_MAX
        for row in rows
    )
    required_significant_events = max(6, math.ceil(0.8 * len(rows)))
    scientific_pass = bool(
        structurally_complete
        and median_margin >= PHASE_SCRAMBLE_MEDIAN_MARGIN_MIN
        and significant_events >= required_significant_events
    )
    status = "pass" if scientific_pass else ("fail" if structurally_complete else "blocked")
    return {
        "status": status,
        "complete": structurally_complete,
        "scientific_pass": scientific_pass,
        "minimum_events": MIN_PHASE_SCRAMBLE_EVENTS,
        "median_margin": median_margin,
        "significant_events": significant_events,
        "required_significant_events": required_significant_events,
        "thresholds": {
            "median_margin_min": PHASE_SCRAMBLE_MEDIAN_MARGIN_MIN,
            "empirical_p_max": PHASE_SCRAMBLE_EMPIRICAL_P_MAX,
        },
        "events": rows,
        "reason": None
        if scientific_pass
        else (
            "ensemble coherence criteria failed"
            if structurally_complete
            else "at least 7 unique events each require 100 unique scramble seeds"
        ),
    }


def summarize_psd_robustness(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Compare recovery and mass-trend statistics across required PSD regimes."""

    if payload.get("schema") != "aigis.gw.psd_robustness.v1":
        raise EvidenceControlError("unexpected PSD-robustness artifact schema")
    _sha256(payload.get("strain_manifest_sha256"), name="strain_manifest_sha256")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise EvidenceControlError("PSD robustness artifact requires rows")

    by_config: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    mass_by_event: dict[str, float] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise EvidenceControlError(f"rows[{index}] must be an object")
        event = str(row.get("event", "")).strip()
        config = str(row.get("psd_config", "")).strip()
        if not event or not config:
            raise EvidenceControlError("PSD rows require event and psd_config")
        pair = (event, config)
        if pair in seen_pairs:
            raise EvidenceControlError(f"duplicate PSD event/config row: {event}/{config}")
        seen_pairs.add(pair)
        mass = _finite(row.get("m_total_det"), name="m_total_det")
        recovery = _finite(row.get("recovery_fraction"), name="recovery_fraction")
        if mass <= 0 or recovery < 0:
            raise EvidenceControlError("mass must be positive and recovery non-negative")
        prior_mass = mass_by_event.setdefault(event, mass)
        if not math.isclose(prior_mass, mass, rel_tol=0.0, abs_tol=1e-9):
            raise EvidenceControlError(f"inconsistent detector-frame mass for {event}")
        by_config[config].append((mass, recovery, event))

    missing = sorted(REQUIRED_PSD_CONFIGS - set(by_config))
    event_sets = {config: {event for _, _, event in values} for config, values in by_config.items()}
    required_event_sets = [event_sets[config] for config in REQUIRED_PSD_CONFIGS if config in event_sets]
    comparable = bool(required_event_sets) and all(events == required_event_sets[0] for events in required_event_sets)

    config_stats: dict[str, Any] = {}
    baseline_by_event = {event: recovery for _, recovery, event in by_config.get("onsource_welch_mean_4s", [])}
    too_small: list[str] = []
    invalid_correlations: list[str] = []
    for config, values in sorted(by_config.items()):
        masses = [mass for mass, _, _ in values]
        recoveries = [recovery for _, recovery, _ in values]
        if config in REQUIRED_PSD_CONFIGS and len(values) < MIN_PSD_EVENTS_PER_CONFIG:
            too_small.append(config)
        rho_value: float | None = None
        p_value_float: float | None = None
        if len(set(masses)) > 1 and len(set(recoveries)) > 1:
            rho, p_value = spearmanr(masses, recoveries)
            if math.isfinite(float(rho)) and math.isfinite(float(p_value)):
                rho_value = float(rho)
                p_value_float = float(p_value)
        if config in REQUIRED_PSD_CONFIGS and (rho_value is None or p_value_float is None):
            invalid_correlations.append(config)
        deltas = [
            abs(recovery - baseline_by_event[event]) for _, recovery, event in values if event in baseline_by_event
        ]
        config_stats[config] = {
            "n_events": len(values),
            "spearman_rho": rho_value,
            "spearman_p": p_value_float,
            "median_recovery": statistics.median(recoveries),
            "median_abs_delta_vs_onsource_mean4s": statistics.median(deltas) if deltas else None,
        }

    structurally_complete = not missing and comparable and not too_small and not invalid_correlations
    trend_failures = sorted(
        config
        for config in REQUIRED_PSD_CONFIGS
        if config_stats.get(config, {}).get("spearman_rho") is not None
        and config_stats[config]["spearman_rho"] > STUDY3_RHO_MAX
    )
    scientific_pass = bool(structurally_complete and not trend_failures)
    status = "pass" if scientific_pass else ("fail" if structurally_complete else "blocked")
    return {
        "status": status,
        "complete": structurally_complete,
        "scientific_pass": scientific_pass,
        "missing_psd_configs": missing,
        "minimum_events_per_config": MIN_PSD_EVENTS_PER_CONFIG,
        "undersized_psd_configs": sorted(too_small),
        "invalid_spearman_configs": sorted(invalid_correlations),
        "trend_threshold_spearman_rho_max": STUDY3_RHO_MAX,
        "trend_failure_configs": trend_failures,
        "same_event_set_across_required_configs": comparable,
        "configs": config_stats,
        "reason": (
            None
            if scientific_pass
            else (
                "mass-trend criterion failed under at least one PSD regime"
                if structurally_complete
                else "required PSD regimes need unique rows, the same event set, enough events, and finite Spearman statistics"
            )
        ),
    }


def summarize_posterior_uncertainty(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize detector-frame mass, ISCO, and recovery over posterior draws."""

    if payload.get("schema") != "aigis.gw.posterior_uncertainty.v1":
        raise EvidenceControlError("unexpected posterior artifact schema")
    if payload.get("analysis_scope") != "study3_oos":
        raise EvidenceControlError("posterior analysis_scope must be study3_oos")
    _sha256(payload.get("posterior_source_sha256"), name="posterior_source_sha256")
    draws = payload.get("draws")
    if not isinstance(draws, list) or not draws:
        raise EvidenceControlError("posterior artifact requires draws")

    by_event: dict[str, list[dict[str, float]]] = defaultdict(list)
    by_draw: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    seen_draws: set[tuple[str, str]] = set()
    for index, draw in enumerate(draws):
        if not isinstance(draw, Mapping):
            raise EvidenceControlError(f"draws[{index}] must be an object")
        event = str(draw.get("event", "")).strip()
        if not event:
            raise EvidenceControlError("posterior draw requires event")
        draw_id = str(draw.get("draw_id", "")).strip()
        if not draw_id:
            raise EvidenceControlError("posterior draw requires draw_id")
        draw_key = (event, draw_id)
        if draw_key in seen_draws:
            raise EvidenceControlError(f"duplicate posterior draw: {event}/{draw_id}")
        seen_draws.add(draw_key)
        m1 = _finite(draw.get("mass_1_source"), name="mass_1_source")
        m2 = _finite(draw.get("mass_2_source"), name="mass_2_source")
        redshift = _finite(draw.get("redshift"), name="redshift")
        recovery = _finite(draw.get("recovery_fraction"), name="recovery_fraction")
        predicted = _finite(draw.get("predicted_recovery"), name="predicted_recovery")
        if m1 <= 0 or m2 <= 0 or redshift < 0 or recovery < 0 or predicted < 0:
            raise EvidenceControlError("posterior mass must be positive; redshift/recovery non-negative")
        detector_mass = (m1 + m2) * (1.0 + redshift)
        f_isco = 1.0 / (6.0**1.5 * math.pi * detector_mass * _MSUN_SECONDS)
        by_event[event].append(
            {
                "m_total_det": detector_mass,
                "f_isco_hz": f_isco,
                "recovery_fraction": recovery,
            }
        )
        by_draw[draw_id].append(
            {
                "event": event,
                "m_total_det": detector_mass,
                "recovery_fraction": recovery,
                "predicted_recovery": predicted,
            }
        )

    def quantiles(values: Iterable[float]) -> dict[str, float]:
        ordered = sorted(values)
        n = len(ordered)

        def pick(frac: float) -> float:
            return ordered[round((n - 1) * frac)]

        return {"q05": pick(0.05), "q50": pick(0.50), "q95": pick(0.95)}

    summaries: dict[str, Any] = {}
    insufficient: list[str] = []
    for event, event_draws in sorted(by_event.items()):
        if len(event_draws) < MIN_POSTERIOR_DRAWS_PER_EVENT:
            insufficient.append(event)
        summaries[event] = {
            "n_draws": len(event_draws),
            "m_total_det": quantiles(row["m_total_det"] for row in event_draws),
            "f_isco_hz": quantiles(row["f_isco_hz"] for row in event_draws),
            "recovery_fraction": quantiles(row["recovery_fraction"] for row in event_draws),
        }

    event_names = set(by_event)
    aligned_draws = all({str(row["event"]) for row in draw_rows} == event_names for draw_rows in by_draw.values())
    draw_metrics: list[dict[str, float | str]] = []
    for draw_id, draw_rows in sorted(by_draw.items()):
        masses = [float(row["m_total_det"]) for row in draw_rows]
        recoveries = [float(row["recovery_fraction"]) for row in draw_rows]
        if len(set(masses)) <= 1 or len(set(recoveries)) <= 1:
            continue
        rho, p_value = spearmanr(masses, recoveries)
        rho_float = float(rho)
        p_float = float(p_value)
        if not (math.isfinite(rho_float) and math.isfinite(p_float)):
            continue
        draw_metrics.append(
            {
                "draw_id": draw_id,
                "spearman_rho": rho_float,
                "spearman_p": p_float,
                "median_abs_prediction_error": statistics.median(
                    abs(float(row["recovery_fraction"]) - float(row["predicted_recovery"])) for row in draw_rows
                ),
            }
        )
    structurally_complete = bool(
        len(event_names) >= MIN_POSTERIOR_EVENTS
        and len(by_draw) >= MIN_POSTERIOR_DRAWS_PER_EVENT
        and not insufficient
        and aligned_draws
        and len(draw_metrics) == len(by_draw)
    )
    rho_pass_fraction = (
        sum(float(row["spearman_rho"]) <= STUDY3_RHO_MAX for row in draw_metrics) / len(draw_metrics)
        if draw_metrics
        else 0.0
    )
    prediction_pass_fraction = (
        sum(float(row["median_abs_prediction_error"]) <= STUDY3_MEDIAN_ABS_ERROR_MAX for row in draw_metrics)
        / len(draw_metrics)
        if draw_metrics
        else 0.0
    )
    # Contract v3: PASS gates on the O1 trend criterion only. O2 (the withdrawn
    # posterior-robust-curve criterion) is still computed and preserved below as
    # the withdrawn-claim record; it no longer contributes to scientific_pass.
    trend_criterion_met = rho_pass_fraction >= POSTERIOR_CRITERIA_PASS_FRACTION
    prediction_criterion_met = prediction_pass_fraction >= POSTERIOR_CRITERIA_PASS_FRACTION
    scientific_pass = bool(structurally_complete and trend_criterion_met)
    status = "pass" if scientific_pass else ("fail" if structurally_complete else "blocked")
    # Withdrawn-claim record: the original O2 per-draw curve criterion, its
    # original required pass fraction, and its ORIGINAL fail/pass verdict
    # (recomputed from the data so the record cannot rot), stamped withdrawn with
    # the v3 authorization. This is the record of the claim the revised paper
    # dropped; the pre-v3 contract required BOTH O1 (trend) and O2 (curve) to pass.
    withdrawn_claim_record = {
        "criterion": "posterior_robust_prediction_curve",
        "description": "median |R - R_hat(M_det)| <= 0.15 preserved in at least 90% of joint draws",
        "median_abs_prediction_error_max": STUDY3_MEDIAN_ABS_ERROR_MAX,
        "per_draw_pass_fraction": prediction_pass_fraction,
        "required_pass_fraction": POSTERIOR_CRITERIA_PASS_FRACTION,
        "original_verdict": "pass" if prediction_criterion_met else "fail",
        "pre_v3_contract": "scientific_pass required O1 (trend) AND O2 (curve)",
        "withdrawn": True,
        "withdrawn_rationale": (
            "revised paper (commit d66eddd5b) withdrew the posterior-robust-curve "
            "claim; it claims point-estimate-conditional transfer only"
        ),
        "authorization": POSTERIOR_V3_AUTHORIZATION,
    }
    return {
        "status": status,
        "complete": structurally_complete,
        "scientific_pass": scientific_pass,
        "contract_version": POSTERIOR_CONTRACT_VERSION,
        "v3_authorization": POSTERIOR_V3_AUTHORIZATION,
        "scientific_pass_criterion": "trend_only_O1",
        "minimum_draws_per_event": MIN_POSTERIOR_DRAWS_PER_EVENT,
        "minimum_events": MIN_POSTERIOR_EVENTS,
        "insufficient_events": insufficient,
        "aligned_joint_draws": aligned_draws,
        "n_joint_draws": len(by_draw),
        "n_finite_draw_metrics": len(draw_metrics),
        "rho_criterion_pass_fraction": rho_pass_fraction,
        "prediction_criterion_pass_fraction": prediction_pass_fraction,
        "required_criteria_pass_fraction": POSTERIOR_CRITERIA_PASS_FRACTION,
        "withdrawn_claim_record": withdrawn_claim_record,
        "thresholds": {
            "spearman_rho_max": STUDY3_RHO_MAX,
            "median_abs_prediction_error_max": STUDY3_MEDIAN_ABS_ERROR_MAX,
        },
        "events": summaries,
        "reason": None
        if scientific_pass
        else (
            "posterior trend criterion O1 (rho <= -0.5) failed"
            if structurally_complete
            else "at least 10 events need the same 100+ unique joint draw IDs with finite recomputed criteria"
        ),
    }


def validate_oracle_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate matches against an independently implemented PhenomD backend."""

    if payload.get("schema") != "aigis.gw.phenomd_oracle.v1":
        raise EvidenceControlError("unexpected PhenomD oracle artifact schema")
    backend = str(payload.get("backend", ""))
    if backend not in {"lalsimulation", "pycbc"}:
        raise EvidenceControlError("oracle backend must be lalsimulation or pycbc")
    if payload.get("independent_implementation") is not True:
        raise EvidenceControlError("oracle must declare an independent implementation")
    if payload.get("comparison_mode") != "exact_phenomd":
        raise EvidenceControlError("oracle comparison_mode must be exact_phenomd")
    _sha256(payload.get("oracle_environment_sha256"), name="oracle_environment_sha256")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) < MIN_ORACLE_GRID_POINTS:
        raise EvidenceControlError(f"oracle grid requires at least {MIN_ORACLE_GRID_POINTS} rows")
    match_floor = _finite(payload.get("match_floor"), name="match_floor")
    if match_floor < MIN_ORACLE_MATCH or match_floor > 1:
        raise EvidenceControlError(f"match_floor must be in [{MIN_ORACLE_MATCH}, 1]")
    matches: list[float] = []
    grid_points: set[str] = set()
    required_parameters = {"mass1_msun", "mass2_msun", "chi1z", "chi2z", "f_min_hz"}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise EvidenceControlError(f"oracle rows[{index}] must be an object")
        parameters = row.get("parameters")
        if not isinstance(parameters, Mapping) or not required_parameters.issubset(parameters):
            raise EvidenceControlError("each oracle row requires the exact-PhenomD parameter set")
        m1 = _finite(parameters["mass1_msun"], name="mass1_msun")
        m2 = _finite(parameters["mass2_msun"], name="mass2_msun")
        chi1 = _finite(parameters["chi1z"], name="chi1z")
        chi2 = _finite(parameters["chi2z"], name="chi2z")
        f_min = _finite(parameters["f_min_hz"], name="f_min_hz")
        if m1 <= 0 or m2 <= 0 or f_min <= 0 or not (-1 <= chi1 <= 1 and -1 <= chi2 <= 1):
            raise EvidenceControlError("oracle masses/frequency must be positive and spins in [-1, 1]")
        identity = _content_sha256(
            {
                "mass1_msun": m1,
                "mass2_msun": m2,
                "chi1z": chi1,
                "chi2z": chi2,
                "f_min_hz": f_min,
            }
        )
        if identity in grid_points:
            raise EvidenceControlError("oracle grid points must be unique")
        grid_points.add(identity)
        match = _finite(row.get("match"), name="match")
        if match < 0 or match > 1:
            raise EvidenceControlError("each oracle row requires a match in [0, 1]")
        matches.append(match)
    minimum = min(matches)
    passed = minimum >= match_floor
    return {
        "status": "pass" if passed else "fail",
        "complete": True,
        "backend": backend,
        "grid_size": len(rows),
        "minimum_match": minimum,
        "match_floor": match_floor,
        "code_owned_minimum_match": MIN_ORACLE_MATCH,
        "comparison_mode": "exact_phenomd",
        "passed": passed,
    }


def validate_study3_coincidence_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Require new Study-3 rows to carry both detector peak times."""

    if payload.get("schema") != "aigis.gw.study3_coincidence.v1":
        raise EvidenceControlError("unexpected Study-3 coincidence artifact schema")
    _sha256(payload.get("source_receipt_sha256"), name="source_receipt_sha256")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise EvidenceControlError("Study-3 coincidence artifact requires rows")
    audited: list[dict[str, Any]] = []
    seen_events: set[str] = set()
    unaccounted: list[str] = []
    included_measurements: list[tuple[float, float, float]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise EvidenceControlError(f"rows[{index}] must be an object")
        event = str(row.get("event", "")).strip()
        if not event or event in seen_events:
            raise EvidenceControlError("Study-3 coincidence events must be non-empty and unique")
        seen_events.add(event)
        result = independent_peak_statistic(
            h1_snr=row["h1_snr"],
            l1_snr=row["l1_snr"],
            h1_gps=row["h1_peak_gps"],
            l1_gps=row["l1_peak_gps"],
        )
        expected_disposition = (
            "included_within_window" if result["within_coincidence_window"] else "excluded_outside_window"
        )
        disposition = str(row.get("analysis_disposition", ""))
        if disposition != expected_disposition:
            unaccounted.append(event)
        mass = _finite(row.get("m_total_det"), name="m_total_det")
        recovery = _finite(row.get("recovery_fraction"), name="recovery_fraction")
        predicted = _finite(row.get("predicted_recovery"), name="predicted_recovery")
        if mass <= 0 or recovery < 0 or predicted < 0:
            raise EvidenceControlError("Study-3 mass must be positive and recoveries non-negative")
        if disposition == "included_within_window":
            included_measurements.append((mass, recovery, predicted))
        audited.append(
            {
                "event": event,
                "analysis_disposition": disposition,
                "m_total_det": mass,
                "recovery_fraction": recovery,
                "predicted_recovery": predicted,
                **result,
            }
        )
    declared_audit_digest = _sha256(payload.get("audited_rows_sha256"), name="audited_rows_sha256")
    digest_matches = declared_audit_digest == _content_sha256(audited)
    enough_included = len(included_measurements) >= MIN_STUDY3_COINCIDENT_EVENTS
    recomputed_metrics: dict[str, Any] = {
        "n_included": len(included_measurements),
        "spearman_rho": None,
        "spearman_p": None,
        "median_abs_prediction_error": None,
    }
    metrics_finite = False
    if enough_included:
        masses = [mass for mass, _, _ in included_measurements]
        recoveries = [recovery for _, recovery, _ in included_measurements]
        if len(set(masses)) > 1 and len(set(recoveries)) > 1:
            rho, p_value = spearmanr(masses, recoveries)
            if math.isfinite(float(rho)) and math.isfinite(float(p_value)):
                recomputed_metrics.update(
                    {
                        "spearman_rho": float(rho),
                        "spearman_p": float(p_value),
                        "median_abs_prediction_error": statistics.median(
                            abs(recovery - predicted) for _, recovery, predicted in included_measurements
                        ),
                    }
                )
                metrics_finite = True
    declared_result_digest = _sha256(
        payload.get("recomputed_result_sha256"),
        name="recomputed_result_sha256",
    )
    result_digest_matches = declared_result_digest == _content_sha256(recomputed_metrics)
    structurally_complete = (
        len(audited) == STUDY3_EXPECTED_PRIMARY_VALID_EVENTS
        and not unaccounted
        and digest_matches
        and enough_included
        and metrics_finite
        and result_digest_matches
    )
    scientific_pass = bool(
        structurally_complete
        and recomputed_metrics["spearman_rho"] <= STUDY3_RHO_MAX
        and recomputed_metrics["median_abs_prediction_error"] <= STUDY3_MEDIAN_ABS_ERROR_MAX
    )
    status = "pass" if scientific_pass else ("fail" if structurally_complete else "blocked")
    return {
        "status": status,
        "complete": structurally_complete,
        "scientific_pass": scientific_pass,
        "n_expected": STUDY3_EXPECTED_PRIMARY_VALID_EVENTS,
        "n_audited": len(audited),
        "n_unique_events": len(seen_events),
        "n_within_window": sum(row["within_coincidence_window"] for row in audited),
        "minimum_included_events": MIN_STUDY3_COINCIDENT_EVENTS,
        "unaccounted_events": unaccounted,
        "audited_rows_digest_matches": digest_matches,
        "recomputed_result_digest_matches": result_digest_matches,
        "recomputed_metrics": recomputed_metrics,
        "thresholds": {
            "spearman_rho_max": STUDY3_RHO_MAX,
            "median_abs_prediction_error_max": STUDY3_MEDIAN_ABS_ERROR_MAX,
        },
        "rows": audited,
        "reason": None
        if scientific_pass
        else (
            "recomputed Study-3 criteria failed"
            if structurally_complete
            else "all 16 unique measured events need classified peak times, >=10 included rows, and content-bound finite recomputation"
        ),
    }


def validate_fresh_holdout_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate chronology and completion fields for the final untouched holdout."""

    if payload.get("schema") != "aigis.gw.fresh_holdout.v1":
        raise EvidenceControlError("unexpected fresh-holdout artifact schema")
    catalog_release = str(payload.get("catalog_release", "")).strip()
    if not catalog_release:
        raise EvidenceControlError("fresh holdout requires catalog_release")
    events_raw = payload.get("events")
    development_raw = payload.get("development_events")
    if not isinstance(events_raw, list) or not isinstance(development_raw, list):
        raise EvidenceControlError("fresh holdout requires events and development_events lists")
    events = [str(event).strip() for event in events_raw]
    development_events = [str(event).strip() for event in development_raw]
    if len(events) < MIN_FRESH_HOLDOUT_EVENTS or any(not event for event in events):
        raise EvidenceControlError(f"fresh holdout requires at least {MIN_FRESH_HOLDOUT_EVENTS} named events")
    if len(set(events)) != len(events) or len(set(development_events)) != len(development_events):
        raise EvidenceControlError("holdout and development event lists cannot contain duplicates")
    cohort_digest = _sha256(payload.get("cohort_manifest_sha256"), name="cohort_manifest_sha256")
    development_digest = _sha256(
        payload.get("development_manifest_sha256"),
        name="development_manifest_sha256",
    )
    cohort_bound = cohort_digest == _content_sha256({"catalog_release": catalog_release, "events": events})
    development_bound = development_digest == _content_sha256(development_events)
    _sha256(payload.get("template_commit_sha256"), name="template_commit_sha256")
    _sha256(payload.get("freeze_receipt_sha256"), name="freeze_receipt_sha256")
    _sha256(payload.get("evaluation_receipt_sha256"), name="evaluation_receipt_sha256")
    result = payload.get("result")
    if not isinstance(result, Mapping) or not result:
        raise EvidenceControlError("fresh holdout requires a non-empty result object")
    result_digest = _sha256(payload.get("result_sha256"), name="result_sha256")
    result_bound = result_digest == _content_sha256(dict(result))
    outcome = str(payload.get("outcome", ""))
    if outcome not in {"confirmed", "falsified", "inconclusive"}:
        raise EvidenceControlError("fresh holdout outcome must be confirmed, falsified, or inconclusive")
    template_locked_at = _timestamp(payload.get("template_locked_at"), name="template_locked_at")
    cohort_frozen_at = _timestamp(payload.get("cohort_frozen_at"), name="cohort_frozen_at")
    evaluation_started_at = _timestamp(payload.get("evaluation_started_at"), name="evaluation_started_at")
    evaluation_completed_at = _timestamp(payload.get("evaluation_completed_at"), name="evaluation_completed_at")
    chronology = template_locked_at <= cohort_frozen_at < evaluation_started_at <= evaluation_completed_at
    no_reuse = set(events).isdisjoint(development_events)
    passed = bool(cohort_bound and development_bound and result_bound and chronology and no_reuse)
    return {
        "status": "pass" if passed else "blocked",
        "complete": passed,
        "minimum_holdout_events": MIN_FRESH_HOLDOUT_EVENTS,
        "n_holdout_events": len(events),
        "cohort_manifest_bound": cohort_bound,
        "development_manifest_bound": development_bound,
        "result_bound": result_bound,
        "outcome": outcome,
        "chronology_verified": chronology,
        "development_reuse_excluded": no_reuse,
        "evaluation_complete": evaluation_completed_at >= evaluation_started_at,
        "reason": (
            None
            if passed
            else "holdout must be content-bound, template-locked before cohort freeze, development-naive, and receipted"
        ),
    }


def local_oracle_backend_status() -> dict[str, Any]:
    """Report local package availability without treating availability as validation."""

    available = {name: importlib.util.find_spec(name) is not None for name in ("lalsimulation", "pycbc")}
    return {
        "available": available,
        "any_backend_available": any(available.values()),
        "oracle_validated": False,
        "note": "package availability is not an oracle result; a match-grid artifact is still required",
    }


def reason_counts(results: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Compact helper for machine-readable readiness summaries."""

    return dict(Counter(str(result.get("status", "unknown")) for result in results))
