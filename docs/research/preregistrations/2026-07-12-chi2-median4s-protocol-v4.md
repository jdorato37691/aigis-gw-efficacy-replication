# Preregistration: chi2-vetoed replication protocol (v4, median-4s PSD)

**Program:** CHARTER G3 track, instrument/protocol iteration 4 ·
**Preregistered:** 2026-07-12 (committed before any on-source v4 run)
**Motivating results:** instrument v3's χ² veto passed every validity gate
(template oracle χ²_r = 0.65 / ρ̂ untouched; blip crushed; 39σ transient
annihilated) but its re-measure assay was invalidated by an oracle: under the
Welch-median-16s PSD (~3 averages in 32 s) a PERFECT signal scores χ²_r ≈ 4.0
and loses 44% of ρ̂ (receipt `CHI2_v3_oracle_20260712T043222Z.json`). The fix is
a robust-AND-averaged estimator: **Welch median, 4 s segments** (~15 averages in
the same window; scipy applies the median bias correction).

## The v4 protocol (locked)

Identical to v3's statistic (χ² p = 16, dof = 30, re-weighted SNR, coincident 10
ms pairing, no floor — all module code unchanged) with ONE change: the
replication PSD is **median-4s** instead of median-16s. This remains a distinct
re-analysis relative to the Study-6 confirm pass (mean-4s raw matched filter):
different PSD estimator, different statistic (χ²-vetoed), distinct executor
identity.

## Instrument-validity gates (Y0-Y3 — ALL required before any registry

## action; every oracle runs UNDER THE EXACT v4 CONFIG — the v3 lesson)

- **Y0a (in-config template oracle):** exact template injected into real
  off-source noise at calibrated ρ = 20, median-4s PSD → χ²_r at the peak ∈
  [0.3, 3.0] AND ρ̂/ρ ≥ **0.90**. If a perfect signal cannot pass, no on-source
  run happens.
- **Y0b (in-config blip oracle):** 1 ms blip at ρ ≥ 15, median-4s PSD → χ²_r ≥ 5
  AND ρ̂/ρ < 0.6.
- **Y1 (no clean-event veto, in-config):** for all 13 rows, v4 ≥ **0.75** × the
  same-config raw coincident maximum (v1-inline, median-4s).
- **Y2 (glitch suppression):** on GW200220's on-source window under median-4s:
  if the H1 raw maximum exceeds 15 (the transient shows in this config), then H1
  ρ̂ < **0.5** × raw; in all cases the v4 network < **15**.
- **Y3 (known-bad):** off-source v4 < **8** on all 13 events.

## Preregistered replication criteria (Y5)

All 13 rows measured under the v4 protocol (`matched_filter_replicator`): R1
median heavy GWTC-1 ≥ 0.65 AND within ±0.10 of the confirm 0.902; R2 median
GWTC-3 (n = 6) ≥ 0.408; R3 median |R_v4 − R_confirm| ≤ 0.10.

## Registry action (locked, conditional)

- Any Y0-Y3 failure → instrument invalid for this config, Y5 gets **no
  verdict**, NO registry action, preserved negative.
- Y0-Y3 all pass → append one reproduction attempt to
  exp_83871cc6eeadf4d1b80ec4d8, `method_id="welch_median_4s_chi2_veto_v4"`,
  outcome CONFIRMED iff Y5 passes, FAILED otherwise (now meaningful — the assay
  is oracle-validated in-config), receipt-bound.

One pass; no re-runs; no threshold edits. Paper §3.9 and memory updated either
way.
