# Preregistration: PhenomD external-oracle match grid (referee item 1)

**Program:** CHARTER G3 track, verification package - external waveform oracle
**Preregistered:** 2026-07-16 (grid locked before the expanded oracle run)
**Artifact:** `docs/research/papers/gw-inspiral-template-efficacy/verification/phenomd_external_oracle.json`
(schema `aigis.gw.phenomd_oracle.v1`)
**Validator:** `scripts/research/gw_evidence_controls.py::validate_oracle_artifact`
**Runner:** `scripts/research/lal_oracle_compare.py` (isolated `lal_venv`,
lalsimulation 6.2.1)

## Why this preregistration exists

Every AIGIS waveform control to date is a self-injection: the same code
generates and recovers the template, so a shared convention or transcription
error passes all of them. Referee item 1 is the decisive missing test -
agreement with an independent reference implementation (LALSimulation
IMRPhenomD). The existing runner already implements the comparison on a 5-point
grid (paper reports median 0.9895, min 0.9620). No committed preregistration
locked that grid, and the readiness validator requires at least 12 unique
preregistered grid points. This document locks a fair 12+ point grid so the
oracle artifact rests on a committed protocol, not a post-hoc selection.

## Backend and comparison mode (locked)

- **Backend:** `lalsimulation` (lalsuite in the isolated `~/.aigis/research/lal_venv`;
  lalsimulation 6.2.1). The reference waveform is
  `SimInspiralChooseFDWaveform(..., IMRPhenomD)`.
- **Comparison mode:** `exact_phenomd`. The oracle reference is LAL's exact
  IMRPhenomD. The reported `match` per grid point is the noise-weighted phase
  match between the AIGIS transcribed Fourier phase
  (`phenomd_phase.phenomd_psi`) and LAL's IMRPhenomD phase, using a COMMON
  amplitude (LAL's), an analytic aLIGO ZeroDetHighPower design PSD, maximized
  over time (IFFT) and overall phase (magnitude), and over both phase-sign
  conventions. f_low = 20 Hz, df = 0.125 Hz. This is the committed physics of
  `_lal_fd` / `_aligo_psd` / `_match` / `_compare` and is NOT changed by this
  preregistration - only the set of evaluated grid points is expanded.
- **Match floor:** `0.99` (the code-owned `MIN_ORACLE_MATCH`; the validator
  rejects any floor below it). Pass iff min(match) over all grid points >= 0.99.

## Grid (locked - 13 unique points)

Single effective aligned spin per point (declared deviation D3:
chi1z = chi2z = chi_eff), f_min_hz = 20.0 for every point. The grid spans the
heavy-BBH intrinsic parameter space of the study (total mass ~60-150 Msun, mass
ratio q up to ~1.4, aligned spin 0.0 to 0.6) and is a superset of the original
5-point grid for continuity. It deliberately samples both the non-spinning
regime (where AIGIS is exact PhenomD to numerical precision) and the aligned-spin
regime (where the declared deviations act), so the artifact honestly
characterizes the full space rather than one regime.

| # | mass1_msun | mass2_msun | chi1z = chi2z | f_min_hz |
|---|-----------:|-----------:|--------------:|---------:|
| 1 | 36.0 | 29.0 | 0.0 | 20.0 |
| 2 | 30.0 | 30.0 | 0.0 | 20.0 |
| 3 | 60.0 | 40.0 | 0.0 | 20.0 |
| 4 | 50.0 | 45.0 | 0.0 | 20.0 |
| 5 | 50.0 | 40.0 | 0.2 | 20.0 |
| 6 | 36.0 | 30.0 | 0.2 | 20.0 |
| 7 | 70.0 | 50.0 | 0.2 | 20.0 |
| 8 | 45.0 | 40.0 | 0.3 | 20.0 |
| 9 | 80.0 | 70.0 | 0.3 | 20.0 |
| 10 | 60.0 | 55.0 | 0.4 | 20.0 |
| 11 | 65.0 | 55.0 | 0.4 | 20.0 |
| 12 | 40.0 | 35.0 | 0.5 | 20.0 |
| 13 | 55.0 | 48.0 | 0.6 | 20.0 |

## Declared deviations from full PhenomD (locked; carried from Study 6)

- **D1** psi_TF2 spin sector is the validated 1.5PN spin-orbit term only.
- **D2** f_RD / f_damp from the anchor-validated remnant module, not Paper-1 fits.
- **D3** single effective spin chi1 = chi2 = chi_eff in chi_PN.
- **D4** amplitude common (LAL's) so the match isolates the transcribed phase.

These deviations mean the AIGIS phase is an APPROXIMATION of PhenomD in the
spin sector, not an exact copy. The match is therefore expected to be at or
above the floor only in the non-spinning limit.

## Preregistered prediction (falsifiable)

- **Primary (P1):** min(match) over the 13 grid points >= 0.99 (the gate PASS
  condition). **Expected outcome given the declared deviations: FAIL.** The
  non-spinning points (1-4) are predicted to sit at or above 0.99; the
  aligned-spin points are predicted to fall below 0.99 (the 5-point run already
  showed 0.962 at chi=0.3), so the grid minimum is predicted below the floor.
  A below-floor minimum is an HONEST NEGATIVE: it quantifies the spin-sector
  approximation against the field-standard implementation, not a code bug. It is
  recorded as a first-class negative result; the grid is NOT pruned to the
  non-spinning regime to force a pass, and the floor is NOT lowered.
- **Secondary (P2, reported not gated):** the match degrades monotonically with
  |chi_eff|; the non-spinning subset matches to >= 0.99 with sub-0.01 rad phase
  residual, externally confirming the core coefficient transcription.

## Stopping rule (locked)

One pass over the 13-point grid (cached-free analytic LAL generation + AIGIS
phase). No re-runs, no threshold edits, no grid edits after results, no floor
edits. The artifact registers regardless of outcome.

## Promotion rule (locked)

The artifact feeds the read-only fail-closed readiness auditor
(`gw_package_readiness.py`). `belief_moved=false`; it does not touch the truth
ladder. A PASS clears only the local `phenomd_external_oracle` follow-up gate; a
FAIL is preserved as the honest gate verdict and the paper's item-1 language
already reflects the spin-sector approximation.
