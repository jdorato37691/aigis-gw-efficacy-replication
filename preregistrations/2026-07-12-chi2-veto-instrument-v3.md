# Preregistration: per-detector chi-squared veto (instrument v3)

**Program:** CHARTER G3 track, instrument iteration 3 · **Preregistered:**
2026-07-12 (committed before any on-source v3 run) **Motivating negative
(instrument v2, receipt `COINCIDENT_v2_20260712T042113Z.json`):** coincidence
plus an amplitude floor cannot both keep quiet real events and reject loud
transients — the 4.0 floor zeroed genuine detections (GW170818 confirm H1 ≈ 3.9)
while the 39σ H1 transient survived at 32.9. The discriminating information is
waveform consistency, which is what the Allen frequency-binned χ² measures
(Allen 2005, PRD 71, 062001 — standard published methodology, not a
fitted-coefficient table).

## The v3 statistic (locked)

Per detector, the matched-filter integrand is partitioned into **p = 16**
frequency bins of equal template power (equal Σ|h̃|²/S_n by cumulative sum over
|f|; Σ_l z_l(t) = z(t) exactly by construction):

    chi2(t)   = p * sum_l | z_l(t) - z(t)/p |^2 ,   dof = 2p - 2 = 30
    chi2_r(t) = chi2(t) / dof
    rho_hat(t) = rho(t)                                if chi2_r <= 1
               = rho(t) * [ (1 + chi2_r^3) / 2 ]^(-1/6) otherwise

(the standard re-weighted SNR; a transient that does not share the template's
frequency evolution concentrates power in few bins, inflating χ² and suppressing
ρ̂; Gaussian noise and template-matching signals sit at χ²_r ≈ 1).

    v3 = max_j sqrt( rho_hat_H[j]^2 + max_{|k-j| <= 10 ms} rho_hat_L[k]^2 )

over the same ±0.1 s / interior windows as v1-v2. **No amplitude floor** (the v2
C1 lesson). Coincidence pairing retained from the validated `coincident_network`
module. v1/v2 code paths untouched.

## Instrument-validity gates (X0-X4 — ALL required before any registry action)

- **X0a (template injection, off-source noise):** injected exact template at
  calibrated ρ = 20 → χ²_r at the peak ∈ [0.3, 3.0] AND ρ̂/ρ ≥ 0.90.
- **X0b (blip injection, the synthetic glitch):** a 1 ms Gaussian-windowed
  impulse scaled to matched-filter response ρ ≥ 15 → χ²_r at its peak ≥ 5 AND ρ̂
  < 0.6·ρ. A veto that cannot tell a blip from a chirp is invalid.
- **X1 (no clean-event veto):** all 13 Study-6 confirm rows: v3 ≥ **0.75·v1**
  (template-mismatch χ² inflation is allowed to cost at most 25%; zeroing or
  gross suppression of genuine events invalidates the instrument, per v2).
- **X2 (glitch suppression):** GW200220 replicate row: v3 < v1 (39.56) strictly
  AND the H1 transient's ρ̂ < **0.5** of its raw 39.0.
- **X3 = X0a executed on the first event's real off-source segment.**
- **X4 (known-bad):** off-source v3 < 8 on all 13 events (ρ̂ ≤ ρ makes this
  monotone from v2's C3; still measured).

## Preregistered replication re-measure (X5)

All 13 rows re-measured under v3 (Welch-median 16 s,
`matched_filter_replicator`): R1 median heavy GWTC-1 ≥ 0.65 AND within ±0.10 of
0.902; R2 median GWTC-3 (n = 6) ≥ 0.408; R3 median |R_v3 − R_confirm| ≤ 0.10.

## Registry action (locked, conditional — the v2 lesson)

- If ANY of X0-X4 fails: the instrument is invalid, X5 receives **no verdict**,
  NO registry action; preserved negative in paper + memory.
- If X0-X4 all pass: append one reproduction attempt to
  exp_83871cc6eeadf4d1b80ec4d8 with `method_id="welch_median_16s_chi2_veto_v3"`,
  outcome CONFIRMED iff X5 passes, FAILED otherwise, receipt-bound.

One pass; no re-runs; no threshold edits. Paper §3.8 and memory updated either
way.
