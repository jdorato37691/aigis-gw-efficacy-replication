# Preregistration: GW170817 matched-filter network SNR + GW→GRB delay

**Program:** CHARTER.md §4 target 3 (multi-messenger capstone) ·
**Preregistered:** 2026-07-12 (committed before any on-source analysis) **Claims
under test:**

1. The public GW170817 strain data contain a binary-neutron-star signal whose
   matched-filter network SNR reproduces the published value.
2. The recovered merger time precedes the Fermi-GBM trigger for GRB 170817A by
   the published ~1.7 s — the multi-messenger association.

**Published references:** Abbott et al. 2017, Phys. Rev. Lett. 119, 161101
(network matched-filter SNR **32.4**; H1 18.8, L1 26.4); Abbott et al. 2017,
ApJL 848, L13 (GW→GRB delay **+1.74 s**; GBM trigger GPS **1187008884.47**).

## Data (locked)

- Source: GWOSC open data via `gwpy.timeseries.TimeSeries.fetch_open_data`, 4096
  Hz, detectors H1 and L1 (V1 contributes ≈0.1 to network SNR; excluded, and the
  published H1⊕L1 quadrature is 32.4).
- Catalog merger time: GPS **1187008882.4** (`gwosc.datasets.event_gps`, fetched
  pre-registration).
- On-source segment: GPS **[1187008762.4, 1187008890.4]** (128 s: 120 s of
  inspiral + 8 s post-merger; the 30 Hz-to-merger chirp is ~54 s).
- Off-source control segment: GPS **[1187008250.4, 1187008378.4]** (128 s, 512 s
  earlier; NaN-free, verified pre-registration).

## Template (locked): TaylorF2, pure numpy

No pycbc/lalsuite is installed; the template is the standard frequency-domain
TaylorF2 stationary-phase inspiral, 3.5PN point-particle phasing, implemented in
numpy from the published coefficients:

- Detector-frame chirp mass **1.1977 M☉** (source 1.186 × (1+z), z=0.0099);
  component masses 1.46/1.27 M☉ (source) for η and the ISCO cutoff.
- Amplitude ∝ f^(−7/6); band **[30, f_ISCO≈1590] Hz**; h = h+ + i·h× via a 90°
  phase rotation; converted to the time domain on the analysis grid with the
  merger placed at a known index (the instrument's time convention).
- Absolute amplitude is irrelevant (σ-normalization cancels it).
- **Coefficient-integrity check (locked, part of instrument validation):** the
  3.5PN phase implementation must agree with an independently written 2PN
  implementation to <0.5 rad across [30, 400] Hz when the 2.5PN+ terms are
  zeroed — a transcription-error tripwire that never touches on-source data.
- Tidal terms omitted (they contribute negligible SNR below ~600 Hz); this is a
  detection-grade, not parameter-estimation-grade, template. Expected match loss
  ≤ a few percent — covered by the tolerance.

## Pipeline (locked)

As validated on GW150914/GW151226 (Tukey 1/8; Welch mean 4 s PSD; FD matched
filter; template-peak time convention) with one locked band change: analysis
band **[30, 2048] Hz** (BNS inspiral; below 30 Hz the PSD is unusable and the
template would be minutes long).

### L1 glitch rule (locked, mechanical — decided without inspecting on-source data)

L1 had a documented instrumental transient ~1.1 s before merger. Whether GWOSC's
served data still contains it is unknown at preregistration time and will NOT be
inspected beforehand. Locked conditional: whiten L1 on-source; if any |whitened
strain| > 15σ occurs in [tc−2 s, tc−0.5 s], gate [t_glitch−0.2 s, t_glitch+0.2
s] with an inverse-Tukey (0.1 s taper) before filtering — the published
mitigation class; the gating receipt records whether the branch fired. H1 gets
no gate.

## Success / failure criteria (locked)

- **SNR success:** network SNR within **±15%** of 32.4 → **[27.54, 37.26]**.
- **Timing success (multi-messenger):** recovered H1/L1 merger peaks within ±0.1
  s of catalog GPS, H1–L1 delay ≤ 10 ms (causal), and **T_GRB − T_merger ∈ [1.5,
  2.0] s** (published +1.74 s).
- **Failure:** either criterion outside its interval → falsifier fires; the
  negative is preserved.
- **Instrument validity (Rule 26):** injection validation on off-source noise
  with the TaylorF2 template (scale <8, recovery ±25%, alignment ≤10 ms) + the
  coefficient-integrity check + off-source network max < 8.

## Replication requirement (locked)

Welch **median** PSD, **16 s** FFT length, executor `matched_filter_replicator`.
Success: within ±15% of 32.4 AND within ±10% of the confirmatory value.

## Stopping rule (locked)

One confirmatory on-source run + one off-source control + one replication. No
post-hoc parameter changes; deviations require a v2 amendment (data availability
only) or a new preregistration, and failed runs are preserved.

## Promotion rule (locked)

As GW150914/GW151226: registry record; receipt-bound
EXTERNAL_EXPERIMENTAL_RESULT / EXTERNAL / SUPPORTS evidence (the LIGO
measurement is the physical experiment; the TaylorF2 waveform is NOT the
validation — it is the filter); replication through the reproduction machinery;
expected externally_grounded → experimentally_validated. The GRB delay result is
recorded in the same receipt with its own pass/fail.

---

## Erratum (2026-07-12, post-run; the negative stands)

The timing criterion FAILED as preregistered (recovered delay 2.026 s vs the
locked [1.5, 2.0] s window) and that verdict is unchanged. Post-run diagnosis of
the WINDOW's derivation: this preregistration locked the Fermi-GBM **trigger**
GPS (1187008884.47 ↔ 12:41:06.4746 UTC) but derived the window from the
published **+1.74 s**, which measures merger to the burst **onset** (the GBM
light-curve start precedes the trigger by ~0.3 s). Trigger minus catalog
coalescence is ~2.04–2.05 s; the recovered 2.026 s sits within ~20 ms of that —
i.e., the measurement is sound and the window paired mismatched fiducials. No
re-test is scientifically meaningful on this data (the recovered merger time is
already known); a corrected timing claim would require a new preregistration on
materially different analysis. Lesson recorded: lock the fiducial DEFINITION
(trigger vs onset), not just the number.
