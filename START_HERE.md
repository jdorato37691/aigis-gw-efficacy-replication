# AIGIS GW inspiral-template-efficacy replication bundle

Built 20260717T115457Z at git HEAD `9365ae751e4d3b87564f9657ab3481624cf8218b`
(research(gw): builder emits ssh-signing push+tag natively (operator has no gpg key)).

Start with the runbook:
`docs/research/papers/gw-inspiral-template-efficacy/REPLICATION.md`

Integrity: verify `MANIFEST.sha256` (the anchor), then read `BUILD_INFO.json`
and `READINESS_AT_BUILD.json`. `BUNDLE_SHA256` is the sha256 of `MANIFEST.sha256`.

## Operator push+tag (ssh-signing; run from this directory)

This is the operator's single identity-bearing step; nothing runs it
automatically. git's ssh-signing mode is used because no gpg signing key
is configured on the build machine; the SSH key already used for GitHub
auth signs the tag. The tag message binds the bundle hash at tag time via
`$(cat BUNDLE_SHA256)`, so this block needs no manual hash edit. One
decision: replace `<YOUR_PUBLIC_REMOTE_URL>` -- or create the repo first
with `gh repo create aigis-gw-efficacy-replication --public --source=.
--push` from inside this directory after the commit step, then skip the
remote/push lines.

```bash
cd ~/.aigis/research/gw_replication/bundle/aigis-gw-efficacy-bundle-20260717T115457Z
git init -q
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
git add -A
git commit -qm "AIGIS GW inspiral-template-efficacy replication bundle"
git tag -s aigis-gw-efficacy-20260717 -m "BUNDLE_SHA256=$(cat BUNDLE_SHA256)"
git remote add origin <YOUR_PUBLIC_REMOTE_URL>
git push -u origin HEAD --tags
```

For the tag signature to show "Verified" on GitHub, also register the same
key as a SIGNING key (it may currently be registered for auth only):
`gh ssh-key add ~/.ssh/id_ed25519.pub --type signing`
