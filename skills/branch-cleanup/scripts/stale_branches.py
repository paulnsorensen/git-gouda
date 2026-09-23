#!/usr/bin/env python3
"""Report stale git branches with a keep/archive/delete recommendation.

Standard-library only. Wraps ``git`` for local classification and, when
``--github`` is passed, wraps ``gh`` for open-pull-request and ruleset
checks. Never deletes a branch; it only prints the report and, on request,
the exact ``git push origin --delete`` commands for a human to run.

Run ``--self-test`` to exercise classification against a disposable git
repository fixture (no network, no ``gh`` required).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DAYS = 90


class GitError(RuntimeError):
    """A wrapped ``git`` or ``gh`` invocation failed."""


def _run(cmd: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise GitError(f"{' '.join(cmd)}: {result.stderr.strip()}")
    return result.stdout.strip()


def default_branch(repo: Path) -> str:
    """Return the default branch name, preferring the origin HEAD symlink."""
    try:
        ref = _run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], repo)
        return ref.rsplit("/", 1)[-1]
    except GitError:
        pass
    for candidate in ("main", "master"):
        check = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{candidate}"],
            cwd=repo,
            capture_output=True,
        )
        if check.returncode == 0:
            return candidate
    raise GitError("could not determine the default branch")


def remote_branches(repo: Path) -> list[str]:
    """Return short names of remote branches, excluding the HEAD symlink."""
    prefix = "refs/remotes/origin/"
    raw = _run(["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"], repo)
    names = [line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)]
    return [name for name in names if name != "HEAD"]


def branch_ref(repo: Path, branch: str, remote: bool) -> str:
    return f"origin/{branch}" if remote else branch


def last_commit(repo: Path, ref: str) -> tuple[str, str]:
    """Return (ISO commit date, author name) for the branch tip."""
    raw = _run(["git", "log", "-1", "--format=%cI%x1f%an", ref], repo)
    date, author = raw.split("\x1f", 1)
    return date, author


def ahead_behind(repo: Path, default: str, ref: str) -> tuple[int, int]:
    """Return (behind, ahead) of ``ref`` relative to ``default``."""
    raw = _run(["git", "rev-list", "--left-right", "--count", f"{default}...{ref}"], repo)
    behind, ahead = raw.split()
    return int(behind), int(ahead)


def is_merged(repo: Path, default: str, branch: str, remote: bool) -> bool:
    flag = "-r" if remote else ""
    cmd = ["git", "branch"] + ([flag] if flag else []) + ["--merged", default]
    raw = _run(cmd, repo)
    merged_refs = {line.strip().lstrip("* ") for line in raw.splitlines()}
    ref = branch_ref(repo, branch, remote)
    return branch in merged_refs or ref in merged_refs


def gh_open_pr(owner_repo: str, branch: str) -> bool:
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", owner_repo, "--head", branch, "--state", "open", "--json", "number"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(f"gh pr list failed for {branch}: {result.stderr.strip()}")
    prs = json.loads(result.stdout or "[]")
    return len(prs) > 0


def gh_protected(owner_repo: str, branch: str) -> bool:
    result = subprocess.run(
        ["gh", "api", f"repos/{owner_repo}/rules/branches/{branch}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # A 404-shaped failure means no rules target the branch.
        return False
    rules = json.loads(result.stdout or "[]")
    return len(rules) > 0


def age_days(commit_date: str, now: datetime | None = None) -> float:
    commit_dt = datetime.fromisoformat(commit_date)
    now = now or datetime.now(timezone.utc)
    return (now - commit_dt).total_seconds() / 86400


def classify(merged: bool, protected: bool, open_pr: bool, age: float, days: int) -> str:
    """Return one of "keep", "archive", "delete"."""
    if protected or open_pr:
        return "keep"
    if merged:
        return "delete"
    if age >= days:
        return "archive"
    return "keep"


@dataclass
class BranchReport:
    branch: str
    last_commit_date: str
    author: str
    age_days: float
    ahead: int
    behind: int
    merged: bool
    open_pr: bool
    protected: bool
    recommendation: str


def build_report(
    repo: Path,
    default: str,
    branch: str,
    *,
    remote: bool,
    owner_repo: str | None,
    days: int,
) -> BranchReport:
    ref = branch_ref(repo, branch, remote)
    date, author = last_commit(repo, ref)
    behind, ahead = ahead_behind(repo, default, ref)
    merged = is_merged(repo, default, branch, remote)
    open_pr = gh_open_pr(owner_repo, branch) if owner_repo else False
    protected = gh_protected(owner_repo, branch) if owner_repo else False
    age = age_days(date)
    return BranchReport(
        branch=branch,
        last_commit_date=date,
        author=author,
        age_days=round(age, 1),
        ahead=ahead,
        behind=behind,
        merged=merged,
        open_pr=open_pr,
        protected=protected,
        recommendation=classify(merged, protected, open_pr, age, days),
    )


def print_table(reports: list[BranchReport]) -> None:
    reports = sorted(reports, key=lambda r: r.age_days, reverse=True)
    header = ("branch", "age (days)", "author", "ahead", "behind", "merged", "open PR", "protected", "recommendation")
    rows = [header] + [
        (
            r.branch,
            f"{r.age_days:.1f}",
            r.author,
            str(r.ahead),
            str(r.behind),
            str(r.merged),
            str(r.open_pr),
            str(r.protected),
            r.recommendation,
        )
        for r in reports
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    for row in rows:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def print_delete_commands(reports: list[BranchReport]) -> None:
    deletable = [r for r in reports if r.recommendation == "delete"]
    if not deletable:
        return
    print("\nProposed deletions (run only after explicit authorization):")
    for r in deletable:
        print(f"git push origin --delete {r.branch}")


def run_self_test() -> int:
    checks: list[tuple[bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="branch-cleanup-fixture-") as tmp:
        repo = Path(tmp)
        env_cmds = [
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.email", "fixture@example.invalid"],
            ["git", "config", "user.name", "fixture"],
            ["git", "config", "commit.gpgsign", "false"],
        ]
        for cmd in env_cmds:
            _run(cmd, repo)
        (repo / "README.md").write_text("init\n", encoding="utf-8")
        _run(["git", "add", "README.md"], repo)
        _run(["git", "commit", "-qm", "init"], repo)

        _run(["git", "checkout", "-qb", "merged-branch"], repo)
        (repo / "merged.txt").write_text("merged\n", encoding="utf-8")
        _run(["git", "add", "merged.txt"], repo)
        _run(["git", "commit", "-qm", "add merged.txt"], repo)
        _run(["git", "checkout", "-q", "main"], repo)
        _run(["git", "merge", "-q", "--no-ff", "-m", "merge merged-branch", "merged-branch"], repo)

        _run(["git", "checkout", "-qb", "unmerged-branch"], repo)
        (repo / "unmerged.txt").write_text("unmerged\n", encoding="utf-8")
        _run(["git", "add", "unmerged.txt"], repo)
        _run(["git", "commit", "-qm", "add unmerged.txt"], repo)
        _run(["git", "checkout", "-q", "main"], repo)

        default = "main"
        for branch, expect_merged, expect_recommendation in (
            ("merged-branch", True, "delete"),
            ("unmerged-branch", False, "keep"),
        ):
            report = build_report(repo, default, branch, remote=False, owner_repo=None, days=DEFAULT_DAYS)
            checks.append((report.merged == expect_merged, f"{branch}: expected merged={expect_merged}, got {report.merged}"))
            checks.append((
                report.recommendation == expect_recommendation,
                f"{branch}: expected recommendation={expect_recommendation!r}, got {report.recommendation!r}",
            ))

        old_report = build_report(repo, default, "unmerged-branch", remote=False, owner_repo=None, days=0)
        checks.append((
            old_report.recommendation == "archive",
            f"unmerged-branch with days=0: expected recommendation='archive', got {old_report.recommendation!r}",
        ))

        checks.append((
            classify(merged=False, protected=True, open_pr=False, age=999, days=0) == "keep",
            "protected branch must classify as keep regardless of age",
        ))
        checks.append((
            classify(merged=False, protected=False, open_pr=True, age=999, days=0) == "keep",
            "branch with an open PR must classify as keep regardless of age",
        ))

    failures = [message for passed, message in checks if not passed]
    print(f"self-test: {len(checks) - len(failures)}/{len(checks)} passed")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report stale git branches with a keep/archive/delete recommendation.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"staleness threshold in days (default: {DEFAULT_DAYS})")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    parser.add_argument("--github", metavar="OWNER/REPO", help="also check open PRs and rulesets via gh")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="path to the git repository (default: cwd)")
    parser.add_argument("--self-test", action="store_true", help="run the embedded fixture self-test and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    repo = args.repo.resolve()
    try:
        default = default_branch(repo)
        branches = [b for b in remote_branches(repo) if b != default]
        reports = [
            build_report(repo, default, b, remote=True, owner_repo=args.github, days=args.days) for b in branches
        ]
    except GitError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([asdict(r) for r in reports], indent=2))
    else:
        print_table(reports)
        print_delete_commands(reports)
    return 0


if __name__ == "__main__":
    sys.exit(main())
