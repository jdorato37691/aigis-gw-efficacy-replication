# Inspiral-only matched-filter efficacy across the GWTC catalogs: a preregistered characterization with two out-of-sample tests

**Internal preprint · AIGIS research program (CHARTER.md, GW-astrophysics
beachhead) · 2026-07-12** **Status:** internal; reviewed at the
frontier-reviewer tier by operator directive
([`referee-review.md`](referee-review.md) — author-adjacent, verification-first;
findings F1-F5 actioned or noted). An independent human domain-expert review is
still recommended before any external use (charter §10 note). **External
readiness: analysis-ready for external review (contract v3, Decision B); not yet
externally published.** All six executable follow-up gates in
`verification/README.md` have been executed and now pass: phase-scramble
ensemble null, Study-3 coincidence, PSD robustness, the fresh untouched
holdout — outcome `confirmed` — the PhenomD external oracle (which first failed
honestly on 2026-07-16 at minimum match 0.918 and passes after the preregistered
spin-sector completion retry of 2026-07-17 at minimum match 0.99997 on the frozen
grid, the original fail preserved in provenance — §3.6), and the
posterior-uncertainty propagation of the prediction curve, which passes under
**contract v3** on the O1 trend criterion alone (ρ ≤ −0.5 preserved in 98/100
joint draws, §3.4). Contract-vs-claim note (resolved): the posterior gate
originally tested the _original_ posterior-robust-curve criterion (O2, median
|R − R̂| ≤ 0.15 preserved in ≥ 90% of draws), which failed honestly at 54/100
joint draws and is broader than the paper's revised point-estimate-conditional
claim. The operator resolved the mismatch by authorizing contract v3 (PI-approved
2026-07-16, `OPERATOR-DECISIONS.md` Decision B, commit `13eb7b848`), which gates
the PASS on O1 alone and preserves the original O2 criterion and its `fail`
verdict as a withdrawn-claim record in the gate output rather than deleting it.
With all six gates passing, the readiness auditor (`gw_package_readiness.py`)
reports `analysis_ready_for_external_review`; external publication stays
hard-blocked on an external immutable trust anchor (Decision C, not executed
here).

## Abstract

We characterize a legacy recovery statistic: the quadrature sum of independently
maximized H1 and L1 matched-filter SNR magnitudes, divided by the published
catalog network SNR. This ratio is not an equivalent coincident network
statistic. We apply it to an inspiral-only TaylorF2 template across the GWTC
binary-black-hole population using one fixed, injection-controlled FFT
matched-filter pipeline in pure numpy on public GWOSC strain. Across the ten
GWTC-1 BBH events, recovery fraction R declines with detector-frame total mass
(Spearman ρ = −0.891, p = 5.4×10⁻⁴ at catalog point masses; ρ = −0.65, 90% CI
[−0.83, −0.31] once parameter-posterior uncertainty is propagated — the trend
survives but the point value overstates its strength), from R ≈ 0.88 at 20 M☉ to
R ≈ 0.21 at 125 M☉. The decline itself is an anticipated relationship, not a new
one: Flanagan & Hughes (1998) derived the monotonic inspiral-share decline in
this exact regressor, and it is established template-family doctrine (Damour,
Iyer & Sathyaprakash 2001; Buonanno et al. 2009) — the contribution here is the
per-event quantification of the R statistic on real catalog events, with
preregistered cross-catalog and holdout transfer (§8). The trend is not a PSD
artifact: it survives all four locked PSD regimes (on-source mean-4s, off-source
mean-4s, many-average median-4s, glitch-gated mean-4s; ρ −0.830 to −0.891, n =
10 each). A preregistered low-mass
adequacy prediction **failed** on
GW151226 (R = 0.557): the one GWTC-1 event with significant aligned spin (χ_eff
≈ 0.18). Adding the single 1.5PN aligned spin-orbit phasing term raised its
recovery to 0.789 under locked differential predictions — the four
near-zero-spin events moved ≤ 0.034, consistent with a targeted aligned-spin
contribution within those controls — while the mass trend persisted (ρ =
−0.903), the residual heavy-event deficit being **consistent with** the missing
merger–ringdown share of the standard IMR energy budget (Flanagan & Hughes
1998) — a textbook mechanism verified here event-by-event on real catalog data,
not a new localization. Two
clean out-of-sample tests now exist. A seeded 20-event GWTC-3 sample untouched
by Studies 1–2 transfers the trend (ρ = −0.87, p = 2.4×10⁻⁵), the GWTC-1-derived
binned predictor forecasting unseen recoveries at 0.088 median absolute error;
and a fresh untouched holdout — ten GWTC-2.1 O3a events frozen by a
deterministic preregistered rule, fully disjoint from the 31-event development
manifest, evaluated exactly once — **confirms** both locked criteria (7 of 10
measured, 3 excluded by a mechanical data-availability rule; ρ = −0.964, p =
4.8×10⁻⁴; median |R − R̂| = 0.129 ≤ 0.15), the three heaviest events recovering
R ≈ 0 as the ISCO-below-band mechanism predicts. Both median-error results are
point-estimate-conditional: propagating parameter-posterior uncertainty through
the Study-3 evaluation preserves the trend criterion (ρ ≤ −0.5) in 98/100 joint
draws but the ≤ 0.15 median-error criterion in only 54/100 — the curve is a
point-estimate tool with demonstrated out-of-sample transfer, not a
posterior-robust predictor. After two preserved negatives pointed toward a phase
contribution to the merger phase, a source-transcribed PhenomD phase
(coefficients transcribed from the arXiv:1508.07253 LaTeX source, never from
memory) substantially reduced the measured deficit: median heavy-event recovery
0.438 → **0.902** in-sample and 0.857 on the GWTC-3 **cross-catalog cohort** (a
development cohort reused across Studies 4–6, not a fresh holdout — see §4),
coherence-controlled against a 100-scramble ensemble null (all 7 heavy events at
empirical p = 0.0099, physical recovery above the entire scramble distribution),
all four preregistered predictions passing. The phase transcription is now
externally validated through a preserved fail-diagnosis-completion arc: the
first preregistered oracle gate against LALSimulation IMRPhenomD **failed
honestly** (minimum match 0.918 against the 0.99 floor, tracking the
then-declared 1.5PN-only/single-χ_eff spin deviations), the preserved fail
diagnosed the incomplete aligned-spin sector, and the preregistered completion
retry — the full two-spin 3.5PN aligned-spin phasing transcribed from the same
source, evaluated under a preregistered sub-bin refinement of the locked match
metric — **passes** the frozen 13-point grid at minimum match 0.99997 (median
0.99999). Every study was preregistered before execution; all negatives are
preserved — including the superseded oracle fail (kept on disk and in git
history as the diagnosis that drove the completion) and one of the six
follow-up verification gates (posterior robustness of the prediction curve),
which fails honestly and stands in the record beside the five that pass.

## 1. Provenance and discipline

Every result traces to a committed preregistration (metric, tolerance, data
segments, pipeline, and falsifiers locked in git history before any on-source
run), sha256-stamped run receipts, and a canonical scientific- memory record
with receipt-verified external evidence:

| Study                    | Preregistration                                         | Registry record              | Historical registry enum            |
| ------------------------ | ------------------------------------------------------- | ---------------------------- | ----------------------------------- |
| GW150914 replication     | `2026-07-12-gw150914-matched-filter.md`                 | exp_2f55a6d265f9d8b6958c3636 | experimentally_validated            |
| GW151226 replication     | `2026-07-12-gw151226-matched-filter.md` (+v2 amendment) | exp_30798f9bc3a7b4e1f7fe8c93 | experimentally_validated            |
| GW170817 replication     | `2026-07-12-gw170817-matched-filter.md` (+erratum)      | exp_c97691dba56754396b8e901d | experimentally_validated            |
| Study 1: efficacy sweep  | `2026-07-12-gwtc1-taylorf2-efficacy.md`                 | exp_d8083481cdf64d910ac08118 | externally_grounded                 |
| Study 2: aligned spin    | `2026-07-12-gwtc1-aligned-spin.md`                      | exp_b443c6340e6a56f4d898d11f | externally_grounded                 |
| Study 3: OOS transfer    | `2026-07-12-gwtc3-out-of-sample.md`                     | exp_03f6bd4cfa9019dc7e94ed71 | externally_grounded                 |
| Study 4: IMR ansatz v1   | `2026-07-12-imr-ansatz-heavy-events.md`                 | exp_20f8fb7cc45ac49a2987dfd2 | contested (preserved negative)      |
| Study 5: coherence test  | `2026-07-12-imr-coherence-controlled.md`                | exp_1d6565aa2c7c0c1b51c6b10a | externally_grounded (mixed verdict) |
| Study 6: PhenomD phase   | `2026-07-12-phenomd-sourced-phase.md` (+replication)    | exp_83871cc6eeadf4d1b80ec4d8 | experimentally_validated            |
| Study 7: sourced physics | `2026-07-12-sourced-physics-completion.md`              | exp_45123cf9e6ab4e23e397a5e4 | externally_grounded (mixed verdict) |
| Study 8: Virgo arm       | `2026-07-12-virgo-network-extension.md` (+v2 amendment) | exp_9449ac379daee2245b552011 | contested (preserved negative)      |

The final column reports persisted machine metadata, not current claim
clearance. In particular, `experimentally_validated` was assigned by an older
independence rule to same-project alternate-configuration reruns. The
human-readable interpretation is **within-project computational reproduction**;
the package is **analysis-ready for external review (contract v3, §1 status
header) but not independently validated**, and makes no independent
experimental-validation claim.

The six executable follow-up gates (`verification/README.md`, validated
fail-closed by `scripts/research/gw_package_readiness.py`) are artifact-bound
the same way. The four artifacts landed after the round-3 audit:

| Gate                    | Preregistration                                    | Artifact                                    | Verdict                                              |
| ----------------------- | -------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------- |
| PSD robustness          | `2026-07-16-psd-robustness-artifact-regimes.md`    | `verification/psd_robustness.json`          | pass (trend survives all four locked regimes)        |
| Posterior uncertainty   | `2026-07-12-gwtc3-out-of-sample.md` (locked O1/O2) | `verification/posterior_uncertainty.json`   | pass under contract v3 — trend-only O1 in 98/100 draws; O2 curve fail (54/100) preserved as the withdrawn-claim record (Decision B) |
| PhenomD external oracle | `2026-07-16-phenomd-oracle-match-grid.md` + retry `2026-07-16-phenomd-oracle-spin-sector-retry.md` (b504786a7) | `verification/phenomd_external_oracle.json` | pass after preregistered completion retry (min match 0.99997; the 2026-07-16 fail at 0.918 preserved in provenance) |
| Fresh untouched holdout | `2026-07-16-fresh-untouched-holdout.md`            | `verification/fresh_untouched_holdout.json` | pass (outcome `confirmed`; chronology validator-verified) |

The other two gates — the phase-scramble ensemble and Study-3 coincidence — were
already satisfied by `verification/phase_scramble_ensemble.json` and
`verification/study3_coincidence.json` (2026-07-13); §4 and §7 carry their
numbers.

Condition-1 (novelty) due diligence:
[`literature-positioning.md`](literature-positioning.md) — a three-pass,
evidence-checked prior-art review (a 20-entry verified prior-art table; a
TGR-catalog / 2024-26 follow-up / methodology-literature addendum; and a final
residual-venue pass covering GWTC-4-era TGR, theses/DCC/proceedings, and the
methodology venues, addendum 2; policy "err toward finding prior art";
per-claim verdicts with adversarially checked citations). Its required
repositionings are folded into this text and carried in §8. The surviving
narrow claims held against the final pass; residual risk is assessed there as
LOW for the measurement claims and LOW-MODERATE for the methodology claim,
with the honestly unswept remainder stated: non-English literature, paywalled
journal-only papers, LVK-internal DCC documents, and anything posted after the
July 2026 sweep snapshot.

Run receipts: `~/.aigis/research/gw_replication/`. Code:
`scripts/research/{matched_filter_gw150914,taylorf2,gw_event_replication,gwtc1_taylorf2_sweep,gwtc1_aligned_spin_study,gwtc3_oos_study,phenomd_coefficients,phenomd_phase,phenomd_phase_study}.py`.

## 2. Methods

**Instrument and statistic.** Frequency-domain matched filter (LOSC-tutorial
normalization): Tukey(1/8) window, one-sided Welch PSD interpolated onto the
two-sided grid, snr(t) = |2 f_s IFFT(d̃ h̃*/S_n)|/σ, σ² = |Σ h̃h̃*/S_n| df,
band-limited weights. Controlled before every first use on off-source data:
absolute scale (pure-noise max SNR ~4–5), injection recovery (±25% of a
deterministically calibrated target), and time-convention alignment (≤10 ms).
Three instrument bugs were caught by these controls before any on-source run (a
broken normalization; a noise-swamped injection calibration; a correlation-shift
vs time-index confusion in peak search) — each preserved in control receipts.
For historical receipt compatibility the quadrature of the independently
selected H1/L1 maxima is stored under `network_snr`, but new receipts also store
`recovered_statistic.statistic_name` as
`quadrature_of_independently_maximized_single_detector_snrs` and
`recovered_statistic.coincidence_enforced` as `false`. The analysis ratio R
divides that statistic by the catalog network SNR; no equality or one-sided bias
is assumed.

**Reproduction engine (the three named events).** NR-calibrated templates from
GWOSC's own event releases (GW150914, GW151226); TaylorF2 for the BNS GW170817.
Per-event: injection validation → off-source known-bad control (<8) → single
confirmatory on-source run → within-project alternative-PSD reproduction
(median-Welch 16 s PSD, distinct process label but shared data, code, project,
and development history) → receipt-bound registry update.

**TaylorF2 (pure numpy, no pycbc/lalsuite).** 3.5PN point-particle stationary-
phase phasing; coefficient-integrity tripwire (independently written 2PN twin
must agree ≤0.5 rad; observed 10⁻¹² rad); FFT sign convention validated against
the analytic chirp-time relation τ(f) = (5/256)Mc^(−5/3)(πf)^(−8/3). Study 2
adds the 1.5PN aligned spin-orbit term (113/3 − 76η/3)χ_eff with an exact
zero-spin regression gate. Tidal terms and 2PN spin-spin omitted (stated
detection-grade approximations).

## 3. Results

### 3.1 The three within-project reproductions (G1+G2 cleared)

| Event    | Published catalog net SNR | Confirm legacy statistic | Alternate-PSD reproduction | Notes                                                                                                                         |
| -------- | ------------------------- | ------------------------ | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| GW150914 | 23.7                      | 22.76                    | 20.62                      | H1–L1 delay 7.1 ms (published ~6.9)                                                                                           |
| GW151226 | 13.1                      | 11.89                    | 11.37                      | NR template                                                                                                                   |
| GW170817 | 32.4                      | 30.48                    | 30.46                      | L1 glitch mechanically gated at 92.9σ, GPS 1187008881.3885 — the documented transient, found by a rule locked without peeking |

**Preserved negative:** GW170817's preregistered GW→GRB timing window [1.5, 2.0]
s failed (recovered 2.026 s). Erratum: the window paired the GBM _trigger_ GPS
with the burst-_onset_-based +1.74 s figure; trigger−coalescence is ~2.04–2.05
s, so the measurement is sound (~20 ms) and the window was mis-derived. The
verdict stands unrevised. Lesson: lock the fiducial definition, not just the
number.

### 3.2 Study 1 — the efficacy curve (in-sample)

R declines with detector-frame total mass: ρ = −0.891 (p = 5.4×10⁻⁴), all 10
events off-source-valid. R spans 0.875 (GW170608, 19.9 M☉) → 0.214 (GW170729,
125.5 M☉, whose ISCO ≈ 35 Hz sits at the analysis band floor as predicted).
Direction and threshold are established doctrine, not findings of this study:
Damour, Iyer & Sathyaprakash (2001) already quantified that inspiral-only PN
templates lose significant SNR above m ≳ 30 M☉, Buonanno et al. (2009) made the
degradation canonical in template-family design, and the ISCO-vs-band-floor
argument is Hanna et al. (2008); what this study contributes is the per-event
measurement (§8). **Preregistered H1 failed:** GW151226 R = 0.557 despite
M_det = 23.3.

### 3.3 Study 2 — the spin diagnosis (differential confirmation)

| Prediction (locked)                       | Outcome                               |
| ----------------------------------------- | ------------------------------------- |
| P1: R(GW151226) ≥ 0.75 with the spin term | **0.789** (from 0.557) — pass         |
| P2: near-zero-spin events move < 0.05     | 0.000 / −0.001 / 0.007 / 0.034 — pass |
| P3: mass trend persists (ρ ≤ −0.6)        | ρ = −0.903 — pass                     |

The residual heavy-event deficit is thereby **consistent with** the missing
merger–ringdown rather than spin (a differential localization, not an isolated
causal proof — the spin sector is probed by essentially one event, GW151226).
That GW151226 requires spin is not a new result: the discovery paper measured
nonzero aligned spin with ~55 in-band cycles (Abbott et al. 2016), and Capano
et al. (2016) showed aligned-spin templates recover the most SNR at low mass.
The claim here is narrower and sharper — that exactly one 1.5PN spin-orbit
term suffices for this event's recovery deficit, under locked differential
predictions (§8).
GW170729 (χ = 0.37 but 125 M☉) was unchanged, as expected (too few in-band
cycles) — noted pre-run, deliberately not locked.

### 3.4 Study 3 — out-of-sample transfer (GWTC-3)

Seeded 20-event sample of unseen O3 BBH; 15 measured, 5 excluded by mechanical
availability/validity rules (3 lacked clean H1+L1 data; 2 failed the off-source
control). Locked predictor: binned medians of Study 2's GWTC-1 recoveries.

| Prediction (locked)                 | Outcome                             |
| ----------------------------------- | ----------------------------------- |
| O1: ρ(M, R) ≤ −0.5 on unseen events | **ρ = −0.87** (p = 2.4×10⁻⁵) — pass |
| O2: median \|R − R̂(M)\| ≤ 0.15      | **0.088** — pass                    |

The curve transfers across observing runs (O1/O2 → O3) despite different
detector sensitivities.

**Posterior propagation (2026-07-16) — a preserved fail with a split.** The
O1/O2 verdicts above are point-estimate-conditional: R and R̂ are evaluated at
catalog point masses. Propagating parameter-posterior uncertainty through this
evaluation (100 joint cohort draws over the 15 measured events; per-parameter
two-piece-normal marginals from the eventapi median + 90% CI; R recomputed and
the locked predictor re-evaluated per draw; artifact
`verification/posterior_uncertainty.json`) splits the two criteria. O1 (ρ ≤
−0.5) is preserved in **98/100** draws — ρ percentiles [5/50/95] = [−0.888,
−0.734, −0.530], every draw negative. O2 (median |R − R̂| ≤ 0.15) is preserved
in only **54/100** draws — median-error percentiles [0.079, 0.143, 0.210].
Under the locked ≥ 90%-of-draws rule the gate fails, and the fail is preserved:
the mass **trend** is posterior-robust; the point-prediction **curve** is not.
The 0.088 median error is therefore a point-estimate result, not a
posterior-marginalized one (naive and posterior-median M_det differ by up to
16.1 M☉ on these heavier events). The claim this paper carries forward is
correspondingly scoped: the predictor works at catalog point estimates and
transfers out of sample there (§3.12); it is not established under full
parameter uncertainty.

### 3.5 Studies 4–5 — the merger–ringdown extension (artifact caught, coherence signal observed, target missed)

**Label note (applies to Studies 4–6).** The preregistered prediction rows below
say "OOS heavy median" — but these GWTC-3 heavy events were first used in Study
3 and then _reused_ across Studies 4–6, so from Study 4 onward they are a
**cross-catalog development cohort**, not an untouched holdout. Study 3 (§3.4)
was the one genuine out-of-sample test when Studies 4–6 ran; the 2026-07-16
fresh untouched holdout (§3.12) has since added a second. The locked prereg
labels are left verbatim (editing a pre-commitment would break its integrity);
this note carries the correction, consistent with §6.

A PhenomA-shaped hybrid (control-checked inspiral + f^(−2/3) merger amplitude +
Lorentzian ringdown at published-anchor-checked remnant QNM values; TaylorF2
phase continued through merger) was tested under the same discipline.

**Study 4 — the artifact control fired.** The preregistered no-degradation
control failed: GW151226 lost 0.061 (limit 0.05) — phase-incoherent merger
content dilutes template norm on low-mass events. Per the locked rule the assay
was declared invalid and the tantalizing heavy-event improvements received **no
verdict**. All integrity gates had passed (remnant anchors vs published
GW150914/GW170729 values; inspiral-limit regression at 3×10⁻¹⁶; injection
validation): the failure isolates the merger _phase_.

**Study 5 — the coherence-controlled redesign.** Known-bad = a per-event
phase-scrambled twin (identical amplitude; seeded uniform phase in the added
band): a norm artifact survives scrambling, coherent physics does not.
Applicability was mass-gated (M_det ≥ 60), justified by Study 4's measurement.

| Prediction (locked)                                | Outcome                        |
| -------------------------------------------------- | ------------------------------ |
| Q1: median heavy R_hybrid ≥ 0.65                   | **0.540 — FAILED** (preserved) |
| Q2: median margin vs scrambled ≥ +0.10, wins ≥ 6/7 | **+0.123, 7/7 — pass**         |
| Q3: OOS heavy median ≥ 0.408 with margin ≥ +0.10   | **0.562, +0.164 — pass**       |

**Net result:** under the single-realization negative control, the
merger-amplitude extension adds a coherence-sensitive recovery signal in the
GWTC-1 sample and reused cross-catalog development cohort, raising heavy-event
medians 0.438→0.540 and 0.258→0.562 respectively. The continued-TaylorF2 merger
phase leaves the Q1 recovery target unmet. These two preserved negatives (Study
4 P2, Study 5 Q1) are consistent with a partial ansatz, but do not isolate a
unique physical mechanism. Study 6 tests a phenomenological merger phase.

### 3.6 Study 6 — a transcribed PhenomD phase, since oracle-validated through a preserved fail, closes the measured deficit

The "operator must supply the papers" gate dissolved: arXiv serves the LaTeX
source of both PhenomD papers, so verifiable transcription became possible
without any hand-copied number. The full 19×11 coefficient table of Khan et al.
2016 (arXiv:1508.07253, `tab:coefftable`) was parsed from the sha256-stamped
tarball behind a parse tripwire (exact shape, exact label order, 8 cells
spot-checked against verbatim source strings spanning every number format). The
three-region phase (TF2+σ inspiral / β intermediate / α merger–ringdown,
C¹-stitched at Mf = 0.018 and 0.5 f_RD per the paper) was placed on the Study-4
amplitude unchanged — a phase-only swap, so any delta attributes to the phase.
Gates: stitcher-identity positive control (residual exactly 0), per-config C¹
continuity, bitwise amplitude regression against the Study-4 code path (0.0),
mapped α₅ ∈ [0.992, 0.993] vs the paper's stated [0.98, 1.04], injection
validation (recovered 22.3/20.0, 0.0 ms alignment). Declared deviations:
1.5PN-only spin sector; anchor-validated QNM instead of Paper 1's fits; single
effective spin; amplitude untouched.

| Prediction (locked)                                   | Outcome                           |
| ----------------------------------------------------- | --------------------------------- |
| S1: median heavy R ≥ 0.65 (twice-missed target)       | **0.902** — pass                  |
| S2: margin vs scrambled ≥ +0.10, wins ≥ 6/7           | **+0.573, 7/7** — pass            |
| S3: OOS heavy median ≥ 0.408 with margin ≥ +0.10      | **0.857, +0.517** — pass          |
| S4: beats Study-5 hybrid paired per-event (both sets) | **+0.404 / +0.305 median** — pass |

Registry: exp\*83871cc6eeadf4d1b80ec4d8. Per-event recoveries now span 0.60–0.97
of published network SNR (H1+L1-only, detection-grade approximations) — heavy
events recover as well as light ones. This is **consistent with** the two
preserved negatives having localized the deficit to the merger phase: swapping
only the phase model (amplitude held fixed) recovers ≈0.40 of recovery fraction,
exactly where Studies 4–5 pointed. The mechanism is textbook — the deficit is
the missing merger–ringdown share of the standard IMR energy budget (Flanagan
& Hughes 1998), and Phenom-family phasing (Ajith et al. 2007) was invented
precisely to cure it; what this study contributes is the event-by-event
verification on real catalog data (§8). It establishes that _this_ phase model
improves _this_ benchmark — not that the merger phase was the sole binding
physical constraint. The diagnosis chain (mass trend → spin term → amplitude
coherence → phase) closed in six preregistered studies with zero threshold
edits.

**External-oracle validation (2026-07-16 → 2026-07-17) — a preserved fail, its
diagnosis, and the preregistered completion that passes.** This is the
verification layer working as designed, and the record keeps all three stages.
**Stage 1, the honest fail (2026-07-16).** Against LALSimulation IMRPhenomD
over the preregistered 13-point mass/spin grid (prereg
`2026-07-16-phenomd-oracle-match-grid.md`; `exact_phenomd` mode, isolated
`lal_venv`, common LAL amplitude so the match isolates the phase): median
noise-weighted match 0.98864, minimum **0.91751** at (55 + 48 M☉, χ = 0.6),
against the preregistered floor of 0.99 — gate FAIL, preserved (receipt
`LAL_oracle_20260716T113628Z.json`, commit 2203e431a). The fail was
diagnostic: the merger-band RMS phase residual grew monotonically with aligned
spin (≈ 0.01 rad at χ = 0 to 0.69 rad at χ = 0.6), exactly where the
then-declared deviations lived (1.5PN-only spin sector, single effective
spin), plus a discrete-IFFT time-alignment quantization in the committed match
metric costing non-spinning points (0.9745 at 50 + 45 M☉ despite < 0.01 rad
residual). **Stage 2, the preregistered completion retry**
(`2026-07-16-phenomd-oracle-spin-sector-retry.md`, committed b504786a7 before
the run; grid, floor, and validator frozen): the full two-spin 3.5PN
aligned-spin TaylorF2 phasing — the φ₃–φ₇ spin-orbit terms plus the 2PN
quadratic-in-spin terms and the two-spin χ_PN mapping — transcribed from the
same sha256-stamped arXiv:1508.07253 TeX appendix behind a four-leg tripwire
(independently typed twin, worst 4.0×10⁻¹³ rad; equal-spin consistency against
Study 7's independent implementation; zero-spin regression 2.3×10⁻¹³ rad;
verbatim TeX anchors), the oracle path switched to the Study-7 sourced Paper-1
remnant fits (narrowing D2 to the Berti-Cardoso-Will fit-vs-table QNM
conversion), and a preregistered sub-bin evaluation (32× zero-padded
correlation + parabolic peak) of the _identical_ locked maximized-over-time
match, reported alongside the discrete value at every point. **Stage 3, the
result (2026-07-17).** The completed transcription alone, under the unchanged
discrete metric, moves the grid to min 0.97451 / median 0.99791 — the
inspiral residuals collapse from 0.15–0.47 rad to 0.001–0.009 rad and the
χ-monotone trend is gone; the remaining sub-floor points are non-spinning,
i.e. quantization, not physics. Under the preregistered sub-bin evaluation:
**minimum match 0.99997, median 0.99999 — the gate PASSES** (artifact
`verification/phenomd_external_oracle.json`, receipt
`LAL_oracle_20260717T001009Z.json`; the residual ~3×10⁻⁵ deficit is consistent
with the narrowed D2 fit-vs-table QNM conversion). Scope consequence: the
transcribed phase is externally validated on the frozen grid — for the full
aligned-spin sector, not just the non-spinning core. The deficit-reduction
results in this section (0.438 → 0.902; 0.857 on the reused cross-catalog
cohort) stand as measured with the Study-6-era phase, whose spin sector Study
7 and this retry completed from the same source.

**Within-project alternative-configuration reproduction.** The persisted
registry enum is `experimentally_validated`, assigned under a historical
independence rule; it is not the human claim state and does **not** mean
independent experimental validation of the LIGO detections. The observations are
the experiments; this package reproduces and characterizes them computationally.
Under a pre-committed protocol
(`2026-07-12-phenomd-sourced-phase-replication.md`): Welch-median 16 s PSD,
distinct executor identity, templates rebuilt from the sha256-verified artifact
behind re-run gates. All three locked criteria passed: R1 heavy median 0.842
(within ±0.10 of the confirm 0.902, ≥0.65); R2 reused-cohort median 0.850; R3
median per-event |ΔR| 0.088. **Coincidence audit (referee review, corrected
scope):** a post-hoc per-row audit keyed by template sha256 (receipt
`STUDY6_review_coincidence_audit_20260712T040807Z.json`) found the confirm pass
fully coincident — all 13 rows have H1–L1 peaks within a 15 ms coincidence
window (the H1–L1 light-travel time is ≈10 ms; the extra 5 ms is a timing
margin, not the light-travel bound itself; worst 8.8 ms) — but **three**
replicate rows non-coincident, not the one first documented: GW200220 (a 39.0σ
H1 transient the median PSD exposes because, unlike a mean-4s estimator, it does
not absorb a glitch's own power), plus GW200128 (94 ms) and GW200219 (185 ms),
whose quieter recoveries leave the true peak sub-threshold in one detector under
the robust estimator. All three locked criteria pass under full exclusion of the
non-coincident rows (R1 0.842 unchanged; R2 0.909, though on n=3; R3 0.074) —
the locked numerical verdict does not hinge on them, but the reused-cohort
reproduction evidence is correspondingly weaker than the confirm pass. This does
not establish a fresh holdout or independent validation; the historical registry
enum is retained only as provenance.

### 3.7 Instrument v2 attempt — a preserved negative on coincidence enforcement

A preregistered coincidence-enforcing statistic
(`2026-07-12-coincident-network-statistic.md`: 10 ms sliding pair maximum with a
4.0 per-detector floor) was built to close review finding F3 and validated
against its own controls (receipt `COINCIDENT_v2_20260712T042113Z.json`). **The
controls invalidated it.** C1 (identity on coincident data) failed: the floor
zeroes genuine quiet events — GW170818's confirm H1 peaks at ≈3.9 and GW200220's
confirm sits sub-4 in both detectors, while the other 11 rows reproduced v1
exactly (relative difference 0.0000). C2 (glitch rejection) failed on the loud
row: the 39σ H1 transient survives at 32.9 because a quadrature maximum is
glitch-dominated whenever noise in the partner detector fluctuates past the
floor anywhere in the 20 ms pairing window — though the two moderate
non-coincident rows were correctly rejected to honest `no_coincident_pair`
nulls, and the dual-detector injection (C4: 30.4 vs expected 28.3, 4.6 ms
pairing) and known-bads (C3) passed. Per the Study-4 precedent, the assay is
invalid and its downstream replication re-measure (C5) receives **no verdict**;
Study 6's registry record is untouched. The mechanism is now measured, not
assumed: coincidence plus an amplitude floor cannot both keep quiet real events
and reject loud transients — the discriminating information is waveform
consistency, i.e. a per-detector χ² (Allen-style frequency-binned) veto, which
is the properly scoped next instrument iteration.

### 3.8 Instrument v3 — the χ² veto passes its controls; its re-measure assay does not

The preregistered Allen frequency-binned χ² veto
(`2026-07-12-chi2-veto-instrument-v3.md`: p = 16 equal-template-power bins, dof
= 30, standard re-weighted SNR, on the coincidence pairing with **no** amplitude
floor; receipt `CHI2_v3_20260712T043014Z.json`) **passed every
instrument-validity gate**: an exact injected template sits at χ²_r = 0.65 with
ρ̂/ρ = 1.0 (X0a); a 1 ms blip scaled to ρ = 15 is crushed to χ²_r = 17.2, ρ̂/ρ =
0.27 (X0b); no clean confirm row loses more than 4.5% (X1, worst ratio 0.955);
and the 39σ GW200220 transient is annihilated — H1 39.0 → ρ̂ 3.0, network 39.56 →
5.21 (X2) — while all known-bads stay < 8 (X4). The v2 dilemma is resolved:
waveform consistency keeps quiet real events AND rejects loud transients.

The preregistered replication re-measure (X5) then failed its locked criteria
(R3 median |ΔR| = 0.269) — but a post-hoc Rule-26 oracle control (receipt
`CHI2_v3_oracle_20260712T043222Z.json`) shows the X5 assay itself was invalid: a
**perfect** injected signal under the replication PSD config (Welch median, 16 s
— only ~3 averages in a 32 s segment) scores χ²_r ≈ 4.0 and is suppressed to ρ̂/ρ
≈ 0.556, independent of signal strength. Per-bin PSD-estimation error
masquerades as signal inconsistency, scaling χ² with ρ². No real signal could
have passed X5's thresholds under that config, so its failure is an assay
artifact, not evidence — the same class as Study 4's invalid assay and the
Genesis-P0 precedent. **Named protocol conflict:** the prereg's locked clause
required appending a FAILED reproduction on X5; the positive-control invariant
overrides it (recording an artifact would be false rigor), so no registry action
was taken and Study 6's record is untouched. The prereg's own omission — the
injection control ran only under the confirm config — is the documented root
cause. Measured constraint for all future χ² use: the veto requires a
well-averaged PSD (mean-4s: χ²_r = 0.65 on the oracle; median-16s: 4.0); a v4
replication protocol should pair the χ² veto with a robust-but-averaged
estimator (e.g. median-of-many-4s-segments).

### 3.9 Protocol v4/v5 — the glitch-immune replication arm lands

Pairing the control-passing χ² veto with a robust-AND-averaged PSD (Welch
median, 4 s — ~15 averages; prereg `2026-07-12-chi2-median4s-protocol-v4.md`)
fixed the §3.8 constraint: the in-config template oracle sits at χ²_r = 0.689
with ρ̂ untouched, so the assay is unbiased in the exact configuration it
measures. One drafting bug intervened: v4's Y1 (no clean-event veto) was locked
over all 13 rows including the one Y2 required suppressed — the instrument was
convicted for obeying the other gate (GW200220 ratio 0.347; every other row ≥
0.914). Per the locked clause that run received no verdict (receipt
`CHI2_v4_20260712T101908Z.json`); the v5 prereg corrected the partition
(complementary gates must partition the sample; the Y2-designated glitch row is
excluded from Y1 by definition) and re-evaluated the same deterministic
measurements (integrity-checked via the v4 receipt digest — no new data, no
threshold edits).

**Result (receipt `CHI2_v5_20260712T102124Z.json`): all gates pass, outcome
CONFIRMED.** R1 median heavy recovery 0.912 (confirm pass: 0.902); R2
reused-cohort median 0.839 on all six measured GWTC-3 events, every row H1-L1
coincident (0.5–9.5 ms); R3 median per-event |ΔR| vs the confirm pass **0.012**.
The GW200220 H1 transient is χ²-suppressed 14.1 → 1.8 while the real event
content survives. A second within-project reproduction attempt
(`welch_median_4s_chi2_veto_v5` — different PSD estimator and detection
statistic, but shared data, code, project, and development history) is
receipt-bound on the Study 6 record. The instrument arc that began with a 39σ
anomaly closes with a glitch-robust reproduction arm that passes its in-config
injection control and agrees with the confirm pass at the percent level. This
remains computational robustness evidence, not scientific independence.

### 3.10 Study 7 — sourced-physics completion (D1/D2 closed; a control mis-specified)

The declared deviations D1 (1.5PN-only spin sector) and D2 (unsourced remnant
fits) were closed by the same verifiable-transcription machinery as Study 6: the
complete φ₀–φ₇ with full spin dependence from the arXiv:1508.07253 appendix, and
Paper 1's `eqn:FinalSpin`/`eqn:Erad` remnant fits — with the S-vs-Ŝ convention
_discriminated by the GW170729 anchor_ (the unrescaled-S reading gives a_f =
0.785 vs published 0.81; the rescaled reading fails at 0.91). Gates: zero-spin
and 1.5PN-only regressions at ~1e-13 rad; transcription spot-checks; a bitwise
harness-identity control on the module-injection mechanism. Design: paired
in-run arms (baseline = committed Study-6 pipeline) on 15 events including both
low-mass controls.

| Prediction (locked)                             | Outcome                          |
| ----------------------------------------------- | -------------------------------- |
| Z1: GW151226 (χ=0.18) must not degrade          | **0.746 → 0.906 (+0.16)** — pass |
| Z2: every \|χ\| ≤ 0.10 event moves < 0.02       | **GW170608 +0.035 — FAILED**     |
| Z3: heavy median must not degrade               | **0.902 → 0.906** — pass         |
| Z4 (reported): GW170729 +0.016; GW191109 −0.001 | improvement, as expected         |

Registry: exp*45123cf9e6ab4e23e397a5e4, externally_grounded, **mixed verdict
preserved**. The measured benchmark gain is differential: GW151226 lands at
0.906 — within half a percent of the NR-template benchmark (0.91) — and no event
anywhere degrades by more than 0.002. Z2's failure is itself the finding: the
breach is the \_low-mass* control improving (+0.035 at χ = 0.03) while all nine
near-zero-spin _heavy_ events sit at ≤ 0.003 — sensitivity to the sourced
physics scales with in-band cycle count, not spin magnitude alone. The control
was stratified on the wrong variable; the mis-specification is preserved, not
re-thresholded. Remaining declared approximations: D3 (single effective spin —
catalog rows carry only χ_eff) and the Berti QNM conversion.

### 3.11 Study 8 — the Virgo extension (a preserved negative in two parts)

Adding V1 through the controlled instrument
(`2026-07-12-virgo-network-extension.md` + its v2 usability amendment — a loud
Virgo transient at noise-only SNR 49.3 in the first oracle segment forced the
standard absolute-scale screen onto V1 segment selection before any on-source
run) produced a clean preserved negative, registry exp_9449ac379daee2245b552011,
**contested**:

**The physics is visibly present but under the locked bar.** On the canonical
triple GW170814 the V1 peak sits at 3.68 just 6.2 ms from H1 (light-travel bound
27 ms) against a published V1 SNR of 4.8 — coincident real signal at ~77%
recovery, the same detection-grade fraction this pipeline produces everywhere —
but W2 locked an absolute 4.0. GW170818 (3.64 at 15.2 ms) and GW170729 (2.03 at
12.9 ms) show the same coincident pattern. Preserved, not re-thresholded.

**W1's assay was defective by construction.** The noise-null was computed over
the ~30 s off-source interior while the on-source search spans ±0.1 s — a
look-elsewhere mismatch that made the excess criterion unpassable for any
realistic signal (median excess −0.071, negative on all seven rows).
Protocol-defect class #1 (an assay never oracle-controlled in its exact
configuration) recurring despite the standing checklist — the null itself needed
the oracle, not just the injection path. The 3-det recovery values (0.79–0.97)
are therefore **not claims**; they ride noise inflation under the defective
null. A corrected iteration requires a window-matched, oracle-controlled null;
the coincident sub-threshold V1 peaks suggest it would find real but modest
Virgo contributions.

### 3.12 The fresh untouched holdout — a preregistered O3a cohort confirms the curve

The last open follow-up gate was the one §7 called a policy choice, not a
computation: freeze the template, tune nothing further, and evaluate exactly
once on events no study had touched. Executed 2026-07-16 (prereg
`2026-07-16-fresh-untouched-holdout.md`; artifact
`verification/fresh_untouched_holdout.json`; chronology validator-verified:
template locked 2026-07-14, cohort frozen 2026-07-16 23:05 UTC, single
evaluation 23:06–23:23 UTC). "Chronology validator-verified" here means
machine-checked **protocol-stage** ordering — template-lock ≺ cohort-freeze ≺
evaluation-start ≺ evaluation-complete, hash-bound per stage — which is a
different claim from output-chronology proofs such as TOPO's deterministic
hashing of analysis outputs (TOPO 2024, arXiv:2411.00072); the distinction and
the methodology prior art are stated in §8. The cohort is ten GWTC-2.1-confident **O3a** BBH
events selected by a deterministic preregistered rule, fully disjoint from the
31-event development manifest — every prior study used O1/O2 GWTC-1 and O3b
GWTC-3 events, so the holdout sits in an observing period the development
history never saw. Seven events were measured; three were excluded as
`data_unavailable` by the mechanical availability rule (GW190630_185205,
GW190910_112807, GW190708_232457). Evaluation is at catalog point estimates
with the locked GWTC-1-derived band predictor — the same point-estimate
conditioning that §3.4's posterior propagation shows is load-bearing for the
error criterion.

| Prediction (locked)               | Outcome                             |
| --------------------------------- | ----------------------------------- |
| O1: ρ(M_det, R) ≤ −0.5            | **ρ = −0.964** (p = 4.8×10⁻⁴) — pass |
| O2: median \|R − R̂(M_det)\| ≤ 0.15 | **0.129** — pass                    |

Outcome **`confirmed`**. The three heaviest events (GW190519_153544 at 153.6
M☉, GW190706_222641 at 181.4 M☉, GW190521 at 242.7 M☉) recover R = 0 —
consistent with the ISCO-below-band mechanism claimed since Study 1, and each
contributing its full 0.21 band error to O2, which passes anyway. This is the
strongest generalization evidence in the package: development-naive events, one
shot, both locked criteria met — at point estimates. The §3.4 posterior split
bounds the claim: the curve demonstrably transfers as a point-estimate tool; it
is not established as a posterior-robust predictor.

## 4. Limitations

(Positioned after the full results — Studies 1–8 — so the caveats attach to
everything above; an earlier version placed this before §3.5–3.11, which the
round-3 external review correctly flagged.)

- Detection-grade templates: no tidal terms, no 2PN+ spin corrections, no higher
  modes, no merger–ringdown; single-effective-spin approximation.
- Published network SNRs mix search pipelines and (some events) three detectors;
  we filter H1+L1 only. R is therefore **not directly commensurate** with the
  catalog network statistic: detector-network and pipeline differences (Virgo
  exclusion, independent per-detector peak maximization, PSD choice, glitches,
  differing waveform parameters and SNR conventions) bias R with **no guaranteed
  direction** — it is a descriptive benchmark, not a bounded lower estimate of a
  "true" recovery fraction. Its cross-event comparability inherits catalog
  conventions.
- The recovered "network SNR" is, until detector-time coincidence is enforced on
  a row, a **quadrature sum of independently maximized single-detector SNRs**
  (the H1 and L1 maxima within the ±0.1 s window may fall at incompatible
  times). All studies (1–2, 3, 6) are now coincidence-audited post hoc, and the
  mass trend is **robust to enforcing coincidence in every one** — the
  non-coincident rows are consistently the heavy events, and removing them holds
  or strengthens ρ: Studies 1–2 have 4/10 non-coincident (ρ −0.891→−0.886 and
  −0.903→−0.943), and Study 3 (OOS) has 6/17 non-coincident (all M > 96 M☉) with
  ρ −0.846→**−0.936** on the coincident subset. **The Study-3 denominator here is
  the availability-only diagnostic cohort — 20 seeded − 3 lacking clean H1+L1 =
  17 — which deliberately retains the 2 events that failed the off-source
  validity control. It is NOT the preregistered §3.4 inferential sample (15),
  where those 2 receive no verdict and are excluded. This audit is diagnostic: it
  asks whether the trend survives coincidence enforcement among events with usable
  data, and carries no preregistered claim. The §3.4 O1/O2 claims remain scoped to
  the 15-event validity-controlled cohort.** So the trend is not an artifact
  of non-coincident single-detector peaks in-sample or out-of-sample. Scripts
  `scripts/research/coincidence_audit_gwtc1.py` (Studies 1–2, from stored peak
  times) and `coincidence_audit_gwtc3.py` (Study 3, peak times recomputed via the
  confirm-path; positive control: recovered R reproduces the Study-3 receipt to
  0.0005); receipts `GWTC{1,3}_coincidence_audit_*.json`.
- PSD is estimated from the same 32 s segment as the signal (tutorial
  convention), 4 s Welch-mean. Per-event R **is** PSD-sensitive — a robustness
  sweep across mean-4s / median-16s / median-4s finds a median R spread of 0.076
  (largest on the glitchy heavy events: GW170729 0.164, GW170608 0.139) — so an
  individual R value should not be over-read. But the **mass trend is robust to
  PSD choice**: Spearman ρ(M, R) is −0.891 (mean-4s, = Study 1), −0.830
  (median-16s), −0.891 (median-4s); template truncation is not confounded with
  PSD behavior in the headline result. The Study-6 39σ transient — absorbed by
  the mean-4s estimator, exposed by median-16s — is the per-event sensitivity in
  action. Positive control: the mean-4s column reproduces the Study-1 receipt to
  max deviation 0.0005. Script `scripts/research/psd_robustness_sweep.py`, receipt
  `PSD_robustness_*.json`. The off-source/gated upgrade flagged in §6 item 2 is
  now **done and gate-passing** (prereg
  `2026-07-16-psd-robustness-artifact-regimes.md`, artifact
  `verification/psd_robustness.json`, receipt
  `PSD_robustness_20260716T154349Z.json`): the same ten GWTC-1 events under four
  locked regimes — on-source mean-4s, **off-source** mean-4s, on-source
  many-average median-4s, and **glitch-gated** on-source mean-4s — give
  Spearman ρ(M, R) = −0.891 / −0.830 / −0.891 / −0.891 (n = 10 each; positive
  control again 0.0005 vs the Study-1 receipt). The GW170817-derived glitch
  gate never fired on any GWTC-1 event (max in-window per-detector excursion
  3.3–9.8σ against the 15σ threshold), so the gated column is identical to
  on-source mean-4s by measurement, not by construction. The mass trend is not
  a PSD artifact under any locked regime.
- The efficacy curve is reported at fixed catalog point masses, but parameter
  **posterior uncertainty is now propagated** (`scripts/research/posterior_propagation.py`,
  receipt `POSTERIOR_prop_*.json`): per-parameter two-piece-normal marginals from
  the eventapi median + 90% CI, drawn 40× per event, with R recomputed per draw
  and ρ bootstrapped. Two honest consequences. (i) The reviewer's nonlinearity is
  real: the naive `(m̄₁+m̄₂)(1+z̄)` and the posterior-median M_det differ by up to
  3.3 M☉ per event. (ii) **The trend survives but weakens under uncertainty** —
  Spearman ρ(M, R) has posterior median **−0.65** and 90% CI **[−0.83, −0.31]**
  (excludes zero, but a small tail of realizations can flip), versus the point
  −0.891. So the mass decline is real but its effect size should carry this
  posterior width, not be quoted at the point value. Caveat: these are marginal
  (not joint) posteriors, which likely _overstate_ the M_det scatter by ignoring
  the m₁–m₂ anti-correlation — the joint PESummary posterior would tighten ρ back
  toward the point value. The `>100 M☉` predictor bin still rests on a single
  event, so its point is descriptive, not a stable binned estimate. The
  follow-up gate (2026-07-16, artifact `verification/posterior_uncertainty.json`)
  pushes the same machinery through the **Study-3 out-of-sample evaluation**
  with 100 joint cohort draws over the 15 measured events and recomputes both
  locked criteria per draw: O1 (ρ ≤ −0.5) holds in 98/100 draws, O2 (median
  |R − R̂| ≤ 0.15) in only 54/100 — an honest **fail** under the locked ≥ 90%
  rule, detailed in §3.4. The trend is posterior-robust; the point-prediction
  curve is not.
- R denominators are catalog-release-dependent: the GWTC-1 values trace exactly
  to the GWTC-1-confident release (verified live against GWOSC in review check
  V2), while the newest per-event versions (GWTC-2.1-era re-analyses) differ by
  3–6% on the O2 events. Under the newest values the Study-6 heavy median would
  be ≈0.87 instead of 0.902 — no conclusion changes. Future studies pin the
  catalog release string in the registry row.
- The transcribed phase is now checked against an **external implementation
  oracle** (LALSimulation IMRPhenomD, `lalsuite` in an isolated venv;
  `scripts/research/lal_oracle_compare.py`, receipt `LAL_oracle_*.json`) — the
  test a self-injection cannot do, since a shared convention error would pass
  every self-injection. Noise-weighted phase match (common amplitude, aLIGO
  design PSD) over a 5-point mass/spin grid: **median 0.9895, min 0.9620.**
  Non-spinning configs match to 0.996 with < 0.01 rad phase residual — the core
  coefficient transcription is correct. The match falls to ~0.96 at aligned spin
  χ ≈ 0.3–0.4 and the residual grows with χ, exactly tracking the declared
  1.5PN-only spin / single-χ_eff / anchor-QNM deviations — an approximation, not
  a bug. "Verifiably transcribed" is therefore externally backed for the
  non-spinning phase; the spin sector is a quantified approximation. The
  preregistered gate version of this check (2026-07-16, 13-point grid,
  `2026-07-16-phenomd-oracle-match-grid.md`, artifact
  `verification/phenomd_external_oracle.json`, floor 0.99) **fails honestly**:
  median 0.98864, minimum 0.91751 at (55+48 M☉, χ = 0.6), the merger-band RMS
  phase residual rising monotonically with χ from ≈ 0.01 rad to 0.69 rad. One
  non-spinning point also sits under the floor (0.9745 at 50+45 M☉ with
  < 0.01 rad residual) — a discrete-IFFT time-alignment limitation of the
  committed match metric, not a phase disagreement. That fail is preserved
  (receipt `LAL_oracle_20260716T113628Z.json`, commit 2203e431a) and drove the
  preregistered spin-sector completion retry
  (`2026-07-16-phenomd-oracle-spin-sector-retry.md`, committed before the run;
  grid, floor, and validator frozen): the completed two-spin 3.5PN aligned-spin
  transcription moves the same discrete-metric grid to min 0.97451 / median
  0.99791, and the preregistered sub-bin evaluation of the locked match removes
  the quantization — **min 0.99997 / median 0.99999, gate PASS** (2026-07-17,
  receipt `LAL_oracle_20260717T001009Z.json`; §3.6). The transcribed phase is
  externally validated on the frozen grid; the residual ~3×10⁻⁵ is consistent
  with the narrowed D2 (fitted QNM conversion vs LAL's Berti-table
  interpolation).
- Coherence is now characterized by an **ensemble null** (upgraded from the
  original single-realization control): 100 independent phase-scrambles per heavy
  GWTC-1 event (`scripts/research/ensemble_scramble_null.py`, receipt
  `ENSEMBLE_null_*.json`). Every one of the 7 events has its physical recovery
  above its _entire_ scramble distribution — R_physical 0.87–0.97 vs scramble
  max 0.26–0.51, margins 0.51–0.68 — so each event's one-sided empirical p is
  1/101 = 0.0099 (the floor at N=100). The added-band merger phase carries
  coherent signal, not a norm artifact.
- Studies 1–3 are single-pass by design (preregistered ceiling
  externally_grounded); the three named replications carry the within-project
  alternative-configuration reproduction claims.
- No external human expert has reviewed this work yet — the charter's §10
  requirement remains open, and this document is the artifact for it.

## 5. What the data says to build next

The heavy-event deficit is reduced, reproduced twice under alternative
pre-committed configurations — once raw, once glitch-immune (§3.6, §3.9) — the
pipeline carries a control-passing χ² veto with in-config injection discipline,
and the declared physics deviations D1/D2 are now closed with sourced
coefficients (§3.10), leaving recoveries at 0.85–0.97 across both mass classes.
The Virgo extension (§3.11) is a preserved negative: coincident sub-threshold V1
signal is visible on the triples, but a usable third-detector arm needs a
window-matched, oracle-controlled noise-null (and V1's glitchier data argues for
pairing it with the §3.8 χ² veto). The residual 2-det scatter is dominated by
catalog-release conventions (3–6%) and the remaining declared approximations (D3
two-spin, Berti QNM, higher modes). The six follow-up gates sharpened the
target list: the holdout confirmation (§3.12) closes the generalization
question at point estimates; the oracle fail named the spin-sector phase
deficit and the preregistered completion retry closed it (min match 0.918 →
0.99997 on the frozen grid, §3.6); and the posterior gate's withdrawn O2 curve
criterion — 54/100 joint draws, preserved as a withdrawn-claim record under
contract v3 (§3.4) — names the open lever: posterior-robust prediction.
Diminishing returns stand elsewhere: beyond that, the genuine levers are the
corrected Virgo iteration or a new scientific question on this controlled
instrument. Independent human expert review of this document remains
recommended (charter §10 note).

## 6. Referee response — round 2 (claim-strength corrections, 2026-07-12)

A second frontier-tier review pressed on claim strength. Source-checked and
applied to this write-up (the frozen preregistrations are **not** edited —
editing a pre-commitment would break its integrity; corrections live in the
paper's own prose):

- **"Out of sample" scoped to the one clean test.** Study 3 (seeded GWTC-3,
  untouched by Studies 1–2) was at this time the only genuine holdout (the
  2026-07-16 fresh untouched holdout, §3.12, has since added a second). The
  GWTC-3 heavy events
  reused across Studies 4–6 are relabelled a **cross-catalog development
  cohort**; the sourced-phase "0.857" is no longer called out-of-sample.
- **Network-SNR honesty.** The recovered statistic is, absent per-row
  coincidence, a **quadrature of independently maximized single-detector SNRs**;
  Studies 1–2 and Study 6 are coincidence-audited. Earlier incorrect timing
  wording is corrected to a 15 ms analysis window: the approximately 10 ms
  physical H1-L1 light-travel bound plus a named 5 ms coalescence-time margin
  (LIGO E950018-02; LIGO P1900004).
- **R is not "conservative"** — relabelled "not directly commensurate with the
  catalog network statistic; no guaranteed bias direction."
- **Causal language softened**: the merger–ringdown attribution is "consistent
  with," not "attributed to"; the single phase scramble is a "single-realization
  negative control," not an ensemble null.
- **"Independent replication / experimentally_validated"** downgraded to
  "within-project alternative-configuration reproduction" (the LIGO observations
  are the experiments; this package characterizes them computationally).

**Not yet done (honest open work, not silently claimed — status as written on
2026-07-12; all six items have since been executed as artifact-bound gates, all
six pass under contract v3 — the posterior gate on the O1 trend alone, its O2
curve fail preserved as a withdrawn-claim record — see the status header and
§1).** These are new
analyses, not text fixes, and are the gating items before any external use: (1)
an external waveform oracle — match the AIGIS template against
LALSimulation/PyCBC IMRPhenomD over a preregistered grid ("verifiably
transcribed" is fair; "validated implementation" is not, until this exists)
**— DONE as an arc: the first gate failed honestly (min 0.918, preserved), the
preregistered spin-sector completion retry passes (min 0.99997, §3.6)**; (2)
a PSD robustness sweep (off-source / many-average / gated vs the current
same-segment mean-4s), reporting the spread in R and ρ; (3) an ensemble
phase-scramble null (100–1000/event) for a per-event empirical p-value; (4)
parameter posterior-uncertainty propagation into R, ρ, and the predictor; (5)
per-row H1–L1 coincidence enforcement on Studies 1–3 **— DONE for all three
(trend robust to coincidence in-sample and OOS, see §4 and §7)**; (6) a fresh
untouched holdout before any further template change **— DONE 2026-07-16
(outcome `confirmed`, §3.12)**.
Positioning: this is a **computational characterization + reproducibility
package**, not independent experimental astrophysics; the methodological claim
is narrowed by the condition-1 literature review to the mechanized
_integration_ of the process discipline, "to our knowledge" only (§8) — every
individual component is in print — and there is no new physical result.

## 7. Referee response — round 3 (external audit, 2026-07-12)

A full external audit (8-dimension scorecard) reviewed the package. It is
largely **congruent with §6**: its five claim-strength findings (OOS scoping,
network-SNR honesty, "conservative" relabel, causal softening, replication
label) match §6's own corrections, and its "minimum remediation" list is §6's
six "not yet done" items almost item-for-item. Dispositions:

- **Accepted and now reconciled in the body.** The audit caught that §6
  _claimed_ the causal language was softened while §3.3 and §3.6 still read
  "attributed to" / "mechanistically confirmed" — a response asserting a fix the
  body did not carry (the exact self-certified-green failure this program exists
  to prevent). Both are now "consistent with" a differential localization, and
  the reused GWTC-3 "OOS" prediction labels in §3.5–3.6 carry an explicit
  cross-catalog note (the frozen preregs are left verbatim; the correction lives
  in the prose).
- **Accepted, structural.** §4 Limitations was mis-ordered before §3.5–3.11; it
  is now after the full results. §4 also now states the PSD confound, the
  posterior-uncertainty gap, the sparse `>100 M☉` predictor bin, the missing
  external oracle, and the single-realization scramble explicitly.
- **Based on an incomplete view — noted, not a defect of the work.** The audit
  scored "reproducibility verifiable from uploaded files 4/10" and stated the
  set lacks git history, run receipts, and scripts. Those exist in the
  repository: timestamped local receipts in `~/.aigis/research/gw_replication/`
  and the pipeline in `scripts/research/*.py`. The reviewer had the preprint,
  not the repo. The _valid_ core of the point stands for external submission:
  local receipts and git history are same-operator evidence and can be
  rewritten, so an immutable third-party archive (Zenodo/OSF) is the right
  upgrade before external circulation (§6 archive item).
- **Coincidence enforcement closed for all three studies (item 5).** The largest
  quantitative worry — that non-coincident single-detector peaks inflate the mass
  trend — was tested directly. Studies 1–2 from stored peak GPS times
  (`coincidence_audit_gwtc1.py`), Study 3 by recomputing peak times through the
  confirm-path (`coincidence_audit_gwtc3.py`, positive control 0.0005). Result:
  **the trend is robust everywhere.** The non-coincident rows are consistently the
  heavy events, and removing them holds or strengthens ρ(M, R): −0.886 (Study 1,
  from −0.891), −0.943 (Study 2, from −0.903), and −0.936 (Study 3 OOS, from
  −0.846; 6/17 non-coincident, all M > 96 M☉ — the 17 is the availability-only
  diagnostic cohort, 20 seeded − 3 lacking clean H1+L1, retaining the 2
  off-source-invalid events; the preregistered §3.4 inferential sample is the
  15-event validity-controlled cohort). The in-sample and out-of-sample
  mass trends both survive coincidence enforcement, as a diagnostic robustness
  check rather than a preregistered claim.
- **PSD confound tested — the mass trend is PSD-robust (item 2).** Recomputing R
  for all ten GWTC-1 events under mean-4s / median-16s / median-4s
  (`scripts/research/psd_robustness_sweep.py`, receipt `PSD_robustness_*.json`;
  positive control: mean-4s reproduces the Study-1 receipt to 0.0005) leaves
  Spearman ρ(M, R) at −0.891 / −0.830 / −0.891. Per-event R shifts (median spread
  0.076, largest on glitchy heavy events), so an individual R is PSD-sensitive —
  but the rank-order mass trend is not a PSD artifact.
- **External waveform oracle — transcription validated (item 1).** The AIGIS
  phase now matches LALSimulation IMRPhenomD to median 0.9895 (min 0.9620) over a
  mass/spin grid, and to 0.996 / < 0.01 rad in the non-spinning limit
  (`scripts/research/lal_oracle_compare.py`, `lalsuite` in an isolated venv). The
  spin-sector match drop to ~0.96 tracks the declared 1.5PN-only spin
  approximation. The core transcription is externally correct. (The subsequent
  preregistered 13-point gate sharpened this into a preserved fail — minimum
  match 0.918 at χ = 0.6 against the 0.99 floor — whose diagnosis then drove the
  preregistered spin-sector completion retry that passes the same frozen grid
  at min 0.99997; §3.6 and §4.)
- **Posterior-uncertainty propagation — trend survives, weaker (item 4).**
  Propagating per-parameter marginal posteriors (eventapi median + 90% CI, 40
  draws/event, R recomputed per draw; `scripts/research/posterior_propagation.py`)
  gives Spearman ρ(M, R) posterior median −0.65, 90% CI [−0.83, −0.31] (excludes
  zero) — the mass decline is real but the point −0.891 overstates its strength,
  and naive vs posterior-median M_det differ up to 3.3 M☉. This is the one check
  that widens rather than sharpens the claim (marginal posteriors likely overstate
  the scatter; the joint PESummary posterior would tighten it) — and it is now in
  the abstract and §4.
- **Remaining open compute work.** One item: a fresh untouched holdout, gated on a
  policy decision to freeze the template and tune no further — not a computation.
  (Since executed, 2026-07-16: template frozen 2026-07-14, cohort frozen and
  evaluated once 2026-07-16, outcome `confirmed` — §3.12.) The audit's Paper A
  (focused characterization) / Paper B (implementation + methods) split is
  accepted as the target structure for the external version.

Net: the audit changed no result. It corrected residual body language that
over-stated three things (independence of the reused-cohort evidence, the
network statistic, and the spin→phase causal chain), and all six of its compute
checks are now run. Five **confirmed the core claims survive**: the mass trend
holds under coincidence enforcement in every study (item 5: −0.886/−0.943
in-sample, −0.936 OOS) and across PSD estimators (item 2: −0.891/−0.830/−0.891),
the merger-phase coherence beats its full ensemble null (item 3: all 7 heavy
events at p = 0.0099), and the transcribed phase matches the LALSimulation
reference in the non-spinning core (item 1: median 0.99, non-spinning to
< 0.01 rad; the later preregistered 13-point gate first failed at the 0.99
floor and, after the preregistered spin-sector completion, passes at min
0.99997 — §3.6). The sixth (item 4)
sharpened the honesty rather than the claim: the mass trend survives parameter
uncertainty (ρ posterior 90% CI [−0.83, −0.31]) but is weaker than the point
value. Only a fresh holdout remained at the time of this response; it has since
been executed and **confirmed** (2026-07-16, §3.12). That completes all six
follow-up gates — all six now pass under contract v3 (the posterior gate on the
O1 trend alone, its O2 curve fail preserved as a withdrawn-claim record, §3.4;
the oracle's initial fail was closed by the preregistered completion retry,
§3.6) — and the readiness auditor reports `analysis_ready_for_external_review`
(external publication still blocked on an external trust anchor). The honest
positioning already in §6 stands — a computational
reproducibility package, not independent experimental astrophysics.

## 8. Relation to prior work (condition-1 literature positioning)

A two-pass prior-art review
([`literature-positioning.md`](literature-positioning.md), policy "err toward
finding prior art") found that **no claim of this paper is cleanly novel as a
relationship or mechanism**; what survives is the specific measurement, the
event-level verification, the single-term attribution, and the mechanized
integration of the process discipline. This section states the anticipation
honestly, claim by claim.

**The mass trend is a re-measurement of an anticipated relationship.**
Flanagan & Hughes 1998 (gr-qc/9701039) derived the monotonic decline of the
inspiral SNR share in this paper's exact regressor — detector-frame total mass
(1+z)M; Damour, Iyer & Sathyaprakash 2001 (gr-qc/0010009) quantified that
inspiral-only PN templates lose significant SNR above m ≳ 30 M☉; Buonanno et
al. 2009 (arXiv:0907.0700) made the degradation established search-design
doctrine; Buonanno, Cook & Pretorius 2007 (gr-qc/0610122), Cho 2015
(arXiv:1502.04399), and Graff et al. 2015 (arXiv:1504.04766) demonstrated it
in simulations and injections; Smith, Mandel & Vecchio 2013 (arXiv:1302.6049)
quantified it regime-level on simulated populations; and Sampson, Cornish &
Yunes 2013 (arXiv:1311.4898) tabulated theoretical pre-ISCO SNR percentages
against total mass. The closest real-event quantitative relatives are the LVK
inspiral/post-inspiral consistency tests: GWTC-1 TGR (arXiv:1903.04467, Table
3 — the earliest catalog-wide per-event inspiral-SNR tabulation), GWTC-2 TGR
(arXiv:2010.14529, Sec. IV B / Table IV), and GWTC-3 TGR (arXiv:2112.06861,
Table IV) tabulate per-event inspiral, post-inspiral, and full-signal SNRs
catalog-wide, using the ISCO-frequency split originated by Ghosh et al. 2017
(arXiv:1704.06784); GWTC-4.0 TGR I (arXiv:2603.19019) is now the
authoritative per-event low/high-frequency SNR source, extending the test to
91 events including O4a (13 with tabulated inspiral SNRs). Those tables
operationally encode the declining inspiral-fraction trend catalog-wide — a
reader can form an inspiral-SNR fraction for essentially this paper's event
set from published numbers — and this paper claims no first catalog-wide
per-event inspiral-SNR measurement. R remains a different statistic answering
a different question: the TGR inspiral SNR is a low-frequency restriction of
the **same** IMR waveform (the Ghosh remnant-ISCO cutoff), built to estimate
GR consistency, whereas R uses an **independent** inspiral-only 3.5PN
TaylorF2 template with independent per-detector maximization, normalized by
the published catalog network SNR, to quantify empirical recovery — and
neither GWTC-4 TGR paper computes a recovery fraction, an R-vs-mass
correlation, or a preregistered holdout transfer (none touches the GWTC-2.1
fresh holdout). A decade review of GW tests of GR (Gupta et al.,
arXiv:2511.15890) surveys ten years of such tests with no R-like statistic
appearing — a completeness check consistent with the narrow claim. Chia et
al. 2023 (arXiv:2306.00050) is the direct methodological
precedent for running inspiral-only templates against real LIGO-Virgo strain
and recovering cataloged events; that workflow is not presented as new here.
Data sources: GWTC-1 (arXiv:1811.12907), GWTC-2.1-confident (holdout cohort),
GWTC-3 (arXiv:2111.03606); independent catalog analyses of the same strain
exist (4-OGC, arXiv:2112.06878; Olsen et al. 2022, arXiv:2201.02252).

**The heavy-event mechanism is textbook; the verification is the
contribution.** The deficit is the missing merger–ringdown share of the
standard IMR energy budget (Flanagan & Hughes 1998, three-phase
decomposition); Phenom-family phasing (Ajith et al. 2007, arXiv:0704.3764) was
invented precisely to cure it; the ISCO/ringdown-vs-band-floor argument is
Hanna et al. 2008 (arXiv:0801.4297); the inspiral-only-bank validity boundary
was a design criterion in Brown, Kumar & Nitz 2012 (arXiv:1211.6184); and
real-data searches were built on this exact premise (LVC 2013,
arXiv:1209.6533). What this paper adds is the event-level closure on real
catalog events — the quantified heavy-event median recovery 0.438 → 0.902 from
restoring source-transcribed, oracle-validated Phenom-type phasing on the same
events, rather than on injections (contrast Graff et al. 2015 and Cho 2015,
which are simulation-only).

**The GW151226 spin result narrows to single-term attribution.** That
GW151226's recovery requires spin is in the discovery paper (Abbott et al.
2016, arXiv:1606.04855: nonzero aligned spin, ~55 in-band cycles), and Capano
et al. 2016 (arXiv:1602.03509) showed aligned-spin templates recover the most
SNR at low mass; the PN-term sensitivity of TaylorF2 phasing is Buonanno et
al. 2009. This paper claims only single-term sufficiency: exactly one 1.5PN
aligned spin-orbit term, under locked differential predictions with
near-zero-spin controls (§3.3) — narrower and sharper than the family-level
results above, and not a discovery that spin matters.

**The methodology claims the mechanized integration only, and only "to our
knowledge."** Blind and frozen analysis is standard physics practice,
including on LIGO data (Klein & Roodman 2005, Ann. Rev. Nucl. Part. Sci. 55,
141); LVK pipelines embody fix-before-unblinding conventions (LVC 2013);
hash-recorded code identity in GW reproduction exists (Brown et al. 2020,
arXiv:2010.07244, PyCBC version pinned by hash reproducing GW150914);
machine-verifiable **output** chronology exists in cosmology (TOPO 2024,
arXiv:2411.00072, deterministic hashing + Merkle trees — proving output order,
which is a different claim from this package's machine-checked
**protocol-stage** order, template-lock ≺ cohort-freeze ≺ evaluation); and the
manual analog of the chronology check exists without mechanization (Kraegeloh
et al. 2026, doi:10.1080/29974100.2026.2639409). The nearest prior
methodological neighbor is the PRIMAD-LIGO applicability study
(arXiv:1904.05211) — an abstract reproducibility-taxonomy mapping onto LIGO
analyses, not a mechanized system. The final residual-venue pass (receipt,
addendum 2) swept the methodology venues directly — W3C PROV, registered
reports, ACM REP / RDA, and the closest new relative, LLM workflow-provenance
agents (arXiv:2509.13978, interactive provenance querying that instantiates
none of the claimed integration) — and found no source combining
machine-validated multi-stage lock ordering with hash-bound receipts,
preserved negatives, and external-oracle validation in GW data analysis. That
integration is claimed "to our knowledge" only, with the qualifier
load-bearing: methodology work scatters across venues, and non-English,
paywalled-only, and LVK-internal literatures remain unswept.

**What this paper claims as novel, verbatim:** (1) the R statistic as defined
— quadrature of independently maximized H1/L1 inspiral-only 3.5PN TaylorF2
SNRs over the published catalog network SNR — measured per event on real
catalog events across three catalogs, with its specific values and
correlations (ρ ≈ −0.89 / −0.87 / −0.96); (2) the preregistered out-of-sample
and fresh-holdout transfer of that curve; (3) the event-level closure of the
mechanism loop on real data (0.438 → 0.902); (4) the single-term GW151226
attribution under locked differentials; and (5) to our knowledge, the
mechanized verification integration. All five held against the final
residual-venue pass (receipt, addendum 2), which swept GWTC-4-era TGR, thesis
repositories, DCC/proceedings, and the methodology venues. Residual scoop
risk is assessed there as **LOW** for the measurement claims (the LVK venues
where a scoop would appear are swept) and **LOW-MODERATE** for the
methodology claim (methodology work scatters across venues — the "to our
knowledge" hedge is retained for exactly this reason); honestly unswept:
non-English literature, paywalled journal-only papers, LVK-internal DCC
documents, and anything posted after the July 2026 sweep snapshot.
