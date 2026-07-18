## Adversarial review + reproducibility closure (2026-07-17)

A fresh adversary ran 9 attacks against this freeze (freeze-before-compute
ordering, physics-fixed boundaries, honest-quantile bands, grader discretion,
**power to falsify a wrong mechanism**, R->0 firability, Rule-19 authored-state
independence, manifest binding, self-fix verification). **VERDICT: HOLDS** —
every computational check reproduced byte-for-byte; the git-enforced ordering is
airtight (procedure `8e43efdb5` is a strict ancestor of the bands and contains
no band numbers); the [5,95] residual quantiles were independently recomputed to
1e-6; and the decisive power test confirmed a null/biased predictor is REJECTED
(constant R=0.5 -> coverage 0.35 FALSIFIED; biased mechanism 0.10-0.44
FALSIFIED), while the honest development-residual spread is not inflated. The
prereg's own binomial power table (~0.4 power vs a mildly-miscalibrated p=0.70
predictor) is the honestly-disclosed limitation, not a hidden one;
discriminating power lives additionally in the light-regime band and the heavy
R->0 sub-claim.

Soft findings closed:

- **Band-derivation reproducibility (finding 1):** the three residual receipts
  (Study-3 OOS, O3a holdout, P1.5 O4) are now bundled hash-verified at
  `../papers/gw-inspiral-template-efficacy/verification/p2_residual_receipts/`
  (commit `5aaef178d`) so the derivation reproduces from the public repo alone.
- **Mislabeled commit (finding 2):** the band artifacts were first added under a
  concurrent autonomy commit mislabeled `d99016ec8 "ChronoSim round 3"` (the
  documented shared-tree autonomy-committer hazard). Chronologically after the
  procedure freeze and hash-consistent — integrity intact; annotated here so a
  release-day auditor of git history is not confused.

**STATUS: FROZEN and adversarially cleared. Staged to the edge of the operator
push** (signed tag `aigis-gw-p2-freeze-20260717`, command in
`../papers/gw-inspiral-template-efficacy/verification/P2_FREEZE_MANIFEST.md`).
The external push spends operator identity and is operator-gated. On O4c release
(~Dec 2026) the frozen grader fires with no discretion.
