# AIGIS GW inspiral-template-efficacy — replication bundle

**What this is.** A small, self-contained computational study on public GWOSC
strain data, packaged for independent replication. The study measures a
recovery statistic R — the quadrature sum of independently maximized H1/L1
matched-filter SNRs from an inspiral-only 3.5PN TaylorF2 template, divided by
the published catalog network SNR — per event across the GWTC catalogs, and
tests whether the R-vs-detector-frame-total-mass relationship transfers
out-of-sample and to a fresh holdout. Internally preregistered and
hash-receipted before each run, with the complete package first externally
anchored in the signed July 17, 2026 tag. The declining trend itself
is anticipated in the literature (see [`paper/literature-positioning.md`](paper/literature-positioning.md));
the contribution under test is the per-event quantification and its
preregistered transfer, not new physics.

**The ask.** Determine whether you obtain the same numerical results when
executing the supplied runbook. Agreement with the paper's conclusions is not
requested — only independent re-execution. Any outcome is welcome; a
refutation helps as much as a confirmation.

## The audited artifact is the signed tag

- Tag **`aigis-gw-efficacy-20260717-r1`** (ssh-signed) binds the bundle hash: its tag message
  records `BUNDLE_SHA256` = sha256 of [`MANIFEST.sha256`](MANIFEST.sha256),
  which lists every audited file. The same value is in the
  [`BUNDLE_SHA256`](BUNDLE_SHA256) file; verify both as step 1 of the runbook.
- Everything in this tree is manifest-covered except `MANIFEST.sha256` and
  `BUNDLE_SHA256` themselves (the anchor cannot hash itself).
- Tag `aigis-gw-efficacy-20260717-r1` supersedes `aigis-gw-efficacy-20260717.2` (replicator-first
  layout) and `aigis-gw-efficacy-20260717` (the first anchored build, internal
  repo-mirroring layout); both remain in history with the same scientific
  content. Check out the tag you intend to audit.

## Verify the tag signature

1. Signing key (ED25519), fingerprint
   `SHA256:L9aqePBZg0bj/+Qh03KQQLmkrhR0bGmsKv1FN8JbTBM`, GitHub identity
   `jdorato37691`.
2. Construct the allowed-signers file from the public key (public by nature,
   reproduced here verbatim):
   ```bash
   echo "jdorato37691 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDZKQl2Q7FXAW5TRJuvU7L/eVrYrl6UbMUthpDqbSw2/" > allowed_signers
   ```
3. Verify:
   ```bash
   git -c gpg.ssh.allowedSignersFile=./allowed_signers verify-tag aigis-gw-efficacy-20260717-r1
   ```
4. Success looks like:
   `Good "git" signature for jdorato37691 with ED25519 key SHA256:L9aqePBZg0bj/+Qh03KQQLmkrhR0bGmsKv1FN8JbTBM`
5. GitHub's web "Verified" badge state: pending signing-key registration on the account. The cryptographic
   verification in steps 2-3 does not depend on GitHub.

## Layout

| Path                | Contents                                                       |
| ------------------- | -------------------------------------------------------------- |
| `REPLICATION.md`    | **Start here** — the runbook: commands, tolerances, runtimes   |
| `paper/`            | paper, referee review, literature positioning, operator decisions, `verification/` gate artifacts |
| `preregistrations/` | the 20 preregistrations (metric, tolerance, falsifiers locked before each run) |
| `scripts/`          | the runnable pipeline + verification code (`scripts/research/`) |
| `receipts/`         | the 18 referenced run receipts (sha256-stamped)                |
| `environment/`      | pinned replication locks (`*-replication.txt`) + full venv inventories |
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

The three computations require roughly 40-50 minutes on the reference setup,
excluding initial environment installation and network variability.

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

License: not yet designated; for reuse questions open an issue.
