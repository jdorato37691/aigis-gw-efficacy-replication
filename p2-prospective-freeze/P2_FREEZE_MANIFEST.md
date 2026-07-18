# P2 prospective freeze manifest (signed-tag payload)

**Program:** Prospective R-prediction program (G0 charter
`docs/research/preregistrations/2026-07-17-prospective-r-prediction-program-g0.md`),
stage **P2 — the prospective freeze**. · **Built:** 2026-07-17. · `belief_moved=false`.

This manifest hash-binds the frozen P2 artifacts into a single content hash
suitable to become the payload of an ssh-signed tag on the public replication
repo. **It is STAGED, NOT pushed** — the external anchor is operator-gated at
external-push time per the G0 charter, exactly like the replication bundle
(`aigis-gw-efficacy-20260717`).

## What P2 predicts

The inspiral-only matched-filter recovery fraction `R` for the GWOSC **O4c** bulk
release (planned **December 2026**), frozen NOW before that strain data exists,
as a frozen function `r_mech(M_det)` + pre-committed mass-dependent uncertainty
bands + a mechanical O4c cohort rule + a mechanical coverage grade that fires on
release day with zero discretion. The bands are calibrated on **retrospective,
development-adjacent** residuals (Study-3 OOS + O3a holdout + P1.5 O4a/O4b) and
tested **prospectively** on O4c — stated plainly, not hidden.

## Freeze-before-compute ordering (the integrity guarantee)

The band-derivation PROCEDURE was committed at `8e43efdb5` **before** any band
number was computed. The band table was then produced mechanically by running
that frozen procedure; no band parameter was chosen after seeing coverage; the
predictor was not refit. The procedure commit strictly precedes the band commit
in git history.

## Bound artifacts (file sha256 over committed bytes)

| Artifact | Role | sha256 |
| -------- | ---- | ------ |
| `docs/research/preregistrations/2026-07-17-p2-prospective-freeze.md` | frozen procedure + grading rule + results | `2057b6c6c7e797d87b1eb88880da4747a1fec13914b0dca466611f43dcfcf40b` |
| `docs/research/papers/gw-inspiral-template-efficacy/verification/p2_prospective_bands.json` | frozen band table | `04da214e5def25acc5bd2903d1caa27b0761c7c5a6b5d3343d85cc156773c5da` |
| `scripts/research/p2_prospective_bands.py` | band-derivation code | `f97447495d51a58dd39845b037306cd565e2b69affb2a8ddf14e97c078de3ba7` |
| `scripts/research/p2_release_day_grade.py` | release-day grader | `a1f638c26a68c9f55ceda39722346ca229a778789cb837cc21069b15934ce183` |
| `tests/unit/scripts/research/test_p2_release_day_grade.py` | grader controls (Rule 26) | `718adfd6255a10d2b3ab8100f152d66297f1a65ad65dc794bd532456bd5bb1bb` |
| `scripts/research/r_predictor.py` | frozen predictor `r_mech` (read-only) | `beff27c5d780a92b5f6d8394f0fe1aba7004a944b6b6a207f017ef705c0c3dcf` |

**Band table hashes:** `content_sha256 =
677135a901d0469d00d1865b4177423f836dd4f875726da9e128e4179445661b` (the
reproducible scientific payload — re-running `p2_prospective_bands.py` reproduces
the entire file byte-for-byte, no timestamp); `self_sha256 =
2f08d3fb879f6842d1040f2961ca17a9924aaeb75fe4d52b79ff77af0aba7c7b` (pins the
committed file; verified by `p2_release_day_grade.load_bands`).

**Frozen commit refs:**

- Procedure prereg commit (Step A): `8e43efdb5ca6a3d29b8fddce7e938feb7beccd03`
- Frozen predictor commit: `767d93bbd576d598f81e9b16c71bdff095c97f22`
- Frozen pipeline governing commit: `79d3c2c5ad1caec84edfa4f261afb7b8e38cb1d4`
  (`template_commit_sha256 =
  4c43f31143db2a98cf53c19d8fce6f062d18c5c920cd6c4c4ca5d54a62340446`, byte-identical
  to the fresh-holdout and P1.5 frozen pipeline)

## The single freeze hash

```
P2_FREEZE_SHA256 = 19e534508a7e2c646673f2069cf0f78db747aac927bfd2a3efa26643b6e8dc99
```

**Recomputation recipe (third-party reproducible):** `sha256` of the canonical
JSON (`json.dumps(..., sort_keys=True, separators=(",",":"), ensure_ascii=True)`)
of the object mapping `artifacts` (each path -> its file sha256 above),
`band_content_sha256`, `band_self_sha256`, `prereg_procedure_commit`,
`predictor_frozen_commit`, `pipeline_governing_commit`, and
`template_commit_sha256` to the exact values above. This is the value the signed
tag binds.

## Frozen bands (summary; full table in `p2_prospective_bands.json`)

| Regime | `M_det` (M_sun) | n | Band for an event |
| ------ | --------------- | - | ----------------- |
| LIGHT (`f_ISCO >= 215 Hz`) | `<= 20.45` | 5 | `clip(r_mech + [-0.289, -0.058], 0, 1)` |
| INTERMEDIATE (`30 < f_ISCO < 215 Hz`) | `20.45 .. 146.57` | 35 | `clip(r_mech + [-0.189, +0.245], 0, 1)` |
| HEAVY / ISCO-below-band (`f_ISCO <= 30 Hz`) | `>= 146.57` | 8 | `[0, 0.05]` (R -> 0 sub-claim) |

Grade on release day = coverage of these bands over the measured O4c cohort:
**CONFIRMED** if `coverage >= 0.80`, **FALSIFIED** if `coverage < 0.70`,
INCONCLUSIVE otherwise (`n_measured >= 8` required); plus the `R -> 0` sub-claim
(every ISCO-below-band O4c event must recover `R <= 0.05`). A FALSIFIED outcome is
a first-class product.

## Operator push + sign command (STAGED — do NOT run without operator sign-off)

Mirrors the replication-bundle anchor (`aigis-gw-efficacy-20260717`). Run only at
the operator's explicit external-push instruction, from the public replication
checkout after the P2 artifacts are copied in:

```bash
# from the public replication repo checkout (github.com/jdorato37691/aigis-gw-efficacy-replication)
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub    # jdorato37691 ssh-ed25519 key (SHA256:L9aqePBZg0bj/+Qh03KQQLmkrhR0bGmsKv1FN8JbTBM)
git add -A && git commit -m "P2 prospective freeze: O4c inspiral-recovery prediction (frozen $(date -u +%Y-%m-%d))"
git push origin main
git tag -s aigis-gw-p2-freeze-20260717 \
  -m "P2 prospective freeze; O4c (Dec 2026) inspiral-recovery prediction; P2_FREEZE_SHA256=19e534508a7e2c646673f2069cf0f78db747aac927bfd2a3efa26643b6e8dc99"
git push origin aigis-gw-p2-freeze-20260717
# verify (allowed_signers as in BUNDLE-README):
git -c gpg.ssh.allowedSignersFile=./allowed_signers verify-tag aigis-gw-p2-freeze-20260717
```

The signed tag on the public remote timestamps the freeze **outside** AIGIS's own
git history — the external immutable anchor the G0 charter requires, applied
forward to a prediction whose measuring data does not yet exist.

## What a third party needs to falsify this on release day

Given this manifest, the committed `p2_prospective_bands.json`, the frozen
`r_predictor.py` (`767d93bbd`), the frozen pipeline (`template_commit_sha256`
above), and the O4c public release: run `p2_release_day_grade.py
--catalog-release <O4c catalog>` (or reimplement the frozen Section 4-5 rule) —
enumerate the O4c cohort by the frozen rule (BBH, FAR<1/yr, network SNR>=12,
strain available, GPS-sorted, disjoint from the frozen development manifest),
measure `R` with the frozen pipeline, and compute coverage against the frozen
bands. If `coverage < 0.70` (or any ISCO-below-band O4c event recovers
`R > 0.05`), the band-floor mechanism's prospective prediction is **falsified**.
Nothing in the grade depends on AIGIS's own authored state — only on O4c strain,
O4c published masses, and these frozen artifacts.
