# Preregistration: sourced-physics completion — closing D1/D2 (Study 7)

**Program:** CHARTER G3 track, Study 7 · **Preregistered:** 2026-07-12
(committed before any on-source run) **Motivating item:** the paper's §5
top-ranked residual — the declared deviations D1 (ψ_TF2 spin sector is
1.5PN-only) and D2 (remnant fits anchor-validated but unsourced) — closed by the
same verifiable-transcription machinery as Study 6, from the two
already-sha256-stamped arXiv sources.

## Sourced physics (locked; `scripts/research/sourced_physics.py`)

- **Full-spin TaylorF2** (closes D1): the complete φ₀–φ₇ from arXiv:1508.07253
  Appendix `sec:app_pncoeffs` (tex ~2497-2560) — linear spin-orbit to 3.5PN (φ₅
  with its log, φ₆, φ₇) and quadratic-in-spin at 2PN (φ₄) — under the retained
  equal-spin approximation χ₁=χ₂=χ_eff (χ_a = 0; all δχ_a cross terms vanish
  identically; D3 remains declared).
- **Sourced remnant** (closes most of D2): a_f from arXiv:1508.07250
  `eqn:FinalSpin` (S = S₁+S₂ convention; equal spins → S = χ_eff(1−2η)); E_rad
  from `eqn:Erad` (Ŝ = χ_eff), whose nonspinning polynomial is identical to the
  previously anchor-validated one. QNM conversion stays the Berti fit — D2
  narrows to exactly that.
- Everything else — the Study-6 sourced PhenomD σ/β/α phase, the amplitude
  ansatz, C¹ stitching, all thresholds — is byte-identical code.

## Integrity gates (all PASSED pre-registration; re-run before measurements)

- **g1** zero-spin regression vs the validated point-particle series: 2.3e-13
  rad worst. PASS.
- **g2** 1.5PN-only consistency vs the validated Study-2 spin term: 1.1e-13 rad
  worst. PASS.
- **g3** transcription spot-checks against verbatim source strings. PASS.
- **g4** remnant anchors: GW150914 a_f 0.680 / f_RD 247.7 Hz / E_rad 4.76%
  (published 0.69 / ~250 / 4.6%); GW170729 a_f 0.785 (published 0.81, band
  ±0.06). The GW170729 anchor DISCRIMINATES the S-vs-Ŝ convention: the rescaled
  reading yields 0.91 and fails. PASS.
- **g5 (harness identity control, in-run):** the module-injection mechanism used
  to build the sourced arm, when injected with the ORIGINAL functions, must
  reproduce the baseline arm's templates bitwise. A harness that alters what it
  wraps is invalid.

## Design (locked): paired, in-run, differential

Both arms measured in one run per event under the Study-6 confirm configuration
(Welch mean 4 s, raw v1 statistic within ±0.1 s of catalog time), with per-event
off-source known-bad (< 8) and the standard post-run coincidence audit. Arms:
**baseline** = the committed Study-6 pipeline; **sourced** = same pipeline with
φ_TF2 → full-spin and remnant → sourced. Event set: the 7 heavy GWTC-1, the 6
measured GWTC-3, plus the two low-mass controls GW170608 (χ ≈ 0.03) and GW151226
(χ ≈ 0.18) — 15 events × 2 arms.

## Preregistered predictions (locked)

- **Z1 (the spin-sensitive subject):** GW151226 — thousands of in-band cycles,
  χ_eff ≈ 0.18 — must not degrade: R_sourced ≥ R_baseline − **0.02**. Falsifier:
  the completed spin sector + sourced remnant degrading the highest-cycle spin
  event indicates a transcription/convention error or a destructive interaction
  with the σ-terms' fitted baseline.
- **Z2 (differential control):** every event with |χ_eff| ≤ 0.10: |R_sourced −
  R_baseline| < **0.02**. The sourced physics is spin physics plus small
  remnant-fit refinements; near-zero-spin events must not move.
- **Z3 (no heavy degradation):** median heavy GWTC-1 R_sourced ≥ median
  R_baseline − **0.02**.
- **Z4 (spin events, reported not locked):** per-event ΔR for |χ_eff| > 0.10
  (GW170729, GW151226, and any GWTC-3 rows qualifying) reported with direction.
  Expectation: improvement; heavy spin events carry few in-band inspiral cycles,
  so honest uncertainty is declared rather than locked.

## Stopping & promotion rules (locked)

One pass (30 measurements + off-source controls, cached strain), no re-runs, no
threshold edits. One registry record, receipt-bound external evidence,
single-pass ceiling **externally_grounded**, registers regardless of outcome.
Paper §3.10/§5 and memory updated either way.
