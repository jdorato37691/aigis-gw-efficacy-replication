# GW package follow-up evidence

This directory is intentionally empty of result JSON until the corresponding
analysis is actually run. `scripts/research/gw_package_readiness.py` is
read-only and fail-closed: prose, package availability, or a historical registry
enum cannot substitute for one of these artifacts. Every artifact must be a JSON
object with no duplicate key at any nesting level.

Required files:

- `phenomd_external_oracle.json`: schema `aigis.gw.phenomd_oracle.v1`, an
  independent LALSimulation or PyCBC implementation, at least 12 preregistered
  unique parameter-grid matches in `exact_phenomd` mode, a declared match floor
  no lower than the code-owned 0.99 floor, and an environment hash.
- `psd_robustness.json`: schema `aigis.gw.psd_robustness.v1`, the same events
  under on-source mean-4s, off-source mean-4s, on-source many-average median-4s,
  and gated on-source mean-4s PSD regimes, with a strain-manifest hash. Each
  required configuration needs the same unique event set, at least 10 events,
  consistent masses, and finite Spearman statistics. A structurally complete
  result that loses the locked ρ ≤ −0.5 mass trend is an honest `fail`, not a
  readiness pass.
- `phase_scramble_ensemble.json`: schema `aigis.gw.phase_scramble_ensemble.v1`,
  template hash, and at least 100 uniquely identified scramble seeds and
  recoveries for each of at least seven unique events. The code recomputes the
  median ≥0.10 margin and empirical p≤0.05 event criteria; a complete negative
  remains `fail`.
- `posterior_uncertainty.json`: schema `aigis.gw.posterior_uncertainty.v1`,
  posterior-source hash, and at least 100 posterior-conditioned recovery reruns
  with the same unique joint draw IDs across at least 10 events. The validator
  recomputes the Study-3 Spearman (O1) and prediction-error (O2) criteria per
  joint draw. **Contract v3** (PI-approved 2026-07-16, `OPERATOR-DECISIONS.md`
  Decision B, commit `13eb7b848`): the gate PASSES on the O1 trend criterion
  alone — ρ ≤ −0.5 preserved in ≥ 90% of joint draws — matching the revised
  paper's point-estimate-conditional claim. The O2 posterior-robust-curve
  criterion (median |R − R̂| ≤ 0.15 preserved in ≥ 90% of draws) is not deleted:
  it stays computed and is reported in the gate output as a
  `withdrawn_claim_record` carrying its per-draw fraction, its original
  criterion, its original `fail` verdict, and `withdrawn: true` with the v3
  authorization stamp — the standing record of the withdrawn claim. A
  structurally incomplete artifact still `blocks`; an O1 trend failure still
  `fail`s.
- `study3_coincidence.json`: schema `aigis.gw.study3_coincidence.v1`, source
  receipt hash, and H1/L1 peak times and magnitudes for all 16 measured Study-3
  events. Every event must explicitly be included within the window or excluded
  outside it; the classified rows and recomputed result are hash-bound. The
  validator reports the 10 ms physical bound separately from the named 5 ms
  analysis margin, requires at least 10 included events, and recomputes the
  locked Study-3 correlation and prediction-error criteria.
- `fresh_untouched_holdout.json`: schema `aigis.gw.fresh_holdout.v1`, cohort and
  development manifest hashes computed from unique event lists, at least five
  holdout events disjoint from development, template/freeze/evaluation receipt
  hashes, and ordered template-lock, cohort-freeze, evaluation-start, and
  evaluation-complete timestamps. The result object is content-bound and may
  honestly be `confirmed`, `falsified`, or `inconclusive`.

Run:

```bash
uv run python scripts/research/gw_package_readiness.py
uv run python scripts/research/gw_package_readiness.py --require-analysis-ready-for-external-review
uv run python scripts/research/gw_package_readiness.py --require-external-ready
```

The first command is an honest status report and may exit zero while reporting
blocked work. The analysis-readiness command exits nonzero unless all six local
gates pass. That state means only `analysis_ready_for_external_review`.
`--require-external-ready` remains nonzero because same-operator local JSON
hashes and git history are not an externally controlled immutable attestation;
this local audit implements no external-attestation validator. External
publication therefore stays blocked. None of these commands runs an experiment,
touches the network, or mutates AIGIS state.
