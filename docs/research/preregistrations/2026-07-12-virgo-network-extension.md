# Preregistration: Virgo network extension (Study 8)

**Program:** CHARTER G3 track, Study 8 · **Preregistered:** 2026-07-12
(committed before any on-source V1 run) **Motivating item:** the paper's §5
residual — three-detector events are filtered to H1+L1 while their published
network SNRs include Virgo, making those rows conservative by construction. This
study adds V1 through the same validated instrument (`_detector_snr("V1", ...)`;
off-source availability probed pre-registration: GW170809/GW170814/GW170818 and
the O3 arm fetch clean; GW170823 is all-NaN — Virgo not observing — and is
excluded mechanically).

## The design hazard, named first (Rule 26)

An independent-max network statistic GAINS a positive term from a third detector
even on pure noise: sqrt(H² + L² + V²) > sqrt(H² + L²) always. Any "improvement"
claim must therefore beat a measured noise-null, and the known-bad threshold
must be recalibrated for three detectors.

## Statistic & controls (locked)

- **3-det network:** sqrt(H1² + L1² + V1²), each detector's peak searched
  independently in the ±0.1 s catalog window (the v1 convention), Study-7
  sourced-physics templates (the current best), confirm config (Welch mean 4 s).
- **Per-event noise-null:** on each event's off-source segment, ΔR_null = (net3
  − net2)/published — the mechanical inflation V1 noise adds. Computed per
  event, in-run, before its on-source measurement is interpreted.
- **Known-bad (3-det):** off-source net3 < **9.80** = √(3/2) × 8 (each detector
  contributes comparable noise quadrature; the 2-det threshold scales by
  √(3/2)). The 2-det < 8 control is also still evaluated.
- **V1 injection validation (in-config oracle):** a calibrated template injected
  into real V1 off-source noise at ρ = 20 must be recovered within ±25% with ≤
  10 ms alignment, once, before any on-source V1 run.
- **Coincidence audit:** V1 peak time within **30 ms** of the H1 peak
  (H1-V1/L1-V1 light travel ≈ 27 ms) — reported per event, feeding W2.

## Event set (locked, mechanical)

All 15 Study-7 events; V1 attempted per event; events whose V1 strain is absent
or NaN on either segment are excluded from V1 claims (their 2-det values are
untouched by construction). Expected V1-available: GW170809, GW170814, GW170818,
and the six GWTC-3 rows (subject to the mechanical check).

## Preregistered predictions (locked)

- **W1 (signal beyond the noise-null):** median over V1-available events of
  (ΔR_onsource − ΔR_null,event) > **0**, where ΔR = (net3 − net2)/published on
  the respective segment. Falsifier: Virgo adds no more on-source than its noise
  inflation → the V1 arm carries no usable signal in this pipeline.
- **W2 (the canonical triple):** GW170814 — the first published three-detector
  detection (published V1 SNR ≈ 4.8) — must show a V1 on-source peak ≥ **4.0**
  coincident with H1 within **30 ms**.
- **W3 (no 2-det regression):** the in-run 2-det values must equal Study 7's
  sourced-arm values for every event (same templates, same config — determinism
  check, tolerance 0.001).

## Stopping & promotion rules (locked)

One pass; no re-runs; no threshold edits. One registry record, receipt-bound
external evidence, single-pass ceiling **externally_grounded**, registers
regardless of outcome. Paper §3.11/§5 and memory updated either way.

## Amendment v2 (2026-07-12, committed before any on-source V1 run)

The first V1 injection-oracle attempt failed closed: GW170814's first off-source
candidate contains a loud Virgo transient (noise-only max SNR 49.3; the next
three candidates are clean at 4.3-4.7 with median |SNR| 1.08 — whitening
verified healthy). The oracle as drafted omitted the absolute-scale screen that
`run_validate` has always applied to H1/L1 noise, and had no segment walk.
Amendment (usability rule, same class as the GW151226 NaN amendment):

- **Oracle noise segment:** the first off-source candidate whose V1 strain is
  non-NaN AND whose V1 noise-only max SNR (1 s edges excluded) is < **8** (the
  standard absolute-scale screen). The candidate-0 glitch observation is
  preserved in the receipt.
- **Per-event off-source selection** for V1-available events extends the same
  usability screen to V1 (non-NaN + noise-only max < 8), exactly as H1/L1
  candidates have always been walked on NaN. The 3-det known-bad (< 9.80) is
  then evaluated on the selected segment as locked.

No prediction, threshold, or on-source rule changes.
