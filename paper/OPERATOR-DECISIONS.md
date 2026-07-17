# Operator decision brief — GW efficacy package (2026-07-16)

**State at HEAD:** six verification gates executed — **5 pass / 1 fail**;
`claim_scope: pass`; `epistemic_status: major_revision_open`. The paper carries
the full honest record: the oracle fail-diagnosis-completion arc, the posterior
trend/curve split, the fresh-holdout confirmation, and a two-pass condition-1
literature positioning ("no claim cleanly novel as a relationship; the
measurement, verification, attribution, and mechanized integration survive").

Two decisions are yours; both come with a decided recommendation to veto rather
than a menu to choose from.

---

## Decision B — the posterior gate (contract vs claim)

> **Status: APPROVED & EXECUTED (2026-07-17).** Contract v3 landed in
> `scripts/research/gw_evidence_controls.py`
> (`summarize_posterior_uncertainty`): the posterior gate now PASSES on the O1
> trend criterion alone, and the original O2 per-draw curve criterion is
> preserved in the gate output as a `withdrawn_claim_record` carrying its
> original `fail` verdict (54/100 draws) plus the v3 authorization stamp (which
> references this brief, commit `13eb7b848`). All six readiness gates now pass,
> so `gw_package_readiness.py` reports
> `epistemic_status: analysis_ready_for_external_review`. `external_ready` stays
> hardcoded false (Decision C not executed here).

The sole failing gate (`posterior_uncertainty`) tests the ORIGINAL claim: the
prediction curve robust under posterior draws (>= 90% of draws with median |R -
R_hat| <= 0.15; observed 54%). The revised paper **no longer makes that claim**
— it claims point-estimate-conditional transfer only, and the trend criterion
passed 98/100 draws. The gate now audits a withdrawn claim, so the package is
terminally `major_revision_open` under the all-pass contract.

**Recommendation: authorize contract v3 for this one gate**, transparently:
replace the per-draw curve criterion with the trend-only posterior criterion
(matching the paper's actual claim), keep the original gate definition, its fail
verdict, and the artifact preserved in the contract file as the record of the
withdrawn claim, and commit the change with your sign-off noted. This is
goalpost movement done in the open with the PI's signature — the Genesis-P0
pattern (preserve the stop, correct the record). I have deliberately not touched
the contract; charter §0 makes this yours.

- Veto path: leave as-is. The package stays honest and permanently
  `major_revision_open`; external review can still read it, with the mismatch
  explained in the status header (already written there).

## Decision C — the external lane

> **Status: APPROVED & EXECUTED BY DELEGATION (2026-07-17).** At the operator's
> explicit in-session instruction ("you go"), the agent pushed the final bundle
> (`aigis-gw-efficacy-bundle-20260717T115457Z`, 83 files) to the public remote
> https://github.com/jdorato37691/aigis-gw-efficacy-replication with ssh-signed
> tag `aigis-gw-efficacy-20260717` binding
> `BUNDLE_SHA256=adb1b336fa5e8f01c47e3f4a11ba94bdf080f9d6cf6c65eaa277dc70afb33deb`.
> Delegation is recorded in the bundle commit message. GitHub "Verified" badge
> pends one operator step
> (`gh auth refresh -h github.com -s admin:ssh_signing_key` then
> `gh ssh-key add ~/.ssh/id_ed25519.pub --type signing`). Decision D's personal
> ask remains the operator's.

`external_ready` is hardcoded false by design: it demands an external immutable
trust anchor and an attestation validator that deliberately do not exist
locally. The ceiling AIGIS reaches alone is `analysis_ready_for_external_review`
(reachable only after Decision B).

**Recommendation:** after B, I assemble the replication bundle (paper + preregs

- receipts + verification artifacts + runnable pipeline + data refs, content
  hash over the bundle), you push it to a public repository and sign the tag —
  the remote + signature is the minimal external trust anchor — and the single
  identity-bearing action left is yours: hand the bundle to one independent
  replicator.

## Decision D — the edge (decided, as asked)

The novelty hunts keep concluding "needs operator-seeded edge." My call on what
to seed: **not new data — one human.** The highest-EV move available to this
institution is completing conditions 4/5 on the paper's narrow surviving claims
via ONE independent replication. The bundle makes replication approximately one
command; the edge being spent is your identity/social capital on a single ask (a
GW-adjacent colleague, or the GWOSC/open-data-workshop community). A
preregistered, receipted, machine-audited result independently replicated by an
external party would be the institution's first full Discovery-Standard crossing
— and the charter already says one replicated moderate result outranks fifty
conjectures. Everything else (new domains, new data purchases) is worse EV until
this loop closes once.

## Cheap follow-ups (no decision needed; I can run these on request)

- Residual scoop-risk sweep: 2025-26 arXiv / GWTC-4-era TGR papers, thesis
  repositories, LVK DCC (the positioning memo's stated remaining risk).
- The C4 methodology-adjacent venues (W3C PROV, registered reports, ACM REP).

---

_All numbers and verdicts in this brief trace to: `verification/*.json`,
`literature-positioning.md`, and the readiness auditor output at commit
`d66eddd5b`. belief_moved=false; this brief allocates nothing._
