# Preregistration: out-of-sample test of the inspiral-efficacy curve (GWTC-3)

**Program:** CHARTER G3 track, Study 3 · **Preregistered:** 2026-07-12
(committed before any run) **Question:** do the GWTC-1 findings — the
mass–recovery curve (Study 1) and the aligned-spin template (Study 2) — predict
recovery on events that played NO role in forming them?

This is the strongest replication form available to the program: a locked
predictor from in-sample data, scored on a seeded random sample of unseen GWTC-3
events. (The 2026-07-09 KALB lesson institutionalized: pre-registered
out-of-sample or it isn't real.)

## Sample (locked; seeded, drawn pre-registration)

From GWTC-3-confident (eventapi, fetched pre-registration): eligible = BBH (m2 ≥
3 M☉), published network SNR ≥ 8, not in GWTC-1 → 26 events.
`numpy.random.default_rng(20260712).choice(26, 20, replace=False)` selects these
20 (name / GPS / published SNR / M_det / χ_eff):

GW200316_215756 1268431094.1 10.3 25.5 +0.13 · GW200311_115853 1267963151.3 17.8
76.1 −0.02 · GW200302_015811 1267149509.5 10.8 74.0 +0.01 · GW200225_060421
1266645879.3 12.5 40.6 −0.12 · GW200224_222234 1266618172.4 20.0 96.0 +0.10 ·
GW200220_124850 1266238148.1 8.5 110.9 −0.07 · GW200219_094415 1266140673.1 10.7
102.7 −0.08 · GW200202_154313 1264693411.5 10.8 19.0 +0.04 · GW200128_022011
1264213229.9 10.6 116.7 +0.12 · GW200112_155838 1262879936.0 19.8 79.2 +0.06 ·
GW191230_180458 1261764316.4 10.4 146.0 −0.05 · GW191222_033537 1261020955.1
12.5 120.5 −0.04 · GW191216_213338 1260567236.4 18.6 21.2 +0.11 ·
GW191215_223052 1260484270.3 11.2 58.1 −0.04 · GW191204_171526 1259514944.0 17.4
22.7 +0.16 · GW191204_110529 1259492747.5 8.9 62.3 +0.05 · GW191129_134029
1259070047.1 13.1 20.2 +0.06 · GW191127_050227 1258866165.5 9.2 120.9 +0.18 ·
GW191126_115259 1258804397.6 8.3 26.5 +0.21 · GW191109_010717 1257296855.2 17.3
140.0 −0.29

## Pipeline (locked — identical to Studies 1–2)

Spin-extended TaylorF2 (Study 2's template, χ_eff from the table above), same
instrument, 32 s on-source, band [30, 2048] Hz, Welch mean 4 s PSD, per-event H3
off-source validity (< 8) with the mechanical offset fallback chain. **O3
availability rule (mechanical):** an event lacking NaN-free H1+L1 data in its
segments after the fallback chain → `data_unavailable`, excluded, documented.
Excluded events do not count against the predictions.

## Locked predictor (derived ONLY from GWTC-1 in-sample results)

R̂(M_det), binned medians of Study 2's spin-template recoveries:

| M_det bin | R̂     | derived from                                                   |
| --------- | ----- | -------------------------------------------------------------- |
| < 30      | 0.849 | GW170608 0.909, GW151226 0.789                                 |
| 30–70     | 0.554 | GW151012 0.683, GW170104 0.480, GW170814 0.554                 |
| 70–100    | 0.428 | GW170809 0.261, GW150914 0.445, GW170818 0.410, GW170823 0.438 |
| > 100     | 0.210 | GW170729 0.210                                                 |

## Preregistered predictions

- **O1 (trend generalizes):** Spearman ρ(M_det, R) ≤ **−0.5** across measured
  OOS events (softer than in-sample −0.6: O3 events are quieter and the sample
  narrower in places; locked here, before any run).
- **O2 (the curve predicts):** median |R − R̂(M_det)| ≤ **0.15** across measured
  OOS events.
- **O3-validity (Rule 26):** per-event off-source max < 8, else no verdict for
  that event.

Falsifiers: O1 fails → the mass trend was a GWTC-1 artifact. O2 fails → the
curve does not transfer across observing runs (instrument-era dependence —
itself informative).

## Stopping rule (locked)

One pass over the 20-event sample (checkpointed; resumable across process
restarts without re-measuring). No re-runs, no parameter changes after results.
The study registers regardless of outcome.

## Promotion rule (locked)

One registry record, receipt-bound external evidence, single-pass ceiling
**externally_grounded**. If O1+O2 hold, Studies 1+2 gain an out-of-sample
replication arm and the SET (curve + spin fix + OOS transfer) becomes the
program's first preprint-consolidated contribution.
