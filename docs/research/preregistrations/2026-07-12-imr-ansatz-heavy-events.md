# Preregistration: IMR hybrid ansatz — recovering the heavy-BBH deficit

**Program:** CHARTER G3 track, Study 4 · **Preregistered:** 2026-07-12
(committed before any on-source run) **Motivating result:** Studies 1–3
established that inspiral-only recovery declines with detector-frame mass
(in-sample ρ = −0.891; OOS ρ = −0.87) because heavy binaries carry their SNR in
the post-ISCO merger–ringdown band the template lacks. This study tests whether
a physically-anchored hybrid template recovers that deficit.

## Template choice (stated per the program's honesty rule)

**NOT PhenomD.** Transcribing the ~100 fitted PhenomD coefficients
(Husa/Khan 2016) without the papers in hand is a fabrication risk this program
does not take. Instead, a **PhenomA-shaped hybrid ansatz**, every ingredient
either already validated or anchor-checkable:

- **Inspiral (f < f_ISCO):** the validated spin-extended TaylorF2 (Studies 2–3),
  amplitude f^(−7/6), unchanged.
- **Merger (f_ISCO ≤ f < f_RD):** amplitude continued C⁰ as
  A(f_ISCO)·(f/f_ISCO)^(−2/3) — the PhenomA merger slope.
- **Ringdown (f ≥ f_RD):** Lorentzian L(f) ∝ f_damp² / ((f − f_RD)² + f_damp²),
  amplitude-matched at f_RD; cutoff at f_RD + 4 f_damp.
- **Phase:** the TaylorF2 analytic phase continued through merger–ringdown — a
  stated detection-grade approximation (the dominant known weakness; an
  imperfect merger phase erodes but does not zero the added band's SNR).

**Remnant quantities per event** from (m1, m2, χ_eff): a_f = 2√3 η − 3.5171 η² +
2.5763 η³ + 0.48 χ_eff (clamped); E_rad = 0.0559745 η + 0.580951 η² − 0.960673
η³ + 3.35241 η⁴; M_f = M(1−E_rad); QNM via Berti–Cardoso–Will: Mω = 1.5251 −
1.1568(1−a_f)^0.1292, Q = 0.7 + 1.4187(1−a_f)^(−0.499); f_damp = f_RD/2Q.

## Integrity gates (all required BEFORE any on-source run; Rule 26)

- **G-a (anchor tripwire, executed pre-registration and re-run in code):** the
  remnant pipeline must put GW150914 at a*f ∈ [0.62, 0.76], f_RD ∈ [220, 280]
  Hz, E_rad ∈ [0.035, 0.06] (published: 0.69, ~250 Hz, 4.6%) and GW170729 at
  |a_f − 0.81| < 0.06. \_Verified 2026-07-12 pre-registration: 0.679 / 247.4 Hz
  / 0.048 / 0.844 — all pass.*
- **G-b (inspiral-limit regression):** for the BNS anchor configuration
  (GW170817 masses), the IMR template must equal the spin-TaylorF2 template over
  the analysis band to numerical precision wherever f < f_ISCO ≈ 1590 Hz (the
  modification must live strictly above the matching frequency).
- **G-c (instrument validation):** injection recovery of an IMR-ansatz waveform
  on off-source noise (scale < 8, recovery ±25%, alignment ≤ 10 ms).
- **G-d (per-event known-bad):** off-source network max < 8, else no verdict.

## Event sets (locked; all parameters from the prior committed preregs)

- **Heavy in-sample (P1):** the 7 GWTC-1 events with M_det ≥ 60: GW170104,
  GW170814, GW170809, GW150914, GW170818, GW170823, GW170729. Baseline (Study 2
  spin-template) recoveries: 0.480, 0.554, 0.261, 0.445, 0.410, 0.438, 0.210 →
  median 0.438.
- **Low-mass controls (P2):** GW170608 (baseline 0.909), GW151226 (0.789).
- **OOS heavy arm (P3):** the 7 measured GWTC-3 events with M_det ≥ 100:
  GW200220 (0.258), GW200219 (0.239), GW200128 (0.443), GW191230 (0.254),
  GW191222 (0.298), GW191127 (0.398), GW191109 (0.098) → median 0.258.

## Preregistered predictions

- **P1 (primary):** median R over the 7 heavy GWTC-1 events ≥ **0.65** (baseline
  0.438). **P1-strong (secondary, aspirational):** ≥ 0.75. Both reported; the
  study's pass/fail verdict is P1.
- **P2 (no-degradation artifact control):** neither low-mass control loses more
  than **0.05** (R_IMR ≥ R_baseline − 0.05). The inspiral part is identical
  below f_ISCO, so degradation would indicate the added band is injecting
  incoherent junk (artifact), not physics. Improvement is allowed (their merger
  bands carry real residual SNR).
- **P3 (OOS heavy arm):** median R over the 7 GWTC-3 heavy events improves by ≥
  **+0.15** absolute (from 0.258).

Falsifiers: P1 fails with valid gates → the ansatz (most plausibly its
continued-TaylorF2 merger phase) is insufficient — a preserved negative that
would justify the full PhenomD transcription effort with sourced tables. P2
fails → artifact; NO P1/P3 verdicts are issued (assay invalid).

## Stopping rule (locked)

One pass per event set. No re-runs, no parameter changes, no threshold edits
after results. Registers regardless of outcome.

## Promotion rule (locked)

One registry record, receipt-bound EXTERNAL_EXPERIMENTAL_RESULT evidence,
single-pass ceiling **externally_grounded**. Update the internal preprint with
the outcome (positive or negative) and the memory file.
