# Preregistration: coincidence-enforcing network statistic (instrument v2)

**Program:** CHARTER G3 track, instrument upgrade + Study-6 replication
re-measure · **Preregistered:** 2026-07-12 (committed before any on-source v2
run) **Motivating finding:** referee review F3 + the V1 coincidence audit
(receipt `STUDY6_review_coincidence_audit_20260712T040807Z.json`): the v1
network statistic takes independent per-detector maxima within ±0.1 s of catalog
time, so nothing enforces H1-L1 arrival consistency — three replication rows
(GW200128 94 ms, GW200219 185 ms, GW200220 140 ms with a 39.0σ H1 transient)
formed exactly this way.

## The v2 statistic (locked)

Per event, both detectors' full SNR series are rolled to merger-time indexing
(`snr_t = roll(snr, tpl_peak_idx)`, monotonic times). Then:

    v2 = max over samples j in the search window of
         sqrt( snrH[j]^2 + max_{|k-j| <= 10 ms} snrL[k]^2 )
    subject to BOTH factors >= 4.0 (per-detector significance floor)

- 10 ms = H1-L1 light-travel bound (41 samples at 4096 Hz), implemented as a
  sliding maximum filter — O(n).
- The 4.0 floor is what rejects single-detector transients: a loud H1 glitch
  paired only with sub-floor L1 noise contributes no valid pair.
- If no pair passes the floor, v2 = 0.0 with flag `no_coincident_pair`.
- Search windows identical to v1 (±0.1 s of catalog time on-source; interior of
  the segment off-source).
- v1 code paths are untouched; v2 is a new module
  (`scripts/research/coincident_network.py`).

## Positive/negative controls in code (Rule 26, data-free, run before use)

Synthetic twin-bump control: two series with coincident bumps (dt = 5 ms) must
yield v2 = quadrature of the bump peaks; moving one bump to dt = 50 ms with only
noise nearby must reject the cross-pair (v2 falls to the noise pairing or
`no_coincident_pair`). Both assertions must pass on import of the gate runner.

## Preregistered predictions (locked)

- **C1 (identity on coincident data):** for all 13 Study-6 confirm rows (cached
  strain, worst v1 pair separation 8.8 ms < 10 ms), |v2 − v1|/v1 < **0.005**.
  The statistic must not change clean measurements.
- **C2 (glitch rejection, the point):** on the 3 non-coincident replicate rows,
  v2 < v1 strictly; specifically GW200220's replicate v2 ≤ **20** (v1 = 39.56 —
  the H1 transient must not survive the pairing floor).
- **C3 (known-bad):** on every event's off-source control segment, v2 ≤ v1 and
  v2 < **8**.
- **C4 (dual-detector injection):** a calibrated waveform injected into BOTH
  detectors' off-source noise (target single-detector SNR 20 each, +5 ms L1
  offset) must be recovered at v2 = √800 ≈ 28.3 within **±25%**, with the
  maximizing pair separation ≤ 10 ms.
- **C5 (replication criteria under v2):** re-measuring all 13 replication rows
  (Welch-median 16 s, `matched_filter_replicator`) with v2: R1 median heavy
  GWTC-1 ≥ 0.65 AND within ±0.10 of 0.902; R2 median GWTC-3 ≥ 0.408 (now on all
  6 measured events, coincident by construction); R3 median |R_v2 − R_confirm| ≤
  0.10. Falsifier: C5 failing means the GWTC-3 replication arm's recoveries do
  not survive coincidence enforcement — a preserved negative reported in the
  paper; the existing v1 reproduction verdict stands on its own locked protocol
  either way.

## Registry action (locked)

One additional reproduction attempt appended to exp_83871cc6eeadf4d1b80ec4d8
with `method_id="welch_median_16s_coincident_v2"`, outcome CONFIRMED iff C5
passes (FAILED otherwise), receipt-bound. One pass; no re-runs; no threshold
edits. Paper §3.6/§5 and the memory file updated either way.
