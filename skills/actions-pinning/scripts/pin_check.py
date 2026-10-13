#!/usr/bin/env python3
"""Scan GitHub Actions workflow files for unpinned `uses:` references.

Regex-scans every workflow file and every `action.yml` / `action.yaml` manifest
under a root directory for `uses:` lines, classifies each reference, and
prints a table of (file, line, action, ref, status). Exits 1 when any
reference is an unpinned tag, branch, commit-like, or other ref, is missing a
ref, or is a `$/` self-repository reference with an `@ref` suffix.

Manifest discovery skips VCS and dependency directories (see `SKIP_DIRS`).
Vendored actions under `vendor/` stay in scope because `./vendor/...` can run
them.

Regex limits (standard library only, so no YAML parser):
- A `uses:` line inside a `run: |` block scalar gives a false row.
- Flow-style mappings such as `- {uses: owner/repo@v1}` give no row.

Standard library only. No network calls; SHA resolution and the
impostor-commit check happen separately through `gh api` (see SKILL.md).

Pass `--self-test` to run the embedded fixtures instead of scanning the
tree (mirrors `validate_evals.py --self-test`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

USES_RE = re.compile(r"^\s*-?\s*uses:\s*(?P<value>\S+)\s*(?:#.*)?$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
COMMIT_LIKE_RE = re.compile(r"^[0-9A-Fa-f]{7,40}$")
BRANCH_NAMES = {"main", "master", "trunk", "develop", "latest", "head"}
TAG_RE = re.compile(r"^v?\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z.-]+)?$")

SKIP_DIRS = frozenset(
    {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".tox", "target"}
)

DEFAULT_GLOBS = (
    ".github/workflows/**/*.yml",
    ".github/workflows/**/*.yaml",
    ".github/actions/**/*.yml",
    ".github/actions/**/*.yaml",
    "**/action.yml",
    "**/action.yaml",
)

STATUS_PINNED = "pinned-sha"
STATUS_UNPINNED_TAG = "unpinned-tag"
STATUS_UNPINNED_BRANCH = "unpinned-branch"
STATUS_UNPINNED_REF = "unpinned-ref"
STATUS_UNPINNED_COMMIT = "unpinned-commit"
STATUS_MISSING_REF = "missing-ref"
STATUS_INVALID_SELF_REF = "invalid-self-ref"
STATUS_LOCAL = "local"
STATUS_DOCKER = "docker"

FAILING_STATUSES = {
    STATUS_UNPINNED_TAG,
    STATUS_UNPINNED_BRANCH,
    STATUS_UNPINNED_REF,
    STATUS_UNPINNED_COMMIT,
    STATUS_MISSING_REF,
    STATUS_INVALID_SELF_REF,
}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    action: str
    ref: str
    status: str


def strip_quotes(value: str) -> str:
    """Remove one matching pair of surrounding YAML quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def classify(value: str) -> tuple[str, str, str]:
    """Return (action, ref, status) for one `uses:` value."""
    value = strip_quotes(value)
    if value.startswith("$/"):
        if "@" in value:
            action, _, ref = value.rpartition("@")
            return action, ref, STATUS_INVALID_SELF_REF
        return value, "", STATUS_LOCAL
    if value.startswith(("./", "../")):
        return value, "", STATUS_LOCAL
    if value.startswith("docker://"):
        return value, "", STATUS_DOCKER
    if "@" not in value:
        return value, "", STATUS_MISSING_REF
    action, _, ref = value.rpartition("@")
    if SHA_RE.match(ref):
        return action, ref, STATUS_PINNED
    if ref.lower() in BRANCH_NAMES:
        return action, ref, STATUS_UNPINNED_BRANCH
    if TAG_RE.match(ref):
        return action, ref, STATUS_UNPINNED_TAG
    if COMMIT_LIKE_RE.match(ref):
        return action, ref, STATUS_UNPINNED_COMMIT
    return action, ref, STATUS_UNPINNED_REF


def scan_text(text: str, file_label: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = USES_RE.match(line)
        if not match:
            continue
        action, ref, status = classify(match.group("value"))
        findings.append(Finding(file=file_label, line=lineno, action=action, ref=ref, status=status))
    return findings


def iter_workflow_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in DEFAULT_GLOBS:
        for path in root.glob(pattern):
            if SKIP_DIRS.isdisjoint(path.relative_to(root).parts[:-1]):
                files.add(path)
    return sorted(files)


def scan_root(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_workflow_files(root):
        label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        findings.extend(scan_text(path.read_text(encoding="utf-8"), label))
    return findings


def print_table(findings: list[Finding]) -> None:
    headers = ("file", "line", "action", "ref", "status")
    rows = [headers] + [(f.file, str(f.line), f.action, f.ref or "-", f.status) for f in findings]
    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    for i, row in enumerate(rows):
        print("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)))
        if i == 0:
            print("  ".join("-" * widths[j] for j in range(len(headers))))


# (label, workflow_text, expected_statuses). Each case pins one classification
# decision the scanner relies on, so a regex or classification regression
# shows up as a self-test failure instead of a silent miscount downstream.
_SELF_TEST_CASES: list[tuple[str, str, list[str]]] = [
    (
        "pinned sha with version comment",
        "steps:\n  - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2\n",
        [STATUS_PINNED],
    ),
    (
        "unpinned semver tag",
        "steps:\n  - uses: actions/setup-node@v4\n",
        [STATUS_UNPINNED_TAG],
    ),
    (
        "unpinned branch ref",
        "steps:\n  - uses: some-org/action@main\n",
        [STATUS_UNPINNED_BRANCH],
    ),
    (
        "missing ref entirely",
        "steps:\n  - uses: some-org/action\n",
        [STATUS_MISSING_REF],
    ),
    (
        "unknown ref name is not inferred as a tag",
        "steps:\n  - uses: some-org/action@release/v1\n",
        [STATUS_UNPINNED_REF],
    ),
    (
        "local composite action",
        "steps:\n  - uses: ./.github/actions/setup-gate\n",
        [STATUS_LOCAL],
    ),
    (
        "self-repository reference",
        "steps:\n  - uses: $/.github/actions/build\n",
        [STATUS_LOCAL],
    ),
    (
        "self-repository reference must not carry a ref",
        "steps:\n  - uses: $/.github/actions/build@v1\n",
        [STATUS_INVALID_SELF_REF],
    ),
    (
        "single-quoted sha pin is still pinned",
        "steps:\n  - uses: 'actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd' # v6.0.2\n",
        [STATUS_PINNED],
    ),
    (
        "double-quoted local path is still local",
        'steps:\n  - uses: "./.github/actions/setup-gate"\n',
        [STATUS_LOCAL],
    ),
    (
        "prerelease tag",
        "steps:\n  - uses: some-org/action@v1.2.3-rc.1\n",
        [STATUS_UNPINNED_TAG],
    ),
    (
        "hyphenated numeric tag",
        "steps:\n  - uses: some-org/action@1-2\n",
        [STATUS_UNPINNED_TAG],
    ),
    (
        "build metadata is not inferred as a tag",
        "steps:\n  - uses: some-org/action@v1.2.3-rc.1+build\n",
        [STATUS_UNPINNED_REF],
    ),
    (
        "uppercase V is not inferred as a tag",
        "steps:\n  - uses: some-org/action@V4\n",
        [STATUS_UNPINNED_REF],
    ),
    (
        "four-part version is not inferred as a tag",
        "steps:\n  - uses: some-org/action@v1.2.3.4\n",
        [STATUS_UNPINNED_REF],
    ),
    (
        "short sha is commit-like, not pinned",
        "steps:\n  - uses: actions/checkout@de0fac2\n",
        [STATUS_UNPINNED_COMMIT],
    ),
    (
        "uppercase full sha is commit-like, not pinned",
        "steps:\n  - uses: actions/checkout@DE0FAC2E4500DABE0009E67214FF5F5447CE83DD\n",
        [STATUS_UNPINNED_COMMIT],
    ),
    (
        "docker reference",
        "steps:\n  - uses: docker://alpine:3.19\n",
        [STATUS_DOCKER],
    ),
    (
        "mixed file, three findings",
        (
            "steps:\n"
            "  - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2\n"
            "  - uses: actions/setup-node@v4\n"
            "  - uses: some-org/action@main\n"
        ),
        [STATUS_PINNED, STATUS_UNPINNED_TAG, STATUS_UNPINNED_BRANCH],
    ),
]


def _write_manifests(root: Path, rels: tuple[str, ...]) -> None:
    for rel in rels:
        manifest = root / rel
        manifest.parent.mkdir(parents=True)
        manifest.write_text("runs:\n  steps:\n    - uses: actions/setup-node@v4\n", encoding="utf-8")


def _composite_manifest_discovery_failure() -> str | None:
    """Return a failure message unless a manifest outside .github/actions is scanned."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_manifests(root, ("tools/setup/action.yml", "tools/lint/action.yaml"))
        actual = sorted((f.file, f.status) for f in scan_root(root))
    expected = [
        (str(Path("tools/lint/action.yaml")), STATUS_UNPINNED_TAG),
        (str(Path("tools/setup/action.yml")), STATUS_UNPINNED_TAG),
    ]
    if actual != expected:
        return f"composite manifests outside .github/actions: expected {expected}, got {actual}"
    return None


def _skip_dirs_discovery_failure() -> str | None:
    """Return a failure message unless VCS and dependency directories are skipped and vendor/ is scanned."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_manifests(
            root,
            (
                ".git/x/action.yml",
                "node_modules/some-pkg/action.yml",
                ".venv/lib/action.yaml",
                "vendor/acme/act/action.yml",
            ),
        )
        actual = sorted(f.file for f in scan_root(root))
    expected = [str(Path("vendor/acme/act/action.yml"))]
    if actual != expected:
        return f"skip VCS/dependency dirs: expected {expected}, got {actual}"
    return None


_DISCOVERY_CHECKS = (_composite_manifest_discovery_failure, _skip_dirs_discovery_failure)


def self_test() -> int:
    failures: list[str] = []
    for label, text, expected in _SELF_TEST_CASES:
        actual = [f.status for f in scan_text(text, "fixture.yml")]
        if actual != expected:
            failures.append(f"{label}: expected {expected}, got {actual}")
    for check in _DISCOVERY_CHECKS:
        failure = check()
        if failure:
            failures.append(failure)

    total = len(_SELF_TEST_CASES) + len(_DISCOVERY_CHECKS)
    print(f"self-test: {total - len(failures)}/{total} passed")
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root to scan (default: current directory).",
    )
    parser.add_argument("--json", action="store_true", help="Print findings as JSON instead of a table.")
    parser.add_argument("--self-test", action="store_true", help="Run embedded fixtures and exit.")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    findings = scan_root(root)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    elif findings:
        print_table(findings)
    else:
        print("No `uses:` references found.")

    return 1 if any(f.status in FAILING_STATUSES for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
