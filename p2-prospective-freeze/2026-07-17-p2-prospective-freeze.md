# Preregistration: P2 — the prospective freeze (O4c inspiral-recovery prediction)

**Program:** Prospective R-prediction program
(`2026-07-17-prospective-r-prediction-program-g0.md`), stage **P2 — the
prospective freeze**. · **Preregistered:** 2026-07-17 — this file freezes the
band-derivation PROCEDURE and the release-day grading rule **BEFORE any band
number is computed** (the band table is computed mechanically in a second commit
that references this one; see Chronology, Section 9). · **Lane:** sandbox;
`belief_moved=false` throughout. · **Decision owner:** operator (PI); the
external anchor (signed tag on the public replication repo) is operator-gated at
push time per the G0 charter.

## 0. What this document is and why the ordering matters

P2 registers a **prospective** scientific prediction: a frozen prediction of the
inspiral-only matched-filter recovery fraction `R` for the GWOSC **O4c** bulk
release (planned **December 2026**), frozen NOW, before that strain data exists.
Because O4c events have not been released, the prediction cannot be per-event
numbers; it is a **frozen function** plus **pre-committed uncertainty bands**
plus a **fully mechanical cohort rule** plus a **fully mechanical grading rule**
that fires on release day with zero discretion.

The single way to cheat a prospective prediction is to fit the uncertainty bands
so the eventual result looks good. This document makes that impossible by
**freezing the band-derivation procedure before any band is computed**. Every
choice below — the predictor, the residual pool, the regime boundaries, the
percentile rule, the clip, the epsilon, the cohort rule, the pass/fail
thresholds — is fixed here as a mechanical recipe a third party could execute.
The band NUMBERS are then produced by `scripts/research/p2_prospective_bands.py`
running this recipe, committed in a **separate, later** commit that cites this
preregistration commit SHA. No band parameter is chosen after seeing coverage;
the predictor is never refit.

**The bands are calibrated on RETROSPECTIVE, development-adjacent residuals.**
This is stated plainly and is not hidden: the calibration residuals come from
already-measured cohorts (Study-3 OOS, the O3a fresh holdout, and the P1.5 O4a+O4b
expanded validation). That is exactly correct for the design — the bands encode
the mechanism's *demonstrated* error envelope, and are then tested
**prospectively** on O4c, a set that did not exist when this file was written and
that no development step has touched.

## 1. Predictor (FROZEN — never refit)

The point predictor is the zero-fitted-parameter band-floor mechanism
`r_mech(M_det)` (candidate 1 of the P1 family), frozen at
`scripts/research/r_predictor.py`, commit
`767d93bbd576d598f81e9b16c71bdff095c97f22` (`r_predictor.r_mech`, invoked via
`predict_r_mech(m1_source, m2_source, redshift)`):

```
r_mech(M_det) = sqrt( I(f_low, f_end(M_det)) / I(f_low, f_high) ),   clipped to [0, 1]
I(a, b)       = integral from a to b of  f^(-7/3) / S_n(f)  df
f_end(M_det)  = Schwarzschild f_ISCO of the detector-frame total mass, clamped to [f_low, f_high]
f_low = 30 Hz, f_high = 2048 Hz, S_n = Ajith (2011) aLIGO design analytic PSD
```

Zero fitted parameters; the chirp-mass prefactor cancels in the ratio, so
`r_mech` depends on the source only through `M_det = (m1 + m2)(1 + z)`.
`r_mech` is **not refit, rescaled, or re-tuned in P2**. The P1 grading already
established it as candidate 1 (holdout point error 0.026; O4 P1.5 point error
0.105, trend `rho = -0.958`, R -> 0 confirmed 5/5). P2 adds only an uncertainty
band around this frozen point predictor.

The twin-integral independent-check tripwire (`r_predictor.assert_twin`, linear
trapezoid vs. log-Simpson, tolerance `1e-3`) MUST pass over every graded mass
before any band or grade is emitted (both in the band computation and on release
day).

## 2. Residual pool for band calibration (named, enumerable, extracted from committed receipts)

The bands are calibrated on the union of the **already-measured**,
development-adjacent residuals `(R_measured - r_mech(M_det))` from the three prior
out-of-sample cohorts. This pool is **retrospective and development-adjacent by
construction** — that is correct and stated plainly; the bands calibrate on
demonstrated error and are then tested prospectively on O4c.

**Extraction rule (mechanical, third-party-reproducible from the receipts + the
frozen predictor):** from each receipt below, take every row in the top-level
`rows` array whose `status == "measured"`; from each such row read `m_det`
(detector-frame total mass) and `recovery_fraction` (the measured `R`). Compute
`r_mech = r_predictor.r_mech(m_det)` from the frozen predictor (Section 1), and
the calibration residual `resid = recovery_fraction - r_mech`. `r_mech` depends
on the source only through `M_det`, so evaluating it on the receipt's stored
`m_det` fully reproduces the predictor; the receipts store `m_det` rounded to
0.1 M_sun, which perturbs `r_mech` by `< 0.002` (verified; negligible against
band widths of order 0.1-0.5). The P1.5 receipt additionally stores a per-row
`r_mech` computed on the un-rounded catalog masses; the band script asserts
`|r_mech(m_det) - stored_r_mech| < 0.005` for all 26 P1.5 rows as a positive
control that the extraction reproduces the frozen pipeline (Rule 26).

**The three receipts (the binding calibration record):**

| Cohort | Receipt path | `receipt_sha256` | measured rows |
| ------ | ------------ | ---------------- | ------------- |
| Study-3 OOS (O3b / GWTC-3) | `~/.aigis/research/gw_replication/GWTC3_oos_20260712T023453Z.json`* | `e38e953f1d89bc280a2ef7c7562b665129ee0e5c6f40e8c01c048f24c70ced53` | 15 |
| O3a fresh holdout (GWTC-2.1) | `~/.aigis/research/gw_replication/FRESH_HOLDOUT_eval_20260716T232341Z.json` | (see receipt) | 7 |
| P1.5 O4a+O4b expanded validation | `~/.aigis/research/gw_replication/O4_EXPANDED_eval_20260717T214059Z.json` | `82738cf926a3e2d9693df3453f3779fdb3cf604918eabcd9ab2c6570d76da020` | 26 |

*(The Study-3 receipt file is written with a UTC filename stamp; its
`receipt_sha256` is the binding identifier and is asserted by the band script,
which locates the receipt by that hash, not by filename.)*

**Pool size: 15 + 7 + 26 = 48 measured `(M_det, R_measured, r_mech)` rows.** The
band script re-derives all 48 residuals from the receipts and stamps the exact
row list into the committed band table
(`verification/p2_prospective_bands.json`), so the calibration set is fully
enumerable and auditable.

## 3. Band model (mass-dependent, PRE-COMMITTED)

P1.5 proved the mechanism's error is mass-dependent (systematic low-mass
over-prediction; median `|R - r_mech|` of 0.227 / 0.105 / 0.071 / 0.000 across
light / mid / heavy / ISCO-below-band). The band is therefore **partitioned by
`M_det`** into three regimes whose boundaries are set by **ISCO-in-band
physics** — the position of the source's Schwarzschild ISCO frequency relative to
the analysis band — **NOT** by which split makes coverage pass.

`f_ISCO(M_det) = c / M_det` with `c = 1 / (6^1.5 * pi * G*Msun/c^3) = 4397.17 Hz*Msun`
(fixed geometry of the frozen predictor's ISCO definition, Section 1). Two
frozen physical frequencies define the boundaries:

- **`f_low = 30 Hz`** (band floor). `f_ISCO <= f_low` ⟺ `M_det >= c/30 = 146.57
  M_sun`. Here the inspiral track terminates at or below the band floor and
  `r_mech = 0` exactly — the **band-floor onset**, the mechanism's sharp
  `R -> 0` regime.
- **`f_ref = 215 Hz`** = the Ajith (2011) design-PSD reference frequency
  (`_PSD_F0` in the frozen `r_predictor.py`), which lies in the detector's most
  sensitive bucket (verified PSD minimum ~228 Hz; `f_ref` sits on the flat floor
  of the bucket). `f_ISCO >= f_ref` ⟺ `M_det <= c/215 = 20.45 M_sun`. Above this
  ISCO frequency the inspiral spans the whole sensitive band and `r_mech`
  saturates toward 1 (`r_mech(20.45) = 0.910`), which is exactly where the
  mechanism over-predicts because real template-faithfulness / PN-cutoff /
  whitening losses (not modeled by the floor) bite.

**Frozen regime boundaries (from the two frozen frequencies above):**

| Regime | Mechanical condition | `M_det` range (M_sun) | Physical meaning |
| ------ | -------------------- | --------------------- | ---------------- |
| **LIGHT** | `f_ISCO >= f_ref = 215 Hz` | `M_det <= 20.45` | ISCO above the sensitive bucket; `r_mech -> 1`; over-prediction regime |
| **INTERMEDIATE** | `f_low < f_ISCO < f_ref` | `20.45 < M_det < 146.57` | ISCO sweeps through the sensitive band; floor is a faithful model (the Studies 1-3 development range ~20-126) |
| **HEAVY (ISCO-below-band)** | `f_ISCO <= f_low = 30 Hz` | `M_det >= 146.57` | ISCO at/below band floor; `r_mech = 0` exactly; the sharp `R -> 0` sub-claim |

The boundary between LIGHT and INTERMEDIATE (`M_det = 20.45`) and between
INTERMEDIATE and HEAVY (`M_det = 146.57`) are computed from the two frozen
frequencies only. They are fixed in this preregistration and used verbatim by
the band script and the release-day grader.

**90% central prediction interval within LIGHT and INTERMEDIATE (empirical
percentile rule, PRE-COMMITTED):** within each of these two regimes, over that
regime's calibration residuals `resid = R_measured - r_mech(M_det)`, compute the
empirical 5th and 95th percentiles `q05`, `q95` (numpy `percentile`, default
linear interpolation; twin-checked against a manual sort-index computation that
must agree exactly). For an event with point prediction `r_mech`, the 90%
prediction interval is:

```
[ clip(r_mech + q05, 0, 1),  clip(r_mech + q95, 0, 1) ]
```

Coverage target: **90%** (the [5th, 95th] span). No free parameter is chosen
after seeing coverage; `q05`/`q95` are pure empirical percentiles of the frozen
residual pool, and the clip to `[0, 1]` is fixed.

**HEAVY regime = the `R -> 0` sharp sub-claim (frozen SEPARATELY):** for an event
with `f_ISCO <= f_low = 30 Hz` (the mechanical condition, i.e. `M_det >= 146.57`),
`r_mech = 0` and the prediction interval is the frozen

```
[ 0, epsilon ],   epsilon = 0.05
```

**`epsilon = 0.05` is frozen here.** Justification (not chosen from coverage):
across the pool, all 8 ISCO-below-band events (3 in the O3a holdout, 5 in P1.5)
recovered **exactly `R = 0.0`**; `epsilon = 0.05` allows a marginally-above-noise
recovery on a future ISCO-below-band event while keeping the sub-claim sharp and
well below the `r_hat` step-baseline's 0.210 floor that the mechanism beats on
these events. The HEAVY band is NOT an empirical percentile band (which would be
the degenerate `[0, 0]`); it is the pre-committed physical claim `R in [0, 0.05]`.

**Honesty note on band widths (pre-committed acknowledgement).** The LIGHT regime
is expected to be thinly populated in the calibration pool (few pool events have
`M_det <= 20.45`) and, per P1.5, to carry the widest residuals (low-mass
over-prediction). A wide LIGHT band is the mechanism telling the truth about its
own low-mass envelope; it will NOT be narrowed. The band script reports each
regime's `n` and residual rows honestly, whatever the widths.

## 4. O4c cohort rule (deterministic, frozen)

On release day the graded cohort is selected mechanically from the O4c catalog
release (the GWOSC eventapi catalog corresponding to the December 2026 O4c bulk
release), by exactly the P1.5 rule applied to O4c. An O4c event is **eligible**
iff ALL of:

1. **BBH:** `mass_2_source >= 3.0` M_sun.
2. **Confident astrophysical origin:** `far < 1.0` per year.
3. **Recovery power:** published `network_matched_filter_snr >= 12.0`.
4. **Strain available:** eventapi metadata resolves AND the frozen pipeline
   returns NaN-free H1+L1 on-source strain with a valid off-source control
   (Section 6 availability rule, identical to P1.5). Events failing this are
   `data_unavailable` / `instrument_invalid_no_verdict`, logged, and do **not**
   count against the prediction.
5. **Development-disjoint (the critical check):** neither the event's
   `commonName` nor its `GWYYMMDD` date prefix appears in the frozen **P2
   development manifest** — the union of (a) the 42-event P1.5 development
   exclusion set, (b) every event named in the three residual-pool receipts
   (Section 2: the Study-3, O3a-holdout, and P1.5 cohorts, including cap-dropped
   and excluded rows), and (c) all O4a/O4b events. O4c is disjoint from all of
   these by construction (new observing run, new GPS epoch, new names), but the
   mechanical check is stated and executed; any hit is removed and logged. The
   band script stamps this development manifest (and its sha256) into the
   committed band table so the grader loads the identical frozen set.

**Ordering + cap:** eligible events sorted by catalog **GPS ascending**,
tie-broken by `commonName` ascending (GPS is independent of mass and of `R`, so
the ordering cannot bias the graded outcome). Grade the first **`N_max = 40`**
eligible events — a **compute bound, not a result filter** (each event is one
~1-2 min on-source + off-source pipeline run; 40 bounds the release-day run to
~1-1.5 h, checkpointed per event). Every cap-dropped event is enumerated with
its published `M_det` and SNR. If O4c yields fewer than 40 eligible events, grade
all of them.

**Contract minimum:** if fewer than **8** events are `measured` after the
availability rule, the grade is **INCONCLUSIVE / NEEDS_CONTEXT** with the full
census — the cohort rule is NOT loosened post hoc.

## 5. Grading rule (mechanical, ZERO discretion — fires on release day)

On release day the frozen pipeline measures `R = recovered network statistic /
published network SNR` for each cohort event (the P1.5 `_run_event` output,
unchanged, by import). Each event gets its frozen 90% prediction interval from
Section 3 (LIGHT / INTERMEDIATE percentile band, or HEAVY `[0, epsilon]`). Define:

- **Primary metric — empirical coverage:** `coverage = (# measured events whose
  measured R falls within its frozen 90% band) / n_measured`.
- **Frozen pass/fail (no post-hoc tolerance):**
  - **CONFIRMED** iff `n_measured >= 8` AND `coverage >= 0.80`.
  - **FALSIFIED** iff `n_measured >= 8` AND `coverage < 0.70`.
  - **INCONCLUSIVE** otherwise (`0.70 <= coverage < 0.80`, or `n_measured < 8`).
- **`R -> 0` sub-check (reported separately, first-class):** every ISCO-below-band
  cohort event (`f_ISCO <= 30 Hz`) must have measured `R <= epsilon = 0.05`; if
  any such event has `R > 0.05` the **`R -> 0` sub-claim is FALSIFIED**,
  reported as its own named verdict regardless of the coverage headline (an
  ISCO-below-band event's band IS `[0, 0.05]`, so this also counts against
  coverage).
- **Secondary reported metric — trend:** Spearman `rho(M_det, R)` over the
  measured events, with frozen expectation `rho ~ -0.9` (P1.5 `-0.958`,
  fresh-holdout `-0.964`, Study-3 `-0.87`). Reported with its expectation;
  informational, not part of the coverage pass/fail.

**Why `[0.80, 1.0]` CONFIRMED and `< 0.70` FALSIFIED (finite-N binomial
justification, frozen).** The nominal band is a 90% interval, so a
well-calibrated predictor produces `covered ~ Binomial(N, 0.90)`. The
inconclusive buffer `[0.70, 0.80)` absorbs finite-N sampling noise so the
falsifier does not fire spuriously. Tail probabilities under true coverage
`p = 0.90` and the power against a truly `0.70`-calibrated predictor:

| N | CONFIRMED cut | FALSIFIED cut | P(FALSIFIED \| true p=0.90) [false alarm] | P(FALSIFIED \| true p=0.70) [power] |
| - | ------------- | ------------- | ----------------------------------------- | ----------------------------------- |
| 15 | `>= 12/15` | `< 11/15` | 0.013 | 0.49 |
| 20 | `>= 16/20` | `< 14/20` | 0.002 | 0.39 |
| 30 | `>= 24/30` | `< 21/30` | 0.0005 | 0.41 |
| 40 | `>= 32/40` | `< 28/40` | 0.0001 | 0.42 |

The false-falsify rate on a genuinely well-calibrated predictor is `<= 1.3%`
across the plausible O4c cohort size (`N ~ 15-40`); a truly `0.70`-calibrated
(mildly-miscalibrated) predictor is FALSIFIED with `~0.4` probability at those
sizes, and a badly-broken predictor much higher. This is the frozen tolerance;
it is not adjusted after N is known.

**A FALSIFIED outcome is a FIRST-CLASS product, not a failure.** A prospective
kill of the band-floor mechanism's sufficiency — bands calibrated on demonstrated
error that then fail to cover unseen O4c recoveries — is the strongest possible
test of the mechanism and publishes into the same replication repo beside a
confirmed outcome, exactly as the G0 charter and Rule 23 (negative results are
first-class) require.

## 6. Availability rule (mechanical, identical to P1.5 / the O3 rule)

Per event, in the frozen `_run_event` order: (a) eventapi metadata must resolve
(else `data_unavailable`); (b) on-source H1+L1 must return NaN-free strain (else
`data_unavailable`); (c) an off-source control segment with NaN-free H1+L1 must
be found and its network max must stay `< 8` (else
`instrument_invalid_no_verdict`). Dropped events are logged with the census and
do **not** count against the prediction — identical to Study-3, the fresh
holdout, and P1.5.

## 7. Falsifier-can-fire check (Rule 20)

The grading falsifier can physically fire on the O4c release. The data needed to
grade — O4c H1/L1 strain frames (the anonymous/authenticated GWOSC S3 buckets the
frozen pipeline already reads) and the O4c catalog's published `mass_1_source`,
`mass_2_source`, `redshift`, `far`, `network_matched_filter_snr`, `GPS`
(the GWOSC eventapi the P1.5 driver already reads) — is released together in the
December 2026 O4c bulk data release. On that release the frozen cohort rule
enumerates events, the frozen pipeline measures `R`, and the frozen coverage rule
returns CONFIRMED / FALSIFIED / INCONCLUSIVE with no human input. The falsifier
is therefore falsifiable-in-fact, not merely in form: if the mechanism's demonstrated
error envelope does not generalize to O4c, coverage drops below 0.70 and the
prediction is killed. (Should GWOSC delay O4c or release it without public
strain, the grade is `structurally-untestable` until the strain arrives — the
falsifier is deferred, never faked.)

## 8. Release-day artifacts (frozen now; run untouched on release)

- **Band table (Step B, computed mechanically per this procedure, committed in a
  later commit that cites this file):**
  `docs/research/papers/gw-inspiral-template-efficacy/verification/p2_prospective_bands.json`
  (schema `aigis.gw.p2_prospective_bands.v1`, `belief_moved=false`, sha256
  self-bound), produced by `scripts/research/p2_prospective_bands.py`.
- **Release-day grader:** `scripts/research/p2_release_day_grade.py` — freezes the
  O4c cohort by Section 4, runs the frozen `_run_event`, loads the frozen band
  table, applies the Section 5 coverage rule, emits CONFIRMED / FALSIFIED /
  INCONCLUSIVE with the coverage number and per-event covered flags. Positive- and
  negative-controlled against synthetic O4c cohorts (Rule 26;
  `tests/unit/scripts/research/test_p2_release_day_grade.py`).
- **Freeze manifest / signed-tag payload:**
  `docs/research/papers/gw-inspiral-template-efficacy/verification/P2_FREEZE_MANIFEST.md`
  hash-binds this preregistration + the band table + the grader + the frozen
  `r_predictor.py` + the frozen pipeline commit, ready to become the signed-tag
  payload on the public replication repo. The external anchor (signed tag) is
  operator-gated at push time and is NOT executed by this work.

## 9. Chronology (freeze-before-compute, enforced by commit ordering)

```
template_locked_at (frozen pipeline commit, 2026-07-14, template_commit_sha256
    4c43f31143db2a98cf53c19d8fce6f062d18c5c920cd6c4c4ca5d54a62340446)
 <= this preregistration commit (Step A: procedure only, NO band numbers)
 <  band-table + grader commit (Step B/C: p2_prospective_bands.json computed by
    running the frozen procedure above; cites this preregistration commit SHA)
 <  O4c release (Dec 2026)
 <  release-day grade (Step: p2_release_day_grade.py fires the frozen rule)
```

The preregistration commit **strictly precedes** the band-computation commit in
git history — that ordering is the freeze-before-compute guarantee. The frozen
predictor commit (`767d93bbd`), the frozen pipeline `template_commit_sha256`, the
band table sha256, and the freeze-manifest hash are each recorded so a third
party can verify nothing moved between freeze and grade.

## 10. What a third party needs to falsify this on release day

Given (a) this preregistration commit, (b) the committed band table
`p2_prospective_bands.json`, (c) the frozen `r_predictor.py` (`767d93bbd`), (d)
the frozen pipeline (`template_commit_sha256` above), and (e) the O4c public
release, a third party runs `p2_release_day_grade.py` (or reimplements the
Section 4-5 rule): enumerate the O4c cohort by the frozen rule, measure `R` with
the frozen pipeline, and compute coverage against the frozen bands. If
`coverage < 0.70` (or any ISCO-below-band O4c event recovers `R > 0.05`), the
band-floor mechanism's prospective prediction is **falsified**. Nothing in the
grade depends on this program's own authored state — only on the O4c strain, the
O4c published masses, and the frozen artifacts.

`belief_moved=false`; sandbox lane; the external anchor is operator-gated per G0.

---

## Results — the mechanically-derived frozen bands (Step B/C, computed AFTER the procedure above was committed at `8e43efdb5`)

The procedure in Sections 1-9 was committed at `8e43efdb5` **before** any band
number existed. `scripts/research/p2_prospective_bands.py` then ran that
procedure mechanically over the 48-row residual pool. No band parameter was
chosen after seeing coverage; the predictor was not refit.

**Band table:**
`docs/research/papers/gw-inspiral-template-efficacy/verification/p2_prospective_bands.json`
(`schema aigis.gw.p2_prospective_bands.v1`, `belief_moved=false`).
`content_sha256 = 677135a901d0469d00d1865b4177423f836dd4f875726da9e128e4179445661b`,
`self_sha256 = 2f08d3fb879f6842d1040f2961ca17a9924aaeb75fe4d52b79ff77af0aba7c7b`. The
table carries no wall-clock timestamp, so `p2_prospective_bands.py` reproduces the
entire file **byte-for-byte** on any machine.

**Integrity controls (all passed):**

- Twin `r_mech` integral disagreement `4.54e-9` (<< `1e-3` gate).
- Twin percentile disagreement `0.0` (numpy vs. manual sort-index, exact).
- Extraction positive control (Rule 26): `r_mech(m_det)` vs. the P1.5 receipt's
  stored per-event `r_mech` cross-checked on **26** rows, max delta `0.000561`
  (< `0.005`; the expected M_det-rounding effect). The control is guarded against
  becoming a no-op (fails closed if fewer than 26 rows are cross-checked).
- Pool `n = 48` (15 Study-3 + 7 O3a holdout + 26 P1.5), enumerated in the band
  table's `residual_pool.rows`.

**Frozen band table (per regime; honest widths, NOT narrowed):**

| Regime | `M_det` (M_sun) | n | Residual `(R - r_mech)` [5th, 95th] | Band for an event |
| ------ | --------------- | - | ----------------------------------- | ----------------- |
| LIGHT | `<= 20.45` | 5 | `[-0.289, -0.058]` (raw min/max `[-0.304, -0.050]`) | `clip(r_mech + [-0.289, -0.058], 0, 1)` |
| INTERMEDIATE | `20.45 .. 146.57` | 35 | `[-0.189, +0.245]` (raw min/max `[-0.231, +0.293]`) | `clip(r_mech + [-0.189, +0.245], 0, 1)` |
| HEAVY (ISCO-below-band) | `>= 146.57` | 8 | (all 8 pool events measured `R = 0.0`) | `[0, epsilon = 0.05]` (R -> 0 sub-claim) |

Honest read of the widths (the mechanism telling the truth, per the pre-committed
acknowledgement in Section 3):

- **LIGHT** both percentiles are **negative** — the band sits entirely BELOW
  `r_mech`, encoding the P1.5-measured systematic low-mass over-prediction.
  Width ~0.23. `n = 5` is thin (few pool events are `M_det <= 20.45`), so this
  band is correspondingly uncertain; it is NOT narrowed.
- **INTERMEDIATE** spans zero, width ~0.43 — wide because it pools the full
  mid-mass range where `r_mech` both over- and under-shoots. This is the mass
  range Studies 1-3 were developed on.
- **HEAVY** is the sharp `R -> 0` sub-claim `[0, 0.05]`; all 8 development-adjacent
  ISCO-below-band events recovered exactly `R = 0.0`.

**Release-day grader:** `scripts/research/p2_release_day_grade.py`
(`load_bands` self-verifies the band table; `event_band` + `grade_cohort` are
pure; `freeze_o4c_cohort` + `run_release_day` are the live driver). Verdict on
release day = coverage of the frozen bands over the measured O4c cohort.

**Grader controls (Rule 26 positive + negative, on synthetic O4c cohorts;
`tests/unit/scripts/research/test_p2_release_day_grade.py`, 27 tests pass):**

- **Positive control** — a well-calibrated synthetic cohort (R drawn inside the
  frozen bands ~90% of the time, heavy events at `R = 0`) grades **CONFIRMED**
  with coverage `>= 0.80` across 5 seeds.
- **Negative control** — a systematically-biased synthetic cohort (R shoved above
  the bands; heavy events recovering `R = 0.6`) grades **FALSIFIED** with coverage
  `< 0.70` and the `R -> 0` sub-claim **FALSIFIED**, across 5 seeds.
- Deterministic edge cases confirm the frozen thresholds: coverage `0.80` ->
  CONFIRMED, `0.75` -> INCONCLUSIVE, `0.70` -> INCONCLUSIVE (falsified is strict
  `< 0.70`), `0.40` -> FALSIFIED, `n < 8` -> INCONCLUSIVE; the `R -> 0` sub-claim
  fires independently of a high coverage headline; a tampered band table is
  rejected by `load_bands`.

**Freeze manifest / signed-tag payload:**
`docs/research/papers/gw-inspiral-template-efficacy/verification/P2_FREEZE_MANIFEST.md`
hash-binds this preregistration + the band table + the grader + the frozen
predictor + the frozen pipeline. The external anchor (signed tag on the public
replication repo) is operator-gated at push time and is NOT executed by this
work.

`belief_moved=false`; sandbox lane. The grade fires with zero discretion when
O4c is released (Dec 2026).
