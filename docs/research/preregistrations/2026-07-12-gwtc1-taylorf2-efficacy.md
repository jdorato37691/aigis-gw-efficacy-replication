# Preregistration: GWTC-1 inspiral-only template efficacy characterization

**Program:** CHARTER.md moonshot lane (10%) / G3 track · **Preregistered:**
2026-07-12 (committed before any sweep run) **Study question:** how much of the
published matched-filter network SNR does an inspiral-only TaylorF2 template
recover across the GWTC-1 BBH population, as a function of detector-frame total
mass?

This is a method-characterization benchmark, not a set of detection claims.
Heavy binaries merge at low frequency (f_ISCO ≈ 4400/M_det Hz), so an
inspiral-only filter should lose the merger–ringdown SNR share as mass grows.
Quantifying that curve with one fixed, validated pipeline is the deliverable.

## Event set + published values (locked; GWTC-1-confident via the eventapi, fetched pre-registration)

| Event    | GPS          | published net SNR | m1/m2 (source) | z    | M_total_det (M☉) |
| -------- | ------------ | ----------------- | -------------- | ---- | ---------------- |
| GW170608 | 1180922494.5 | 15.4              | 11.0/7.6       | 0.07 | 19.9             |
| GW151226 | 1135136350.6 | 13.1              | 13.7/7.7       | 0.09 | 23.3             |
| GW151012 | 1128678900.4 | 10.0              | 23.2/13.6      | 0.21 | 44.5             |
| GW170104 | 1167559936.6 | 13.0              | 30.8/20.0      | 0.20 | 61.0             |
| GW170814 | 1186741861.5 | 17.2              | 30.6/25.2      | 0.12 | 62.5             |
| GW170809 | 1186302519.8 | 12.4              | 35.0/23.8      | 0.20 | 70.6             |
| GW150914 | 1126259462.4 | 25.2              | 35.6/30.6      | 0.09 | 72.2             |
| GW170818 | 1187058327.1 | 11.3              | 35.4/26.7      | 0.21 | 75.1             |
| GW170823 | 1187529256.5 | 11.5              | 39.5/29.0      | 0.35 | 92.5             |
| GW170729 | 1185389807.3 | 10.8              | 50.2/34.0      | 0.49 | 125.5            |

GW170817 (M_det ≈ 2.78, R = 30.48/32.4 = 0.94 from the validated program's
existing receipts) serves as the low-mass anchor; it is not re-run.

## Pipeline (locked — the validated instrument, one configuration for all)

- Detectors H1+L1; on-source **[gps−16, gps+16]** (32 s); Welch mean 4 s PSD;
  band **[30, 2048] Hz**; template-peak time convention.
- Template per event: TaylorF2 3.5PN with the LOCKED table masses
  (detector-frame: source × (1+z)), f_low = 30 Hz, f_cut = ISCO. Events whose
  ISCO approaches the band floor keep their honest tiny band — a near-empty band
  yielding R ≈ 0 is a measurement, not a failure.
- Off-source control per event: **[gps−272, gps−240]**, mechanical NaN fallback
  chain (+240..+272, then −512, then +512 offsets); all-NaN after the chain →
  event marked data_unavailable and excluded (documented).
- Per-event metrics: recovered network SNR (peak within ±0.1 s of catalog GPS),
  **R = recovered / published**, off-source segment-wide max.

## Preregistered hypotheses

- **H1 (low-mass adequacy):** R ≥ 0.85 for every event with M_total_det < 30 M☉
  (GW170608, GW151226; anchor GW170817).
- **H2 (mass dependence):** Spearman ρ(M_total_det, R) ≤ **−0.6** across the 10
  BBH events.
- **H3 (instrument validity, Rule 26, per event):** off-source network max < 8;
  an event failing H3 yields NO verdict and is excluded from H1/H2.

Falsifiers: H1 fails if any sub-30 event recovers < 0.85; H2 fails if ρ > −0.6
(e.g. mass does not organize the loss — which would itself be a
publishable-grade surprise about PSD-dominated recovery).

## Stopping rule (locked)

One sweep pass (one on-source + one off-source run per event). No re-runs, no
parameter changes after results. Data-availability fallbacks are mechanical
(above). The study is registered REGARDLESS of hypothesis outcomes.

## Promotion rule (locked)

The study registers as ONE experiment (source `gw_replication`, the
characterization study) with the sweep table as its result and the receipt as
receipt-bound EXTERNAL_EXPERIMENTAL_RESULT evidence (real strain, real
recoveries). Single-pass study → ceiling **externally_grounded**; no per-event
validation claims are made from single runs, and no event promotes to
experimentally_validated via this sweep.
