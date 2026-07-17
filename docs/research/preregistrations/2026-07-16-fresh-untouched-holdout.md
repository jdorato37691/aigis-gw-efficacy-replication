# Preregistration: fresh untouched holdout of the mass-trend claim (GWTC-2.1 / O3a)

**Program:** CHARTER G3 track, final verification artifact ·
**Preregistered:** 2026-07-16 (committed BEFORE any holdout strain is fetched or
filtered) · **Schema target:** `aigis.gw.fresh_holdout.v1`
(`validate_fresh_holdout_artifact`, `scripts/research/gw_evidence_controls.py`).

**Question.** Does the paper's central, preregistered **mass-trend claim** — that
inspiral-only template recovery fraction R declines with detector-frame total
mass M_det — hold on gravitational-wave events that played **NO role whatsoever**
in forming, testing, or replicating the claim, when scored by the **frozen
Study-1/2/3 pipeline**?

This is the strongest replication form the program has attempted. Study 3
(`2026-07-12-gwtc3-out-of-sample.md`) already tested transfer to *unseen* O3b
(GWTC-3) events, but those O3b events were subsequently reused across Studies
4-6 and both coincidence audits, so they are development-touched. This holdout
draws from a **different observing run and a different catalog release entirely**
(O3a / GWTC-2.1-confident), none of whose events appear anywhere in the
development record. Outcome may honestly be `confirmed`, `falsified`, or
`inconclusive`; all three are first-class and the artifact registers regardless.
`belief_moved=false` (this is a verification artifact, not a belief-update path).

## 1. Development manifest (exhaustive, enumerated pre-freeze)

Every GW event named anywhere in the development record is contaminated and
excluded from the holdout. A `grep -roE "GW[0-9]{6}(_[0-9]{6})?"` sweep of
`scripts/research/`, `docs/research/` (paper.md, referee-review.md,
verification/*, preregistrations/*), and `~/.aigis/research/gw_replication/`
receipts returned 42 raw strings resolving to **31 physically distinct events**
(short-form references such as `GW191109` are truncations of the full-form ID
`GW191109_010717`):

- **GWTC-1 / O1-O2 in-sample (11):** GW150914, GW151012, GW151226, GW170104,
  GW170608, GW170729, GW170809, GW170814, GW170817, GW170818, GW170823.
- **GWTC-3 / O3b Study-3 OOS + Studies 4-6 reuse + coincidence audits (20):**
  GW191109_010717, GW191126_115259, GW191127_050227, GW191129_134029,
  GW191204_110529, GW191204_171526, GW191215_223052, GW191216_213338,
  GW191222_033537, GW191230_180458, GW200112_155838, GW200128_022011,
  GW200202_154313, GW200219_094415, GW200220_124850, GW200224_222234,
  GW200225_060421, GW200302_015811, GW200311_115853, GW200316_215756.

No O3a (GW190xxxxx) event appears in the development record. The holdout cohort
is drawn exclusively from O3a and screened against this 31-event manifest by base
event id (version suffixes such as `-v4` stripped). GWTC-2.1-confident re-serves
the original GWTC-1 events (GW150914-v4, GW170814-v4, GW170608-v4, GW170104-v3,
GW170809-v2); the manifest screen deterministically removes them.

## 2. Frozen pipeline (locked; identical physics to Studies 1-3)

The holdout runs the **frozen Study-1/2/3 matched-filter pipeline** with **no
new physics**: spin-extended TaylorF2 3.5PN templates at catalog masses and
`chi_eff`, H1+L1 only, 32 s on-source segment, band [30, 2048] Hz, Welch mean 4 s
PSD, per-event off-source validity control (off-source network max < 8, else no
verdict for that event), mechanical off-source fallback chain, O3 availability
rule (an event lacking NaN-free H1+L1 data after the fallback chain is
`data_unavailable`, excluded, documented — exclusions do not count against the
predictions). The evaluation engine reuses
`scripts/research/gwtc3_oos_study.py` (`_run_event`, `r_hat`) and
`gwtc1_taylorf2_sweep._load_instrument()` / `taylorf2` / `matched_filter_gw150914`
unchanged.

- **Governing pipeline commit:** `79d3c2c5ad1caec84edfa4f261afb7b8e38cb1d4`
  (2026-07-14T20:20:13-04:00) — the most recent commit touching any governing
  file. This is `template_locked_at`.
- **template_commit_sha256:**
  `4c43f31143db2a98cf53c19d8fce6f062d18c5c920cd6c4c4ca5d54a62340446` =
  `sha256` over the concatenated committed bytes of the four governing files in
  filename-sorted order: `gwtc1_taylorf2_sweep.py`, `gwtc3_oos_study.py`,
  `matched_filter_gw150914.py`, `taylorf2.py`.

## 3. Locked predictor R-hat(M_det) (GWTC-1 in-sample ONLY)

The frozen predictor is the binned medians of Study 2's GWTC-1 spin-template
recoveries, transcribed unchanged from Study 3 (`gwtc3_oos_study.r_hat`), derived
from in-sample data only and therefore development-naive with respect to this
cohort:

| M_det bin | R-hat |
| --------- | ----- |
| < 30      | 0.849 |
| 30-70     | 0.554 |
| 70-100    | 0.428 |
| >= 100    | 0.210 |

## 4. Deterministic cohort selection rule (locked BEFORE any strain fetch)

`catalog_release = "GWTC-2.1-confident"` (O3a). From that release, an event is
**eligible** iff ALL of:

1. **BBH:** `mass_2_source >= 3.0` M_sun (excludes BNS/NSBH-ambiguous mass-gap
   events; identical to the Study-3 BBH cut).
2. **Confident astrophysical origin:** `far < 1.0` per year (the standard LVK
   confident-detection false-alarm-rate threshold).
3. **Recovery power:** published `network_matched_filter_snr >= 12.0`. Justified
   a priori for testability: comfortably above the SNR ~ 8 detection floor so the
   H1+L1 matched filter has genuine recovery power and R is a real measurement
   rather than a noise-dominated ratio (Study 3 documented that quieter SNR ~ 8
   recoveries leave the true peak sub-threshold in one detector). This threshold
   is chosen on physical grounds, not by inspecting recoveries.
4. **Development-naive:** base event id (version suffix stripped) NOT in the
   Section-1 development manifest.

**Ordering (deterministic):** sort eligible events by `network_matched_filter_snr`
**descending**, tie-broken by base event id **ascending**. **Cohort = the first
N = 10** (the loudest ten). Rationale for N = 10: loudest events give the pipeline
maximal recovery power (a trend failure is then attributable to physics, not
noise), the SNR-loudest O3a BBH span the full mass range (maximizing
rank-correlation power for a monotone-trend test without biasing its sign), and
10 leaves margin above the contract minimum of 5 measured events against
mechanical `data_unavailable` / off-source-invalid exclusions, while bounding
strain-fetch compute to a single background run. If fewer than 10 but at least 5
eligible events exist, the cohort is all of them. If fewer than 5 eligible events
exist under this rule, the study halts and reports `NEEDS_CONTEXT` with the pool
census; the rule is NOT loosened post hoc.

A metadata-only census (names, network SNR, FAR, `mass_2_source` — catalog
selection metadata, not recovery outcomes) confirmed **>= 5 eligible events exist**
before this preregistration was committed (14 development-naive O3a BBH events at
network SNR >= 12, FAR < 1/yr). The specific frozen cohort is enumerated
mechanically at the freeze step AFTER this file is committed; no holdout strain
and no recovery statistic is computed before then.

## 5. Statistic and locked grading criteria (transcribed from the paper's claim)

For each measured event: R = recovered network statistic / published network SNR;
M_det = (m1_source + m2_source) x (1 + z) from the catalog; R-hat(M_det) per
Section 3. The two locked predictions are transcribed verbatim from the paper's
central claim (Study 1 in-sample P3/H2: rho <= -0.6; Study 3 out-of-sample O1/O2,
`2026-07-12-gwtc3-out-of-sample.md`), using the softer out-of-sample O1 threshold
because O3a events span a different, in-places narrower detector-sensitivity era:

- **O1 (the mass trend generalizes):** Spearman `rho(M_det, R) <= -0.5` across
  measured holdout events.
- **O2 (the frozen curve predicts):** `median |R - R-hat(M_det)| <= 0.15` across
  measured holdout events.

**Outcome mapping (locked; deterministic):**

- **`confirmed`** iff `n_measured >= 5` AND O1 passes AND O2 passes — the central
  mass-trend claim AND the frozen GWTC-1-derived curve both generalize to
  development-naive events.
- **`falsified`** iff `n_measured >= 5` AND O1 fails (`rho > -0.5`) — the mass
  trend did NOT generalize; it was an artifact of the in-sample + O3b cohorts.
- **`inconclusive`** iff `n_measured < 5` (holdout under-powered by mechanical
  exclusions), OR O1 passes but O2 fails (`rho <= -0.5` AND
  `median|R - R-hat| > 0.15`) — the trend direction transfers but the absolute
  recovery curve does not transfer across observing eras (instrument-era
  dependence; central claim directionally supported, quantitative curve not).

## 6. Stopping rule (locked)

One pass over the frozen N-event cohort, checkpointed after every event
(resumable across process restarts without re-measuring). No re-runs, no
parameter changes, no threshold changes after results. The study registers its
honest outcome regardless.

## 7. Chronology (validator-enforced)

`template_locked_at` (governing pipeline commit, 2026-07-14) <= `cohort_frozen_at`
(freeze receipt, 2026-07-16, after this preregistration is committed) <
`evaluation_started_at` < `evaluation_completed_at`. The freeze receipt,
evaluation receipt, and the frozen-pipeline content hash are each bound into the
final artifact by sha256.
