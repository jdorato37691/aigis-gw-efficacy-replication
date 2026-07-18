# P2 band-derivation residual receipts

These three receipts are the **exact, hash-pinned** source of the 48-row
residual pool from which the P2 prospective prediction bands were mechanically
derived (`../p2_prospective_bands.json`, procedure frozen in
`docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md`). They are
copied here verbatim so an external reviewer can reproduce the **band
derivation** from the public repository alone — not only the release-day grade.

| Receipt | Cohort | Rows | sha256 (first 16) |
| ------- | ------ | ---- | ----------------- |
| `GWTC3_oos_20260712T023453Z.json` | Study-3 OOS | 15 | `273811476e55f361` |
| `FRESH_HOLDOUT_eval_20260716T232341Z.json` | O3a fresh holdout | 7 | `2d3b5248f7f25ba3` |
| `O4_EXPANDED_eval_20260717T214059Z.json` | P1.5 O4a+O4b | 26 | `1ec3358f973949f9` |

Each sha256 is embedded in `p2_prospective_bands.json` (`file_bytes_sha256`).
To reproduce: extract each receipt's per-event `(M_det, R_measured)` rows,
recompute `r_mech(M_det)` with the frozen predictor (`scripts/research/r_predictor.py`
@ commit `767d93bbd`), and take the frozen `[5, 95]` percentiles of
`(R_measured - r_mech)` within the three physics-fixed mass regimes. The
adversarial review of 2026-07-17 recomputed these to 1e-6.

The release-day grader (`scripts/research/p2_release_day_grade.py`) does NOT
read these files — they document how the *bands* were built; the *grade* uses
only O4c public data + the frozen artifacts.
