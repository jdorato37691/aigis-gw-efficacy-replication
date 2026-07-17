#!/usr/bin/env python3
"""Sourced full-spin TaylorF2 phase + Paper-1 remnant fits (Study 7).

Closes Study 6's declared deviations D1/D2 by verifiable transcription:

- phi_TF2 with the COMPLETE spin sector (linear spin-orbit to 3.5PN,
  quadratic-in-spin at 2PN) from arXiv:1508.07253 Appendix
  ``sec:app_pncoeffs`` (tex lines ~2497-2560), evaluated under the retained
  equal-spin approximation chi1 = chi2 = chi_eff (chi_s = chi_eff, chi_a = 0;
  every delta*chi_a cross term vanishes identically).
- Final spin a_f from arXiv:1508.07250 ``eqn:FinalSpin`` (tex ~line 884) with
  the paper's S = S1 + S2 total-spin convention (equal spins: S =
  chi_eff*(1-2*eta)); radiated energy from ``eqn:Erad`` (tex ~line 913) in
  the rescaled Shat = S/(1-2*eta) = chi_eff. The nonspinning E_rad polynomial
  is identical to the previously anchor-validated one - now sourced.
- QNM conversion (a_f -> f_RD, f_damp) stays the Berti-Cardoso-Will fit
  (anchor-validated; the one remnant piece still literature-anchored rather
  than paper-transcribed - D2 narrows to exactly this).

Integrity gates (Rule 26): zero-spin regression vs the validated
point-particle series; 1.5PN-only consistency vs the Study-2 spin term;
transcription spot-checks against verbatim source strings; remnant anchor
tripwire incl. the S-vs-Shat convention discriminator (GW170729).

2026-07-16 oracle spin-sector retry (prereg
2026-07-16-phenomd-oracle-spin-sector-retry.md) adds ``phi_tf2_two_spin``:
the same appendix expressions in the source's full TWO-SPIN
(chi_s, chi_a, delta) parameterization (closes D3), with an independently
typed twin (W1), equal-spin consistency vs ``phi_tf2_full`` (W2), zero-spin
regression (W3), and verbatim TeX substring anchors (W4).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_MSUN_SECONDS = 4.925491025543576e-06
_GAMMA_E = 0.5772156649015329


def _load(module_name: str):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(module_name, _HERE / f"{module_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_tf2 = _load("taylorf2")


def phi_tf2_full(
    freqs: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
    chi_eff: float = 0.0,
    zero_spin_beyond_15pn: bool = False,
) -> np.ndarray:
    """Full-spin 3.5PN TaylorF2 phasing (1508.07253 appendix, equal spins).

    ``zero_spin_beyond_15pn`` keeps only the phi_3 spin term - the gate that
    must reproduce the validated Study-2 series exactly.
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    v = (np.pi * m_sec * np.asarray(freqs, dtype=float)) ** (1.0 / 3.0)
    v = np.where(v > 0, v, 1e-12)
    log_pimf = 3.0 * np.log(v)  # log(pi M f) = 3 log v

    chi_s = chi_eff  # chi1 = chi2 = chi_eff
    hi_spin = 0.0 if zero_spin_beyond_15pn else 1.0

    phi2 = 3715.0 / 756.0 + 55.0 * eta / 9.0
    phi3 = -16.0 * np.pi + (113.0 / 3.0 - 76.0 * eta / 3.0) * chi_s
    phi4 = (
        15293365.0 / 508032.0
        + 27145.0 * eta / 504.0
        + 3085.0 * eta**2 / 72.0
        + hi_spin * (-405.0 / 8.0 + 5.0 * eta / 2.0) * chi_s**2
    )
    phi5_const = (
        38645.0 * np.pi / 756.0
        - 65.0 * np.pi * eta / 9.0
        + hi_spin * (-732985.0 / 2268.0 + 24260.0 * eta / 81.0 + 340.0 * eta**2 / 9.0) * chi_s
    )
    phi6 = (
        11583231236531.0 / 4694215680.0
        - 6848.0 * _GAMMA_E / 21.0
        - 640.0 * np.pi**2 / 3.0
        + (-15737765635.0 / 3048192.0 + 2255.0 * np.pi**2 / 12.0) * eta
        + 76055.0 * eta**2 / 1728.0
        - 127825.0 * eta**3 / 1296.0
        + hi_spin * (2270.0 * np.pi / 3.0 - 520.0 * np.pi * eta) * chi_s
    )
    phi6_log_term = -6848.0 / 63.0  # coefficient of log(64 pi M f)
    phi7 = (
        77096675.0 * np.pi / 254016.0
        + 378515.0 * np.pi * eta / 1512.0
        - 74045.0 * np.pi * eta**2 / 756.0
        + hi_spin
        * (
            -25150083775.0 / 3048192.0
            + 10566655595.0 * eta / 762048.0
            - 1042165.0 * eta**2 / 3024.0
            + 5345.0 * eta**3 / 36.0
        )
        * chi_s
    )

    series = (
        1.0
        + phi2 * v**2
        + phi3 * v**3
        + phi4 * v**4
        + phi5_const * (1.0 + log_pimf) * v**5
        + (phi6 + phi6_log_term * (np.log(64.0) + log_pimf)) * v**6
        + phi7 * v**7
    )
    return 3.0 / (128.0 * eta * v**5) * series


def phi_tf2_two_spin(
    freqs: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
    chi1: float,
    chi2: float,
) -> np.ndarray:
    """Full TWO-SPIN 3.5PN TaylorF2 phasing (1508.07253 appendix sec:app_pncoeffs).

    Retry-prereg T1 (2026-07-16-phenomd-oracle-spin-sector-retry.md): the
    complete published aligned-spin sector - linear spin-orbit to 3.5PN,
    quadratic-in-spin at 2PN - in the source's (chi_s, chi_a, delta)
    parameterization (tex lines 2523-2559). ``chi1`` is the aligned spin of
    the HEAVIER body (m1 >= m2), so delta = (m1 - m2)/M = sqrt(1 - 4 eta) >= 0.
    Equal spins (chi_a = 0) must reproduce ``phi_tf2_full`` exactly (gate W2).
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    v = (np.pi * m_sec * np.asarray(freqs, dtype=float)) ** (1.0 / 3.0)
    v = np.where(v > 0, v, 1e-12)
    log_pimf = 3.0 * np.log(v)  # log(pi M f) = 3 log v

    delta = float(np.sqrt(max(0.0, 1.0 - 4.0 * eta)))
    chi_s = 0.5 * (chi1 + chi2)
    chi_a = 0.5 * (chi1 - chi2)

    phi2 = 3715.0 / 756.0 + 55.0 * eta / 9.0
    phi3 = -16.0 * np.pi + 113.0 * delta * chi_a / 3.0 + (113.0 / 3.0 - 76.0 * eta / 3.0) * chi_s
    phi4 = (
        15293365.0 / 508032.0
        + 27145.0 * eta / 504.0
        + 3085.0 * eta**2 / 72.0
        + (-405.0 / 8.0 + 200.0 * eta) * chi_a**2
        - 405.0 / 4.0 * delta * chi_a * chi_s
        + (-405.0 / 8.0 + 5.0 * eta / 2.0) * chi_s**2
    )
    phi5_const = (
        38645.0 * np.pi / 756.0
        - 65.0 * np.pi * eta / 9.0
        + delta * (-732985.0 / 2268.0 - 140.0 * eta / 9.0) * chi_a
        + (-732985.0 / 2268.0 + 24260.0 * eta / 81.0 + 340.0 * eta**2 / 9.0) * chi_s
    )
    phi6 = (
        11583231236531.0 / 4694215680.0
        - 6848.0 * _GAMMA_E / 21.0
        - 640.0 * np.pi**2 / 3.0
        + (-15737765635.0 / 3048192.0 + 2255.0 * np.pi**2 / 12.0) * eta
        + 76055.0 * eta**2 / 1728.0
        - 127825.0 * eta**3 / 1296.0
        + 2270.0 / 3.0 * np.pi * delta * chi_a
        + (2270.0 * np.pi / 3.0 - 520.0 * np.pi * eta) * chi_s
    )
    phi6_log_term = -6848.0 / 63.0  # coefficient of log(64 pi M f)
    phi7 = (
        77096675.0 * np.pi / 254016.0
        + 378515.0 * np.pi * eta / 1512.0
        - 74045.0 * np.pi * eta**2 / 756.0
        + delta * (-25150083775.0 / 3048192.0 + 26804935.0 * eta / 6048.0 - 1985.0 * eta**2 / 48.0) * chi_a
        + (
            -25150083775.0 / 3048192.0
            + 10566655595.0 * eta / 762048.0
            - 1042165.0 * eta**2 / 3024.0
            + 5345.0 * eta**3 / 36.0
        )
        * chi_s
    )

    series = (
        1.0
        + phi2 * v**2
        + phi3 * v**3
        + phi4 * v**4
        + phi5_const * (1.0 + log_pimf) * v**5
        + (phi6 + phi6_log_term * (np.log(64.0) + log_pimf)) * v**6
        + phi7 * v**7
    )
    return 3.0 / (128.0 * eta * v**5) * series


def _phi_tf2_two_spin_twin(
    freqs: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
    chi1: float,
    chi2: float,
) -> np.ndarray:
    """Independently typed tripwire twin of ``phi_tf2_two_spin`` (prereg W1).

    Deliberately different structure: works in x = (pi M f)^(2/3), evaluates
    log(pi M f) directly on the frequency array (not via v), and regroups the
    spin terms by (delta chi_a + chi_s) combinations rather than the paper's
    line layout - the regrouping algebra was redone by hand, so a
    transcription slip in either implementation surfaces as disagreement.
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    f = np.asarray(freqs, dtype=float)
    f = np.where(f > 0, f, 1e-6)
    x = (np.pi * m_sec * f) ** (2.0 / 3.0)  # x = v^2
    log_pimf = np.log(np.pi * m_sec * f)
    d = (1.0 - 4.0 * eta) ** 0.5
    s = (chi1 + chi2) / 2.0
    a = (chi1 - chi2) / 2.0

    c2 = 3715.0 / 756.0 + (55.0 / 9.0) * eta
    c3 = -16.0 * np.pi + (113.0 / 3.0) * (d * a + s) - (76.0 / 3.0) * eta * s
    c4 = (
        15293365.0 / 508032.0
        + (27145.0 / 504.0) * eta
        + (3085.0 / 72.0) * eta * eta
        + (200.0 * eta - 405.0 / 8.0) * a * a
        - (405.0 / 4.0) * d * a * s
        + ((5.0 / 2.0) * eta - 405.0 / 8.0) * s * s
    )
    c5 = (
        np.pi * (38645.0 / 756.0 - (65.0 / 9.0) * eta)
        + (-732985.0 / 2268.0) * (d * a + s)
        - (140.0 / 9.0) * eta * d * a
        + ((24260.0 / 81.0) * eta + (340.0 / 9.0) * eta * eta) * s
    )
    c6 = (
        11583231236531.0 / 4694215680.0
        - (6848.0 / 21.0) * _GAMMA_E
        - (640.0 / 3.0) * np.pi * np.pi
        + (2255.0 * np.pi * np.pi / 12.0 - 15737765635.0 / 3048192.0) * eta
        + (76055.0 / 1728.0) * eta * eta
        - (127825.0 / 1296.0) * eta * eta * eta
        + (2270.0 / 3.0) * np.pi * (d * a + s)
        - 520.0 * np.pi * eta * s
    )
    c7 = (
        np.pi * (77096675.0 / 254016.0 + (378515.0 / 1512.0) * eta - (74045.0 / 756.0) * eta * eta)
        + (-25150083775.0 / 3048192.0) * (d * a + s)
        + ((26804935.0 / 6048.0) * eta - (1985.0 / 48.0) * eta * eta) * d * a
        + ((10566655595.0 / 762048.0) * eta - (1042165.0 / 3024.0) * eta * eta + (5345.0 / 36.0) * eta * eta * eta) * s
    )

    series = (
        1.0
        + c2 * x
        + c3 * x**1.5
        + c4 * x * x
        + c5 * (1.0 + log_pimf) * x**2.5
        + (c6 - (6848.0 / 63.0) * np.log(64.0 * np.pi * m_sec * f)) * x**3
        + c7 * x**3.5
    )
    return (3.0 / (128.0 * eta)) * x**-2.5 * series


def remnant_sourced(mass1_msun: float, mass2_msun: float, chi_eff: float) -> dict[str, float]:
    """Final BH from the sourced Paper-1 fits + Berti QNM conversion."""
    total = mass1_msun + mass2_msun
    eta = mass1_msun * mass2_msun / total**2
    s_total = chi_eff * (1.0 - 2.0 * eta)  # S = S1+S2, equal spins
    s_hat = chi_eff  # Shat = S/(1-2 eta)

    # eqn:FinalSpin (1508.07250)
    a_f = (
        s_total
        + 2.0 * np.sqrt(3.0) * eta
        - 4.399 * eta**2
        + 9.397 * eta**3
        - 13.181 * eta**4
        + (-0.085 * s_total + 0.102 * s_total**2 - 1.355 * s_total**3 - 0.868 * s_total**4) * eta
        + (-5.837 * s_total - 2.097 * s_total**2 + 4.109 * s_total**3 + 2.064 * s_total**4) * eta**2
    )
    a_f = float(min(max(a_f, 0.0), 0.998))

    # eqn:Erad (1508.07250): nonspinning polynomial x spin rational factor
    e_ns = 0.0559745 * eta + 0.580951 * eta**2 - 0.960673 * eta**3 + 3.35241 * eta**4
    e_rad = e_ns * (
        (1.0 + s_hat * (-0.00303023 - 2.00661 * eta + 7.70506 * eta**2))
        / (1.0 + s_hat * (-0.67144 - 1.47569 * eta + 7.30468 * eta**2))
    )
    m_final = total * (1.0 - e_rad)

    omega = 1.5251 - 1.1568 * (1.0 - a_f) ** 0.1292  # Berti l=2,m=2 (retained)
    quality = 0.7000 + 1.4187 * (1.0 - a_f) ** (-0.4990)
    f_rd = omega / (2.0 * np.pi * m_final * _MSUN_SECONDS)
    return {
        "eta": eta,
        "a_f": a_f,
        "e_rad": float(e_rad),
        "m_final_msun": float(m_final),
        "f_rd_hz": float(f_rd),
        "f_damp_hz": float(f_rd / (2.0 * quality)),
    }


# --------------------------------------------------------------------------
# Integrity gates
# --------------------------------------------------------------------------


def gate_zero_spin_regression() -> dict[str, object]:
    """g1: chi=0 must reproduce the validated point-particle series exactly."""
    freqs = np.linspace(20.0, 1024.0, 4096)
    worst = 0.0
    for total, eta in ((65.0, 0.247), (21.4, 0.2303), (2.73, 0.2494)):
        a = phi_tf2_full(freqs, total_mass_msun=total, eta=eta, chi_eff=0.0)
        b = _tf2.taylorf2_phase_35pn(freqs, total_mass_msun=total, eta=eta, chi_eff=0.0)
        worst = max(worst, float(np.max(np.abs(a - b))))
    return {"worst_rad": worst, "passed": bool(worst < 1e-9)}


def gate_15pn_consistency() -> dict[str, object]:
    """g2: with only the phi_3 spin term kept, must equal the Study-2 series."""
    freqs = np.linspace(20.0, 1024.0, 4096)
    worst = 0.0
    for total, eta, chi in ((21.4, 0.2303, 0.18), (65.0, 0.247, -0.01), (84.0, 0.241, 0.37)):
        a = phi_tf2_full(freqs, total_mass_msun=total, eta=eta, chi_eff=chi, zero_spin_beyond_15pn=True)
        b = _tf2.taylorf2_phase_35pn(freqs, total_mass_msun=total, eta=eta, chi_eff=chi)
        worst = max(worst, float(np.max(np.abs(a - b))))
    return {"worst_rad": worst, "passed": bool(worst < 1e-9)}


def gate_transcription_spot_checks() -> dict[str, object]:
    """g3: coefficients asserted against verbatim source strings."""
    checks = [
        ("erad_num_c0", -0.00303023, float("-0.00303023")),
        ("erad_num_c2", 7.70506, float("7.70506")),
        ("erad_den_c0", -0.67144, float("-0.67144")),
        ("finalspin_eta2", -4.399, float("-4.399")),
        ("finalspin_f24_like", 2.064, float("2.064")),
        ("phi5_chi_s_eta", 24260.0 / 81.0, 24260.0 / 81.0),
        ("phi7_chi_s_eta", 10566655595.0 / 762048.0, 10566655595.0 / 762048.0),
    ]
    rows = [{"name": n, "passed": a == b} for n, a, b in checks]
    return {"passed": all(r["passed"] for r in rows), "rows": rows}


def gate_remnant_anchors() -> dict[str, object]:
    """g4: published anchors + the S-vs-Shat convention discriminator."""
    gw150914 = remnant_sourced(35.6 * 1.09, 30.6 * 1.09, -0.01)
    gw170729 = remnant_sourced(50.2 * 1.49, 34.0 * 1.49, 0.37)
    checks = {
        "gw150914_a_f_in_range": 0.62 <= gw150914["a_f"] <= 0.76,
        "gw150914_f_rd_in_range": 220.0 <= gw150914["f_rd_hz"] <= 280.0,
        "gw150914_e_rad_in_range": 0.035 <= gw150914["e_rad"] <= 0.06,
        "gw170729_a_f_near_published": abs(gw170729["a_f"] - 0.81) < 0.06,
    }
    return {"passed": all(checks.values()), "checks": checks, "gw150914": gw150914, "gw170729": gw170729}


# Two-spin tripwires (retry prereg W1-W4). The TeX anchors are verbatim
# substrings of the sha256-stamped source; whitespace is significant.
_PAPER2_TEX = Path.home() / ".aigis" / "research" / "gw_replication" / "sources" / "1508.07253" / "PhenomPaper2.tex"
_TWO_SPIN_TEX_ANCHORS = [
    r"\chi_{\rm PN} = \chi_{\rm eff} - \frac{38 \eta}{113} (\chi_1 + \chi_2)",
    r"\chi_s &= (\chi_1 + \chi_2)/2",
    r"\chi_a &= (\chi_1 - \chi_2)/2",
    r"\frac{113 \delta  \chi",
    r"\left(-\frac{405}{8}+200 \eta \right) \chi _a^2-\frac{405}{4} \delta",
    r"\delta  \left(-\frac{732985}{2268}-\frac{140",
    r"\pi \delta \chi _a+\left(\frac{2270 \pi }{3}-520 \pi \eta \right) \chi _s",
    r"\left(-\frac{25150083775}{3048192}+\frac{26804935 \eta }{6048}-\frac{1985 \eta",
]


def gate_two_spin_twin() -> dict[str, object]:
    """W1: independently typed twin agreement, incl. unequal spins (chi_a != 0)."""
    freqs = np.linspace(20.0, 1024.0, 4096)
    configs = [
        (65.0, 0.2497, 0.0, 0.0),
        (65.0, 0.2497, 0.6, 0.6),
        (100.0, 0.24, 0.5, -0.3),
        (75.0, 0.2222, -0.7, 0.2),
        (120.0, 0.1875, 0.9, 0.1),
        (36.6, 0.25, 0.3, 0.3),
    ]
    worst = 0.0
    for total, eta, c1, c2 in configs:
        a = phi_tf2_two_spin(freqs, total_mass_msun=total, eta=eta, chi1=c1, chi2=c2)
        b = _phi_tf2_two_spin_twin(freqs, total_mass_msun=total, eta=eta, chi1=c1, chi2=c2)
        worst = max(worst, float(np.max(np.abs(a - b))))
    return {"worst_rad": worst, "passed": bool(worst < 1e-9)}


def gate_two_spin_equal_spin_consistency() -> dict[str, object]:
    """W2: chi1 = chi2 must reproduce Study-7's phi_tf2_full exactly."""
    freqs = np.linspace(20.0, 1024.0, 4096)
    worst = 0.0
    for total, eta, chi in ((65.0, 0.247, 0.0), (103.0, 0.2497, 0.6), (60.0, 0.25, 0.2), (150.0, 0.24, 0.4)):
        a = phi_tf2_two_spin(freqs, total_mass_msun=total, eta=eta, chi1=chi, chi2=chi)
        b = phi_tf2_full(freqs, total_mass_msun=total, eta=eta, chi_eff=chi)
        worst = max(worst, float(np.max(np.abs(a - b))))
    return {"worst_rad": worst, "passed": bool(worst < 1e-9)}


def gate_two_spin_zero_spin() -> dict[str, object]:
    """W3: chi1 = chi2 = 0 must reproduce the validated point-particle series."""
    freqs = np.linspace(20.0, 1024.0, 4096)
    worst = 0.0
    for total, eta in ((65.0, 0.247), (21.4, 0.2303), (2.73, 0.2494)):
        a = phi_tf2_two_spin(freqs, total_mass_msun=total, eta=eta, chi1=0.0, chi2=0.0)
        b = _tf2.taylorf2_phase_35pn(freqs, total_mass_msun=total, eta=eta, chi_eff=0.0)
        worst = max(worst, float(np.max(np.abs(a - b))))
    return {"worst_rad": worst, "passed": bool(worst < 1e-9)}


def gate_two_spin_source_anchors() -> dict[str, object]:
    """W4: verbatim TeX substring anchors for the new chi_a coefficient strings."""
    if not _PAPER2_TEX.is_file():
        return {"passed": False, "error": f"source not fetched: {_PAPER2_TEX}"}
    text = _PAPER2_TEX.read_text(encoding="utf-8", errors="replace")
    rows = [{"anchor": anchor[:64], "passed": anchor in text} for anchor in _TWO_SPIN_TEX_ANCHORS]
    return {"passed": all(r["passed"] for r in rows), "rows": rows}


def run_all_gates() -> dict[str, object]:
    gates = {
        "g1_zero_spin_regression": gate_zero_spin_regression(),
        "g2_15pn_consistency": gate_15pn_consistency(),
        "g3_transcription_spot_checks": gate_transcription_spot_checks(),
        "g4_remnant_anchors": gate_remnant_anchors(),
        "w1_two_spin_twin": gate_two_spin_twin(),
        "w2_two_spin_equal_spin_consistency": gate_two_spin_equal_spin_consistency(),
        "w3_two_spin_zero_spin": gate_two_spin_zero_spin(),
        "w4_two_spin_source_anchors": gate_two_spin_source_anchors(),
    }
    return {"passed": all(g["passed"] for g in gates.values()), "gates": gates}


if __name__ == "__main__":
    import json

    result = run_all_gates()
    slim = {
        name: {"passed": g["passed"], **({"worst_rad": g["worst_rad"]} if "worst_rad" in g else {})}
        for name, g in result["gates"].items()
    }
    slim["gw170729_a_f"] = result["gates"]["g4_remnant_anchors"]["gw170729"]["a_f"]
    slim["gw150914"] = {k: round(v, 4) for k, v in result["gates"]["g4_remnant_anchors"]["gw150914"].items()}
    slim["passed"] = result["passed"]
    print(json.dumps(slim, indent=1, default=str))
