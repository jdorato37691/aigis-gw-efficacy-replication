# Preregistration: GW150914 matched-filter network SNR reproduction

**Program:** CHARTER.md §4 target 1 (Day-90 gate) · **Preregistered:**
2026-07-12 (committed before any on-source run) **Claim under test:** the public
GW150914 strain data contain a signal whose matched-filter network SNR
reproduces the published value. **Published reference:** Abbott et al. 2016,
Phys. Rev. Lett. 116, 061102 — network matched-filter SNR **23.7** (GWTC catalog
value 23.7~24).

## Data (locked)

- Source: GWOSC open data via `gwpy.timeseries.TimeSeries.fetch_open_data`.
- Detectors: H1 and L1.
- On-source segment: GPS **[1126259446, 1126259478]** (32 s centered on the
  catalog merger time 1126259462.4), sample rate 4096 Hz.
- Off-source control segment: GPS **[1126259190, 1126259222]** (identical
  duration, 256 s earlier; no catalog event in the segment).
- Template: the NR-calibrated GW150914 template published in GWOSC's own event
  release (`GW150914_4_template.hdf5`, from the GWOSC GW150914 event page). Its
  SHA-256 is recorded in the run receipt at fetch time.

## Pipeline (locked)

1. Tukey window (alpha = 1/8) on data and template.
2. One-sided PSD of each detector's on-source (resp. off-source) segment via
   Welch mean-average, 4 s FFT length, 50% overlap (`scipy.signal.welch`).
3. Frequency-domain matched filter, band-limited to **[20, 2048] Hz**:
   `snr(t) = |4 df · IFFT( d̃(f) · h̃*(f) / S_n(f) )| / sigma`, with
   `sigma² = 4 df · Σ |h̃(f)|² / S_n(f)`; complex template
   `h = h_plus + i·h_cross`.
4. Per-detector SNR = peak `|snr(t)|` within **±0.1 s** of the catalog merger
   time (on-source) or the segment-wide maximum (off-source control).
5. **Primary metric:** network SNR = sqrt(SNR_H1² + SNR_L1²).

## Success / failure criteria (locked)

- **Success:** on-source network SNR within **±15%** of 23.7 → **[20.1, 27.3]**.
- **Failure (falsifier fires):** on-source network SNR outside that interval.
- **Instrument validity (Rule 26, both required before the verdict counts):**
  - Known-good: the on-source run is the oracle input and must PASS if the
    pipeline is valid AND the published claim is true.
  - Known-bad: the off-source control's segment-wide network SNR must be **<
    8**; if noise alone produces ≥ 8, the instrument is invalid and NO verdict
    is issued (assay artifact, not a result).
- Engineering validation before the confirmatory run uses INJECTION into
  off-source noise only — the on-source segment is not touched until the single
  confirmatory run.

## Replication requirement (locked)

One independent re-run with a **different PSD estimator (Welch median-average)**
and a **different segment length (16 s)**. Replication succeeds if its network
SNR is within ±15% of 23.7 AND within ±10% of the confirmatory run's value.
Executed by a different executor identity than the confirmatory run
(`matched_filter_replicator` vs `matched_filter_pipeline`) so independence is
derivable under `scientific_memory` rules.

## Stopping rule (locked)

One confirmatory on-source run + one off-source control + one replication run.
No parameter changes after seeing on-source results; any deviation requires a
new preregistration (v2) and the failed run is preserved as a negative result.

## Promotion rule (locked)

Only if success + valid instrument + replication: register the experiment in the
registry, attach the receipt-backed matched-filter recovery as
EXTERNAL_EXPERIMENTAL_RESULT / EXTERNAL / SUPPORTS evidence (the LIGO strain
measurement is the physical experiment; the template is NOT the validation), and
record the replication via the reproduction machinery. Expected ladder position:
externally_grounded, then experimentally_validated after the independent
confirmation binds.
