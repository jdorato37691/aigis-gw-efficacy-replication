# Preregistration: coherence-controlled IMR test on heavy BBH (Study 5)

**Program:** CHARTER G3 track, Study 5 · **Preregistered:** 2026-07-12
(committed before any run) **Motivating result (Study 4,
exp_20f8fb7cc45ac49a2987dfd2, contested):** the continued-phase IMR hybrid
FAILED its no-degradation artifact control (GW151226 −0.061) — phase-incoherent
merger content dilutes template norm on low-mass events. The heavy-event
improvements (unverdicted medians 0.438→0.540 in-sample, 0.258→0.562 OOS)
therefore received no verdict.

**Redesign, from the failure mechanism:** the question is whether those heavy
improvements are COHERENT merger signal or a loudness/norm artifact. The correct
known-bad is a **phase-scrambled twin**: identical amplitude model, identical
inspiral, but the added band's phase replaced by seeded uniform noise. A norm
artifact survives scrambling; coherent physics does not.

**Applicability domain (declared, measured):** the hybrid template family is
mass-gated — heavy events only (M_det ≥ 60). Study 4's preserved negative IS the
measurement justifying the gate; low-mass events keep the validated
spin-TaylorF2. No low-mass predictions are made here.

## Template & twin (locked)

- **Hybrid:** exactly Study 4's ansatz (same code path, same remnant fits, gates
  G-a/G-b/G-c re-run as prerequisites).
- **Scrambled twin:** identical except phase(f ≥ f_ISCO) ~ U[0, 2π),
  `numpy.random.default_rng(20260712)`, one draw per event (deterministic).
- Inspiral content below f_ISCO is bitwise-identical between twin and hybrid.

## Event sets (locked; same rows as Study 4)

- Heavy GWTC-1 (7): GW170104, GW170814, GW170809, GW150914, GW170818, GW170823,
  GW170729 — spin-TaylorF2 baselines median 0.438.
- Heavy GWTC-3 OOS arm (7): GW200220, GW200219, GW200128, GW191230, GW191222,
  GW191127, GW191109 — baselines median 0.258.

## Preregistered predictions

- **Q1 (recovery):** median R_hybrid over the 7 heavy GWTC-1 events ≥ **0.65**.
- **Q2 (coherence, the decisive control):** median (R_hybrid − R_scrambled) over
  the 7 heavy GWTC-1 events ≥ **+0.10**, AND R_hybrid ≥ R_scrambled for at least
  **6 of 7** events. Falsifier: the scrambled twin matches the hybrid → the
  "improvement" is a norm/loudness artifact and the ansatz is dead in its
  current form.
- **Q3 (OOS arm):** median R_hybrid over the 7 GWTC-3 heavy events ≥ baseline +
  **0.15** (i.e. ≥ 0.408), with the same coherence margin (median hybrid −
  scrambled ≥ +0.10).

## Stopping rule (locked)

One pass: hybrid + scrambled twin per event (28 runs, cached strain). No
re-runs, no threshold edits. Registers regardless of outcome.

## Promotion rule (locked)

One registry record, receipt-bound external evidence, ceiling
**externally_grounded**. Paper and memory updated with the outcome either way.
If Q2 fails, the merger-phase problem is fundamental to the ansatz and the
program's next step is sourcing the real PhenomD tables (with the operator
supplying the papers for verifiable transcription).
