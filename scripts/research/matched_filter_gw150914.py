#!/usr/bin/env python3
"""GW150914 matched-filter recovery benchmark (preregistered).

Implements docs/research/preregistrations/2026-07-12-gw150914-matched-filter.md
EXACTLY. The preregistration was committed before any on-source run; this
script refuses to deviate from it silently - every locked parameter is a module
constant mirroring the prereg text.

Method: the canonical GWOSC/LOSC reproduction recipe - the NR-calibrated
template from GWOSC's own GW150914 event release, an FFT matched filter with a
Welch PSD, band-limited to 20-2048 Hz. No pycbc/lalsuite dependency: h5py +
gwpy + scipy only (nothing is installed into the canonical venv).

Modes:
    --validate   injection test into OFF-SOURCE noise only (engineering
                 control; does not touch the on-source segment)
    --control    off-source known-bad control (legacy two-detector statistic)
    --confirm    the single confirmatory on-source run
    --replicate  within-project alternative-configuration run (median PSD,
                 16 s segments) per prereg

Every mode writes a sha256-stamped receipt to
~/.aigis/research/gw_replication/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import urllib.request
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts.research.gw_evidence_controls import independent_peak_statistic
except ModuleNotFoundError:  # direct script execution
    from gw_evidence_controls import independent_peak_statistic

warnings.filterwarnings("ignore")

# --- locked by the preregistration (2026-07-12) -----------------------------
_EVENT = "GW150914"
_CITATION = "Abbott et al. 2016, Phys. Rev. Lett. 116, 061102"
_PUBLISHED_NETWORK_SNR = 23.7
_TOLERANCE = 0.15  # +/-15% -> [20.145, 27.255]
_CATALOG_GPS = 1126259462.4
_ON_SOURCE = (1126259446.0, 1126259478.0)  # 32 s
_OFF_SOURCE = (1126259190.0, 1126259222.0)  # 256 s earlier, no catalog event
_SAMPLE_RATE = 4096.0
_BAND = (20.0, 2048.0)
_PEAK_WINDOW_S = 0.1  # on-source peak search: +/-0.1 s around catalog GPS
_OFF_SOURCE_MAX_ALLOWED = 8.0  # known-bad gate: noise must stay below this
_WELCH_FFT_S = 4.0  # confirmatory PSD: 4 s Welch mean
_REPLICATION_FFT_S = 16.0  # replication PSD: 16 s segments, median average
_TEMPLATE_URL = "https://gwosc.org/s/events/GW150914/GW150914_4_template.hdf5"
# -----------------------------------------------------------------------------

_RECEIPT_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
_TEMPLATE_CACHE = _RECEIPT_DIR / "GW150914_4_template.hdf5"


def _environment() -> dict[str, str]:
    versions: dict[str, str] = {"python": platform.python_version(), "platform": platform.platform()}
    for package in ("gwpy", "gwosc", "numpy", "scipy", "h5py"):
        try:
            import importlib.metadata as md  # noqa: PLC0415

            versions[package] = md.version(package)
        except Exception:  # noqa: BLE001
            versions[package] = "absent"
    return versions


def _fetch_template() -> tuple[np.ndarray, str]:
    """Download (once) and load the GWOSC NR-calibrated template; return (h, sha256)."""
    import h5py  # noqa: PLC0415

    if not _TEMPLATE_CACHE.is_file():
        _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(_TEMPLATE_URL, timeout=60) as response:  # noqa: S310
            _TEMPLATE_CACHE.write_bytes(response.read())
    raw = _TEMPLATE_CACHE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with h5py.File(_TEMPLATE_CACHE, "r") as handle:
        template = handle["template"][...]
    template = np.asarray(template)
    if template.ndim == 2 and template.shape[0] == 2:  # noqa: PLR2004
        h_complex = template[0] + 1j * template[1]
    else:
        h_complex = template.astype(complex)
    return h_complex, digest


def _fetch_strain(detector: str, segment: tuple[float, float]) -> np.ndarray:
    from gwpy.timeseries import TimeSeries  # noqa: PLC0415

    series = TimeSeries.fetch_open_data(detector, *segment, cache=True, verbose=False)
    if float(series.sample_rate.value) != _SAMPLE_RATE:
        series = series.resample(_SAMPLE_RATE)
    return np.asarray(series.value, dtype=float)


def _psd(data: np.ndarray, *, fft_seconds: float, average: str) -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import welch  # noqa: PLC0415

    nperseg = int(fft_seconds * _SAMPLE_RATE)
    freqs, psd = welch(
        data,
        fs=_SAMPLE_RATE,
        nperseg=nperseg,
        noverlap=nperseg // 2,
        average=average,
    )
    return freqs, psd


def matched_filter_snr(
    data: np.ndarray,
    template: np.ndarray,
    *,
    fft_seconds: float,
    psd_average: str,
    psd_override: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, float]:
    """Return (|snr(t)| series, sigma) - the LOSC-tutorial normalization, exactly.

    Continuous-FT convention: FFTs are scaled by dt so amplitudes match the
    analytic transform; the one-sided Welch PSD (strain^2/Hz) is interpolated
    onto |f| of the full two-sided grid; snr(t) = |2 fs IFFT(d~ h~* / S_n)| /
    sigma with sigma^2 = |sum(h~ h~* / S_n)| df. Frequencies outside the
    preregistered 20-2048 Hz band get zero weight in both numerator and sigma.
    """
    from scipy.signal.windows import tukey  # noqa: PLC0415

    n = len(data)
    if len(template) < n:
        padded = np.zeros(n, dtype=complex)
        padded[: len(template)] = template
        template = padded
    else:
        template = template[:n]

    dt = 1.0 / _SAMPLE_RATE
    window = tukey(n, alpha=1.0 / 8.0)
    data_fft = np.fft.fft(data * window) * dt
    template_fft = np.fft.fft(template * window) * dt

    freqs = np.fft.fftfreq(n, d=dt)
    df = _SAMPLE_RATE / n

    if psd_override is not None:
        psd_freqs, psd = psd_override
    else:
        psd_freqs, psd = _psd(data, fft_seconds=fft_seconds, average=psd_average)
    power_vec = np.interp(np.abs(freqs), psd_freqs, psd)
    power_vec[power_vec <= 0] = np.inf
    out_of_band = (np.abs(freqs) < _BAND[0]) | (np.abs(freqs) > _BAND[1])
    power_vec[out_of_band] = np.inf  # zero weight outside the preregistered band

    optimal = data_fft * np.conj(template_fft) / power_vec
    optimal_time = 2.0 * np.fft.ifft(optimal) * _SAMPLE_RATE
    sigma_sq = float(np.abs(np.sum(template_fft * np.conj(template_fft) / power_vec))) * df
    sigma = float(np.sqrt(sigma_sq)) if sigma_sq > 0 else float("inf")
    return np.abs(optimal_time) / sigma, sigma


def _detector_snr(
    detector: str,
    segment: tuple[float, float],
    template: np.ndarray,
    *,
    fft_seconds: float,
    psd_average: str,
    peak_mode: str,
    psd_override: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict[str, Any]:
    # psd_override=None keeps the frozen confirm-path exactly: the PSD is still
    # estimated from `data` itself. Supplying one whitens against an external PSD
    # (e.g. off-source) without changing any existing caller.
    data = _fetch_strain(detector, segment)
    snr, sigma = matched_filter_snr(
        data, template, fft_seconds=fft_seconds, psd_average=psd_average, psd_override=psd_override
    )
    # circular correlation peaks at the template START shift; the merger sits
    # at the template's internal amplitude peak - map times accordingly
    tpl_peak_idx = int(np.argmax(np.abs(template.real[: len(data)])))
    times = segment[0] + ((np.arange(len(snr)) + tpl_peak_idx) % len(snr)) / _SAMPLE_RATE
    if peak_mode == "on_source":
        mask = np.abs(times - _CATALOG_GPS) <= _PEAK_WINDOW_S
    else:
        # exclude filter wrap-around edges (1 s each side), search the whole segment
        mask = (times > segment[0] + 1.0) & (times < segment[1] - 1.0)
    idx = int(np.argmax(snr * mask))
    return {
        "detector": detector,
        "segment_gps": list(segment),
        "snr_peak": round(float(snr[idx]), 3),
        "peak_gps": round(float(times[idx]), 4),
        "sigma": round(sigma, 6),
        "samples": len(data),
    }


def _network_statistic(h1: dict[str, Any], l1: dict[str, Any]) -> dict[str, Any]:
    """Describe the legacy two-detector statistic without implying coincidence."""
    return independent_peak_statistic(
        h1_snr=h1["snr_peak"],
        l1_snr=l1["snr_peak"],
        h1_gps=h1["peak_gps"],
        l1_gps=l1["peak_gps"],
    )


def _network(h1: dict[str, Any], l1: dict[str, Any]) -> float:
    """Compatibility scalar for historical preregistration/receipt fields."""
    return float(_network_statistic(h1, l1)["value"])


def _receipt(mode: str, payload: dict[str, Any]) -> Path:
    receipt = {
        "receipt_type": "gw_matched_filter",
        "preregistration": "docs/research/preregistrations/2026-07-12-gw150914-matched-filter.md",
        "event": _EVENT,
        "citation": _CITATION,
        "mode": mode,
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": _environment(),
        **payload,
        "can_influence_belief": False,
    }
    body = json.dumps(receipt, indent=2, default=str)
    receipt["receipt_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    _RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _RECEIPT_DIR / f"{_EVENT}_mf_{mode}_{stamp}.json"
    path.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    return path


def run_validate() -> dict[str, Any]:
    """Engineering control on OFF-SOURCE noise only. Three instrument checks:

    (a) absolute scale: pure-noise max SNR must stay below the off-source
        threshold (a broken normalization shows up as thousands - caught live
        on the first cut of this script);
    (b) linearity + recovery: a template injected at a deterministically
        calibrated target SNR must be recovered within 25%;
    (c) alignment: the recovered peak (under the template-peak time
        convention) must land within 10 ms of the injection time.
    """
    template, template_sha = _fetch_template()
    noise_h1 = _fetch_strain("H1", _OFF_SOURCE)
    n = len(noise_h1)
    edge = int(1.0 * _SAMPLE_RATE)
    noise_psd = _psd(noise_h1, fft_seconds=_WELCH_FFT_S, average="mean")

    snr_noise, _ = matched_filter_snr(
        noise_h1, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", psd_override=noise_psd
    )
    baseline = float(np.max(snr_noise[edge:-edge]))

    # deterministic calibration: filter the PURE injection (no noise) against
    # the noise PSD; its peak is the exact linear response of a unit amplitude
    tpl_real = np.pad(template.real[:n], (0, max(0, n - len(template.real[:n]))))
    tpl_peak_idx = int(np.argmax(np.abs(tpl_real)))
    # inject at quarter-segment so the correlation SHIFT index is far from 0
    # (an injection at the template's natural position peaks at shift ~0,
    # which a naive edge exclusion would wrongly discard - found live)
    inject_peak_at = n // 4
    unit = np.roll(tpl_real, inject_peak_at - tpl_peak_idx)
    snr_unit, _ = matched_filter_snr(
        unit, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", psd_override=noise_psd
    )
    unit_response = float(np.max(snr_unit))
    target_snr = 20.0
    amplitude = target_snr / max(unit_response, 1e-12)

    injected = noise_h1 + unit * amplitude
    snr_inj, _ = matched_filter_snr(
        injected, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", psd_override=noise_psd
    )
    # the SNR series is indexed by correlation SHIFT, not time: search the
    # full series and map to merger time via the template-peak convention
    peak_idx = int(np.argmax(snr_inj))
    recovered = float(snr_inj[peak_idx])
    # template-peak time convention (same mapping the run modes use)
    merger_idx = (peak_idx + tpl_peak_idx) % n
    peak_time_offset_ms = abs(merger_idx - inject_peak_at) / _SAMPLE_RATE * 1000.0

    scale_ok = baseline < _OFF_SOURCE_MAX_ALLOWED
    recovery_ok = abs(recovered - target_snr) / target_snr < 0.25
    alignment_ok = peak_time_offset_ms <= 10.0
    payload = {
        "template_sha256": template_sha,
        "noise_baseline_max_snr": round(baseline, 3),
        "absolute_scale_ok": scale_ok,
        "unit_response_snr": round(unit_response, 6),
        "injected_target_snr": target_snr,
        "recovered_snr": round(recovered, 3),
        "recovery_ok": recovery_ok,
        "peak_time_offset_ms": round(peak_time_offset_ms, 3),
        "alignment_ok": alignment_ok,
        "instrument_valid": bool(scale_ok and recovery_ok and alignment_ok),
        "note": "injection into off-source noise only; on-source segment untouched",
    }
    path = _receipt("validate", payload)
    payload["receipt"] = str(path)
    return payload


def run_control() -> dict[str, Any]:
    """Known-bad control: signal-free legacy recovery statistic must stay below 8."""
    template, template_sha = _fetch_template()
    h1 = _detector_snr("H1", _OFF_SOURCE, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", peak_mode="max")
    l1 = _detector_snr("L1", _OFF_SOURCE, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", peak_mode="max")
    statistic = _network_statistic(h1, l1)
    network = float(statistic["value"])
    payload = {
        "template_sha256": template_sha,
        "h1": h1,
        "l1": l1,
        "network_snr_max_offsource": network,
        "recovered_statistic": statistic,
        "threshold": _OFF_SOURCE_MAX_ALLOWED,
        "control_passed": network < _OFF_SOURCE_MAX_ALLOWED,
    }
    path = _receipt("control", payload)
    payload["receipt"] = str(path)
    return payload


def run_confirm() -> dict[str, Any]:
    """THE confirmatory on-source run (single, preregistered)."""
    template, template_sha = _fetch_template()
    h1 = _detector_snr("H1", _ON_SOURCE, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", peak_mode="on_source")
    l1 = _detector_snr("L1", _ON_SOURCE, template, fft_seconds=_WELCH_FFT_S, psd_average="mean", peak_mode="on_source")
    statistic = _network_statistic(h1, l1)
    network = float(statistic["value"])
    low, high = _PUBLISHED_NETWORK_SNR * (1 - _TOLERANCE), _PUBLISHED_NETWORK_SNR * (1 + _TOLERANCE)
    payload = {
        "template_sha256": template_sha,
        "h1": h1,
        "l1": l1,
        "network_snr": network,
        "recovered_statistic": statistic,
        "published_network_snr": _PUBLISHED_NETWORK_SNR,
        "preregistered_interval": [round(low, 3), round(high, 3)],
        "success": bool(low <= network <= high),
        "executor": "matched_filter_pipeline",
    }
    path = _receipt("confirm", payload)
    payload["receipt"] = str(path)
    return payload


def run_replicate() -> dict[str, Any]:
    """Within-project robustness run: median PSD, 16 s segments (per prereg)."""
    template, template_sha = _fetch_template()
    h1 = _detector_snr(
        "H1", _ON_SOURCE, template, fft_seconds=_REPLICATION_FFT_S, psd_average="median", peak_mode="on_source"
    )
    l1 = _detector_snr(
        "L1", _ON_SOURCE, template, fft_seconds=_REPLICATION_FFT_S, psd_average="median", peak_mode="on_source"
    )
    statistic = _network_statistic(h1, l1)
    network = float(statistic["value"])
    low, high = _PUBLISHED_NETWORK_SNR * (1 - _TOLERANCE), _PUBLISHED_NETWORK_SNR * (1 + _TOLERANCE)
    payload = {
        "template_sha256": template_sha,
        "h1": h1,
        "l1": l1,
        "network_snr": network,
        "recovered_statistic": statistic,
        "published_network_snr": _PUBLISHED_NETWORK_SNR,
        "preregistered_interval": [round(low, 3), round(high, 3)],
        "within_published_tolerance": bool(low <= network <= high),
        "psd_estimator": "welch_median_16s",
        "executor": "matched_filter_replicator",
    }
    path = _receipt("replicate", payload)
    payload["receipt"] = str(path)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--replicate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        out = run_validate()
    elif args.control:
        out = run_control()
    elif args.confirm:
        out = run_confirm()
    elif args.replicate:
        out = run_replicate()
    else:
        parser.print_help()
        return 2
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
