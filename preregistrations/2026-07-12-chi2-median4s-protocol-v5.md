# Preregistration: protocol v5 — the v4 gate partition, corrected

**Program:** CHARTER G3 track, protocol iteration 5 · **Preregistered:**
2026-07-12 (committed before the re-evaluation runs) **Motivating defect
(protocol v4, receipt `CHI2_v4_20260712T101908Z.json`):** Y1 (no clean-event
veto) was locked over ALL 13 rows while Y2 (glitch suppression) required the
GW200220 row suppressed — on that one row the two gates demand opposite
behavior, and the instrument was convicted by Y1 (ratio 0.347) for doing exactly
what Y2 required. Every other row passed Y1 at ≥ 0.914. This is a drafting bug
in the gate definitions, not an instrument or measurement defect; the locked
clause correctly produced `instrument_invalid_no_verdict` and that receipt
stands.

## The correction (locked)

Complementary gates must PARTITION the sample:

- **Y1′ (no clean-event veto):** applies to all rows EXCEPT the Y2-designated
  glitch event (GW200220_124850, designated from the committed V1
  coincidence-audit receipt, not post hoc). Threshold unchanged (≥ 0.75 ×
  same-config raw).
- **Y2 (glitch suppression):** unchanged, applies to the designated event.
- **Y0 oracles, Y3 known-bad, Y5 replication criteria:** unchanged in every
  respect.

## What runs (locked)

NO new data collection. The v4 measurements are deterministic (cached strain,
fixed seeds, fixed code — modules unchanged since the v4 receipt); v5
re-evaluates the v4 receipt's rows (integrity-checked via its embedded
`receipt_sha256`) under the corrected partition. The in-config oracle (Y0a: χ²_r
= 0.689, ρ̂/ρ = 1.0) already validates the Y5 assay for this config.

## Registry action (locked, conditional)

- Y0, Y1′, Y2, Y3 all pass → the instrument is valid; append one reproduction
  attempt to exp_83871cc6eeadf4d1b80ec4d8 with
  `method_id="welch_median_4s_chi2_veto_v5"`, outcome CONFIRMED iff Y5 passes,
  FAILED otherwise, receipt-bound. This would be Study 6's glitch-immune
  replication arm.
- Any validity gate failing under the corrected partition → no registry action,
  preserved negative.

One pass; no threshold edits; paper §3.9 and memory updated either way.
