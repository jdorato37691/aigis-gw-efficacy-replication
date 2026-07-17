# AIGIS GW inspiral-template-efficacy — replication bundle

**What this is.** A small, self-contained computational study on public GWOSC
strain data, packaged for independent replication. The study measures a
recovery statistic R — the quadrature sum of independently maximized H1/L1
matched-filter SNRs from an inspiral-only 3.5PN TaylorF2 template, divided by
the published catalog network SNR — per event across the GWTC catalogs, and
tests whether the R-vs-detector-frame-total-mass relationship transfers
out-of-sample and to a preregistered fresh holdout. The declining trend itself
is anticipated in the literature (see [`paper/literature-positioning.md`](paper/literature-positioning.md));
the contribution under test is the per-event quantification and its
preregistered transfer, not new physics.

**The ask.** Determine whether you obtain the same numerical results when
executing the supplied runbook. Agreement with the paper's conclusions is not
requested — only independent re-execution. Any outcome is welcome; a
refutation helps as much as a confirmation.

## The audited artifact is the signed tag

- Tag **`aigis-gw-efficacy-20260717.2`** (ssh-signed) binds the bundle hash: its tag message
  records `BUNDLE_SHA256` = sha256 of [`MANIFEST.sha256`](MANIFEST.sha256),
  which lists every audited file. The same value is in the
  [`BUNDLE_SHA256`](BUNDLE_SHA256) file; verify both as step 1 of the runbook.
- Everything in this tree is manifest-covered except `MANIFEST.sha256` and
  `BUNDLE_SHA256` themselves (the anchor cannot hash itself).
- Tag `aigis-gw-efficacy-20260717.2` supersedes `aigis-gw-efficacy-20260717`, which remains in
  history as the first anchored build (internal repo-mirroring layout, same
  scientific content). Check out the tag you intend to audit.

## Layout

| Path                | Contents                                                       |
| ------------------- | -------------------------------------------------------------- |
| `REPLICATION.md`    | **Start here** — the runbook: commands, tolerances, runtimes   |
| `paper/`            | paper, referee review, literature positioning, operator decisions, `verification/` gate artifacts |
| `preregistrations/` | the 20 preregistrations (metric, tolerance, falsifiers locked before each run) |
| `scripts/`          | the runnable pipeline + verification code (`scripts/research/`) |
| `receipts/`         | the 18 referenced run receipts (sha256-stamped)                |
| `environment/`      | pinned package lists for the two venvs                         |
| `audit/`            | build provenance, readiness state at build, safety scan        |
| `docs/`             | compatibility symlink into `paper/` so the pipeline code runs unmodified |

## How to replicate (three scripted stages)

Full runbook with exact commands, pinned versions, and runtimes:
[`REPLICATION.md`](REPLICATION.md)

1. **Verify integrity + re-run the six audit gates** — read-only, no network,
   seconds.
2. **Re-run the headline computations** from public GWOSC data — the Study-1
   sweep (~20-30 min) and the fresh-holdout evaluation (~20 min).
3. **External oracle check** — the PhenomD phase transcription vs
   LALSimulation on the preregistered 13-point grid (requires
   `lalsimulation`; minutes).

## Expected reference results (preregistered tolerances in the runbook)

| Quantity                                        | Reference value        |
| ----------------------------------------------- | ---------------------- |
| Study 1 (GWTC-1, n=10): Spearman rho(M_det, R)  | -0.891 (p = 5.4e-4)    |
| GWTC-3 OOS transfer (n=20): rho / median error  | -0.87 / 0.088          |
| Fresh holdout (GWTC-2.1, 7 of 10 measured): rho | -0.9636 (p = 4.75e-4)  |
| Fresh holdout median abs prediction error       | 0.129 (criterion 0.15) |
| Oracle match, min / median (13-point grid)      | 0.99997 / 0.99999      |
| Oracle match floor (preregistered)              | 0.99                   |
| PSD-robustness rho range (4 regimes, n=10 each) | -0.830 to -0.891       |

The paper, referee review, three-pass literature positioning, preserved
negative results (including the original oracle FAIL that diagnosed the
incomplete spin sector), preregistrations, run receipts, and environment
manifests are enumerated in `MANIFEST.sha256`.

## Contact

Open a GitHub issue on this repository for questions or to report a
replication attempt (any outcome). Pass/fail is defined by the preregistered
tolerances in the runbook, not by agreement with interpretation.
