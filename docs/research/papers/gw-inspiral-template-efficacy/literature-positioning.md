# Literature-Positioning Memo — "Inspiral-only matched-filter efficacy across the GWTC catalogs"

**Purpose:** Condition 1 (Novel) input for the AIGIS Discovery Standard. Policy
applied: err toward finding prior art. All citations below are from the verified
prior-art table only.

---

## 1. Verdict per claim

| Claim                                                                                  | Verdict                                                                                                                                                                                                                                                                              | Deciding citations                                                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1 (R-vs-mass decline, cross-catalog)                                                  | **Partially anticipated** — direction, mechanism, and approximate shape predicted and simulated for 25+ years; only the specific statistic on real catalog events is new                                                                                                             | Flanagan & Hughes 1998 (arxiv.org/abs/gr-qc/9701039); Damour, Iyer & Sathyaprakash 2001 (gr-qc/0010009); Buonanno, Cook & Pretorius 2007 (gr-qc/0610122); Cho 2015 (1502.04399); Graff et al. 2015 (1504.04766); LVC TGR 2019 (1903.04467); Chia et al. 2023 (2306.00050) |
| C2 (missing merger-ringdown mechanism; PhenomD phase recovers R)                       | **Anticipated as a mechanism claim.** This is the standard IMR picture; the fix C2 applies (Phenom phasing) was invented in 2007–08 precisely to cure this deficit. Only the event-level demonstration on real GWTC events (0.438 → 0.902) is new                                    | Flanagan & Hughes 1998; Damour et al. 2001; Ajith et al. 2007/2008 (0704.3764); Hanna et al. 2008 (0801.4297, ISCO/ringdown band estimates); Brown, Kumar & Nitz 2012 (1211.6184)                                                                                         |
| C3 (single 1.5PN aligned-spin term explains GW151226)                                  | **Partially anticipated** — that aligned-spin phasing recovers SNR, most strongly at low mass, and that GW151226 specifically requires spin, are both in print                                                                                                                       | Capano et al. 2016 (1602.03509); GW151226 discovery (1606.04855); Buonanno et al. 2009 (0907.0700)                                                                                                                                                                        |
| C4 (preregistration, machine-validated chronology, hash receipts, preserved negatives) | **Novelty NOT established — search gap.** LVC pipelines embody fix-before-unblinding conventions (1209.6533; 1903.04467 partially anticipate), and the table contains zero coverage of the blind-analysis / preregistration / metascience literature. Treat as unverified, not novel | LVC 2013 (1209.6533); LVC TGR 2019 (1903.04467)                                                                                                                                                                                                                           |

**Bottom line:** no claim is cleanly novel as currently phrased. C1 survives
only as a _measurement/confirmation_ claim; C2 survives only as a
_demonstration_; C3 survives as a narrow attribution result; C4 cannot be
claimed novel until the methodology literature is searched.

## 2. Required citations and sentence-level repositioning

**C1 — must cite:** Flanagan & Hughes 1998; Damour et al. 2001; Buonanno et al.
2007; Buonanno et al. 2009; Brown et al. 2012; Cho 2015; Graff et al. 2015; Chia
et al. 2023; LVC TGR 2019; plus data sources GWTC-1 (1811.12907), GWTC-3
(2111.03606), 4-OGC (2112.06878), Olsen et al. 2022 (2201.02252).

- Any sentence of the form "we find/discover that inspiral-only recovery
  declines with total mass" must become "we quantify on real catalog events the
  decline long predicted analytically and in injections (Flanagan & Hughes 1998;
  Damour et al. 2001; Buonanno et al. 2007; Graff et al. 2015)."
- Chia et al. 2023 must be cited as the direct methodological precedent for
  running inspiral-only templates against real LIGO-Virgo strain and recovering
  cataloged events; the paper cannot present that workflow as new.
- LVC TGR 2019's low/high-frequency IMR consistency test is the closest
  real-event quantitative relative of R on the same GWTC-1 events; the paper
  must cite it and state explicitly how R differs (per-detector maximized
  inspiral-only SNR ratio vs. posterior-based parameter-consistency test) —
  otherwise reviewers will read C1 as a rediscovery of Sec. V B of 1903.04467.
- Damour et al. 2001 already quantified that inspiral-only PN templates lose
  significant SNR above m ≳ 30 M☉; the paper's mass threshold framing must
  acknowledge this number.

**C2 — must cite:** Flanagan & Hughes 1998 (three-phase SNR decomposition);
Ajith et al. 0704.3764 (the Phenom family used as the fix); Hanna et al.
0801.4297 (ISCO/ringdown frequency vs. band-floor argument); Brown et al. 2012
(inspiral-only bank validity boundary as a design criterion); LVC 2013
(1209.6533, real-data search built on this exact premise).

- "We localize the mechanism to the missing merger-ringdown" must be rewritten
  as "the deficit is consistent with the standard IMR energy budget (Flanagan &
  Hughes 1998); we verify this event-by-event on real catalog data by restoring
  Phenom-type phasing (Ajith et al.)." The mechanism is textbook; only the
  verification is the contribution.

**C3 — must cite:** 1606.04855 (GW151226: spin measurably nonzero, ~55 cycles in
band); Capano et al. 1602.03509 (aligned-spin templates recover most SNR at low
mass — the same effect, in a search context); 0907.0700 (PN-term sensitivity of
TaylorF2 phasing).

- Claim only single-term sufficiency under the locked differential protocol; do
  not claim discovery that spin matters for GW151226.

**C4 —** cite 1209.6533 and 1903.04467 as examples of
fixed-pipeline/blind-search practice in the field, and either (a) downgrade C4
from a novelty claim to a methods description, or (b) hold the claim until a
dedicated preregistration/blind-analysis literature search is done.

## 3. What genuinely remains novel (narrow, defensible statements)

1. **The R statistic itself, measured on real events:** R = (quadrature sum of
   independently maximized H1/L1 inspiral-only 3.5PN TaylorF2 SNRs) / (published
   catalog network SNR), computed per event across GWTC-1, with the specific
   values (R ≈ 0.88 at 20 M☉ → ≈ 0.21 at 125 M☉; Spearman ρ ≈ −0.89). No table
   entry contains this measurement.
2. **Preregistered out-of-sample transfer** of that curve to GWTC-3 (ρ ≈ −0.87)
   and a fresh GWTC-2.1 holdout (ρ ≈ −0.96). Cross-catalog replication of an
   inspiral-deficit curve appears in no entry.
3. **Event-level closure of the mechanism loop on real data:** the quantified
   heavy-event median recovery 0.438 → 0.902 from adding sourced Phenom-type
   phasing to the same events, rather than injections (contrast Graff et al.
   2015, Cho 2015 — simulation only).
4. **Single-term attribution for GW151226:** that exactly one 1.5PN aligned-spin
   phase term, under locked differential predictions, accounts for the low-mass
   outlier — narrower and sharper than Capano et al.'s family-level result.
5. Possibly the machine-validated chronology + hash-bound receipt packaging (C4)
   — but claim it only as "to our knowledge" pending the missing methodology
   search.

## 4. Search limitations (honest)

- **Venues:** essentially arXiv/ar5iv/journal PDFs plus one GitHub tutorial. No
  systematic ADS/INSPIRE-HEP sweep, no Google Scholar, no LIGO DCC technical
  notes, no conference proceedings (Amaldi, GWPAW), no textbooks, and — highest
  risk — **no PhD theses**, where exactly this kind of catalog-wide
  inspiral-only recovery exercise is plausibly already done.
- **Recency:** the table's newest entries are 2023. arXiv 2024–2026 was not
  covered; GWTC-2/GWTC-3 Tests-of-GR papers, which extend the 1903.04467
  IMR-consistency test to heavier events, were not checked and are the most
  likely place C1 is partially scooped.
- **Pipeline-methods gap:** PyCBC/GstLAL/MBTA methods papers and template-bank
  construction papers beyond Brown et al. 2012 were not surveyed;
  inspiral-vs-IMR bank tradeoffs are working knowledge in that literature.
- **Adjacent-physics gaps:** ringdown-only searches,
  higher-harmonics/mode-content literature, IMBH search papers (which live
  exactly in the "band floor swallows the inspiral" regime) not covered.
- **C4 gap:** zero coverage of preregistration, registered reports, or
  blind-analysis-in-physics literature; C4's novelty verdict is therefore a
  non-finding, not a clearance.
- **The GWTC-2.1 catalog paper itself** (holdout data source) is absent from the
  table.
- **Candidate-generation noise observed:** one entry conflated two citations
  (0801.4297 attributed to Mandel et al.; actual paper is Hanna et al.), and the
  Ajith entry's PRD number belongs to a companion paper — the assessed texts
  were verified, but this indicates the candidate list was noisy and coverage
  should not be presumed complete.
- Depth caveat: several verdicts rest on abstracts plus partial text (e.g.,
  GWTC-3 assessed from abstract only); "adjacent_only" for those is
  lower-confidence than for fully read entries.

**Recommendation for the Discovery Standard gate:** condition 1 passes only for
the narrow statements in §3, items 1–4, with the §2 repositioning applied; C4
novelty must be withheld or a supplementary methodology-literature search run.
Basis stamp: 20-entry verified prior-art table, evidence-checked sources only.

---

# ADDENDUM — TGR-Catalog, 2024–26 Follow-up, and C4 Methodology Pass (2026-07-16)

Closes open items (a) and (c); item (b) partially closed. All citations below
were read against real full texts.

## 1. C1 updated verdict: NOT scooped, but partial anticipation is now materially heavier — narrow the claim

The highest-risk gap (a) is retired, at a cost. GWTC-2 TGR
([arXiv:2010.14529](https://arxiv.org/abs/2010.14529), Sec. IV B/Table IV) and
GWTC-3 TGR ([arXiv:2112.06861](https://arxiv.org/abs/2112.06861), Table IV)
tabulate **per-event** inspiral, post-inspiral, and full-signal SNRs (ρinsp,
ρpostinsp, ρIMR) across GWTC-1+O3a and GWTC-3 — a reader can form an
inspiral-SNR fraction for essentially C1's event set from published numbers.
GWTC-1 TGR ([arXiv:1903.04467](https://arxiv.org/abs/1903.04467), Table 3) does
the same for O1/O2; Ghosh et al. 2017
([arXiv:1704.06784](https://arxiv.org/abs/1704.06784)) originates the
ISCO-frequency inspiral/post-inspiral split. Separately, Buonanno et al. 2009
([arXiv:0907.0700](https://arxiv.org/abs/0907.0700)) makes the **qualitative**
claim (inspiral-only 3.5PN templates degrade with total mass, ~12 Msun
threshold) established search-design doctrine; Flanagan & Hughes 1998
([arXiv:gr-qc/9701039](https://arxiv.org/abs/gr-qc/9701039)) derives the
monotonic inspiral-share decline in C1's **exact regressor**, detector-frame
(1+z)M; Smith, Mandel & Vecchio 2013
([arXiv:1302.6049](https://arxiv.org/abs/1302.6049)) quantifies it regime-level
on simulated populations. The 2024 IMRCT follow-ups checked
([arXiv:2405.05884](https://arxiv.org/abs/2405.05884),
[arXiv:2402.15110](https://arxiv.org/abs/2402.15110)) are adjacent-only — no
scoop. **Verdict: partially anticipated, more deeply than the prior memo held.**
What survives is only the specific measurement: the R statistic as defined
(independently maximized per-detector H1/L1 inspiral-only 3.5PN TaylorF2 SNR in
quadrature over **catalog network SNR**), its per-event correlation across real
catalogs (rho −0.89 / −0.87 / −0.96 holdout), and the preregistered
holdout-transfer design. C1 must be reframed as a quantified, cross-catalog
re-measurement of an anticipated relationship — not a new relationship.

## 2. C4 first verdict: partially anticipated — every component is in print somewhere; only the integration is novel

- **Freeze-before-evaluation / preregistration / blind analysis, already applied
  to LIGO data**: Klein & Roodman 2005
  ([ADS](https://ui.adsabs.harvard.edu/abs/2005ARNPS..55..141K/abstract)).
  Deciding citation against any "first frozen-analysis discipline in GW"
  reading.
- **Hash-bound code-identity receipts in GW analysis**: Brown et al. 2020
  ([arXiv:2010.07244](https://arxiv.org/abs/2010.07244)) recorded PyCBC version
  by hash reproducing GW150914. Deciding citation against "first hash receipts
  in GW."
- **Machine-verifiable time-ordering of outputs**: TOPO 2024
  ([arXiv:2411.00072](https://arxiv.org/abs/2411.00072)), deterministic
  hashing + Merkle trees — but cosmology-MCMC, and it proves output chronology,
  not protocol-stage ordering.
- **Manual analog of the chronology check**: Kraegeloh et al. 2026
  ([doi:10.1080/29974100.2026.2639409](https://www.tandfonline.com/doi/full/10.1080/29974100.2026.2639409))
  — human-verified timestamping; sharpens "machine-validated" as C4's operative
  adjective.
- Adjacent-only: PRIMAD applicability
  ([arXiv:1904.05211](https://arxiv.org/abs/1904.05211)), prediction scoring
  ([arXiv:2211.10314](https://arxiv.org/abs/2211.10314)). **Verdict: partially
  anticipated.** No found source combines machine-validated multi-stage lock
  ordering (template-lock ≺ cohort-freeze ≺ evaluation) with hash-bound
  receipts, preserved negatives, and external-oracle validation in GW data
  analysis. C4 may claim the mechanized integration only — no individual
  component.

## 3. Newly required citations and the sentence-level repositioning each forces

1. **2010.14529 + 2112.06861**: delete any sentence implying per-event
   inspiral/post-inspiral SNRs are unreported catalog-wide; replace with an
   explicit differencing sentence — R differs by independent per-detector
   maximization, fixed inspiral-only 3.5PN TaylorF2, and network-SNR
   normalization, and the mass-trend quantification is not performed there.
2. **1903.04467**: promote from "closest relative" to one of three TGR anchors;
   cite Table 3 explicitly.
3. **1704.06784**: credit Ghosh et al. for the inspiral/post-inspiral
   decomposition mechanism wherever the split is described.
4. **0907.0700**: recast the direction/threshold sentence as "consistent with
   established template-family doctrine (Buonanno et al. 2009)"; no
   new-qualitative-finding language anywhere.
5. **gr-qc/9701039**: the theory paragraph must state Flanagan & Hughes derived
   the monotonic decline in detector-frame total mass — C1's contribution is
   empirical per-event quantification on real catalog events.
6. **1302.6049**: any "first quantification" sentence must be qualified:
   regime-level simulated quantification exists; C1's is per-event on detected
   events with holdout transfer.
7. **Klein & Roodman 2005**: C4's introduction must position blind/frozen
   analysis as standard physics practice including LIGO; C4 claims
   mechanization, not the discipline.
8. **2010.07244**: the receipts sentence must acknowledge hash-recorded code
   identity in GW reproduction; C4's claim narrows to binding receipts to lock
   stages.
9. **2411.00072**: cite TOPO wherever "machine-validated chronology" appears,
   with the output-order vs. protocol-stage-order distinction stated in-text.
10. **Kraegeloh et al. 2026**: cite as the manual analog demonstrating the
    practice exists without mechanization.

## 4. Remaining search limitations after this pass

- **2025–2026 arXiv not swept**: an O4-era/GWTC-4 TGR paper would tabulate the
  same per-event SNRs on new events; residual scoop risk on the GWTC-2.1-holdout
  framing and on any newer inspiral-fraction analysis. Highest remaining
  priority.
- **Theses still unsearched** (open item b only half-closed: 2024 arXiv
  follow-ups checked; no thesis repositories, no LVK technical documents/DCC, no
  conference proceedings).
- **C4 search bounded** to
  reproducibility/preregistration/blind-analysis/timestamping;
  software-provenance standards (W3C PROV, workflow systems), registered-reports
  literature, and computational-science venues (ACM REP, RDA) unchecked —
  plausible further partial anticipations of the chronology-verifier idea.
- Journal-only and non-English literature beyond the URLs above not swept;
  verdicts rest on the provided sources only.

---

# ADDENDUM 2 — Final residual-venue pass (2026-07-17)

Venues now swept: 2025–26 arXiv / GWTC-4-era TGR, theses–DCC–proceedings, and
the C4 methodology venues (W3C PROV, registered reports, ACM REP / RDA). Twelve
candidates verified against full texts. **No candidate scoops the surviving
narrow claims; two partially anticipate and force citation changes (Sec. 3).**

## 1. C1 — final verdict: SURVIVES, further narrowed

The GWTC-4.0 TGR suite (Paper I,
[arXiv:2603.19019](https://arxiv.org/abs/2603.19019); Paper II,
[arXiv:2603.19020](https://arxiv.org/abs/2603.19020); Paper III on remnants is
off-topic) extends the standard IMR-consistency low/high-frequency SNR split to
91 events including 42 O4a events (13 with tabulated inspiral SNRs). Verified
from Paper I: its inspiral SNR is a low-frequency restriction of the _same_ IMR
waveform (Ghosh et al. remnant-ISCO cutoff) — **not** AIGIS's independent
per-detector inspiral-only 3.5PN TaylorF2 SNR, maximized in H1/L1 and normalized
by catalog network SNR. Neither paper computes a recovery fraction R, an
R-vs-detector-frame-total-mass correlation, or a preregistered cross-catalog
holdout transfer, and neither touches the GWTC-2.1 fresh holdout. Chandra &
Bustillo ([arXiv:2607.07070](https://arxiv.org/abs/2607.07070)), GW250114
spectroscopy ([arXiv:2509.08099](https://arxiv.org/abs/2509.08099)), and the
Gupta decade review ([arXiv:2511.15890](https://arxiv.org/abs/2511.15890)) are
adjacent only; the review mildly _strengthens_ C1 as a completeness check (no
R-like statistic appears in ten years of surveyed tests). Historical anchors
confirm the already-conceded background, not the statistic: Flanagan & Hughes
([gr-qc/9701039](https://arxiv.org/abs/gr-qc/9701039)) for the general
inspiral-SNR-declines-with-mass physics; Sampson–Cornish–Yunes
([arXiv:1311.4898](https://arxiv.org/abs/1311.4898)) tabulates theoretical
pre-ISCO SNR percentages vs total mass, not per-event measurements on real
strain; McWilliams–Kelly–Baker
([arXiv:1004.0961](https://arxiv.org/abs/1004.0961)) background only; TGR GWTC-1
([arXiv:1903.04467](https://arxiv.org/abs/1903.04467)) is the earliest
catalog-wide per-event inspiral-SNR tabulation but with a materially different
construction on every surviving axis.

**Surviving C1 novelty (final form):** the specific R statistic (independent
H1/L1 inspiral-only 3.5PN TaylorF2 quadrature SNR / catalog network SNR), its
per-event cross-catalog quantification of the R-vs-mass relationship on
GWTC-1/GWTC-3, and the preregistered GWTC-2.1 holdout transfer. The
declining-inspiral-fraction _relationship itself_ is anticipated (conceded since
revision d66eddd5b) and now has an authoritative O4-era instantiation that must
be differenced explicitly.

## 2. C4 — final verdict: SURVIVES intact ("to our knowledge" holds)

The closest new relative, LLM workflow-provenance agents
([arXiv:2509.13978](https://arxiv.org/abs/2509.13978)), is a reference
architecture for _interactive provenance querying_ — it instantiates none of the
claimed integration (multi-stage lock ordering template-lock < cohort-freeze <
evaluation, hash-bound receipts, preserved negatives, external-oracle
validation). The PRIMAD–LIGO applicability study
([arXiv:1904.05211](https://arxiv.org/abs/1904.05211)) is an abstract taxonomy
mapping, not a mechanized system, and arguably strengthens C4 as the nearest
prior methodological neighbor. No W3C PROV / registered-reports / REP-RDA
candidate mechanizes the combination.

## 3. Newly required citations / repositioning

- **Must cite + explicitly difference:** GWTC-4.0 TGR I (2603.19019) — now the
  authoritative per-event low/high-frequency SNR source, incl. O4a; state that
  AIGIS's R is a different statistic (independent inspiral-only template vs
  same-waveform frequency restriction) answering a different question (empirical
  recovery quantification vs GR consistency).
- **Must cite as closest prior art, soften one leg:** TGR GWTC-3
  ([arXiv:2112.06861](https://arxiv.org/abs/2112.06861)) — its per-event
  inspiral SNRs operationally encode the declining trend catalog-wide; C1's
  framing should not imply first catalog-wide per-event inspiral-SNR
  measurement.
- **Should cite:** Flanagan & Hughes (gr-qc/9701039) as the canonical anchor for
  the anticipated physics; 1311.4898 for the theoretical mass-dependence tables;
  1904.05211 in C4 related work; 2511.15890 as the completeness-check review.
- **Erratum:** the internal candidate ledger misattributes arXiv:1004.0961 to
  "Reisswig et al."; it is McWilliams, Kelly & Baker (2010). Correct before any
  citation lands in the memo.

## 4. Honestly unswept after this pass

- Non-English literature (Chinese, Japanese, Russian GW-group journals and
  theses without arXiv mirrors).
- Paywalled journal-only papers with no arXiv preprint; conference talks/posters
  with no written proceedings.
- LVK-internal technical notes and access-restricted DCC documents; GWTC-4
  companion papers still in preparation.
- Anything posted after the July 2026 sweep snapshot; non-arXiv preprint servers
  (Zenodo, HAL) beyond incidental hits.
- Residual risk assessed LOW for C1 (LVK venues are where a scoop would appear;
  both swept) and LOW-MODERATE for C4 (methodology work scatters across venues;
  the "to our knowledge" hedge is retained for exactly this reason).
