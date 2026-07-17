#!/usr/bin/env python3
"""Deterministic replication-bundle builder for the GW inspiral-template-efficacy package.

Assembles a self-contained, content-addressed replication bundle from the
COMMITTED package state (git HEAD) plus the receipts, environment manifests, and
referenced preregistration/pipeline code the package's claims rest on. The goal
is to make independent replication approximately one command: hand the produced
directory (or its tar.gz) to a replicator, and every input travels with it,
hash-anchored.

Design contract (Decision C, OPERATOR-DECISIONS.md):

  * Committed state only. Every git-tracked file is read from ``git HEAD``, never
    from the working tree, so a stray uncommitted edit cannot leak into the
    bundle and re-running at the same HEAD is reproducible. Receipts and venv
    package lists (not tracked in git) come from the live filesystem.
  * The builder READS the repository and receipt store; it MUTATES nothing in the
    repo and moves no belief. Its only writes are under the output bundle
    directory. It sends nothing and pushes nothing.
  * Receipts are enumerated MECHANICALLY: a receipt from ``~/.aigis/research/
    gw_replication/`` is bundled only if its sha256 or its basename is referenced
    by a committed verification artifact, the paper text, or a bundled
    preregistration. The 3000-file receipt store is never bulk-copied.
  * The MANIFEST.sha256 is the integrity anchor. Files are hashed in a fixed
    sorted order; ``BUNDLE_SHA256`` is the sha256 of the manifest file. Re-running
    at the same git HEAD with the same receipts reproduces identical MANIFEST and
    BUNDLE hashes, EXCEPT the two ``environment/*.freeze.txt`` snapshots, which are
    point-in-time and are the only expected source of drift. The tar.gz is not
    byte-reproducible (embedded mtimes); compare the MANIFEST, not the tarball.
  * A secrets/keys safety scan runs before finalizing. Credential-class findings
    are hard blockers (the tar.gz is not written and the builder exits nonzero).
    Home-directory path strings are reported as informational only: receipts
    legitimately record ``~/.aigis/...`` run paths.
  * ``DRAFT-ASK.md`` (the operator's outreach draft, Decision D) is deliberately
    excluded from the replicator-facing bundle, and the operator push+tag
    runsheet (START_HERE) is written OUTSIDE the bundle as a sibling file.
  * Layout is replicator-first (v2): README.md + REPLICATION.md at root, then
    paper/, preregistrations/, scripts/research/, receipts/, environment/,
    audit/, plus a docs/ compatibility symlink into paper/ that keeps the
    pipeline code runnable unmodified.

Usage:
    .venv/bin/python3 scripts/research/build_replication_bundle.py
    .venv/bin/python3 scripts/research/build_replication_bundle.py --dry-run
    .venv/bin/python3 scripts/research/build_replication_bundle.py --output-root /tmp/bundles
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_REL = "docs/research/papers/gw-inspiral-template-efficacy"
PREREG_REL = "docs/research/preregistrations"
SCRIPTS_REL = "scripts/research"
RECEIPTS_DIR = Path.home() / ".aigis" / "research" / "gw_replication"
MAIN_VENV_PY = REPO_ROOT / ".venv" / "bin" / "python3"
LAL_VENV_PY = Path.home() / ".aigis" / "research" / "lal_venv" / "bin" / "python"
DEFAULT_OUTPUT_ROOT = RECEIPTS_DIR / "bundle"

# Package files that are deliverables for the operator, not the replicator.
EXCLUDE_FROM_BUNDLE = {f"{PACKAGE_REL}/DRAFT-ASK.md"}

# --- Replicator-first bundle layout (v2, PI-requested restructure) -----------
# The v1 bundle mirrored internal repo paths (docs/research/papers/...); the PI
# review called the public repo "messy". v2 presents a shallow tree:
#   README.md REPLICATION.md MANIFEST.sha256 BUNDLE_SHA256
#   paper/ preregistrations/ scripts/research/ receipts/ environment/ audit/
# Scripts stay nested at scripts/research/ because they resolve repo-relative
# paths from __file__ (REPO_ROOT = parents[2]) and import siblings; flattening
# would break them. A relative symlink docs/research/papers/<package> -> paper/
# keeps the pipeline code runnable UNMODIFIED: the readiness auditor and the
# gate runners find the package dir through the symlink (macOS/Linux only).
_PACKAGE_TO_ROOT = {
    f"{PACKAGE_REL}/REPLICATION.md": "REPLICATION.md",
    f"{PACKAGE_REL}/BUNDLE-README.md": "README.md",
}
_COMPAT_SYMLINK_PARENT = "docs/research/papers"
_COMPAT_SYMLINK_NAME = "gw-inspiral-template-efficacy"
_COMPAT_SYMLINK_TARGET = "../../../paper"


def bundle_dest_rel(rel: str) -> str:
    """Map a repo-relative tracked path to its replicator-first bundle path."""
    if rel in _PACKAGE_TO_ROOT:
        return _PACKAGE_TO_ROOT[rel]
    if rel.startswith(f"{PACKAGE_REL}/"):
        return "paper/" + rel[len(PACKAGE_REL) + 1 :]
    if rel.startswith(f"{PREREG_REL}/"):
        return "preregistrations/" + rel[len(PREREG_REL) + 1 :]
    return rel  # scripts/... keep their nesting for runnability


# --- Pipeline + verification code the bundle must carry -----------------------
# The paper's section 1 lists the pipeline scripts; the six-gate verification
# runners and their sibling code dependencies are added so the bundled
# gw_package_readiness.py audit runs correctly against the bundled artifacts.
# gw_package_readiness.audit_script_scope REQUIRES six scope-audit files to be
# present (imr_heavy_study, imr_coherence_study, phenomd_phase_study,
# phenomd_phase_replication, gw_event_replication, promote_gw150914) or it fails
# closed -- all six are included below.
BUNDLED_SCRIPTS: tuple[str, ...] = (
    "build_replication_bundle.py",  # this builder, so the bundle documents its own provenance
    "fresh_holdout_study.py",
    "gw_evidence_controls.py",
    "gw_event_replication.py",
    "gw_package_readiness.py",
    "gwtc1_aligned_spin_study.py",
    "gwtc1_taylorf2_sweep.py",
    "gwtc3_oos_study.py",
    "imr_coherence_study.py",
    "imr_heavy_study.py",
    "lal_oracle_compare.py",
    "matched_filter_gw150914.py",
    "phenomd_coefficients.py",
    "phenomd_phase.py",
    "phenomd_phase_replication.py",
    "phenomd_phase_study.py",
    "posterior_propagation.py",
    "promote_gw150914.py",
    "psd_robustness_sweep.py",
    "sourced_physics.py",
    "study3_coincidence_gate.py",
    "taylorf2.py",
)

# Preregistrations are selected by glob-token match OR explicit reference in the
# package text; the union is bundled. Every prereg governing a study or gate
# carries a token below.
_PREREG_TOKENS = re.compile(
    r"gw\d|gwtc|phenomd|holdout|psd|oracle|taylor|aligned|imr|virgo|chi2|coincid|sourced|matched-filter",
    re.IGNORECASE,
)
_PREREG_NAME_RE = re.compile(r"20\d{2}-\d{2}-\d{2}-[a-z0-9-]+\.md")

_SHA256_RE = re.compile(r"\b[a-f0-9]{64}\b")
_RECEIPT_NAME_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_]*_(?:[0-9]{8}T[0-9]{6}Z|latest|checkpoint|template)\.(?:json|hdf5|npz|npy|csv)"
)

# Credential-class blockers: an opaque value bound to a secret-ish key, or a PEM
# private-key header. These abort the build.
_CRED_BLOCKER_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r"|\b(?:api[_-]?key|secret|token|passphrase|password|aws_secret_access_key|bearer)\b"
    r"\s*[:=]\s*[\"']?[A-Za-z0-9/+_.\-]{16,}",
    re.IGNORECASE,
)
# Informational keyword hits (may be prose such as "approval-token"): reported,
# not blocking.
_CRED_KEYWORD_RE = re.compile(r"api[_-]?key|secret|token|passphrase|-----BEGIN", re.IGNORECASE)
_HOME_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.-]+|~/\.aigis")

_TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".csv", ".cfg", ".toml", ".yaml", ".yml"}
_SCAN_SUFFIXES = {".md", ".json", ".txt"}


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], *, cwd: Path | None = None, text: bool = True) -> tuple[int, Any, Any]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=text,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ---------------------------------------------------------------------------
# Git (committed-state) helpers
# ---------------------------------------------------------------------------
def git_head_sha() -> str:
    code, out, _ = _run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    return out.strip() if code == 0 else "unknown"


def git_head_subject() -> str:
    code, out, _ = _run(["git", "log", "-1", "--pretty=%s"], cwd=REPO_ROOT)
    return out.strip() if code == 0 else "unknown"


def git_tracked_files(pathspec: str) -> list[str]:
    """Repo-relative paths committed under the given pathspec at HEAD."""
    code, out, _ = _run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", pathspec], cwd=REPO_ROOT)
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def git_is_tracked(relpath: str) -> bool:
    code, _, _ = _run(["git", "cat-file", "-e", f"HEAD:{relpath}"], cwd=REPO_ROOT)
    return code == 0


def git_show_bytes(relpath: str) -> bytes:
    code, out, _ = _run(["git", "show", f"HEAD:{relpath}"], cwd=REPO_ROOT, text=False)
    if code != 0:
        raise RuntimeError(f"git show failed for {relpath}")
    return out


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Selection (committed content)
# ---------------------------------------------------------------------------
def select_package_rel_files() -> list[str]:
    return sorted(f for f in git_tracked_files(PACKAGE_REL) if f not in EXCLUDE_FROM_BUNDLE)


def select_prereg_rel_files(package_texts: dict[str, str]) -> list[str]:
    referenced: set[str] = set()
    for text in package_texts.values():
        referenced.update(_PREREG_NAME_RE.findall(text))
    selected: set[str] = set()
    for rel in git_tracked_files(PREREG_REL):
        name = rel.rsplit("/", 1)[-1]
        if name in referenced or _PREREG_TOKENS.search(name):
            selected.add(rel)
    return sorted(selected)


def select_script_rel_files() -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for name in BUNDLED_SCRIPTS:
        rel = f"{SCRIPTS_REL}/{name}"
        if git_is_tracked(rel):
            present.append(rel)
        else:
            missing.append(name)
    return sorted(present), missing


def collect_referenced_receipt_refs(rel_files: list[str], head_bytes: dict[str, bytes]) -> tuple[set[str], set[str]]:
    hashes: set[str] = set()
    names: set[str] = set()
    for rel in rel_files:
        if Path(rel).suffix.lower() not in _SCAN_SUFFIXES:
            continue
        text = _decode(head_bytes[rel])
        hashes.update(_SHA256_RE.findall(text))
        names.update(_RECEIPT_NAME_RE.findall(text))
    return hashes, names


def select_receipts(ref_hashes: set[str], ref_names: set[str]) -> tuple[list[Path], dict[str, list[str]]]:
    if not RECEIPTS_DIR.is_dir():
        return [], {"missing_receipt_dir": [str(RECEIPTS_DIR)]}
    matched: dict[Path, str] = {}
    by_name: list[str] = []
    by_hash: list[str] = []
    files = sorted(p for p in RECEIPTS_DIR.iterdir() if p.is_file())
    for path in files:
        if path.name in ref_names:
            matched[path] = "name"
            by_name.append(path.name)
    for path in files:
        if path in matched:
            continue
        if _sha256_file(path) in ref_hashes:
            matched[path] = "hash"
            by_hash.append(path.name)
    return sorted(matched), {"by_name": sorted(by_name), "by_hash": sorted(by_hash)}


# ---------------------------------------------------------------------------
# Environment manifests
# ---------------------------------------------------------------------------
def _freeze(python_path: Path) -> tuple[str, str]:
    if not python_path.exists():
        return f"# venv python not found: {python_path}\n", "missing"
    code, out, _ = _run(["uv", "pip", "list", "--python", str(python_path), "--format=freeze"])
    if code == 0 and out.strip():
        return out, "uv pip list --format=freeze"
    code, out, _ = _run([str(python_path), "-m", "pip", "freeze"])
    if code == 0 and out.strip():
        return out, "python -m pip freeze"
    return f"# freeze failed for {python_path}\n", "failed"


def _lal_oracle_env(python_path: Path) -> tuple[str, str | None]:
    if not python_path.exists():
        return f"# lal venv python not found: {python_path}\n", None
    snippet = (
        "import hashlib\n"
        "from importlib.metadata import distributions\n"
        "pkgs = sorted(f\"{d.metadata['Name']}=={d.version}\" for d in distributions() if d.metadata['Name'])\n"
        "body = '\\n'.join(pkgs)\n"
        "print(hashlib.sha256(body.encode('utf-8')).hexdigest())\n"
        "print(body)\n"
    )
    code, out, _ = _run([str(python_path), "-c", snippet])
    if code != 0 or not out.strip():
        return f"# oracle-env computation failed for {python_path}\n", None
    lines = out.splitlines()
    digest = lines[0].strip()
    listing = "\n".join(lines[1:])
    text = (
        "# lal_venv oracle environment description\n"
        "# Algorithm mirrors scripts/research/lal_oracle_compare._oracle_environment_sha256:\n"
        "#   sha256 of the newline-joined, sorted 'Name==version' importlib.metadata list.\n"
        "# This value should equal verification/phenomd_external_oracle.json:oracle_environment_sha256\n"
        "# for a byte-identical oracle environment. Date-versioned transitive deps (e.g.\n"
        "# astropy-iers-data) drift daily, so a mismatch here does NOT invalidate the oracle\n"
        "# result -- the load-bearing package is lalsuite/lalsimulation.\n"
        f"oracle_environment_sha256 = {digest}\n\n"
        f"{listing}\n"
    )
    return text, digest


def _python_version(python_path: Path) -> str:
    if not python_path.exists():
        return "unknown"
    code, out, _ = _run([str(python_path), "-c", "import sys;print(sys.version.split()[0])"])
    return out.strip() if code == 0 else "unknown"


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------
def safety_scan(staged_files: list[Path], bundle_root: Path) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    keyword_hits: list[dict[str, str]] = []
    home_path_files: list[str] = []
    binary_skipped: list[str] = []
    for path in staged_files:
        rel = str(path.relative_to(bundle_root))
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            binary_skipped.append(rel)
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            binary_skipped.append(rel)
            continue
        blockers.extend(
            {"file": rel, "match": m.group(0)[:24] + "...[REDACTED]"} for m in _CRED_BLOCKER_RE.finditer(text)
        )
        kw = _CRED_KEYWORD_RE.search(text)
        if kw:
            keyword_hits.append({"file": rel, "keyword": kw.group(0)})
        if _HOME_PATH_RE.search(text):
            home_path_files.append(rel)
    return {
        "blockers": blockers,
        "blocker_count": len(blockers),
        "keyword_hits": keyword_hits,
        "keyword_hit_count": len(keyword_hits),
        "home_path_file_count": len(home_path_files),
        "home_path_files_sample": sorted(home_path_files)[:20],
        "binary_files_skipped": sorted(binary_skipped),
    }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def _write(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def _under_compat_symlink(path: Path, bundle_root: Path) -> bool:
    """True if a walked path is inside the docs/ compat symlink (already hashed under paper/)."""
    rel = path.relative_to(bundle_root).as_posix()
    return rel.startswith(f"{_COMPAT_SYMLINK_PARENT}/{_COMPAT_SYMLINK_NAME}/")


def build(*, output_root: Path, dry_run: bool, tag_name: str | None = None, remote_url: str | None = None) -> int:
    stamp = _utc_stamp()
    bundle_name = f"aigis-gw-efficacy-bundle-{stamp}"
    bundle_root = output_root / bundle_name
    tag_name = tag_name or f"aigis-gw-efficacy-{stamp[:8]}"
    remote_url = remote_url or "<YOUR_PUBLIC_REMOTE_URL>"

    head_sha = git_head_sha()
    head_subject = git_head_subject()

    package_rel = select_package_rel_files()
    head_bytes: dict[str, bytes] = {rel: git_show_bytes(rel) for rel in package_rel}
    package_texts = {rel: _decode(b) for rel, b in head_bytes.items() if Path(rel).suffix.lower() in _SCAN_SUFFIXES}

    prereg_rel = select_prereg_rel_files(package_texts)
    for rel in prereg_rel:
        head_bytes[rel] = git_show_bytes(rel)

    script_rel, scripts_missing = select_script_rel_files()
    for rel in script_rel:
        head_bytes[rel] = git_show_bytes(rel)

    ref_hashes, ref_names = collect_referenced_receipt_refs(package_rel + prereg_rel, head_bytes)
    receipt_files, receipt_reasons = select_receipts(ref_hashes, ref_names)

    summary = {
        "bundle_name": bundle_name,
        "git_head": head_sha,
        "git_head_subject": head_subject,
        "counts": {
            "package_files": len(package_rel),
            "preregistrations": len(prereg_rel),
            "scripts": len(script_rel),
            "scripts_missing": len(scripts_missing),
            "receipts": len(receipt_files),
        },
        "receipts_matched_by": receipt_reasons,
        "scripts_missing": scripts_missing,
    }

    if dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        print("\n[dry-run] no files written")
        return 0

    if scripts_missing:
        print(f"WARNING: {len(scripts_missing)} named scripts not tracked at HEAD: {scripts_missing}", file=sys.stderr)

    bundle_root.mkdir(parents=True, exist_ok=False)

    # 1-3. Tracked files, from HEAD, remapped to the replicator-first layout.
    for rel in package_rel + prereg_rel + script_rel:
        data = head_bytes[rel]
        dest_rel = bundle_dest_rel(rel)
        if dest_rel == "README.md":
            data = data.replace(b"{{TAG_NAME}}", tag_name.encode("utf-8"))
        _write(bundle_root / dest_rel, data)
    # scripts package markers so `scripts.research.*` imports resolve if used.
    if git_is_tracked("scripts/__init__.py"):
        _write(bundle_root / "scripts" / "__init__.py", git_show_bytes("scripts/__init__.py"))
    (bundle_root / SCRIPTS_REL / "__init__.py").write_text("", encoding="utf-8")
    # Compatibility symlink so the pipeline code finds the package dir at its
    # repo-relative path (the scripts compute REPO_ROOT from __file__).
    symlink_parent = bundle_root / _COMPAT_SYMLINK_PARENT
    symlink_parent.mkdir(parents=True, exist_ok=True)
    (symlink_parent / _COMPAT_SYMLINK_NAME).symlink_to(_COMPAT_SYMLINK_TARGET, target_is_directory=True)

    # 4. Receipts (mechanically selected only; from the live store).
    for src in receipt_files:
        dest = bundle_root / "receipts" / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    # 5. Environment manifests.
    env_dir = bundle_root / "environment"
    env_dir.mkdir(parents=True, exist_ok=True)
    main_freeze, main_method = _freeze(MAIN_VENV_PY)
    lal_freeze, lal_method = _freeze(LAL_VENV_PY)
    lal_oracle_text, lal_oracle_hash = _lal_oracle_env(LAL_VENV_PY)
    main_py_ver = _python_version(MAIN_VENV_PY)
    lal_py_ver = _python_version(LAL_VENV_PY)
    (env_dir / "main_venv.freeze.txt").write_text(
        f"# AIGIS main .venv package list (python {main_py_ver})\n"
        f"# captured via: {main_method}\n"
        "# The Study-1 sweep, fresh-holdout, PSD, and posterior runners need only\n"
        "# numpy + scipy from this list; GWOSC fetches use the stdlib urllib.\n"
        f"{main_freeze}",
        encoding="utf-8",
    )
    (env_dir / "lal_venv.freeze.txt").write_text(
        f"# Isolated lal_venv package list (python {lal_py_ver})\n"
        f"# captured via: {lal_method}\n"
        "# Provides lalsuite/lalsimulation for the external oracle grid\n"
        "# (lal_oracle_compare.py). Never install lalsuite into the main .venv.\n"
        f"{lal_freeze}",
        encoding="utf-8",
    )
    (env_dir / "lal_venv.oracle_environment.txt").write_text(lal_oracle_text, encoding="utf-8")

    # 6. audit/READINESS_AT_BUILD.json -- run the BUNDLED audit over the bundled
    # HEAD artifacts (exercising the docs/ compat symlink), then normalize the
    # bundle path so the record is deterministic.
    audit_dir = bundle_root / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    readiness_path = audit_dir / "READINESS_AT_BUILD.json"
    # -B: do not write .pyc bytecode into the bundle's scripts/research dir.
    code, readiness_out, readiness_err = _run(
        [str(MAIN_VENV_PY), "-B", str(bundle_root / SCRIPTS_REL / "gw_package_readiness.py")],
        cwd=bundle_root,
    )
    if code == 0 and readiness_out.strip():
        normalized = readiness_out.replace(str(bundle_root), "<BUNDLE_ROOT>")
        readiness_path.write_text(normalized, encoding="utf-8")
    else:
        # Fallback: audit the repo checkout.
        code2, out2, err2 = _run([str(MAIN_VENV_PY), "-B", str(REPO_ROOT / SCRIPTS_REL / "gw_package_readiness.py")])
        if code2 == 0 and out2.strip():
            readiness_path.write_text(out2.replace(str(REPO_ROOT), "<REPO_ROOT>"), encoding="utf-8")
        else:
            readiness_path.write_text(
                json.dumps(
                    {"error": "gw_package_readiness.py produced no output", "stderr": readiness_err or err2}, indent=2
                ),
                encoding="utf-8",
            )
    try:
        readiness_obj = json.loads(readiness_path.read_text(encoding="utf-8"))
        readiness_state = {
            "epistemic_status": readiness_obj.get("epistemic_status"),
            "analysis_ready_for_external_review": readiness_obj.get("analysis_ready_for_external_review"),
            "external_ready": readiness_obj.get("external_ready"),
            "gate_status_counts": readiness_obj.get("gate_status_counts"),
        }
    except (json.JSONDecodeError, OSError):
        readiness_state = {"error": "unparseable readiness output"}

    # 7. audit/BUILD_INFO.json -- provenance + reproduction note.
    build_info = {
        "schema": "aigis.gw.replication_bundle.v2",
        "layout": "replicator-first-v2",
        "bundle_name": bundle_name,
        "built_at": stamp,
        "git_head": head_sha,
        "git_head_subject": head_subject,
        "tag_name": tag_name,
        "source_policy": "all git-tracked files read from HEAD; receipts and venv freezes from the live filesystem",
        "layout_note": (
            "Shallow replicator-first tree: README.md + REPLICATION.md at root, paper/, "
            "preregistrations/, scripts/research/ (nesting kept for runnability), receipts/, "
            "environment/, audit/. docs/research/papers/gw-inspiral-template-efficacy is a "
            "relative symlink to paper/ so the pipeline code resolves its repo-relative "
            "package path unmodified (macOS/Linux)."
        ),
        "counts": summary["counts"],
        "receipts_matched_by": receipt_reasons,
        "scripts_missing": scripts_missing,
        "excluded_from_bundle": sorted(EXCLUDE_FROM_BUNDLE),
        "environment": {
            "main_venv_python": main_py_ver,
            "main_venv_freeze_method": main_method,
            "lal_venv_python": lal_py_ver,
            "lal_venv_freeze_method": lal_method,
            "lal_oracle_environment_sha256_live": lal_oracle_hash,
        },
        "readiness_at_build": readiness_state,
        "determinism_note": (
            "MANIFEST.sha256 hashes every bundled regular file except MANIFEST.sha256 and "
            "BUNDLE_SHA256, in fixed sorted order (the docs/ compat symlink is not a regular "
            "file and is not hashed). Re-running at the same git HEAD with the same receipt "
            "store reproduces identical file hashes for all scientific content and for the "
            "path-normalized audit/READINESS_AT_BUILD.json. The only files that differ across "
            "rebuilds are the build-stamp-bearing audit/BUILD_INFO.json and the point-in-time "
            "environment/*.freeze.txt snapshots. bundle.tar.gz is not byte-reproducible "
            "(embedded mtimes); compare MANIFEST, not tar.gz."
        ),
    }
    (audit_dir / "BUILD_INFO.json").write_text(json.dumps(build_info, indent=2, sort_keys=True), encoding="utf-8")

    # 8. Operator START_HERE -- written OUTSIDE the bundle as a sibling file.
    # Its audience is the operator (push+tag instructions), not the replicator,
    # so it must not ship inside the bundle. The tag message binds the bundle
    # hash via $(cat BUNDLE_SHA256) shell substitution rather than a literal:
    # the hash does not exist until the manifest is finalized, and the
    # substitution resolves to the exact same value at tag time.
    display_root = str(bundle_root).replace(str(Path.home()), "~")
    (output_root / f"{bundle_name}.START_HERE.md").write_text(
        "# OPERATOR ONLY -- push+tag instructions (not part of the bundle)\n\n"
        f"Bundle: `{display_root}`\n"
        f"Built {stamp} at git HEAD `{head_sha}`\n"
        f"({head_subject}).\n\n"
        "This file is written OUTSIDE the bundle directory on purpose: it is the\n"
        "operator's push+tag runsheet, and the replicator-facing entry point is\n"
        "the bundle's own README.md + REPLICATION.md.\n\n"
        "## Push + signed tag (ssh-signing; no gpg key on this machine)\n\n"
        "git's ssh-signing mode signs the tag with the SSH key already used for\n"
        "GitHub auth. The tag message binds the bundle hash at tag time via\n"
        "`$(cat BUNDLE_SHA256)`, so this block needs no manual hash edit. If the\n"
        "remote already has history (a prior bundle layout), the force-push\n"
        "replaces main; do NOT delete prior signed tags -- they stay as the\n"
        "anchored history of earlier builds.\n\n"
        "```bash\n"
        f"cd {display_root}\n"
        "git init -q\n"
        "git config gpg.format ssh\n"
        "git config user.signingkey ~/.ssh/id_ed25519.pub\n"
        "git add -A\n"
        'git commit -qm "AIGIS GW inspiral-template-efficacy replication bundle (replicator-first layout)"\n'
        f'git tag -s {tag_name} -m "BUNDLE_SHA256=$(cat BUNDLE_SHA256)"\n'
        f"git remote add origin {remote_url}\n"
        "git fetch origin\n"
        "git push -f -u origin HEAD:main\n"
        f"git push origin {tag_name}\n"
        "```\n\n"
        'For the tag signature to show "Verified" on GitHub, the same key must be\n'
        "registered as a SIGNING key (auth-only registration is not enough):\n"
        "`gh ssh-key add ~/.ssh/id_ed25519.pub --type signing`\n",
        encoding="utf-8",
    )

    # 9. Prune any bytecode caches (defensive; -B should prevent these) so the
    # bundle carries no non-deterministic .pyc artifacts.
    for pyc_dir in bundle_root.rglob("__pycache__"):
        shutil.rmtree(pyc_dir, ignore_errors=True)

    # 10. Safety scan (before finalizing the manifest / tarball).
    staged_now = sorted(p for p in bundle_root.rglob("*") if p.is_file() and not _under_compat_symlink(p, bundle_root))
    scan = safety_scan(staged_now, bundle_root)
    (audit_dir / "SAFETY_SCAN.json").write_text(json.dumps(scan, indent=2, sort_keys=True), encoding="utf-8")

    if scan["blocker_count"] > 0:
        print("SAFETY SCAN BLOCKED -- credential-class findings:", file=sys.stderr)
        print(json.dumps(scan["blockers"], indent=2), file=sys.stderr)
        print(f"\nPartial staging left at: {bundle_root}", file=sys.stderr)
        print("tar.gz NOT written. Remove the credential(s) from source and rebuild.", file=sys.stderr)
        return 3

    # 11. MANIFEST.sha256 -- deterministic, sorted, excludes itself + BUNDLE_SHA256.
    manifest_lines: list[str] = []
    for path in sorted(p for p in bundle_root.rglob("*") if p.is_file() and not _under_compat_symlink(p, bundle_root)):
        rel = path.relative_to(bundle_root).as_posix()
        if rel in {"MANIFEST.sha256", "BUNDLE_SHA256"}:
            continue
        manifest_lines.append(f"{_sha256_file(path)}  {rel}")
    manifest_text = "\n".join(manifest_lines) + "\n"
    (bundle_root / "MANIFEST.sha256").write_text(manifest_text, encoding="utf-8")
    bundle_sha256 = _sha256_bytes(manifest_text.encode("utf-8"))
    (bundle_root / "BUNDLE_SHA256").write_text(bundle_sha256 + "\n", encoding="utf-8")

    # 12. tar.gz of the directory.
    tar_path = output_root / f"{bundle_name}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(bundle_root, arcname=bundle_name)

    # Report.
    print("=" * 72)
    print(f"Replication bundle built: {bundle_root}")
    print(f"tarball:        {tar_path}")
    print(f"BUNDLE_SHA256:  {bundle_sha256}")
    print(f"git HEAD:       {head_sha}  ({head_subject})")
    print(
        "counts: "
        f"package={len(package_rel)} preregs={len(prereg_rel)} "
        f"scripts={len(script_rel)} receipts={len(receipt_files)} "
        f"manifest_files={len(manifest_lines)}"
    )
    print(
        f"receipts by name: {len(receipt_reasons.get('by_name', []))}  by hash: {len(receipt_reasons.get('by_hash', []))}"
    )
    print(f"readiness at build: {readiness_state}")
    print(
        "safety: "
        f"blockers={scan['blocker_count']} keyword_hits={scan['keyword_hit_count']} "
        f"home_path_files={scan['home_path_file_count']} (home paths informational)"
    )
    print(f"operator runsheet (outside bundle): {output_root / f'{bundle_name}.START_HERE.md'}")
    print(f"tag name: {tag_name}")
    print("=" * 72)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--dry-run", action="store_true", help="report selection without writing the bundle")
    parser.add_argument("--tag-name", help="signed-tag name templated into README + the operator START_HERE")
    parser.add_argument("--remote-url", help="origin URL templated into the operator START_HERE")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    return build(output_root=args.output_root, dry_run=args.dry_run, tag_name=args.tag_name, remote_url=args.remote_url)


if __name__ == "__main__":
    raise SystemExit(main())
