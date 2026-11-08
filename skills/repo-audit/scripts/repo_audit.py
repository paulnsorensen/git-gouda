#!/usr/bin/env python3
"""Read-only audit of every catalog skill's checks for one repository.

Inspects the working tree (and, with --github, read-only GitHub API GET
endpoints) and prints one row per catalog skill: whether its setup is in
place, the evidence found, and which skill fixes a gap. This script never
writes a file and never calls a mutating GitHub API endpoint.

Exit code is always 0 unless the script itself errors (an unhandled
exception). A missing or failing check is reported as a table row, not a
nonzero exit.

Usage:
    repo_audit.py [--root PATH] [--github] [--json | --markdown]
    repo_audit.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

STATUS_PASS = "pass"
STATUS_WARN = "warn"
STATUS_MISSING = "missing"
STATUS_SKIPPED = "skipped"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)\s*(?:#.*)?$", re.MULTILINE)
REMOTE_RE = re.compile(r"github\.com[:/]+([^/]+)/([^/.]+?)(?:\.git)?$")

GH_API_TIMEOUT = 10


@dataclass
class CheckResult:
    check: str
    status: str
    evidence: str
    route_to: str


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _first_existing(root: Path, candidates: list[str]) -> Path | None:
    for rel in candidates:
        path = root / rel
        if path.exists():
            return path
    return None


def _workflow_files(root: Path) -> list[Path]:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return []
    return sorted(p for p in workflows.iterdir() if p.suffix in (".yml", ".yaml") and p.is_file())


def _discover_owner_repo(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=GH_API_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    match = REMOTE_RE.search(out.stdout.strip())
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def _gh_api(endpoint: str) -> tuple[object | None, str | None]:
    """Run a read-only `gh api GET <endpoint>` call. Returns (data, error)."""
    try:
        out = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=GH_API_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        return None, "gh CLI not found"
    except subprocess.TimeoutExpired:
        return None, f"gh api {endpoint} timed out"
    if out.returncode != 0:
        return None, (out.stderr.strip() or f"gh api {endpoint} failed")
    try:
        return json.loads(out.stdout), None
    except json.JSONDecodeError:
        return None, f"gh api {endpoint} returned non-JSON output"


def _git_tags(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "tag", "--list"],
            capture_output=True,
            text=True,
            timeout=GH_API_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0:
        return []
    return [line for line in out.stdout.splitlines() if line.strip()]


def check_prek(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = _first_existing(root, ["prek.toml", ".pre-commit-config.yaml"])
    if found:
        return CheckResult("prek", STATUS_PASS, f"found {found.relative_to(root)}", "prek")
    return CheckResult("prek", STATUS_MISSING, "prek.toml and .pre-commit-config.yaml not found", "prek")


def check_oss_hygiene(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    required = {
        "LICENSE": _first_existing(root, ["LICENSE", "LICENSE.md", "LICENSE.txt"]) is not None,
        "CODE_OF_CONDUCT.md": (root / "CODE_OF_CONDUCT.md").is_file(),
        "CONTRIBUTING.md": (root / "CONTRIBUTING.md").is_file(),
        "SECURITY.md": (root / "SECURITY.md").is_file(),
        ".github/ISSUE_TEMPLATE": (root / ".github" / "ISSUE_TEMPLATE").is_dir(),
        "PULL_REQUEST_TEMPLATE": _first_existing(
            root, [".github/PULL_REQUEST_TEMPLATE.md", "PULL_REQUEST_TEMPLATE.md"]
        )
        is not None,
        ".github/dependabot.yml": (root / ".github" / "dependabot.yml").is_file(),
    }
    present = [name for name, ok in required.items() if ok]
    missing = [name for name, ok in required.items() if not ok]
    workflow_names = {p.name for p in _workflow_files(root)}
    workflow_bits = [
        f"{label}={'yes' if any(marker in name for name in workflow_names) else 'no'}"
        for label, marker in (("scorecard", "scorecard"), ("codeql", "codeql"), ("dependency-review", "dependency-review"))
    ]
    evidence = f"present {len(present)}/{len(required)}"
    if missing:
        evidence += f"; missing: {', '.join(missing)}"
    evidence += f"; workflows: {', '.join(workflow_bits)}"
    if not present:
        status = STATUS_MISSING
    elif missing:
        status = STATUS_WARN
    else:
        status = STATUS_PASS
    return CheckResult("oss-hygiene", status, evidence, "oss-hygiene")


def check_gh_bootstrap(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    release_yml = (root / ".github" / "release.yml").is_file()
    if not github:
        status = STATUS_PASS if release_yml else STATUS_MISSING
        evidence = f".github/release.yml {'found' if release_yml else 'not found'}; run with --github for merge settings and ruleset checks"
        return CheckResult("gh-bootstrap", status, evidence, "gh-bootstrap")
    if owner_repo is None:
        return CheckResult("gh-bootstrap", STATUS_SKIPPED, "could not discover owner/repo from git remote", "gh-bootstrap")
    repo_data, repo_err = _gh_api(f"repos/{owner_repo}")
    rulesets_data, rulesets_err = _gh_api(f"repos/{owner_repo}/rulesets")
    if repo_err or rulesets_err:
        return CheckResult("gh-bootstrap", STATUS_SKIPPED, f"gh api call failed: {repo_err or rulesets_err}", "gh-bootstrap")
    squash_only = bool(
        isinstance(repo_data, dict)
        and repo_data.get("allow_squash_merge")
        and not repo_data.get("allow_merge_commit")
        and not repo_data.get("allow_rebase_merge")
    )
    rulesets_present = bool(isinstance(rulesets_data, list) and rulesets_data)
    checks = [release_yml, squash_only, rulesets_present]
    evidence = (
        f"release.yml={release_yml}, squash-only-merge={squash_only}, "
        f"non-empty rulesets={rulesets_present}"
    )
    if all(checks):
        status = STATUS_PASS
    elif any(checks):
        status = STATUS_WARN
    else:
        status = STATUS_MISSING
    return CheckResult("gh-bootstrap", status, evidence, "gh-bootstrap")


def check_safe_settings(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = (root / ".github" / "settings.yml").is_file()
    status = STATUS_PASS if found else STATUS_SKIPPED
    evidence = ".github/settings.yml found" if found else ".github/settings.yml not found (informational; org-wide settings-as-code is opt-in)"
    return CheckResult("safe-settings", status, evidence, "safe-settings")


def check_config_review_bot(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = (root / ".coderabbit.yaml").is_file()
    status = STATUS_PASS if found else STATUS_MISSING
    evidence = ".coderabbit.yaml found" if found else ".coderabbit.yaml not found"
    return CheckResult("config-review-bot", status, evidence, "config-review-bot")


def check_release(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    tags = _git_tags(root)
    changelog = (root / "CHANGELOG.md").is_file()
    evidence = f"tags: {len(tags)}; CHANGELOG.md {'found' if changelog else 'not found'}"
    if tags and changelog:
        status = STATUS_PASS
    elif tags or changelog:
        status = STATUS_WARN
    else:
        status = STATUS_MISSING
    return CheckResult("release", status, evidence, "release")


def check_justfile(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = _first_existing(root, ["justfile", "Justfile"])
    status = STATUS_PASS if found else STATUS_MISSING
    evidence = f"found {found.relative_to(root)}" if found else "justfile not found"
    return CheckResult("justfile", status, evidence, "justfile")


def check_ci_optimize(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    workflows = _workflow_files(root)
    if not workflows:
        return CheckResult("ci-optimize", STATUS_SKIPPED, "no workflows under .github/workflows (informational)", "ci-optimize")
    with_concurrency = [p.name for p in workflows if "concurrency:" in (_read_text(p) or "")]
    status = STATUS_PASS if with_concurrency else STATUS_SKIPPED
    evidence = f"{len(with_concurrency)}/{len(workflows)} workflows set concurrency: (informational)"
    return CheckResult("ci-optimize", status, evidence, "ci-optimize")


def check_build_optimize(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    return CheckResult(
        "build-optimize", STATUS_SKIPPED, "needs measured wall-time data; not computable from a static audit", "build-optimize"
    )


def check_github_copilot(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    single = (root / ".github" / "copilot-instructions.md").is_file()
    instructions_dir = root / ".github" / "instructions"
    scoped = instructions_dir.is_dir() and any(instructions_dir.glob("*.instructions.md"))
    status = STATUS_PASS if (single or scoped) else STATUS_MISSING
    evidence = f"copilot-instructions.md={single}, scoped instructions={scoped}"
    return CheckResult("github-copilot-repo-instructions", status, evidence, "github-copilot-repo-instructions")


def check_codeowners(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = _first_existing(root, ["CODEOWNERS", "docs/CODEOWNERS", ".github/CODEOWNERS"])
    if not found:
        return CheckResult("codeowners", STATUS_MISSING, "CODEOWNERS not found in root, docs/, or .github/", "codeowners")
    evidence = f"found {found.relative_to(root)}"
    status = STATUS_PASS
    if github:
        if owner_repo is None:
            evidence += "; could not discover owner/repo from git remote"
        else:
            data, err = _gh_api(f"repos/{owner_repo}/codeowners/errors")
            if err:
                evidence += f"; gh api call failed: {err}"
            else:
                errors = data.get("errors", []) if isinstance(data, dict) else []
                evidence += f"; codeowners/errors: {len(errors)}"
                if errors:
                    status = STATUS_WARN
    return CheckResult("codeowners", status, evidence, "codeowners")


def check_actions_pinning(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    workflows = _workflow_files(root)
    if not workflows:
        return CheckResult("actions-pinning", STATUS_MISSING, "no workflows under .github/workflows", "actions-pinning")
    total = 0
    unpinned: list[str] = []
    for path in workflows:
        text = _read_text(path) or ""
        for ref in USES_RE.findall(text):
            if ref.startswith("./") or ref.startswith("docker://"):
                continue
            total += 1
            _, _, version = ref.partition("@")
            if not SHA_RE.match(version):
                unpinned.append(ref)
    if total == 0:
        return CheckResult("actions-pinning", STATUS_MISSING, "no `uses:` references found in workflows", "actions-pinning")
    status = STATUS_PASS if not unpinned else STATUS_WARN
    evidence = f"{total - len(unpinned)}/{total} refs pinned to a 40-hex SHA"
    if unpinned:
        evidence += f"; unpinned: {', '.join(unpinned[:5])}" + (" ..." if len(unpinned) > 5 else "")
    return CheckResult("actions-pinning", status, evidence, "actions-pinning")


def check_pr_title_lint(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    workflows = _workflow_files(root)
    markers = ("action-semantic-pull-request", "commitlint")
    hits = [p.name for p in workflows if any(marker in (_read_text(p) or "") for marker in markers)]
    status = STATUS_PASS if hits else STATUS_MISSING
    evidence = f"workflows with a title-lint marker: {', '.join(hits)}" if hits else "no workflow references action-semantic-pull-request or commitlint"
    return CheckResult("pr-title-lint", status, evidence, "pr-title-lint")


def check_labels_as_code(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    found = _first_existing(root, [".github/labels.yml", ".github/labeler.yml"])
    status = STATUS_PASS if found else STATUS_MISSING
    evidence = f"found {found.relative_to(root)}" if found else ".github/labels.yml and .github/labeler.yml not found"
    return CheckResult("labels-as-code", status, evidence, "labels-as-code")


def check_repo_attributes(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    required = {
        ".gitattributes": (root / ".gitattributes").is_file(),
        ".editorconfig": (root / ".editorconfig").is_file(),
        ".gitignore": (root / ".gitignore").is_file(),
    }
    present = [name for name, ok in required.items() if ok]
    missing = [name for name, ok in required.items() if not ok]
    evidence = f"present {len(present)}/{len(required)}"
    if missing:
        evidence += f"; missing: {', '.join(missing)}"
    if not present:
        status = STATUS_MISSING
    elif missing:
        status = STATUS_WARN
    else:
        status = STATUS_PASS
    return CheckResult("repo-attributes", status, evidence, "repo-attributes")


def check_branch_cleanup(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    if not github:
        return CheckResult("branch-cleanup", STATUS_SKIPPED, "requires --github to read delete_branch_on_merge", "branch-cleanup")
    if owner_repo is None:
        return CheckResult("branch-cleanup", STATUS_SKIPPED, "could not discover owner/repo from git remote", "branch-cleanup")
    data, err = _gh_api(f"repos/{owner_repo}")
    if err:
        return CheckResult("branch-cleanup", STATUS_SKIPPED, f"gh api call failed: {err}", "branch-cleanup")
    enabled = bool(isinstance(data, dict) and data.get("delete_branch_on_merge"))
    status = STATUS_PASS if enabled else STATUS_MISSING
    return CheckResult("branch-cleanup", status, f"delete_branch_on_merge={enabled}", "branch-cleanup")


def check_agents_md(root: Path, github: bool, owner_repo: str | None) -> CheckResult:
    path = root / "AGENTS.md"
    if not path.is_file():
        return CheckResult("agents-md", STATUS_MISSING, "AGENTS.md not found", "agents-md")
    size = path.stat().st_size
    lines = len((_read_text(path) or "").splitlines())
    evidence = f"{size} bytes, {lines} lines"
    if size < 32 * 1024 and lines < 200:
        status = STATUS_PASS
    else:
        status = STATUS_WARN
        evidence += "; exceeds 32 KiB or ~200 lines"
    return CheckResult("agents-md", status, evidence, "agents-md")


CHECKS = [
    check_prek,
    check_oss_hygiene,
    check_gh_bootstrap,
    check_safe_settings,
    check_config_review_bot,
    check_release,
    check_justfile,
    check_ci_optimize,
    check_build_optimize,
    check_github_copilot,
    check_codeowners,
    check_actions_pinning,
    check_pr_title_lint,
    check_labels_as_code,
    check_repo_attributes,
    check_branch_cleanup,
    check_agents_md,
]


def run(root: Path, github: bool) -> list[CheckResult]:
    owner_repo = _discover_owner_repo(root) if github else None
    return [check(root, github, owner_repo) for check in CHECKS]


def _format_table(results: list[CheckResult]) -> str:
    headers = ("check", "status", "evidence", "route-to")
    rows = [(r.check, r.status, r.evidence, r.route_to) for r in results]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths))]
    lines.append("  ".join("-" * w for w in widths))
    for row in rows:
        lines.append("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    return "\n".join(lines)


def _format_markdown(results: list[CheckResult]) -> str:
    lines = ["| Check | Status | Evidence | Route to |", "| --- | --- | --- | --- |"]
    for r in results:
        evidence = r.evidence.replace("|", "\\|")
        lines.append(f"| {r.check} | {r.status} | {evidence} | {r.route_to} |")
    return "\n".join(lines)


def _run_self_test() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        empty_root = Path(tmp)
        empty_results = run(empty_root, github=False)
        bad = [r for r in empty_results if r.status not in (STATUS_MISSING, STATUS_SKIPPED)]
        if bad:
            failures.append(f"empty repo: expected only missing/skipped, got: {[(r.check, r.status) for r in bad]}")

    this_repo = Path(__file__).resolve().parents[3]
    this_results = {r.check: r for r in run(this_repo, github=False)}
    for name in ("prek", "oss-hygiene", "justfile"):
        result = this_results.get(name)
        if result is None or result.status != STATUS_PASS:
            failures.append(f"this repository: expected {name} to pass, got {result.status if result else 'missing check'}")

    if failures:
        for failure in failures:
            print(f"SELF-TEST FAIL: {failure}", file=sys.stderr)
        return 1
    print("OK: self-test passed")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo_audit.py",
        description="Read-only audit of every catalog skill's checks for one repository.",
    )
    parser.add_argument("--root", default=".", help="repository root to audit (default: current directory)")
    parser.add_argument("--github", action="store_true", help="also run read-only GET calls against the GitHub API via gh")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="print results as JSON")
    output.add_argument("--markdown", action="store_true", help="print results as a GitHub-flavored Markdown table")
    parser.add_argument("--self-test", action="store_true", help="run embedded fixtures instead of auditing a repository")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.self_test:
        return _run_self_test()
    root = Path(args.root).resolve()
    results = run(root, args.github)
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    elif args.markdown:
        print(_format_markdown(results))
    else:
        print(_format_table(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
