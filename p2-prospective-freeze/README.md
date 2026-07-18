# P2 — prospective freeze: an inspiral-recovery prediction for GWOSC O4c

**This is a scientific pre-commitment, frozen and publicly timestamped before its
measuring data exists.** It predicts the inspiral-only matched-filter recovery
fraction `R` for the LIGO-Virgo-KAGRA **O4c** bulk release (planned December
2026), as a frozen function of source parameters plus pre-committed uncertainty
bands and a mechanical grading rule that fires on release day with zero
discretion. `belief_moved=false`.

Posted by the study's automated research system on behalf of the maintainer
(jdorato37691); the tag is signed with the maintainer's SSH key. Companion to the
retrospective replication bundle in this repository (tag
`aigis-gw-efficacy-20260717-r1`).

## The prediction (full detail in `P2_FREEZE_MANIFEST.md`)

For each O4c BBH event, `R` is predicted by the frozen zero-parameter mechanism
`r_mech(M_det)` (`r_predictor.py`) within a mass-dependent 90% band:

| Regime | detector-frame total mass M_det | 90% band |
| ------ | ------------------------------- | -------- |
| light (f_ISCO >= 215 Hz) | <= 20.45 M_sun | clip(r_mech + [-0.289, -0.058], 0, 1) |
| intermediate | 20.45 - 146.57 M_sun | clip(r_mech + [-0.189, +0.245], 0, 1) |
| heavy / ISCO-below-band (f_ISCO <= 30 Hz) | >= 146.57 M_sun | [0, 0.05] (sharp R -> 0 sub-claim) |

The bands are calibrated on retrospective, development-adjacent residuals
(Study-3 OOS + O3a holdout + O4a/O4b validation; the 48-row pool and its source
receipts are in `residual_receipts/`) and tested **prospectively** on O4c. This
is stated plainly, not hidden.

## Why you can trust the freeze wasn't fit to pass

- **Freeze-before-compute is enforced in git.** The band-derivation *procedure*
  was committed (`2026-07-17-p2-prospective-freeze.md`, sha256 `2057b6c6...`)
  before any band number was computed; the procedure text contains no band
  numbers. Every bound artifact's sha256 is listed in `P2_FREEZE_MANIFEST.md`
  and combined into `P2_FREEZE_SHA256 =
  19e534508a7e2c646673f2069cf0f78db747aac927bfd2a3efa26643b6e8dc99`, which the
  signed tag binds.
- **The bands are the honest residual quantiles**, recomputable from
  `residual_receipts/` — an independent adversarial review reproduced them to
  1e-6 (`P2_REVIEW_NOTES.md`).
- **The test has power.** A null/biased predictor is rejected: constant R=0.5 ->
  coverage 0.35 -> FALSIFIED; the honestly-disclosed power vs mild
  miscalibration is ~0.4 (binomial table in the prereg). This is a modestly-
  powered but real test, not theater.

## Verify the signature (offline)

```bash
git -c gpg.ssh.allowedSignersFile=../allowed_signers verify-tag aigis-gw-p2-freeze-20260717
# expect: Good "git" signature for jdorato37691 with ED25519 key SHA256:L9aqePBZg0bj/+Qh03KQQLmkrhR0bGmsKv1FN8JbTBM
```

## How to falsify this on release day (no permission needed)

When O4c is public: enumerate its cohort by the frozen rule (BBH m2_source>=3,
FAR<1/yr, network SNR>=12, strain available, GPS-sorted, disjoint from the frozen
development manifest), measure `R` with the frozen pipeline (the replication
bundle in this repo, `template_commit_sha256 4c43f311...`), and compute coverage
of the frozen bands. **CONFIRMED if coverage >= 0.80; FALSIFIED if < 0.70**
(INCONCLUSIVE between, n>=8 required); plus: any ISCO-below-band O4c event that
recovers R > 0.05 falsifies the sharp sub-claim. `p2_release_day_grade.py`
mechanizes this. A falsified outcome is a first-class result and will be posted
here beside the prediction.

Nothing in the grade depends on the maintainer's own systems — only O4c public
strain, O4c published masses, and these frozen artifacts.
