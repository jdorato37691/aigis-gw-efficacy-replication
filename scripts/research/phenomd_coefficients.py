#!/usr/bin/env python3
r"""Sourced PhenomD coefficient extraction (Study 6 foundation).

Parses the 19x11 phenomenological-coefficient table of Khan et al. 2016
(arXiv:1508.07253, "PhenomPaper2.tex", table \\label{tab:coefftable}) directly
from the fetched arXiv LaTeX source, never from memory. The program invariant
this enforces: fitted coefficient tables enter AIGIS only by verifiable
transcription from a sha256-stamped source artifact.

Source provenance (fetched 2026-07-12, receipts in the artifact):
  ~/.aigis/research/gw_replication/sources/1508.07253.tar.gz
  -> 1508.07253/PhenomPaper2.tex

Model equations transcribed from the same source (line anchors in artifact):
  chi_PN  = chi_eff - (38 eta / 113)(chi1 + chi2)                 [line ~289]
  Lambda^i(eta, chi_PN) mapping polynomial                        [eqn:mapping]
  phi_Ins = phi_TF2 + (1/eta)(s0 + s1 f + 3/4 s2 f^{4/3}
            + 3/5 s3 f^{5/3} + 1/2 s4 f^2)                        [equ:phiins]
  phi_Int = (1/eta)(b0 + b1 f + b2 ln f - b3/3 f^{-3})            [eqn:IntPhase]
  phi_MR  = (1/eta){a0 + a1 f - a2 f^{-1} + 4/3 a3 f^{3/4}
            + a4 arctan((f - a5 f_RD)/f_damp)}                    [eqn:MRDPhase]
  regions: inspiral Mf < 0.018; intermediate [0.018, 0.5 f_RD]; MR above.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

_SOURCES = Path.home() / ".aigis" / "research" / "gw_replication" / "sources"
_TEX = _SOURCES / "1508.07253" / "PhenomPaper2.tex"
_TARBALL = _SOURCES / "1508.07253.tar.gz"
_ARTIFACT = _SOURCES / "phenomd_coefficients.json"

_EXPECTED_LABELS = [
    "rho_1",
    "rho_2",
    "rho_3",
    "v_2",
    "gamma_1",
    "gamma_2",
    "gamma_3",
    "sigma_1",
    "sigma_2",
    "sigma_3",
    "sigma_4",
    "beta_1",
    "beta_2",
    "beta_3",
    "alpha_1",
    "alpha_2",
    "alpha_3",
    "alpha_4",
    "alpha_5",
]
_LAMBDA_COLUMNS = [
    "l00",
    "l10",
    "l01",
    "l11",
    "l21",
    "l02",
    "l12",
    "l22",
    "l03",
    "l13",
    "l23",
]

# Rule-26 parse tripwire: cells asserted against the RAW source strings
# (verbatim from the table text), spanning plain floats, trailing-dot
# integers, and both x10^{n} exponent spellings. A regex misparse anywhere
# in the pipeline fails here before any physics runs.
_SPOT_CHECKS = [
    ("rho_1", "l00", "3931.9"),
    ("rho_1", "l21", r"-1.21626$\times 10^6$"),
    ("rho_2", "l11", r"-3.47618$\times 10^6$"),
    ("v_2", "l00", "0.814984"),
    ("sigma_1", "l22", "-108609."),
    ("beta_3", "l23", r"7.97402$\times 10^{-5}$"),
    ("alpha_4", "l13", "0.157503"),
    ("alpha_5", "l23", "-2.06089"),
]

_NUM_RE = re.compile(
    r"^\s*(-?\d+\.?\d*)\s*(?:\$?\\times\s*10\^\{?(-?\d+)\}?\$?)?\s*$",
)


def _parse_latex_number(cell: str) -> float:
    text = cell.strip().strip("$").strip()
    match = _NUM_RE.match(text)
    if match is None:
        raise ValueError(f"unparseable table cell: {cell!r}")
    mantissa = float(match.group(1))
    exponent = int(match.group(2)) if match.group(2) else 0
    return mantissa * 10.0**exponent


def _normalize_label(cell: str) -> str:
    text = cell.replace("$", "").replace("\\", "").replace(" ", "").strip()
    return {
        "rho_1": "rho_1",
        "rho_2": "rho_2",
        "rho_3": "rho_3",
        "v_2": "v_2",
        "gamma_1": "gamma_1",
        "gamma_2": "gamma_2",
        "gamma_3": "gamma_3",
        "sigma_1": "sigma_1",
        "sigma_2": "sigma_2",
        "sigma_3": "sigma_3",
        "sigma_4": "sigma_4",
        "beta_1": "beta_1",
        "beta_2": "beta_2",
        "beta_3": "beta_3",
        "alpha_1": "alpha_1",
        "alpha_2": "alpha_2",
        "alpha_3": "alpha_3",
        "alpha_4": "alpha_4",
        "alpha_5": "alpha_5",
    }[text]


def parse_table() -> tuple[dict[str, dict[str, float]], tuple[int, int]]:
    """Parse the coefficient table; returns (coefficients, (line_start, line_end))."""
    lines = _TEX.read_text(encoding="utf-8", errors="replace").splitlines()
    header_idx = next(i for i, line in enumerate(lines) if r"\multicolumn{1}{c}{$\Lambda^i$}" in line)
    coefficients: dict[str, dict[str, float]] = {}
    row_end = header_idx
    for i in range(header_idx + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith(r"\end{tabular}"):
            break
        if "&" not in line:
            continue
        row = line.replace(r"\hline", "").strip().rstrip("\\").strip()
        cells = [c.strip() for c in row.split("&")]
        if len(cells) != 12:
            raise ValueError(f"row at tex line {i + 1} has {len(cells)} cells, expected 12")
        label = _normalize_label(cells[0])
        coefficients[label] = {
            col: _parse_latex_number(cell) for col, cell in zip(_LAMBDA_COLUMNS, cells[1:], strict=True)
        }
        row_end = i
    return coefficients, (header_idx + 1, row_end + 1)


def integrity_check(coefficients: dict[str, dict[str, float]]) -> dict[str, object]:
    """Rule-26 gate on the parser itself: shape, label order, spot-checked cells."""
    labels = list(coefficients)
    shape_ok = labels == _EXPECTED_LABELS and all(
        list(row) == _LAMBDA_COLUMNS and all(v == v and abs(v) < 1e9 for v in row.values())
        for row in coefficients.values()
    )
    spot_results = []
    for label, column, raw in _SPOT_CHECKS:
        expected = _parse_latex_number(raw)
        got = coefficients.get(label, {}).get(column)
        spot_results.append(
            {"cell": f"{label}.{column}", "raw_source": raw, "parsed": got, "passed": got == expected},
        )
    passed = shape_ok and all(s["passed"] for s in spot_results)
    return {
        "passed": passed,
        "shape_19x11": shape_ok,
        "spot_checks": spot_results,
    }


def phenomd_lambda(coefficients: dict[str, dict[str, float]], eta: float, chi_pn: float) -> dict[str, float]:
    """Evaluate the eqn:mapping polynomial for every Lambda^i at (eta, chi_pn)."""
    x = chi_pn - 1.0
    out: dict[str, float] = {}
    for label, c in coefficients.items():
        out[label] = (
            c["l00"]
            + c["l10"] * eta
            + x * (c["l01"] + c["l11"] * eta + c["l21"] * eta**2)
            + x**2 * (c["l02"] + c["l12"] * eta + c["l22"] * eta**2)
            + x**3 * (c["l03"] + c["l13"] * eta + c["l23"] * eta**2)
        )
    return out


def load_artifact() -> dict[str, object]:
    """Load the committed provenance artifact, re-verifying its payload digest."""
    artifact = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    payload = json.dumps(artifact["coefficients"], sort_keys=True).encode()
    if hashlib.sha256(payload).hexdigest() != artifact["coefficients_sha256"]:
        raise ValueError("phenomd coefficient artifact digest mismatch")
    return artifact


def main() -> int:
    if not _TEX.is_file():
        raise SystemExit(f"source not fetched: {_TEX}")
    coefficients, (line_start, line_end) = parse_table()
    gate = integrity_check(coefficients)
    if not gate["passed"]:
        print(json.dumps(gate, indent=2))
        raise SystemExit("parse integrity gate FAILED - artifact not written")

    payload = json.dumps(coefficients, sort_keys=True).encode()
    artifact = {
        "artifact_type": "phenomd_sourced_coefficients",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": {
            "arxiv_id": "1508.07253",
            "reference": "Khan, Husa, Hannam et al. 2016, PhysRevD.93.044007 (PhenomD Paper 2)",
            "tarball": str(_TARBALL),
            "tarball_sha256": hashlib.sha256(_TARBALL.read_bytes()).hexdigest(),
            "tex_file": str(_TEX),
            "tex_sha256": hashlib.sha256(_TEX.read_bytes()).hexdigest(),
            "table_label": "tab:coefftable",
            "table_tex_lines": [line_start, line_end],
        },
        "model_equation_anchors": {
            "chi_pn_definition": "chi_PN = chi_eff - (38 eta/113)(chi1+chi2)  [tex ~line 289]",
            "mapping": "eqn:mapping  [tex ~lines 1496-1503]",
            "inspiral_phase": "equ:phiins  [tex ~lines 1398-1406]",
            "intermediate_phase": "eqn:IntPhase  [tex ~lines 1024-1028]",
            "merger_ringdown_phase": "eqn:MRDPhase  [tex ~lines 941-948]",
            "phase_regions": "inspiral Mf<0.018; intermediate [0.018, 0.5 f_RD]; MR above [tex lines 999, 1016]",
        },
        "parse_integrity_gate": gate,
        "coefficients": coefficients,
        "coefficients_sha256": hashlib.sha256(payload).hexdigest(),
        "can_influence_belief": False,
    }
    _ARTIFACT.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"parsed {len(coefficients)} parameters x {len(_LAMBDA_COLUMNS)} lambdas")
    print(json.dumps(gate["spot_checks"], indent=1))
    print("artifact:", _ARTIFACT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
