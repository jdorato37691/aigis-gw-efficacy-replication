# Win: GW matched-filter inspiral-template efficacy

**Result.** A preregistered computational characterization of inspiral-only
matched-filter recovery across the GWTC catalogs. Study 3 is the one clean
out-of-sample test. Later GWTC-3 studies reuse that cohort for development.
Three published detections were reproduced within one project, a heavy-event
template deficit was narrowed with sourced PhenomD phase coefficients, the
chi-squared veto passed its declared instrument controls, and every negative was
preserved.

**Human-readable status:** **major revision open; not externally ready.** Some
historical registry rows retain the machine enum `experimentally_validated`, but
the supporting reruns share data, code, template machinery, project, and
development history. They are within-project computational reproductions, not
independent experimental validation. External human expert review remains
recommended (charter §10).

The read-only readiness audit makes open work fail closed:

```bash
uv run python scripts/research/gw_package_readiness.py
uv run python scripts/research/gw_package_readiness.py --require-analysis-ready-for-external-review
uv run python scripts/research/gw_package_readiness.py --require-external-ready
```

The analysis-readiness command remains nonzero until all six machine-readable
follow-up artifacts pass: an external LALSimulation/PyCBC oracle grid, PSD
robustness, 100+ phase scrambles per event, posterior propagation, Study-3
coincidence, and a genuinely fresh holdout. Even then, the result is only
`analysis_ready_for_external_review`. The external-readiness command remains
nonzero: this local audit implements no external-attestation validator, and
same-operator local hashes and git history do not clear publication.

## Contents

- [`paper.md`](paper.md) — the internal preprint (Studies 1-8 + replications).
- [`referee-review.md`](referee-review.md) — historical author-adjacent review;
  its earlier status conclusion is superseded by the package-level readiness
  gate and the external audit response in the paper.

## Supporting artifacts (elsewhere in the repo)

- Preregistrations: `docs/research/preregistrations/2026-07-12-*.md`
  (GW150914/GW151226/GW170817 matched-filter, GWTC-1 TaylorF2/aligned-spin,
  GWTC-3 OOS, PhenomD sourced phase, IMR ansatz, chi2 veto v3, coincident
  network, protocol v4/v5, Virgo extension).
- Pipeline + studies: `scripts/research/phenomd_*.py`, `chi2_*_study.py`,
  `coincident_*.py`, `sourced_physics*.py`, `virgo_network_study.py`.
- Program charter: `docs/research/CHARTER.md`.
