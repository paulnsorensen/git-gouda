#!/usr/bin/env python3
"""Scan GitHub Actions workflow files for unpinned `uses:` references.

Regex-scans every workflow and composite-action file under a root directory
for `uses:` lines, classifies each reference, and prints a table of
(file, line, action, ref, status). Exits 1 when any reference is an unpinned
tag, an unpinned branch ref, or missing a ref entirely.

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
from dataclasses import asdict, dataclass
from pathlib import Path

USES_RE = re.compile(r"^\s*-?\s*uses:\s*(?P<value>\S+)\s*(?:#.*)?$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
BRANCH_NAMES = {"main", "master", "trunk", "develop", "latest", "head"}

DEFAULT_GLOBS = (
    ".github/workflows/**/*.yml",
    ".github/workflows/**/*.yaml",
    ".github/actions/**/*.yml",
    ".github/actions/**/*.yaml",
)

STATUS_PINNED = "pinned-sha"
STATUS_UNPINNED_TAG = "unpinned-tag"
STATUS_UNPINNED_BRANCH = "unpinned-branch"
STATUS_MISSING_REF = "missing-ref"
STATUS_LOCAL = "local"
STATUS_DOCKER = "docker"

FAILING_STATUSES = {STATUS_UNPINNED_TAG, STATUS_UNPINNED_BRANCH, STATUS_MISSING_REF}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    action: str
    ref: str
    status: str


def classify(value: str) -> tuple[str, str, str]:
    """Return (action, ref, status) for one `uses:` value."""
    if value.startswith("./") or value.startswith("../"):
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
    return action, ref, STATUS_UNPINNED_TAG


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
        files.update(root.glob(pattern))
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
        "local composite action",
        "steps:\n  - uses: ./.github/actions/setup-gate\n",
        [STATUS_LOCAL],
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


def self_test() -> int:
    failures: list[str] = []
    for label, text, expected in _SELF_TEST_CASES:
        actual = [f.status for f in scan_text(text, "fixture.yml")]
        if actual != expected:
            failures.append(f"{label}: expected {expected}, got {actual}")

    print(f"self-test: {len(_SELF_TEST_CASES) - len(failures)}/{len(_SELF_TEST_CASES)} passed")
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
