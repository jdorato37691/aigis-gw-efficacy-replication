# Preregistration: sourced-PhenomD phase on heavy BBH (Study 6)

**Program:** CHARTER G3 track, Study 6 · **Preregistered:** 2026-07-12
(committed before any on-source run) **Motivating results:** two
mechanism-attributed negatives bound the Study-4/5 ansatz: the continued-
TaylorF2 merger phase failed the low-mass artifact control (Study 4 P2,
contested) and left the heavy recovery target unmet (Study 5 Q1: 0.540 < 0.65)
even though the added amplitude band is coherent (Q2 7/7, +0.123; Q3 +0.164).
The phase is the quantified bottleneck. This study replaces it with the real
phenomenological phase of PhenomD (Khan et al. 2016, arXiv:1508.07253).

## The sourcing gate is satisfied (program honesty rule)

Study 4's prereg refused PhenomD because transcribing ~200 fitted coefficients
from memory is a fabrication risk. That objection is now dissolved by verifiable
transcription: both PhenomD papers' LaTeX sources were fetched from arXiv
(read-only ingestion lane) and sha256-stamped:

- `1508.07253.tar.gz` sha256
  `e70cde9d5e9ee92e4592c4c93152f6eb2410264358486f6a68064fb03b39b1cf` →
  `PhenomPaper2.tex` (sha256
  `ed0d9ca1031def94a8df3d2964967dd88d50aa179bd12fd2bbf1cfb067070b44`; table
  `tab:coefftable`, 19 parameters × 11 λ coefficients, tex lines 2623-2642;
  mapping polynomial `eqn:mapping`; phase ansätze `equ:phiins`, `eqn:IntPhase`,
  `eqn:MRDPhase`; χ_PN definition line 289)
- `1508.07250.tar.gz` sha256
  `79dd5b277fd99d8ff3576800fb274b296bea8ae1553f134a015205f40fae5b4a` → Paper 1
  (held for reference; its remnant fits are NOT transcribed — deviation D2
  below)
- parsed-payload digest
  `aff21107f1b7714b7026a226aa2b7ae855c2c7c2a29b005eb75f42df486209d6`
  (re-verified on every load by `load_artifact()`)

`scripts/research/phenomd_coefficients.py` parses the table into a
provenance-stamped artifact (`phenomd_coefficients.json`: tarball + tex sha256s,
table line range, payload digest) behind a Rule-26 parse tripwire: exact 19×11
shape, exact label sequence, and 8 spot-checked cells asserted against verbatim
raw source strings spanning every number format in the table (plain,
trailing-dot, both `\times 10^{n}` spellings). All pass.

## Template (locked)

`scripts/research/phenomd_phase.py::phenomd_time_domain` — the Study-4 amplitude
ansatz EXACTLY (gate G6-d proves the copy is bitwise-faithful), with the phase
replaced by the sourced three-region PhenomD construction:

- inspiral (Mf < 0.018): validated ψ_TF2 + (1/η)(σ₁f + ¾σ₂f^{4/3} + ⅗σ₃f^{5/3}
  \+ ½σ₄f²)
- intermediate [0.018, 0.5 f_RD]: (1/η)(β₁f + β₂ln f − β₃/3 f⁻³)
- merger-ringdown (≥ 0.5 f_RD): (1/η)(α₁f − α₂f⁻¹ + 4/3 α₃f^¾ + α₄
  arctan((f−α₅f_RD)/f_damp))
- integration constants fixed by C¹ connection at both boundaries (per the
  paper); all 19 Λ from the sourced mapping polynomial at (η, χ_PN).

**Declared deviations from full PhenomD (locked):** D1 ψ_TF2 spin sector is the
validated 1.5PN spin-orbit term only; D2 f_RD/f_damp from the anchor-validated
remnant module (Study 4 G-a), not Paper 1's fits; D3 single effective spin
χ₁=χ₂=χ_eff in χ_PN; D4 amplitude unchanged (phase-only swap — deltas attribute
to the phase alone).

**Scrambled twin:** identical amplitude; phase(Mf ≥ 0.018) ~ U[0, 2π), seed
`20260712 ^ adler32(event_name)` (Study 5's construction, band widened to the
full phase-modified region).

## Integrity gates (all PASSED pre-registration; re-run in code before runs)

- **G6-a** parse tripwire + mapped α₅ ∈ [0.95, 1.05] for all 14 event configs
  (paper states α₅ ∈ [0.98, 1.04]; observed 0.9919-0.9931). PASS.
- **G6-b** stitch positive control: the C¹ stitcher fed TF2 as all three regions
  must be the identity (constants ~0, residual < 1e-6 rad). Observed exactly
  0.0. PASS.
- **G6-c** C¹ continuity at both boundaries for all 14 configs
  (side-extrapolated value jump < 1e-3 rad, slope mismatch < 1e-2). Worst slope
  residual 1.2e-3. PASS.
- **G6-d** amplitude regression: `phase_model="tf2_continued"` reproduces
  `imr_ansatz.imr_time_domain` exactly (max |Δ| = 0.0). PASS.
- **G6-e** per-event injection validation + off-source known-bad (< 8), as in
  every prior study; instrument-invalid events get no verdict.

## Event sets (locked; same rows and parameters as Studies 4-5)

- Heavy GWTC-1 (7): GW170104, GW170814, GW170809, GW150914, GW170818, GW170823,
  GW170729. Spin-TaylorF2 baselines median 0.438; Study-5 hybrid per-event:
  0.540, 0.513, 0.608, 0.417, 0.473, 0.551, 0.631 (median 0.540).
- Heavy GWTC-3 OOS arm (7 registered, 6 measured in Study 5 — GW191230 was
  instrument-invalid): GW200220 (S5 0.559), GW200219 (0.584), GW200128 (0.542),
  GW191230 (—), GW191222 (0.566), GW191127 (0.607), GW191109 (0.518).

## Preregistered predictions

- **S1 (primary, the twice-missed target):** median R over the 7 heavy GWTC-1
  events ≥ **0.65**.
- **S2 (coherence control):** median (R_phenomd − R_scrambled) over the 7 heavy
  GWTC-1 events ≥ **+0.10** AND wins ≥ **6/7**.
- **S3 (OOS arm):** median R over the measured GWTC-3 heavy events ≥ **0.408**
  with the same coherence margin ≥ +0.10.
- **S4 (head-to-head, the decisive phase question):** paired per-event against
  the Study-5 hybrid values above, median (R_S6 − R_S5) > **0** on each event
  set separately (events measured in both studies only). Falsifier: the sourced
  phase does not beat the continued-TaylorF2 phase → either this
  implementation's deviations (D1-D3) break the model or the merger phase was
  not the binding constraint — a preserved negative that redirects the program
  to amplitude/spin-sector work.

## Stopping rule (locked)

One pass: template + scrambled twin per event (28 runs, cached strain), no
re-runs, no threshold edits, no coefficient edits after results. Registers
regardless of outcome.

## Promotion rule (locked)

One registry record, receipt-bound EXTERNAL_EXPERIMENTAL_RESULT evidence,
single-pass ceiling **externally_grounded**. Paper §3.6 and the memory file
updated with the outcome either way.
