# Replication protocol: Study 6 sourced-PhenomD phase (independent re-run)

**Program:** CHARTER G3 track, Study 6 replication · **Locked:** 2026-07-12
(committed before the replication run) **Target:** exp_83871cc6eeadf4d1b80ec4d8
(externally_grounded, all four Study-6 predictions passed; confirm receipt
`PHENOMD_phase_20260712T032158Z.json`).

## Independence basis (the same distinct-executor pattern as the three named event replications)

- PSD estimator changed: Welch **median**, **16 s** segments (confirm used Welch
  mean, 4 s) — the `run_replicate` code path.
- Executor identity: `matched_filter_replicator` (digest includes host),
  distinct from `matched_filter_pipeline`.
- Templates rebuilt from the committed code and the sha256-verified coefficient
  artifact; all G6 integrity gates must re-pass before any measurement.
- Independence is derived from these digests by the registry, never asserted.

## Event set (locked)

The 13 events measured in the confirm pass (7 heavy GWTC-1 + 6 heavy GWTC-3;
GW191230 stays excluded — it failed its off-source control in the confirm pass
and gets no replication attempt). Per-event off-source known-bad (< 8) re-run
under the replication configuration; an event failing it drops from the
replication comparison rather than being forced.

## Locked criteria (all three required for outcome CONFIRMED)

- **R1 (headline):** median R over the measured heavy GWTC-1 events ≥ **0.65**
  AND within **±0.10 absolute** of the confirm median 0.902.
- **R2 (OOS arm):** median R over the measured GWTC-3 events ≥ **0.408**.
- **R3 (per-event agreement):** median |R_replicate − R_confirm| over all
  measured events ≤ **0.10**.

Failure of any criterion → the reproduction attempt is recorded with a FAILED
outcome (preserved negative; the record does NOT advance). No re-runs, no
threshold edits.

## Promotion rule (locked)

One `append_reproduction` call binding the replication receipt
(`aigis.scientific_evidence_receipt`-style reproduction receipt with target +
run digests). CONFIRMED on all three criteria advances the record along the
registry's own independence derivation (expected: experimentally_validated); the
rung is verified by a raw Redis re-read, not the return value alone. Paper §3.6
and the memory file updated either way.
