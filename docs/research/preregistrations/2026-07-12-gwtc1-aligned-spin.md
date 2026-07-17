# Preregistration: aligned-spin TaylorF2 — testing the GW151226 diagnosis

**Program:** CHARTER G3 track, Study 2 · **Preregistered:** 2026-07-12
(committed before any run) **Motivating result (Study 1,
exp_d8083481cdf64d910ac08118):** the zero-spin TaylorF2 sweep recovered only R =
0.557 on GW151226 (M_det 23.3) while the NR-calibrated template recovered R =
0.91 on the same data. Diagnosis under test: the loss is the omitted
**aligned-spin phasing** (GW151226 is the one GWTC-1 event with significant
χ_eff ≈ 0.18); a 1.5PN spin-orbit term should recover most of the gap — and
should NOT move non-spinning events.

## Template extension (locked)

Add the leading-order aligned-spin-orbit contribution to the 1.5PN phasing
coefficient of the existing TaylorF2 implementation:

- a3 = −16π + **(113/3 − 76η/3) · χ_eff** (single-effective-spin,
  detection-grade approximation: both component spins set to χ_eff, aligned).
- 2PN spin-spin (σ) and higher-order spin terms are deliberately omitted (|χ| ≤
  0.4 across the set; their phase contribution is second-order) — a stated
  approximation, not an oversight.
- **Zero-spin regression (Rule 26, required):** with χ_eff = 0 the extended
  implementation must reproduce the Study-1 template exactly (max absolute
  waveform difference < 1e-12), so any recovery change is attributable to the
  spin term alone.

## Event spins (locked; GWTC-1-confident eventapi, fetched pre-registration)

GW150914 −0.01 · GW151012 0.05 · GW151226 **0.18** · GW170104 −0.04 · GW170608
0.03 · GW170729 **0.37** · GW170809 0.08 · GW170814 0.07 · GW170818 −0.09 ·
GW170823 0.09

All other event parameters, segments, pipeline, and validity rules are identical
to Study 1's preregistration (same instrument, same locked table).

## Preregistered predictions

- **P1 (the diagnosis):** GW151226 recovery fraction with the spin-extended
  template ≥ **0.75** (from 0.557). Falsifier: R < 0.75 → the spin-omission
  diagnosis is insufficient (implicating higher modes, spin-spin, or the
  single-spin approximation) — that negative is itself informative.
- **P2 (differential control):** the four near-zero-spin events (|χ_eff| ≤ 0.05:
  GW150914, GW170104, GW170608, GW151012) each change by **< 0.05 absolute** in
  R. Falsifier: any of them moves ≥ 0.05 → the "spin term" is doing something
  other than spin (implementation artifact).
- **P3 (structure preserved):** Spearman ρ(M_det, R_spin) ≤ **−0.6** — spin
  phasing does not substitute for the missing merger–ringdown, so the mass trend
  persists.
- GW170729 (χ = 0.37, M_det = 125.5): expectation of a modest improvement is
  noted but NOT locked as a criterion (its band holds too few cycles for a
  confident quantitative prediction).

## Stopping rule (locked)

One sweep pass with the spin-extended templates (H3 off-source validity per
event as in Study 1). No re-runs or parameter changes after results. The study
registers regardless of outcome; failed predictions are preserved.

## Promotion rule (locked)

One registry record (source `gw_replication`), receipt-bound external evidence
as Study 1; single-pass ceiling **externally_grounded**. If P1+P2 both hold, the
pair (Study 1 negative + Study 2 recovery under a locked differential
prediction) constitutes the charter's first completed
hypothesis→falsification→mechanism→verification loop on external physics.
