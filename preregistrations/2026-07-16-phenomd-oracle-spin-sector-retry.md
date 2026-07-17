# Preregistration: PhenomD oracle spin-sector retry (follow-up to the preserved negative)

**Program:** CHARTER G3 track, verification package - external waveform oracle
retry **Preregistered:** 2026-07-16 (committed before the retry run)
**Follow-up to:** the preserved honest FAIL of 2026-07-16 (receipt
`~/.aigis/research/gw_replication/LAL_oracle_20260716T113628Z.json`, committed
at 2203e431a: min match 0.91751 / median 0.98864 vs floor 0.99) **Grid
authority:**
`docs/research/preregistrations/2026-07-16-phenomd-oracle-match-grid.md`
(FROZEN - not modified by this document)

## What is frozen (unchanged, restated for clarity)

- The 13-point grid, exactly as locked in the grid preregistration.
- Match floor 0.99 (`MIN_ORACLE_MATCH`); pass iff min(match) >= 0.99.
- `comparison_mode = exact_phenomd`; backend lalsimulation (isolated
  `~/.aigis/research/lal_venv`, lalsimulation 6.2.1); common LAL amplitude;
  analytic aLIGO ZeroDetHighPower PSD; f_low = 20 Hz, df = 0.125 Hz; both
  phase-sign conventions tried, better kept.
- The validator (`gw_evidence_controls.validate_oracle_artifact`) and the
  readiness auditor. No criteria, threshold, or grid edits.

What legitimately changes here is the IMPLEMENTATION (completing the spin
sector of the sourced transcription) and, explicitly preregistered below, the
numerical evaluation of the already-locked "maximized over time" metric.

## Diagnosis carried from the fail receipt (what the retry targets)

The preserved negative has two characterized causes:

1. **Spin sector (D1/D3):** the oracle path
   (`phenomd_phase.phenomd_psi`) uses the 1.5PN-only single-chi_eff
   `taylorf2.taylorf2_phase_35pn`. Inspiral phase residual after linear
   alignment grows monotonically with |chi_eff|: 0.15 rad (chi=0.2) -> 0.24-0.28
   (0.2-0.3) -> 0.47 rad (0.5) - exactly the P2 prediction of the grid
   preregistration.
2. **Discrete time-grid quantization (metric, not physics):** the committed
   `_match` maximizes over the discrete IFFT time grid, bin width
   dt = 1/(N df) ~ 0.488 ms (N = 16385, df = 0.125 Hz). A sub-bin residual
   time offset tau <= dt/2 = 0.244 ms leaves an unremovable linear phase ramp
   2*pi*f*tau (~0.4 rad at 300 Hz), costing up to ~2.5% match. Observed:
   non-spinning 50+45 Msun scored 0.97451 with only 0.008 rad rms aligned
   residual; 30+30 scored 0.98992 with 0.0074 rad - both are quantization
   artifacts, not physics.

## Preregistered changes

### T1 - complete the aligned-spin TaylorF2 phasing (closes D1 and D3)

New function `phi_tf2_two_spin(freqs, total_mass_msun, eta, chi1, chi2)` in
`scripts/research/sourced_physics.py`, transcribed from the arXiv:1508.07253
LaTeX (`PhenomPaper2.tex`, sha256-stamped tarball already in
`~/.aigis/research/gw_replication/sources/`), appendix
`\section{PN coefficients} \label{sec:app_pncoeffs}` (tex line 2497). The
parameter combinations delta = (m1-m2)/M, chi_s = (chi1+chi2)/2,
chi_a = (chi1-chi2)/2 are defined at tex lines 2523-2525. Exact terms entering
(spin-dependent pieces; the point-particle pieces are the already-validated
Study-2/6/7 series):

| Order  | Term (as in source)                                                                                                          | Source lines (PhenomPaper2.tex) |
| ------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| 1.5PN  | varphi_3: (113 delta chi_a)/3 + (113/3 - 76 eta/3) chi_s                                                                       | 2532-2533                       |
| 2PN    | varphi_4: (-405/8 + 200 eta) chi_a^2 - (405/4) delta chi_a chi_s + (-405/8 + 5 eta/2) chi_s^2                                   | 2537-2539                       |
| 2.5PN  | varphi_5: [1 + log(pi M f)] x [delta (-732985/2268 - 140 eta/9) chi_a + (-732985/2268 + 24260 eta/81 + 340 eta^2/9) chi_s]      | 2540-2543                       |
| 3PN    | varphi_6: (2270/3) pi delta chi_a + (2270 pi/3 - 520 pi eta) chi_s                                                              | 2545-2550                       |
| 3.5PN  | varphi_7: delta (-25150083775/3048192 + 26804935 eta/6048 - 1985 eta^2/48) chi_a + (-25150083775/3048192 + 10566655595 eta/762048 - 1042165 eta^2/3024 + 5345 eta^3/36) chi_s | 2553-2559                       |

Scope note transcribed with the terms (tex lines 1361-1367 and 2499-2505): the
paper incorporates spin-independent corrections to 3.5PN, LINEAR spin-orbit to
3.5PN, and QUADRATIC spin corrections at 2PN only ("we drop all quadratic and
higher-order spin corrections beyond 2PN order"). No term beyond the published
list is added, and none will be added post-hoc to chase the oracle - if the
current LALSimulation IMRPhenomD carries additional spin terms beyond the
published paper, the resulting residual is CHARACTERIZED, not fitted.

`phenomd_phase.phenomd_psi` gains optional two-spin support
(`chi1z`/`chi2z`; default `None` keeps chi1 = chi2 = chi_eff so all committed
callers are unchanged) and computes the mapping spin per the source as
chi_PN = chi_eff - (38 eta / 113)(chi1 + chi2) (tex line 289) with
chi_eff = (m1 chi1 + m2 chi2)/M, m1 >= m2, delta = sqrt(1 - 4 eta). On the
frozen grid chi1z = chi2z = chi_eff (D3 of the grid prereg is the grid's
parameterization, retained), so the equal-spin limit is what the gate
exercises; the delta*chi_a sector is exercised by the tripwire twin below.

### T2 - sourced remnant on the oracle path (narrows D2)

The oracle runner switches f_RD/f_damp from
`imr_ansatz.remnant_quantities` (anchor-validated Berti-fit module) to the
Study-7 sourced transcription `sourced_physics.remnant_sourced`: final spin
from arXiv:1508.07250 `eqn:FinalSpin` (PhenomPaper1.tex lines 881-888, S =
S1+S2 convention; equal spins S = chi_eff (1 - 2 eta)), radiated energy from
`eqn:Erad` (lines 906-920, Shat = chi_eff). Declared residual deviation
(narrowed D2): the a_f -> (f_RD, f_damp) conversion stays the
Berti-Cardoso-Will fitted formulas, while LALSimulation interpolates Berti's
tabulated QNM data - a sub-percent-level fit-vs-table difference that is NOT
transcribable from the two PhenomD papers and is therefore declared, not
chased.

### T3 - metric evaluation refinement (preregistered; reported both ways)

The grid preregistration locked the match as "maximized over time (IFFT) and
overall phase". The committed implementation evaluates that time maximization
only on the discrete IFFT grid (0.488 ms bins), which systematically
UNDER-estimates the locked quantity max_t |<h1, h2>(t)| (see diagnosis 2).
Refinement, applied uniformly to every grid point:

- zero-pad the correlation integrand by a factor 32 before the inverse FFT
  (this evaluates the IDENTICAL continuous correlation function on a 32x finer
  time grid - same integrand, same normalization, no new degrees of freedom);
- parabolic (3-point) interpolation of |corr| around the discrete peak to
  estimate the continuum maximum.

Both numbers are computed and reported for every grid point: `match` (refined,
the honest evaluation of the frozen criterion - the gate evaluates this) and
`match_discrete_time` (the previous discrete-grid evaluation, for
transparency). The refinement can only reduce quantization loss; it cannot
manufacture agreement where phase residuals are real (a genuine spin-sector
error is invariant under time refinement).

## Tripwire protocol (ALL must pass BEFORE the grid run; any failure = BLOCKED)

- **W1 independent twin:** a second, independently typed implementation of the
  same appendix expressions (structurally different evaluation; coefficients
  re-typed from the source) must agree with `phi_tf2_two_spin` to < 1e-9 rad
  across [20, 1024] Hz for configs spanning the grid masses and UNEQUAL spins
  (chi1 != chi2), so the delta*chi_a sector is exercised.
- **W2 equal-spin consistency:** at chi1 = chi2, `phi_tf2_two_spin` must agree
  with Study-7's independently written equal-spin `phi_tf2_full` to
  < 1e-9 rad (third independent leg, different author-session).
- **W3 zero-spin regression:** chi1 = chi2 = 0 must reproduce the validated
  point-particle series to < 1e-9 rad (Study-7 g1 form).
- **W4 source anchors:** verbatim TeX substring assertions for the new chi_a
  coefficient strings against the sha256-stamped PhenomPaper2.tex.
- **W5 existing gates:** Study-6 G6-a..d (`phenomd_phase.py`) and Study-7
  g1-g4 (`sourced_physics.py`) re-run and pass after the wiring change.

## Preregistered predictions (falsifiable)

- **P1 (primary, the gate):** min over the 13 frozen grid points of the
  refined `match` >= 0.99. FAIL preserves the negative with the
  characterization in P3.
- **P2:** the four non-spinning points reach >= 0.999 under the refined
  metric (they are already at 0.008-0.011 rad aligned residual; their prior
  sub-floor scores were quantization).
- **P3 (characterization, reported regardless):** per-point `match` and
  `match_discrete_time`, plus inspiral/merger rms residuals, so any remaining
  deficit splits into metric (discrete vs refined gap), spin-inspiral
  (inspiral residual growth with chi), and merger/remnant (merger residual)
  contributions.

## Stopping rule (locked)

Tripwires first; if any fails, STOP (report BLOCKED with the equation
reference). Then ONE pass over the frozen 13-point grid. No re-runs, no
threshold edits, no grid edits, no floor edits, no post-hoc term additions.
The artifact registers regardless of outcome; the prior FAIL receipt stays
preserved on disk and in git history and is referenced in the new artifact's
provenance.

## Promotion rule (locked)

Identical to the grid preregistration: the artifact feeds the read-only
fail-closed readiness auditor; `belief_moved = false`; a PASS clears only the
local `phenomd_external_oracle` follow-up gate; a FAIL is preserved as the
honest gate verdict.
