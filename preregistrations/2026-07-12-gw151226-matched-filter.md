# Preregistration: GW151226 matched-filter network SNR reproduction

**Program:** CHARTER.md §4 target 2 · **Preregistered:** 2026-07-12 (committed
before any on-source run) **Claim under test:** the public GW151226 strain data
contain a signal whose matched-filter network SNR reproduces the published
value. **Published reference:** Abbott et al. 2016, Phys. Rev. Lett. 116, 241103
— network matched-filter SNR **13.0**. This is the charter's low-SNR stress
test: a quieter, longer-inspiral binary that exercises the pipeline away from
the loud-event regime it was validated on.

## Data (locked)

- Source: GWOSC open data via `gwpy.timeseries.TimeSeries.fetch_open_data`.
- Detectors: H1 and L1.
- Catalog merger time: GPS **1135136350.6** (from `gwosc.datasets.event_gps`,
  fetched 2026-07-12 before this preregistration was committed).
- On-source segment: GPS **[1135136334.6, 1135136366.6]** (32 s centered).
- Off-source control segment: GPS **[1135136078.6, 1135136110.6]** (identical
  duration, 256 s earlier; no catalog event).
- Template: `GW151226_4_template.hdf5` from GWOSC's GW151226 event page
  (HEAD-verified 2026-07-12, 1,056,864 bytes); SHA-256 recorded at fetch.

## Pipeline (locked — identical to the validated GW150914 instrument)

Tukey(1/8) window; one-sided Welch mean PSD, 4 s FFT, 50% overlap;
frequency-domain matched filter band-limited to [20, 2048] Hz; complex template
h = h_plus + i·h_cross; per-detector SNR = peak |snr(t)| within ±0.1 s of the
catalog merger (on-source) or segment-wide max (off-source); **network SNR =
sqrt(SNR_H1² + SNR_L1²)**. Time convention: merger = correlation-shift index +
template internal peak index (validated to 0.24 ms on GW150914's instrument
checks; re-validated per-event below).

## Success / failure criteria (locked)

- **Success:** on-source network SNR within **±25%** of 13.0 → **[9.75, 16.25]**
  (wider than GW150914's ±15% per the charter: quieter event, noisier recovery
  regime — locked here, before any run).
- **Failure (falsifier fires):** outside that interval.
- **Instrument validity (Rule 26, required before any verdict):**
  - Injection validation on THIS event's off-source noise with THIS event's
    template: absolute scale (noise baseline < 8), recovery within 25% of a
    target-20 injection, alignment within 10 ms.
  - Known-bad: off-source segment-wide network SNR **< 8**, else no verdict
    (assay artifact).

## Replication requirement (locked)

Welch **median** PSD, **16 s** FFT length, executor `matched_filter_replicator`.
Success: within ±25% of 13.0 AND within ±10% of the confirmatory value.

## Stopping rule (locked)

One confirmatory on-source run + one off-source control + one replication. No
parameter changes after seeing on-source results; deviations require a v2
preregistration and the failed run is preserved as a negative result.

## Promotion rule (locked)

Identical to GW150914: register in the experiment registry; attach the
confirmatory recovery as receipt-bound EXTERNAL_EXPERIMENTAL_RESULT / EXTERNAL /
SUPPORTS (the LIGO measurement is the physical experiment); record the
replication through the reproduction machinery; expected ladder position
externally_grounded → experimentally_validated.

---

## Amendment v2 (2026-07-12, before any on-source analysis)

The locked off-source segment [1135136078.6, 1135136110.6] contains **no
science-mode data** (fetch returns 131072/131072 NaN samples for H1 — the
detector entered observing mode shortly before the event; verified with two
probe windows: −144/−112 s is 67% NaN, +112/+144 s is clean). Off-source control
and injection validation move to GPS **[1135136462.6, 1135136494.6]** (112–144 s
AFTER the event; no catalog event in the window). This is a data- availability
correction, not results-contingent tuning: no on-source analysis had been
executed for this event when this amendment was committed. All other locked
parameters are unchanged.
