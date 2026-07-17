#!/usr/bin/env python3
"""TaylorF2 stationary-phase inspiral template, pure numpy.

The standard frequency-domain post-Newtonian inspiral waveform (3.5PN
point-particle phasing, zero spin, no tidal terms) used as the GW170817
matched-filter template per the 2026-07-12 preregistration. Coefficients
follow the standard published series (e.g. Buonanno, Iyer, Ochsner, Pan &
Sathyaprakash 2009, Phys. Rev. D 80, 084043, Eq. 3.18).

Detection-grade only: absolute amplitude is arbitrary (sigma-normalization
cancels it in the matched filter) and tidal phasing is omitted (negligible
SNR contribution below ~600 Hz).

The preregistered coefficient-integrity tripwire lives here too: an
independently written 2PN implementation must agree with the 3.5PN series
(2.5PN+ terms zeroed) to <0.5 rad across [30, 400] Hz.
"""

from __future__ import annotations

import numpy as np

_GAMMA_E = 0.5772156649015329
_MSUN_SECONDS = 4.925491025543576e-06  # G*Msun/c^3


def _pn_variable(freqs: np.ndarray, total_mass_seconds: float) -> np.ndarray:
    return (np.pi * total_mass_seconds * freqs) ** (1.0 / 3.0)


def taylorf2_phase_35pn(
    freqs: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
    chi_eff: float = 0.0,
    zero_beyond_2pn: bool = False,
) -> np.ndarray:
    """3.5PN point-particle phasing Psi(f) without the tc/phic linear terms.

    ``chi_eff`` adds the leading-order aligned spin-orbit contribution at
    1.5PN (single-effective-spin, detection-grade: both component spins set
    to chi_eff). Zero-spin reproduces the original series exactly (Study-2
    preregistered regression).
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    v = _pn_variable(freqs, m_sec)
    v = np.where(v > 0, v, 1e-12)

    a2 = 3715.0 / 756.0 + 55.0 * eta / 9.0
    a3 = -16.0 * np.pi + (113.0 / 3.0 - 76.0 * eta / 3.0) * chi_eff
    a4 = 15293365.0 / 508032.0 + 27145.0 * eta / 504.0 + 3085.0 * eta**2 / 72.0
    a5 = np.pi * (38645.0 / 756.0 - 65.0 * eta / 9.0)
    a6 = (
        11583231236531.0 / 4694215680.0
        - 640.0 * np.pi**2 / 3.0
        - 6848.0 * _GAMMA_E / 21.0
        - 6848.0 / 21.0 * np.log(4.0)
        + eta * (-15737765635.0 / 3048192.0 + 2255.0 * np.pi**2 / 12.0)
        + eta**2 * 76055.0 / 1728.0
        - eta**3 * 127825.0 / 1296.0
    )
    a6_log = -6848.0 / 21.0
    a7 = np.pi * (77096675.0 / 254016.0 + 378515.0 * eta / 1512.0 - 74045.0 * eta**2 / 756.0)

    series = 1.0 + a2 * v**2 + a3 * v**3 + a4 * v**4
    if not zero_beyond_2pn:
        series = series + a5 * (1.0 + 3.0 * np.log(v)) * v**5 + (a6 + a6_log * np.log(v)) * v**6 + a7 * v**7
    return 3.0 / (128.0 * eta * v**5) * series


def taylorf2_phase_2pn_independent(
    freqs: np.ndarray,
    *,
    total_mass_msun: float,
    eta: float,
) -> np.ndarray:
    """Independently written 2PN phasing (the preregistered tripwire twin).

    Deliberately re-derived and re-typed rather than shared with the 3.5PN
    series: a transcription error in either implementation surfaces as a
    phase disagreement.
    """
    m_sec = total_mass_msun * _MSUN_SECONDS
    x = (np.pi * m_sec * freqs) ** (2.0 / 3.0)  # x = v^2
    x = np.where(x > 0, x, 1e-24)
    prefactor = 3.0 / (128.0 * eta) * x ** (-5.0 / 2.0)
    newtonian = 1.0
    one_pn = (3715.0 / 756.0 + (55.0 / 9.0) * eta) * x
    one_five_pn = -16.0 * np.pi * x ** (3.0 / 2.0)
    two_pn = (15293365.0 / 508032.0 + (27145.0 / 504.0) * eta + (3085.0 / 72.0) * eta * eta) * x * x
    return prefactor * (newtonian + one_pn + one_five_pn + two_pn)


def coefficient_integrity_check(
    *,
    total_mass_msun: float,
    eta: float,
    f_low: float = 30.0,
    f_high: float = 400.0,
    max_rad: float = 0.5,
) -> dict[str, float | bool]:
    """The preregistered tripwire: 3.5PN(<=2PN terms) vs the independent 2PN."""
    freqs = np.linspace(f_low, f_high, 2048)
    a = taylorf2_phase_35pn(freqs, total_mass_msun=total_mass_msun, eta=eta, zero_beyond_2pn=True)
    b = taylorf2_phase_2pn_independent(freqs, total_mass_msun=total_mass_msun, eta=eta)
    worst = float(np.max(np.abs(a - b)))
    return {"worst_phase_disagreement_rad": worst, "passed": bool(worst < max_rad)}


def taylorf2_time_domain(
    *,
    n_samples: int,
    sample_rate: float,
    chirp_mass_det_msun: float,
    mass1_msun: float,
    mass2_msun: float,
    f_low: float,
    f_cut: float | None = None,
    merger_position: float = 0.75,
    chi_eff: float = 0.0,
) -> np.ndarray:
    """Complex time-domain template h = h+ + i*hx on the analysis grid.

    Built in the frequency domain (amplitude ~ f^{-7/6}, 3.5PN phase), with
    the coalescence placed at ``merger_position`` * segment length via the tc
    phase term, then inverse-FFTed. Absolute amplitude is arbitrary.
    """
    total = mass1_msun + mass2_msun
    eta = mass1_msun * mass2_msun / total**2
    # detector-frame total mass consistent with the detector-frame chirp mass
    total_det = chirp_mass_det_msun / eta**0.6
    m_sec = total_det * _MSUN_SECONDS
    if f_cut is None:
        f_cut = 1.0 / (6.0**1.5 * np.pi * m_sec)  # Schwarzschild ISCO

    freqs = np.fft.rfftfreq(n_samples, d=1.0 / sample_rate)
    in_band = (freqs >= f_low) & (freqs <= f_cut)

    amplitude = np.zeros_like(freqs)
    amplitude[in_band] = freqs[in_band] ** (-7.0 / 6.0)

    psi = np.zeros_like(freqs)
    psi[in_band] = taylorf2_phase_35pn(freqs[in_band], total_mass_msun=total_det, eta=eta, chi_eff=chi_eff)

    # Sign convention validated against the analytic chirp-time relation
    # tau(f) = (5/256) Mc^{-5/3} (pi f)^{-8/3}: for Mc=1.1977 the sweep must
    # pass ~44 Hz at merger-20 s and ~138 Hz at merger-1 s. Only the
    # (-tc, -psi) convention under numpy's +i inverse-FFT kernel reproduces
    # that sweep; the conjugate convention chirps at the wrong rate.
    t_c = merger_position * n_samples / sample_rate
    phase = -2.0 * np.pi * freqs * t_c - psi - np.pi / 4.0

    h_plus_fd = amplitude * np.exp(1j * phase)
    h_cross_fd = h_plus_fd * np.exp(1j * np.pi / 2.0)

    h_plus = np.fft.irfft(h_plus_fd, n=n_samples)
    h_cross = np.fft.irfft(h_cross_fd, n=n_samples)
    template = h_plus + 1j * h_cross
    # normalize to a sane numeric scale (arbitrary; sigma cancels it)
    peak = float(np.max(np.abs(template)))
    return template / peak if peak > 0 else template
