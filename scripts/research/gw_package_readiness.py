#!/usr/bin/env python3
"""Fail-closed analysis-readiness audit for the GW efficacy package.

The command is read-only.  Missing follow-up artifacts remain ``blocked`` and
cannot be converted into a pass by prose in the paper or reviewer response.
Passing local artifacts can make the package ready for external review, but
cannot authorize external publication without a separately verified immutable
trust-domain anchor.

Usage:
    python scripts/research/gw_package_readiness.py
    python scripts/research/gw_package_readiness.py --artifacts-dir /path/to/followups
    python scripts/research/gw_package_readiness.py --require-analysis-ready-for-external-review
    python scripts/research/gw_package_readiness.py --require-external-ready
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

try:
    from scripts.research.gw_evidence_controls import (
        EvidenceControlError,
        local_oracle_backend_status,
        reason_counts,
        summarize_posterior_uncertainty,
        summarize_psd_robustness,
        validate_fresh_holdout_artifact,
        validate_oracle_artifact,
        validate_phase_scramble_artifact,
        validate_study3_coincidence_artifact,
    )
except ModuleNotFoundError:  # direct ``python scripts/research/...`` execution
    from gw_evidence_controls import (  # type: ignore[no-redef]
        EvidenceControlError,
        local_oracle_backend_status,
        reason_counts,
        summarize_posterior_uncertainty,
        summarize_psd_robustness,
        validate_fresh_holdout_artifact,
        validate_oracle_artifact,
        validate_phase_scramble_artifact,
        validate_study3_coincidence_artifact,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "docs" / "research" / "papers" / "gw-inspiral-template-efficacy"
SCRIPTS_DIR = REPO_ROOT / "scripts" / "research"

_CLAIM_PATTERNS = {
    "unqualified_experimental_validation": re.compile(
        r"\*\*Status:\*\*\s*`?experimentally_validated|independent experimental validation\s+(?:was|is)\s+achieved",
        re.IGNORECASE,
    ),
    "independent_same_project_replication": re.compile(
        r"two\s+independent\s+confirmed\s+replications|independent\s+replication\s+binds",
        re.IGNORECASE,
    ),
    "incorrect_light_travel_wording": re.compile(r"15\s*ms\s+light[- ]travel\s+bound", re.IGNORECASE),
    "reused_cohort_called_oos": re.compile(r"in[- ]sample\s+and\s+out\s+of\s+sample", re.IGNORECASE),
    "coherence_overclaim": re.compile(r"coherence\s+proven", re.IGNORECASE),
}

_SCRIPT_PATTERNS = {
    "reused_cohort_serialized_as_oos": re.compile(r'"(?:P3_oos_heavy_arm|Q3_oos_arm|S3_oos_arm|R2_oos_arm)"'),
    "same_project_declared_independent": re.compile(
        r'independence_basis\s*=\s*\(\s*"independent re-analysis',
        re.IGNORECASE,
    ),
}

_SCRIPT_SCOPE_FILES = (
    "imr_heavy_study.py",
    "imr_coherence_study.py",
    "phenomd_phase_study.py",
    "phenomd_phase_replication.py",
    "gw_event_replication.py",
    "promote_gw150914.py",
)

_ARTIFACT_VALIDATORS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "phenomd_external_oracle": validate_oracle_artifact,
    "psd_robustness": summarize_psd_robustness,
    "phase_scramble_ensemble": validate_phase_scramble_artifact,
    "posterior_uncertainty": summarize_posterior_uncertainty,
    "study3_coincidence": validate_study3_coincidence_artifact,
    "fresh_untouched_holdout": validate_fresh_holdout_artifact,
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting duplicate keys at every depth."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceControlError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_artifact_object(artifact_bytes: bytes) -> Mapping[str, Any]:
    """Parse one evidence artifact as a duplicate-free JSON object."""

    payload = json.loads(artifact_bytes, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(payload, dict):
        raise EvidenceControlError("artifact root must be a JSON object")
    return payload


def audit_claim_scope(package_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    """Find only residual unqualified claims, not historical quoted labels."""

    findings: list[dict[str, Any]] = []
    for path in sorted(package_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        flattened = re.sub(r"\s+", " ", text)
        for finding, pattern in _CLAIM_PATTERNS.items():
            match = pattern.search(flattened)
            if match is not None:
                findings.append(
                    {
                        "finding": finding,
                        "file": path.name,
                        "matched_text": match.group(0),
                    }
                )
    return {
        "status": "pass" if not findings else "fail",
        "passed": not findings,
        "findings": findings,
    }


def audit_script_scope(scripts_dir: Path = SCRIPTS_DIR) -> dict[str, Any]:
    """Prevent new receipts from recreating the corrected semantic claims."""

    findings: list[dict[str, Any]] = []
    missing: list[str] = []
    for name in _SCRIPT_SCOPE_FILES:
        path = scripts_dir / name
        if not path.is_file():
            missing.append(name)
            continue
        flattened = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for finding, pattern in _SCRIPT_PATTERNS.items():
            match = pattern.search(flattened)
            if match is not None:
                findings.append(
                    {
                        "finding": finding,
                        "file": name,
                        "matched_text": match.group(0),
                    }
                )
    passed = not findings and not missing
    return {
        "status": "pass" if passed else "fail",
        "passed": passed,
        "findings": findings,
        "missing_files": missing,
    }


def _artifact_gate(name: str, path: Path, validator: Callable[[Mapping[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    if not path.is_file():
        return {
            "gate": name,
            "status": "blocked",
            "complete": False,
            "artifact": str(path),
            "reason": "follow-up artifact is missing",
        }
    try:
        artifact_bytes = path.read_bytes()
        payload = _load_artifact_object(artifact_bytes)
        result = validator(payload)
    except (EvidenceControlError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "gate": name,
            "status": "fail",
            "complete": False,
            "artifact": str(path),
            "reason": str(exc),
        }
    return {
        "gate": name,
        "artifact": str(path),
        "artifact_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        **result,
    }


def build_readiness(
    *,
    package_dir: Path = PACKAGE_DIR,
    artifacts_dir: Path | None = None,
    scripts_dir: Path = SCRIPTS_DIR,
) -> dict[str, Any]:
    """Build the package status without reading mutable AIGIS stores."""

    artifact_root = artifacts_dir or package_dir / "verification"
    claim_scope = audit_claim_scope(package_dir)
    script_scope = audit_script_scope(scripts_dir)
    gates = [
        _artifact_gate(name, artifact_root / f"{name}.json", validator)
        for name, validator in _ARTIFACT_VALIDATORS.items()
    ]
    analysis_ready_for_external_review = bool(
        claim_scope["passed"] and script_scope["passed"] and all(gate.get("status") == "pass" for gate in gates)
    )
    external_publication_gate = {
        "status": "blocked",
        "complete": False,
        "external_trust_anchor_required": True,
        "attestation_validator_implemented": False,
        "reason": (
            "local same-operator JSON hashes and git history are not an external immutable trust anchor, "
            "and this audit does not implement an external-attestation validator"
        ),
    }
    return {
        "schema": "aigis.gw.package_readiness.v2",
        "package": str(package_dir),
        "claim_scope": claim_scope,
        "script_scope": script_scope,
        "local_oracle_backend": local_oracle_backend_status(),
        "follow_up_gates": gates,
        "gate_status_counts": reason_counts(gates),
        "analysis_ready_for_external_review": analysis_ready_for_external_review,
        "external_publication_gate": external_publication_gate,
        "external_ready": False,
        "epistemic_status": (
            "analysis_ready_for_external_review" if analysis_ready_for_external_review else "major_revision_open"
        ),
        "note": (
            "A successful local analysis audit reports missing work honestly and may clear human external review. "
            "It does not clear external publication, execute network studies, mutate the registry, or promote "
            "scientific-memory state."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-analysis-ready-for-external-review", action="store_true")
    parser.add_argument("--require-external-ready", action="store_true")
    args = parser.parse_args()
    result = build_readiness(artifacts_dir=args.artifacts_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    analysis_blocked = bool(
        args.require_analysis_ready_for_external_review and not result["analysis_ready_for_external_review"]
    )
    publication_blocked = bool(args.require_external_ready and not result["external_ready"])
    return int(analysis_blocked or publication_blocked)


if __name__ == "__main__":
    raise SystemExit(main())
