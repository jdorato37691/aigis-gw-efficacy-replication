# Study-3 cohort accounting — RESOLVED 2026-07-14

**Status: CLOSED.** One constant was serving two different cohorts. It is now
two contracts, the paper states both, and the gate passes on the real artifact.
Belief unchanged throughout; this was a harness/accounting correction, not a
science change. Kept as scar tissue — the defect class is live everywhere else.

## The defect (what was wrong)

`STUDY3_EXPECTED_MEASURED_EVENTS = 16` matched **neither** real cohort. It, five
`_study3_payload(16)` positive-control tests, and paper §3.4's "16 measured, 4
excluded (…1 failed the off-source control)" all traced to one stale count.

Ground truth, from canonical receipt
`~/.aigis/research/gw_replication/GWTC3_oos_20260712T023453Z.json` (sha256
`e38e953f…`, `n_measured: 15`): 15 measured, 3 `data_unavailable`, **2**
`instrument_invalid_no_verdict` — `GW200224_222234` off-source max **9.774** and
`GW191204_110529` **16.202**, both over the 8.0 detection-scale threshold. §3.4
said _1_ off-source failure; there are **2**. A fresh off-source-controlled
reproduction (`study3_coincidence_gate.py`) yields the **set-identical**
15-event cohort.

Decisively: §3.4's own cited statistics were already computed on those 15 events
— recomputation gives ρ = **−0.8704**, p = **2.44e-05**, median|R−R̂| = **0.088**
against §3.4's cited −0.87 / 2.4e-05 / 0.088. The reported ρ, p, and median
prediction error were correctly calculated on the 15-event cohort; only the
accompanying count sentence was incorrect. The section contradicted its own
numbers.

## Resolution — two cohorts, two contracts

| Cohort                             | Rule                                       | n      | Role                                   |
| ---------------------------------- | ------------------------------------------ | ------ | -------------------------------------- |
| **PRIMARY** (inferential)          | on-source avail **+ off-source ≥8 reject** | **15** | carries the locked O1/O2 claims        |
| **AVAILABILITY-ONLY** (diagnostic) | on-source avail only                       | **17** | descriptive "6/17 non-coincident" only |

The preregistration gives **no verdict** to events failing the off-source
validity control, so they are excluded from any inferential sample. Accounting
closes both ways: 15 + 5 excluded = 20 seeded; 20 − 3 unavailable = 17.

**Which cohort the gate uses, and why 15:**
`validate_study3_coincidence_artifact` enforces `STUDY3_RHO_MAX = -0.5` and
`STUDY3_MEDIAN_ABS_ERROR_MAX = 0.15` — these are §3.4's locked O1/O2 _verbatim_.
It is therefore an **inferential** gate and must use the validity-controlled 15;
17 would let verdict-less events carry a preregistered claim. §7's "6/17" is a
_count_ — a diagnostic — and keeps its own constant. One constant must not serve
two masters.

Landed:

- `6a5040d1e` — `STUDY3_EXPECTED_PRIMARY_VALID_EVENTS = 15` +
  `STUDY3_EXPECTED_AVAILABILITY_AUDIT_EVENTS = 17`; validator repointed to the
  primary contract; tests split into
  `test_study3_primary_statistics_valid_cohort` and
  `test_study3_availability_only_coincidence_audit`, each pinning real cohort
  identity (event IDs, exclusion reasons, cohort sha256 `67f283e2…`, source
  receipt sha256 `e38e953f…`, expected count, locked statistics) rather than a
  synthetic count. The audit test asserts the inferential gate **rejects** the
  17-event cohort.
- `123bbaa59` — §3.4 count corrected to "15 measured, 5 excluded … 2 failed the
  off-source control". Prose only; no figure altered.
- `509e20372` — §7's two "6/17" citations labeled as the availability-only
  diagnostic cohort, explicitly not the preregistered inferential sample.

**Positive control (Rule 26):** the real off-source-controlled artifact
`study3_coincidence.json` now passes its own gate — `status: pass`, 15/15, ρ =
−0.9273, median err = 0.0758, `reason: null`. Suite: 22 passed.

Independently reproduced for the diagnostic side too: an availability-only run
(same rule `coincidence_audit_gwtc3.py` applies) yields 17 measured / 11
coincident = **6/17 non-coincident**, ρ = **−0.936** — matching §7 exactly. Both
cohorts are real; neither was wrong; they were merely conflated under one
number.

## Why this is kept

The failure had no symptom. Five green positive-control tests, a passing suite,
and a published section all agreed on a number that matched no cohort — because
they all inherited it from the same stale source. Nothing threw, nothing
alerted. Cf. `project-aigis-fatal-exit-preempts-safe-cleanup` and the analyzer's
`bfloat16`/`float16` constant (fixed `a50ec61`), which would have burned a
7-hour whole-stack window for zero result. Same signature every time: **a
confident green that no gate could have gone red on.**
