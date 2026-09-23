#!/usr/bin/env python3
"""Run repository hooks against a disposable snapshot."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _files_for_snapshot(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = [root / item for item in result.stdout.decode("utf-8").split("\0") if item]
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"refusing symlink in checkout snapshot: {path.relative_to(root)}")
    return [path for path in paths if path.is_file()]


def _copy_snapshot(root: Path, destination: Path, files: list[Path]) -> None:
    for source in files:
        relative = source.relative_to(root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _content_map(root: Path) -> dict[str, bytes]:
    files = {}
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            files[str(path.relative_to(root))] = path.read_bytes()
    return files


def run_checks(root: Path) -> int:
    root = root.resolve()
    config = root / "prek.toml"
    if not config.is_file():
        print(f"ERROR: missing {config}", file=sys.stderr)
        return 1

    try:
        files = _files_for_snapshot(root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="git-gouda-hooks-") as temporary:
        snapshot = Path(temporary) / "repo"
        snapshot.mkdir()
        _copy_snapshot(root, snapshot, files)
        subprocess.run(["git", "init", "-q"], cwd=snapshot, check=True)
        subprocess.run(["git", "add", "--all"], cwd=snapshot, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=git-gouda-hook-check",
                "-c",
                "user.email=hook-check@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=/dev/null",
                "commit",
                "-qm",
                "snapshot",
            ],
            cwd=snapshot,
            check=True,
        )
        before = _content_map(snapshot)
        environment = os.environ.copy()
        environment["PREK_HOME"] = str(Path(temporary) / "prek-home")
        result = subprocess.run(
            ["prek", "--config", str(snapshot / "prek.toml"), "run", "--all-files"],
            cwd=snapshot,
            env=environment,
        )
        after = _content_map(snapshot)
        changed = sorted(set(before) | set(after), key=str)
        changed = [path for path in changed if before.get(path) != after.get(path)]
        if changed:
            print("ERROR: hooks would modify the checkout:", file=sys.stderr)
            for path in changed:
                print(f"  {path}", file=sys.stderr)
            return 1
        return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    return run_checks(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
