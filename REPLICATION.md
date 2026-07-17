# Replication runbook — GW inspiral-template-efficacy package

This runbook is the entry point for an independent replicator holding the
content-addressed bundle produced by
`scripts/research/build_replication_bundle.py`. It describes only steps the
bundle actually supports: verifying integrity, rebuilding the environment,
re-running the six machine-checked verification gates, and re-executing the
three headline computations from public GWOSC data.

**What this package claims (narrow, per §8 of `paper.md`).** No relationship in
this paper is claimed as cleanly novel. What is offered for replication is
specific and bounded: (1) the **R statistic** — quadrature of independently
maximized H1/L1 inspiral-only 3.5PN TaylorF2 SNRs over the published catalog
network SNR — measured per event across three GWTC catalogs, with its values and
mass correlations; and (2) the **out-of-sample and fresh-holdout transfer** of
that mass-recovery curve. Internally preregistered and hash-receipted before
each run, with the complete package first externally anchored in the signed
July 17, 2026 tag. The mass-decline relationship itself is an anticipated,
textbook one (Flanagan & Hughes 1998; Damour, Iyer & Sathyaprakash 2001); the
contribution under test is the per-event quantification and its transfer, not
the physics of the decline.

The three computations require roughly 40-50 minutes on the reference setup,
excluding initial environment installation and network variability.

**Honest status.** The local readiness auditor reports
`analysis_ready_for_external_review` (six gates pass under the committed
contract) but `external_ready = false`, by design: same-operator local hashes
and git history are not an external immutable trust anchor. Your independent
re-execution is exactly the missing external evidence. Any outcome —
confirmation, partial, or refutation — is a valid and welcome result.

---

## 0. Prerequisites

- Python 3.13 on macOS or Linux.
- `git` is not required — the bundle is self-contained.
- Network access to `gwosc.org` for the strain/event fetches (steps 3d, 3e).
  The oracle grid (step 3f) needs no network but needs a `lalsimulation`
  install.
- `shasum` (macOS) or `sha256sum` (Linux) for integrity checks.
- Roughly 3 GB free disk for fetched strain caches and receipts.

Set a working root and know where outputs go. All runners write their run
receipts to `~/.aigis/research/gw_replication/` on **your** machine and (for the
gate runners) overwrite the corresponding `paper/verification/<gate>.json`
inside the bundle in place. One layout note: the bundle's `docs/` entry is a
compatibility symlink into `paper/` — the pipeline scripts resolve their
repo-relative paths from their own location, and the symlink lets them run
unmodified (macOS/Linux; the symlink does not resolve on Windows):

```bash
export BUNDLE=/path/to/aigis-gw-efficacy-bundle-<stamp>
mkdir -p ~/.aigis/research/gw_replication
cd "$BUNDLE"
```

---

## 1. Verify the manifest (integrity anchor)

`MANIFEST.sha256` is the integrity anchor; `BUNDLE_SHA256` is the sha256 of the
manifest file. Verify both before trusting anything else.

```bash
# every listed file hashes as recorded (run from the bundle root)
shasum -a 256 -c MANIFEST.sha256        # macOS
# sha256sum -c MANIFEST.sha256          # Linux

# the manifest itself matches the published bundle hash
shasum -a 256 MANIFEST.sha256           # compare first field to BUNDLE_SHA256
cat BUNDLE_SHA256
```

`MANIFEST.sha256` intentionally excludes itself and `BUNDLE_SHA256`. Re-running
the builder at the same git HEAD with the same receipts reproduces identical
hashes for all scientific content (package, preregistrations, verification
artifacts, pipeline code, receipts) and for the path-normalized
`audit/READINESS_AT_BUILD.json`. The only files that differ across rebuilds are
the build-stamp-bearing `audit/BUILD_INFO.json` and the point-in-time
`environment/*.freeze.txt` snapshots. `bundle.tar.gz` is not byte-reproducible
(embedded mtimes) — compare the manifest, never the tarball.

Read `audit/BUILD_INFO.json` (git HEAD, counts, environment fingerprints) and
`audit/READINESS_AT_BUILD.json` (the six-gate state captured at build time).

**Then make a disposable working copy and run everything there.** The gate
runners overwrite `paper/verification/*.json` in place, so keep the verified
checkout pristine for later re-verification and diffing:

```bash
cp -a "$BUNDLE" "$BUNDLE-work"
export BUNDLE="$BUNDLE-work"
cd "$BUNDLE"
```

Pristine original, disposable working copy — every command below runs in the
working copy.

---

## 2. Build the environments

Two isolated virtualenvs. The main env runs the pipeline and the readiness
audit; a **separate** env holds `lalsuite` for the external oracle only (never
mix them).

```bash
# (a) main pipeline env — pinned replication lock
python3.13 -m venv ~/gwrepl-venv
~/gwrepl-venv/bin/pip install -r environment/main-replication.txt

# (b) oracle env — lalsimulation (used ONLY in step 3f)
python3.13 -m venv ~/gwrepl-lal-venv
~/gwrepl-lal-venv/bin/pip install -r environment/oracle-replication.txt
export MAIN=~/gwrepl-venv/bin/python
export LAL=~/gwrepl-lal-venv/bin/python
```

The `environment/*-replication.txt` files are the fit-for-purpose replication
locks (exactly the packages the runbook needs, at the versions the reference
runs used); the `environment/*_venv.freeze.txt` files are the full environment
inventories of the reference machine, kept for byte-level environment matching
and forensics — install from the locks, consult the inventories.

`environment/lal_venv.oracle_environment.txt` records the sha256 the oracle
runner computes over its package list. Date-versioned transitive deps (e.g.
`astropy-iers-data`) drift daily, so this hash will not match byte-for-byte on a
fresh install — that is expected and does not invalidate the oracle result. The
load-bearing package is `lalsuite`/`lalsimulation`.

---

## 3. Re-run the evidence

### (c) The six verification gates — read-only, no network, seconds

`gw_package_readiness.py` re-validates the six `verification/*.json` artifacts
against their locked criteria. It runs no experiment, touches no network, and
mutates nothing.

```bash
$MAIN scripts/research/gw_package_readiness.py
$MAIN scripts/research/gw_package_readiness.py --require-analysis-ready-for-external-review
```

Expected on the pristine bundle: `epistemic_status =
analysis_ready_for_external_review`, six gates `pass`, `external_ready = false`.
The posterior gate passes on the trend-only criterion under contract v3; its
withdrawn per-draw curve criterion (0.54 of draws) is preserved in the gate
output as the record of the withdrawn claim — read it, it is part of the honest
account. `--require-external-ready` will exit nonzero by design.

### (d) Study 1 — the efficacy sweep (network; ~20–30 min)

Ten GWTC-1 BBH events, inspiral-only TaylorF2 at the locked catalog masses,
recovery fraction R versus detector-frame total mass. Fetches ~32 s of H1+L1
strain per event from GWOSC.

```bash
$MAIN scripts/research/gwtc1_taylorf2_sweep.py
# writes ~/.aigis/research/gw_replication/GWTC1_taylorf2_sweep_<stamp>.json
```

**Agreement:** a monotonic decline of R with detector-frame total mass,
Spearman `rho <= -0.5` (the paper measures `rho = -0.891`, p = 5.4e-4, R falling
from ~0.88 at 20 Msun to ~0.21 at 125 Msun). The PSD-robustness gate reuses this
receipt as its positive control.

### (e) The fresh untouched holdout (network; ~17 min for the evaluate phase)

Ten O3a / GWTC-2.1-confident events selected by a deterministic preregistered
rule, disjoint from the 31-event development manifest, evaluated exactly once.

**Seed the exact frozen cohort first.** The freeze phase is idempotent: if a
freeze receipt is already in place it is reused, so seeding the bundled receipt
pins your evaluation to the exact cohort the reference run froze (rather than
re-deriving it against today's GWOSC event API):

```bash
mkdir -p ~/.aigis/research/gw_replication
cp receipts/FRESH_HOLDOUT_freeze_latest.json ~/.aigis/research/gw_replication/
```

Then run the three idempotent, checkpointed phases:

```bash
$MAIN scripts/research/fresh_holdout_study.py --freeze
$MAIN scripts/research/fresh_holdout_study.py --evaluate
$MAIN scripts/research/fresh_holdout_study.py --build-artifact
# regenerates paper/verification/fresh_untouched_holdout.json, then self-validates it
```

**Agreement:** outcome `confirmed` — both locked criteria hold: trend
`rho <= -0.5` and median `|R - R_hat| <= 0.15`. The paper measures `rho =
-0.964`, p = 4.8e-4, median error 0.129 (7 of 10 measured, 3 excluded by a
mechanical data-availability rule), with the three heaviest events recovering
R ~ 0 as the ISCO-below-band mechanism predicts.

### (f) The external oracle match grid (no network; ~1 min; needs `lalsimulation`)

Compares the AIGIS source-transcribed PhenomD phase (from arXiv:1508.07253)
against LALSimulation's IMRPhenomD over the preregistered parameter grid. Run
with the **oracle** env only.

```bash
$LAL scripts/research/lal_oracle_compare.py
# regenerates paper/verification/phenomd_external_oracle.json
```

**Agreement:** minimum noise-weighted phase match `>= 0.99` across the frozen
13-point grid (the completed two-spin 3.5PN transcription measures min 0.99997,
median 0.99999). The bundle also carries the preserved 2026-07-16 fail receipt
(`LAL_oracle_20260716T113628Z.json`, min 0.918) that diagnosed the incomplete
aligned-spin sector — the fail-diagnosis-completion arc is part of the record.

### Optional: the remaining two gate runners

For completeness the PSD-robustness and posterior-propagation runners are
included (both network, tens of minutes):

```bash
$MAIN scripts/research/psd_robustness_sweep.py                 # 10 events x 4 PSD regimes
$MAIN scripts/research/posterior_propagation.py --draws 100    # >=100 draws to satisfy the gate
```

**PSD agreement:** the mass trend survives all four locked regimes (`rho` between
-0.830 and -0.891). **Posterior agreement (contract v3):** the trend criterion
(`rho <= -0.5`) holds in >= 90% of joint draws (98/100); the withdrawn per-draw
curve criterion is preserved, not gated.

---

## 4. What agreement means, and where to report

Because GWOSC fetches, PSD estimation, and posterior draws carry run-to-run
structure, **agreement is judged by the preregistered verdicts and tolerances
above, not by byte-identical artifacts.** The manifest confirms you started from
the pristine bundle; the gate criteria define a pass.

A useful replication reports, per computation: the recomputed statistic, whether
it clears the locked tolerance, your environment fingerprint
(`$MAIN -m pip freeze`), and any step that diverged. A refutation is as valuable
as a confirmation and should be reported with the same detail. Each
preregistration under `preregistrations/` states its own locked metric,
tolerance, data segments, and falsifiers — read the relevant one before scoring
a gate.

**Report results to the party who provided this bundle.** This package sends
nothing automatically; there is no callback. The provider will fold your outcome
into a co-authored replication report and share the full receipt set. If you
reached this bundle through a public channel and do not have a direct contact,
the provenance and contact are in the accompanying transmittal, not in this
file.
