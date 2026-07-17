# Preregistration addendum: PSD-robustness artifact regimes (referee item 2)

**Program:** CHARTER.md moonshot lane / G3 track · **Preregistered:** 2026-07-16
(committed before the four-regime artifact run) · **Parent studies:**
[`2026-07-12-gwtc1-taylorf2-efficacy.md`](2026-07-12-gwtc1-taylorf2-efficacy.md)
(the locked GWTC-1 sweep, event set, and Study-1 pipeline) and
[`2026-07-12-gw170817-matched-filter.md`](2026-07-12-gw170817-matched-filter.md)
(the locked mechanical glitch-gate rule reused below).

## Purpose

Referee item 2 asks whether the recovered mass trend (Spearman rho = -0.891 in
Study 1, one on-source Welch-mean-4s PSD per event) is an artifact of the PSD
estimator rather than a real inspiral-only template-truncation effect. This
addendum locks the four PSD-estimation regimes and the two genuinely novel
physics decisions (the gating protocol and the off-source PSD segment choice)
so the `aigis.gw.psd_robustness.v1` artifact cannot be reverse-engineered to a
pass. The mass trend is recomputed under each regime; a regime that loses the
locked rho <= -0.5 trend is an honest `fail`, not a readiness pass.

This is method characterization, not a detection claim. `belief_moved = false`.
Single pass over the ten locked GWTC-1 BBH events; the study registers
regardless of outcome.

## Fixed pipeline (inherited, unchanged)

Identical to the Study-1 GWTC-1 sweep: detectors H1+L1; on-source
`[gps-16, gps+16]` (32 s); TaylorF2 3.5PN template at the locked catalog masses;
band `[30, 2048] Hz`; template-peak time convention; recovered network statistic
= quadrature of the two independently maximized single-detector peak SNRs within
+/-0.1 s of the catalog GPS; `R = recovered / published`. Only the PSD used to
whiten the on-source data changes between regimes. The frozen
`matched_filter_gw150914.py` statistic code is not modified; regimes are driven
entirely through its existing `psd_override` and `_fetch_strain` seams.

## The four locked regimes (schema field `psd_config`)

1. **`onsource_welch_mean_4s`** — PSD estimated from the on-source segment
   itself, Welch average = mean, 4 s FFT (nperseg = 4*4096, 50% overlap). This
   is the Study-1 confirm configuration exactly; it is the positive control and
   must reproduce the Study-1 per-event `recovery_fraction` to within rounding.

2. **`offsource_welch_mean_4s`** — PSD estimated from an off-source segment
   (Welch mean, 4 s), then used to whiten the same on-source data. Off-source
   segment selection reuses the Study-1 mechanical NaN-fallback candidate chain
   `[gps-272,gps-240], [gps+240,gps+272], [gps-528,gps-496], [gps+496,gps+528]`
   (first NaN-free candidate wins). This is the standard practice of estimating
   the noise PSD from data adjacent to but not containing the signal, so the
   signal cannot bias its own whitening spectrum.

3. **`onsource_welch_median_many_4s`** — PSD estimated from the on-source
   segment, Welch average = **median**, 4 s FFT. Over the 32 s segment at 4 s /
   50% overlap this is 15 averaged segments ("many-average"), the median-of-many
   estimator that is robust to non-stationary outlier segments.

4. **`gated_onsource_welch_mean_4s`** — loud pre-merger transients are excised
   from the on-source data by the locked mechanical gate below; the PSD (Welch
   mean, 4 s) and the matched filter are then computed on the gated data.

## Locked gating protocol (novel decision 1)

Reuses the mechanical glitch-gate already locked in the GW170817 prereg and
implemented in `gw_event_replication.py`, with the ONLY generalization being
that it is applied symmetrically to both H1 and L1 across all ten events rather
than to L1 for one event. Locked parameters (identical values, decided in the
parent prereg without peeking at these results):

- `threshold_sigma = 15.0` — a sample is a gate candidate only if its whitened
  amplitude exceeds 15 standard deviations of the segment-interior whitened
  baseline. Genuine blip/scattered-light glitches reach z ~ 50-1000; an
  integrated-SNR ~10-25 inspiral does not produce per-sample z >= 15, so this
  threshold excises non-Gaussian transients without touching the signal.
- `window_before_tc = (2.0, 0.5)` s — the gate SEARCHES ONLY the interval
  `[tc-2.0, tc-0.5]`. This window is strictly earlier than the +/-0.1 s
  recovery peak-search window around the catalog GPS, so gating can never excise
  the merger/ringdown samples where recovery is measured. Signal protection is
  the reason the window excludes tc, exactly as in the parent rule.
- `gate_half_width_s = 0.2`, `taper_s = 0.1` — on firing, the loudest in-window
  sample is gated by multiplying a `2*0.2` s region by an inverse-Tukey window
  (0.1 s cosine taper), smoothly zeroing the transient.

Whitening for the gate detector uses a Welch (mean, 4 s) PSD, matching the
parent implementation. If no in-window sample exceeds the threshold the gate
does not fire and the gated regime equals the on-source-mean regime for that
detector-event; a null gate on clean segments is a valid, reported result
(`gate_fired = false`), not a failure.

## Off-source PSD segment (novel decision 2)

Locked to the Study-1 mechanical candidate chain above (already committed in the
GWTC-1 efficacy prereg). No per-event hand-selection: the first NaN-free
candidate in the fixed order is used, and its GPS bounds are recorded in the
strain manifest that the artifact hashes.

## Artifact + acceptance

- Output: `aigis.gw.psd_robustness.v1` at
  `docs/research/papers/gw-inspiral-template-efficacy/verification/psd_robustness.json`,
  with a `strain_manifest_sha256` over the per-(event, detector, regime) segment
  bounds and sample rate, and 40 rows (10 events x 4 regimes) carrying `event`,
  `psd_config`, `m_total_det`, and `recovery_fraction`.
- The validator `summarize_psd_robustness` recomputes, per regime, the Spearman
  rho between detector-frame total mass and recovery.
- **Acceptance (locked):** the trend criterion is `rho <= -0.5` in EVERY one of
  the four required regimes. A structurally complete artifact in which any
  regime yields `rho > -0.5` is an honest `fail` (the mass trend was
  PSD-sensitive) and is written, reported, and preserved as such. No regime,
  event, or window may be dropped to recover a pass.

## Stopping rule (locked)

One sweep pass: one recovery per (event, regime). No re-runs, no parameter
changes after results. Data-availability fallbacks are the mechanical off-source
chain above. The study registers REGARDLESS of the rho outcome in any regime.
