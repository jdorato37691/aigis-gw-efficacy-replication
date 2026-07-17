# Referee review: the GW matched-filter program (Studies 1-6 + replications)

> **Historical review notice (2026-07-13):** this author-adjacent review is
> retained as provenance, not current clearance. Its earlier ladder-status and
> independence conclusions are superseded by the external audit response in
> `paper.md` and the fail-closed `gw_package_readiness.py` gate. The current
> human-readable status is **analysis-ready for external review (contract v3,
> Decision B); not externally published**.

**Reviewer:** Claude (Fable 5), frontier-reviewer lane · **Date:** 2026-07-12 ·
**Mandate:** operator directive ("do it yourself") for the charter §10 review of
[`paper.md`](paper.md) (this win's paper).

**Independence caveat (stated first, per Rule 21).** This reviewer is
author-adjacent: the same agent authored the studies under review in the same
session. This review therefore cannot substitute for an independent human domain
expert — it is structured to compensate by being verification-first: every check
below runs against receipts, the sha256-stamped source, or GWOSC (external), and
can fail. Where a check found a problem, the problem is reported and actioned,
not absorbed. An independent GW-literate human review remains recommended before
any external use of these results.

## Verification performed (all receipted)

- **V1 — Coincidence audit** (receipt
  `STUDY6_review_coincidence_audit_20260712T040807Z.json`): every Study-6
  measurement row keyed by template sha256 (excluding scrambled twins and other
  studies' receipts), per-row H1-L1 peak separation checked against a 15 ms
  analysis window: the approximately 10 ms physical H1-L1 light-travel bound
  plus a named 5 ms coalescence-time margin (LIGO E950018-02; LIGO P1900004).
  **Confirm pass: 13/13 within that window** (worst 8.8 ms) — the headline
  recoveries are physically anchored at the events. **Replication pass: 3/13
  non-coincident** (GW200128, GW200219, GW200220 — all GWTC-3 arm, all under the
  median-16s PSD). Coincidence-enforced re-analysis: R1 0.842 (unchanged), R2
  0.909 (n=3), R3 0.074 — all criteria still pass.
- **V2 — External catalog cross-check** (GWOSC eventapi, live): all 14 event GPS
  times match. All GWTC-3 published SNRs match exactly. The 7 GWTC-1 published
  SNRs match the **GWTC-1-confident catalog release exactly** and differ 3-6%
  from the newest per-event versions (GWTC-2.1-era re-analyses) that the
  single-event endpoint now serves.
- **V3 — Coefficient artifact:** payload digest re-verified on load; the 8-cell
  parse tripwire and 19x11 shape/label gates re-ran green in the replication
  pass; mapped α₅ ∈ [0.992, 0.993] sits inside the paper's stated [0.98, 1.04].
  Advisory (not evidence): sampled cells are consistent with this reviewer's
  training-set memory of the LALSuite PhenomD constants.
- **V4 — Integrity gates:** G6-a/b/c/d re-executed green before the replication
  measurements (stitcher identity exactly 0; amplitude regression bitwise 0).
- **V5 — Number trace:** every headline number in the paper (§3.6 table,
  abstract, replication paragraph) traced to
  `PHENOMD_phase_20260712T032158Z.json` /
  `PHENOMD_replication_20260712T033224Z.json` / the V1 audit receipt. One
  discrepancy found → F1.

## Findings

- **F1 (corrective — actioned).** The replication's anomaly documentation
  understated scope: the reproduction receipt and paper flagged ONE
  non-coincident row (GW200220) but the V1 audit finds THREE (adding GW200128 at
  94 ms and GW200219 at 185 ms). All three are in the GWTC-3 arm under the
  median PSD — at these quieter recoveries the robust estimator leaves the true
  peak sub-threshold in one detector within the ±0.1 s window. The locked
  criteria pass under full exclusion (R1 0.842 / R2 0.909 / R3 0.074), so the
  locked numerical criteria still pass, but this within-project reproduction
  does not establish independent experimental validation. Its reused-cohort
  statement rests on n=3 window-compatible events — materially weaker than the
  confirm pass's 6/6 window-compatible rows. Actioned: paper amended and the
  historical registry enum translated into human-readable scope.
- **F2 (hygiene).** Published-SNR denominators are catalog-release-dependent:
  the GWTC-1 values trace exactly to the GWTC-1-confident release, but the
  newest GWOSC event versions differ by 3-6%. Sensitivity: under the newest
  values the S1 median falls from 0.902 to roughly 0.87 — all conclusions
  unchanged. Action for future studies: pin the catalog release string in every
  registry row.
- **F3 (methodological, standing).** The network statistic is a quadrature sum
  of per-detector maxima found independently within ±0.1 s of catalog time;
  nothing enforces inter-detector coincidence. The V1 audit is the concrete
  demonstration of the failure mode (already ranked as a next lever in the
  paper). Until a coincidence-enforcing statistic lands, every future study
  should run the V1-style audit as a standard gate.
- **F4 (minor, no action).** In the arXiv LaTeX source, `eqn:mapping`'s second
  line lacks an explicit leading `+` before the (χ_PN−1) group (a line-break
  artifact); the implementation assumes summation. Corroborated by the α₅
  physical-range check and the empirical results; flagged for completeness.
- **F5 (adequacy of declared limitations).** The D1-D4 deviations,
  in-segment-PSD convention, H1+L1-only non-commensurability, and
  single-effective-spin approximation are declared in the paper and are
  appropriate for descriptive recovery-benchmark claims. The paper correctly
  does NOT claim parameter-estimation-grade accuracy anywhere.

## Verdict

The receipts support a within-project computational characterization and
preserve the preregistered negatives. They do not establish external readiness,
scientific independence, or physical validation. The package remains blocked on
an external waveform oracle, PSD robustness, an ensemble scramble null,
posterior propagation, Study-3 coincidence evidence, and a fresh untouched
holdout. The historical registry enums are machine metadata rather than the
human claim state.

**Charter §10 status:** author-adjacent frontier review completed; independent
human expert review and the package readiness gates remain open before external
publication.

## Addendum — follow-up gates executed (2026-07-16/17)

All six blockers named in the verdict above have since been executed as
artifact-bound gates (`verification/*.json`, validated fail-closed by
`scripts/research/gw_package_readiness.py`). Outcomes, each verified against the
artifact:

- **PSD robustness — pass.** Ten GWTC-1 events under four locked regimes
  (on-source mean-4s, off-source mean-4s, many-average median-4s, glitch-gated
  mean-4s): Spearman ρ(M, R) −0.891 / −0.830 / −0.891 / −0.891, n = 10 each;
  positive control reproduces the Study-1 receipt to 0.0005; the
  GW170817-derived glitch gate never fired on any event. (`psd_robustness.json`,
  2026-07-16)
- **Ensemble scramble null — pass.** At least 100 seeded scrambles per event
  across 12 events; 10 events at one-sided empirical p = 0.0099 with median
  margin 0.159 over the scramble median (locked: ≥ 10 events at p ≤ 0.05, median
  margin ≥ 0.10). (`phase_scramble_ensemble.json`, 2026-07-13)
- **Study-3 coincidence — pass.** All 15 measured rows audited hash-bound; 10
  within the 15 ms analysis window; recomputed on the included rows: ρ = −0.927
  (p = 1.1×10⁻⁴), median |R − R̂| = 0.076 — both locked criteria hold.
  (`study3_coincidence.json`, 2026-07-13)
- **Posterior propagation — pass under contract v3 (trend-only), curve fail
  preserved.** 100 joint cohort draws over the 15 Study-3 events: the trend
  criterion (ρ ≤ −0.5) is preserved in 98/100 draws (ρ percentiles [−0.888,
  −0.734, −0.530]); the prediction criterion (median |R − R̂| ≤ 0.15) in only
  54/100 (percentiles [0.079, 0.143, 0.210]) — fails the ≥ 90% rule. The mass
  trend is posterior-robust; the point-prediction curve is not. Under contract
  v3 (Decision B) the gate PASSES on the trend criterion alone and preserves the
  O2 curve fail as a withdrawn-claim record carrying its original fail verdict.
  (`posterior_uncertainty.json`, 2026-07-16)
- **External waveform oracle — pass, through a preserved fail-diagnosis-
  completion arc.** The first gate run (2026-07-16) failed honestly:
  LALSimulation IMRPhenomD over the preregistered 13-point grid gave median
  match 0.98864, minimum 0.91751 at (55+48 M☉, χ = 0.6) against the 0.99 floor,
  the merger-band RMS phase residual growing monotonically with aligned spin —
  tracking the then-declared 1.5PN-only / single-χ_eff deviations — plus a
  discrete-IFFT time-alignment quantization costing one non-spinning point
  (0.9745 at 50+45 M☉). That fail is preserved (receipt
  `LAL_oracle_20260716T113628Z.json`, commit 2203e431a) and drove the
  preregistered spin-sector completion retry
  (`2026-07-16-phenomd-oracle-spin-sector-retry.md`, committed before the run;
  grid, floor, and validator frozen): the full two-spin 3.5PN aligned-spin
  phasing transcribed from the same sha256-stamped source behind a four-leg
  tripwire (worst 4.0×10⁻¹³ rad), the sourced Paper-1 remnant fits on the oracle
  path, and a preregistered sub-bin evaluation of the identical locked match.
  Result (2026-07-17): the completed transcription alone moves the
  discrete-metric grid to min 0.97451 / median 0.99791 (inspiral residuals
  collapse 0.15–0.47 → 0.001–0.009 rad; the χ-monotone trend is gone), and under
  the sub-bin evaluation **min 0.99997 / median 0.99999 — gate PASS**, the
  residual ~3×10⁻⁵ consistent with the narrowed D2 fit-vs-table QNM conversion.
  (`phenomd_external_oracle.json`, regenerated 2026-07-17; receipt
  `LAL_oracle_20260717T001009Z.json`)
- **Fresh untouched holdout — pass, outcome `confirmed`.** Ten
  GWTC-2.1-confident O3a events, deterministically preregistered and fully
  disjoint from the 31-event development manifest; chronology validator-verified
  (template locked 2026-07-14, cohort frozen and evaluated once 2026-07-16).
  Seven measured, three `data_unavailable` by mechanical rule: ρ = −0.964 (p =
  4.8×10⁻⁴), median |R − R̂| = 0.129 ≤ 0.15. (`fresh_untouched_holdout.json`,
  2026-07-16)

Six pass under contract v3. The posterior gate initially returned a preserved
honest fail (O1 trend in 98/100 draws; O2 curve in only 54/100 against the 90%
rule); the operator has since authorized **contract v3** (PI-approved
2026-07-16, `OPERATOR-DECISIONS.md` Decision B; the v3 authorization stamp
references the Decision B brief, commit `13eb7b848`), which gates the posterior
PASS on the O1 trend criterion alone — matching the paper's revised
point-estimate-conditional claim. The withdrawn O2 posterior-robust-curve
criterion is not deleted: `gw_evidence_controls.summarize_posterior_uncertainty`
still computes it and reports it as a `withdrawn_claim_record` carrying its
original `fail` verdict (54/100) and the v3 authorization stamp. All six local
gates now pass, so `gw_package_readiness.py` reports
`analysis_ready_for_external_review`; the package is still **not externally
published** — external publication stays hard-blocked on an external immutable
trust anchor (Decision C, not executed here). The remaining scope correction to
the paper's claims — the prediction curve is a point-estimate tool, not a
posterior-robust one — stands in `paper.md` (§3.4, §3.12); the oracle's initial
fail is preserved as the diagnosis in a fail → completion → pass arc (§3.6).
Contract-vs-claim note (resolved): the posterior gate previously tested the
_original_ posterior-robust-curve criterion, broader than the paper's revised
claim; the operator resolved the mismatch by authorizing contract v3, preserving
the original criterion and its fail verdict as the withdrawn-claim record rather
than deleting it.

Condition-1 note (2026-07-16, updated 2026-07-17 after addendum 2): the
literature-positioning review (`literature-positioning.md`, three passes, policy
"err toward finding prior art") is folded into the paper. The mass trend is
presented as a quantified, cross-catalog, per-event re-measurement of an
anticipated relationship (Flanagan & Hughes 1998 derived the decline in the
exact regressor; Buonanno et al. 2009 is the search-design doctrine; the
GWTC-1/2/3/4 TGR papers tabulate per-event inspiral/post-inspiral SNRs
catalog-wide — GWTC-4.0 TGR I, arXiv:2603.19019, now the authoritative O4-era
source — with the explicit differencing of R stated in-text: same-waveform
low-frequency restriction vs independent inspiral-only template, and no recovery
fraction, R-vs-mass correlation, or preregistered holdout transfer computed
there); the heavy-event mechanism as the textbook IMR energy budget verified
event-by-event; the GW151226 result as single-term attribution under locked
differentials only; and the methodology claim narrowed to the mechanized
integration, "to our knowledge" only, with the output-order vs
protocol-stage-order distinction stated and PRIMAD-LIGO (arXiv:1904.05211) cited
as the nearest prior methodological neighbor. The surviving narrow claims held
against addendum 2's final residual-venue pass (GWTC-4-era TGR,
theses/DCC/proceedings, methodology venues); residual risk assessed LOW for the
measurement claims, LOW-MODERATE for the methodology claim; honestly unswept:
non-English, paywalled-only, LVK-internal DCC, post-July-2026. An erratum guard
was verified: arXiv:1004.0961 is McWilliams, Kelly & Baker (2010) — the sweep
ledger's "Reisswig et al." misattribution appears nowhere in the paper package.
Paper §8 carries the full citation set and the verbatim-defensible novelty list.
